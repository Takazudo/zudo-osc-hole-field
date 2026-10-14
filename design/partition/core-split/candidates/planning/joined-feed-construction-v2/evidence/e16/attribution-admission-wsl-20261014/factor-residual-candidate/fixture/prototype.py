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
        for k in range(a.indptr[i],a.indptr[i+1]):
            j=int(a.indices[k]);v=float(a.data[k])
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


def produce_coercivity_tree(a, context, meter):
    validate_a(a);n=a.shape[0]
    # Row-local dyadic scratch, parent, edge, BFS order; independent recomputation.
    meter.entries(8*n+16)
    root=-1;best=0
    for i,margin in enumerate(symmetric_margins(a,meter,'coercivity_producer_margins')):
        integer_charge(meter,1,DYADIC_BITS,'root_margin_comparison')
        if margin>best:root,best=i,margin
    need(root>=0,'coercivity no positive root margin')
    g=positive_dyadic_floor(best,meter)
    del best,margin
    parent=[-1]*n;edge=[0.]*n;order=[root];parent[root]=root
    meter.phase='coercivity_producer_tree'
    for i in order:
        for k in range(a.indptr[i],a.indptr[i+1]):
            j=int(a.indices[k])
            if parent[j]!=-1: continue
            sij=half_sum(float(a.data[k]),stored_reverse(a,i,j),meter)
            integer_charge(meter,1,DYADIC_BITS,'edge_sign_comparison')
            if sij<0:
                integer_charge(meter,1,DYADIC_BITS,'edge_negation')
                parent[j]=i;edge[j]=positive_dyadic_floor(-sij,meter);order.append(j)
    need(len(order)==n,'coercivity negative-edge tree disconnected')
    packet={'method':COERCIVITY_METHOD,'matrix':I.matrix_hash(a),'context':digest(context),
            'root':root,'ground':g,'parent':parent,'edge':edge,'order':order}
    return packet,digest(packet)


def verify_coercivity_tree(a, context, packet, expected_digest, meter, refine=False):
    """Independent SDD/tree coercivity proof for the complete stored operator.

    If S+delta*I-T is SDD, S>=T-delta*I. For nonsymmetric A,
    ||A x||2 >= lambda_min(S)||x||2. Trace(T^-1)=n/g+sum(subtree_size/c);
    inverse <=ceil(sqrt(n))*trace/(1-delta*trace) when delta*trace<1.
    Integer square root avoids relying on correct libm rounding for sqrt.
    """
    validate_a(a);n=a.shape[0];meter.entries(12*n+16)
    need(type(packet) is dict and set(packet)=={'method','matrix','context','root','ground','parent','edge','order'},'coercivity schema')
    need(packet['method']==COERCIVITY_METHOD and packet['matrix']==I.matrix_hash(a)
         and packet['context']==digest(context) and digest(packet)==expected_digest,'stale coercivity binding')
    root,g=packet['root'],packet['ground'];parent,edge,order=packet['parent'],packet['edge'],packet['order']
    need(type(root) is int and 0<=root<n and type(g) is float and math.isfinite(g) and g>0,'coercivity root/ground')
    need(type(parent) is list and type(edge) is list and type(order) is list
         and len(parent)==len(edge)==len(order)==n,'coercivity tree shape')
    need(all(type(i) is int and 0<=i<n for i in order) and sorted(order)==list(range(n))
         and order[0]==root,'coercivity order permutation')
    need(all(type(i) is int and 0<=i<n for i in parent),'coercivity parent index')
    need(all(type(c) is float and math.isfinite(c) and c>=0 for c in edge)
         and edge[root]==0. and parent[root]==root,'coercivity edge shape')
    deficit=0
    for i,margin in enumerate(symmetric_margins(a,meter,'coercivity_verify_margins')):
        integer_charge(meter,2,DYADIC_BITS,'deficit_negation_comparison');deficit=max(deficit,-margin)
        if i==root:
            integer_charge(meter)
            need(dyadic(g,meter)<=margin,'coercivity excess root ground')
    del margin
    meter.phase='coercivity_verify_tree';seen=[False]*n;seen[root]=True
    for i in order:
        if i==root:continue
        j=parent[i];need(seen[j] and edge[i]>0,'coercivity parent order/edge')
        aij=stored_reverse(a,j,i);aji=stored_reverse(a,i,j)
        sij=half_sum(aij,aji,meter)
        integer_charge(meter,2,DYADIC_BITS,'conductance_negation_comparison')
        need(dyadic(edge[i],meter)<=-sij,'coercivity excess tree conductance')
        seen[i]=True
    mass=[1]*n
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
    delta=0.
    if deficit:
        delta=positive_dyadic_floor(deficit,meter)
        integer_charge(meter,1,DYADIC_BITS,'deficit_rounding_comparison')
        if dyadic(delta,meter)<deficit:
            meter.charge();delta=math.nextafter(delta,math.inf)
    shift_q=meter.mul(delta,trace)
    need(shift_q<1.,'coercivity diagonal deficit defeats tree bound')
    meter.charge();denominator=I.sub((1.,1.),(shift_q,shift_q))[0]
    meter.charge()  # exact bounded integer-to-binary64 conversion
    bound=meter.div(meter.mul(float(ceil_root),trace),denominator)
    need(math.isfinite(bound),'coercivity inverse-bound overflow')
    trace_bound=bound;refinement={'status':'NOT REQUESTED'}
    if refine:
        meter.phase='coercivity_path_cauchy'
        path=[0.]*n;path[root]=meter.div(1.,g)
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
            'matrix_sha256':I.matrix_hash(a),'witness_sha256':digest(packet),
            'updates':meter.work.updates,'phase_updates':dict(meter.phases),
            'integer_operations':meter.integer_operations,'integer_phase_operations':dict(meter.integer_phases),
            'integer_max_bits':DYADIC_BITS,'integer_kernel_units':dict(meter.integer_kernel_units),
            'integer_bit_work_envelope':meter.integer_bit_work_envelope,'peak_entries':meter.work.peak_entries,
            'scope':'whole stored operator; no factor, residual expansion or Schur solve'}


def coercivity_interval_certificate(a, entries, context, meter):
    """Whole CSR midpoint plus explicitly bound sparse interval replacements.

    The final infinity-norm perturbation proof supports nonsymmetric interval
    entries too; it does not rely on a symmetric radius or a row-to-2norm claim.
    Input assembly is caller work and is not claimed as part of these counters.
    """
    validate_a(a);n=a.shape[0]
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
    bound_context={'context':context,'interval_replacements':entries}
    packet,h=produce_coercivity_tree(a,bound_context,meter)
    result=verify_coercivity_tree(a,bound_context,packet,h,meter,refine=True)
    meter.phase='coercivity_interval_perturbation';meter.entries(14*n+16+4*len(entries))
    rows=[0.]*n
    for i,j,lo,hi in entries:
        # Sparse scalar read is index work, no numerical solve or summation.
        value=float(a[i,j])
        meter.charge();difference=I.sub((lo,hi),(value,value))
        rows[i]=meter.add(rows[i],I.magnitude(difference))
    radius=max(rows);q=meter.mul(result['inverse_infinity_upper'],radius)
    need(q<1.,'coercivity interval perturbation refuses')
    meter.charge();denominator=I.sub((1.,1.),(q,q))[0]
    bound=meter.div(result['inverse_infinity_upper'],denominator)
    result.update(midpoint_inverse_infinity_upper=result['inverse_infinity_upper'],
                  inverse_infinity_upper=bound,interval_perturbation_q=q,
                  interval_radius_infinity_upper=radius,
                  interval_operator_sha256=digest({'A':I.matrix_hash(a),'context':bound_context}),
                  updates=meter.work.updates,phase_updates=dict(meter.phases),
                  peak_entries=meter.work.peak_entries)
    return result
