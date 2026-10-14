"""Independent exact checks of adaptive dyadic rows; synthetic only.

No oracle value enters production. Existing fixture sets512MiB/20CPU bounds.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import random
import struct
import math
import hashlib
import json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'fixture'))
import test_prototype as T
P,F,np=T.P,T.F,T.np


def value(pair):
    m,e=pair
    return F(m)*(F(2)**e)


def scalar_cases():
    rng=random.Random(281)
    values=[0.,-0.,5e-324,-5e-324,2.**-1022,math.nextafter(2.**-1022,0.),
            math.nextafter(math.inf,0.),-math.nextafter(math.inf,0.),1.,-1.]
    while len(values)<1000:
        v=struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0]
        if math.isfinite(v):values.append(v)
    total_units=0
    for i,x in enumerate(values):
        y=values[-1-i];meter=P.Meter()
        a=P.compact_decode(x,meter);b=P.compact_decode(y,meter)
        assert value(a)==F(x) and value(b)==F(y)
        add=P.compact_add(a,b,meter);half=P.compact_half_sum(x,y,meter)
        assert value(add)==F(x)+F(y) and value(half)==(F(x)+F(y))/2
        assert value(P.compact_negative(a,meter))==-F(x)
        assert value(P.compact_absolute(a,meter))==abs(F(x))
        assert F(P.compact_to_fixed(half,meter),1<<1075)==value(half)
        zero=P.compact_add(a,P.compact_negative(a,meter),meter)
        assert zero==(0,0)
        total_units+=meter.integer_operations
    return {'seed':281,'pairs':1000,'exact_decode_checks':2000,'exact_add_half_neg_abs_fixed_cancel_checks':6000,
            'sum_independent_case_kernel_units':total_units,'status':'PASS'}


def row_cases():
    rng=random.Random(282);checked=0
    for case in range(100):
        rows=[]
        for i in range(3):
            rows.append([math.ldexp(float(rng.choice([-7,-3,-1,1,3,7])),rng.randint(-1000,900)) for _ in range(3)])
        a=T.csr(rows)
        exact=[F(rows[i][i])-sum(abs((F(rows[i][j])+F(rows[j][i]))/2) for j in range(3) if j!=i) for i in range(3)]
        compact=list(P.compact_symmetric_margins(a,P.Meter(),'review'))
        fixed=list(P.symmetric_margins(a,P.Meter(),'review'))
        assert compact==fixed
        assert [F(v,1<<1075) for v in compact]==exact
        checked+=3
    return {'seed':282,'matrices':100,'exact_margin_checks':checked,'status':'PASS'}


def proof_integration():
    rng=random.Random(283)
    for case in range(100):
        x=rng.randint(1,16)/8;y=rng.randint(1,16)/8;z=rng.randint(1,4)/32;s=rng.randint(-3,3)/64
        a=T.csr([[x+z+1,-x+s,z],[-x-s,x+y-2.**-40,-y+s],[z,-y-s,y+z]])
        results=[];witnesses=[]
        for mode in ('fixed','compact'):
            meter=P.Meter();packet,h=P.produce_coercivity_tree(a,{},meter,packed=True,exact_kernel=mode)
            cert=P.verify_coercivity_tree(a,{},packet,h,meter,path_only=True,exact_kernel=mode)
            results.append(cert['inverse_infinity_upper']);witnesses.append(h)
            assert F(results[-1])>=T.exact_norm(a)
        assert results[0]==results[1] and witnesses[0]==witnesses[1]
    return {'seed':283,'matrices':100,'exact_inverse_bound_checks':200,'identical_witnesses_and_bounds':True,'status':'PASS'}


def malformed():
    bad=[None,[],(1,), (1,0,0),[1,0],(True,0),(1.,0),(1,0.),(1,-1076),(1,2049),(2,0),(0,1)]
    count=0
    for a in bad:
        for operation in [lambda:P.compact_add((0,0),a,P.Meter()),
                          lambda:P.compact_negative(a,P.Meter()),
                          lambda:P.compact_absolute(a,P.Meter()),
                          lambda:P.compact_to_fixed(a,P.Meter())]:
            try:operation()
            except ValueError:count+=1
            else:raise AssertionError(('malformed compact accepted',a))
    for m,e in [(2,2048),(True,0),(1.,0),(1,0.),(1,-1076)]:
        try:P.compact_normalize(m,e,P.Meter())
        except ValueError:count+=1
        else:raise AssertionError('invalid normalize accepted')
    try:P.compact_add((1,2048),(1,-1075),P.Meter())
    except ValueError:count+=1
    else:raise AssertionError('wide alignment accepted')
    return {'malformed_or_width_refusals':count,'status':'PASS'}


if __name__=='__main__':
    result={'synthetic_only':True,'scalar':scalar_cases(),'rows':row_cases(),
            'proof_integration':proof_integration(),'malformed':malformed(),
            'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [Path(__file__),HERE/'fixture/prototype.py',HERE/'fixture/test_compact.py']}}
    print(json.dumps(result,indent=2))
