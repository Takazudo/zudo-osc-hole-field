"""Independent tiny exact-rational check of the factor-only Schur lift.

Only generated matrices are used. Dense Fraction algebra is limited to order 16.
This is not an original-data entrypoint or a resource qualification.
"""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
import resource
resource.setrlimit(resource.RLIMIT_AS, (512*1024**2, 512*1024**2))
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
import hashlib
import json
from pathlib import Path
import sys
HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[3]
ROOT = SOURCE.parents[5]
sys.path.insert(0, str(HERE / 'fixture'))
import prototype as P
import numpy as np
from scipy.sparse import csr_matrix
from fractions import Fraction as F
I = P.I


def inverse(a):
    n = len(a)
    assert n <= 6
    r = [list(a[i])+[F(int(i == j)) for j in range(n)] for i in range(n)]
    for k in range(n):
        pivot = next(i for i in range(k, n) if r[i][k])
        r[k], r[pivot] = r[pivot], r[k]
        d = r[k][k]
        r[k] = [v/d for v in r[k]]
        for i in range(n):
            if i != k:
                d = r[i][k]
                r[i] = [x-d*y for x, y in zip(r[i], r[k])]
    return [row[n:] for row in r]


def multiply(a, b):
    return [[sum(x*y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def encloses(v, x):
    return F(v[0]) <= x <= F(v[1])


def absolute_sum(values):
    total = 0.
    for value in values:
        total = I.upper_add(total, abs(float(value)))
    return total


def board(g, ground, weights, pattern):
    a = np.array([[g+ground, -g], [-g, g]], dtype=float)
    rt = .7
    a += np.outer(weights, weights)/rt
    b = -np.asarray(weights)/rt
    d = 1./rt
    matrix = csr_matrix(a)
    matrix.eliminate_zeros()
    meter = P.Meter()
    fixed_pattern = P.pattern_of(matrix, True) if pattern == 'full' else [[0], [1]]
    context = {'fixture': 'independent-factor-Schur'}
    witness, stamp = P.produce(matrix, context, fixed_pattern, meter)
    cert = P.verify(matrix, context, witness, stamp, meter)
    if cert['status'] != 'CERTIFIED':
        return None, cert
    lower, upper = witness['L'], witness['U']
    y = []
    for i in range(2):
        v = (float(b[i]),)*2
        for j, coefficient in lower[i]:
            v = I.sub(v, I.mul((coefficient, coefficient), y[j]))
        y.append(v)
    h = [None]*2
    for i in range(1, -1, -1):
        v = y[i]
        diagonal = None
        for j, coefficient in upper[i]:
            if i == j:
                diagonal = coefficient
            else:
                v = I.sub(v, I.mul((coefficient, coefficient), h[j]))
        h[i] = (I.div_positive(v, (diagonal, diagonal)) if diagonal > 0 else
                I.div_positive((-v[1], -v[0]), (-diagonal, -diagonal)))
    q = cert['q']
    denominator = I.sub((1., 1.), (q, q))[0]
    error = I.upper_mul(I.div_positive((q, q), (denominator, denominator))[1],
                        max(map(I.magnitude, h)))
    schur = (d, d)
    bsum = 0.
    for bi, hi in zip(b, h):
        schur = I.sub(schur, I.mul((float(bi),)*2, hi))
        bsum = I.upper_add(bsum, abs(float(bi)))
    radius = I.upper_mul(bsum, error)
    schur = I.add(schur, (-radius, radius))
    ainv = inverse([[F(float(v)) for v in row] for row in a])
    exact_h = multiply(ainv, [[F(float(v))] for v in b])
    exact_s = F(d)-sum(F(float(b[i]))*exact_h[i][0] for i in range(2))
    assert encloses(schur, exact_s)
    for i in range(2):
        assert encloses(I.add(h[i], (-error, error)), exact_h[i][0])
    return {'a': a, 'b': b, 'd': d, 's': schur, 'exact_s': exact_s,
            'inverse': cert['inverse_infinity_upper'], 'q': q, 'radius': radius}, cert


def constant_schur(board_record):
    """Scalar-terminal identity, verified from stored A and B without metadata."""
    bd = board_record
    row_residuals = []
    additions = 0
    for i in range(2):
        value = (float(bd['b'][i]),)*2
        for coefficient in bd['a'][i]:
            value = I.add(value, (float(coefficient),)*2)
            additions += 1
        row_residuals.append(I.magnitude(value))
    residual = max(row_residuals)
    center = (bd['d'],)*2
    bnorm = 0.
    for bi in bd['b']:
        center = I.add(center, (float(bi),)*2)
        bnorm = I.upper_add(bnorm, abs(float(bi)))
        additions += 2
    radius = I.upper_mul(I.upper_mul(bd['inverse'], bnorm), residual)
    schur = I.add(center, (-radius, radius))
    assert encloses(schur, bd['exact_s'])
    info = {'original_factor_radius': bd['radius'], 'constant_residual': residual,
            'constant_radius': radius, 'inverse_bound': bd['inverse'],
            'row_sum_additions': 4, 'all_additions': additions+1,
            'upper_multiplications': 2}
    bd['s'], bd['radius'] = schur, radius
    return info


def run(ground, pattern, kb_constant=False):
    aa, ca = board(2., ground, [.25, .75], pattern)
    bb, cb = board(3., 0., [1/3, 2/3], 'diagonal' if kb_constant else pattern)
    if aa is None or bb is None:
        return {'ground': ground, 'pattern': pattern,
                'board_refusal': {'KA': ca['q'], 'KB': cb['q']}}
    constant_info = constant_schur(bb) if kb_constant else None
    wire = 4.
    schur = [[I.add(aa['s'], (wire, wire)), (-wire, -wire)],
             [(-wire, -wire), I.add(bb['s'], (wire, wire))]]
    midpoint = np.array([[sum(v)/2 for v in row] for row in schur])
    approximate_inverse = np.linalg.inv(midpoint)
    q = knorm = 0.
    for i in range(2):
        row_sum = inverse_row_sum = 0.
        for j in range(2):
            value = (float(i == j),)*2
            for k in range(2):
                value = I.sub(value, I.mul((float(approximate_inverse[i, k]),)*2,
                                          schur[k][j]))
            row_sum = I.upper_add(row_sum, I.magnitude(value))
            inverse_row_sum = I.upper_add(inverse_row_sum, abs(float(approximate_inverse[i, j])))
        q = max(q, row_sum)
        knorm = max(knorm, inverse_row_sum)
    result = {'ground': ground, 'pattern': pattern,
              'board_q': [aa['q'], bb['q']],
              'board_S_radius': [aa['radius'], bb['radius']], 'schur_q': q}
    if kb_constant:
        result['KB_pattern'] = 'diagonal'
        result['KB_constant_witness'] = constant_info
    if q >= 1:
        result['status'] = 'SCHUR_REFUSED'
        return result
    sinv = I.div_positive((knorm, knorm), (I.sub((1., 1.), (q, q))[0],)*2)[1]
    boards = [aa, bb]
    forward = max(I.upper_mul(bd['inverse'], max(abs(bd['b']))) for bd in boards)
    backward = max(I.upper_mul(bd['inverse'], absolute_sum(bd['b'])) for bd in boards)
    bound = I.upper_mul(I.upper_mul(I.upper_add(1., forward),
                                    max(sinv, *[bd['inverse'] for bd in boards])),
                        I.upper_add(1., backward))
    # Exact terminal diagonal is stored D plus stored wire, not a newly rounded sum.
    matrix = [[F(0) for j in range(6)] for i in range(6)]
    for offset, terminal, bd in [(0, 4, aa), (2, 5, bb)]:
        for i in range(2):
            for j in range(2):
                matrix[offset+i][offset+j] = F(float(bd['a'][i, j]))
            matrix[offset+i][terminal] = matrix[terminal][offset+i] = F(float(bd['b'][i]))
        matrix[terminal][terminal] = F(bd['d'])+F(wire)
    matrix[4][5] = matrix[5][4] = -F(wire)
    exact_norm = max(sum(abs(v) for v in row) for row in inverse(matrix))
    assert F(bound) >= exact_norm
    result.update(status='CERTIFIED', global_inverse_bound=bound,
                  exact_inverse_norm=float(exact_norm),
                  exact_inverse_norm_fraction=str(exact_norm))
    return result


def weighted_tree_oracle():
    """Exact proposal calculation; obtaining h uses a tiny dense oracle ONLY."""
    side = 4
    n = side*side
    a = [[F(0) for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in [i+1 if i % side < side-1 else -1, i+side if i+side < n else -1]:
            if j >= 0:
                a[i][i] += 1
                a[j][j] += 1
                a[i][j] -= 1
                a[j][i] -= 1
    a[0][0] += 1
    rows = [list(row)+[F(1)] for row in a]
    for k in range(n):
        diagonal = rows[k][k]
        rows[k] = [v/diagonal for v in rows[k]]
        for i in range(n):
            if i != k:
                coefficient = rows[i][k]
                rows[i] = [x-coefficient*y for x, y in zip(rows[i], rows[k])]
    h = [row[-1] for row in rows]
    assert min(h) > 0

    def parent(i):
        return i-side if i >= side else i-1 if i else None

    def solve(rhs):
        values = []
        for i in range(n):
            previous = parent(i)
            values.append((rhs[i]+(values[previous] if previous is not None else 0))/a[i][i])
        return values

    y = solve([F(1)]*n)
    r = [sum(abs(a[i][j]-(a[i][i] if i == j else -1 if parent(i) == j else 0))*h[j]
             for j in range(n)) for i in range(n)]
    z = solve(r)
    ratios = [yi/hi for yi, hi in zip(y, h)]
    q = max(zi/hi for zi, hi in zip(z, h))
    k = max(ratios)
    assert q == 1-min(ratios) and q < 1
    q0 = 1-min(solve([F(int(i == 0)) for i in range(n)]))
    weighted_bound = max(h)*k/(1-q)
    assert weighted_bound >= max(h)
    return {'side': side, 'max_h_exact': str(max(h)), 'weighted_q_exact': str(q),
            'weighted_K_exact': str(k), 'weighted_inverse_upper_exact': str(weighted_bound),
            'weighted_inverse_upper': float(weighted_bound),
            'unweighted_inverse_upper': float(max(y)/(1-q0)),
            'actual_inverse_norm': float(max(h)),
            'weight_production': 'exact dense Fraction oracle ONLY; no original witness or production route',
            'status': 'EXACT_PROPOSAL_CALCULATION_ONLY'}


if __name__ == '__main__':
    cases = [run(1., 'full'), run(2**-30, 'full'), run(1., 'diagonal'),
             run(1., 'full', kb_constant=True)]
    assert [case['status'] for case in cases] == ['CERTIFIED', 'CERTIFIED', 'SCHUR_REFUSED', 'CERTIFIED']
    files = [Path(__file__).resolve(), Path(P.__file__).resolve(), SOURCE/'attribution_uniqueness.py']
    print(json.dumps({'reviewer': '/root/math_review', 'synthetic_only': True,
                      'limits': {'order': 16, 'address_space_MiB': 512,
                                 'cpu_seconds': 20, 'blas_threads': 1},
                      'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                      'cases': cases, 'weighted_tree_proposal': weighted_tree_oracle(),
                      'result': 'PASS'}, indent=2))
