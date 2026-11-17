import copy
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import study as s


def footprint(ref='U4524'):
    return {'ref':ref,'side':'B','origin':[.5,.5],'angle':0,'courtyard':[0,0,1,1],
            'pads':[{'bbox':[0,0,1,1],'type':'smd'}]}


def scene(bodies=(), links=(), inside=True):
    idx={('K',f):s.sg.RectIndex() for f in 'FB'}
    for ref in bodies:idx['K','B'].add([0,0,1,1],('body',('K',ref),'courtyard'))
    link=s.sg.RectIndex()
    for label in links:link.add([0,0,1,1],label)
    field=SimpleNamespace(idx=idx,links={('K','B'):link},gap=.35,pad_gap=.35,margin=.3)
    src=SimpleNamespace(field=field,model=SimpleNamespace(inside=lambda *args:inside))
    return s.DiagnosticScene(src,{('K','C4544')},{('K','U4524'),('K','U4526'),('K','U4527')},{('K','J_FIXED')})


class AttributionTests(unittest.TestCase):
    def test_all_simultaneous_blockers_and_self_only_exclusion(self):
        d=scene(('U4524','U4526','U4527','C4544','R_STATIONARY','J_FIXED'),('slot of L06','K field of L06'))
        d.scene.field.idx['K','B'].add([-1,-1,1,1],('circle',(.5,.5,.5),'fixing keep-out FIX'))
        before=copy.deepcopy(d.scene.field.idx['K','B'].items)
        ids=d.blockers('K',footprint(),0,0);rows=[d.registry[k] for k in ids]
        self.assertEqual({r.get('ref') for r in rows if 'ref' in r},{'U4526','U4527','C4544','R_STATIONARY','J_FIXED'})
        self.assertEqual({r['class'] for r in rows},{'unresolved_body','accepted_body','stationary_body','fixed_hardware','fixed_slot','fixed_link_field','fixed_fixing'})
        self.assertEqual(d.scene.field.idx['K','B'].items,before)
        self.assertIsNone(s.accepted_only_obstruction(ids,d.registry))
    def test_fixed_hardware_never_exchange_candidate_even_if_accepted(self):
        kind,mobility=s.body_category(('K','POT'),{('K','POT')},set(),{('K','POT')})
        self.assertEqual((kind,mobility),('fixed_hardware','FIXED_NONEXCHANGEABLE'))
    def test_stationary_and_accepted_movability_remain_unknown(self):
        for ref in ('R_STATIONARY','C4544'):
            d=scene((ref,));ids=d.blockers('K',footprint(),0,0)
            self.assertTrue(all(d.registry[k]['movability'].startswith('UNKNOWN') for k in ids))
    def test_named_accepted_attribution_is_not_selected_placement(self):
        d=scene(('C4544',));result=s.audit(d,[footprint()],[(0,0,0)])
        self.assertEqual(result['diagnostic_points'][0]['all_obstructions_are_named_accepted_bodies'],['C4544'])
        self.assertEqual(result['selected_placements'],[]);self.assertEqual(result['adopted_placements'],[])
        self.assertNotIn('positions',result)
    def test_empty_hits_are_not_claimed_accepted_removal_opportunity(self):
        d=scene();ids=d.blockers('K',footprint(),0,0)
        self.assertEqual(ids,[]);self.assertIsNone(s.accepted_only_obstruction(ids,d.registry))
    def test_fixed_tail_latch_outline_are_not_body_exchange(self):
        d=scene(links=('front tail of L06','latch margin of L06'),inside=False)
        ids=d.blockers('K',footprint(),0,0)
        self.assertEqual({d.registry[k]['class'] for k in ids},{'fixed_tail','fixed_latch','fixed_outline'})
        self.assertIsNone(s.accepted_only_obstruction(ids,d.registry))
    def test_unknown_target_or_unbounded_offset_rejected(self):
        d=scene()
        for fp,dx,dy in ((footprint('OTHER'),0,0),(footprint(),26,0),(footprint(),float('nan'),0)):
            with self.assertRaises(ValueError):d.blockers('K',fp,dx,dy)
    def test_obstacle_rounding_preserves_retained_boundary(self):
        self.assertEqual(s.r1.obstacle_rect([0,0,1,1],.35),[-.35,-.35,1.35,1.35])
        d=scene(('C4544',))
        # Retained intersection predicate treats exact touching as non-overlap.
        self.assertEqual(d.blockers('K',footprint(),1,0),[])
    def test_mutiple_diagnostic_queries_never_move_any_body(self):
        d=scene(('U4526','C4544'));fp=footprint();old=copy.deepcopy(fp)
        result=s.audit(d,[fp],[(0,0,0),(.25,.25,0)])
        self.assertEqual(fp,old);self.assertEqual(len(result['diagnostic_points']),2)
        self.assertEqual(result['selected_placements'],[])
    def test_stale_dependency_pin(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'input').write_text('changed')
            with self.assertRaises(ValueError):s.r1.verify_pins(root,{'sha256':{'input':'0'*64}})
    def test_existing_and_symlink_output_do_not_consume_analysis(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);cache=root/'.circuit-cache';cache.mkdir();target=cache/'out';target.write_text('preserve');link=cache/'dangling';link.symlink_to(cache/'missing')
            for p in (target,link):
                with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run') as run,contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):s.main(['--output',str(p)])
                    run.assert_not_called()
            self.assertEqual(target.read_text(),'preserve')
    def test_racing_output_creator_does_not_consume_analysis(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=root/'.circuit-cache/out';original=Path.open
            def racing(path,mode='r',*args,**kwargs):
                if path==target and mode=='x':
                    with original(path,'w') as stream:stream.write('other writer')
                return original(path,mode,*args,**kwargs)
            with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run') as run,mock.patch.object(Path,'open',racing):
                with self.assertRaises(FileExistsError):s.main(['--output',str(target)])
                run.assert_not_called()
            self.assertEqual(target.read_text(),'other writer')
    def test_failure_receipt_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=root/'.circuit-cache/out'
            with mock.patch.object(s,'ROOT',root),mock.patch.object(s,'run',side_effect=ValueError('fixture')):
                with self.assertRaisesRegex(ValueError,'fixture'):s.main(['--output',str(target)])
            self.assertEqual(json.loads(target.read_text())['status'],'ADMISSION_OR_EXECUTION_FAILED')


if __name__=='__main__':unittest.main()
