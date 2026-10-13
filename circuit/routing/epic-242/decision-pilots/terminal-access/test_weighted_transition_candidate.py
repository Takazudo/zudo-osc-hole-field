"""Fixed ordering and unchanged physical gates; synthetic tests, no native."""
import ast
import heapq
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np

import f3_adapter as a
import exact_transition_candidate as base
import weighted_transition_candidate as weighted
from test_exact_transition_candidate import gate
import test_exact_transition_candidate as regression


class WeightedTests(unittest.TestCase):
    def terminals(self,g):
        src=np.zeros(g.shape,bool);src[0,0,0]=True
        goal=np.zeros(g.shape,bool);goal[0,0,8]=True
        return src,goal

    def test_weight_two_and_higher_g_tie_are_fixed(self):
        # Weight1 prefers g1/h3 over g6/h0; fixed weight2 prefers the latter.
        self.assertLess(1+3,6+0)
        self.assertLess(weighted.priority(6,0,(0,0,1)),weighted.priority(1,3,(0,0,2)))
        # Equal f=10: g8/h1 outranks g2/h4, then node gives deterministic ties.
        self.assertLess(weighted.priority(8,1,(0,0,8)),weighted.priority(2,4,(0,0,2)))
        self.assertLess(weighted.priority(8,1,(0,0,1)),weighted.priority(8,1,(0,0,2)))
        self.assertEqual(weighted.ORDER['heuristic_weight'],2)

    def test_solver_change_is_only_queue_priority_and_positive_g_decode(self):
        # Structural regression protects costs, reopening, graph calls and cap order.
        s=Path(base.__file__).read_text();old=s[s.index('def solve('):s.index('\n\ndef validate_candidate')]
        expected=old.replace('def solve(', 'def solve_weighted(')
        expected=expected.replace('heapq.heappush(heap,(float(distance[node[1:]]),0.,node))','heapq.heappush(heap,priority(0.,float(distance[node[1:]]),node))')
        expected=expected.replace('gate.limits();_,cost,node=heapq.heappop(heap)','gate.limits();_,negative_cost,node=heapq.heappop(heap);cost=-negative_cost')
        expected=expected.replace('heapq.heappush(heap,(value+float(distance[q[1:]]),value,q))','heapq.heappush(heap,priority(value,float(distance[q[1:]]),q))')
        s=Path(weighted.__file__).read_text();actual=s[s.index('def solve_weighted('):s.index('\n\ndef method_binding')]
        def normalized(text):
            tree=ast.parse(text);tree.body[0].body=tree.body[0].body[1:]
            return ast.dump(tree,include_attributes=False)
        self.assertEqual(normalized(actual),normalized(expected))

    def test_solver_uses_fixed_priority_and_returns_complete_original_goal(self):
        g=gate();src,goal=self.terminals(g)
        with patch.object(weighted,'priority',wraps=weighted.priority) as calls:
            path,result=weighted.solve_weighted(g,src,goal,50)
        self.assertEqual(path[0],(0,0,0));self.assertEqual(path[-1],(0,0,8))
        self.assertGreater(calls.call_count,1);self.assertTrue(all(c.args[0]>=0 for c in calls.call_args_list))
        self.assertEqual(result['status'],'COMPLETE_SOURCE_GRAPH_PATH')

    def test_stale_entry_uses_positive_g_and_is_not_expanded(self):
        g=gate();src,goal=self.terminals(g);reference=weighted.solve_weighted(g,src,goal,50)[1]
        real=heapq.heappop;first=True
        def pop(queue):
            nonlocal first
            if first:
                first=False
                return weighted.priority(999,0,(0,0,0))
            return real(queue)
        with patch.object(weighted.heapq,'heappop',side_effect=pop):
            path,result=weighted.solve_weighted(gate(),src,goal,50)
        self.assertEqual(path[-1],(0,0,8));self.assertEqual(result['expanded'],reference['expanded'])

    def test_same_caps_and_no_partial_path(self):
        g=gate();src,goal=self.terminals(g)
        path,result=weighted.solve_weighted(g,src,goal,1)
        self.assertIsNone(path);self.assertEqual(result['expanded'],1);self.assertEqual(result['status'],'EXPANSION_LIMIT')
        g=gate();g.max_edges=0
        path,result=weighted.solve_weighted(g,src,goal,50000)
        self.assertIsNone(path);self.assertEqual(result['status'],'EXACT_EDGE_CHECK_LIMIT')

    def test_graph_and_full_physical_validator_are_identical_objects(self):
        self.assertIs(weighted.ExactTransitions,base.ExactTransitions)
        self.assertIs(weighted.validate_candidate,base.validate_candidate)
        args=list(regression.ExactTransitionTests().candidate_fixture())
        candidate=weighted.validate_candidate(*args)
        self.assertTrue(candidate['continuity']['emitted_geometry_connects_named_anchors'])
        self.assertFalse(candidate['accepted']);self.assertFalse(candidate['native_exact_pair_closed'])
        args[1][-1][1]=13000000
        with self.assertRaisesRegex(ValueError,'not two named-anchor'):weighted.validate_candidate(*args)
        args=list(regression.ExactTransitionTests().candidate_fixture())
        with patch.object(a,'cumulative_fill_ok',return_value=False):
            with self.assertRaisesRegex(ValueError,'fill veto'):weighted.validate_candidate(*args)

    def test_method_authentication_refuses_graph_validation_drift(self):
        with patch.object(weighted.region,'sha',return_value='0'*64):
            with self.assertRaisesRegex(ValueError,'graph/validation source drift'):weighted.method_binding()


if __name__=='__main__':unittest.main()
