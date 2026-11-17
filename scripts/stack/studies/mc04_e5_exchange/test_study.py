import copy
import contextlib
import io
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import study as s


def fp(ref,x=0,y=0):
    return {'ref':ref,'origin':[x,y],'side':'B','angle':90 if ref=='R4577' else 0,
            'courtyard':[x,y,x+1,y+1],'pads':[{'bbox':[x,y,x+1,y+1],'center':[x+.5,y+.5],'type':'smd'}]}


def scene(blocked=None):
    observed=[]
    def violations(board,body,dx,dy,excluded):
        observed.append((body['ref'],excluded))
        return ['frozen obstruction'] if blocked and blocked(body,dx,dy) else []
    return SimpleNamespace(field=SimpleNamespace(gap=.35),_violations=violations,observed=observed)


class ExchangeTests(unittest.TestCase):
    def test_all_seven_frozen_anchors_match_actual_source_representation(self):
        spec=json.loads(s.SPEC.read_text())
        board_path='boards/osc-core/osc-core.kicad_pcb'
        lock_path='design/grid/placements.lock.json'
        for relative in (board_path,lock_path,'scripts/stack/studies/mc04_r1/spec.json'):
            self.assertEqual(hashlib.sha256((s.ROOT/relative).read_bytes()).hexdigest(),spec['sha256'][relative])
        translation=json.loads((s.ROOT/lock_path).read_text())['frame']['kicad_translation_mm']
        parsed=s.sg.kicad_extract.parse_board(s.ROOT/board_path,(translation['x'],translation['y']))
        frozen=json.loads((s.ROOT/'scripts/stack/studies/mc04_r1/spec.json').read_text())
        rows=[r for r in frozen['replacement'] if r['board']=='K']
        boards,accepted=s.r1.reconstruct({'K':parsed},rows,rows)
        bodies={fp['ref']:fp for fp in boards['K']}
        self.assertEqual(len(spec['frozen_geometry']),7)
        for ref,expected in spec['frozen_geometry'].items():
            actual=bodies[ref]
            with self.subTest(ref=ref):
                self.assertEqual((actual['origin'],actual['side'],actual['angle']),
                                 (expected['origin'],expected['face'],expected['angle']))
        self.assertEqual(bodies['C4534']['angle'],-90)
        self.assertNotEqual(bodies['C4534']['angle'],270)
        self.assertIn(('K','C4544'),accepted)
        self.assertEqual(bodies['C4544']['origin'],[189.2026,136.8974])
        self.assertEqual((bodies['C4544']['side'],bodies['C4544']['angle']),('B',90))

    def test_displacement_inclusive_and_no_tolerance_expansion(self):
        self.assertTrue(s.within25([25,0]));self.assertTrue(s.within25([15,20]))
        self.assertFalse(s.within25([25.0001,0]));self.assertFalse(s.within25([float('nan'),0]))
    def test_current_and_total_original_displacement_are_both_required(self):
        sc=scene();body=fp('U4517',10,0);probe=fp('U4527',100,100)
        eligible,tests=s.candidates(sc,body,[0,0],probe,[(0,0,0),(16,16,0),(15,15,0),(25,25,0)])
        self.assertEqual([r['offset_index'] for r in eligible],[0,2])
        self.assertEqual(tests[1]['disposition'],'FILTERED_DISPLACEMENT_BOUND')
        self.assertEqual(tests[3]['disposition'],'FILTERED_DISPLACEMENT_BOUND')
        self.assertEqual(len(sc.observed),2)
    def test_individual_domain_cap(self):
        with self.assertRaisesRegex(ValueError,'enumeration cap'):
            s.candidates(scene(),fp('U4517'),[0,0],fp('U4527',100,100),[(0,0,0)]*2402)
    def test_only_exact_three_removed_and_companions_stay_fixed(self):
        sc=scene(lambda body,dx,dy:True)
        self.assertEqual(s.fixed_hits(sc,fp('U4517')),['frozen obstruction'])
        self.assertEqual(sc.observed[0][1],{('K','U4517'),('K','U4527'),('K','R4577')})
        with self.assertRaisesRegex(ValueError,'exact three'):s.fixed_hits(sc,fp('U4517'),excluded=s.KEYS|{('K','C4534')})
        with self.assertRaisesRegex(ValueError,'identity or face'):s.fixed_hits(sc,fp('C4544'))
    def test_original_orientation_and_complete_pads_are_preserved(self):
        body=fp('R4577');old=copy.deepcopy(body);moved=s.translate(body,1.25,-.5)
        self.assertEqual(body,old);self.assertEqual(moved['angle'],90);self.assertEqual(moved['side'],'B')
        self.assertEqual(moved['pads'][0]['bbox'],[1.25,-.5,2.25,.5])
    def test_pad_beyond_courtyard_is_a_mutual_obstacle(self):
        a=fp('U4517');b=fp('R4577',4,0);a['pads'][0]['bbox']=[4,0,5,1]
        self.assertTrue(s.mutual(a,b,.35))
    def test_fixed_probe_is_not_ignored_during_individual_enumeration(self):
        eligible,tests=s.candidates(scene(),fp('U4517'),[0,0],fp('U4527'),[(0,0,0)])
        self.assertEqual(eligible,[]);self.assertIn('fixed U4527 probe',tests[0]['blockers'])
    def test_pair_cap_is_not_exhaustion_or_no_fit(self):
        a=[{'offset_index':1,'geometry':fp('U4517')}]
        b=[{'offset_index':i,'geometry':fp('R4577')} for i in (2,3)]
        r=s.pair_search(scene(),fp('U4527',100,100),a,b,cap=1)
        self.assertEqual(r,{'status':'SEARCH_CAP_REACHED','pair_checks':1})
        r=s.pair_search(scene(),fp('U4527',100,100),a,b,cap=3)
        self.assertEqual(r,{'status':'NO_PAIR_FIT_IN_DECLARED_DOMAIN','pair_checks':2})
        # Exactly the full domain at the cap has no unexplored pair remaining.
        r=s.pair_search(scene(),fp('U4527',100,100),a,b,cap=2)
        self.assertEqual(r,{'status':'NO_PAIR_FIT_IN_DECLARED_DOMAIN','pair_checks':2})
    def test_pair_order_and_final_all_three_revalidation(self):
        sc=scene();probe=fp('U4527',100,100)
        left=[{'offset_index':2,'geometry':fp('U4517')},{'offset_index':5,'geometry':fp('U4517',10,0)}]
        right=[{'offset_index':3,'geometry':fp('R4577')},{'offset_index':4,'geometry':fp('R4577',4,0)}]
        r=s.pair_search(sc,probe,left,right)
        self.assertEqual(r['witness_offset_indices'],[2,4]);self.assertEqual(r['pair_checks'],2)
        self.assertEqual({ref for ref,_ in sc.observed},set(s.MOVING))
    def test_final_validation_rejects_any_fixed_or_mutual_collision(self):
        bodies=[fp('U4527',100,100),fp('U4517'),fp('R4577',4,0)]
        for ref in s.MOVING:
            with self.assertRaisesRegex(ValueError,'frozen scene'):
                s.validate_final(scene(lambda body,dx,dy:body['ref']==ref),bodies)
        with self.assertRaisesRegex(ValueError,'mutual'):
            s.validate_final(scene(),[fp('U4527'),fp('U4517'),fp('R4577',4,0)])
    def test_ledger_preserves45_and_marks_one_movable(self):
        report={'physical_packages':[{'ref':'R4577','mpn':''}],'package_units':[]}
        expected={'refs':['R4577'],'rows':copy.deepcopy(report)}
        old={'RISE':[{'ref':'U4517','unit':4,'pin':'12','role':'NAND23'}]+[{'ref':'FROZEN'+str(i),'unit':1,'pin':'1','role':'fixture'} for i in range(44)]}
        r=s.ledger(report,old,expected)
        self.assertEqual(len(r['original_45_contacts']),45);self.assertEqual(r['original_frozen_contacts'],44)
        self.assertEqual(r['R4577_MPN'],'')
        old['RISE'].pop()
        with self.assertRaisesRegex(ValueError,'45-contact'):s.ledger(report,old,expected)
    def test_changed_mpn_cannot_be_adopted(self):
        report={'physical_packages':[{'ref':'R4577','mpn':'new'}],'package_units':[]}
        with self.assertRaisesRegex(ValueError,'remain blank'):
            s.ledger(report,{}, {'refs':['R4577'],'rows':report})
    def test_diagnostic_unique_point_and_blockers_are_frozen(self):
        point={'target':'U4527','offset_index':214,'radius_mm':2.25,'diagnostic_offset_mm':[1.591,-1.591],
               'all_obstructions_are_named_accepted_bodies':['R4577','U4517'],'blocker_ids':[str(i) for i in range(16)]}
        empty={'all_obstructions_are_named_accepted_bodies':None}
        receipt={'diagnostic_points':[point]+[empty]*7202,
                 'blockers':{str(i):{'class':'accepted_body','ref':'R4577' if i%2 else 'U4517'} for i in range(16)}}
        self.assertEqual(s.validate_diagnostic(receipt),point)
        point['diagnostic_offset_mm']=[1.591,1.591]
        with self.assertRaisesRegex(ValueError,'point changed'):s.validate_diagnostic(receipt)
        point['diagnostic_offset_mm']=[1.591,-1.591];receipt['blockers']['0']['ref']='C4544'
        with self.assertRaisesRegex(ValueError,'attribution changed'):s.validate_diagnostic(receipt)

    def test_existing_and_dangling_output_do_not_run(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cache=root/'.circuit-cache';cache.mkdir();f=cache/'old';f.write_text('old');link=cache/'link';link.symlink_to(cache/'missing')
            for p in (f,link):
                with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run') as run,contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):s.main(['--output',str(p)])
                    run.assert_not_called()
    def test_racing_output_creator_does_not_run(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=root/'.circuit-cache/out';original=Path.open
            def race(path,mode='r',*args,**kwargs):
                if path==target and mode=='x':
                    with original(path,'w') as stream:stream.write('other')
                return original(path,mode,*args,**kwargs)
            with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run') as run,mock.patch.object(Path,'open',race):
                with self.assertRaises(FileExistsError):s.main(['--output',str(target)])
                run.assert_not_called()
    def test_cli_exit_status_whitelist_and_receipt(self):
        for status,expected in [('SOURCE_OR_PREDICATE_MISMATCH',1),('UNKNOWN_FUTURE_FAILURE',1),
                                ('ROOM_EXCHANGE_WITNESS_ONLY',0),('NO_INDIVIDUAL_ROOM_FOR_EXCHANGE',0),
                                ('NO_PAIR_FIT_IN_DECLARED_DOMAIN',0),('SEARCH_CAP_REACHED',0)]:
            with tempfile.TemporaryDirectory() as d:
                root=Path(d);target=root/'.circuit-cache/result.json'
                with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run',return_value={'status':status}),contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(s.main(['--output',str(target)]),expected)
                self.assertEqual(json.loads(target.read_text())['status'],status)

    def test_failure_receipt_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=root/'.circuit-cache/out'
            with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run',side_effect=ValueError('fixture')):
                with self.assertRaises(ValueError):s.main(['--output',str(target)])
            self.assertEqual(json.loads(target.read_text())['status'],'ADMISSION_OR_EXECUTION_FAILED')


if __name__=='__main__':unittest.main()
