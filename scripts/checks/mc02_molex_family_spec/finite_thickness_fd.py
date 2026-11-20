"""2-D finite-difference capacitance matrix of a layered multi-conductor FFC cross-section (per metre)."""
import numpy as np, scipy.sparse as sp, scipy.sparse.linalg as spl, sys, json
EPS0=8.8541878128e-12
def solve(t_cu=0.10, t_ins=0.086, eps_d=3.2, h=0.0125, W=14.0, H=8.0, n=8, p=0.5, w=0.30, layered=True):
    nx,ny=int(round(W/h)),int(round(H/h))
    x=(np.arange(nx)+0.5)*h-W/2; y=(np.arange(ny)+0.5)*h-H/2
    X,Y=np.meshgrid(x,y,indexing='ij')
    eps=np.ones((nx,ny))
    width=p*(n+1)
    if layered:
        eps[(np.abs(X)<=width/2)&(np.abs(Y)<=t_cu/2+t_ins)]=eps_d
    else:
        eps[:]=eps_d
    cond=-np.ones((nx,ny),int)
    centers=[(i-(n-1)/2)*p for i in range(n)]
    for k,c in enumerate(centers):
        cond[(np.abs(X-c)<=w/2)&(np.abs(Y)<=t_cu/2)]=k
    N=nx*ny; idx=np.arange(N).reshape(nx,ny)
    # face permittivities (harmonic mean)
    ex=2*eps[1:,:]*eps[:-1,:]/(eps[1:,:]+eps[:-1,:]); ey=2*eps[:,1:]*eps[:,:-1]/(eps[:,1:]+eps[:,:-1])
    rows=[];cols=[];vals=[];diag=np.zeros((nx,ny))
    def add(a,b,e):
        rows.extend([a.ravel(),b.ravel()]);cols.extend([b.ravel(),a.ravel()]);vals.extend([-e.ravel(),-e.ravel()])
    add(idx[1:,:],idx[:-1,:],ex); add(idx[:,1:],idx[:,:-1],ey)
    diag[1:,:]+=ex;diag[:-1,:]+=ex;diag[:,1:]+=ey;diag[:,:-1]+=ey
    # outer boundary grounded at half-cell: add 2*eps to diag on boundary cells
    diag[0,:]+=2*eps[0,:];diag[-1,:]+=2*eps[-1,:];diag[:,0]+=2*eps[:,0];diag[:,-1]+=2*eps[:,-1]
    A=sp.coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(N,N)).tocsr()+sp.diags(diag.ravel())
    free=(cond.ravel()<0)
    Aff=A[free][:,free].tocsc(); lu=spl.splu(Aff)
    Afc=A[free]
    C=np.zeros((n,n))
    for j in range(n):
        V=np.zeros(N); V[cond.ravel()==j]=1.0
        rhs=-(Afc@V); V[free]=lu.solve(rhs)
        Q=A@V  # charge*... per cell (units eps0)
        for i in range(n): C[i,j]=Q[cond.ravel()==i].sum()*EPS0
    return C  # F/m, includes capacitance to the far box; see open_boundary
def readings(C):
    n=len(C); i,j=n//2-1,n//2
    P=np.linalg.pinv(C); q=np.zeros(n); q[i]=1;q[j]=-1; v=P@q
    return {'pair_floating':1/(v[i]-v[j])*1e12,'pair_grounded':(C[i,i]+C[j,j]-2*C[i,j])/4*1e12,
            'interior_vs_all':C[i,i]*1e12,'edge_vs_all':C[0,0]*1e12,'mutual_adj':-C[i,j]*1e12}


def open_boundary(C):
    """Eliminate the far grounded box as a floating zero-charge conductor (Schur complement)."""
    c = C.sum(axis=0)
    return C - np.outer(c, c) / c.sum()
