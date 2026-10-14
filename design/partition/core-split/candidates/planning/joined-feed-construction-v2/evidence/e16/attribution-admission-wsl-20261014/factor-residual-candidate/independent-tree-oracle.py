"""Independent exact sparse checks of emitted tree-barrier weights.

No original inputs, dense matrix, inverse, or expected weights enter production.
The existing fixture import sets 512 MiB and 20 CPU-second bounds.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import hashlib
import json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'fixture'))
import test_prototype as T
P,F=T.P,T.F


def run(side):
    a=T.grid(side);n=side*side
    pattern=[[i] if i==0 else [i-side if i>=side else i-1,i] for i in range(n)]
    meter=P.Meter();w,stamp=P.produce(a,{},pattern,meter)
    packet,ph=P.produce_tree_weights(a,{},w,stamp,meter)
    cert=P.verify(a,{},w,stamp,meter,packet,ph)
    p=list(map(F,packet['values']))
    # Exact sparse matrix and factor products, independent of outward verifier.
    residual=[];ap=[]
    for i in range(n):
        row={int(a.indices[k]):F(float(a.data[k])) for k in range(a.indptr[i],a.indptr[i+1])}
        ap.append(sum(v*p[j] for j,v in row.items()))
        for k,lik in [(i,1.)]+w['L'][i]:
            for j,ukj in w['U'][k]:row[j]=row.get(j,F(0))-F(lik)*F(ukj)
        residual.append(sum(abs(v)*p[j] for j,v in row.items()))
    y=[]
    for i in range(n):y.append(residual[i]+sum(abs(F(v))*y[j] for j,v in w['L'][i]))
    z=[F(0)]*n
    for i in range(n-1,-1,-1):
        z[i]=(y[i]+sum(abs(F(v))*z[j] for j,v in w['U'][i] if j>i))/abs(F(w['U'][i][0][1]))
    ratios=[z[i]/p[i] for i in range(n)];q=max(ratios)
    assert q>1 and cert['status']=='REFUSED' and F(cert['q'])>=q
    assert min(ap)<0
    return {'side':side,'order':n,'weights':packet['values'],'exact_q':str(q),
            'q_float':float(q),'q_outward':cert['q'],'maximizing_row':ratios.index(q),
            'min_original_Ap':str(min(ap)),'min_Ap_row':ap.index(min(ap)),
            'outcome':'exact contraction failure; omitted graph edges invalidate tree supersolution',
            'total_updates':meter.work.updates,'phase_updates':meter.phases}


if __name__=='__main__':
    print(json.dumps({'synthetic_only':True,'dense_oracle_used':False,'cases':[run(m) for m in [4,8,9]],
        'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in [Path(__file__),HERE/'fixture/prototype.py',HERE/'fixture/test_prototype.py']}},indent=2))
