import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import contextlib
import io
from types import SimpleNamespace

import study as s


def body(ref, x, y=0):
    rect = [x, y, x+1, y+1]
    return {'ref': ref, 'side': 'B', 'origin': [x+.5, y+.5], 'angle': 0, 'lib': 'fixture',
            'courtyard': rect, 'pads': [{'bbox': rect, 'type': 'smd'}]}


def scene(pair, extra=()):
    obj = s.Scene.__new__(s.Scene)
    obj.model = SimpleNamespace(inside=lambda b,r,m: s.sg.inside(r, [-50,-50,50,50]))
    obj.field = SimpleNamespace(gap=0, pad_gap=0, margin=0, links={},
                               idx={('K',f):s.sg.RectIndex() for f in 'FB'})
    for fp in list(pair)+list(extra):
        obj.field.idx['K',fp['side']].add(fp['courtyard'], ('body',('K',fp['ref']),'footprint'))
    return obj


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.pair=[body('U4324',0), body('C4341',2)]
        self.scene=scene(self.pair)

    def test_new_freedom_then_rigid_witness(self):
        result=s.search(self.scene,self.pair,[(2,2,0)])
        self.assertEqual(result['status'],'ROOM_WITNESS_ONLY')
        self.assertEqual(result['group_count'],1)

    def test_no_new_opportunity_never_group_search(self):
        result=s.search(self.scene,self.pair,[(1,-1,0)])
        self.assertEqual(result['status'],'NO_NEW_OPPORTUNITY')
        self.assertEqual(result['group_count'],0)

    def test_ic_fit_capacitor_fails(self):
        result=s.search(scene(self.pair,[body('fixed',4)]),self.pair,[(2,2,0)])
        self.assertEqual(result['status'],'NO_RIGID_PAIR_FIT')

    def test_unrelated_obstacle_cannot_be_removed(self):
        with self.assertRaises(s.AdmissionError):
            self.scene.violations(self.pair[0],0,0,('U4324','other'))

    def test_displacement_cap(self):
        with self.assertRaises(s.AdmissionError):
            s.search(self.scene,self.pair,[(25,25.1,0)])
        self.assertIn('displacement cap',self.scene.violations(self.pair[1],26,0,s.PAIR))

    def test_slot(self):
        ix=s.sg.RectIndex(); ix.add([2,0,3,1],'slot of fixture')
        self.scene.field.links['K','B']=ix
        self.assertIn('slot of fixture',self.scene.violations(self.pair[0],2,0,s.PAIR))

    def test_fixing(self):
        self.scene.field.idx['K','B'].add([1,-1,4,2],('circle',(2.5,.5,1),'fixing fixture'))
        self.assertIn('fixing fixture',self.scene.violations(self.pair[0],2,0,s.PAIR))

    def test_outline_and_full_pad(self):
        self.pair[0]['pads'][0]['bbox']=[49,0,51,1]
        self.assertIn('outline',self.scene.violations(self.pair[0],0,0,s.PAIR))

    def test_pair_mutual_conflict(self):
        self.pair[1]=body('C4341',.5)
        self.assertEqual(s.search(self.scene,self.pair,[])['status'],'INCONSISTENT_PAIR')

    def test_wrong_pair(self):
        self.pair[1]['ref']='C000'
        with self.assertRaises(s.AdmissionError): s.search(self.scene,self.pair,[])

    def test_wrong_association_and_pin_net(self):
        spec=json.loads(s.SPEC.read_text())
        for key in ('physical_packages','package_units'):
            report=copy.deepcopy(spec['identity'])
            if key=='physical_packages':
                next(r for r in report[key] if r['ref']=='C4341')['decouples_ref']='U000'
            else:
                report[key][0]['pins']['1']='wrong'
            with self.assertRaises(s.AdmissionError): s.verify_identity(report,spec['identity'])

    def test_stale_pin(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'in').write_text('changed')
            with self.assertRaises(s.AdmissionError): s.verify_pins(root,{'sha256':{'in':'0'*64}})

    def test_missing_accepted_move(self):
        with self.assertRaises(s.AdmissionError): s.reconstruct({},[],[{'ref':'required'}])

    def test_reconstruction_frozen_unresolved_and_transform(self):
        fp=body('fixed',0)
        row={'board':'K','ref':'fixed','old':fp['origin'],'face':'B','package':'fixture',
             'new':[2.5,.5],'shift_mm':[2,0],'turned':False,'new_face':'B','new_courtyard':[2,0,3,1]}
        out,accepted=s.reconstruct({'K':[fp,self.pair[1]]},[row],[row])
        self.assertEqual(out['K'][1],self.pair[1]);self.assertEqual(accepted,[('K','fixed')])
        self.assertEqual(out['K'][0]['pads'][0]['bbox'],[2,0,3,1])
        self.assertEqual(fp['origin'],[.5,.5])

    def test_duplicate_nonfinite_invalid_geometry(self):
        for fps in ([self.pair[0],self.pair[0]], [body('bad',float('nan'))], [body('bad',float('inf'))]):
            with self.assertRaises(s.AdmissionError):s.reconstruct({'K':fps},[],[])

    def test_complete_scene_construction_retains_union(self):
        accepted=body('accepted',0)
        # Asymmetric pad makes rotation and face reconstruction observable.
        accepted['pads'][0]['bbox']=[0,.1,.2,.4]
        accepted['angle']=30
        row={'board':'K','ref':'accepted','old':accepted['origin'],'face':'B','package':'fixture',
             'new':[3.5,.5],'shift_mm':[3,0],'turned':True,'new_face':'F','new_courtyard':[3,0,4,1]}
        frozen=body('unresolved',8)
        stationary=body('stationary',12)
        stationary['pads'][0]['bbox']=[15,0,16,1]  # outside courtyard
        th=body('th',20)
        th['pads'][0]['type']='thru_hole'
        th['pads'][0]['drill']=.5
        th['pads'][0]['center']=[20.5,.5]
        boards={b:[] for b in s.rp.SCOPE_BOARDS}
        boards['K']=[accepted,frozen,stationary,th]
        boards,moves=s.reconstruct(boards,[row],[row])
        self.assertEqual(boards['K'][0]['angle'],300)
        self.assertEqual(boards['K'][0]['pads'][0]['bbox'],[3.6,0,3.9,.2])
        model=SimpleNamespace(dropped={},margin=0,
            forb={(b,f):s.sg.RectIndex() for b in s.rp.SCOPE_BOARDS for f in 'FB'},
            inside=lambda b,r,m:True)
        om={'own_face_courtyard_growth_mm':.1,'opposite_face_through_hole_pad_growth_mm':.2,
            'hole_growth_mm':.3}
        inp={'ci':{'boards':boards,'parameters':{'obstacle_model':om}}}
        built=s.Scene(SimpleNamespace(model=model,opts={'latch_access_margin_mm':0}),inp,[])
        def hits(face,rect):
            return {p[1][1] for r,p in built.field.idx['K',face].near(rect)
                    if p[0]=='body' and s.sg.inter(r,rect)}
        self.assertIn('accepted',hits('F',[3.2,.2,3.3,.3]))
        self.assertNotIn('accepted',hits('B',[.2,.2,.3,.3]))
        self.assertIn('unresolved',hits('B',[8.2,.2,8.3,.3]))
        self.assertIn('stationary',hits('B',[15.2,.2,15.3,.3]))
        self.assertIn('th',hits('F',[20.2,.2,20.3,.3]))
        # The named unresolved ledger binds original complete geometry to source pins.
        unresolved={'board':'K','ref':'unresolved','new':None}
        spec={'engineering_commit':'fixture','sha256':{
            'design/stack/geometry/links/link-gate.json':'links',s.sg.BOARD_FILES['K']:'board'}}
        ledger=s.liability_ledger(built,[row,unresolved],spec)
        self.assertEqual(ledger[0]['geometry'],frozen)
        self.assertEqual(ledger[0]['disposition'],'frozen unresolved obstacle')
        self.assertEqual(ledger[0]['provenance']['source_board_sha256'],'board')

    def test_existing_output_does_not_run_geometry(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); output=root/'.circuit-cache/result.json'
            output.parent.mkdir();output.write_text('preserve')
            with patch.object(s,'ROOT',root), patch.object(s,'run') as run, \
                    patch('sys.argv',['study.py','--output',str(output)]), \
                    contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):s.main()
            run.assert_not_called()
            self.assertEqual(output.read_text(),'preserve')

    def test_original_rings_deterministic_bound(self):
        offsets=s.rp.ring_offsets(.25,24,25)
        self.assertEqual(len(offsets),2401)
        self.assertEqual(offsets[0],(0,0,0))
        self.assertTrue(all(r<=25 for r,x,y in offsets))
        self.assertEqual(sum(r<=12 for r,x,y in offsets),1153)


if __name__=='__main__': unittest.main()
