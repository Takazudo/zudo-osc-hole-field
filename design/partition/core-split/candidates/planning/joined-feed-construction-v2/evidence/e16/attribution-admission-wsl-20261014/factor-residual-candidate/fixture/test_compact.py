"""Compact row arithmetic against exact references and fixed proof controls."""
import test_virtual as V
from test_virtual import C,W,T,P,np,csr,CONTEXT
import unittest
import json
import struct
import random
from pathlib import Path

RESULTS={}


def exact(a):
    return T.F(a[0])*(T.F(2)**a[1])


class CompactTests(unittest.TestCase):
    def test_binary64_and_full_span(self):
        rng=random.Random(280)
        values=[0.,-0.,2.**-1074,-2.**-1074,2.**-1022,1.,-1.,.1,float.fromhex('0x1.fffffffffffffp1023')]
        while len(values)<300:
            v=struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0]
            if P.math.isfinite(v):values.append(v)
        for i,v in enumerate(values):
            m=P.Meter();a=P.compact_decode(v,m)
            self.assertEqual(exact(a),T.F(v))
            w=values[-i-1]
            result=P.compact_half_sum(v,w,m)
            self.assertEqual(exact(result),(T.F(v)+T.F(w))/2)
            self.assertEqual(T.F(P.compact_to_fixed(result,m),2**1075),exact(result))
            b=P.compact_decode(w,m)
            expected=(T.F(v)>T.F(w))-(T.F(v)<T.F(w))
            self.assertEqual(P.compact_compare(a,b,m),expected)
            if v>0:
                floor=P.compact_positive_floor(a,m)
                self.assertLessEqual(T.F(floor),T.F(v))
                upper=P.ExactRowArithmetic('compact',m).upper_nonnegative(a)
                self.assertGreaterEqual(T.F(upper),T.F(v))
        m=P.Meter()
        with self.assertRaises(ValueError):P.compact_add((1,2048),(1,-1075),m)
        self.assertGreater(m.integer_operations,0)
        with self.assertRaises(ValueError):P.compact_positive_floor((1,-1075),P.Meter())
        with self.assertRaises(ValueError):P.ExactRowArithmetic('compact',P.Meter()).upper_nonnegative((1,-1075))

    def test_rows_exact_and_same_bounds(self):
        for side in [4,8,9]:
            a=T.grid(side);fixed=P.Meter();compact=P.Meter()
            self.assertEqual(list(P.symmetric_margins(a,fixed,'rows')),list(P.compact_symmetric_margins(a,compact,'rows')))
            RESULTS[f'row_work_grid{side}']={'fixed_units':fixed.integer_operations,'compact_units':compact.integer_operations,
                'fixed_bit_work':fixed.integer_bit_work_envelope,'compact_bit_work':compact.integer_bit_work_envelope}
            self.assertLess(compact.integer_bit_work_envelope,fixed.integer_bit_work_envelope)
            norms=[]
            for mode in ['fixed','compact']:
                m=P.Meter();packet,h=P.produce_coercivity_tree(a,CONTEXT,m,packed=True,exact_kernel=mode)
                r=P.verify_coercivity_tree(a,CONTEXT,packet,h,m,path_only=True,exact_kernel=mode)
                r['exact_kernel']=mode;RESULTS[f'grid{side}_{mode}']=r;norms.append(r['inverse_infinity_upper'])
            self.assertEqual(*norms)

    def test_cancellation_and_bad_kernel(self):
        cases=[csr([[1.,-1.],[-1.,1.]]),csr([[1.,-.1],[-.3,1.]]),
               csr([[float.fromhex('0x1.fffffffffffffp1023'),2.**-1074],[-2.**-1074,1.]]),
               csr([[2.**-1074,-2.**-1074],[-2.**-1074,2.**-1074]])]
        for a in cases:
            self.assertEqual(list(P.symmetric_margins(a,P.Meter(),'r')),list(P.compact_symmetric_margins(a,P.Meter(),'r')))
        with self.assertRaises(ValueError):P.produce_coercivity_tree(T.grid(4),CONTEXT,P.Meter(),exact_kernel='invalid')
        malformed=[(0,1),(2,0),(True,0),(1,False),[1,0],(1,),('x',0),(1,2049),(1,-1076)]
        for bad in malformed:
            for fn in [lambda:P.compact_add((0,0),bad,P.Meter()),
                       lambda:P.compact_negative(bad,P.Meter()),
                       lambda:P.compact_absolute(bad,P.Meter()),
                       lambda:P.compact_to_fixed(bad,P.Meter())]:
                with self.assertRaises(ValueError):fn()
        with self.assertRaises(ValueError):P.compact_normalize(2,2048,P.Meter())
        with self.assertRaises(ValueError):P.compact_normalize('x',0,P.Meter())

    def test_virtual_coupled_equivalence(self):
        for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
            bounds=[]
            for kernel in ['fixed','compact']:
                blocks,d,reference,meter,view=V.view_case(kwargs)
                r=W.measured(lambda:P.coercivity_interval_certificate(view,view.interval_entries(),CONTEXT,meter,
                    bound_mode='path-only',packed=True,exact_kernel=kernel),meter)
                self.assertEqual(r['status'],'CERTIFIED')
                r.update(W.physical_result(r,blocks,reference));bounds.append(r['inverse_infinity_upper'])
                r['integer_units']=meter.integer_operations;r['integer_bit_work_envelope']=meter.integer_bit_work_envelope
                r['view_access']=dict(view.access);RESULTS[name+'_'+kernel]=r
            self.assertEqual(*bounds)

if __name__=='__main__':
    import sys
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CompactTests))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(RESULTS,indent=2,sort_keys=True)+'\n')
    raise SystemExit(not r.wasSuccessful())
