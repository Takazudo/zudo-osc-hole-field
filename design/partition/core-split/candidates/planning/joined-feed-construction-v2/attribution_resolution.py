"""Outward error enclosures for the single selected field and Stage C screen.

No new load is solved. Residuals are evaluated at the computed field, and the
verified block inverse norm bounds its distance from the exact selected solution.
Reference block bounds apply only to the complete symmetric part H of the stored
joined operator M. Coercivity converts them once to an original M inverse bound;
residuals and all selected-field calculations continue to use original M.
"""
import math
import numpy as np

import attribution_uniqueness as U
from resistance_attribution import need


def pair(x):
    f=float(x)
    need(math.isfinite(f), 'nonfinite interval field')
    return (f,f) if np.longdouble(f)==x else U.enclosure(f,f)


def sum_intervals(values):
    result=U.ZERO
    for value in values:
        result=U.add(result,value)
    return result


def matrix_norms(B):
    """Outward row/column sums; terminals <=8, no large transposed copy."""
    rows=0.;columns=[0.]*B.shape[1]
    for row in B:
        acc=0.
        for j,x in enumerate(row):
            v=abs(float(x));acc=U.upper_add(acc,v);columns[j]=U.upper_add(columns[j],v)
        rows=max(rows,acc)
    return rows,max(columns,default=0.)


def network_inverse_bound(boards,coupled):
    forward=backward=0.
    diagonal=coupled['inverse_infinity_upper']
    for cert in boards.values():
        inv=cert['inverse_infinity_upper']
        diagonal=max(diagonal,inv)
        forward=max(forward,U.upper_mul(inv,cert['B_infinity_upper']))
        backward=max(backward,U.upper_mul(inv,cert['BT_infinity_upper']))
    bound=U.upper_mul(U.upper_mul(U.upper_add(1.,forward),diagonal),U.upper_add(1.,backward))
    references=[c.get('analysis_reference_only',False) for c in boards.values()]+[coupled.get('analysis_reference_only',False)]
    need(all(references) or not any(references),'mixed original/reference inverse certificates')
    if all(references):
        need(all(c.get('status')=='SYMMETRIC_PART_REFERENCE_SPD' for c in boards.values()) and
             coupled.get('status')=='EXACT_COUPLED_REFERENCE_SCHUR_SPD','reference certificate status differs')
        n=sum(c['order'] for c in boards.values())+coupled['order']
        need(type(n) is int and 0<n<=2**53,'invalid full-network reference dimension')
        factor=math.isqrt(n)
        if factor*factor<n:factor+=1
        # x'Mx=x'Hx gives ||M^-1||inf <= sqrt(N)||H^-1||inf. Integer
        # ceiling avoids assuming libm square-root rounding. Apply once globally.
        bound=U.upper_mul(bound,float(factor))
    return bound


def residual_bound(A,B,D,x,t,f,wire_injection,budget):
    """Infinity bound of exact free + terminal residual, with all rounding."""
    a=A.tocsr()
    bound=0.
    for i in range(len(x)):
        budget.check()
        residual=pair(f[i])
        for p in range(a.indptr[i],a.indptr[i+1]):
            residual=U.sub(residual,U.mul(pair(a.data[p]),pair(x[a.indices[p]])))
        for j in range(len(t)):
            residual=U.sub(residual,U.mul(pair(B[i,j]),pair(t[j])))
        bound=max(bound,U.magnitude(residual))
    for j in range(len(t)):
        residual=U.ZERO
        for i in range(len(x)):
            budget.check()
            residual=U.sub(residual,U.mul(pair(B[i,j]),pair(x[i])))
        for k in range(len(t)):
            residual=U.sub(residual,U.mul(pair(D[j,k]),pair(t[k])))
        residual=U.sub(residual,wire_injection[j])
        bound=max(bound,U.magnitude(residual))
    return bound


def field_interval(x,error,fixed=False):
    return U.ZERO if fixed else U.add(pair(x),(-error,error))


def energy_interval(matrix,nodes,field,error,fixed,budget):
    """Enclose exact local quadratic form; preserve negative lower bounds."""
    m=matrix.tocsr();result=U.ZERO
    for i in range(len(nodes)):
        budget.check()
        vi=field_interval(field[nodes[i]],error,bool(fixed[nodes[i]]))
        for p in range(m.indptr[i],m.indptr[i+1]):
            j=int(m.indices[p]);vj=field_interval(field[nodes[j]],error,bool(fixed[nodes[j]]))
            result=U.add(result,U.mul(U.mul(vi,pair(m.data[p])),vj))
    return result


def reaction_interval(K,nodes,field,error,fixed,supports,vt,rt,budget):
    """Exact held functional: original copper plus whole termination stamps."""
    result=U.ZERO
    for i in nodes:
        budget.check()
        for p in range(K.indptr[i],K.indptr[i+1]):
            j=int(K.indices[p])
            result=U.add(result,U.mul(pair(K.data[p]),field_interval(field[j],error,bool(fixed[j]))))
    held=set(map(int,nodes))
    for j,(ns,w) in enumerate(supports):
        delta=U.sub(sum_intervals(U.mul(pair(weight),field_interval(field[node],error,bool(fixed[node])))
                                 for node,weight in zip(ns,w)),field_interval(vt[j],error))
        current=U.div_positive(delta,pair(rt))
        for node,weight in zip(ns,w):
            if int(node) in held:
                result=U.add(result,U.mul(pair(weight),current))
    return result


def screen(target,copper,reaction):
    """Predeclared 10%/resolved-nonzero screen; uncertainty never favors via."""
    if copper[0] <= 0:
        return {'status':'INCONCLUSIVE','reason':'copper energy enclosure includes zero'}
    share=U.div_positive(target,copper)
    resolved_nonzero=reaction[0] > 0 or reaction[1] < 0
    if share[1] < .1:
        status='REJECTED'
    elif share[0] >= .1 and resolved_nonzero:
        status='SUPPORTED'
    elif reaction == U.ZERO:
        status='REJECTED'
    else:
        status='INCONCLUSIVE'
    return {'status':status,'share_interval':list(share),'reaction_interval_A':list(reaction),
            'resolved_nonzero_reaction':resolved_nonzero,'minimum_share':.1}
