"""Independent exact virtual-row checks; tiny dense references are oracle only.

No full joined CSR or transpose is passed to certificate producer/verifier.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import random
import copy
import array
import hashlib
import json
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'fixture'))
import test_prototype as T
P,F,np=T.P,T.F,T.np


def expected_matrix(blocks,d):
    n=sum(a.shape[0] for a,_,_ in blocks);m=len(d)
    values=[[F(0) for _ in range(n+m)] for _ in range(n+m)]
    offset=0
    for a,b,columns in blocks:
        for i in range(a.shape[0]):
            for j in range(a.shape[1]):values[offset+i][offset+j]=F(float(a[i,j]))
            for j,t in enumerate(columns):
                values[offset+i][n+t]=values[n+t][offset+i]=F(float(b[i,j]))
        offset+=a.shape[0]
    for i in range(m):
        for j in range(m):values[n+i][n+j]=F(d[i][j][0]*.5+d[i][j][1]*.5)
    return values


def check_view(view,expected):
    n=len(expected)
    for i in range(n):
        items=list(P.operator_row(view,i))
        assert items==sorted(items) and len(set(j for j,_ in items))==len(items)
        actual={j:F(v) for j,v in items}
        assert actual=={j:x for j,x in enumerate(expected[i]) if x}
        for j in range(n):
            assert F(P.operator_value(view,i,j))==expected[i][j]
            if expected[i][j]:assert F(view.lookup(i,j,True))==expected[i][j]
    return n*n


def exact_norm(values):
    return max(sum(map(abs,row)) for row in T.exact_inverse_values(values))


def random_cases():
    rng=random.Random(280);entry_checks=0
    for k in range(100):
        m=2+(k%2);blocks=[]
        for board in range(2):
            skew=rng.randint(-3,3)/32
            a=T.csr([[4.,-1.+skew],[-1.-skew,4.]])
            columns=(0,m-1) if board==0 else tuple(range(m))
            b=np.array([[-rng.randint(1,4)/16 for _ in columns] for _ in range(2)],dtype=np.float64)
            if k%3==0:b[1,0]=0.
            blocks.append((a,b,columns))
        d=[[(3.-2.**-40,3.+2.**-40) if i==j else (-.125,-.125) for j in range(m)] for i in range(m)]
        view=P.JoinedRows(blocks,d,P.Meter());expected=expected_matrix(blocks,d)
        entry_checks+=check_view(view,expected)
        certs=[P.coercivity_interval_certificate(view,view.interval_entries(),{'case':k},P.Meter(),bound_mode=mode,packed=packed)
               for mode,packed in [('refined',False),('path-only',False),('path-only',True)]]
        for cert in certs:assert F(cert['inverse_infinity_upper'])>=exact_norm(expected)
        assert certs[1]['inverse_infinity_upper']==certs[2]['inverse_infinity_upper']
        corner=[row[:] for row in expected]
        for i in range(m):
            for j in range(m):corner[4+i][4+j]=F(d[i][j][(i+j+k)%2])
        for cert in certs:assert F(cert['inverse_infinity_upper'])>=exact_norm(corner)
    return {'seed':280,'cases':100,'scalar_row_lookup_comparisons':entry_checks,
            'exact_inverse_bound_checks':600,'bound_modes':['refined-list','path-only-list','path-only-packed'],'shared_terminal_and_sparse_mapping':'covered','status':'PASS'}


def mutations():
    blocks,d,_=T.separated_fixture()
    local=[(a,b,(0,1)) for a,b in blocks]
    view=P.JoinedRows(local,d,P.Meter())
    packet,h=P.produce_coercivity_tree(view,{},P.Meter())
    outcomes=[]
    for name,target,index in [('A',blocks[0][0].data,0),('B',blocks[0][1],(0,0)),
                              ('midpoint',view.midpoint[0],0)]:
        old=target[index];target[index]=float(old)+.125
        try:P.verify_coercivity_tree(view,{},packet,h,P.Meter())
        except ValueError:outcomes.append(name)
        else:raise AssertionError('stale content accepted')
        finally:target[index]=old
    before=P.coercivity_interval_certificate(view,view.interval_entries(),{},P.Meter())
    old=d[0][0];d[0][0]=(old[0]-2.**-40,old[1]+2.**-40)
    after=P.coercivity_interval_certificate(view,view.interval_entries(),{},P.Meter())
    assert before['interval_operator_sha256']!=after['interval_operator_sha256']
    d[0][0]=old
    return {'stale_packet_refusals':outcomes,'terminal_interval_binding':'changed independently of midpoint hash','status':'PASS'}


def malformed_live_view():
    blocks,d,_=T.separated_fixture()
    view=P.JoinedRows([(a,b,(0,1)) for a,b in blocks],d,P.Meter())
    old=d[0];d[0]=old[:1]
    try:
        try:view.interval_entries()
        except ValueError:pass
        else:raise AssertionError('shortened live interval row accepted')
    finally:d[0]=old
    old=d[0][0];d[0][0]=(2.,1.)
    try:
        try:view.interval_entries()
        except ValueError:pass
        else:raise AssertionError('reversed live interval accepted')
    finally:d[0][0]=old
    blocks[0][0].resize((3,3))
    try:view.validate()
    except ValueError:pass
    else:raise AssertionError('stale cached coordinate layout accepted')
    return {'live_interval_refusals':2,'changed_CSR_shape_refusals':1,'status':'PASS'}


def packed_mutations():
    a=T.grid(4);packet,h=P.produce_coercivity_tree(a,{},P.Meter(),packed=True)
    for field,change in [('parent',lambda v:array.array('Q',v)),
                         ('edge',lambda v:array.array('f',v)),
                         ('order',lambda v:array.array('I',[0]*16))]:
        bad=copy.deepcopy(packet);bad[field]=change(bad[field])
        try:P.verify_coercivity_tree(a,{},bad,P.coercivity_digest(bad),P.Meter(),path_only=True)
        except ValueError:pass
        else:raise AssertionError('fresh-hash malformed packed witness accepted')
    bad=copy.deepcopy(packet);bad['edge'][1]=float('inf')
    try:P.verify_coercivity_tree(a,{},bad,P.coercivity_digest(bad),P.Meter(),path_only=True)
    except ValueError:pass
    else:raise AssertionError('nonfinite packed edge accepted')
    return {'fresh_hash_packed_refusals':4,'status':'PASS'}


def one_sided():
    a=T.csr([[2.,-1.],[0.,2.]])
    view=P.JoinedRows([(a,np.array([[-.25],[-.25]]),(0,))],[[(2.,2.)]],P.Meter())
    try:P.produce_coercivity_tree(view,{},P.Meter())
    except ValueError as exc:
        assert 'structural symmetry' in str(exc)
        return {'status':'REFUSED AS REQUIRED','reason':str(exc)}
    raise AssertionError('one-sided original support accepted')


if __name__=='__main__':
    result={'synthetic_only':True,'random':random_cases(),'mutations':mutations(),'one_sided':one_sided(),'malformed_live_view':malformed_live_view(),'packed_mutations':packed_mutations(),
            'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in [Path(__file__),HERE/'fixture/prototype.py']}}
    print(json.dumps(result,indent=2))
