"""The silk (added-mask) auditor reads fixtures in short-lived children; pcbnew and kicad-cli are faked."""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import types
import unittest
import unittest.mock
from pathlib import Path

import scripts.pcbgen.audit_added_mask as audit
from scripts.pcbgen.test_audit_added_mask import board, item

UUID=re.compile(r'uuid "([^"]+)"')


class Point:
    def __init__(self,x,y):self.x,self.y=x,y


class Box:
    def Inflate(self,margin):pass
    def Intersects(self,other):return True


class Uuid:
    def __init__(self,text):self.text=text
    def AsString(self):return self.text


class Track:
    def __init__(self,uid,kind):self.m_Uuid=Uuid(uid);self.kind=kind;self.n=int(uid[-4:])
    def Type(self):return fake.PCB_VIA_T if self.kind=='via' else fake.PCB_TRACE_T
    def HasSolderMask(self):return False
    def GetSolderMaskExpansion(self):return 50_000
    def GetBoundingBox(self):return Box()
    def GetStart(self):return Point(self.n,1)
    def GetEnd(self):return Point(self.n,2)
    def GetPosition(self):return Point(self.n,3)
    def GetWidth(self,*layer):return 200_000
    def GetLayer(self):return 0
    def GetDrillValue(self):return 300_000
    def GetLayerSet(self):return types.SimpleNamespace(Seq=lambda:[0,31])
    def IsTented(self,layer):return False


class Text:
    m_Uuid=Uuid('00000000-0000-4000-8000-text00000001')
    def GetShownText(self,flag):return 'OSC'
    def GetLayer(self):return 5
    def IsOnLayer(self,layer):return False
    def GetBoundingBox(self):return Box()


class Board:
    def __init__(self,tracks):self.tracks=tracks;self.footprints=[];self.drawings=[Text()]
    def GetTracks(self):return list(self.tracks)
    def Zones(self):return []
    def GetFootprints(self):return list(self.footprints)
    def GetDrawings(self):return list(self.drawings)
    def GetDesignSettings(self):return types.SimpleNamespace(m_SolderMaskMinWidth=0)


fake=types.SimpleNamespace(PCB_VIA_T=1,PCB_TRACE_T=2,F_Mask=10,B_Mask=11,Edge_Cuts=12,F_SilkS=13,B_SilkS=14,F_Cu=0)


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp());self.addCleanup(__import__('shutil').rmtree,self.root)
        self.before=self.root/'before.kicad_pcb';self.after=self.root/'after.kicad_pcb'
        self.added=[item(i,'via' if i%5==0 else 'segment') for i in range(1,41)]
        self.before.write_text(board(item(0)));self.after.write_text(board(item(0),*self.added))
        for path in (self.before,self.after):
            path.with_suffix('.kicad_pro').write_text(json.dumps({'board':{'design_settings':{'rules':{'min_silk_clearance':0.1}}}}))
            path.with_suffix('.kicad_dru').write_text('(version 1)\n')
        self.loads={'parent':0,'child':0};self.in_child=False;self.probes=[];self.tamper=None;self.row_tamper=None
        def kinds(text):return [(m[1],'via' if block.startswith('(via') else 'segment')
                                for block in re.findall(r'\((?:via|segment)[^()]*(?:\([^()]*\)[^()]*)*\)',text) for m in [UUID.search(block)]]
        def load(path):
            self.loads['child' if self.in_child else 'parent']+=1
            loaded=Board([Track(u,k) for u,k in kinds(Path(path).read_text())])
            if self.in_child and self.tamper:self.tamper(loaded)
            return loaded
        fake.LoadBoard=load
        patch=unittest.mock.patch.dict(sys.modules,{'pcbnew':fake});patch.start();self.addCleanup(patch.stop)

    def run_audit(self,fixture_range=None,name='silk'):
        def run(args,**kw):
            if audit.PROBE_FLAG in args:
                self.probes.append(len(args)-3);self.in_child=True
                try:out=''.join(audit.PROBE_PREFIX+json.dumps((self.row_tamper or (lambda r:r))(audit.native_fixture_view(Path(f))))+'\n' for f in args[3:])
                finally:self.in_child=False
                return types.SimpleNamespace(stdout=out)
            Path(args[args.index('--output')+1]).write_text(json.dumps({'violations':[]}))
            return types.SimpleNamespace(stdout='')
        out=self.root/name
        with unittest.mock.patch.object(audit.subprocess,'run',side_effect=run),\
             unittest.mock.patch.object(audit.subprocess,'check_output',return_value='10.0.6\n'),\
             unittest.mock.patch('builtins.print'):
            audit.main(self.before,self.after,out,expected_copper=40,expected_vias=8,fixture_range=fixture_range)
        return json.loads((out/('result.json' if fixture_range is None else 'shard-result.json')).read_text())

    def test_parent_loads_only_the_two_source_boards_and_children_read_every_fixture(self):
        result=self.run_audit()
        self.assertEqual(self.loads,{'parent':2,'child':40})
        self.assertEqual(self.probes,[audit.PROBE_BATCH,40-audit.PROBE_BATCH])
        self.assertEqual(len(result['fixtures']),40);self.assertEqual(result['new_mask_identities'],[])
        uids=[f['copper_uuid'] for f in result['fixtures']];self.assertEqual(uids,sorted(uids))
        via=next(f for f in result['fixtures'] if f['kind']=='via')
        self.assertEqual(via['native_mask_signature'],[int(via['copper_uuid'][-4:]),3,300_000,200_000,[0,31],50_000,False,False])

    def test_monolithic_rows_bind_the_probed_fixture_bytes(self):
        result=self.run_audit()
        for i,f in enumerate(result['fixtures']):
            board=self.root/'silk'/f'fixture-{i:03d}'/self.after.name
            self.assertEqual(f['fixture_sha256'],hashlib.sha256(board.read_bytes()).hexdigest())
        self.assertTrue(result['added_copper_scope_complete']);self.assertFalse((self.root/'silk'/'shard-result.json').exists())

    def test_range_mode_writes_only_a_shard_receipt_with_global_fixture_indices(self):
        whole=self.run_audit()
        shard=self.run_audit((32,40),'shard')
        out=self.root/'shard'
        self.assertFalse((out/'result.json').exists());self.assertNotIn('added_copper_scope_complete',shard)
        self.assertEqual(shard['status'],audit.SHARD_STATUS);self.assertEqual((shard['fixture_range'],shard['fixture_total']),([32,40],40))
        self.assertEqual(sorted(p.name for p in out.glob('fixture-*')),[f'fixture-{i:03d}' for i in range(32,40)])
        self.assertEqual(shard['fixtures'],whole['fixtures'][32:])
        self.assertEqual(shard['ordered_scope_sha256'],audit.ordered_scope_sha256(whole['added_copper_source_scope']))
        for suffix,key in (('.kicad_pro','project_sha256'),('.kicad_dru','rules_sha256')):
            self.assertEqual(shard[key],hashlib.sha256(self.after.with_suffix(suffix).read_bytes()).hexdigest())
        for key in ('version','before_sha256','after_sha256','unchanged_nonrouting_objects','added_unmasked_tracks','added_copper_source_scope'):
            self.assertEqual(shard[key],whole[key])
        self.assertEqual(self.probes[-1],8)

    def test_range_mode_rejects_unaligned_or_out_of_scope_ranges_before_any_fixture(self):
        for rng in ((16,40),(0,41),(32,32),(40,41),(-32,8)):
            with self.subTest(rng=rng):
                self.probes.clear();out=self.root/f'bad-{rng[0]}-{rng[1]}'
                with self.assertRaisesRegex(ValueError,'fixture range'):self.run_audit(rng,out.name)
                self.assertEqual(self.probes,[]);self.assertEqual(list(out.glob('fixture-*')),[])
                self.assertFalse((out/'shard-result.json').exists())
        for text in ('0-32','a:b','00:32','0:','0:0'):
            with self.subTest(text=text),self.assertRaisesRegex(ValueError,'START:END'):audit.parse_fixture_range(text)

    def test_killed_shard_leaves_no_shard_receipt(self):
        calls=[]
        def run(args,**kw):
            if audit.PROBE_FLAG in args:
                return types.SimpleNamespace(stdout=''.join(audit.PROBE_PREFIX+json.dumps(audit.native_fixture_view(Path(f)))+'\n' for f in args[3:]))
            calls.append(args)
            if len(calls)==5:raise subprocess.CalledProcessError(137,args)
            Path(args[args.index('--output')+1]).write_text(json.dumps({'violations':[]}))
        out=self.root/'killed'
        with unittest.mock.patch.object(audit.subprocess,'run',side_effect=run),\
             unittest.mock.patch.object(audit.subprocess,'check_output',return_value='10.0.6\n'),\
             unittest.mock.patch('builtins.print'),self.assertRaises(subprocess.CalledProcessError):
            audit.main(self.before,self.after,out,expected_copper=40,expected_vias=8,fixture_range=(0,32))
        self.assertTrue((out/'started.json').exists())
        self.assertFalse((out/'shard-result.json').exists());self.assertFalse((out/'result.json').exists())

    def test_capped_fixture_fails_the_shard_itself(self):
        def run(args,**kw):
            if audit.PROBE_FLAG in args:
                return types.SimpleNamespace(stdout=''.join(audit.PROBE_PREFIX+json.dumps(audit.native_fixture_view(Path(f)))+'\n' for f in args[3:]))
            rows=[dict(type='silk_over_copper',severity='warning',items=[{'uuid':'a'},{'uuid':str(i)}]) for i in range(199)]
            Path(args[args.index('--output')+1]).write_text(json.dumps({'violations':rows}))
        out=self.root/'capped'
        with unittest.mock.patch.object(audit.subprocess,'run',side_effect=run),\
             unittest.mock.patch.object(audit.subprocess,'check_output',return_value='10.0.6\n'),\
             unittest.mock.patch('builtins.print'),self.assertRaisesRegex(ValueError,'report cap'):
            audit.main(self.before,self.after,out,expected_copper=40,expected_vias=8,fixture_range=(0,32))
        self.assertFalse((out/'shard-result.json').exists())

    def test_fixture_observations_still_fail_closed(self):
        class Shown(Text):
            def GetShownText(self,flag):return 'OSC2'
        def retext(b):b.drawings=[Shown()]
        def pads(b):b.footprints=[types.SimpleNamespace(Pads=lambda:['pad'],GetFields=lambda:[],GraphicalItems=lambda:[])]
        def drill(b):b.tracks=[type('T',(Track,),{'GetDrillValue':lambda self:1})(x.m_Uuid.AsString(),x.kind) for x in b.tracks]
        def twice(b):b.tracks=b.tracks+b.tracks
        for tamper,message in ((twice,'copper identity changed'),(drill,'mask/hole geometry changed'),
                               (pads,'old pad masks remain'),(retext,'fixture text rendering changed')):
            with self.subTest(message=message):
                self.tamper=tamper
                with self.assertRaisesRegex(ValueError,message):self.run_audit()
        self.tamper=None;self.row_tamper=lambda r:{**r,'sha256':'0'*64}
        with self.assertRaisesRegex(ValueError,'probe read other bytes'):self.run_audit()

    def test_probe_rows_must_bind_one_observation_to_each_fixture(self):
        row=lambda f:audit.PROBE_PREFIX+json.dumps({'fixture':f})
        for stdout in ('',row('a')+'\n',row('b')+'\n'+row('a')+'\n'):
            with self.subTest(stdout=stdout),unittest.mock.patch.object(audit.subprocess,'run',return_value=types.SimpleNamespace(stdout=stdout)):
                with self.assertRaisesRegex(ValueError,'one observation per fixture'):audit.probe_fixtures([Path('a'),Path('b')])
        with unittest.mock.patch.object(audit.subprocess,'run',return_value=types.SimpleNamespace(stdout='noise\n'+row('a')+'\n'+row('b')+'\n')) as run:
            self.assertEqual([r['fixture'] for r in audit.probe_fixtures([Path('a'),Path('b')])],['a','b'])
        self.assertEqual(run.call_args.args[0][1:],[audit.__file__,audit.PROBE_FLAG,'a','b']);self.assertTrue(run.call_args.kwargs['check'])


FAKE_PCBNEW="""
import re
PCB_VIA_T,PCB_TRACE_T,F_SilkS,B_SilkS,F_Cu,Edge_Cuts=1,2,13,14,0,12
class _U:
    def __init__(self,t):self.t=t
    def AsString(self):return self.t
class _P:
    def __init__(self,x,y):self.x,self.y=x,y
class _Via:
    def __init__(self,u):self.m_Uuid=_U(u)
    def Type(self):return PCB_VIA_T
    def GetPosition(self):return _P(7,8)
    def GetDrillValue(self):return 300000
    def GetWidth(self,*a):return 600000
    def GetLayerSet(self):return type('S',(),{'Seq':lambda self:[0,31]})()
    def GetSolderMaskExpansion(self):return 50000
    def IsTented(self,layer):return layer==F_SilkS
class _Board:
    def __init__(self,ids):self.ids=ids
    def GetTracks(self):return [_Via(u) for u in self.ids]
    def GetFootprints(self):return []
    def GetDrawings(self):return []
def LoadBoard(path):
    print('pcbnew noise on stdout')
    return _Board(re.findall(r'uuid "([^"]+)"',open(path).read()))
"""


class RealChildTests(unittest.TestCase):
    def test_probe_runs_the_main_branch_in_a_child_and_binds_rows_to_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);(folder/'pcbnew.py').write_text(FAKE_PCBNEW)
            fixtures=[folder/'a.kicad_pcb',folder/'b.kicad_pcb']
            fixtures[0].write_text(board(item(1,'via')));fixtures[1].write_text(board(item(2,'via'),item(3,'via')))
            env={**os.environ,'PYTHONPATH':os.pathsep.join(filter(None,[str(folder),os.environ.get('PYTHONPATH')]))}
            with unittest.mock.patch.dict(os.environ,env):rows=audit.probe_fixtures(fixtures)
            self.assertEqual([r['fixture'] for r in rows],[str(f) for f in fixtures])
            self.assertEqual([r['sha256'] for r in rows],[hashlib.sha256(f.read_bytes()).hexdigest() for f in fixtures])
            self.assertEqual([len(r['track_uuids']) for r in rows],[1,2])
            self.assertEqual(rows[0]['signature'],[7,8,300000,600000,[0,31],50000,True,False]);self.assertIsNone(rows[1]['signature'])
            self.assertEqual((rows[0]['pads'],rows[0]['texts']),(False,[]))
            failed=subprocess.run([sys.executable,audit.__file__,audit.PROBE_FLAG,str(folder/'missing.kicad_pcb')],env=env,capture_output=True,text=True)
            self.assertNotEqual(failed.returncode,0)


if __name__=='__main__':unittest.main()
