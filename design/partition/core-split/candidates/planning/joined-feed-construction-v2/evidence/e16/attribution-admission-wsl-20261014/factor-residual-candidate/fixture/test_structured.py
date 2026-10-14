"""Bounded non-oracle tree construction; keeps its negative grid evidence."""
import test_weighted as W
from test_weighted import T, P, np, csr, CONTEXT
from unittest.mock import patch
import unittest
import json
from pathlib import Path

RESULTS = {}


def run(a, pattern):
    m=P.Meter()
    def call():
        w,h=P.produce(a,CONTEXT,pattern,m)
        packet,stamp=P.produce_tree_weights(a,CONTEXT,w,h,m)
        result=P.verify(a,CONTEXT,w,h,m,packet,stamp)
        result['weights']=packet['values']
        result['producer_outcome']='CANDIDATE_EMITTED'
        result['auxiliary_system']='explicit full-order tree; no original-system solve'
        result['screen']='NOT RUN: rejected board strategy; no coupled implementation'
        return result
    result=W.measured(call,m)
    # Override old Picard-specific reporting: the tree is an actual auxiliary.
    result['accounting']['requested_auxiliary_order']=a.shape[0]
    result['accounting']['auxiliary_system_order']=a.shape[0] if m.weight_outputs else None
    result['accounting']['auxiliary_scope']='emitted tree order; None means failure before emission, possibly partial construction'
    result.setdefault('producer_outcome','CANDIDATE_EMITTED' if m.weight_outputs else 'CANDIDATE_FAILED')
    result['producer_failure_reason']=result.get('reason') if not m.weight_outputs else None
    result['accounting']['auxiliary_construction_updates']=sum(v for k,v in m.phases.items() if k.startswith('weight_tree_'))
    return result


class StructuredTests(unittest.TestCase):
    def test_retained_and_heldout_negative(self):
        for side,ground in [(4,1.),(8,1.),(9,1.),(4,2.**-30)]:
            a=T.grid(side,ground)
            with patch.object(T,'exact_inverse',side_effect=AssertionError('oracle forbidden')):
                result=run(a,W.tree(a,side))
            RESULTS[f'tree_grid_{side}_{ground}']=result
            self.assertEqual(result['producer_outcome'],'CANDIDATE_EMITTED')
            self.assertEqual(result['status'],'REFUSED')
            self.assertGreater(result['q'],1.)
            self.assertEqual(result['accounting']['weight_passes_completed'],0)

    def test_path_positive_control(self):
        a=csr([[2.,-1.,0.],[-1.,2.,-1.],[0.,-1.,1.]])
        result=run(a,[[0],[0,1],[1,2]])
        RESULTS['path_positive']=result
        self.assertEqual(result['status'],'CERTIFIED')
        self.assertEqual(result['weights'],[3.,5.,6.])
        inv=T.exact_inverse(a)
        self.assertGreaterEqual(T.F(result['inverse_infinity_upper']),max(sum(map(abs,row)) for row in inv))

    def test_failures_and_repeatability(self):
        cases={'disconnected':csr([[1.,0.],[0.,1.]]),
               'mixed_sign':csr([[2.,.2],[.2,2.]]),
               'nonsymmetric':csr([[2.,-1.],[-.5,1.]]),
               'ungrounded':csr([[1.,-1.],[-1.,1.]]),
               'overflow':csr([[2.**-500]])}
        for name,a in cases.items():
            result=run(a,[[i] for i in range(a.shape[0])]);RESULTS[name]=result
            self.assertEqual(result['status'],'REFUSED')
            self.assertGreater(result['accounting']['total_updates'],0)
        a=T.grid(4)
        x=run(a,W.tree(a,4));y=run(a,W.tree(a,4))
        self.assertEqual(x['weights'],y['weights'])
        self.assertEqual(x['accounting'],y['accounting'])

if __name__=='__main__':
    import sys
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(StructuredTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(RESULTS,indent=2,sort_keys=True)+'\n')
    raise SystemExit(not result.wasSuccessful())
