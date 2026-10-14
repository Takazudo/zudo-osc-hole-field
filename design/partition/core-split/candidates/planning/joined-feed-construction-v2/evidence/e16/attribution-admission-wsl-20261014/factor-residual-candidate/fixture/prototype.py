"""Synthetic-only sparse factor/residual proof experiment; no production entrypoint.

A, L, U are exact real interpretations of their binary64 entries. If
r >= |A-LU|1, z >= C(U)^-1 C(L)^-1 r and q=max(z)<1,
then ||A^-1||inf <= max(C(U)^-1 C(L)^-1 1)/(1-q).
C uses positive absolute diagonals and negative absolute off diagonals.
Every recurrence below uses NONNEGATIVE sums, never signed cancellation.
The proof is inverse comparison followed by a Neumann series for
A=LU(I+(LU)^-1 E). It needs neither symmetry nor positive definiteness.
"""
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path
from itertools import chain

# This module is intentionally local/synthetic, and refuses larger orders.
SOURCE = next((p for p in Path(__file__).resolve().parents if (p / 'attribution_uniqueness.py').is_file()), None)
if SOURCE is None:
    SOURCE = Path(__file__).resolve().parents[2] / 'design/partition/core-split/candidates/planning/joined-feed-construction-v2'
sys.path.insert(0, str(SOURCE))
import numpy as np
import attribution_uniqueness as I
import attribution_resolution as V
from resistance_attribution import need

METHOD = 'synthetic-fixed-pattern-factor-residual-v1'


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def validate_a(a):
    need(a.format == 'csr' and a.shape[0] == a.shape[1] and 0 < a.shape[0] <= 128, 'fixture CSR/order gate')
    need(a.dtype.name == 'float64' and a.has_canonical_format, 'noncanonical binary64 CSR')
    need(all(math.isfinite(float(v)) and v != 0 for v in a.data), 'nonfinite or explicit zero matrix')


class Meter:
    def __init__(self, work=None):
        self.work = work or I.Work(max_entries=100000, max_updates=1000000)
        self.phase = 'input'
        self.phases = {}
        self.live = 0
        self.offset = 0
        self.started = time.monotonic()
        self.dropped_products = 0

    def charge(self, n=1):
        need(time.monotonic() - self.started < 30, 'fixture wall-time cap')
        self.phases[self.phase] = self.phases.get(self.phase, 0) + n
        self.work.check(self.live, n)

    def entries(self, n):
        self.live = self.offset + n
        self.work.check(self.live)

    def add(self, a, b):
        self.charge()
        return I.upper_add(a, b)

    def mul(self, a, b):
        self.charge()
        return I.upper_mul(a, b)

    def div(self, a, b):
        self.charge()
        return I.div_positive((a, a), (b, b))[1]


def pattern_of(a, full=False):
    validate_a(a)
    n = a.shape[0]
    return [list(range(n)) if full else sorted(set(map(int, a.indices[a.indptr[i]:a.indptr[i+1]])) | {i}) for i in range(n)]


def produce(a, context, pattern, meter):
    validate_a(a)
    n = a.shape[0]
    need(len(pattern) == n, 'pattern length')
    for i, p in enumerate(pattern):
        need(p == sorted(set(p)) and i in p and all(type(j) is int and 0 <= j < n for j in p), 'fixed canonical pattern')
        need(len(p) <= 128, 'fixture fixed degree cap')
    meter.phase = 'production'
    pattern_entries = sum(map(len, pattern))
    base = pattern_entries + 8*n  # vectors/metadata-index slots conservatively reserved
    retained = 0
    L, U = [], []
    for i in range(n):
        # Count row scratch before any initial insertion, including zeros.
        meter.entries(base + retained + len(pattern[i]))
        row = {j: 0. for j in pattern[i]}
        for pos in range(a.indptr[i], a.indptr[i+1]):
            j = int(a.indices[pos])
            if j in row: row[j] = float(a.data[pos])
        lower = []
        for j in (j for j in pattern[i] if j < i):
            diag = U[j][0][1] if U[j] and U[j][0][0] == j else None
            need(diag is not None and math.isfinite(diag) and diag != 0, 'producer zero/nonfinite pivot')
            meter.charge()
            lij = row[j]/diag
            need(math.isfinite(lij), 'producer nonfinite factor')
            if lij:
                meter.entries(base + retained + len(row) + 1)
                lower.append([j, lij]); retained += 1
            for k, ujk in U[j]:
                if k <= j: continue
                meter.charge()  # each attempted product, including a dropped contribution
                product = lij*ujk
                need(math.isfinite(product), 'producer overflow')
                if k in row:
                    meter.charge()
                    row[k] -= product
                    need(math.isfinite(row[k]), 'producer overflow')
                else: meter.dropped_products += 1
        upper = []
        for j in pattern[i]:
            if j >= i and row[j]:
                meter.entries(base + retained + len(row) + 1)
                upper.append([j, row[j]]); retained += 1
        need(any(j == i for j, _ in upper), 'producer missing diagonal')
        L.append(lower); U.append(upper)
        del row
        meter.entries(base + retained)
    witness = {'method': METHOD, 'matrix': I.matrix_hash(a), 'context': digest(context),
               'permutation': list(range(n)), 'pattern': pattern, 'L': L, 'U': U}
    return witness, digest(witness)


def verify(a, context, w, expected_digest, meter):
    validate_a(a)
    n = a.shape[0]
    need(w.get('method') == METHOD and w.get('matrix') == I.matrix_hash(a) and w.get('context') == digest(context), 'stale matrix/context/method binding')
    need(w.get('permutation') == list(range(n)), 'unsupported/stale permutation')
    need(digest(w) == expected_digest, 'incomplete/stale witness binding')
    need(set(w) == {'method','matrix','context','permutation','pattern','L','U'}, 'witness schema')
    pattern = w['pattern']
    need(len(pattern) == n and all(p == sorted(set(p)) and i in p and all(type(j) is int and 0 <= j < n for j in p) for i,p in enumerate(pattern)), 'pattern binding')
    L, U = w['L'], w['U']
    need(len(L) == len(U) == n, 'factor row count')
    for triangular, rows in [('L', L), ('U', U)]:
        for i, row in enumerate(rows):
            js = [p[0] for p in row]
            need(js == sorted(set(js)), 'noncanonical factor row')
            for j, v in row:
                need(type(j) is int and 0 <= j < n and type(v) is float and math.isfinite(v) and v != 0 and j in pattern[i], 'factor coefficient/index/pattern')
                need(j < i if triangular == 'L' else j >= i, 'nontriangular factor')
            if triangular == 'U': need(i in js, 'missing U diagonal')
    retained = sum(map(len, L)) + sum(map(len, U))
    base = retained + sum(map(len, pattern)) + 8*n
    meter.entries(base)
    meter.phase = 'residual'
    r = []
    for i in range(n):
        row = {}
        def put(j, val):
            if j not in row: meter.entries(base + len(row) + 1)
            row[j] = val
        for p in range(a.indptr[i], a.indptr[i+1]):
            v = float(a.data[p]); put(int(a.indices[p]), (v, v))
        for k, lik in chain(((i, 1.),), L[i]):
            for j, ukj in U[k]:
                meter.charge(2)  # product and interval subtraction, no omitted fill
                put(j, I.sub(row.get(j, I.ZERO), I.mul((lik, lik), (ukj, ukj))))
        acc = 0.
        for value in row.values(): acc = meter.add(acc, I.magnitude(value))
        r.append(acc)
        meter.entries(base)

    def comparison(rhs, phase):
        meter.phase = phase
        y = [0.]*n
        for i in range(n):
            val = rhs[i]
            for j, lij in L[i]: val = meter.add(val, meter.mul(abs(lij), y[j]))
            y[i] = val  # exact unit L diagonal, implicit by schema
        z = [0.]*n
        for i in range(n-1, -1, -1):
            val = y[i]
            for j, uij in U[i]:
                if j > i: val = meter.add(val, meter.mul(abs(uij), z[j]))
            z[i] = meter.div(val, abs(U[i][0][1]))
        return max(z)
    q = comparison(r, 'comparison_residual')
    k = comparison([1.]*n, 'comparison_ones')
    result = {'q': q, 'K': k, 'factor_entries': retained, 'residual_row_upper': r,
              'updates': meter.work.updates, 'phase_updates': dict(meter.phases),
              'peak_entries': meter.work.peak_entries, 'dropped_products': meter.dropped_products}
    if q >= 1:
        result.update(status='REFUSED', reason='comparison residual norm is not below one')
        return result
    meter.phase = 'neumann'
    meter.charge()
    denominator = I.sub((1.,1.), (q,q))[0]
    need(denominator > 0, 'unresolved Neumann denominator')
    inv = meter.div(k, denominator)
    result.update(status='CERTIFIED', inverse_infinity_upper=inv,
                  updates=meter.work.updates, phase_updates=dict(meter.phases))
    return result


def signed_factor_solve(w, rhs, meter):
    """Outward F^-1 rhs; fixed coefficients are exact real binary64."""
    need(all(type(x) in (float, np.float64) and math.isfinite(x) for x in rhs), 'signed RHS must be exact binary64')
    n = len(rhs); need(n==len(w['L'])==len(w['U']), 'signed RHS shape')
    y = [I.ZERO]*n; z = [I.ZERO]*n
    meter.phase = 'schur_factor_solve'
    for i in range(n):
        value = (float(rhs[i]), float(rhs[i]))
        for j,lij in w['L'][i]:
            meter.charge(2); value = I.sub(value, I.mul((lij,lij),y[j]))
        y[i] = value
    for i in range(n-1,-1,-1):
        value=y[i]; diagonal=None
        for j,uij in w['U'][i]:
            if j==i: diagonal=uij
            else:
                meter.charge(2);value=I.sub(value,I.mul((uij,uij),z[j]))
        meter.charge()
        z[i]=I.div_positive(value,(abs(diagonal),abs(diagonal)))
        if diagonal < 0: z[i]=(-z[i][1],-z[i][0])
    return z


def small_inverse_witness(s, meter):
    """Fixed-order float Gauss-Jordan; success is NOT certification."""
    n=len(s);need(0<n<=8,'tiny Schur order cap')
    meter.phase='schur_inverse_production'
    rows=[[float((s[i][j][0]*.5)+(s[i][j][1]*.5)) for j in range(n)] + [float(i==j) for j in range(n)] for i in range(n)]
    for k in range(n):
        pivot=rows[k][k];need(math.isfinite(pivot) and pivot!=0,'small inverse fixed pivot refusal')
        for j in range(2*n):
            meter.charge();rows[k][j]/=pivot
            need(math.isfinite(rows[k][j]),'small inverse nonfinite')
        for i in range(n):
            if i==k:continue
            scale=rows[i][k]
            for j in range(2*n):
                meter.charge(2);rows[i][j]-=scale*rows[k][j]
                need(math.isfinite(rows[i][j]),'small inverse nonfinite')
    return [r[n:] for r in rows]


def schur_inverse_bound(s, meter):
    r=small_inverse_witness(s,meter);n=len(s)
    meter.phase='schur_inverse_verification';q=0.;knorm=0.
    for i in range(n):
        row=0.;rn=0.
        for j in range(n):
            residual=(float(i==j),float(i==j))
            for k in range(n):
                meter.charge(2);residual=I.sub(residual,I.mul((r[i][k],r[i][k]),s[k][j]))
            row=meter.add(row,I.magnitude(residual));rn=meter.add(rn,abs(r[i][j]))
        q=max(q,row);knorm=max(knorm,rn)
    need(q<1,f'small interval Schur residual refuses: q={q!r}')
    meter.charge();denominator=I.sub((1.,1.),(q,q))[0]
    return meter.div(knorm,denominator),q


def block_certificate(blocks, D, context, meter, patterns=None):
    """Tiny factor-only Schur bridge, with original lower couplings B.T.

    blocks: [(A,B), ...], stored full operator [[diag(A),B],[B.T,D]].
    No original A*Y check or new physical RHS. h are certificate witnesses only.
    """
    import numpy as np
    m=len(D);need(0<m<=8 and all(len(row)==m for row in D),'small terminal shape')
    def interval(x):
        need(isinstance(x,tuple) or type(x) in (float,np.float64),'D scalar must be exact binary64')
        v=x if isinstance(x,tuple) else (float(x),float(x))
        need(len(v)==2 and all(type(y) is float and math.isfinite(y) for y in v) and v[0]<=v[1], 'D interval')
        return v
    for a,B in blocks:
        validate_a(a)
        need(isinstance(B,np.ndarray) and B.dtype==np.dtype('float64') and B.shape==(a.shape[0],m) and np.isfinite(B).all(),'B must be finite binary64 array of expected shape')
    # The max backward block norm needs disjoint per-board terminal support.
    for j in range(m):
        need(sum(any(float(x)!=0 for x in B[:,j]) for _,B in blocks)<=1,'shared terminal unsupported by max-block bound')
    meter.entries(12*m*m)  # interval S, midpoint/inverse scratch and endpoint slots
    meter.offset=meter.live
    s=[[interval(D[i][j]) for j in range(m)] for i in range(m)]
    global_input_digest=digest({'context':context,'boards':[{'A':I.matrix_hash(a),'B':B.tolist()} for a,B in blocks],'D_intervals':s})
    certificates=[];norms=[]
    for board_index,(a,B) in enumerate(blocks):
        need(B.shape==(a.shape[0],m) and np.isfinite(B).all(),'B shape/nonfinite')
        # Fixed sparse original pattern; tiny fixtures may select full explicitly.
        pattern=pattern_of(a,full=True) if patterns is None else patterns[board_index]
        w,h=produce(a,{**context,'board':board_index},pattern,meter)
        cert=verify(a,{**context,'board':board_index},w,h,meter)
        need(cert['status']=='CERTIFIED','board factor residual refuses')
        certificates.append(cert)
        meter.phase='coupling_norms'
        row_norm=0.;column_sums=[0.]*m
        for i in range(a.shape[0]):
            row=0.
            for j in range(m):
                row=meter.add(row,abs(float(B[i,j])))
                column_sums[j]=meter.add(column_sums[j],abs(float(B[i,j])))
            row_norm=max(row_norm,row)
        norms.append((row_norm,max(column_sums)))
        meter.phase='schur_correction';meter.charge()
        denominator=I.sub((1.,1.),(cert['q'],cert['q']))[0]
        ratio=meter.div(cert['q'],denominator)
        for j in range(m):
            values=signed_factor_solve(w,B[:,j],meter)
            meter.phase='schur_construction'
            correction=meter.mul(ratio,max(map(I.magnitude,values)))
            for i in range(m):
                value=s[i][j]
                for k,bki in enumerate(B[:,i]):
                    b=float(bki)
                    if b==0:continue
                    meter.charge(2);value=I.sub(value,I.mul((b,b),values[k]))
                widen=meter.mul(column_sums[i],correction)
                meter.charge();s[i][j]=I.add(value,(-widen,widen))
        # Reserve previously retained witness arrays and scratch across boards;
        # no work reset. This overcounts released vectors, harmless for toy cap.
        meter.offset=meter.live
    inv_s,q_s=schur_inverse_bound(s,meter)
    meter.phase='global_block_bound'
    forward=backward=0.;diagonal=inv_s
    for cert,(bn,btn) in zip(certificates,norms):
        ai=cert['inverse_infinity_upper'];diagonal=max(diagonal,ai)
        forward=max(forward,meter.mul(ai,bn));backward=max(backward,meter.mul(ai,btn))
    bound=meter.mul(meter.mul(meter.add(1.,forward),diagonal),meter.add(1.,backward))
    return {'status':'CERTIFIED','global_input_sha256':global_input_digest,'inverse_infinity_upper':bound,'schur_intervals':s,
            'schur_inverse_infinity_upper':inv_s,'schur_q':q_s,'boards':certificates,
            'updates':meter.work.updates,'phase_updates':dict(meter.phases),
            'peak_entries':meter.work.peak_entries}
