"""Source graph and exact-boundary regressions; no saved-board routing or native."""
import copy
from types import SimpleNamespace
import unittest
import numpy as np

import analyze_f3_breakout_region as region
import f3_adapter as adapter
from test_f3_breakout import fixture
from test_f3_adapter import BUDGET
from test_exact_access import pad


def graph():
    free=np.zeros((2,5,8),bool)
    free[0,2,1:3]=True;free[1,2,1:4]=True;free[1,2,6]=True
    src=np.zeros_like(free);src[0,2,1]=True
    goal=np.zeros_like(free);goal[1,2,6]=True
    return {'free':free,'via':np.zeros((5,8),bool),'src':src,'goal':goal,
            'raster':SimpleNamespace(layers=['B.Cu','In2.Cu']),'window':[0,5,0,8]}


class RegionTests(unittest.TestCase):
    def test_legal_local_seed_can_still_be_isolated_from_goal(self):
        before=graph();after=copy.deepcopy(before);after['src'][1,2,1]=True
        # Use a different x to avoid a synthetic all-layer through source in this toy.
        after['src'][1,2,1]=False;after['src'][1,2,2]=True
        summary,masks=region.compare(before,after,(1,2,2))
        self.assertEqual(summary['new_seed_only']['reachable_nodes'],3)
        self.assertEqual(summary['combined_after']['reachable_nodes'],5)
        self.assertEqual(summary['new_seed_only']['goal_nodes_reached'],0)
        self.assertEqual(summary['old_sources_on_repaired_graph'],summary['before'])
        self.assertFalse(summary['new_seed_only']['touches_window_edge'])

    def test_rejects_window_obstacle_goal_and_source_drift(self):
        before=graph();base=copy.deepcopy(before);base['src'][1,2,2]=True
        for mutation in ('window','free','via','goal','old_source','extra_seed'):
            after=copy.deepcopy(base)
            if mutation=='window':after['window'][0]=1
            elif mutation in ('free','goal'):after[mutation][1,1,1]=True
            elif mutation=='via':after['via'][1,1]=True
            elif mutation=='old_source':after['src'][0,2,1]=False
            else:after['src'][1,1,1]=True
            with self.assertRaises(ValueError):region.compare(before,after,(1,2,2))

    def test_goal_reachability_is_reported_when_real_corridor_exists(self):
        before=graph();before['free'][1,2,1:7]=True
        after=copy.deepcopy(before);after['src'][1,2,2]=True
        summary,_=region.compare(before,after,(1,2,2))
        self.assertEqual(summary['before']['goal_nodes_reached'],0)
        self.assertEqual(summary['new_seed_only']['goal_nodes_reached'],1)

    def test_no_corner_cut_or_layer_switch_without_permission(self):
        before=graph();before['free'][1,3,4]=True
        after=copy.deepcopy(before);after['src'][1,2,2]=True
        summary,_=region.compare(before,after,(1,2,2))
        self.assertEqual(summary['new_seed_only']['reachable_nodes'],3)
        before['via'][2,2]=True;after['via'][2,2]=True
        summary,_=region.compare(before,after,(1,2,2))
        self.assertEqual(summary['new_seed_only']['reachable_nodes'],5)

    def test_exact_clear_boundary_does_not_override_raster_and_extra_via_spacing(self):
        original,domain,pool,card=fixture()
        r=adapter.grid.Raster(original,.1,bounds_mm=domain['common_bounds_mm'])
        y,x=r.cell(*card['via_nm']);li=r.layers.index('In2.Cu')
        # Synthetic conservative raster veto; exact original geometry stays clear.
        r.d_keep_track[li].fill(0)
        saved={'raster':r,'window':[y-1,y+2,x-1,x+2],'via':np.zeros((3,3),bool)}
        reached=np.zeros((len(r.layers),3,3),bool);reached[li,1,1]=True
        report=region.exact_region(original,card,{'budget':BUDGET},saved,reached)
        self.assertEqual(report['boundary_exact_pass'],4)
        self.assertEqual(report['original_exact_via_sites'],1)
        self.assertEqual(report['distinct_exact_vias_after_breakout'],0)
        self.assertFalse(report['via_checks'][0]['raster_via_ok'])
        self.assertEqual(int(reached.sum()),1)

    def test_exact_invalid_internal_edge_fails_claim_closed(self):
        original,domain,pool,card=fixture()
        original['pads'].append(pad('blocker','OTHER',18,10,layer='In2.Cu',half=.1))
        r=adapter.grid.Raster(original,.1,bounds_mm=domain['common_bounds_mm'])
        y,x=r.cell(*card['via_nm']);li=r.layers.index('In2.Cu')
        saved={'raster':r,'window':[y-1,y+2,x-1,x+2],'via':np.zeros((3,3),bool)}
        reached=np.zeros((len(r.layers),3,3),bool);reached[li,1,1:3]=True
        with self.assertRaisesRegex(ValueError,'exact-invalid internal'):
            region.exact_region(original,card,{'budget':BUDGET},saved,reached)


if __name__=='__main__':unittest.main()
