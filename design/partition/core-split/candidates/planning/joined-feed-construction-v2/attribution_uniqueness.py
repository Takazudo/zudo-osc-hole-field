"""Independent bounded interval LDL certificate for exact stored sparse operators.

This checker never solves a load or changes the production solver. Binary64
coefficients start as singleton real intervals. Each scalar operation rounds
outwards by one nextafter, including underflow. Positive lower pivot bounds
prove exact LDL positivity by induction. Fill/work exhaustion is unresolved.
No approximate-zero pruning or dense board conversion occurs. Optional symmetric-
part references are analysis only: original matrices and solver inputs are never
modified, and reference positivity is not reported as original-operator SPD.
"""
import hashlib
import json
import math
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp
from scipy.sparse.csgraph import reverse_cuthill_mckee

from resistance_attribution import need, digest

METHOD = 'outward-binary64-sparse-LDL-v1'
REFERENCE_METHOD = 'original-operator-symmetric-part-coercivity-v1'
FRONTIER_STORAGE = 'lazy-frontier-interval-LDL-v1'
REFERENCE_ORDER = 'rcm-original-structural-union-v1'
ZERO = (0., 0.)


def enclosure(lo, hi):
    lo, hi = math.nextafter(lo, -math.inf), math.nextafter(hi, math.inf)
    need(math.isfinite(lo) and math.isfinite(hi), 'UNRESOLVED: interval overflow')
    return lo, hi


def add(a, b):
    return enclosure(a[0]+b[0], a[1]+b[1])


def sub(a, b):
    return enclosure(a[0]-b[1], a[1]-b[0])


def mul(a, b):
    if a == ZERO or b == ZERO:
        return ZERO
    p = [x*y for x in a for y in b]
    return enclosure(min(p), max(p))


def div_positive(a, b):
    need(b[0] > 0, 'UNRESOLVED: nonpositive interval divisor')
    return mul(a, enclosure(1/b[1], 1/b[0]))


def magnitude(a):
    return max(abs(a[0]), abs(a[1]))


def upper_add(a, b):
    return add((a, a), (b, b))[1]


def upper_mul(a, b):
    return mul((a, a), (b, b))[1]


@dataclass
class Work:
    # Caps are per diagnostic, shared by both board checks and small Schur.
    max_entries: int = 4_000_000
    max_input_nnz: int = 16_000_000
    max_updates: int = 20_000_000
    checkpoint: object = lambda: None
    updates: int = 0
    peak_entries: int = 0

    def check(self, entries, updates=0):
        self.updates += updates
        self.peak_entries = max(self.peak_entries, entries)
        need(entries <= self.max_entries, f'UNRESOLVED: certificate sparse fill cap (entries={entries}, maximum={self.max_entries})')
        need(self.updates <= self.max_updates, f'UNRESOLVED: certificate arithmetic cap (updates={self.updates}, maximum={self.max_updates})')
        self.checkpoint()


def matrix_hash(matrix):
    """Construction binding, not a positivity proof; no matrix-sized byte copy."""
    h = hashlib.sha256(str(matrix.shape).encode())
    for a in (matrix.indptr, matrix.indices, matrix.data):
        h.update(a.dtype.str.encode())
        h.update(memoryview(a).cast('B'))
    return h.hexdigest()


def _eliminate(rows, pivots, work):
    count = sum(map(len, rows))
    work.check(count)
    pivot_min = math.inf
    factors = []
    forward = np.ones(pivots)
    for k in range(pivots):
        row = rows[k]
        pivot = row.get(k, ZERO)
        need(pivot[0] > 0, 'UNRESOLVED: singular/indefinite/inadequately resolved pivot')
        pivot_min = min(pivot_min, pivot[0])
        adjacent = sorted(i for i in row if i > k)
        column = [(i,magnitude(div_positive(row[i],pivot))) for i in adjacent if i < pivots]
        factors.append(column)
        count += len(column)  # retained factors share the same live-entry quota
        work.check(count)
        for i,bound in column:
            forward[i] = upper_add(float(forward[i]),upper_mul(bound,float(forward[k])))
        for p, i in enumerate(adjacent):
            for j in adjacent[p:]:
                work.check(count, 1)
                old = rows[i].get(j, ZERO)
                new = sub(old, div_positive(mul(row[i], row[j]), pivot))
                if j not in rows[i]:
                    count += 1
                    work.check(count)
                rows[i][j] = new
        count -= len(row)
        rows[k] = None
        work.check(count)
    backward = np.ones(pivots)
    for k in range(pivots-1,-1,-1):
        for i,bound in factors[k]:
            backward[k] = upper_add(float(backward[k]),upper_mul(bound,float(backward[i])))
        work.check(count)
    product = upper_mul(float(forward.max()),float(backward.max()))
    inverse_bound = div_positive((product,product),(pivot_min,pivot_min))[1]
    return pivot_min,inverse_bound


def _order_reference(a,border,work):
    """One prescribed ordering on an owned Boolean structural superset graph.

    Skew-cancelled reference entries can remain graph edges. This is an ordering
    heuristic, never a positivity or reduced-fill claim. No fallback/search.
    """
    work.check(0)
    graph=(a!=0)
    graph=graph+graph.T
    raw=reverse_cuthill_mckee(graph,symmetric_mode=True)
    n=a.shape[0]
    need(isinstance(raw,np.ndarray) and raw.ndim==1 and len(raw)==n and
         np.issubdtype(raw.dtype,np.integer),'invalid analysis permutation type/length')
    permutation=np.ascontiguousarray(raw,dtype=np.int64)
    del raw
    need(int(permutation.min())>=0 and int(permutation.max())<n,'analysis permutation range')
    seen=np.zeros(n,dtype=bool);seen[permutation]=True
    need(seen.all(),'analysis permutation is not bijective')
    info={'method':REFERENCE_ORDER,'order':n,'graph':'symmetric-original-nonzero-structural-superset',
          'graph_nnz':int(graph.nnz),'permutation_dtype':permutation.dtype.str,
          'permutation_sha256':hashlib.sha256(memoryview(permutation).cast('B')).hexdigest()}
    del seen,graph  # Release graph before sparse permutation-copy overlap.
    work.check(0)
    ordered=a[permutation][:,permutation]
    ordered.sort_indices()  # Only an owned analysis copy; original stays untouched.
    new_border=None if border is None else (border[0][permutation],border[1])
    work.check(0)
    return ordered,new_border,info


def _eliminate_frontier(a,at,work,border=None):
    """Same interval LDL/order; retain only touched rows and required factors.

    Immutable original CSR is input storage under the input/kernel caps. Every
    materialized interval entry and factor, including the popped pivot row,
    counts against the same live-entry cap BEFORE insertion. Bounded scalar
    arithmetic temporaries follow the eager checker's convention; dict/list
    metadata, index scratch, vectors and retained CSR all count as kernel memory.
    """
    n=a.shape[0]
    B,D=border if border is not None else (np.zeros((n,0)),np.zeros((0,0)))
    total=n+len(D);pending={};count=0;factors=[];forward=np.ones(n)
    def initial(i,j):
        if i<n and j<n:
            def get(m):
                start,end=m.indptr[i:i+2];p=int(np.searchsorted(m.indices[start:end],j))+start
                return float(m.data[p]) if p<end and m.indices[p]==j else 0.
            return average_enclosure(get(a),get(at))
        v=float(B[i,j-n] if i<n else D[i-n,j-n]);return v,v
    def insert(row,j,value):
        nonlocal count
        if j not in row:
            work.check(count+1);count+=1
        row[j]=value
    def load(i):
        row=pending.pop(i,{})
        if i<n:
            for j,x,y in reference_pairs(a,at,i):
                if j not in row:insert(row,j,average_enclosure(x,y))
            for j in range(len(D)):
                if B[i,j] and n+j not in row:insert(row,n+j,initial(i,n+j))
        else:
            for j in range(i,total):
                if D[i-n,j-n] and j not in row:insert(row,j,initial(i,j))
        return row
    pivot_min=math.inf
    for k in range(n):
        row=load(k);pivot=row.get(k,ZERO)
        need(pivot[0]>0,'UNRESOLVED: singular/indefinite/inadequately resolved pivot');pivot_min=min(pivot_min,pivot[0])
        adjacent=sorted(j for j in row if j>k);column=[];factors.append(column)
        for i in adjacent:
            if i<n:
                work.check(count+1);count+=1
                column.append((i,magnitude(div_positive(row[i],pivot))))
        for i,bound in column:forward[i]=upper_add(float(forward[i]),upper_mul(bound,float(forward[k])))
        for p,i in enumerate(adjacent):
            target=pending.setdefault(i,{})
            for j in adjacent[p:]:
                work.check(count,1)
                old=target[j] if j in target else initial(i,j)
                insert(target,j,sub(old,div_positive(mul(row[i],row[j]),pivot)))
            del target  # Never retain an uncounted completed row through a loop local.
        count-=len(row);del row;work.check(count)
    # Materialize surviving terminal rows while all required factors are live.
    terminals={i:load(i) for i in range(n,total)}
    backward=np.ones(n)
    for k in range(n-1,-1,-1):
        for i,bound in factors[k]:backward[k]=upper_add(float(backward[k]),upper_mul(bound,float(backward[i])))
        work.check(count)
    product=upper_mul(float(forward.max()),float(backward.max()))
    inv=div_positive((product,product),(pivot_min,pivot_min))[1]
    schur=[[terminals[min(i,j)].get(max(i,j),ZERO) for j in range(n,total)] for i in range(n,total)]
    need(count==sum(map(len,terminals.values()))+sum(map(len,factors)), 'frontier entry accounting differs')
    return pivot_min,inv,schur

def average_enclosure(a,b):
    """Enclose exact (a+b)/2 without modifying either stored coefficient."""
    need(math.isfinite(a) and math.isfinite(b),'nonfinite reference coefficient')
    if a==b:return (a,a)
    if a==-b:return ZERO
    lo=math.nextafter(math.nextafter(a*.5,-math.inf)+math.nextafter(b*.5,-math.inf),-math.inf)
    hi=math.nextafter(math.nextafter(a*.5,math.inf)+math.nextafter(b*.5,math.inf),math.inf)
    # Exact average also lies between the original finite endpoints. Intersect
    # before finite-only checking so intermediate rounding overflow is harmless.
    result=max(lo,min(a,b)),min(hi,max(a,b))
    need(all(math.isfinite(v) for v in result) and result[0]<=result[1],'invalid reference enclosure')
    return result


def reference_pairs(a,at,row):
    """Merge two canonical CSR rows with O(1) auxiliary storage."""
    p,end=int(a.indptr[row]),int(a.indptr[row+1])
    q,stop=int(at.indptr[row]),int(at.indptr[row+1])
    p+=int(np.searchsorted(a.indices[p:end],row))
    q+=int(np.searchsorted(at.indices[q:stop],row))
    while p<end or q<stop:
        j=min(int(a.indices[p]) if p<end else a.shape[0],
              int(at.indices[q]) if q<stop else a.shape[0])
        x=y=0.
        if p<end and a.indices[p]==j:x=float(a.data[p]);p+=1
        if q<stop and at.indices[q]==j:y=float(at.data[q]);q+=1
        # Exact real cancellation, including absent/explicit-zero partners.
        if x!=-y:yield j,x,y


def reference_preflight(a,at,work,border_entries=0):
    """Count exact reference entries BEFORE allocating Python row dictionaries."""
    count=border_entries
    work.check(count)
    for i in range(a.shape[0]):
        count+=sum(1 for _ in reference_pairs(a,at,i))
        work.check(count)
    return count


def certify(matrix, binding, expected_binding, work=None, border=None, *, reference=False, frontier=False, ordering=None):
    """Certify exact symmetric Af, or explicitly its symmetric analysis reference.

    reference=True encloses (Af+Af.T)/2 and its own bordered Schur. It does not
    certify that nonsymmetric Af is SPD or relabel its Schur as the reference.
    The caller must derive full-network original inverse bounds by coercivity.

    border=(B,D) appends only terminal columns, never another board. Elimination
    stops before terminal pivots: a floating KB terminal is expected here. The
    returned interval Schur blocks, combined with live wire stamps, must also
    pass certify_coupled. Reference block factorization proves H positive
    definite; full-network coercivity then proves original M nonsingular. Neither
    mode assumes that a retained approximate basis is exact.
    """
    need(binding == expected_binding and bool(binding), 'stale uniqueness binding')
    work = work or Work()
    need(not frontier or reference,'frontier storage requires explicit reference certificate')
    need(ordering is None or (frontier and ordering==REFERENCE_ORDER),'invalid analysis ordering contract')
    need(sp.issparse(matrix) and matrix.dtype == np.dtype('float64'), 'certificate requires binary64 sparse operator')
    need(matrix.shape[0] == matrix.shape[1] > 0, 'invalid certificate order')
    need(matrix.nnz <= work.max_input_nnz, 'UNRESOLVED: certificate input CSR cap')
    work.check(0)
    a = matrix.tocsr(copy=True)
    need(a.has_canonical_format, 'certificate requires canonical sparse entries')
    need(np.isfinite(a.data).all(), 'nonfinite certificate operator')
    mismatch = None if reference else (a != a.T).tocsr()
    if mismatch is not None and mismatch.nnz:
        # Reuse the existing Boolean witness: no extra full floating difference,
        # symmetrization, approximate equality or solver change. Four exact pairs
        # characterize the rejection; they are not a global skew-norm estimate.
        witnesses = []
        for i in range(a.shape[0]):
            if i % 4096 == 0:work.check(0)
            for j in mismatch.indices[mismatch.indptr[i]:mismatch.indptr[i+1]]:
                witnesses.append({'row':i,'column':int(j),
                    'a_ij_hex':float(a[i,j]).hex(),'a_ji_hex':float(a[j,i]).hex()})
                if len(witnesses)==4:break
            if len(witnesses)==4:break
        report={'schema':'e16-exact-reciprocity-witness-v1','matrix_sha256':matrix_hash(a),
                'binding_sha256':digest(binding),'order':int(a.shape[0]),'nnz':int(a.nnz),
                'mismatched_entries':int(mismatch.nnz),'sample_limit':4,'witnesses':witnesses,
                'matrix_abs_max':max(float(a.data.max()),-float(a.data.min())),
                'global_skew_norm':'NOT_COMPUTED','symmetrized':False}
        need(False,'nonreciprocal exact certificate operator: '+json.dumps(report,sort_keys=True,separators=(',',':')))
    del mismatch
    n = a.shape[0]
    if border is not None:
        B,D=border
        need(B.dtype==D.dtype==np.dtype('float64') and B.ndim==2 and B.shape[0]==n
             and D.shape==(B.shape[1],B.shape[1]) and 0<len(D)<=8,'invalid certificate border')
        need(np.isfinite(B).all() and np.isfinite(D).all() and np.array_equal(D,D.T),'nonfinite/asymmetric border')
    at=matrix.T.tocsr(copy=False) if reference else None
    if reference:
        need(at.has_canonical_format,'certificate requires canonical transpose entries')
    order_info={'method':'original-node-order'}
    if frontier:
        stamp=matrix_hash(a)  # Original binding survives analysis-only permutation.
        if ordering is not None:
            del at
            a,border,order_info=_order_reference(a,border,work)
            at=a.T.tocsr(copy=False)
            need(a.has_canonical_format and at.has_canonical_format,'noncanonical ordered analysis')
        try:
            minimum,inverse_bound,schur=_eliminate_frontier(a,at,work,border)
        except ValueError as error:
            if ordering is None:raise
            raise ValueError(str(error)+'; analysis_ordering='+json.dumps(order_info|{'original_matrix_sha256':stamp},sort_keys=True,separators=(',',':'))) from error
        del a,at
    else:
        if reference:
            reference_preflight(a,at,work,0 if border is None else int(np.count_nonzero(B))+D.size)
        rows = []
        entries = 0
        for i in range(n):
            work.check(entries)
            if reference:
                rows.append({j:average_enclosure(x,y) for j,x,y in reference_pairs(a,at,i)})
            else:
                rows.append({int(j): (float(x), float(x))
                             for j, x in zip(a.indices[a.indptr[i]:a.indptr[i+1]], a.data[a.indptr[i]:a.indptr[i+1]])
                             if j >= i and x != 0})
            entries += len(rows[-1])
            work.check(entries)
        stamp = matrix_hash(a)  # Original stored matrix hash, never a replaced solver input.
        del a,at
        if border is not None:
            B, D = border
            work.check(entries + int(np.count_nonzero(B)) + D.size)
            for i in range(n):
                for j in range(len(D)):
                    if B[i,j] != 0:
                        rows[i][n+j] = (float(B[i,j]),)*2
            rows.extend({n+j: (float(D[i,j]),)*2 for j in range(i,len(D)) if D[i,j] != 0} for i in range(len(D)))
        minimum,inverse_bound = _eliminate(rows, n, work)
        schur = []
        for i in range(n,len(rows)):
            schur.append([rows[min(i,j)].get(max(i,j),ZERO) for j in range(n,len(rows))])
    return {'method': REFERENCE_METHOD if reference else METHOD,
            'status': 'SYMMETRIC_PART_REFERENCE_SPD' if reference else 'EXACT_STORED_OPERATOR_SPD',
            'analysis_reference_only':reference,
            'storage':FRONTIER_STORAGE if frontier else 'eager-interval-rows-v1',
            'analysis_ordering':order_info,
            'matrix_sha256': stamp, 'binding_sha256': digest(binding), 'order': n,
            'minimum_pivot_lower': minimum, 'inverse_infinity_upper':inverse_bound, 'schur_intervals': schur,
            'arithmetic_updates': work.updates, 'peak_sparse_entries': work.peak_entries}


def certify_coupled(ka, kb, bulk, live, work, *, reference=False):
    """Certify exact combined Schur, accounting wire reciprocal rounding too."""
    k = len(ka)
    need(k > 0 and len(kb) == len(live) == k and math.isfinite(bulk) and bulk > 0, 'invalid coupled certificate')
    rows = [{} for _ in range(2*k)]
    for offset, block in ((0,ka),(k,kb)):
        for i in range(k):
            need(len(block[i]) == k, 'invalid Schur intervals')
            for j in range(i,k):
                v = tuple(block[i][j])
                need(len(v) == 2 and all(math.isfinite(x) for x in v) and v[0] <= v[1]
                     and v == tuple(block[j][i]), 'invalid Schur interval symmetry')
                if v != ZERO:
                    rows[offset+i][offset+j] = v
    # Match the actual stored binary64 conductance in small_system. No change
    # to the original construction/solver convention; this is its exact value.
    conductance = 1./bulk
    need(math.isfinite(conductance), 'nonfinite wire conductance')
    g = (conductance,conductance)
    for i, present in enumerate(live):
        if present:
            rows[i][i] = add(rows[i].get(i,ZERO),g)
            rows[k+i][k+i] = add(rows[k+i].get(k+i,ZERO),g)
            rows[i][k+i] = (-g[1],-g[0])
    minimum,inverse_bound = _eliminate(rows,2*k,work)
    return {'method': REFERENCE_METHOD if reference else METHOD,
            'status': 'EXACT_COUPLED_REFERENCE_SCHUR_SPD' if reference else 'EXACT_COUPLED_SCHUR_SPD',
            'analysis_reference_only':reference,'order':2*k,
            'minimum_pivot_lower': minimum, 'inverse_infinity_upper':inverse_bound, 'arithmetic_updates': work.updates,
            'peak_sparse_entries': work.peak_entries}
