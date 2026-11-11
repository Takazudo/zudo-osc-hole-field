import json
import ast
from pathlib import Path, PurePosixPath
import unittest
import os
import tempfile
from unittest.mock import patch
from types import SimpleNamespace
import osc_frozen_topology as t
import osc_topology_check as run

class Item:
    def __init__(self,uuid,net,layers=('F.Cu',),hit=True):
        self.m_Uuid=SimpleNamespace(AsString=lambda:uuid);self.net=net;self.layers=layers;self.hit=hit
    def GetNetname(self):return self.net
    def IsOnLayer(self,l):return l in self.layers
    def GetEffectiveShape(self,l):return self
    def Collide(self,other,clearance):return self.hit
    def GetNumber(self):return self.number
    def GetIsRuleArea(self):return False
    def GetFilledPolysList(self,l):return SimpleNamespace(OutlineCount=lambda:0)

def fixture(link=False):
    pads={};fps=[]
    for name,e in t.EXPECTED.items():
        p=Item(e['uuid'],e['net']);p.number=name.split('.')[1];pads[name]=p
        fps.append(SimpleNamespace(GetReference=lambda n=name:n.split('.')[0],Pads=lambda p=p:[p]))
    tracks=[Item(u,n,('B.Cu',)) for u,n in t.TRACKS.items()]
    zones=[Item(u,'AGND') for u in t.ZONES]
    a,b=t.PAIRS[0]
    def members(p):return [pads[b]] if link and p is pads[a] else []
    conn=SimpleNamespace(RecalculateRatsnest=lambda:None,GetConnectedItems=members)
    board=SimpleNamespace(GetFootprints=lambda:fps,GetTracks=lambda:tracks,Zones=lambda:zones,GetConnectivity=lambda:conn)
    pcb=SimpleNamespace(**{n.replace('.','_'):n for n in t.COPPER_LAYERS})
    return board,pcb,pads

class Topology(unittest.TestCase):
    def test_incomplete_or_malformed_evidence(self):
        mutations=[lambda r:r['pairs'][0].pop('b_reported_by_a'),
          lambda r:r['foreign_net_shape_observations'][0].pop('shared_layer'),
          lambda r:r['foreign_net_shape_observations'][0].update(shape_intersection=1),
          lambda r:r['foreign_net_shape_observations'][0].update(pad='OTHER.1'),
          lambda r:r['pad_copper_layers'].clear(),
          lambda r:r['zones'].append(r['zones'][0]),
          lambda r:r['zones'][0]['layers'][0].update(saved_filled_outline_count=-1),
          lambda r:r.pop('return_terminal_selection')]
        for mutate in mutations:
            b,p,_=fixture();r=t.observe(b,p);mutate(r)
            with self.assertRaises(ValueError):t.validate(r)
    def test_readonly_mount(self):
        args=['run','--rm','--network','none','--volume','/source:/work','--volume','/tmp/home:/tmp/kicad-home',run.c.IMAGE]
        result=run.readonly_args(args,PurePosixPath('/source'),PurePosixPath('/payload.py'))
        self.assertIn('/source:/work:ro',result);self.assertIn('/payload.py:/topology.py:ro',result)
        with self.assertRaises(ValueError):run.readonly_args(args+['-v','/other:/secret'],PurePosixPath('/source'),PurePosixPath('/payload.py'))
    def test_no_cad_mutators(self):
        tree=ast.parse(Path(t.__file__).read_text())
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls & {'SaveBoard','Save','Fill','Add','Remove','Delete','SetNetCode','SetPosition'})
    def test_cleanup_failure_stops_controller(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)/'source';root.mkdir();out=Path(folder)/'out'
            good=lambda output:dict(output=output,failure=None,exit_code=0)
            with patch.object(run.sys,'argv',['controller',str(root),str(out)]), patch.dict(run.os.environ,{'TOOLING_SHA':'a'*40}), patch.object(run.c,'snapshot',return_value={}), patch.object(run.shutil,'which',return_value='docker'), patch.object(run.c,'run_command',side_effect=[good(run.c.SOURCE),good('pulled'),good('10.0.6')]) as command, patch.object(run.c,'cleanup_owned',side_effect=ValueError('cleanup failure')):
                self.assertEqual(run.main(),1)
            self.assertEqual(command.call_count,3)
            self.assertEqual(json.loads((out/'receipt.json').read_text())['status'],'FAILED')
            self.assertFalse((out/'topology.json').exists())
    def stage(self,mode,extra=False):
        w=json.loads((Path(__file__).resolve().parents[2]/'.github/workflows/osc-candidate-check.yml').read_text())
        code=next(iter(w['jobs'].values()))['steps'][-2]['run'].split('\n',1)[1].rsplit('\nPY',1)[0]
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder);Path('receipts').mkdir();Path('receipts/receipt.json').write_text('{}')
                Path('topology-receipts').mkdir();Path('topology-receipts/receipt.json').write_text('{}');Path('topology-receipts/topology.json').write_text('{}')
                if extra:Path('topology-receipts/board.kicad_pcb').write_text('forbidden')
                with patch.dict(os.environ,{'OSC_MODE':mode}):
                    if extra or mode!='topology':
                        with self.assertRaises(SystemExit):exec(compile(code,'artifact-stage','exec'),{})
                        self.assertEqual({p.name for p in Path('upload-safe').iterdir()},{'receipt.json'})
                    else:
                        exec(compile(code,'artifact-stage','exec'),{})
                        self.assertEqual({p.name for p in Path('upload-safe').iterdir()},{'receipt.json','topology.json'})
            finally:os.chdir(old)
    def test_topology_artifacts(self):self.stage('topology')
    def test_board_artifact_rejected(self):self.stage('topology',True)
    def test_topology_in_identity_rejected(self):self.stage('identity')
    def test_topology_in_smoke_rejected(self):self.stage('smoke')
    def test_smd_projected_overlap_not_shared_layer(self):
        p=Item('p','+12V');track=Item('t','AGND',('B.Cu',))
        self.assertEqual(t.contact_observation(p,track,'B.Cu'),{'shared_layer':False,'shape_intersection':False})
    def test_through_hole_contact_not_filtered_by_net(self):
        p=Item('p','+12V',('F.Cu','B.Cu'));track=Item('t','AGND',('B.Cu',))
        self.assertTrue(t.contact_observation(p,track,'B.Cu')['shape_intersection'])
    def test_same_layer_not_necessarily_intersection(self):
        self.assertFalse(t.contact_observation(Item('p','AGND',hit=False),Item('t','AGND'),'F.Cu')['shape_intersection'])
    def test_unsupported_result_rejected(self):
        with self.assertRaises(ValueError):t.contact_observation(Item('p','G',hit=(True,0)),Item('t','G'),'F.Cu')
    def test_net_identity_is_not_connectivity(self):
        b,p,_=fixture();r=t.observe(b,p);t.validate(r)
        self.assertFalse(any(x['b_reported_by_a'] for x in r['pairs']))
    def test_native_membership_only(self):
        b,p,_=fixture(True);r=t.observe(b,p)
        self.assertTrue(r['pairs'][0]['b_reported_by_a']);self.assertFalse(r['pairs'][0]['a_reported_by_b'])
        self.assertFalse(r['board_acceptance'])
    def test_identity_mismatch(self):
        b,p,pads=fixture();next(iter(pads.values())).net='OTHER'
        with self.assertRaises(ValueError):t.observe(b,p)
    def test_unsupported_api(self):
        b,p,_=fixture();b.GetConnectivity=lambda:object()
        with self.assertRaises(AttributeError):t.observe(b,p)
    def test_missing_zone(self):
        b,p,_=fixture();b.Zones=lambda:[]
        with self.assertRaises(ValueError):t.observe(b,p)
    def test_wiring_and_bounds(self):
        w=json.loads((Path(__file__).resolve().parents[2]/'.github/workflows/osc-candidate-check.yml').read_text())
        self.assertEqual(w['permissions'],{'contents':'read'})
        self.assertEqual(set(w['on']),{'workflow_dispatch'})
        j=next(iter(w['jobs'].values()));self.assertEqual(len(w['jobs']),1);self.assertEqual(j['timeout-minutes'],20)
        self.assertFalse(w['concurrency']['cancel-in-progress'])
        self.assertIn("inputs.mode == 'topology'",j['steps'][2]['with']['sparse-checkout'])
        self.assertIn('osc_topology_check.py frozen topology-receipts',j['steps'][4]['run'])
        self.assertIn('osc_frozen_topology.py',j['steps'][1]['with']['sparse-checkout'])
        self.assertIn('upload-safe/topology.json',j['steps'][-1]['with']['path'])
        self.assertEqual(j['steps'][-1]['with']['retention-days'],7)

if __name__=='__main__':unittest.main()
