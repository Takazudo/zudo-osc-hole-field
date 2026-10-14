"""Independent review of tree coercivity and interval whole-operator bounds.

Synthetic only. Existing fixture sets 512MiB/20CPU limits. Exact inverses <=6.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import random
import itertools
import copy
import struct
import math
from unittest.mock import patch
import hashlib
import json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'fixture'))
import test_prototype as T
import test_coercivity as C
P,F,np=T.P,T.F,T.np


def certify(a):
    meter=P.Meter();packet,h=P.produce_coercivity_tree(a,{},meter)
    return P.verify_coercivity_tree(a,{},packet,h,meter,refine=True)


def check_bound(cert,values):
    exact=max(sum(map(abs,r)) for r in T.exact_inverse_values(values))
    assert F(cert['inverse_infinity_upper'])>=exact
    return float(exact)


def dyadic_helpers():
    rng=random.Random(279);meter=P.Meter()
    values=[0.,-0.,5e-324,-5e-324,math.nextafter(0.,1.),
            math.nextafter(float('inf'),0.),-math.nextafter(float('inf'),0.),
            2.**-1022,math.nextafter(2.**-1022,0.)]
    while len(values)<1000:
        v=struct.unpack('>d',rng.getrandbits(64).to_bytes(8,'big'))[0]
        if math.isfinite(v):values.append(v)
    scale=1<<P.DYADIC_EXPONENT
    for v in values:
        assert F(P.dyadic(v,meter),scale)==F(v)
    for x,y in zip(values,values[1:]):
        exact=(F(x)+F(y))/2
        num=P.half_sum(x,y,meter)
        assert F(num,scale)==exact
    return {'seed':279,'binary64_exact_decodes':1000,'exact_half_sums':999,'status':'PASS'}


def random_cases():
    rng=random.Random(278)
    for k in range(100):
        x=rng.randint(1,16)/8;y=rng.randint(1,16)/8;z=rng.randint(1,4)/32;s=rng.randint(-3,3)/64
        deficit=2.**-40 if k%2 else 0.
        a=T.csr([[x+z+1,-x+s,z],[-x-s,x+y-deficit,-y+s],[z,-y-s,y+z]])
        c=certify(a)
        check_bound(c,[[F(float(a[i,j])) for j in range(3)] for i in range(3)])
    return {'seed':278,'cases':100,'with_nonzero_exact_diagonal_deficit':50,'status':'PASS'}


def near_singular():
    a=T.csr([[1.,-1.],[-1.,1.+2.**-52]])
    cert=certify(a);exact=check_bound(cert,[[F(float(a[i,j])) for j in range(2)] for i in range(2)])
    refusals=[]
    for name,values in [('singular',[[1.,-1.],[-1.,1.]]),
                        ('indefinite',[[1.+2.**-52,-1.],[-1.,1.-2.**-51]])]:
        try:certify(T.csr(values))
        except ValueError as exc:refusals.append({'case':name,'reason':str(exc)})
        else:raise AssertionError('uncertified singular/indefinite accepted')
    return {'near_singular_bound':cert['inverse_infinity_upper'],'exact_norm':exact,'refusals':refusals}


def malformed():
    a=T.grid(4);packet,h=P.produce_coercivity_tree(a,{},P.Meter())
    mutations=[('root',True),('root',16),('ground',0.),('ground',float('inf')),
               ('edge',[0.]*16),('order',[0]*16),('parent',[-1]*16),
               ('matrix','stale'),('context','stale'),('method','stale')]
    for field,value in mutations:
        bad=copy.deepcopy(packet);bad[field]=value
        try:P.verify_coercivity_tree(a,{},bad,P.digest(bad),P.Meter())
        except ValueError:pass
        else:raise AssertionError(('malformed accepted',field))
    try:P.verify_coercivity_tree(a,{},packet,'stale',P.Meter())
    except ValueError:pass
    else:raise AssertionError('stale expected digest accepted')
    for entries in [[[0,0,0.,1.],[0,0,0.,1.]],[[0,0,2.,1.]],[[0.,0,1.,2.]]]:
        try:P.coercivity_interval_certificate(a,entries,{},P.Meter())
        except ValueError:pass
        else:raise AssertionError('malformed interval replacements accepted')
    return {'tree_packet_refusals':11,'interval_schema_refusals':3,'status':'PASS'}


def sqrt_witnesses():
    a=T.grid(4);packet,h=P.produce_coercivity_tree(a,{},P.Meter())
    original=math.sqrt
    results=[]
    for name,trial in [('zero',lambda x:0.),('negative',lambda x:-original(x)),
                       ('half',lambda x:original(x)*.5)]:
        meter=P.Meter()
        with patch.object(P.math,'sqrt',side_effect=trial):
            result=P.verify_coercivity_tree(a,{},packet,h,meter,refine=True)
        assert result['path_cauchy_refinement']['status']=='REFUSED'
        assert result['inverse_infinity_upper']==result['trace_inverse_infinity_upper']
        assert result['inverse_infinity_upper']>0
        assert meter.work.updates==sum(meter.phases.values())
        results.append({'trial':name,'status':'trace fallback with failed work retained'})
    return results


def coupled():
    result=[]
    for name,kwargs in [('grounded',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
        blocks,d,exact=T.separated_fixture(**kwargs)
        mid=np.array([[float((v[0]+v[1])/2) for v in row] for row in d])
        a=C.joined_stored(blocks,mid)
        entries=[[4+i,4+j,float(d[i][j][0]),float(d[i][j][1])] for i in range(2) for j in range(2)]
        cert=P.coercivity_interval_certificate(a,entries,{},P.Meter())
        exact_norm=check_bound(cert,exact)
        largest_corner=0.
        for choices in itertools.product([0,1],repeat=4):
            values=[[F(float(a[i,j])) for j in range(6)] for i in range(6)]
            for entry,choice in zip(entries,choices):values[entry[0]][entry[1]]=F(entry[2+choice])
            largest_corner=max(largest_corner,check_bound(cert,values))
        result.append({'case':name,'bound':cert['inverse_infinity_upper'],
                       'exact_original_norm':exact_norm,'all_16_interval_corners_max_norm':largest_corner,
                       'shift_q':cert['coercivity_shift_q'],'interval_q':cert['interval_perturbation_q']})
    return result


if __name__=='__main__':
    result={'synthetic_only':True,'dyadic_helpers':dyadic_helpers(),'random':random_cases(),'near_singular':near_singular(),'malformed':malformed(),'sqrt_witnesses':sqrt_witnesses(),'coupled':coupled(),
            'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [Path(__file__),HERE/'fixture/prototype.py',HERE/'fixture/test_coercivity.py']}}
    print(json.dumps(result,indent=2))
