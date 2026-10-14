from fractions import Fraction as F
import math, random, struct, sys, json

def avg(a,b):
    if a==b:return (a,b)
    if a==-b:return (0.,0.)
    ah=a*.5; bh=b*.5
    lo=math.nextafter(math.nextafter(ah,-math.inf)+math.nextafter(bh,-math.inf),-math.inf)
    hi=math.nextafter(math.nextafter(ah,math.inf)+math.nextafter(bh,math.inf),math.inf)
    return max(lo,min(a,b)),min(hi,max(a,b))

def inverse(A):
    n=len(A);a=[[F(v) for v in row]+[F(i==j) for j in range(n)] for i,row in enumerate(A)]
    for i in range(n):
        k=next((k for k in range(i,n) if a[k][i]),None)
        if k is None:raise ValueError('singular')
        a[i],a[k]=a[k],a[i];p=a[i][i];a[i]=[v/p for v in a[i]]
        for j in range(n):
            if j!=i:
                p=a[j][i];a[j]=[v-p*w for v,w in zip(a[j],a[i])]
    return [r[n:] for r in a]

def infnorm(A):return max(sum(abs(v) for v in r) for r in A)
def ldl_pivots(A):
    a=[[F(v) for v in r] for r in A];out=[]
    for k in range(len(a)):
        p=a[k][k];out.append(p)
        if p<=0:return out
        for i in range(k+1,len(a)):
            for j in range(i,len(a)):
                a[i][j]-=a[k][i]*a[k][j]/p;a[j][i]=a[i][j]
    return out

def sym(A):return [[(F(A[i][j])+F(A[j][i]))/2 for j in range(len(A))] for i in range(len(A))]

def joined(wire=1,skew=100):
    # Free KA: two nodes; free KB: one node; one terminal each.
    # KA H_A=2I, B_A=(-1,-1), D_A=2 => Schur_A=1.
    # KB A_B=1, B_B=-1, D_B=1 => Schur_B=0 (floating board).
    return [[2,skew,0,-1,0],[-skew,2,0,-1,0],[0,0,1,0,-1],[-1,-1,0,2+wire,-wire],[0,0,-1,-wire,1+wire]]

small=math.ulp(0.);maxf=sys.float_info.max
edges=[0.,small,-small,2*small,-2*small,sys.float_info.min,-sys.float_info.min,1.,-1.,maxf,-maxf,math.nextafter(maxf,0),math.nextafter(-maxf,0),100.,-100.]
checks=0
for a in edges:
    for b in edges:
        lo,hi=avg(a,b);exact=(F(a)+F(b))/2
        assert math.isfinite(lo) and math.isfinite(hi) and F(lo)<=exact<=F(hi),(a,b,lo,hi,exact)
        assert min(a,b)<=lo<=hi<=max(a,b)
        checks+=1
rng=random.Random(71054)
while checks<25225:
    a=struct.unpack('d',rng.getrandbits(64).to_bytes(8,'little'))[0]
    b=struct.unpack('d',rng.getrandbits(64).to_bytes(8,'little'))[0]
    if not(math.isfinite(a) and math.isfinite(b)):continue
    lo,hi=avg(a,b);exact=(F(a)+F(b))/2
    assert F(lo)<=exact<=F(hi)
    assert (exact==0)==(a==-b)
    checks+=1

strong=[[2,100],[-100,2]]
assert sym(strong)==[[2,0],[0,2]]
assert infnorm(inverse(strong))**2 <= 2*infnorm(inverse(sym(strong)))**2
M=joined();H=sym(M);p=ldl_pivots(H)
assert all(x>0 for x in p)
# Exact certificate input values for existing block inverse bound:
# A inverses: KA=1/2, KB=1; B norms KA=(1,2), KB=(1,1).
# Q=[[2,-1],[-1,1]], inv(Q)=[[1,1],[1,2]], infinity norm=3.
# forward=max(1/2*1,1*1)=1; backward=max(1/2*2,1*1)=1.
block_bound=F(12)
assert infnorm(inverse(H))<=block_bound
assert infnorm(inverse(M))**2<=len(M)*block_bound**2
# Removing sole wire leaves floating KB+terminal nullspace.
try: inverse(joined(wire=0))
except ValueError:pass
else:raise AssertionError('floating KB not singular')
assert any(x<=0 for x in ldl_pivots(sym(joined(wire=0))))
# Invertible M is insufficient when H is indefinite or semidefinite.
for bad in ([[1,2],[-2,-1]],[[0,1],[-1,0]]):
    inverse(bad)
    assert any(x<=0 for x in ldl_pivots(sym(bad)))
print(json.dumps({'status':'MATHEMATICAL_FIXTURE_PASS','scope':'exact-rational tiny synthetic operators; no original data, numerical loads, qualification or campaign claim','half_sum_pairs_checked':checks,'joined_order':len(M),'joined_H_LDL_pivots':list(map(str,p)),'joined_H_inverse_inf_exact':str(infnorm(inverse(H))),'joined_M_inverse_inf_exact':str(infnorm(inverse(M))),'reference_block_inverse_inf_bound':str(block_bound),'original_inverse_inf_squared_bound':str(len(M)*block_bound**2),'removed_wire_rejected':True,'invertible_indefinite_and_semidefinite_reference_rejected':True},sort_keys=True))
