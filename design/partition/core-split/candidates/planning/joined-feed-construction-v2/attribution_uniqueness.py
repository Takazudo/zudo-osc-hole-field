"""Independent bounded interval LDL certificate for exact stored sparse operators.

This checker never solves a load or changes the production solver. Binary64
coefficients start as singleton real intervals. Each scalar operation rounds
outwards by one nextafter, including underflow. Positive lower pivot bounds
prove exact LDL positivity by induction. Fill/work exhaustion is unresolved.
No approximate-zero pruning, symmetrization, or dense board conversion occurs.
"""
import hashlib
import math
from dataclasses import dataclass

import numpy as np
import scipy.sparse as sp

from resistance_attribution import need, digest

METHOD = 'outward-binary64-sparse-LDL-v1'
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
        need(entries <= self.max_entries, 'UNRESOLVED: certificate sparse fill cap')
        need(self.updates <= self.max_updates, 'UNRESOLVED: certificate arithmetic cap')
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


def certify(matrix, binding, expected_binding, work=None, border=None):
    """Certify exact symmetric binary64 Af and optionally enclose D-B'Af^-1 B.

    border=(B,D) appends only terminal columns, never another board. Elimination
    stops before terminal pivots: a floating KB terminal is expected here. The
    returned interval Schur blocks, combined with live wire stamps, must also
    pass certify_coupled. This proves original full-network uniqueness by block
    factorization, without assuming a retained approximate basis is exact.
    """
    need(binding == expected_binding and bool(binding), 'stale uniqueness binding')
    work = work or Work()
    need(sp.issparse(matrix) and matrix.dtype == np.dtype('float64'), 'certificate requires binary64 sparse operator')
    need(matrix.shape[0] == matrix.shape[1] > 0, 'invalid certificate order')
    need(matrix.nnz <= work.max_input_nnz, 'UNRESOLVED: certificate input CSR cap')
    work.check(0)
    a = matrix.tocsr(copy=True)
    need(a.has_canonical_format, 'certificate requires canonical sparse entries')
    need(np.isfinite(a.data).all(), 'nonfinite certificate operator')
    need((a != a.T).nnz == 0, 'nonreciprocal exact certificate operator')
    n = a.shape[0]
    rows = []
    entries = 0
    for i in range(n):
        work.check(entries)
        rows.append({int(j): (float(x), float(x))
                     for j, x in zip(a.indices[a.indptr[i]:a.indptr[i+1]], a.data[a.indptr[i]:a.indptr[i+1]])
                     if j >= i and x != 0})
        entries += len(rows[-1])
        work.check(entries)
    stamp = matrix_hash(a)
    del a
    if border is not None:
        B, D = border
        need(B.dtype == D.dtype == np.dtype('float64') and B.ndim == 2 and B.shape[0] == n
             and D.shape == (B.shape[1], B.shape[1]) and 0 < len(D) <= 8, 'invalid certificate border')
        need(np.isfinite(B).all() and np.isfinite(D).all() and np.array_equal(D,D.T), 'nonfinite/asymmetric border')
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
    return {'method': METHOD, 'status': 'EXACT_STORED_OPERATOR_SPD',
            'matrix_sha256': stamp, 'binding_sha256': digest(binding), 'order': n,
            'minimum_pivot_lower': minimum, 'inverse_infinity_upper':inverse_bound, 'schur_intervals': schur,
            'arithmetic_updates': work.updates, 'peak_sparse_entries': work.peak_entries}


def certify_coupled(ka, kb, bulk, live, work):
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
    return {'method': METHOD, 'status': 'EXACT_COUPLED_SCHUR_SPD',
            'minimum_pivot_lower': minimum, 'inverse_infinity_upper':inverse_bound, 'arithmetic_updates': work.updates,
            'peak_sparse_entries': work.peak_entries}
