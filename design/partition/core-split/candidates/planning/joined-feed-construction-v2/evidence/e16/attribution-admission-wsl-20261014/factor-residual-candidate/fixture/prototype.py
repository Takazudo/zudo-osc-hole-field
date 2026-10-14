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
WEIGHT_METHOD = 'synthetic-eight-pass-comparison-picard-v1'
WEIGHT_PASSES = 8


class ResidualRow(dict):
    """Named row type lets regression tests observe actual object destruction."""



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
        self.weight_passes_completed = 0
        self.weight_outputs = []
        self.board_certificates = []

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


def validate_factor(a, context, w, expected_digest):
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
    return n, L, U


def storage_base(w, n, weighted=False):
    # Slot model, NOT Python bytes. Extra 8n covers weight packet, old/new p,
    # comparison RHS/y/z, weighted result and serial solve overlap.
    return sum(map(len, w['L'])) + sum(map(len, w['U'])) + sum(map(len, w['pattern'])) + (16 if weighted else 8)*n


def residual_rows(a, w, meter, base, weights=None, approximate=False):
    """Exhaustive row stream. Approximate mode is producer-only, never proof."""
    r = []
    for i in range(a.shape[0]):
        row = ResidualRow()
        def put(j, val):
            if j not in row: meter.entries(base + len(row) + 1)
            row[j] = val
        for pos in range(a.indptr[i], a.indptr[i+1]):
            v = float(a.data[pos]); put(int(a.indices[pos]), v if approximate else (v, v))
        for k, lik in chain(((i, 1.),), w['L'][i]):
            for j, ukj in w['U'][k]:
                meter.charge(2)
                value = (row.get(j, 0.) - lik*ukj if approximate else
                         I.sub(row.get(j, I.ZERO), I.mul((lik, lik), (ukj, ukj))))
                if approximate: need(math.isfinite(value), 'weight producer residual overflow')
                put(j, value)
        acc = 0.
        for j, value in row.items():
            v = abs(value) if approximate else I.magnitude(value)
            if weights is not None:
                if approximate:
                    meter.charge(); v *= weights[j]
                else: v = meter.mul(v, weights[j])
            if approximate:
                meter.charge(); acc += v
                need(math.isfinite(acc), 'weight producer accumulation overflow')
            else: acc = meter.add(acc, v)
        r.append(acc)
        # Both closure and dictionary die BEFORE reducing the live reservation.
        # The scalar interval `value` stays covered by the vector/scratch reserve.
        del put, row
        meter.entries(base)
    return r


def comparison_vector(w, rhs, meter, phase, approximate=False):
    meter.phase = phase
    n = len(rhs); y = [0.]*n; z = [0.]*n
    def step(val, coefficient, previous):
        if approximate:
            meter.charge(2)
            result = val + abs(coefficient)*previous
            need(math.isfinite(result), 'weight producer comparison overflow')
            return result
        return meter.add(val, meter.mul(abs(coefficient), previous))
    for i in range(n):
        val = rhs[i]
        for j, lij in w['L'][i]: val = step(val, lij, y[j])
        y[i] = val
    for i in range(n-1, -1, -1):
        val = y[i]
        for j, uij in w['U'][i]:
            if j > i: val = step(val, uij, z[j])
        diagonal = abs(w['U'][i][0][1])
        if approximate:
            meter.charge(); z[i] = val/diagonal
            need(math.isfinite(z[i]) and z[i] > 0, 'weight producer comparison underflow/overflow')
        else: z[i] = meter.div(val, diagonal)
    return z


def weight_packet(a, context, w, values, origin):
    """Bind actual exact binary64 weights; origin is descriptive, never trusted."""
    return {'method': WEIGHT_METHOD, 'matrix': I.matrix_hash(a),
            'context': digest(context), 'factor': digest(w), 'values': values,
            'origin': origin}


def validate_weights(a, context, w, packet, expected_digest):
    need(type(packet) is dict and set(packet) == {'method','matrix','context','factor','values','origin'}, 'weight schema')
    values = packet['values']
    need(type(values) is list and len(values) == a.shape[0], 'weight shape')
    # Reject extreme scales explicitly. No silent normalization or clipping.
    need(all(type(v) is float and math.isfinite(v) and 2.**-400 <= v <= 2.**400 for v in values), 'weight positivity/finiteness/scale')
    need(packet['method'] == WEIGHT_METHOD and packet['matrix'] == I.matrix_hash(a)
         and packet['context'] == digest(context) and packet['factor'] == digest(w), 'stale weight input binding')
    need(type(packet['origin']) is str and digest(packet) == expected_digest, 'stale weight digest')
    return values


def produce_weights(a, context, w, expected_digest, meter):
    """Exactly eight Picard passes; no oracle, auxiliary system or convergence claim.

    p <- G(1 + |A-LU|p), G=C(U)^-1 C(L)^-1. Recompute one approximate
    residual row at a time rather than retain E. The independent verifier must
    recompute outward E and all inequalities from actual inputs.
    """
    n, _, _ = validate_factor(a, context, w, expected_digest)
    base = storage_base(w, n, True); meter.entries(base)
    p = [1.]*n
    for _ in range(WEIGHT_PASSES):
        meter.phase = 'weight_production_residual'
        rhs = residual_rows(a, w, meter, base, p, approximate=True)
        meter.phase = 'weight_production_rhs'
        for i in range(n):
            meter.charge(); rhs[i] += 1.
            need(math.isfinite(rhs[i]), 'weight producer RHS overflow')
        new_p = comparison_vector(w, rhs, meter, 'weight_production_comparison', approximate=True)
        need(all(2.**-400 <= v <= 2.**400 for v in new_p), 'weight producer scale refusal')
        p = new_p
        del new_p, rhs
        meter.weight_passes_completed += 1
    packet = weight_packet(a, context, w, p, 'candidate:fixed-eight-pass')
    meter.weight_outputs.append({'sha256': digest(packet), 'passes': WEIGHT_PASSES, 'min': min(p), 'max': max(p)})
    return packet, digest(packet)


def verify(a, context, w, expected_digest, meter, weights=None, expected_weights_digest=None):
    n, L, U = validate_factor(a, context, w, expected_digest)
    p = None if weights is None else validate_weights(a, context, w, weights, expected_weights_digest)
    need(weights is not None or expected_weights_digest is None, 'missing bound weights')
    retained = sum(map(len, L)) + sum(map(len, U))
    base = storage_base(w, n, p is not None); meter.entries(base)
    meter.phase = 'weighted_residual' if p is not None else 'residual'
    r = residual_rows(a, w, meter, base, p)
    z = comparison_vector(w, r, meter, 'comparison_residual')
    if p is not None:
        meter.phase = 'weighted_comparison_scaling'
        q = max(meter.div(v, pi) for v, pi in zip(z, p))
    else: q = max(z)
    del z
    y = comparison_vector(w, [1.]*n, meter, 'comparison_ones')
    if p is not None:
        meter.phase = 'weighted_comparison_scaling'
        k = max(meter.div(v, pi) for v, pi in zip(y, p))
    else: k = max(y)
    del y
    result = {'q': q, 'K': k, 'factor_entries': retained, 'residual_row_upper': r,
              'factor_sha256': digest(w),
              'weights_sha256': None if weights is None else digest(weights),
              'max_weight': 1. if p is None else max(p),
              'updates': meter.work.updates, 'phase_updates': dict(meter.phases),
              'peak_entries': meter.work.peak_entries, 'dropped_products': meter.dropped_products}
    if q >= 1:
        result.update(status='REFUSED', reason='comparison residual norm is not below one')
        return result
    meter.phase = 'neumann'; meter.charge()
    denominator = I.sub((1.,1.), (q,q))[0]
    need(denominator > 0, 'unresolved Neumann denominator')
    inv = meter.div(k, denominator)
    if p is not None: inv = meter.mul(max(p), inv)
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
    meter.charge(3*n*n)  # two midpoint products plus addition per entry
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


def block_certificate(blocks, D, context, meter, patterns=None, weight_mode=None, supplied_weights=None):
    """Tiny factor-only Schur bridge, with original lower couplings B.T.

    blocks: [(A,B), ...], stored full operator [[diag(A),B],[B.T,D]].
    No original A*Y check or new physical RHS. h are certificate witnesses only.
    """
    import numpy as np
    need(weight_mode in (None, 'candidate', 'supplied'), 'unknown weight mode')
    need((weight_mode == 'supplied') == (supplied_weights is not None), 'supplied weight mode mismatch')
    if supplied_weights is not None: need(len(supplied_weights) == len(blocks), 'supplied weight board count')
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
        board_context={**context,'board':board_index}
        packet=packet_hash=None
        if weight_mode == 'candidate':
            packet,packet_hash=produce_weights(a,board_context,w,h,meter)
        elif weight_mode == 'supplied':
            packet,packet_hash=supplied_weights[board_index]
        cert=verify(a,board_context,w,h,meter,packet,packet_hash)
        p=None if packet is None else packet['values']
        meter.board_certificates.append(cert)
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
            if p is None:
                correction=meter.mul(ratio,max(map(I.magnitude,values)))
            else:
                # Same weighted norm as the board proof, then convert to inf.
                hnorm=max(meter.div(I.magnitude(v),pi) for v,pi in zip(values,p))
                correction=meter.mul(max(p),meter.mul(ratio,hnorm))
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
            'certificate_sha256':digest({'inputs':global_input_digest,'weights':[c['weights_sha256'] for c in certificates], 'factors':[c['factor_sha256'] for c in certificates],'patterns':patterns,'weight_mode':weight_mode}),
            'updates':meter.work.updates,'phase_updates':dict(meter.phases),
            'peak_entries':meter.work.peak_entries}
