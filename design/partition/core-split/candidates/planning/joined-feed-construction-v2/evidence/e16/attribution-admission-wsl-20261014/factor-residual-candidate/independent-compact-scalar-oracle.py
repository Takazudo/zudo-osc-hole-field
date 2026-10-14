"""Separate exact oracle for complete compact comparison/conversion integration.

Keeps the preceding row-only result untouched; no original inputs or full solve.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import random
import math
import hashlib
import json
import importlib.util
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('compact_row_control',HERE/'independent-compact-oracle.py')
R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
P,F,np,T=R.P,R.F,R.np,R.T


def compare_and_convert():
    rng=random.Random(284);compare_count=0;floors=uppers=refusals=0
    pairs=[(1,-1075),(3,-1075),(5,-1075),(1,-1074),(1,1023),
           ((1<<53)-1,971),((1<<54)-1,970),(1,2048),((1<<2176)-1,-1075)]
    while len(pairs)<1000:
        width=rng.choice([1,2,53,54,100,511,1024,2175,2176])
        m=rng.getrandbits(width)|(1<<(width-1))|1
        if rng.randrange(2):m=-m
        pairs.append((m,rng.randint(-1075,2048)))
    for i,a in enumerate(pairs):
        b=pairs[-1-i];meter=P.Meter();av=R.value(a);bv=R.value(b)
        sign=(av>bv)-(av<bv)
        assert P.compact_compare(a,b,meter)==sign
        assert P.compact_compare(b,a,meter)==-sign
        assert P.compact_compare(a,a,meter)==0
        compare_count+=3
        positive=P.compact_absolute(a,meter);v=abs(av)
        try:
            floor=P.compact_positive_floor(positive,meter)
            assert 0<F(floor)<=v
            above=math.nextafter(floor,math.inf)
            if math.isfinite(above):assert F(above)>v
            floors+=1
        except ValueError:refusals+=1
        arithmetic=P.ExactRowArithmetic('compact',meter)
        try:
            upper=arithmetic.upper_nonnegative(positive)
            assert F(upper)>=v
            uppers+=1
        except ValueError:refusals+=1
    return {'seed':284,'pairs':1000,'exact_comparisons':compare_count,
            'accepted_floor_checks':floors,'accepted_upper_checks':uppers,
            'conservative_conversion_refusals':refusals,'status':'PASS'}


def malformed_new_helpers():
    count=0
    for bad in [None,[],(1,),(1,0,0),[1,0],(True,0),(1.,0),(1,0.),(1,-1076),(1,2049),(2,0),(0,1)]:
        for operation in [lambda:P.compact_compare(bad,(0,0),P.Meter()),
                          lambda:P.compact_positive_floor(bad,P.Meter())]:
            try:operation()
            except ValueError:count+=1
            else:raise AssertionError('malformed compact scalar accepted')
    return {'refusals':count,'status':'PASS'}


def virtual_integration():
    checked=0;kernel_results=[]
    for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
        blocks,d,exact=T.separated_fixture(**kwargs);bounds=[];stamps=[]
        for kernel in ('fixed','compact'):
            meter=P.Meter();view=P.JoinedRows([(a,b,(0,1)) for a,b in blocks],d,meter)
            c=P.coercivity_interval_certificate(view,view.interval_entries(),{},meter,bound_mode='path-only',packed=True,exact_kernel=kernel)
            norm=max(sum(map(abs,r)) for r in T.exact_inverse_values(exact))
            assert F(c['inverse_infinity_upper'])>=norm
            bounds.append(c['inverse_infinity_upper']);stamps.append(c['witness_sha256']);checked+=1
            kernel_results.append({'case':name,'kernel':kernel,'bound':c['inverse_infinity_upper'],
                                   'units':meter.integer_operations,'bit_work':meter.integer_bit_work_envelope})
        assert bounds[0]==bounds[1] and stamps[0]==stamps[1]
    return {'exact_complete_operator_checks':checked,'identical_fixed_compact':True,'cases':kernel_results,'status':'PASS'}


if __name__=='__main__':
    result={'synthetic_only':True,'comparison_conversion':compare_and_convert(),
            'malformed_scalar':malformed_new_helpers(),'retained_scalar_controls':R.scalar_cases(),
            'retained_row_controls':R.row_cases(),'random_proof_integration':R.proof_integration(),
            'virtual_integration':virtual_integration(),
            'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [Path(__file__),HERE/'fixture/prototype.py',HERE/'fixture/test_compact.py',HERE/'independent-compact-oracle.py']}}
    print(json.dumps(result,indent=2))
