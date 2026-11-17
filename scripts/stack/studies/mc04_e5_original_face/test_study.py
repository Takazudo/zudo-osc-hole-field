import copy
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
import study as s


def body(ref,x=0,y=0):
    return {'ref':ref,'side':s.FACES[ref],'angle':s.ANGLES[ref],'origin':[x,y],
            'courtyard':[x,y,x+1,y+1],'pads':[{'bbox':[x,y,x+1,y+1],'center':[x+.5,y+.5],'type':'smd'}]}


def scene(blocked=None):
    observed=[]
    def violations(board,fp,dx,dy,exclude):
        observed.append((fp['ref'],fp['side'],set(exclude)))
        return ['frozen'] if blocked and blocked(fp,dx,dy) else []
    return SimpleNamespace(field=SimpleNamespace(gap=.35),_violations=violations,observed=observed)


def prior_fixture():
    rows=[]
    for index,(radius,dx,dy) in list(enumerate(s.rp.ring_offsets(.25,24,25)))[1:46]:
        rows.append({'offset_index':index,'radius_mm':radius,'shift_from_accepted_mm':[dx,dy],
                     'shift_from_original_mm':[dx,dy],'blockers':[],'disposition':'INDIVIDUAL_ROOM_ONLY'})
    return {'status':'NO_INDIVIDUAL_ROOM_FOR_EXCHANGE','pair_checks':0,'individual_tests':{'R4577':rows}},copy.deepcopy(rows)


class OriginalFaceTests(unittest.TestCase):
    def test_smd_mutual_predicate_distinguishes_opposite_and_same_faces(self):
        self.assertFalse(s.ex.mutual(body('U4517'),body('U4527'),.35))
        self.assertTrue(s.ex.mutual(body('R4577'),body('U4527'),.35))

    def test_annulus_exact_finite_domain_excludes_old12mm(self):
        domain=s.original_domain()
        self.assertEqual(len(domain),1248);self.assertEqual((domain[0][0],domain[-1][0]),(1153,2400))
        self.assertEqual(min(p[1][0] for p in domain),12.25);self.assertEqual(max(p[1][0] for p in domain),25)
        self.assertEqual(len({p[0] for p in domain}),1248)

    def test_source_geometry_binding_is_actual_F_not_B_relabel(self):
        spec=json.loads(s.SPEC.read_text());relative=s.sg.BOARD_FILES['K']
        self.assertEqual(hashlib.sha256((s.ROOT/relative).read_bytes()).hexdigest(),spec['sha256'][relative])
        lock=json.loads((s.ROOT/'design/grid/placements.lock.json').read_text())['frame']['kicad_translation_mm']
        fps=s.sg.kicad_extract.parse_board(s.ROOT/relative,(lock['x'],lock['y']))
        actual=next(fp for fp in fps if fp['ref']=='U4517')
        self.assertEqual(actual,spec['original_U4517'])
        self.assertEqual((actual['side'],actual['angle'],actual['origin']),('F',0,[185.95,140.7]))
        flipped=copy.deepcopy(actual);flipped['side']='B'
        with self.assertRaisesRegex(ValueError,'actual original'):
            s.original_candidates(scene(),flipped,actual['origin'],body('U4527',100,100),[])

    def test_original_and_accepted_displacement_both_required(self):
        candidates,records=s.original_candidates(scene(),body('U4517'),[6.5,0],body('U4527',100,100),
            [(1,(12.25,12.25,0)),(2,(25,-25,0)),(3,(25,25.0001,0))])
        self.assertEqual([c['offset_index'] for c in candidates],[1])
        self.assertTrue(all(r['disposition']=='FILTERED_DISPLACEMENT_BOUND' for r in records[1:]))

    def test_face_angle_and_exact_exclusion_guard(self):
        for ref in s.FACES:
            fp=body(ref);fp['angle']+=90
            with self.assertRaises(ValueError):s.fixed_hits(scene(),fp)
        with self.assertRaisesRegex(ValueError,'exact three'):
            s.fixed_hits(scene(),body('U4517'),excluded=s.ex.KEYS|{('K','C4534')})

    def test_opposite_face_hits_are_still_forwarded_to_scene(self):
        sc=scene(lambda f,dx,dy:f['side']=='F')
        eligible,records=s.original_candidates(sc,body('U4517'),[0,0],body('U4527',100,100),[(1153,(12.25,12.25,0))])
        self.assertEqual(eligible,[]);self.assertEqual(records[0]['blockers'],['frozen'])
        self.assertEqual(sc.observed[0],('U4517','F',s.ex.KEYS))

    def test_prior45_reused_without_new_resistor_enumeration(self):
        receipt,rows=prior_fixture();sc=scene();before=copy.deepcopy(receipt)
        candidates=s.retained_resistor_candidates(sc,body('R4577'),[0,0],body('U4527',100,100),receipt,rows)
        self.assertEqual(len(candidates),45);self.assertEqual(len(sc.observed),45);self.assertEqual(receipt,before)
        self.assertEqual([c['offset_index'] for c in candidates],list(range(1,46)))

    def test_changed_prior_offset_or_failed_revalidation_stops(self):
        receipt,rows=prior_fixture();receipt['individual_tests']['R4577'][0]['shift_from_accepted_mm'][0]+=.1
        with self.assertRaisesRegex(ValueError,'exact prior45|exact prior 45'):
            s.retained_resistor_candidates(scene(),body('R4577'),[0,0],body('U4527',100,100),receipt,rows)
        receipt,rows=prior_fixture()
        with self.assertRaisesRegex(ValueError,'does not revalidate'):
            s.retained_resistor_candidates(scene(lambda *a:True),body('R4577'),[0,0],body('U4527',100,100),receipt,rows)

    def test_pair_caps_and_all_three_final_validation(self):
        left=[{'offset_index':1153,'geometry':body('U4517')}]
        right=[{'offset_index':3,'geometry':body('R4577',4,0)}]
        sc=scene();r=s.pair_search(sc,body('U4527',100,100),left,right)
        self.assertEqual(r['status'],'ORIGINAL_FACE_ROOM_WITNESS_ONLY')
        self.assertEqual({x[0] for x in sc.observed},set(s.FACES))
        self.assertEqual(r['witness_ring_indices'],[1153,3])
        with self.assertRaisesRegex(ValueError,'cap'):s.pair_search(sc,body('U4527'),left,right,cap=56161)
        with self.assertRaisesRegex(ValueError,'frozen'):
            s.validate_final(scene(lambda f,*args:f['ref']=='R4577'),[body('U4517'),body('R4577',4),body('U4527',100)])

    def test_pair_cap_distinct_from_exhaustion(self):
        left=[{'offset_index':1,'geometry':body('U4517')}]
        right=[{'offset_index':2,'geometry':body('R4577')},{'offset_index':3,'geometry':body('R4577')}]
        with mock.patch.object(s.ex,'mutual',return_value=True):
            self.assertEqual(s.pair_search(scene(),body('U4527'),left,right,cap=1)['status'],'ORIGINAL_FACE_SEARCH_CAP_REACHED')
            self.assertEqual(s.pair_search(scene(),body('U4527'),left,right,cap=2)['status'],'NO_ORIGINAL_FACE_PAIR_FIT')

    def test_output_reserved_before_analysis_and_failure_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'.circuit-cache/out';target.parent.mkdir();target.write_text('keep')
            with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run') as run,contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):s.main(['--output',str(target)])
                run.assert_not_called()
            failure=target.with_name('failure')
            with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run',side_effect=ValueError('pin')):
                with self.assertRaises(ValueError):s.main(['--output',str(failure)])
            self.assertEqual(json.loads(failure.read_text())['status'],'ADMISSION_OR_EXECUTION_FAILED')


if __name__=='__main__':unittest.main()
