"""Native scalar/row kernel only; no original-size forest or admission."""
import test_compact as X
from test_compact import T,P
import native_exact as N
import ctypes as C
from fractions import Fraction as F
import json
import random
import struct
import tempfile
import unittest
from pathlib import Path

RESULTS={}
def exact(a):return F(a[0])*F(2)**a[1]

class NativeExactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='e16-native-exact-')
        path,metadata=N.build(cls.tmp.name);cls.k=N.Kernel(path);RESULTS['build']=metadata
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_ieee_and_half(self):
        rng=random.Random(281);values=[0.,-0.,2.**-1074,-2.**-1074,1.,-1.,.1,float.fromhex('0x1.fffffffffffffp1023')]
        while len(values)<500:
            v=struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0]
            if P.math.isfinite(v):values.append(v)
        totals=0
        for i,v in enumerate(values):
            s=N.Stats();a=self.k.decode(v,s);self.assertEqual(exact(a),F(v))
            w=values[-i-1];b=self.k.half(v,w,s);self.assertEqual(exact(b),(F(v)+F(w))/2)
            self.assertEqual(self.k.compare(a,b,s),(exact(a)>exact(b))-(exact(a)<exact(b)))
            totals+=s.kernel_units
        RESULTS['ieee_cases']=len(values);RESULTS['summed_independent_case_units']=totals
    def test_carry_borrow_cancellation_floor(self):
        cases=[((1,0),(-1,0)),(((1<<64)-1,0),(1,0)),(((1<<130)-1,0),(1,0)),
               ((1,128),(-1,0)),(((1<<100)+1,0),(-1,100)),((1,2048),(-1,-1075))]
        for a,b in cases:
            s=N.Stats()
            if a[1]==2048:
                with self.assertRaises(ValueError):self.k.add(a,b,s)
                continue
            value=self.k.add(a,b,s);self.assertEqual(exact(value),exact(a)+exact(b))
            if value[0]>0:
                floor=self.k.floor(value,s);self.assertLessEqual(F(floor),exact(value))
        with self.assertRaises(ValueError):self.k.floor((1,-1075),N.Stats())
        maximum=float.fromhex('0x1.fffffffffffffp1023')
        self.assertEqual(exact(self.k.half(maximum,maximum,N.Stats())),F(maximum))
    def test_rows_and_cumulative_caps(self):
        for side in [4,8,9]:
            a=T.grid(side);s=N.Stats();margins=[]
            for i in range(a.shape[0]):
                js=[int(j) for j in a.indices[a.indptr[i]:a.indptr[i+1]] if int(j)!=i]
                margins.append(self.k.row(float(a[i,i]),[float(a[i,j]) for j in js],[float(a[j,i]) for j in js],s))
            fixed=list(P.symmetric_margins(a,P.Meter(),'reference'))
            self.assertEqual([exact(v) for v in margins],[F(v,2**1075) for v in fixed])
            self.assertEqual(s.proposed_contributions,a.nnz-a.shape[0])
            RESULTS[f'grid{side}']=s.snapshot()
        s=N.Stats();margin=self.k.row(1.,[2.**-100,1.],[2.**-100,-1.],s)
        self.assertEqual(exact(margin),F(1)-F(2.**-100))
        self.assertEqual(s.proposed_contributions,4)
        s=N.Stats();s.kernel_units=199999
        with self.assertRaises(ValueError):self.k.decode(1.,s)
        self.assertGreater(s.kernel_units,200000)
        s=N.Stats();self.k.decode(1.,s);before=s.kernel_units;self.k.decode(1.,s)
        self.assertEqual(s.kernel_units,2*before)
    def test_raw_abi_malformed_refuses(self):
        a=N.Dyadic();a.used=35;a.sign=1;out=N.Dyadic();s=N.Stats()
        code=self.k.lib.e16_add(C.byref(a),C.byref(a),C.byref(out),C.byref(s));self.assertNotEqual(code,0)
        for field in ['bit_work_envelope','limb_visits','initialized_words','copied_words_upper','floating_calls']:
            bad=N.Stats();setattr(bad,field,2**64-1)
            with self.assertRaises(ValueError):self.k.decode(1.,bad)
            self.assertEqual(getattr(bad,field),2**64-1)
        for v in [float('inf'),float('nan')]:
            with self.assertRaises(ValueError):self.k.decode(v,N.Stats())
        with self.assertRaises(ValueError):self.k.row(1.,[1.]*129,[1.]*129,N.Stats())

if __name__=='__main__':
    import sys
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeExactTests))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(RESULTS,indent=2,sort_keys=True)+'\n')
    raise SystemExit(not r.wasSuccessful())
