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
import array
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
TREE_WEIGHT_METHOD = 'synthetic-stored-tree-poisson-v1'


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


def weight_packet(a, context, w, values, origin, method=WEIGHT_METHOD):
    """Bind actual exact binary64 weights; origin is descriptive, never trusted."""
    return {'method': method, 'matrix': I.matrix_hash(a),
            'context': digest(context), 'factor': digest(w), 'values': values,
            'origin': origin}


def validate_weights(a, context, w, packet, expected_digest):
    need(type(packet) is dict and set(packet) == {'method','matrix','context','factor','values','origin'}, 'weight schema')
    values = packet['values']
    need(type(values) is list and len(values) == a.shape[0], 'weight shape')
    # Reject extreme scales explicitly. No silent normalization or clipping.
    need(all(type(v) is float and math.isfinite(v) and 2.**-400 <= v <= 2.**400 for v in values), 'weight positivity/finiteness/scale')
    need(packet['method'] in (WEIGHT_METHOD, TREE_WEIGHT_METHOD) and packet['matrix'] == I.matrix_hash(a)
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


def produce_tree_weights(a, context, w, expected_digest, meter):
    """One stored-coefficient BFS tree and two tree passes, never an original-system solve.

    A symmetric Z-matrix with nonnegative approximate row sums supplies a
    conductance graph. Keep only the strongest grounded root and BFS edges.
    The tree surrogate solves T p=1 by subtree mass and edge integration.
    This identity is NOT a certificate for A: omitted-edge flux can be negative.
    All acceptance still requires the unchanged independent weighted verifier.
    """
    from bisect import bisect_left
    n, _, _ = validate_factor(a, context, w, expected_digest)
    base = storage_base(w, n, True)
    # Grounds, parents, edge conductances, order/queue, subtree mass, output.
    meter.entries(base + 6*n)
    meter.phase = 'weight_tree_coefficients'
    grounds = []
    for i in range(n):
        ground = 0.
        for k in range(a.indptr[i], a.indptr[i+1]):
            j = int(a.indices[k]); value = float(a.data[k])
            meter.charge(); ground += value
            need(math.isfinite(ground), 'tree row-sum overflow')
            if i == j:
                need(value > 0., 'tree positive diagonal required')
            else:
                need(value < 0., 'tree Z coefficients required')
                first, last = int(a.indptr[j]), int(a.indptr[j+1])
                q = bisect_left(a.indices, i, first, last)
                need(q < last and int(a.indices[q]) == i and float(a.data[q]) == value,
                     'tree symmetric stored coefficients required')
        need(ground >= 0., 'tree nonnegative approximate row sum required')
        grounds.append(ground)
    root = max(range(n), key=lambda i: grounds[i])
    need(grounds[root] > 0., 'tree no positive ground')
    parent = [-1]*n; edge = [0.]*n; order = [root]; parent[root] = root
    # Fixed canonical CSR order; every row scanned once, no ordering trials.
    for i in order:
        for k in range(a.indptr[i], a.indptr[i+1]):
            j = int(a.indices[k])
            if parent[j] == -1:
                parent[j] = i; edge[j] = -float(a.data[k]); order.append(j)
    need(len(order) == n, 'tree disconnected coefficient graph')
    mass = [1.]*n
    meter.phase = 'weight_tree_subtree'
    for i in reversed(order):
        if i == root: continue
        meter.charge(); mass[parent[i]] += mass[i]
    p = [0.]*n
    meter.phase = 'weight_tree_integration'
    meter.charge(); p[root] = float(n)/grounds[root]
    for i in order:
        if i == root: continue
        meter.charge(2); p[i] = p[parent[i]] + mass[i]/edge[i]
    need(all(math.isfinite(v) and 2.**-400 <= v <= 2.**400 for v in p),
         'tree weight scale/overflow refusal')
    packet = weight_packet(a, context, w, p, 'candidate:stored-BFS-tree', TREE_WEIGHT_METHOD)
    meter.weight_outputs.append({'sha256': digest(packet), 'passes': 2,
        'auxiliary_tree_order': n, 'auxiliary_edges': n-1, 'root': root,
        'min': min(p), 'max': max(p)})
    del grounds, parent, edge, order, mass
    meter.entries(base)
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

class JoinedRows:
    """Nonowning bounded joined-operator view; only small D midpoint is copied.

    Each block is (CSR A, dense binary64 B, global terminal-column tuple).
    Reverse terminal incidence uses explicit dense B scans, never a transpose.
    Represented midpoint input bytes are rehashed when requested; intervals are
    separately bound by the interval wrapper. No cached construction identity. This is still a synthetic order<=128 view.
    """
    def __init__(self, blocks, terminal_intervals, meter):
        self.blocks=tuple(blocks);self.intervals=terminal_intervals;self.meter=meter
        self.access={'A_entries':0,'B_entries':0,'D_entries':0,'row_calls':0,
                     'lookup_calls':0,'hash_bytes':0,'validation_entries':0,'validation_rows':0,'index_comparisons':0}
        self.m=len(terminal_intervals);self.offsets=[];offset=0
        need(0<self.m<=8,'virtual terminal order cap')
        for a,_,_ in self.blocks:self.offsets.append(offset);offset+=a.shape[0]
        self.free=offset;self.shape=(offset+self.m,offset+self.m)
        self.midpoint=[]
        meter.entries(self.m*self.m+len(self.blocks)+8)
        self.owned_slots=meter.live-meter.offset
        meter.offset=meter.live
        meter.phase='virtual_terminal_midpoint'
        for row in terminal_intervals:
            need(type(row) is list and len(row)==self.m,'virtual terminal shape')
            out=[]
            for v in row:
                need(type(v) is tuple and len(v)==2 and all(type(x) is float and math.isfinite(x) for x in v)
                     and v[0]<=v[1],'virtual terminal interval')
                with ProposedContribution(meter):
                    meter.charge(3);out.append(v[0]*.5+v[1]*.5)
            self.midpoint.append(out)
        self.validate()

    def validate(self):
        need(0<len(self.blocks)<=2,'virtual board cap')
        offsets=[];total=0
        for a,_,_ in self.blocks:offsets.append(total);total+=a.shape[0]
        need(self.offsets==offsets and self.free==total and self.shape==(total+self.m,total+self.m)
             and 0<self.shape[0]<=128,'virtual stale coordinate layout/order cap')
        need(0<self.m<=8 and len(self.midpoint)==len(self.intervals)==self.m
             and all(len(row)==self.m and all(type(v) is float and math.isfinite(v) for v in row) for row in self.midpoint),
             'virtual midpoint layout/value')
        for row in self.intervals:
            need(type(row) is list and len(row)==self.m,'virtual live interval row')
            for v in row:
                need(type(v) is tuple and len(v)==2 and all(type(x) is float and math.isfinite(x) for x in v)
                     and v[0]<=v[1],'virtual live interval value')
        for a,b,columns in self.blocks:
            self.access['validation_entries']+=a.nnz
            self.access['validation_rows']+=a.shape[0]
            validate_a(a)
            need(type(columns) is tuple and len(set(columns))==len(columns)
                 and all(type(j) is int and 0<=j<self.m for j in columns)
                 and list(columns)==sorted(columns),'virtual terminal mapping')
            need(isinstance(b,np.ndarray) and b.dtype==np.dtype('float64')
                 and b.shape==(a.shape[0],len(columns)) and b.flags.c_contiguous,
                 'virtual coupling shape/type/contiguity')
            for x in b.flat:
                self.access['validation_entries']+=1
                need(math.isfinite(float(x)),'virtual nonfinite coupling')
        # No cached input validation: CSR validation likewise rescans actual bytes.

    def input_hash(self):
        h=hashlib.sha256()
        h.update(digest({'shape':self.shape,'maps':[list(v[2]) for v in self.blocks],
                         'D_midpoint':self.midpoint}).encode())
        for a,b,_ in self.blocks:
            h.update(I.matrix_hash(a).encode())
            h.update(str((b.shape,b.dtype.str)).encode());h.update(memoryview(b).cast('B'))
            self.access['hash_bytes']+=a.indptr.nbytes+a.indices.nbytes+a.data.nbytes+b.nbytes
        return h.hexdigest()

    def row(self, i):
        need(type(i) is int and 0<=i<self.shape[0],'virtual row index')
        self.access['row_calls']+=1
        for offset,(a,b,columns) in zip(self.offsets,self.blocks):
            if offset<=i<offset+a.shape[0]:
                local=i-offset
                for k in range(a.indptr[local],a.indptr[local+1]):
                    self.access['A_entries']+=1
                    yield offset+int(a.indices[k]),float(a.data[k])
                for j,t in enumerate(columns):
                    self.access['B_entries']+=1;v=float(b[local,j])
                    if v!=0.:yield self.free+t,v
                return
        terminal=i-self.free
        for offset,(a,b,columns) in zip(self.offsets,self.blocks):
            if terminal in columns:
                col=columns.index(terminal)
                for local in range(a.shape[0]):
                    self.access['B_entries']+=1;v=float(b[local,col])
                    if v!=0.:yield offset+local,v
        for j,v in enumerate(self.midpoint[terminal]):
            self.access['D_entries']+=1
            if v!=0.:yield self.free+j,v

    def lookup(self,i,j,require=False):
        need(type(i) is int and type(j) is int and 0<=i<self.shape[0] and 0<=j<self.shape[0],'virtual lookup index')
        self.access['lookup_calls']+=1
        for offset,(a,b,columns) in zip(self.offsets,self.blocks):
            if offset<=i<offset+a.shape[0]:
                local=i-offset
                if offset<=j<offset+a.shape[0]:
                    first,last=int(a.indptr[local]),int(a.indptr[local+1])
                    lo,hi=first,last
                    while lo<hi:
                        q=(lo+hi)//2;self.access['index_comparisons']+=1
                        if int(a.indices[q])<j-offset:lo=q+1
                        else:hi=q
                    q=lo;self.access['index_comparisons']+=int(q<last)
                    found=q<last and int(a.indices[q])==j-offset
                    need(found or not require,'coercivity structural symmetry required')
                    self.access['A_entries']+=int(found)
                    return float(a.data[q]) if found else 0.
                if j>=self.free and j-self.free in columns:
                    self.access['B_entries']+=1;v=float(b[local,columns.index(j-self.free)])
                    need(v!=0. or not require,'coercivity structural symmetry required');return v
                need(not require,'coercivity structural symmetry required');return 0.
        if j<self.free:return self.lookup(j,i,require)
        self.access['D_entries']+=1;v=self.midpoint[i-self.free][j-self.free]
        need(v!=0. or not require,'coercivity structural symmetry required');return v

    def interval_entries(self):
        self.validate()
        return [[self.free+i,self.free+j,lo,hi] for i,row in enumerate(self.intervals)
                for j,(lo,hi) in enumerate(row)]


def validate_operator(a):
    if isinstance(a,JoinedRows):a.validate()
    else:validate_a(a)


def operator_hash(a):
    return a.input_hash() if isinstance(a,JoinedRows) else I.matrix_hash(a)


def operator_row(a,i):
    if isinstance(a,JoinedRows):yield from a.row(i)
    else:
        for k in range(a.indptr[i],a.indptr[i+1]):yield int(a.indices[k]),float(a.data[k])


def operator_value(a,i,j):
    return a.lookup(i,j) if isinstance(a,JoinedRows) else float(a[i,j])

# Exact binary64/half-binary64 row arithmetic. This is not an exact solve.
# Separate integer metrics are NOT production scalar updates or hidden in Work.
COERCIVITY_METHOD = 'synthetic-stored-SDD-tree-coercivity-v1'
DYADIC_EXPONENT = 1075
DYADIC_BITS = 2176


def integer_charge(meter, count=1, bits=DYADIC_BITS, kernel='exact_arithmetic'):
    """Bounded exact-arithmetic kernels, NOT machine ops or Work updates.

    One unit is an explicitly declared add/subtract/shift/absolute-value,
    comparison, bit-length query, or fixed-width decoding kernel. Index scans,
    container operations and accounting bookkeeping remain runtime work.
    The retained `integer_operations` name is a compatibility alias for these
    declared units. Each unit ALSO receives a conservative bits**2 logical
    bit-work envelope, so a 2176-bit operation is never discounted as a scalar.
    This envelope is not an instruction count or a production mapping.
    """
    need(type(count) is int and count >= 0 and type(bits) is int and 0 < bits <= DYADIC_BITS,
         'invalid bounded integer kernel charge')
    if getattr(meter,'contribution_active',False):
        meter.contribution_width=max(meter.contribution_width,bits)
    if not hasattr(meter, 'integer_phases'):
        meter.integer_phases = {}; meter.integer_operations = 0; meter.integer_peak_bits = 0
        meter.integer_kernel_units = {}; meter.integer_bit_work_envelope = 0
    meter.integer_operations += count
    meter.integer_phases[meter.phase] = meter.integer_phases.get(meter.phase, 0)+count
    key = f'{kernel}:bits<={bits}'
    meter.integer_kernel_units[key] = meter.integer_kernel_units.get(key, 0)+count
    meter.integer_bit_work_envelope += count*bits*bits
    meter.integer_peak_bits = max(meter.integer_peak_bits, bits)
    need(meter.integer_operations <= 200000, 'fixture declared integer-kernel cap')
    need(time.monotonic()-meter.started < 30, 'fixture integer wall cap')


def dyadic(v, meter):
    """Decode fixed eight-byte IEEE binary64; no ratio/reduction algorithm."""
    import struct
    need(type(v) is float and math.isfinite(v), 'dyadic binary64 input')
    integer_charge(meter, 1, 64, 'binary64_decode')
    raw = struct.unpack('>Q', struct.pack('>d', v))[0]
    integer_charge(meter, 5, 64, 'bit_extract')
    sign = raw >> 63
    exponent = (raw >> 52) & 2047
    fraction = raw & ((1 << 52)-1)
    if exponent:
        integer_charge(meter, 1, 53, 'significand_add')
        significand = (1 << 52) + fraction
        shift = exponent  # -1023-52+1075 == 0, exact fixed exponent identity
    else:
        significand, shift = fraction, 1
    # Bounds follow from finite binary64 before the allocation: 53+2046=2099.
    integer_charge(meter, 1, DYADIC_BITS, 'left_shift')
    value = significand << shift
    if sign:
        integer_charge(meter, 1, DYADIC_BITS, 'negate')
        value = -value
    integer_charge(meter, 2, DYADIC_BITS, 'width_check')
    need(value.bit_length() <= DYADIC_BITS, 'dyadic width cap')
    return value


def half_sum(x, y, meter):
    a, b = dyadic(x,meter), dyadic(y,meter)
    integer_charge(meter, 2, DYADIC_BITS, 'add_and_half_shift')
    # Binary64 inputs are even at exponent -1075; this shift is exact.
    value = (a+b) >> 1
    integer_charge(meter, 2, DYADIC_BITS, 'width_check')
    need(value.bit_length() <= DYADIC_BITS, 'dyadic width cap')
    return value


def positive_dyadic_floor(v, meter):
    integer_charge(meter, 3, DYADIC_BITS, 'positive_width_check')
    need(v > 0 and v.bit_length() <= DYADIC_BITS, 'positive bounded dyadic required')
    integer_charge(meter, 1, DYADIC_BITS, 'bit_length')
    width = v.bit_length()
    integer_charge(meter, 2, 16, 'shift_selection')
    shift = max(0,width-53)
    integer_charge(meter, 1, DYADIC_BITS, 'right_shift')
    significand = v >> shift
    integer_charge(meter, 1, 16, 'scale_exponent')
    exponent = shift-DYADIC_EXPONENT
    # Charge both exact small-int conversion and binary64 power-of-two scaling.
    # The latter can round at the subnormal boundary; verify floor afterwards.
    meter.charge(2)
    try:
        result = math.ldexp(float(significand), exponent)
    except OverflowError:
        need(False, 'dyadic coefficient overflow')
    need(math.isfinite(result) and result > 0, 'dyadic coefficient underflow/overflow')
    decoded = dyadic(result,meter)
    integer_charge(meter, 1, DYADIC_BITS, 'floor_comparison')
    need(decoded <= v, 'dyadic coefficient floor rounding refusal')
    return result


def stored_reverse(a, i, j):
    if isinstance(a,JoinedRows):return a.lookup(j,i,require=True)
    from bisect import bisect_left
    first,last=int(a.indptr[j]),int(a.indptr[j+1])
    q=bisect_left(a.indices,i,first,last)
    need(q < last and int(a.indices[q]) == i, 'coercivity structural symmetry required')
    return float(a.data[q])


def symmetric_margins(a, meter, phase):
    """Exact SDD margins of actual (A+A.T)/2, no inferred conservation.

    Structural symmetry is explicitly required; no transpose-only entry is lost.
    Per row only a few bounded dyadic integers live; margins are streamed.
    """
    meter.phase=phase
    for i in range(a.shape[0]):
        diagonal=None; off=0
        for j,v in operator_row(a,i):
            if j==i: diagonal=dyadic(v,meter)
            else:
                sij=half_sum(v,stored_reverse(a,i,j),meter)
                integer_charge(meter,2,DYADIC_BITS,'absolute_row_accumulation');off+=abs(sij)
                integer_charge(meter,2,DYADIC_BITS,'width_check')
                need(off.bit_length()<=DYADIC_BITS,'dyadic row width cap')
        need(diagonal is not None,'coercivity diagonal required')
        integer_charge(meter,1,DYADIC_BITS,'row_margin');margin=diagonal-off
        integer_charge(meter,2,DYADIC_BITS,'width_check')
        need(margin.bit_length()<=DYADIC_BITS,'dyadic margin width cap')
        yield margin


def coercivity_digest(packet):
    """Stream packed witness bytes; list witnesses keep their historical hash."""
    buffers={k:v for k,v in packet.items() if isinstance(v,array.array)}
    if not buffers:return digest(packet)
    h=hashlib.sha256(digest({k:v for k,v in packet.items() if k not in buffers}).encode())
    for k,v in sorted(buffers.items()):
        h.update(digest({'field':k,'typecode':v.typecode,'itemsize':v.itemsize,'length':len(v),'byteorder':sys.byteorder}).encode())
        h.update(memoryview(v).cast('B'))
    return h.hexdigest()


def produce_coercivity_tree(a, context, meter, packed=False, exact_kernel="fixed"):
    validate_operator(a);n=a.shape[0]
    # Row-local dyadic scratch, parent, edge, BFS order; independent recomputation.
    meter.entries(8*n+16)
    exact=ExactRowArithmetic(exact_kernel,meter)
    root=-1;best=exact.zero
    for i,margin in enumerate(exact.rows(a,'coercivity_producer_margins')):
        if exact.compare(margin,best)>0:root,best=i,margin
    need(root>=0,'coercivity no positive root margin')
    g=exact.floor(best)
    del best,margin
    sentinel=n if packed else -1
    if packed:need(n<2**32 and array.array('I').itemsize==4 and array.array('d').itemsize==8,'packed platform widths/range')
    parent=array.array('I',[sentinel])*n if packed else [sentinel]*n
    edge=array.array('d',[0.])*n if packed else [0.]*n
    order=array.array('I',[0])*n if packed else [0]*n
    parent[root]=root;order[0]=root;head=0;tail=1
    meter.phase='coercivity_producer_tree'
    while head<tail:
        i=order[head];head+=1
        for j,v in operator_row(a,i):
            if parent[j]!=sentinel: continue
            sij=exact.half(v,stored_reverse(a,i,j))
            if exact.compare(sij,exact.zero)<0:
                parent[j]=i;edge[j]=exact.floor(exact.negative(sij))
                order[tail]=j;tail+=1
    need(tail==n,'coercivity negative-edge tree disconnected')
    packet={'method':COERCIVITY_METHOD,'matrix':operator_hash(a),'context':digest(context),
            'root':root,'ground':g,'parent':parent,'edge':edge,'order':order}
    return packet,coercivity_digest(packet)


def verify_coercivity_tree(a, context, packet, expected_digest, meter, refine=False, path_only=False, exact_kernel="fixed"):
    """Independent SDD/tree coercivity proof for the complete stored operator.

    If S+delta*I-T is SDD, S>=T-delta*I. For nonsymmetric A,
    ||A x||2 >= lambda_min(S)||x||2. Trace(T^-1)=n/g+sum(subtree_size/c);
    inverse <=ceil(sqrt(n))*trace/(1-delta*trace) when delta*trace<1.
    Integer square root avoids relying on correct libm rounding for sqrt.
    """
    validate_operator(a);n=a.shape[0];meter.entries(12*n+16)
    need(type(packet) is dict and set(packet)=={'method','matrix','context','root','ground','parent','edge','order'},'coercivity schema')
    need(packet['method']==COERCIVITY_METHOD and packet['matrix']==operator_hash(a)
         and packet['context']==digest(context) and coercivity_digest(packet)==expected_digest,'stale coercivity binding')
    root,g=packet['root'],packet['ground'];parent,edge,order=packet['parent'],packet['edge'],packet['order']
    need(type(root) is int and 0<=root<n and type(g) is float and math.isfinite(g) and g>0,'coercivity root/ground')
    need(type(parent) in (list,array.array) and type(edge) in (list,array.array) and type(order) in (list,array.array)
         and len(parent)==len(edge)==len(order)==n,'coercivity tree shape')
    packed=isinstance(parent,array.array)
    need(all(isinstance(v,array.array)==packed for v in (parent,edge,order)),'mixed packed/list tree')
    if packed:need(parent.typecode==order.typecode=='I' and edge.typecode=='d' and parent.itemsize==order.itemsize==4 and edge.itemsize==8,'packed tree widths')
    need(order[0]==root,'coercivity order root')
    order_seen=bytearray(n)
    for i in order:
        need(type(i) is int and 0<=i<n and not order_seen[i],'coercivity order permutation')
        order_seen[i]=1
    del order_seen
    need(all(type(i) is int and 0<=i<n for i in parent),'coercivity parent index')
    need(all(type(c) is float and math.isfinite(c) and c>=0 for c in edge)
         and edge[root]==0. and parent[root]==root,'coercivity edge shape')
    exact=ExactRowArithmetic(exact_kernel,meter)
    deficit=exact.zero
    for i,margin in enumerate(exact.rows(a,'coercivity_verify_margins')):
        negative=exact.negative(margin)
        if exact.compare(negative,deficit)>0:deficit=negative
        if i==root:need(exact.compare(exact.decode(g),margin)<=0,'coercivity excess root ground')
    del margin
    meter.phase='coercivity_verify_tree';seen=bytearray(n);seen[root]=1
    for i in order:
        if i==root:continue
        j=parent[i];need(seen[j] and edge[i]>0,'coercivity parent order/edge')
        aij=stored_reverse(a,j,i);aji=stored_reverse(a,i,j)
        sij=exact.half(aij,aji)
        need(exact.compare(exact.decode(edge[i]),exact.negative(sij))<=0,'coercivity excess tree conductance')
        seen[i]=True
    need(not (refine and path_only),'conflicting coercivity norm modes')
    if path_only:
        meter.phase='coercivity_path_only'
        path=array.array('d',[0.])*n if packed else [0.]*n;path[root]=meter.div(1.,g)
        for i in order:
            if i!=root:path[i]=meter.add(path[parent[i]],meter.div(1.,edge[i]))
        rmax=max(path)
        meter.charge();radius_bound=meter.mul(float(n),rmax)
        delta=exact.upper_nonnegative(deficit)
        shift_q=meter.mul(delta,radius_bound)
        need(shift_q<1.,'path-only diagonal deficit defeats tree bound')
        meter.charge();denominator=I.sub((1.,1.),(shift_q,shift_q))[0]
        bound=meter.div(radius_bound,denominator)
        need(math.isfinite(bound),'path-only inverse-bound overflow')
        return {'status':'CERTIFIED','bound_mode':'path-only','inverse_infinity_upper':bound,
            'tree_max_inverse_diagonal_upper':rmax,'tree_radius_bound_upper':radius_bound,
            'diagonal_deficit_upper':delta,'coercivity_shift_q':shift_q,
            'tree_structure_order':n,'tree_structure_edges':n-1,'auxiliary_solve_order':0,
            'tree_construction_float_updates':sum(v for k,v in meter.phases.items() if k.startswith('coercivity_producer')),
            'tree_construction_integer_units':sum(v for k,v in meter.integer_phases.items() if k.startswith('coercivity_producer')),
            'legacy_auxiliary_fields_scope':'legacy snapshot zero fields denote auxiliary solves only; tree construction is reported explicitly here',
            'matrix_sha256':operator_hash(a),'witness_sha256':coercivity_digest(packet),
            'updates':meter.work.updates,'phase_updates':dict(meter.phases),
            'integer_operations':meter.integer_operations,'integer_phase_operations':dict(meter.integer_phases),
            'integer_max_bits':DYADIC_BITS,'integer_kernel_units':dict(meter.integer_kernel_units),
            'integer_bit_work_envelope':meter.integer_bit_work_envelope,'peak_entries':meter.work.peak_entries,
            'packed_tree':packed,'tree_buffer_payload_bytes':25*n if packed else None,
            'scope':'whole stored operator; path-only bound; no mass/trace/sqrt passes'}
    mass=array.array('I',[1])*n if packed else [1]*n
    meter.phase='coercivity_subtree'
    for i in reversed(order):
        if i!=root:
            integer_charge(meter,1,8);mass[parent[i]]+=mass[i]
    meter.phase='coercivity_trace';meter.charge();trace=meter.div(float(n),g)
    for i in order:
        if i!=root:
            meter.charge()  # exact bounded integer-to-binary64 conversion
            trace=meter.add(trace,meter.div(float(mass[i]),edge[i]))
    integer_charge(meter,4,8,'isqrt_square_compare_add');root_n=math.isqrt(n);ceil_root=root_n+(root_n*root_n<n)
    delta=exact.upper_nonnegative(deficit)
    shift_q=meter.mul(delta,trace)
    need(shift_q<1.,'coercivity diagonal deficit defeats tree bound')
    meter.charge();denominator=I.sub((1.,1.),(shift_q,shift_q))[0]
    meter.charge()  # exact bounded integer-to-binary64 conversion
    bound=meter.div(meter.mul(float(ceil_root),trace),denominator)
    need(math.isfinite(bound),'coercivity inverse-bound overflow')
    trace_bound=bound;refinement={'status':'NOT REQUESTED'}
    if refine:
        meter.phase='coercivity_path_cauchy'
        path=array.array('d',[0.])*n if packed else [0.]*n;path[root]=meter.div(1.,g)
        integer_charge(meter,1,16,'root_mass_square');meter.charge()
        total=meter.div(float(n*n),g)
        for i in order:
            if i==root:continue
            path[i]=meter.add(path[parent[i]],meter.div(1.,edge[i]))
            integer_charge(meter,1,16,'subtree_mass_square');meter.charge()
            total=meter.add(total,meter.div(float(mass[i]*mass[i]),edge[i]))
        rmax=max(path)
        # Trial sqrt never establishes acceptance: independently prove its
        # outward lower square >= the outward upper product. Four attempts max.
        try:
            product=meter.mul(rmax,total)
            meter.charge();root_bound=math.sqrt(product)
            need(math.isfinite(root_bound) and root_bound>0.,'invalid trial sqrt witness')
            established=False
            for attempt in range(4):
                meter.charge();square=I.mul((root_bound,root_bound),(root_bound,root_bound))
                if square[0]>=product:
                    established=True;break
                meter.charge();root_bound=math.nextafter(root_bound,math.inf)
            if established:
                refined=meter.div(root_bound,denominator)
                bound=min(bound,refined)
                refinement={'status':'CERTIFIED','inverse_infinity_upper':refined,
                            'tree_max_inverse_diagonal_upper':rmax,
                            'tree_ones_energy_upper':total,'sqrt_attempts':attempt+1}
            else:refinement={'status':'REFUSED','reason':'four-step outward square check inconclusive'}
        except ValueError as exc:
            # Arithmetic inability to improve does not erase the earlier proof;
            # cumulative work/caps remain in force (cap failures must propagate).
            if 'cap' in str(exc):raise
            refinement={'status':'REFUSED','reason':str(exc)}
        del path
    return {'status':'CERTIFIED','inverse_infinity_upper':bound,'tree_inverse_trace_upper':trace,'trace_inverse_infinity_upper':trace_bound,
            'path_cauchy_refinement':refinement,
            'diagonal_deficit_upper':delta,'coercivity_shift_q':shift_q,
            'tree_structure_order':n,'tree_structure_edges':n-1,'auxiliary_solve_order':0,
            'tree_construction_float_updates':sum(v for k,v in meter.phases.items() if k.startswith('coercivity_producer')),
            'tree_construction_integer_units':sum(v for k,v in meter.integer_phases.items() if k.startswith('coercivity_producer')),
            'legacy_auxiliary_fields_scope':'legacy snapshot zero fields denote auxiliary solves only; tree construction is reported explicitly here',
            'matrix_sha256':operator_hash(a),'witness_sha256':coercivity_digest(packet),
            'updates':meter.work.updates,'phase_updates':dict(meter.phases),
            'integer_operations':meter.integer_operations,'integer_phase_operations':dict(meter.integer_phases),
            'integer_max_bits':DYADIC_BITS,'integer_kernel_units':dict(meter.integer_kernel_units),
            'integer_bit_work_envelope':meter.integer_bit_work_envelope,'peak_entries':meter.work.peak_entries,
            'scope':'whole stored operator; no factor, residual expansion or Schur solve'}


def coercivity_interval_certificate(a, entries, context, meter, bound_mode="refined", packed=False, exact_kernel="fixed", forest=False):
    """Whole CSR midpoint plus explicitly bound sparse interval replacements.

    The final infinity-norm perturbation proof supports nonsymmetric interval
    entries too; it does not rely on a symmetric radius or a row-to-2norm claim.
    Input assembly is caller work and is not claimed as part of these counters.
    """
    need(bound_mode in ('refined','trace','path-only'),'unknown coercivity bound mode')
    validate_operator(a);n=a.shape[0]
    need(type(entries) is list and len(entries)<=128,'interval replacement cap')
    keys=[]
    for entry in entries:
        need(type(entry) is list and len(entry)==4,'interval replacement schema')
        i,j,lo,hi=entry
        need(type(i) is int and type(j) is int and 0<=i<n and 0<=j<n
             and type(lo) is float and type(hi) is float and math.isfinite(lo)
             and math.isfinite(hi) and lo<=hi,'interval replacement value')
        keys.append((i,j))
    need(keys==sorted(set(keys)),'interval replacement uniqueness/order')
    from contextlib import nullcontext
    bound_context={'context':context,'interval_replacements':entries};bound_context_hash=digest(bound_context)
    if forest:
        need(bound_mode=='path-only' and exact_kernel=='compact','forest requires compact path-only mode')
        result=certify_forest(a,bound_context,meter)
    else:
        packet,h=produce_coercivity_tree(a,bound_context,meter,packed=packed,exact_kernel=exact_kernel)
        result=verify_coercivity_tree(a,bound_context,packet,h,meter,refine=bound_mode=='refined',path_only=bound_mode=='path-only',exact_kernel=exact_kernel)
    meter.phase='coercivity_interval_perturbation';meter.entries(14*n+16+4*len(entries))
    rows=[0.]*n
    for i,j,lo,hi in entries:
        # Sparse scalar read is index work, no numerical solve or summation.
        value=operator_value(a,i,j)
        with (ProposedContribution(meter) if forest else nullcontext()):
            meter.charge();difference=I.sub((lo,hi),(value,value))
            rows[i]=meter.add(rows[i],I.magnitude(difference))
    radius=max(rows)
    with (ProposedContribution(meter) if forest else nullcontext()):q=meter.mul(result['inverse_infinity_upper'],radius)
    need(q<1.,'coercivity interval perturbation refuses')
    with (ProposedContribution(meter) if forest else nullcontext()):
        meter.charge();denominator=I.sub((1.,1.),(q,q))[0]
    with (ProposedContribution(meter) if forest else nullcontext()):bound=meter.div(result['inverse_infinity_upper'],denominator)
    need(operator_hash(a)==result['matrix_sha256'] and digest(bound_context)==bound_context_hash,'interval input/context changed during proof')
    if forest:
        result.update(proposed_scalar_contributions=meter.proposed_scalar_contributions,
            proposed_contribution_phases=dict(meter.proposed_contribution_phases),
            proposed_width_histogram=dict(meter.proposed_width_histogram))
    result.update(exact_row_kernel=exact_kernel,midpoint_inverse_infinity_upper=result['inverse_infinity_upper'],
                  inverse_infinity_upper=bound,interval_perturbation_q=q,
                  interval_radius_infinity_upper=radius,
                  interval_operator_sha256=digest({'A':operator_hash(a),'context':bound_context}),
                  updates=meter.work.updates,phase_updates=dict(meter.phases),
                  peak_entries=meter.work.peak_entries)
    return result


# Compact exact row kernel: value is integer significand * 2**exponent.
# Normalization changes representation only; no coefficient or margin rounding.
def compact_validate(a,meter):
    need(type(a) is tuple and len(a)==2 and type(a[0]) is int and type(a[1]) is int,
         'compact canonical tuple/type')
    m,e=a;width=m.bit_length();bits=max(1,min(width,DYADIC_BITS))
    integer_charge(meter,4,bits,'compact_validate_magnitude_width')
    integer_charge(meter,2,16,'compact_validate_exponent')
    need(width<=DYADIC_BITS and -1075<=e<=2048,'compact dyadic range')
    magnitude=abs(m)
    integer_charge(meter,4,bits,'compact_validate_canonical')
    need((m==0 and e==0) or (m!=0 and (magnitude&1)==1),'compact canonical significand')
    return m,e,max(1,width)


def compact_normalize(m, e, meter):
    need(type(m) is int and type(e) is int,'compact normalize integer types')
    width=m.bit_length();bits=max(1,min(width,DYADIC_BITS))
    integer_charge(meter,4,bits,'compact_sign_width')
    integer_charge(meter,2,16,'compact_exponent_range')
    need(width<=DYADIC_BITS and -1075<=e<=2048,'compact dyadic range')
    magnitude=abs(m)
    integer_charge(meter,1,bits,'compact_zero_comparison')
    if not m:return (0,0)
    integer_charge(meter,4,bits,'compact_trailing_zero')
    shift=(magnitude&-magnitude).bit_length()-1
    integer_charge(meter,1,bits,'compact_normalize_shift')
    integer_charge(meter,3,16,'compact_normalize_exponent_and_bounds')
    result_e=e+shift
    need(-1075<=result_e<=2048,'compact normalized exponent range')
    return m>>shift,result_e


def compact_decode(v,meter):
    import struct
    need(type(v) is float and math.isfinite(v),'compact binary64 input')
    integer_charge(meter,1,64,'compact_binary64_decode')
    raw=struct.unpack('>Q',struct.pack('>d',v))[0]
    integer_charge(meter,5,64,'compact_bit_extract')
    sign=raw>>63;exp=(raw>>52)&2047;mant=raw&((1<<52)-1)
    if exp:
        integer_charge(meter,1,53,'compact_significand_add');mant+=(1<<52)
        integer_charge(meter,1,16,'compact_exponent');e=exp-1075
    else:e=-1074
    if sign:
        integer_charge(meter,1,53,'compact_negate');mant=-mant
    return compact_normalize(mant,e,meter)


def compact_add(a,b,meter):
    ma,ea,wa0=compact_validate(a,meter);mb,eb,wb0=compact_validate(b,meter)
    integer_charge(meter,2,max(wa0,wb0),'compact_zero_shortcuts')
    if ma==0:return b
    if mb==0:return a
    integer_charge(meter,3,16,'compact_alignment_exponents')
    e=min(ea,eb);sa=ea-e;sb=eb-e
    integer_charge(meter,5,16,'compact_alignment_width_arithmetic')
    wa=wa0+sa;wb=wb0+sb;result_width=max(wa,wb)+1
    need(result_width<=DYADIC_BITS,'compact alignment width cap')
    integer_charge(meter,1,wa,'compact_align_left')
    integer_charge(meter,1,wb,'compact_align_right')
    integer_charge(meter,1,result_width,'compact_add')
    return compact_normalize((ma<<sa)+(mb<<sb),e,meter)


def compact_negative(a,meter):
    m,e,width=compact_validate(a,meter)
    integer_charge(meter,1,width,'compact_negation')
    return -m,e


def compact_absolute(a,meter):
    m,e,width=compact_validate(a,meter)
    integer_charge(meter,1,width,'compact_absolute')
    return abs(m),e


def compact_half_sum(x,y,meter):
    m,e=compact_add(compact_decode(x,meter),compact_decode(y,meter),meter)
    integer_charge(meter,1,max(1,m.bit_length()),'compact_half_zero')
    if not m:return 0,0
    integer_charge(meter,1,16,'compact_half_exponent')
    return compact_normalize(m,e-1,meter)


def compact_to_fixed(a,meter):
    m,e,width=compact_validate(a,meter)
    integer_charge(meter,1,width,'compact_fixed_zero')
    if not m:return 0
    integer_charge(meter,1,16,'compact_fixed_exponent')
    shift=e+DYADIC_EXPONENT
    integer_charge(meter,4,16,'compact_fixed_width_check')
    need(shift>=0 and width+shift<=DYADIC_BITS,'compact fixed width cap')
    integer_charge(meter,1,width+shift,'compact_fixed_shift')
    return m<<shift


def compact_symmetric_margins(a,meter,phase,as_fixed=True):
    """One exact row at a time; final margin uses the established proof ABI.

    Internal accumulator exponents adapt and all rescaling remains charged.
    as_fixed=True preserves the row-only reference interface; the complete compact
    certificate path selects False and keeps root/deficit/edge scalars compact.
    """
    meter.phase=phase
    for i in range(a.shape[0]):
        diagonal=None;off=(0,0)
        for j,v in operator_row(a,i):
            if i==j:diagonal=compact_decode(v,meter)
            else:
                sij=compact_half_sum(v,stored_reverse(a,i,j),meter)
                off=compact_add(off,compact_absolute(sij,meter),meter)
        need(diagonal is not None,'coercivity diagonal required')
        margin=compact_add(diagonal,compact_negative(off,meter),meter)
        yield compact_to_fixed(margin,meter) if as_fixed else margin


def compact_compare(a,b,meter):
    ma,ea,wa=compact_validate(a,meter);mb,eb,wb=compact_validate(b,meter)
    integer_charge(meter,8,max(wa,wb),'compact_compare_sign_and_branches')
    sa=(ma>0)-(ma<0);sb=(mb>0)-(mb<0)
    if sa!=sb:
        integer_charge(meter,3,16,'compact_compare_differing_sign_result')
        return (sa>sb)-(sa<sb)
    if sa==0:return 0
    integer_charge(meter,3,16,'compact_compare_leading_position')
    la,lb=ea+wa,eb+wb
    if la!=lb:
        integer_charge(meter,4,16,'compact_compare_differing_position_result')
        return sa*((la>lb)-(la<lb))
    integer_charge(meter,3,16,'compact_compare_alignment')
    e=min(ea,eb);shift_a=ea-e;shift_b=eb-e
    integer_charge(meter,5,16,'compact_compare_width_precheck')
    width=max(wa+shift_a,wb+shift_b)
    need(width<=DYADIC_BITS,'compact compare width cap')
    integer_charge(meter,8,width,'compact_compare_absolute_shift_compare')
    aa=abs(ma)<<shift_a;bb=abs(mb)<<shift_b
    return sa*((aa>bb)-(aa<bb))


def compact_positive_floor(a,meter):
    m,e,width=compact_validate(a,meter)
    integer_charge(meter,1,width,'compact_floor_positive')
    need(m>0,'compact floor requires positive input')
    integer_charge(meter,2,16,'compact_floor_shift_selection')
    shift=max(0,width-53)
    integer_charge(meter,1,width,'compact_floor_shift')
    significand=m>>shift
    integer_charge(meter,1,16,'compact_floor_exponent')
    exponent=e+shift
    meter.charge(2)
    try:result=math.ldexp(float(significand),exponent)
    except OverflowError:need(False,'compact coefficient overflow')
    need(math.isfinite(result) and result>0,'compact coefficient underflow/overflow')
    need(compact_compare(compact_decode(result,meter),a,meter)<=0,'compact coefficient floor rounding refusal')
    return result


class ExactRowArithmetic:
    """Small dispatch for the two retained exact representations, same proof."""
    def __init__(self,mode,meter):
        need(mode in ('fixed','compact'),'unknown exact row kernel')
        self.compact=mode=='compact';self.meter=meter
        self.zero=(0,0) if self.compact else 0
    def rows(self,a,phase):
        return compact_symmetric_margins(a,self.meter,phase,as_fixed=False) if self.compact else symmetric_margins(a,self.meter,phase)
    def decode(self,v):
        return compact_decode(v,self.meter) if self.compact else dyadic(v,self.meter)
    def half(self,x,y):
        return compact_half_sum(x,y,self.meter) if self.compact else half_sum(x,y,self.meter)
    def compare(self,a,b):
        if self.compact:return compact_compare(a,b,self.meter)
        integer_charge(self.meter,3,DYADIC_BITS,'exact_compare')
        return (a>b)-(a<b)
    def negative(self,a):
        if self.compact:return compact_negative(a,self.meter)
        integer_charge(self.meter,1,DYADIC_BITS,'exact_negate');return -a
    def floor(self,a):
        return compact_positive_floor(a,self.meter) if self.compact else positive_dyadic_floor(a,self.meter)
    def upper_nonnegative(self,a):
        if self.compare(a,self.zero)==0:return 0.
        result=self.floor(a)
        if self.compare(self.decode(result),a)<0:
            self.meter.charge();result=math.nextafter(result,math.inf)
        need(math.isfinite(result) and self.compare(self.decode(result),a)>=0,'exact upper conversion refusal')
        return result


class ProposedContribution:
    """Separate proposed scalar-recurrence ledger; never replaces Work/bit work.

    Width includes every aligned arithmetic operand/result before normalization.
    Failed scopes are charged. This is reviewed for local experimentation only.
    """
    def __init__(self,meter):self.meter=meter
    def __enter__(self):
        m=self.meter;need(not getattr(m,'contribution_active',False),'nested contribution scope')
        m.contribution_active=True;m.contribution_width=64;self.phase=m.phase
        if not hasattr(m,'proposed_scalar_contributions'):
            m.proposed_scalar_contributions=0;m.proposed_contribution_phases={};m.proposed_width_histogram={}
        return self
    def __exit__(self,*exc):
        m=self.meter;width=m.contribution_width;units=(width+63)//64
        m.contribution_active=False
        m.proposed_scalar_contributions+=units
        m.proposed_contribution_phases[self.phase]=m.proposed_contribution_phases.get(self.phase,0)+units
        m.proposed_width_histogram[width]=m.proposed_width_histogram.get(width,0)+1
        need(m.proposed_scalar_contributions<=m.work.max_updates,'fixture proposed-contribution cap')
        return False


def index_visit(meter,event,count=1):
    if not hasattr(meter,'index_visits'):
        meter.index_visits={};meter.index_visit_total=0;meter.index_phase_visits={}
    meter.index_visits[event]=meter.index_visits.get(event,0)+count
    meter.index_visit_total+=count
    meter.index_phase_visits[meter.phase]=meter.index_phase_visits.get(meter.phase,0)+count
    need(meter.index_visit_total<=1000000,'fixture index-visit cap')
    need(time.monotonic()-meter.started<30,'fixture index wall cap')


def checked_coefficient(a,i,j,meter):
    if isinstance(a,JoinedRows):
        before=a.access['index_comparisons'];v=a.lookup(i,j,require=True)
        index_visit(meter,'virtual_reverse_comparisons',a.access['index_comparisons']-before)
        index_visit(meter,'coefficient_read');return v
    lo,last=int(a.indptr[i]),int(a.indptr[i+1]);hi=last
    while lo<hi:
        mid=(lo+hi)//2;index_visit(meter,'reverse_search_comparison')
        if int(a.indices[mid])<j:lo=mid+1
        else:hi=mid
    index_visit(meter,'reverse_final_comparison')
    need(lo<last and int(a.indices[lo])==j,'coercivity structural symmetry required')
    index_visit(meter,'coefficient_read');return float(a.data[lo])


class _VerifiedForest:
    """Private verifier-owned selected edges; no external witness admission."""
    def __init__(self,n,meter):
        need(n<2**32 and array.array('I').itemsize==4 and array.array('d').itemsize==8,'forest packed widths')
        self.n=n;self.meter=meter;self.edges=0
        meter.entries(4*n+16)  # four buffers; exact row scratch is bounded separately
        self.parent=array.array('I',[0])*n;self.edge=array.array('d',[0.])*n
        self.dsu=array.array('I',[0])*n;self.size=array.array('I',[1])*n
        index_visit(meter,'buffer_initialization_elements',4*n)
        for i in range(n):self.parent[i]=i;self.dsu[i]=i
        index_visit(meter,'initial_parent_identity_writes',2*n)
        meter.forest_order=n;meter.forest_selected_edges=0
        meter.forest_buffer_allocated_peak=sum(sys.getsizeof(v) for v in (self.parent,self.edge,self.dsu,self.size))
    def find(self,v):
        root=v;steps=0
        while True:
            index_visit(self.meter,'find_parent_read');p=self.dsu[root]
            if p==root:break
            root=p;steps+=1;need(steps<=self.n,'forest DSU cycle')
        while v!=root:
            index_visit(self.meter,'find_compression_read_write',2)
            p=self.dsu[v];self.dsu[v]=root;v=p
        return root
    def reroot(self,start):
        cur=start;prev=start;carry=0.;steps=0
        while True:
            index_visit(self.meter,'reroot_parent_edge_read',2)
            following=self.parent[cur];old=self.edge[cur]
            self.parent[cur]=prev;self.edge[cur]=carry
            index_visit(self.meter,'reroot_parent_edge_write',2)
            steps+=1;need(steps<=self.n,'forest parent cycle')
            if following==cur:break
            prev,carry,cur=cur,old,following
    def connect(self,u,v,conductance,ru,rv):
        need(ru!=rv,'forest duplicate component merge')
        index_visit(self.meter,'union_size_read',2)
        if self.size[ru]>self.size[rv]:u,v,ru,rv=v,u,rv,ru
        need(self.parent[ru]==ru and self.parent[rv]==rv,'forest oriented-root invariant')
        need(int(self.size[ru])+int(self.size[rv])<=self.n,'forest union size range')
        index_visit(self.meter,'union_invariant_reads',4)
        self.reroot(u)
        self.parent[u]=v;self.edge[u]=conductance
        self.dsu[ru]=rv;self.size[rv]+=self.size[ru];self.edges+=1
        self.meter.forest_selected_edges=self.edges
        index_visit(self.meter,'union_size_update_read',2)
        index_visit(self.meter,'union_parent_edge_size_write',4)
    def release_selection(self):
        del self.dsu,self.size
        self.meter.entries(2*self.n+16)


def certify_forest(a,context,meter):
    """One verifier-owned exhaustive exact row pass plus checked forest/path.

    Inputs must be stably owned during verification. Before/after hashes detect
    persistent mutations; they do not claim to defeat adversarial transient edits.
    No caller row summary, prebuilt edge list or skip-verification flag is accepted.
    """
    validate_operator(a);n=a.shape[0];input_hash=operator_hash(a);context_hash=digest(context)
    forest=_VerifiedForest(n,meter);root=-1;best=(0,0);deficit=(0,0)
    for i in range(n):
        meter.phase='forest_exact_rows'
        # Initialization is a checked coefficient copy/decode, not an arithmetic
        # destination update. Fine integer/index ledgers retain its full work.
        margin=compact_decode(checked_coefficient(a,i,i,meter),meter)
        for j,value in operator_row(a,i):
            index_visit(meter,'stored_row_visit')
            if j==i:continue
            meter.phase='forest_exact_rows'
            with ProposedContribution(meter):
                symmetric=compact_half_sum(value,checked_coefficient(a,j,i,meter),meter)
                margin=compact_add(margin,compact_negative(compact_absolute(symmetric,meter),meter),meter)
            # Only selection sees one triangle; row verification always sees all.
            meter.phase='forest_selection'
            if i<j and compact_compare(symmetric,(0,0),meter)<0:
                ru,rv=forest.find(i),forest.find(j)
                if ru!=rv:
                    with ProposedContribution(meter):
                        conductance=compact_positive_floor(compact_negative(symmetric,meter),meter)
                    forest.connect(i,j,conductance,ru,rv)
                else:index_visit(meter,'discarded_cycle_edge')
        meter.phase='forest_row_reductions'
        if compact_compare(margin,best,meter)>0:root,best=i,margin
        negative=compact_negative(margin,meter)
        if compact_compare(negative,deficit,meter)>0:deficit=negative
    need(root>=0,'forest no positive root margin')
    need(forest.edges==n-1,'forest negative-edge graph disconnected')
    meter.phase='forest_root'
    with ProposedContribution(meter):g=compact_positive_floor(best,meter)
    forest.reroot(root)
    # DSU is no longer used after final root changes; release actual buffers first.
    forest.release_selection()
    meter.entries(5*n+16)
    path=array.array('d',[0.])*n;state=bytearray(n);stack=array.array('I',[0])*n
    index_visit(meter,'buffer_initialization_elements',3*n)
    meter.forest_buffer_allocated_peak=max(meter.forest_buffer_allocated_peak,
        sum(sys.getsizeof(v) for v in (forest.parent,forest.edge,path,state,stack)))
    meter.phase='forest_paths'
    with ProposedContribution(meter):path[root]=meter.div(1.,g)
    state[root]=2;index_visit(meter,'root_path_state_writes',2)
    for start in range(n):
        index_visit(meter,'path_start_visit')
        if state[start]==2:continue
        cur=start;depth=0
        while True:
            index_visit(meter,'path_state_condition_read')
            if state[cur]==2:break
            index_visit(meter,'path_cycle_state_read')
            need(state[cur]==0 and depth<n,'forest path cycle')
            state[cur]=1;stack[depth]=cur;depth+=1;cur=forest.parent[cur]
            index_visit(meter,'path_push_parent_accesses',3)
        while depth:
            depth-=1;v=stack[depth];p=forest.parent[v]
            index_visit(meter,'path_pop_parent_reads',2)
            index_visit(meter,'path_invariant_state_edge_reads',2)
            need(state[p]==2 and forest.edge[v]>0.,'forest rooted path invariant')
            with ProposedContribution(meter):path[v]=meter.add(path[p],meter.div(1.,forest.edge[v]))
            index_visit(meter,'path_numeric_buffer_reads_write',3)
            state[v]=2;index_visit(meter,'path_state_write')
    meter.phase='forest_norm'
    rmax=0.
    for value in path:
        index_visit(meter,'path_norm_buffer_read');index_visit(meter,'path_norm_comparison')
        rmax=max(rmax,value)
    with ProposedContribution(meter):
        meter.charge();radius=meter.mul(float(n),rmax)
    exact=ExactRowArithmetic('compact',meter)
    with ProposedContribution(meter):delta=exact.upper_nonnegative(deficit)
    with ProposedContribution(meter):q=meter.mul(delta,radius)
    need(q<1.,'forest diagonal deficit defeats tree bound')
    with ProposedContribution(meter):
        meter.charge();denominator=I.sub((1.,1.),(q,q))[0]
    with ProposedContribution(meter):bound=meter.div(radius,denominator)
    need(math.isfinite(bound),'forest inverse-bound overflow')
    need(operator_hash(a)==input_hash and digest(context)==context_hash,'forest input/context changed during proof')
    witness=coercivity_digest({'method':'synthetic-verifier-owned-forest-v1','matrix':input_hash,
        'context':context_hash,'root':root,'ground':g,'parent':forest.parent,'edge':forest.edge})
    return {'status':'CERTIFIED','bound_mode':'verified-forest-path-only','inverse_infinity_upper':bound,
        'tree_radius_bound_upper':radius,'tree_max_inverse_diagonal_upper':rmax,
        'diagonal_deficit_upper':delta,'coercivity_shift_q':q,'matrix_sha256':input_hash,
        'witness_sha256':witness,'witness_buffer_hashed_bytes':12*n,'input_hash_passes':2,'root':root,'ground':g,'tree_structure_order':n,'tree_structure_edges':forest.edges,
        'auxiliary_solve_order':0,'tree_buffer_peak_payload_bytes':25*n,
        'tree_buffer_allocated_peak_bytes':meter.forest_buffer_allocated_peak,
        'updates':meter.work.updates,'phase_updates':dict(meter.phases),
        'integer_operations':meter.integer_operations,'integer_phase_operations':dict(meter.integer_phases),
        'integer_bit_work_envelope':meter.integer_bit_work_envelope,'integer_kernel_units':dict(meter.integer_kernel_units),
        'index_visits':dict(meter.index_visits),'index_visit_total':meter.index_visit_total,
        'index_phase_visits':dict(meter.index_phase_visits),
        'proposed_scalar_contributions':meter.proposed_scalar_contributions,
        'proposed_contribution_phases':dict(meter.proposed_contribution_phases),
        'proposed_width_histogram':dict(meter.proposed_width_histogram),'peak_entries':meter.work.peak_entries,
        'accounting_status':'proposed recurrence mapping; not approved for production fit',
        'scope':'one exhaustive verifier-owned row pass; private checked forest; no auxiliary solve'}
