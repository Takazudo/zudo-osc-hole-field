"""Independent structural/energy oracle for verifier-owned forest construction.

Tiny explicit adjacency and exact inverses are reference-only, never producer inputs.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
import sys
from pathlib import Path
import random
import inspect
import itertools
from unittest.mock import patch
import json
import hashlib
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'fixture'))
import test_prototype as T
P,F,np=T.P,T.F,T.np


def matrix(n,edges,root,ground=2.,skew=False,positive=None,deficit=0.):
    values=np.zeros((n,n),dtype=np.float64)
    for i,j,c in edges:
        values[i,i]+=c;values[j,j]+=c
        s=c/8 if skew else 0.
        values[i,j]=-c+s;values[j,i]=-c-s
    values[root,root]+=ground
    if positive is not None:
        i,j,c=positive;assert not values[i,j] and not values[j,i]
        values[i,j]=values[j,i]=c;values[i,i]+=c;values[j,j]+=c
    values[(root+1)%n,(root+1)%n]-=deficit
    return T.csr(values)


def reference(a):
    n=a.shape[0]
    exact=[[F(float(a[i,j])) for j in range(n)] for i in range(n)]
    sym=[[(exact[i][j]+exact[j][i])/2 for j in range(n)] for i in range(n)]
    margins=[sym[i][i]-sum(abs(sym[i][j]) for j in range(n) if j!=i) for i in range(n)]
    root=max(range(n),key=lambda i:margins[i]);g=margins[root]
    assert g>0
    # Component SETS deliberately differ from producer DSU and pointer reversal.
    components=[{i} for i in range(n)];selected=[]
    for i in range(n):
        for j in range(i+1,n):
            if sym[i][j]>=0:continue
            left=next(c for c in components if i in c)
            right=next(c for c in components if j in c)
            if left is right:continue
            selected.append((i,j,-sym[i][j]))
            components.remove(left);components.remove(right);components.append(left|right)
    assert len(components)==1 and len(selected)==n-1
    adjacency=[[] for _ in range(n)]
    for i,j,c in selected:
        adjacency[i].append((j,c));adjacency[j].append((i,c))
    path=[None]*n;path[root]=1/g;stack=[root]
    while stack:
        i=stack.pop()
        for j,c in adjacency[i]:
            if path[j] is None:path[j]=path[i]+1/c;stack.append(j)
    r=max(path);b=n*r;delta=max([F(0)]+[-x for x in margins])
    assert delta*b<1
    bound=b/(1-delta*b)
    norm=max(sum(map(abs,row)) for row in T.exact_inverse_values(exact))
    return {'root':root,'edges':selected,'rmax':r,'bound':bound,'inverse_norm':norm}


def check(a):
    ref=reference(a);meter=P.Meter();cert=P.certify_forest(a,{},meter)
    assert cert['status']=='CERTIFIED'
    bound=F(cert['inverse_infinity_upper'])
    assert bound>=ref['bound']>=ref['inverse_norm']
    assert bound<=ref['bound']*F(1000000000001,1000000000000)
    return {'order':a.shape[0],'root':ref['root'],'exact_rmax':str(ref['rmax']),
            'exact_tree_bound':str(ref['bound']),'certified_bound':cert['inverse_infinity_upper'],
            'exact_inverse_norm':float(ref['inverse_norm'])}


def wrapper_and_mutations():
    coupled=[]
    for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
        blocks,d,exact=T.separated_fixture(**kwargs);meter=P.Meter()
        view=P.JoinedRows([(a,b,(0,1)) for a,b in blocks],d,meter)
        cert=P.coercivity_interval_certificate(view,view.interval_entries(),{},meter,
                    bound_mode='path-only',exact_kernel='compact',forest=True)
        ref=max(sum(map(abs,row)) for row in T.exact_inverse_values(exact))
        assert F(cert['inverse_infinity_upper'])>=ref
        for choice in itertools.product([0,1],repeat=4):
            corner=[row[:] for row in exact]
            for (i,j),side in zip(itertools.product(range(2),repeat=2),choice):
                corner[4+i][4+j]=F(d[i][j][side])
            assert F(cert['inverse_infinity_upper'])>=max(sum(map(abs,row)) for row in T.exact_inverse_values(corner))
        coupled.append({'case':name,'bound':cert['inverse_infinity_upper'],'exact_original_norm':float(ref)})
    mutations=0
    for mode in ('matrix','context'):
        a=T.grid(4);context={'identity':'original'}
        class Mutator(P.Meter):
            changed=False
            def charge(self,*args,**kwargs):
                super().charge(*args,**kwargs)
                if self.phase=='forest_norm' and not self.changed:
                    self.changed=True
                    if mode=='matrix':a.data[0]+=.125
                    else:context['identity']='changed'
        try:P.certify_forest(a,context,Mutator())
        except ValueError as exc:
            assert 'changed during proof' in str(exc);mutations+=1
        else:raise AssertionError('persistent mutation accepted')
    assert list(inspect.signature(P.certify_forest).parameters)==['a','context','meter']
    a=T.grid(4);seen=[];original=P.operator_row
    def traced(operator,row):
        seen.append(row)
        yield from original(operator,row)
    with patch.object(P,'operator_row',side_effect=traced):P.certify_forest(a,{},P.Meter())
    assert seen==list(range(16))
    return {'complete_interval_inverse_checks':51,'coupled':coupled,
            'persistent_mutation_refusals':mutations,'exhaustive_row_call_order':seen,
            'no_external_summary_parameter':True,'status':'PASS'}


def run():
    cases=[]
    edges=[(0,4,2.),(1,2,.5),(1,3,4.),(2,4,1.25)]
    for skew in [False,True]:
        cases.append(check(matrix(5,edges,3,skew=skew,positive=(0,2,.0625))))
    edges=[(0,7,2.),(1,6,.25),(2,3,.5),(2,4,4.),(3,5,1.25),(4,6,.75),(5,7,3.)]
    cases.append(check(matrix(8,edges,7,ground=.125,skew=True,deficit=2.**-35)))
    rng=random.Random(285)
    for case in range(100):
        n=6+case%5;permutation=list(range(n));rng.shuffle(permutation)
        pairs={tuple(sorted((permutation[i],permutation[i+1]))) for i in range(n-1)}
        for _ in range(n):
            i,j=rng.sample(range(n),2);pairs.add(tuple(sorted((i,j))))
        edges=[(i,j,rng.randint(1,16)/8) for i,j in sorted(pairs)]
        root=rng.randrange(n)
        available=[(i,j) for i in range(n) for j in range(i+1,n) if (i,j) not in pairs]
        positive=(*available[0],.0625) if available else None
        check(matrix(n,edges,root,ground=.5,skew=True,positive=positive,
                     deficit=2.**-35 if case%2 else 0.))
    return {'seed':285,'forced_nonroot_reroot_cases':cases,'random_cases':100,
            'total_exact_tree_energy_and_inverse_checks':103,'status':'PASS'}


if __name__=='__main__':
    print(json.dumps({'synthetic_only':True,'results':run(),'wrapper_mutations_and_row_pass':wrapper_and_mutations(),
        'sha256':{str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in [Path(__file__),HERE/'fixture/prototype.py']}},indent=2))
