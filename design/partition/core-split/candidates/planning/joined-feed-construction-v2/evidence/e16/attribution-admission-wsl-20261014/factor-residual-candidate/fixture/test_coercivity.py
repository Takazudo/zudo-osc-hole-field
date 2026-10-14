"""Bounded complete-operator coercivity experiment and independent references."""
import test_weighted as W
from test_weighted import T,P,np,csr,CONTEXT
import copy
import json
from pathlib import Path
import unittest

RESULTS={}


def run(a, refine=False):
    m=P.Meter()
    def execute():
        packet,h=P.produce_coercivity_tree(a,CONTEXT,m)
        return P.verify_coercivity_tree(a,CONTEXT,packet,h,m,refine=refine)
    result=W.measured(execute,m)
    result['integer_operations']=getattr(m,'integer_operations',0)
    result['integer_phase_operations']=getattr(m,'integer_phases',{})
    result['integer_kernel_units']=getattr(m,'integer_kernel_units',{})
    result['integer_bit_work_envelope']=getattr(m,'integer_bit_work_envelope',0)
    result['integer_max_bits']=P.DYADIC_BITS
    result['integer_scope']='separate declared kernel units with width-squared logical bit-work envelope, not machine instructions or float updates; <=2176-bit operands; no production mapping'
    result['producer_outcome']='EMITTED' if 'coercivity_verify_margins' in result['integer_phase_operations'] else 'REFUSED'
    result['screen']='NOT RUN: board-only fixture'
    return result


def joined_stored(blocks,d):
    from scipy.sparse import bmat
    # Test input construction, not certificate production. Exact dyadic interval
    # midpoint stored as input; enclosing D uncertainty is separately verified.
    return bmat([[blocks[0][0],None,csr(blocks[0][1])],
                 [None,blocks[1][0],csr(blocks[1][1])],
                 [csr(blocks[0][1].T),csr(blocks[1][1].T),csr(d)]],format='csr')


class CoercivityTests(unittest.TestCase):
    def test_grid_polynomial(self):
        for side,g in [(4,1.),(8,1.),(9,1.),(4,2.**-30)]:
            a=T.grid(side,g);r=run(a);RESULTS[f'grid_{side}_{g}']=r
            self.assertEqual(r['status'],'CERTIFIED')
            expected=side**3/g+side**3*(side-1)
            self.assertGreaterEqual(r['inverse_infinity_upper'],expected)
            self.assertLess(r['inverse_infinity_upper'],expected*1.000001)
            if side==4:
                inv=T.exact_inverse(a)
                r['reference_inverse_norm']=float(max(sum(map(abs,row)) for row in inv))
                self.assertGreaterEqual(T.F(r['inverse_infinity_upper']),max(sum(map(abs,row)) for row in inv))

    def test_path_cauchy_and_exact_decode(self):
        import math
        for side in [4,8,9]:
            a=T.grid(side);r=run(a,True);RESULTS[f'grid_{side}_path_cauchy']=r
            self.assertEqual(r['path_cauchy_refinement']['status'],'CERTIFIED')
            self.assertLess(r['inverse_infinity_upper'],r['trace_inverse_infinity_upper'])
            if side==4:
                self.assertGreaterEqual(T.F(r['inverse_infinity_upper']),max(sum(map(abs,row)) for row in T.exact_inverse(a)))
        m=P.Meter()
        for value in [0.,-0.,2.**-1074,-2.**-1074,2.**-1022,-2.**-1022,.1,-.1,1.,-1.,float.fromhex('0x1.fffffffffffffp1023'),-float.fromhex('0x1.fffffffffffffp1023')]:
            self.assertEqual(T.F(P.dyadic(value,m),2**1075),T.F(value))
        for x,y in [(2.**-1074,0.),(.1,-.1),(1.,.1)]:
            self.assertEqual(T.F(P.half_sum(x,y,m),2**1075),(T.F(x)+T.F(y))/2)
        self.assertEqual(m.integer_operations,sum(m.integer_phases.values()))
        self.assertEqual(m.integer_operations,sum(m.integer_kernel_units.values()))
        with self.assertRaises(ValueError):P.integer_charge(m,200001)

    def test_untrusted_sqrt_and_caps(self):
        from unittest.mock import patch
        for bogus in [0.,-1000.,float('nan'),.001]:
            with patch.object(P.math,'sqrt',return_value=bogus):
                r=run(T.grid(4),True)
            self.assertEqual(r['status'],'CERTIFIED')
            self.assertEqual(r['path_cauchy_refinement']['status'],'REFUSED')
            self.assertEqual(r['inverse_infinity_upper'],r['trace_inverse_infinity_upper'])
            self.assertGreater(r['accounting']['phase_updates']['coercivity_path_cauchy'],0)
        a=T.grid(4);m=P.Meter();packet,h=P.produce_coercivity_tree(a,CONTEXT,m)
        limited=P.Meter(P.I.Work(max_entries=100000,max_updates=1))
        with self.assertRaises(ValueError):P.verify_coercivity_tree(a,CONTEXT,packet,h,limited,True)
        self.assertGreater(limited.work.updates,1)

    def test_interval_and_extreme_refusal(self):
        a=csr([[1.]])
        with self.assertRaises(ValueError):P.coercivity_interval_certificate(a,[[0,0,-1.,1.]],CONTEXT,P.Meter())
        for entries in [[[0,0,float('nan'),1.]],[[0,0,1.,1.],[0,0,1.,1.]],[[True,0,1.,1.]]]:
            with self.assertRaises(ValueError):P.coercivity_interval_certificate(a,entries,CONTEXT,P.Meter())
        r=run(csr([[2.**-1074]]));self.assertEqual(r['status'],'REFUSED')
        r=run(csr([[float.fromhex('0x1.fffffffffffffp1023')]]))
        self.assertEqual(r['status'],'CERTIFIED')
        self.assertGreaterEqual(T.F(r['inverse_infinity_upper']),1/T.F(float.fromhex('0x1.fffffffffffffp1023')))

    def test_nonsymmetric_and_signed(self):
        for name,a in [('nonsymmetric',csr([[3.,-1.25],[-.75,2.]])),
                       ('mixed_sign',csr([[4.,-1.,.25],[-1.,4.,-1.],[.25,-1.,4.]]))]:
            r=run(a);RESULTS[name]=r;self.assertEqual(r['status'],'CERTIFIED')
            exact=T.exact_inverse(a)
            self.assertGreaterEqual(T.F(r['inverse_infinity_upper']),max(sum(map(abs,row)) for row in exact))

    def test_refusals_and_bindings(self):
        for name,a in [('one_sided',csr([[2.,-1.],[0.,2.]])),
                       ('disconnected',csr([[1.,0.],[0.,1.]])),
                       ('ungrounded',csr([[1.,-1.],[-1.,1.]])),
                       ('not_sdd',csr([[1.,-2.],[-2.,5.]]))]:
            r=run(a);RESULTS[name]=r;self.assertEqual(r['status'],'REFUSED')
        a=T.grid(4);m=P.Meter();packet,h=P.produce_coercivity_tree(a,CONTEXT,m)
        for field,value in [('ground',100.),('edge',[100.]*16),('parent',[0]*16),
                            ('order',list(reversed(range(16))))]:
            bad=copy.deepcopy(packet);bad[field]=value
            with self.assertRaises(ValueError):P.verify_coercivity_tree(a,CONTEXT,bad,P.digest(bad),P.Meter())
        with self.assertRaises(ValueError):P.verify_coercivity_tree(a,{**CONTEXT,'stale':True},packet,h,P.Meter())

    def test_distributed_rounding_applicability(self):
        for name,kwargs in [('coupled',{}),('weak',{'ground':2.**-30}),('nonsym_coupled',{'nonsymmetric':True})]:
            blocks,d,exact=T.separated_fixture(**kwargs)
            raw=np.array([[float((v[0]+v[1])/2) if isinstance(v,tuple) else v for v in row] for row in d])
            a=joined_stored(blocks,raw);r=run(a);RESULTS[name]=r
            r['reference_inverse_norm']=float(max(sum(map(abs,row)) for row in T.exact_inverse_values(exact)))
            # This is applicability evidence, never silently changed rounding.
            if r['status']=='CERTIFIED':
                self.assertGreaterEqual(T.F(r['inverse_infinity_upper']),max(sum(map(abs,row)) for row in T.exact_inverse(a)))
            entries=[[4+i,4+j,float(d[i][j][0]),float(d[i][j][1])] for i in range(2) for j in range(2)]
            meter=P.Meter()
            full=W.measured(lambda:P.coercivity_interval_certificate(a,entries,CONTEXT,meter),meter)
            self.assertEqual(full['status'],'CERTIFIED')
            full.update(W.physical_result(full,blocks,exact))
            full['coupled_acceptance']='CERTIFIED complete interval operator'
            full['integer_operations']=meter.integer_operations
            full['integer_phase_operations']=dict(meter.integer_phases)
            full['integer_kernel_units']=dict(meter.integer_kernel_units)
            full['integer_bit_work_envelope']=meter.integer_bit_work_envelope
            RESULTS[name+'_interval']=full
            r['screen']='NOT RUN: midpoint control only; see separate interval result'
        # Whole distributed termination ww^T/R creates positive nonadjacent
        # entries. The matrix is SPD (identity plus vv^T), but not SDD.
        v=np.array([.125,.375,.5,-1.])
        a=csr(np.eye(4)*.01+np.outer(v,v));r=run(a)
        RESULTS['nonadjacent_distributed_stamp']=r
        self.assertEqual(r['status'],'REFUSED')
        self.assertTrue('deficit defeats tree bound' in r['reason'] or 'negative-edge tree disconnected' in r['reason'])
        r['reference_inverse_norm']=float(max(sum(map(abs,row)) for row in T.exact_inverse(a)))

if __name__=='__main__':
    import sys
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CoercivityTests))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(RESULTS,indent=2,sort_keys=True)+'\n')
    raise SystemExit(not result.wasSuccessful())
