"""ST-04 attempt a4, part 1: the class of the adapter lines and the DS-62 ratio table at the cable lengths in use.

Imported by link_electrical.py, which writes design/stack/link-electrical/ds62-table.json and the README sections.
Paper bounds on ASSUMED drive, impedance and geometry terms; nothing is measured.
"""
import copy
import json
import math

import numpy as np

import harness_baseline as hb
import link_electrical as le

ONE = 'across one ground'
SIDE = 'side by side'


# ---------------------------------------------------------------- the 511 signals

def adapter_rules(inp):
    return inp['classes_adapter']['rules'] + inp['classes']['rules']


def all_signals(inp, root=le.ROOT):
    """The 490 link signals unchanged, then the 21 adapter signals classified by classes_adapter."""
    base = le.classified_signals(inp, root)
    cand = json.loads((root / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    kinds = le.partition_kinds(root)
    rules = adapter_rules(inp)
    extra = []
    for pr in cand['pairs']:
        if 'K' not in pr['boards'] or le.is_link_pair(pr):
            continue
        front = [b for b in pr['boards'] if b != 'K'][0]
        for net in pr['pin_map']:
            if net not in le.NON_SIGNAL:
                extra.append({'pair': pr['id'], 'family': pr['family'], 'front_board': front, 'net': net,
                              'kind': ' / '.join(sorted(kinds.get(net, {'(not in partition harnesses)'}))),
                              'class': le.classify(net, kinds, rules)})
    return base + extra


# ---------------------------------------------------------------- flat-link windows

def window_parameters(inp, pk, length_mm, eps_r, window, a, v):
    cab = inp['cable'][pk]
    p, w, t = cab['pitch_mm'] * 1e-3, cab['conductor_width_mm'] * 1e-3, cab['conductor_thickness_mm'] * 1e-3
    l = (length_mm + 2 * inp['cable']['end_equivalent_mm']['value']) * 1e-3
    centers = [i * p for i in range(len(window))]
    C = le.capacitance_matrix(centers, w, eps_r) * l
    L = le.lp_matrix(centers, l, w, t)
    m_eff, _ = le.effective_mutual(L, window, a, v)
    return {'Cm_F': float(-C[a, v]), 'Cv_total_F': float(C[v, v]), 'M_eff_H': m_eff}


def link_pattern(circuits):
    return ['S' if i % 2 == 0 else 'G' for i in range(circuits)]


def clip(window, a, v, half):
    lo = max(0, min(a, v) - half)
    hi = min(len(window), max(a, v) + half + 1)
    return window[lo:hi], a - lo, v - lo


def placements(circuits, how, half):
    """Worst-case candidates on a DS-62 link of this size: the pair at the cable edge and in the middle."""
    pat = link_pattern(circuits)
    out = []
    if how == ONE:
        mid = (circuits // 2) // 2 * 2
        for a in sorted({0, max(0, min(mid, circuits - 3) // 2 * 2)}):
            if a + 2 < circuits:
                out.append(('edge' if a == 0 else 'middle',) + clip(pat, a, a + 2, half))
    else:
        edge = ['S', 'S'] + pat[1:circuits - 1]
        out.append(('edge',) + clip(edge[:circuits], 0, 1, half))
        j = max(1, (circuits // 2) // 2 * 2 - 1)
        mid = pat[:j] + ['G', 'S', 'S', 'G'] + pat[j + 3:]
        mid = mid[:circuits]
        if len(mid) >= 4:
            out.append(('middle',) + clip(mid, j + 1, j + 2, half))
    return out


def pairs_allowed(base):
    """Directed class pairs DS-62 lets share a cable, and how they lie: side by side for LOGIC/LOGIC and
    WIPER/WIPER (WIPER exerts nothing) and STATIC/STATIC (no aggressor); across one ground otherwise."""
    rows = []
    for key, b in sorted(base.items()):
        c = {b['aggressor_class'], b['victim']}
        if c == {'LOGIC', 'WIPER'}:
            continue
        rows.append((key, b['aggressor_class'], b['victim'], SIDE if b['aggressor_class'] == b['victim'] == 'LOGIC' else ONE))
    return rows


def ratio_table(inp, base):
    t = inp['ds62']
    pk = t['pitch']
    eps = inp['cable']['eps_eff']['value'][-1]
    half = t['window_half_width']['value']
    rows = []
    cache = {}
    for cab in t['cables']:
        for key, ag, vic, how in pairs_allowed(base):
            worst = None
            by_where = {}
            for where, window, a, v in placements(cab['circuits'], how, half):
                ck = (cab['length_mm'], tuple(window), a, v)
                if ck not in cache:
                    cache[ck] = window_parameters(inp, pk, cab['length_mm'], eps, window, a, v)
                lv = hb.level(cache[ck], hb.aggressor_of(ag), vic, inp)[0]
                by_where[where] = lv / base[key]['min_V']
                if worst is None or lv > worst['V']:
                    worst = {'where': where, 'V': lv}
            rows.append({'cable': cab['code'], 'circuits': cab['circuits'], 'length_mm': cab['length_mm'], 'pair': key,
                         'lies': how, 'where': worst['where'], 'flat_V': worst['V'], 'harness_min_V': base[key]['min_V'],
                         'ratio': worst['V'] / base[key]['min_V'], 'ratio_by_place': by_where})
    return rows


# ---------------------------------------------------------------- the adapter link

def adapter_link(inp, base_patterns):
    """Seven static lines: order, grounds and the selector-step bound on 8 and 14 circuits and on the present
    adapter harness. The step is OCT_SELECTED moving by one ladder step; the victim is a neighbouring tap."""
    t = inp['ds62']
    s = t['selector_step']
    pk = t['pitch']
    eps = inp['cable']['eps_eff']['value'][-1]
    nets = ['OCT_SELECTED'] + [f'OSC_OCT{i}' for i in range(6)]
    layouts = {
        8: {'order': nets + ['AGND'], 'window': ['S'] * 7 + ['G'], 'pair': (0, 1)},
        14: {'order': [x for n in nets for x in (n, 'AGND')], 'window': ['S', 'G'] * 7, 'pair': (0, 2)}}
    inp2 = copy.deepcopy(inp)
    inp2['aggressors']['SELECTOR'] = {'swing_V': s['swing_V'], 'slew_V_per_s': [s['swing_V'] / s['edge_s']], 'nominal_index': 0,
                                      'load_ohm': s['load_ohm'], 'load_F': s['load_F']}
    vv = inp['victims']['PRECISION']
    r = vv['source_ohm'][vv['nominal_index']]

    def bound(par):
        x = le.victim_peak(par, 'SELECTOR', 'PRECISION', inp2)
        i = s['swing_V'] / s['load_ohm'] + s['load_F'] * s['swing_V'] / s['edge_s']
        area = s['swing_V'] * r * par['Cm_F'] + abs(par['M_eff_H']) * i
        return {'peak_V': x['edge_V'], 'area_Vs': area, 'filtered_V': area / s['receiver_filter_s']}

    out = {}
    for n, lay in layouts.items():
        length = min(c['length_mm'] for c in t['cables'] if c['circuits'] == n)
        par = window_parameters(inp, pk, length, eps, lay['window'], *lay['pair'])
        out[f'flat_{n}'] = {'circuits': n, 'length_mm': length, 'order': lay['order'],
                            'grounds': lay['order'].count('AGND'), **bound(par)}
    harness = []
    for p in base_patterns:
        if not p['id'].startswith('K-O') or 'OCT_SELECTED' not in ''.join(p['nets']):
            continue
        cls = ['G' if c == 'G' else 'S' for c in p['classes']]
        par = hb.harness_pair_parameters(inp, cls, 0, 2, p['cut_length_mm'], eps)
        harness.append({'harness': p['id'], 'length_mm': p['cut_length_mm'], **bound(par)})
    q = min(harness, key=lambda x: x['peak_V'])
    out['harness_quietest'] = q
    for n in (8, 14):
        out[f'flat_{n}']['ratio_peak'] = out[f'flat_{n}']['peak_V'] / q['peak_V']
        out[f'flat_{n}']['ratio_filtered'] = out[f'flat_{n}']['filtered_V'] / q['filtered_V']
    return out


# ---------------------------------------------------------------- outputs

def build(inp):
    sig_all = all_signals(inp)
    pats = hb.harness_patterns(copy.deepcopy(inp) | {'classes': {'rules': adapter_rules(inp)}})
    base, counts = hb.baseline(inp, pats)
    old_base, _ = hb.baseline(inp)
    table = ratio_table(inp, base)
    by_len = {}
    for r in table:
        by_len.setdefault(r['length_mm'], []).append(r)
    largest = {L: max(rs, key=lambda r: r['ratio']) for L, rs in sorted(by_len.items())}
    return {'signals_all': sig_all, 'adapter_classes': sorted({s['class'] for s in sig_all[490:]}),
            'adapter_link': adapter_link(inp, pats), 'baseline': base,
            'baseline_change': {k: {'a3_min_V': old_base[k]['min_V'], 'a4_min_V': base[k]['min_V']}
                                for k in base if k in old_base and abs(old_base[k]['min_V'] - base[k]['min_V']) > 1e-15},
            'table': table, 'largest': largest, 'above_1': [r for r in table if r['ratio'] > 1.0]}


def to_json(inp, b):
    doc = {'schema_version': 1, 'task': 'osc-stack-20261114/ST-04 attempt a4, part 1 (DS-62, DS-64, DS-67, DS-70)',
           'status': inp['status'], 'written_by': 'scripts/stack/link_electrical/link_electrical.py', 'inputs': 'inputs.json',
           'adapter_classes': b['adapter_classes'], 'adapter_link': b['adapter_link'],
           'baseline_with_adapter_rule': {k: {'min_V': v['min_V'], 'triples': v['triples']} for k, v in b['baseline'].items()},
           'baseline_change': b['baseline_change'], 'table': b['table'],
           'largest_ratio_per_length': {str(k): v for k, v in b['largest'].items()}, 'above_1': b['above_1']}
    return json.dumps(le.rnd(doc), indent=1, ensure_ascii=False) + '\n'


def readme_lines(inp, b):
    out = []
    w = out.append
    ad = b['adapter_link']
    cls = b['adapter_classes']
    static = cls == ['STATIC']
    w(f'## The seven lines of each adapter are {"static" if static else "not settled as static"}: '
      f'{"8 circuits, seven signals side by side and one ground" if static else "14 circuits stay"} (attempt a4, part 1, DS-64)')
    w('')
    w('From the retained schematic specification (`inputs.json` → `ds62.adapter_evidence`, each with its file and object):')
    w('')
    for e in inp['ds62']['adapter_evidence']:
        w(f'- {e["statement"]}. Source: {e["source"]} ({e["status"]}).')
    w('')
    w(f'Class for DS-62: {", ".join(cls)} for all {len(b["signals_all"]) - 490} adapter signals (`inputs.json` → `classes_adapter`, beside '
      'the unchanged `classes.rules`). STATIC exerts nothing while the instrument plays, so two static lines need no ground between '
      'them; as victims they are PRECISION, because they set the pitch.')
    w('')
    w('| Outcome | Circuits | Order (circuit 1 first) | Grounds | Cable length, mm |')
    w('| --- | --- | --- | --- | --- |')
    for n in (8, 14):
        x = ad[f'flat_{n}']
        w(f'| {"static (this result)" if n == 8 else "analogue"} | {n} | {", ".join(x["order"])} | {x["grounds"]} | {x["length_mm"]:g} |')
    w('')
    q = ad['harness_quietest']
    s = inp['ds62']['selector_step']
    w(f'### Turning the selector by one step couples at most {ad["flat_8"]["peak_V"] * 1000:.3g} mV for nanoseconds into a neighbouring tap on 8 circuits; '
      f'behind the receiver filter that is {ad["flat_8"]["filtered_V"] * 1e6:.3g} µV')
    w('')
    w(f'A step of {s["swing_V"]:g} V on OCT_SELECTED with a {s["edge_s"] * 1e9:g} ns edge into the {s["load_ohm"]:g} Ω receiver '
      f'(terms in `inputs.json` → `ds62.selector_step`), victim the neighbouring tap at the PRECISION impedance. The filtered '
      f'figure is the spike\'s area over the receiver\'s {s["receiver_filter_s"] * 1e6:g} µs filter (V·R·Cm + M·ΔI, DERIVED), '
      'i.e. what reaches OCT_CV of an oscillator whose selector sits on the struck tap. It happens only during a hand turn, '
      'when the pitch changes by an octave anyway, so it does not enter the DS-62 criterion, which compares coupling '
      'while the instrument plays.')
    w('')
    w('| Path | Length, mm | Peak, mV | Filtered, µV | Ratio to the quietest present adapter harness (peak / filtered) |')
    w('| --- | --- | --- | --- | --- |')
    for n in (8, 14):
        x = ad[f'flat_{n}']
        w(f'| Flat {n} circuits | {x["length_mm"]:g} | {x["peak_V"] * 1000:.3g} | {x["filtered_V"] * 1e6:.3g} | {x["ratio_peak"]:.2f} / {x["ratio_filtered"]:.2f} |')
    w(f'| Present harness {q["harness"]} (one ground between) | {q["length_mm"]:g} | {q["peak_V"] * 1000:.3g} | {q["filtered_V"] * 1e6:.3g} | 1 |')
    w('')
    lg = b['largest']
    above = b['above_1']
    worst = max(lg.values(), key=lambda r: r['ratio'])
    w(f'## DS-62 at the lengths in use ({"DONE" if not above else "NEEDS_DESIGN"}): the largest ratio is {", ".join(f"{r["ratio"]:.2f} at {L:g} mm" for L, r in lg.items())}; '
      f'{"no pair is above 1.0" if not above else f"{len(above)} pair-and-cable rows are above 1.0"}')
    w('')
    w(f'0.5 mm pitch, ε_eff {inp["cable"]["eps_eff"]["value"][-1]:g} on both sides, each cable at its own length and size '
      '(`inputs.json` → `ds62.cables`), on the DS-62 link pattern (S G S G …, no outer ground); each bound is the worse of '
      'the pair at the cable edge and in the middle, with every conductor of the cable in the solve. '
      'Reference: the quietest present harness of the same '
      'directed pair, with the adapter lines STATIC, so the adapter harnesses no longer count as ANALOGUE/ANALOGUE.')
    w('')
    if b['baseline_change']:
        w('Reference changes against attempt a3: ' + '; '.join(
            f'{k} {v["a3_min_V"] * 1000:.3g} → {v["a4_min_V"] * 1000:.3g} mV' for k, v in b['baseline_change'].items()) + '.')
        w('')
    cabs = inp['ds62']['cables']
    w('| Aggressor > victim | Lies | ' + ' | '.join(f'{c["code"]} ({c["circuits"]}, {c["length_mm"]:g} mm)' for c in cabs) + ' |')
    w('| --- | --- | ' + '--- | ' * len(cabs))
    for key in sorted({r['pair'] for r in b['table']}):
        rs = {r['cable']: r for r in b['table'] if r['pair'] == key}
        lies = next(iter(rs.values()))['lies']
        w(f'| {key} | {lies} | ' + ' | '.join(f'{rs[c["code"]]["ratio"]:.2f} ({20 * math.log10(rs[c["code"]]["ratio"]):+.1f} dB)' for c in cabs) + ' |')
    w('')
    if above:
        w('Rows above 1.0, with the ratio at the cable edge and in the middle of the link:')
        w('')
        w('| Cable | Length, mm | Aggressor > victim | Lies | Edge | Middle |')
        w('| --- | --- | --- | --- | --- | --- |')
        for r in above:
            w(f'| {r["cable"]} | {r["length_mm"]:g} | {r["pair"]} | {r["lies"]} | {r["ratio_by_place"].get("edge", float("nan")):.2f} | '
              f'{r["ratio_by_place"].get("middle", float("nan")):.2f} |')
        w('')
    w(f'Worst row: {worst["pair"]} on {worst["cable"]} at {worst["length_mm"]:g} mm, {worst["where"]}, '
      f'{worst["flat_V"] * 1000:.3g} mV against {worst["harness_min_V"] * 1000:.3g} mV. WIPER>WIPER and STATIC pairs exert '
      'nothing and are left out; LOGIC/WIPER may not share a cable (DS-62). Every figure is a paper bound; the harness was '
      'never measured either.')
    w('')
    return out


def full_vs_clipped(inp, circuits=14, half=None):
    """Test helper: a window clipped to `half` positions (default: the configured width) against the full pattern."""
    pat = link_pattern(circuits)
    a = (circuits // 2) // 2 * 2
    full = window_parameters(inp, 'pitch_0_5', 50, 3.2, pat, a, a + 2)
    w, ca, cv = clip(pat, a, a + 2, inp['ds62']['window_half_width']['value'] if half is None else half)
    part = window_parameters(inp, 'pitch_0_5', 50, 3.2, w, ca, cv)
    return full, part


__all__ = ['build', 'to_json', 'readme_lines', 'all_signals', 'np']
