"""Source contract for Molex 150200075 from PS-15020-001 Rev F plus SD-15020-001 Rev F.

Binds the family specification to the exact candidate, records conflicts without choosing the
favourable side, and runs only the two model checks whose consumed inputs the specification
changes: the ground-share minimum-resistance input and the capacitance basis of the link ratio.
"""
import argparse
import copy
from decimal import Decimal as D
import hashlib
import json
import os
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
LE = ROOT / 'scripts/stack/link_electrical'
STORE_ENV = 'CIRCUIT_DEV_RESOURCES'
LENGTHS_MM = (49.0, 51.0, 53.0)
# IEC 60028 annealed-copper reference at 20 C (1/58 ohm*mm^2/m); a standard value, not a Molex statement.
RHO_IACS_20 = 1.7241e-8


def load_evidence():
    return json.loads((HERE / 'evidence.json').read_text())


def pm(pair):
    n, t = D(pair[0]), D(pair[1])
    return [n - t, n + t]


def check_sources(ev, store=None):
    """Hash the retained bytes when the private store is available; never silently skip."""
    store = store or os.environ.get(STORE_ENV)
    rows = {}
    for key in ('PS', 'SD'):
        src = ev['sources'][key]
        if not store:
            rows[key] = 'NOT_RUN: set ' + STORE_ENV + ' to a circuit-dev-resources checkout'
            continue
        path = Path(store) / src['store_path']
        if not path.is_file() or path.is_symlink():
            raise ValueError('retained source missing: ' + src['store_path'])
        data = path.read_bytes()
        if len(data) != src['bytes'] or hashlib.sha256(data).hexdigest() != src['sha256']:
            raise ValueError('retained source drift: ' + src['store_path'])
        rows[key] = 'VERIFIED'
    return rows


def dimensional(ev):
    f, c = ev['facts'], ev['conflicts']
    ps, sd = pm(c['reinforcement_length_mm']['PS']), pm(c['reinforcement_length_mm']['SD'])
    if not (sd[0] <= ps[0] and ps[1] <= sd[1]):
        raise ValueError('reinforcement conflict changed shape; review precedence again')
    return {
        'binding': 'PS-15020-001 Rev F covers 15020-XXXX and points to drawing 150200001; SD-15020-001 Rev F '
                   '(material 150200001) sheet 1 binds 150200075 = N8 / 51+/-2 mm / type A. Both apply.',
        'precedence': 'Neither document states precedence. The drawing (approved 2026-02-16) is newer than the '
                      'specification (2023-12-06), but recency is not a stated precedence rule.',
        'reinforcement_length_mm': {'PS': [str(x) for x in ps], 'SD': [str(x) for x in sd],
                                    'governing_envelope': [str(sd[0]), str(sd[1])],
                                    'disposition': 'UNRESOLVED_CONFLICT; checks use the SD envelope that contains the PS one. '
                                                   'The narrower PS interval relaxes nothing. FH12 4.5 mm minimum support '
                                                   'recommendation remains 0.5 mm short at the 4.0 mm envelope end.'},
        'reinforcement_thickness_nominal_mm': {'PS': f['reinforcement_nominal_mm']['PS'],
            'disposition': 'PS 0.15 mm nominal, no tolerance, below the FH12 0.188 mm recommendation. The SD 0.155 mm '
                           'figure is on sheet 2, which applies to odd circuit counts only (sheet 1 note 2).'},
        'sd_sheet_scope': ev['sources']['SD']['scope_note'],
        'agreeing_intervals_mm': {k: [str(x) for x in pm(f[k])] for k in
                                  ('total_width_8p_mm', 'span_8p_mm', 'conductor_width_mm', 'strip_length_mm', 'end_thickness_mm', 'length_mm')},
        'unchanged_from_prior_audit': 'width +/-0.10 vs FH12 +/-0.07, exposure 3.2 mm vs 3.5 mm min, datum mapping NOT_ASSESSED',
    }


def current(ev, inputs):
    f = ev['facts']
    used = sorted(r['value'] for r in inputs['contact']['pitch_0_5']['ratings_A'])
    derated = [r['value'] for r in inputs['contact']['pitch_0_5']['ratings_A'] if r['status'] == 'DERIVED']
    binding = min(derated + [float(f['current_listing_per_contact_A'])])
    return {
        'listing_per_contact_A': f['current_listing_per_contact_A'],
        'ps_test': f['current_test'],
        'disposition': 'Two Molex statements differ: PS item 6 rates 0.55 A per conductor with all conductors loaded '
                       '(<=40 C rise at 23 C); the listing gives 0.5 A per contact. The lower one is used. The FH12 '
                       'all-contacts derating is lower than both and governs the mated link.',
        'model_ratings_A': used, 'binding_A': binding,
        'allocation_effect': 'NONE: ground-share verdicts are evaluated at 0.35 and 0.5 A; neither exceeds the cable listing.',
    }


def _kernel():
    if str(LE) not in sys.path:
        sys.path.insert(0, str(LE))
    import link_ratios as lr
    import ds62_table
    return lr, ds62_table


def ground_share(ev, inputs):
    lr, _ = _kernel()
    d = lr.le.pp.load()
    f = ev['facts']

    l_min = float(pm(f['length_mm'])[0])

    def worst(cmin):
        i2 = copy.deepcopy(inputs)
        i2['conductor_resistance_mohm']['pitch_0_5']['min'] = cmin
        return max(lr.worst_contact_at(i2, b, 1, i2['ground_current']['posts_cases'][case], l_min, d)
                   for b in i2['ground_current']['branches'] for case in ('normal', 'one_post_open'))

    def threshold(limit):
        lo, hi = 0.0, inputs['conductor_resistance_mohm']['pitch_0_5']['min']
        if worst(hi) > limit:
            raise ValueError('retained legacy share already exceeds ' + str(limit))
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if worst(mid) > limit else (lo, mid)
        return hi

    rmax_per_50 = float(D(f['conductor_resistance_max_ohm_per_km'])) * 50.0 / 1000.0
    w_max = float(pm(f['conductor_width_mm'])[1]) * 1e-3
    t_nom = float(D(f['copper_nominal_mm'])) * 1e-3
    t_env = float(pm(f['end_thickness_mm'])[1]) * 1e-3
    cond_nominal = RHO_IACS_20 * 0.050 / (w_max * t_nom) * 1000.0
    cond_envelope = RHO_IACS_20 * 0.050 / (w_max * t_env) * 1000.0
    th = {str(x): round(threshold(x), 3) for x in (0.35, 0.5)}
    return {
        'legacy_min_mohm_per_50mm': inputs['conductor_resistance_mohm']['pitch_0_5']['min'],
        'legacy_applicable_to_150200075': False,
        'why': 'Legacy 65.3 mohm/50 mm is an LX 0.035 mm-copper minimum. Every conforming 150200075 conductor is below it '
                '(source maximum 730 ohm/km = 36.5 mohm/50 mm), so the retained share PASS does not transfer.',
        'source_max_mohm_per_50mm': round(rmax_per_50, 3),
        'source_min': None,
        'required_min_mohm_per_50mm': th,
        'conditional_estimates_20C_mohm_per_50mm': {
            'nominal_copper_0.10_width_max': round(cond_nominal, 3),
            'full_end_stack_thickness_0.35_not_a_copper_bound': round(cond_envelope, 3),
            'basis': 'annealed-copper reference resistivity at 20 C, no temperature correction (colder is lower); '
                     'thickness is nominal or the whole end stack, not a copper tolerance'},
        'evaluated_at_length_mm': l_min,
        'worst_one_ground_contact_A': {
            'at_nominal_estimate': round(worst(cond_nominal), 4),
            'at_end_thickness_envelope': round(worst(cond_envelope), 4)},
        'status': 'OPEN',
        'needs': 'A source minimum for conductor resistance (or copper thickness/section tolerance) at the coldest '
                 'applicable temperature, at least the required minimum above. The end-thickness envelope alone does '
                 'not close it.',
    }


def capacitance(ev, inputs, run_ratios=True):
    import numpy as np
    lr, ds62_table = _kernel()
    le = lr.le
    f = ev['facts']
    eps_hi = inputs['cable']['eps_eff']['value'][-1]
    p = float(D(f['pitch_mm'][0])) * 1e-3
    w = float(D(f['conductor_width_mm'][0])) * 1e-3
    C = np.array(le.capacitance_matrix([i * p for i in range(8)], w, eps_hi)) * 1e12
    P = np.linalg.pinv(C)
    q = np.zeros(8)
    q[3], q[4] = 1.0, -1.0
    v = P @ q
    readings = {
        'adjacent_pair_others_floating': round(float(1.0 / (v[3] - v[4])), 2),
        'adjacent_pair_others_grounded': round(float((C[3, 3] + C[4, 4] - 2 * C[3, 4]) / 4), 2),
        'one_interior_conductor_vs_all_others': round(float(C[3, 3]), 2),
        'one_edge_conductor_vs_all_others': round(float(C[0, 0]), 2),
    }
    spec = float(D(f['capacitance']['value_pF_per_m']))
    out = {'source': f['capacitance'], 'model_eps_upper': eps_hi,
           'model_pF_per_m_at_eps_upper': readings,
           'reading_contradicts_model_upper_bound': {k: v < spec for k, v in readings.items()},
           'method_defined_by_source': False}
    if run_ratios:
        scale = spec / readings['adjacent_pair_others_floating']
        eps_cal = eps_hi * scale
        orig = copy.deepcopy(inputs)
        base = ds62_table.build(orig)['baseline']
        cand = set(json.loads((ROOT / 'scripts/checks/mc02_molex_candidate/evidence.json').read_text())['candidate_link_ids'])
        links = [l for l in lr.load_record() if l['id'] in cand]
        if len(links) != 28:
            raise ValueError('candidate link scope changed')
        i2 = copy.deepcopy(orig)
        i2['cable']['eps_eff']['value'][-1] = eps_cal
        i2['cable']['pitch_0_5']['conductor_thickness_mm'] = float(D(f['copper_nominal_mm']))
        sweep = {}
        for length in LENGTHS_MM:
            rows = [lr.link_row(i2, dict(l, cable_length_mm=length), base) for l in links]
            above = sorted((r['id'], round(r['ratio'], 4)) for r in rows if r['ratio'] is not None and r['ratio'] > 1.0)
            remedies = [r['id'] for r in rows if (r.get('remedy_ds77') or {}).get('ratio_after') is not None]
            sweep[str(length)] = {'max_ratio': round(max(r['ratio'] for r in rows if r['ratio'] is not None), 4),
                                  'links_above_1': len(above), 'above': above, 'ds77_remedy_found': remedies}
        out['pair_floating_calibration'] = {
            'eps_scale': round(scale, 4), 'eps_calibrated': round(eps_cal, 4), 'copper_mm': f['copper_nominal_mm'],
            'baseline': 'harness references from the unchanged retained inputs (eps 3.2)', 'by_length_mm': sweep,
            'cause': 'Uniform eps scaling multiplies every link level; with the harness rebuilt at the same eps no link '
                     'exceeds 1.0. The exceedance is only the cable-versus-harness eps asymmetry.',
            'superseded_by': 'finite-thickness study (physical cross-section); this proxy is retained as a rejected method',
            'scope': 'Conditional sensitivity on the literal adjacent-pair reading; endpoint samples, not an extremum proof.'}
    ft = finite_thickness(ev)
    out['finite_thickness'] = ft
    rows = {e: {k: v for k, v in c.items() if k.startswith(('best_', 'conservative_'))} for e, c in ft['cases'].items()}
    failing = sorted({(e, k) for e, c in rows.items() for k, v in c.items() if v['links_above_1']})
    out['finite_thickness_summary'] = {
        'equal_eps_all_pass_to_eps': max(float(e) for e, c in rows.items()
                                         if all(not v['links_above_1'] for k, v in c.items() if 'same_eps' in k)),
        'retained_harness_failing_cases': [f'{e}:{k}' for e, k in failing],
        'eps_reproducing_62pF_per_m': {'pair_floating': 'about 4.4', 'pair_grounded': 'about 3.3',
                                       'interior_vs_all': 'below 2.5'},
        'retained_harness_crossing_eps': 'about 3.8 (conservative matrix, 53 mm)'}
    out['z_c_consistency'] = ('130 ohm and 62 pF/m together imply eps_eff about 5.8 for one balanced configuration, '
                              'implausible for polyester; the two figures likely include fixture/end effects or differ in setup.')
    out['status'] = 'CONDITIONAL_PASS' if not failing else 'OPEN'
    out['disposition'] = ('Converged finite-thickness cross-section, open boundary, conservative discretisation allowance: '
                          'with cable and harness at the same eps every evaluated link stays below 1.0 up to eps 4.7. '
                          'With the harness held at 3.2, one link exceeds 1.0 once the cable eps passes about 3.8. '
                          'The 62 pF/m figure implies eps about 3.3 under the adjacent-pair-grounded reading (pass) and '
                          'about 4.4 under the adjacent-pair-floating reading (one link fails). Its fixture is not stated, '
                          'so coupling stays OPEN, narrowed to the cable dielectric constant relative to the harness.')
    return out


def finite_thickness(ev):
    spec = ev['finite_thickness_study']
    for rel, sha in spec['inputs_sha256'].items():
        if hashlib.sha256((ROOT / rel).read_bytes()).hexdigest() != sha:
            raise ValueError('finite-thickness input drift: ' + rel + '; rerun finite_thickness_study.py and review')
    path = ROOT / spec['result']
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError('finite-thickness result drift; rerun finite_thickness_study.py and review')
    return json.loads(data)


def contract(ev, inputs, run_ratios=True, store=None):
    if ev['candidate']['mpn'] != '150200075' or ev['sources']['PS']['revision'] != 'F' or ev['sources']['SD']['revision'] != 'F':
        raise ValueError('candidate or source revision changed')
    if ev['facts']['conductor_resistance_min'] is not None:
        raise ValueError('no source minimum resistance exists; do not invent one')
    out = {'status': 'SOURCE_CONTRACT_WITH_OPEN_ITEMS',
           'sources': check_sources(ev, store),
           'dimensional': dimensional(ev),
           'current': current(ev, inputs),
           'ground_share': ground_share(ev, inputs),
           'capacitance': capacitance(ev, inputs, run_ratios),
           'other_facts_for_task_c': {k: ev['facts'][k] for k in ('folding', 'flex_life', 'operating_C', 'insulated_thickness_mm')},
           'remaining_unknowns': ['minimum conductor resistance / copper thickness tolerance',
                                  'capacitance fixture definition (or a measured value); dielectric constant',
                                  'end-region coupling (retained 5 mm equivalent)',
                                  'reinforcement precedence (6+/-1 vs 6+/-2)', 'reinforcement thickness tolerance',
                                  'positional/datum conformity to FH12', 'assembled contact resistance'],
           'product_qualified': False, 'bom_change': None,
           'holds': ['DRC', 'zone fill', 'formal adoption', 'manufacturing']}
    if out['product_qualified'] is not False or out['bom_change'] is not None:
        raise ValueError('qualification or BOM change forbidden')
    return out


def model_hashes(ev):
    return {k: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for k, p in ev['model_bindings'].items()}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    ap.add_argument('--store', help='circuit-dev-resources checkout (or set ' + STORE_ENV + ')')
    args = ap.parse_args()
    ev = load_evidence()
    result = contract(ev, json.loads((ROOT / ev['model_bindings']['inputs']).read_text()), store=args.store)
    result['model_sha256'] = model_hashes(ev)
    text = json.dumps(result, indent=2) + '\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(text)
    else:
        print(text, end='')
