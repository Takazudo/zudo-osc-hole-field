"""Finite-thickness, layered cross-section study for the 28 Molex 150200075 candidate links.

Replaces only the 8-circuit cable capacitance matrix of the retained link-ratio kernel with a
2-D finite-difference solve of the PS-15020-001 cross-section: 0.10 mm copper, 0.30 mm
conductors at 0.50 mm pitch, 0.086 mm polyester+adhesive each side (filling between
conductors), air outside, grounded box far away. Partial inductance uses 0.10 mm copper.
The dielectric constant is not sourced, so it is swept. Requires numpy and scipy.
"""
import argparse
import copy
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'scripts/stack/link_electrical'))
from finite_thickness_fd import solve, readings, open_boundary  # noqa: E402
import numpy as np  # noqa: E402

EPS = (2.5, 3.2, 4.0, 4.7)
LENGTHS = (49.0, 51.0, 53.0)
GRID = {'ladder_h_mm': [0.0125, 0.00625, 0.003125], 'ladder_box_mm': [7.0, 5.0],
        'box_correction': {'h_mm': 0.0125, 'large_box_mm': [20.0, 14.0]}}


def matrix(e):
    """Open-boundary C per metre: grid-extrapolated, box-corrected, plus a conservative copy."""
    W, H = GRID['ladder_box_mm']
    c1, c2, c3 = (open_boundary(solve(eps_d=e, h=h, W=W, H=H)) for h in GRID['ladder_h_mm'])
    off = ~np.eye(len(c3), dtype=bool)
    r = float(np.median((c2 - c1)[off] / (c3 - c2)[off]))
    if not 1.2 < r < 4.5:
        raise ValueError('grid ladder not in the asymptotic range: step ratio %.3f' % r)
    ext = c3 + (c3 - c2) / (r - 1)
    bc = GRID['box_correction']
    big = open_boundary(solve(eps_d=e, h=bc['h_mm'], W=bc['large_box_mm'][0], H=bc['large_box_mm'][1]))
    small = open_boundary(solve(eps_d=e, h=bc['h_mm'], W=W, H=H))
    best = ext + (big - small)
    cons = best + (ext - c3)
    err = float(np.max(np.abs((ext - c3)[off] / ext[off])))
    return best, cons, {'step_ratio': round(r, 3), 'max_rel_extrapolation_offdiag': round(err, 4),
                        'readings_finest_h_pF_per_m': {k: round(v, 2) for k, v in readings(c3).items()}}


def study():
    import link_ratios as lr
    import ds62_table
    orig = lr.le.load_inputs()
    cand = set(json.loads((HERE.parent / 'mc02_molex_candidate/evidence.json').read_text())['candidate_link_ids'])
    links = [l for l in lr.load_record() if l['id'] in cand]
    if len(links) != 28:
        raise ValueError('candidate link scope changed')
    harness_eps = orig['cable']['eps_eff']['value'][-1]
    retained = lr.cable_matrices
    out = {'grid': GRID, 'harness_eps_retained': harness_eps, 'cases': {}}
    try:
        for e in EPS:
            best, cons, conv = matrix(e)
            i2 = copy.deepcopy(orig)
            i2['cable']['pitch_0_5']['conductor_thickness_mm'] = 0.10
            i2['cable']['eps_eff']['value'][-1] = e
            end = i2['cable']['end_equivalent_mm']['value']
            case = {'convergence': conv, 'readings_best_pF_per_m': {k: round(v, 2) for k, v in readings(best).items()}}
            for mlabel, C8 in (('best', best), ('conservative', cons)):
                def matrices(circuits, length_mm, pk, eps_r, key, C8=C8):
                    _, L = retained(circuits, length_mm, pk, eps_r, key)
                    if circuits != 8:
                        raise ValueError('only the 8-circuit cross-section was solved')
                    return C8 * (length_mm + 2 * end) * 1e-3, L
                lr.cable_matrices = matrices
                for label, base_inp in (('harness_same_eps', i2), ('harness_retained_eps', orig)):
                    base = ds62_table.build(base_inp)['baseline']
                    for length in LENGTHS:
                        rows = [lr.link_row(i2, dict(l, cable_length_mm=length), base) for l in links]
                        r = [x['ratio'] for x in rows if x['ratio'] is not None]
                        case[f'{mlabel}_{label}_L{length:g}'] = {'max_ratio': round(max(r), 4),
                                                                 'links_above_1': sum(x > 1 for x in r),
                                                                 'links_with_pairs': len(r)}
                lr.cable_matrices = retained
            out['cases'][str(e)] = case
    finally:
        lr.cable_matrices = retained
    out['scope'] = ('Conditional on the stated cross-section and the swept dielectric constant; endpoint lengths, '
                    'not an extremum proof; end regions keep the retained 5 mm equivalent; no measurement. The '
                    'conservative matrix adds the last extrapolation step again as a discretisation allowance.')
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    text = json.dumps(study(), indent=2) + '\n'
    if args.output:
        with args.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
