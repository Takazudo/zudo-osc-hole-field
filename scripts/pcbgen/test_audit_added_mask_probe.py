"""The silk (added-mask) auditor reads fixtures in short-lived children; pcbnew and kicad-cli are faked."""
import json
import re
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
    def __init__(self,tracks):self.tracks=tracks
    def GetTracks(self):return list(self.tracks)
    def Zones(self):return []
    def GetFootprints(self):return []
    def GetDrawings(self):return [Text()]
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
        self.loads={'parent':0,'child':0};self.in_child=False;self.probes=[];self.tamper=None
        def kinds(text):return [(m[1],'via' if block.startswith('(via') else 'segment')
                                for block in re.findall(r'\((?:via|segment)[^()]*(?:\([^()]*\)[^()]*)*\)',text) for m in [UUID.search(block)]]
        def load(path):
            self.loads['child' if self.in_child else 'parent']+=1
            tracks=[Track(u,k) for u,k in kinds(Path(path).read_text())]
            if self.in_child and self.tamper:tracks=self.tamper(tracks)
            return Board(tracks)
        fake.LoadBoard=load
        patch=unittest.mock.patch.dict(sys.modules,{'pcbnew':fake});patch.start();self.addCleanup(patch.stop)

    def run_audit(self):
        def run(args,**kw):
            if audit.PROBE_FLAG in args:
                self.probes.append(len(args)-3);self.in_child=True
                try:out=''.join(audit.PROBE_PREFIX+json.dumps(audit.native_fixture_view(Path(f)))+'\n' for f in args[3:])
                finally:self.in_child=False
                return types.SimpleNamespace(stdout=out)
            Path(args[args.index('--output')+1]).write_text(json.dumps({'violations':[]}))
            return types.SimpleNamespace(stdout='')
        out=self.root/'silk'
        with unittest.mock.patch.object(audit.subprocess,'run',side_effect=run),\
             unittest.mock.patch.object(audit.subprocess,'check_output',return_value='10.0.6\n'),\
             unittest.mock.patch('builtins.print'):
            audit.main(self.before,self.after,out,expected_copper=40,expected_vias=8)
        return json.loads((out/'result.json').read_text())

    def test_parent_loads_only_the_two_source_boards_and_children_read_every_fixture(self):
        result=self.run_audit()
        self.assertEqual(self.loads,{'parent':2,'child':40})
        self.assertEqual(self.probes,[audit.PROBE_BATCH,40-audit.PROBE_BATCH])
        self.assertEqual(len(result['fixtures']),40);self.assertEqual(result['new_mask_identities'],[])
        uids=[f['copper_uuid'] for f in result['fixtures']];self.assertEqual(uids,sorted(uids))
        via=next(f for f in result['fixtures'] if f['kind']=='via')
        self.assertEqual(via['native_mask_signature'],[int(via['copper_uuid'][-4:]),3,300_000,200_000,[0,31],50_000,False,False])

    def test_fixture_observations_still_fail_closed(self):
        for tamper,message in ((lambda t:t+t,'copper identity changed'),
                               (lambda t:[type('T',(Track,),{'GetDrillValue':lambda self:1})(x.m_Uuid.AsString(),x.kind) for x in t],'mask/hole geometry changed')):
            with self.subTest(message=message):
                self.tamper=tamper
                with self.assertRaisesRegex(ValueError,message):self.run_audit()

    def test_probe_rows_must_bind_one_observation_to_each_fixture(self):
        row=lambda f:audit.PROBE_PREFIX+json.dumps({'fixture':f})
        for stdout in ('',row('a')+'\n',row('b')+'\n'+row('a')+'\n'):
            with self.subTest(stdout=stdout),unittest.mock.patch.object(audit.subprocess,'run',return_value=types.SimpleNamespace(stdout=stdout)):
                with self.assertRaisesRegex(ValueError,'one observation per fixture'):audit.probe_fixtures([Path('a'),Path('b')])
        with unittest.mock.patch.object(audit.subprocess,'run',return_value=types.SimpleNamespace(stdout='noise\n'+row('a')+'\n'+row('b')+'\n')) as run:
            self.assertEqual([r['fixture'] for r in audit.probe_fixtures([Path('a'),Path('b')])],['a','b'])
        self.assertEqual(run.call_args.args[0][1:],[audit.__file__,audit.PROBE_FLAG,'a','b']);self.assertTrue(run.call_args.kwargs['check'])


if __name__=='__main__':unittest.main()
