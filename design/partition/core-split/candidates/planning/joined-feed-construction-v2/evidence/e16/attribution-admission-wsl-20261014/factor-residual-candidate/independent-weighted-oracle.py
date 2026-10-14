"""Separate mathematics reviewer: bounded exact checks, no original inputs.

Dense Fraction inverse is only a <=6 oracle; exact residual check is order16.
Candidate producer is invoked before oracle calculations and never reads them.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import random
import json
import hashlib
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE/'fixture'))
import test_prototype as T  # sets 512 MiB address-space and 20 CPU-second limits
P, F, np = T.P, T.F, T.np


def exact_produced_contraction():
    a = T.grid(4)
    pattern = [[i] if i == 0 else [i-4 if i >= 4 else i-1, i] for i in range(16)]
    context = {'independent_review': 'exact-eight-pass-counterexample'}
    meter = P.Meter()
    w, stamp = P.produce(a, context, pattern, meter)
    packet, phash = P.produce_weights(a, context, w, stamp, meter)
    cert = P.verify(a, context, w, stamp, meter, packet, phash)
    p = list(map(F, packet['values']))
    # Independent exact sparse LU residual and comparison; no approximate math.
    residual = []
    for i in range(16):
        row = {int(a.indices[k]): F(float(a.data[k])) for k in range(a.indptr[i], a.indptr[i+1])}
        for k, lik in [(i, 1.)]+w['L'][i]:
            for j, ukj in w['U'][k]:
                row[j] = row.get(j, F(0))-F(lik)*F(ukj)
        residual.append(sum(abs(v)*p[j] for j,v in row.items()))
    y = []
    for i in range(16):
        y.append(residual[i]+sum(abs(F(v))*y[j] for j,v in w['L'][i]))
    z = [F(0)]*16
    for i in range(15,-1,-1):
        z[i]=(y[i]+sum(abs(F(v))*z[j] for j,v in w['U'][i] if j>i))/abs(F(w['U'][i][0][1]))
    ratios = [z[i]/p[i] for i in range(16)]
    q = max(ratios)
    assert q > 1 and cert['status'] == 'REFUSED' and F(cert['q']) >= q
    return {'order':16,'ground':1.,'passes':8,'exact_q':str(q),'exact_q_float':float(q),
            'maximizing_row':ratios.index(q),'outward_q':cert['q'], 'weights':packet['values'],
            'result':'EXACT_COUNTEREXAMPLE: emitted weights fail weighted contraction'}


def coupled_cases():
    rng=random.Random(277)
    for case in range(100):
        blocks=[]; packets=[]; context={'independent_review':case}; patterns=[[[0],[1]],[[0],[1]]]
        for board in range(2):
            a=T.csr([[4.,rng.randint(-3,3)/32],[rng.randint(-3,3)/32,2.]])
            B=np.zeros((2,2)); B[:,board]=[.25,-.125]
            blocks.append((a,B))
            w,h=P.produce(a,{**context,'board':board},patterns[board],P.Meter())
            values=[2.**rng.randint(-2,2),2.**rng.randint(-2,2)]
            packet=P.weight_packet(a,{**context,'board':board},w,values,'review:nonuniform')
            packets.append((packet,P.digest(packet)))
            cert=P.verify(a,{**context,'board':board},w,h,P.Meter(),packet,P.digest(packet))
            assert cert['status']=='CERTIFIED'
            assert F(cert['inverse_infinity_upper'])>=T.exact_norm(a)
        D=[[2.,-.5],[-.5,2.]]
        cert=P.block_certificate(blocks,D,context,P.Meter(),patterns,weight_mode='supplied',supplied_weights=packets)
        exact_s=[[F(x) for x in row] for row in D]
        full=[[F(0) for _ in range(6)] for _ in range(6)]
        for b,(a,B) in enumerate(blocks):
            ai=T.exact_inverse(a)
            for i in range(2):
                for j in range(2):
                    exact_s[i][j]-=sum(F(float(B[k,i]))*ai[k][l]*F(float(B[l,j])) for k in range(2) for l in range(2))
                    full[2*b+i][2*b+j]=F(float(a[i,j]))
                    full[2*b+i][4+j]=full[4+j][2*b+i]=F(float(B[i,j]))
        for i in range(2):
            for j in range(2):
                lo,hi=cert['schur_intervals'][i][j]
                assert F(lo)<=exact_s[i][j]<=F(hi)
                full[4+i][4+j]=F(D[i][j])
        exactnorm=max(sum(map(abs,row)) for row in T.exact_inverse_values(full))
        assert F(cert['inverse_infinity_upper'])>=exactnorm
    return {'seed':277,'cases':100,'exact_board_inverse_checks':200,
            'exact_schur_interval_checks':400,'exact_joined_inverse_checks':100,'status':'PASS'}


if __name__ == '__main__':
    result={'synthetic_only':True,'producer_counterexample':exact_produced_contraction(),
            'independent_coupled':coupled_cases(),
            'sha256':{str(path.relative_to(HERE)):hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in [Path(__file__),HERE/'fixture/prototype.py',HERE/'fixture/test_prototype.py']}}
    print(json.dumps(result,indent=2,allow_nan=False))
