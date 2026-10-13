"""Exact foreign-raster escapes and atomic full-pair source candidates; no native."""
import collections
import copy
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np

import exact_transition_candidate as method
import f3_adapter as a
from test_exact_access import fixture
from test_f3_adapter import toy, BUDGET, POLICY


def gate(d=None,origin=(12000000,10000000)):
    g=method.ExactTransitions.__new__(method.ExactTransitions)
    g.original=d or fixture();g.geo=a.Geometry(g.original);g.b=BUDGET;g.net='N'
    g.r=SimpleNamespace(layers=['F.Cu','B.Cu'],point=lambda y,x:(origin[0]+x*100000,origin[1]+y*100000))
    g.shape=(2,5,10);g.y0=g.x0=0;g.hard=np.ones(g.shape,bool);g.foreign=np.zeros(g.shape,bool)
    g.saved={'free':np.zeros(g.shape,bool),'src':np.zeros(g.shape,bool),'goal':np.zeros(g.shape,bool),'via':np.zeros(g.shape[1:],bool)}
    g.cache={};g.via_cache={};g.exceptions={};g.failures=collections.Counter();g.exact_checks=0;g.max_edges=250000;g.started=time.monotonic();g.seconds=300
    return g


class ExactTransitionTests(unittest.TestCase):
    def test_foreign_false_exclusion_reuses_exact_sweep_and_is_symmetric(self):
        g=gate();left,right=(0,0,0),(0,0,1)
        self.assertTrue(g.edge(left,right));self.assertTrue(g.edge(right,left))
        self.assertEqual(g.exact_checks,1);self.assertEqual(len(g.exceptions),1)
        self.assertFalse(g.saved['free'].any())

    def test_clear_endpoints_but_colliding_midspan_refuses(self):
        d=fixture();d['vias']=[{'uuid':'midspan','net':'X','xy':[12050000,10400000],'diameter':2000,'drill':1000}]
        g=gate(d)
        for node in [(0,0,0),(0,0,1)]:self.assertTrue(g.geo.segment(g.point(node),g.point(node),'N','F.Cu',.3)['pass'])
        self.assertFalse(g.edge((0,0,0),(0,0,1)));self.assertFalse(g.exceptions)

    def test_east_retained_via_stays_exact_forbidden(self):
        d=fixture();d['edges']=[[0,0,300000000,0],[300000000,0,300000000,300000000],[300000000,300000000,0,300000000],[0,300000000,0,0]]
        d['vias']=[{'uuid':'9bc880ec-2717-59d4-98ee-1358bf13df02','net':'XB2476C897A43616D2B8F','xy':[217775000,263350000],'diameter':600000,'drill':300000}]
        g=gate(d,origin=(217000000,263300000))
        check=g.geo.segment([217,263.3],[217.1,263.3],'N','F.Cu',.3)
        self.assertAlmostEqual(check['checked_margins_mm']['foreign_copper'],-.023150681465943707)
        self.assertFalse(g.edge((0,0,0),(0,0,1)))

    def test_hard_raster_edge_keepout_bounds_and_corner_veto_are_preserved(self):
        g=gate();g.hard[0,0,1]=False
        self.assertFalse(g.edge((0,0,0),(0,0,1)))
        self.assertFalse(g.edge((0,0,0),(0,1,1)))
        self.assertFalse(g.edge((0,0,0),(0,-1,0)))
        self.assertFalse(g.edge((0,0,0),(1,0,0)))
        self.assertEqual(g.exact_checks,0)

    def test_exact_keepout_collision_refuses_even_if_raster_was_clear(self):
        d=fixture();d['keepouts']=[{'name':'real','poly':[[12000000,9900000],[12100000,9900000],[12100000,10100000],[12000000,10100000]],'tracks':True,'vias':True,'layers':['F.Cu']}]
        self.assertFalse(gate(d).edge((0,0,0),(0,0,1)))

    def test_no_new_via_permission_from_planar_exact_override(self):
        g=gate();self.assertTrue(g.edge((0,0,0),(0,0,1)))
        self.assertFalse(g.via((0,0,1),1))
        g.saved['via'][0,1]=True
        self.assertFalse(g.via((0,0,1),1))
        g.saved['free'][:,0,1]=True
        self.assertTrue(g.via((0,0,1),1))

    def test_bounded_solver_returns_complete_goal_or_no_partial_path(self):
        g=gate();src=np.zeros(g.shape,bool);src[0,0,0]=True;goal=np.zeros(g.shape,bool);goal[0,0,8]=True
        path,receipt=method.solve(g,src,goal,50)
        self.assertEqual(path[0],(0,0,0));self.assertEqual(path[-1],(0,0,8));self.assertEqual(receipt['status'],'COMPLETE_SOURCE_GRAPH_PATH')
        path,receipt=method.solve(gate(),src,goal,1)
        self.assertIsNone(path);self.assertEqual(receipt['status'],'EXPANSION_LIMIT')
        blocked=gate();blocked.hard[:,:,4]=False
        path,receipt=method.solve(blocked,src,goal,500)
        self.assertIsNone(path);self.assertEqual(receipt['status'],'GRAPH_EXHAUSTED')

    def test_source_wall_and_edge_caps_are_negative_not_partial_success(self):
        for kind in ('wall','edges'):
            g=gate();src=np.zeros(g.shape,bool);src[0,0,0]=True;goal=np.zeros(g.shape,bool);goal[0,0,8]=True
            if kind=='wall':g.seconds=0
            else:g.max_edges=0
            path,receipt=method.solve(g,src,goal,50)
            self.assertIsNone(path);self.assertIn('LIMIT',receipt['status'])

    def test_diagonal_rechecks_budget_after_its_four_side_edges(self):
        g=gate();g.max_edges=4
        with self.assertRaisesRegex(method.BudgetStop,'EXACT_EDGE_CHECK_LIMIT'):
            g.edge((0,0,0),(0,1,1))
        self.assertEqual(g.exact_checks,4)
        self.assertNotIn(((0,0,0),(0,1,1)),g.cache)

    def candidate_fixture(self):
        original,domain,pool=toy();pool['signal']['b'][0]['via']=True
        groups,records,_=a.portals(original,domain['targets']['signal'],pool['signal'],BUDGET,domain['common_bounds_mm'])
        raw=[['In2.Cu',18000000,10000000,0],['In2.Cu',12000000,10000000,0]]
        return original,raw,groups,records,domain['targets']['signal'],{'budget':BUDGET,'route_policy':POLICY,'demand_and_preservation_contract':domain}

    def test_complete_stitched_original_pair_is_source_only_and_input_unchanged(self):
        values=self.candidate_fixture();before=copy.deepcopy(values[0]);candidate=method.validate_candidate(*values)
        self.assertEqual(values[0],before);self.assertTrue(candidate['continuity']['emitted_geometry_connects_named_anchors'])
        self.assertFalse(candidate['native_exact_pair_closed']);self.assertFalse(candidate['accepted'])
        self.assertEqual(candidate['removed_uuids'],[]);self.assertEqual(set(candidate['anchor_uuids']),{'a','b'})

    def test_wrong_goal_partial_path_fill_veto_and_bad_emission_refuse(self):
        values=list(self.candidate_fixture());bad=copy.deepcopy(values);bad[1][-1][1]=13000000
        with self.assertRaisesRegex(ValueError,'not two named-anchor'):method.validate_candidate(*bad)
        with patch.object(a,'cumulative_fill_ok',return_value=False):
            with self.assertRaisesRegex(ValueError,'fill veto'):method.validate_candidate(*values)
        real=a.grid.copper_rows
        def wrong(*args,**kwargs):
            rows,links=real(*args,**kwargs);next(r for r in rows if r['kind']=='segment')['width_nm']=200000
            return rows,links
        with patch.object(a.grid,'copper_rows',side_effect=wrong):
            with self.assertRaisesRegex(ValueError,'width relaxation'):method.validate_candidate(*values)


if __name__=='__main__':unittest.main()
