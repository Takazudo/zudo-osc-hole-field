"""Exact H(div) edge-curl trial enrichment; conditional numerical diagnostic.

The caller owns physical containment and the hash-bound raw/conserved reference.
No geometry, finite source trace, material class or hardware admission changes.
Energy and cross work are ohms for normalized unit-current columns.
"""
from fractions import Fraction as F
from math import isqrt


def dot(a, b):
    return sum((x*y for x,y in zip(a,b)), F())


def sub(a,b):
    return tuple(x-y for x,y in zip(a,b))


def cross(a,b):
    return a[0]*b[1]-a[1]*b[0]


def geometry(points):
    p=tuple(tuple(F(x) for x in a) for a in points)
    if len(p)!=3 or any(len(a)!=2 for a in p):raise ValueError('triangle required')
    d=cross(sub(p[1],p[0]),sub(p[2],p[0]))
    if d<=0:raise ValueError('strictly positive orientation required')
    grads=tuple(((p[(i+1)%3][1]-p[(i+2)%3][1])/d,
                 (p[(i+2)%3][0]-p[(i+1)%3][0])/d) for i in range(3))
    return p,d/2,grads


def edge_bubble(points, edge):
    p,area,grads=geometry(points)
    edge=tuple(tuple(F(x) for x in a) for a in edge)
    if len(edge)!=2 or edge[0]==edge[1] or not all(a in p for a in edge):
        raise ValueError('distinct actual edge endpoints required')
    a,b=(p.index(v) for v in edge)
    values=[]
    for k in range(3):
        g=tuple((grads[b][i] if k==a else F())+(grads[a][i] if k==b else F()) for i in range(2))
        values.append((g[1],-g[0]))
    return tuple(values)


def check_patch(triangles, fields, edge):
    if len(triangles)!=2 or len(fields)!=2:raise ValueError('two triangles required')
    edge=tuple(tuple(map(F,p)) for p in edge)
    pp=[geometry(t)[0] for t in triangles]
    if set(pp[0]) & set(pp[1]) != set(edge):raise ValueError('wrong shared edge')
    third=[next(p for p in t if p not in edge) for t in pp]
    direction=sub(edge[1],edge[0])
    if cross(direction,sub(third[0],edge[0]))*cross(direction,sub(third[1],edge[0]))>=0:
        raise ValueError('overlapping or degenerate patch')
    internal=[]
    for p,field in zip(pp,fields):
        if len(field)!=3 or any(len(v)!=2 for v in field):raise ValueError('three two-dimensional P1 vectors required')
        grads=geometry(p)[2]
        if sum((dot(v,g) for v,g in zip(field,grads)),F()):raise ValueError('nonzero divergence')
        for i in range(3):
            a,b=p[i],p[(i+1)%3];d=sub(b,a);normal=(d[1],-d[0])
            traces={a:dot(field[i],normal), b:dot(field[(i+1)%3],normal)}
            if {a,b}==set(edge):internal.append(traces)
            elif any(traces.values()):raise ValueError('changed outer normal trace')
    if len(internal)!=2 or any(internal[0][p]+internal[1][p] for p in edge):
        raise ValueError('shared normal trace mismatch')


def p1_work(points, u, v, sheet_resistance=F(1)):
    p,area,grads=geometry(points)
    if len(u)!=3 or len(v)!=3 or any(len(x)!=2 for x in tuple(u)+tuple(v)):
        raise ValueError('three two-dimensional vectors per affine field required')
    rho=F(sheet_resistance)
    if rho<=0:raise ValueError('positive sheet resistance required')
    su=tuple(sum((x[i] for x in u),F()) for i in range(2))
    sv=tuple(sum((x[i] for x in v),F()) for i in range(2))
    return rho*area/12*(sum((dot(a,b) for a,b in zip(u,v)),F())+dot(su,sv))


def sqrt_up(x, bits=80):
    x=F(x)
    if x<0:raise ValueError('negative squared norm')
    n=x.numerator << (2*bits);d=x.denominator
    k=isqrt(n//d)
    if k*k*d<n:k+=1
    return F(k,1<<bits)


def psd(m):
    return len(m)==2 and all(len(r)==2 for r in m) and m[0][1]==m[1][0] and min(m[0][0],m[1][1])>=0 and m[0][0]*m[1][1]>=m[0][1]**2


def gram_update(upper, lower, raw_work_intervals, perturbation_gram, correction_energy):
    """Conditional on U>=Gram(Q), ||raw_i-Q_i||²<=C_i, exact H=Gram(W).

    Entries/energies are ohms for normalized unit-current columns. Work intervals
    enclose <raw_i,W_j>, NOT an off-diagonal of an upper-only metric matrix.
    """
    U=[[F(x) for x in row] for row in upper];L=[[F(x) for x in row] for row in lower]
    H=[[F(x) for x in row] for row in perturbation_gram];C=list(map(F,correction_energy))
    if not all(psd(m) for m in (U,L,H)) or not psd([[U[i][j]-L[i][j] for j in range(2)] for i in range(2)]):
        raise ValueError('invalid source Gram bounds')
    if len(C)!=2 or min(C)<0:raise ValueError('invalid correction energy')
    if len(raw_work_intervals)!=2 or any(len(r)!=2 for r in raw_work_intervals):raise ValueError('two by two work intervals required')
    G=[]
    for i in range(2):
        row=[]
        for j in range(2):
            lo,hi=map(F,raw_work_intervals[i][j])
            if lo>hi:raise ValueError('inverted cross interval')
            sanity=(sqrt_up(U[i][i])+sqrt_up(C[i]))*sqrt_up(H[j][j])
            if lo>sanity or hi < -sanity:raise ValueError('impossible raw cross work')
            radius=sqrt_up(C[i]*H[j][j])
            row.append((lo-radius,hi+radius))
        G.append(row)
    midpoint=[[F() for j in range(2)] for i in range(2)]
    radii=[[F() for j in range(2)] for i in range(2)]
    for i in range(2):
        for j in range(2):
            lo=G[i][j][0]+G[j][i][0]+H[i][j]
            hi=G[i][j][1]+G[j][i][1]+H[i][j]
            midpoint[i][j]=(lo+hi)/2;radii[i][j]=(hi-lo)/2
    out=[[U[i][j]+midpoint[i][j]+(sum(radii[i],F()) if i==j else F()) for j in range(2)] for i in range(2)]
    if not psd([[out[i][j]-L[i][j] for j in range(2)] for i in range(2)]):
        raise ValueError('updated upper contradicts lower; reject, do not clip')
    return out


def rt0_values(points, local_outward_flux):
    """Affine canonical RT0 values; face i is opposite vertex i."""
    p,area,_=geometry(points)
    if len(local_outward_flux)!=3:raise ValueError('three opposite-face fluxes required')
    flux=tuple(map(F,local_outward_flux))
    return tuple(tuple(sum((flux[i]*(x[j]-p[i][j]) for i in range(3)),F())/(2*area)
                       for j in range(2)) for x in p)


def patch_work(triangles, flux_columns, edge, sheet_resistance):
    """Exact two-column raw work and one common bubble energy on this patch."""
    if len(flux_columns)!=2 or any(len(t)!=3 or any(len(v)!=2 for v in t) for t in flux_columns):
        raise ValueError('two triangles, three local faces, two source columns required')
    bubble=tuple(edge_bubble(t,edge) for t in triangles)
    check_patch(triangles,bubble,edge)
    g=[F(),F()];h=F()
    for tri,flux,c in zip(triangles,flux_columns,bubble):
        h+=p1_work(tri,c,c,sheet_resistance)
        for k in range(2):
            q=rt0_values(tri,[row[k] for row in flux])
            g[k]+=p1_work(tri,q,c,sheet_resistance)
    if h<=0:raise ValueError('positive bubble energy required')
    return g,h


def combine_patches(rows):
    """Disjointness is a geometric caller premise, never inferred from energy.

    Round each chosen -g/h coefficient to binary64, then treat it as exact.
    Any finite coefficient defines a valid trial; optimality is not assumed.
    """
    import math
    G=[[F() for _ in range(2)] for _ in range(2)]
    H=[[F() for _ in range(2)] for _ in range(2)]
    coefficients=[]
    for row in rows:
        g=list(map(F,row['raw_work_exact']));h=F(row['bubble_energy_exact'])
        if len(g)!=2 or h<=0:raise ValueError('invalid patch work/energy')
        try:beta=[float(-x/h) for x in g]
        except OverflowError as exc:raise ValueError('unrepresentable trial coefficient') from exc
        if not all(math.isfinite(x) for x in beta):raise ValueError('nonfinite trial coefficient')
        b=list(map(F,beta));coefficients.append(beta)
        for i in range(2):
            for j in range(2):G[i][j]+=g[i]*b[j];H[i][j]+=b[i]*b[j]*h
    return G,H,coefficients


def upper_float_matrix(matrix):
    """A directed PSD allowance encloses ALL final symmetric float rounding."""
    from scripts.pcbgen.observation_support_bound import upward
    m=[[F(x) for x in row] for row in matrix]
    if not psd(m):raise ValueError('PSD matrix required')
    f=[[float(x) for x in row] for row in m]
    error=[[abs(F(f[i][j])-m[i][j]) for j in range(2)] for i in range(2)]
    for i in range(2):f[i][i]=upward(F(f[i][i])+sum(error[i],F()))
    if not psd([[F(f[i][j])-m[i][j] for j in range(2)] for i in range(2)]):
        raise ValueError('matrix serialization enclosure failed')
    return f


def transfer_interval(upper,lower):
    """Whole-domain Loewner polarization, not an upper-matrix off-diagonal."""
    U=[[F(x) for x in row] for row in upper];L=[[F(x) for x in row] for row in lower]
    delta=[[U[i][j]-L[i][j] for j in range(2)] for i in range(2)]
    if not all(psd(m) for m in (U,L,delta)):raise ValueError('invalid transfer Gram enclosure')
    center=(U[0][1]+L[0][1])/2;radius=sqrt_up(delta[0][0]*delta[1][1])/2
    return center-radius,center+radius
