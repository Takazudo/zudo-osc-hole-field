"""ST-04 attempt a4, part 2: gate checks 3 and 4 on the record of the room study.

Reads design/stack/geometry/links/link-gate.json (ST-02 a8 part 2, read only) and computes, per link in use, the
coupling ratio of every directed pair at its actual order and cable, the rule per link, and the ground share per
branch. Imported by link_electrical.py, which writes design/stack/link-electrical/link-ratios.json and the README parts.
Paper bounds on ASSUMED drive, impedance and geometry terms; nothing is measured.
"""
import hashlib
import json
import math
from collections import Counter
from functools import lru_cache

import numpy as np

import ds62_table as d62
import harness_baseline as hb
import link_electrical as le

RECORD = 'design/stack/geometry/links/link-gate.json'
SIDE_BY_SIDE_OK = ('LOGIC', 'WIPER', 'STATIC')
ADAPTER_ORDER = d62.ADAPTER_ORDERS['ds79']['order']


# ---------------------------------------------------------------- the record

def load_record(root=le.ROOT):
    g = json.loads((root / RECORD).read_text())
    return [l for l in g['links'] if not l.get('gone')]


def projection(links):
    """What this calculator reads from the record, per link in use (pinned by hash in inputs.json)."""
    return [{'id': l['id'], 'joint': l['joint'], 'front_board': l['front_board'],
             'circuits': l['circuits'], 'cable': l['cable'], 'cable_length_mm': l['cable_length_mm'],
             'grounds': l['grounds'], 'unused': l['unused'], 'positions': l['positions']}
            for l in sorted(links, key=lambda l: l['id'])]


def projection_sha256(links):
    return hashlib.sha256(json.dumps(projection(links), sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def ordered(link):
    pos = sorted(link['positions'], key=lambda p: p['pos'])
    assert [p['pos'] for p in pos] == list(range(1, link['circuits'] + 1)), link['id']
    return pos


def window_of(pos, as_ground=()):
    """'S' for a signal, 'G' for a ground or an unused position (DS-77: tied to AGND on both boards)."""
    return ['S' if p['kind'] == 'signal' and p['pos'] not in as_ground else 'G' for p in pos]


def branch_of(link):
    """The AGND post branch, as link_electrical.ground_branch defines it; each adapter is a branch of its own."""
    if link['joint'] == 'O-K':
        return 'adapter ' + link['front_board']
    if link['joint'] == 'JL-P via K':
        return 'JL'
    return link['front_board']


# ---------------------------------------------------------------- cable matrices

@lru_cache(maxsize=None)
def cable_matrices(circuits, length_mm, pk, eps_r, cab_key):
    cab = json.loads(cab_key)
    p, w, t = cab['pitch_mm'] * 1e-3, cab['conductor_width_mm'] * 1e-3, cab['conductor_thickness_mm'] * 1e-3
    l = (length_mm + 2 * cab['end_mm']) * 1e-3
    centers = [i * p for i in range(circuits)]
    return le.capacitance_matrix(centers, w, eps_r) * l, le.lp_matrix(centers, l, w, t)


def matrices(inp, circuits, length_mm):
    pk = inp['ds62']['pitch']
    c = inp['cable'][pk]
    key = json.dumps({'pitch_mm': c['pitch_mm'], 'conductor_width_mm': c['conductor_width_mm'],
                      'conductor_thickness_mm': c['conductor_thickness_mm'],
                      'end_mm': inp['cable']['end_equivalent_mm']['value']}, sort_keys=True)
    return cable_matrices(circuits, float(length_mm), pk, inp['cable']['eps_eff']['value'][-1], key)


# ---------------------------------------------------------------- gate check 4: the ratio per link

def lies(window, a, v):
    lo, hi = sorted((a, v))
    if hi - lo == 1:
        return 'side by side'
    if hi - lo == 2 and window[lo + 1] == 'G':
        return 'across one ground'
    if all(c == 'G' for c in window[lo + 1:hi]):
        return f'across {hi - lo - 1} grounds'
    return 'farther, with a signal between'


def link_pairs(inp, link, base, without=()):
    """Every directed pair of signals of the link whose aggressor class has an aggressor term."""
    pos = ordered(link)
    window = window_of(pos, without)
    C, L = matrices(inp, link['circuits'], link['cable_length_mm'])
    sig = [i for i, c in enumerate(window) if c == 'S']
    rows, missing = [], set()
    for a in sig:
        ag = pos[a]['class']
        if ag not in ('LOGIC', 'ANALOGUE', 'PRECISION', 'WIPER', 'STATIC'):
            raise ValueError(f"{link['id']}: unknown signal class {ag!r}")
        if hb.aggressor_of(ag) is None:
            continue
        for v in sig:
            if v == a:
                continue
            vic = pos[v]['class']
            if vic not in ('LOGIC', 'ANALOGUE', 'PRECISION', 'WIPER', 'STATIC'):
                raise ValueError(f"{link['id']}: unknown signal class {vic!r}")
            key = f'{ag}>{vic}'
            if key not in base:
                missing.add(key)
                continue
            m, _ = le.effective_mutual(L, window, a, v)
            par = {'Cm_F': float(-C[a, v]), 'Cv_total_F': float(C[v, v]), 'M_eff_H': m}
            lv = d62.pair_level(par, ag, vic, inp)
            ref = base[key]['min_V']
            if not math.isfinite(lv) or not math.isfinite(ref) or ref <= 0:
                raise ValueError(f"{link['id']}: invalid pair evidence for {key}")
            rows.append({'pair': key, 'aggressor': pos[a]['net'], 'aggressor_pos': a + 1, 'victim': pos[v]['net'],
                         'victim_pos': v + 1, 'lies': lies(window, a, v), 'bound_V': lv,
                         'harness_min_V': ref, 'ratio': lv / ref,
                         'riders': {pos[i]['net']: pos[i]['rider_from'] for i in (a, v) if pos[i].get('rider_from')}})
    return rows, sorted(missing)


def link_row(inp, link, base):
    pos = ordered(link)
    rows, missing = link_pairs(inp, link, base)
    riders = [p for p in pos if p.get('rider_from')]
    out = {'id': link['id'], 'joint': link['joint'], 'branch': branch_of(link), 'circuits': link['circuits'],
           'cable': link['cable'], 'length_mm': link['cable_length_mm'],
           'signals_by_class': dict(sorted(Counter(p['class'] for p in pos if p['kind'] == 'signal').items())),
           'grounds': sum(p['kind'] == 'ground' for p in pos), 'unused': sum(p['kind'] == 'unused' for p in pos),
           'pairs_evaluated': len(rows), 'pairs_without_reference': missing,
           'host': bool(riders), 'riders': [{'net': p['net'], 'pos': p['pos'], 'from': p['rider_from']} for p in riders]}
    if rows:
        w = max(rows, key=lambda r: r['ratio'])
        out.update({'ratio': w['ratio'], 'largest_pair': w})
    else:
        out.update({'ratio': None, 'largest_pair': None})
    if riders:
        r2, _ = link_pairs(inp, link, base, without={p['pos'] for p in riders})
        out['ratio_without_riders'] = max((r['ratio'] for r in r2), default=None)
        cause = [r for r in rows if r['riders'] and r['ratio'] > 1.0]
        out['rider_pairs_above_1'] = cause
    if out['ratio'] is not None and out['ratio'] > 1.0:
        out['remedy_ds77'] = remedy_trial(inp, link, base)
    return out


# ---------------------------------------------------------------- the DS-77 remedy on paper

def with_grounds_in_runs(link, k):
    """The link with k of its unused positions moved as grounds into its logic runs (evenly), size unchanged.
    A paper trial only: the record is not changed and no allocation is made."""
    pos = [dict(p) for p in ordered(link)]
    unused = [i for i, p in enumerate(pos) if p['kind'] == 'unused']
    if k > len(unused):
        return None
    for i in sorted(unused[-k:], reverse=True) if k else []:
        del pos[i]
    runs, i = [], 0
    while i < len(pos):
        if pos[i].get('class') == 'LOGIC':
            j = i
            while j + 1 < len(pos) and pos[j + 1].get('class') == 'LOGIC':
                j += 1
            if j > i:
                runs.append((i, j))
            i = j + 1
        else:
            i += 1
    gaps = [(r, g) for r in runs for g in range(r[0] + 1, r[1] + 1)]
    if k > len(gaps):
        return None
    pick = sorted({gaps[round((m + 0.5) * len(gaps) / k - 0.5)][1] for m in range(k)}, reverse=True) if k else []
    if len(pick) < k:
        return None
    for g in pick:
        pos.insert(g, {'kind': 'ground'})
    for n, p in enumerate(pos, 1):
        p['pos'] = n
    return dict(link, positions=pos)


def remedy_trial(inp, link, base):
    """Fewest grounds moved into the logic runs (from unused positions) that bring the link to 1.0 or below."""
    unused = sum(p['kind'] == 'unused' for p in link['positions'])
    for k in range(1, unused + 1):
        t = with_grounds_in_runs(link, k)
        if t is None:
            break
        rows, _ = link_pairs(inp, t, base)
        r = max(x['ratio'] for x in rows)
        if r <= 1.0:
            return {'grounds_moved_in': k, 'unused_available': unused, 'ratio_after': r,
                    'order_after': ['S' if p['kind'] == 'signal' else 'G' for p in ordered(t)]}
    return {'grounds_moved_in': None, 'unused_available': unused, 'ratio_after': None, 'order_after': None}


# ---------------------------------------------------------------- the rule per link

def rule_check(link):
    pos = ordered(link)
    n = len(pos)
    br = []
    cls = [p['class'] if p['kind'] == 'signal' else None for p in pos]
    for i in range(n - 1):
        a, b = cls[i], cls[i + 1]
        if a and b and not (a == b and a in SIDE_BY_SIDE_OK):
            br.append(f'positions {i + 1} and {i + 2}: {a} beside {b} with no ground between')
    present = set(c for c in cls if c)
    if {'LOGIC', 'WIPER'} <= present:
        br.append('LOGIC and WIPER in one cable')
    if sum(p['kind'] in ('ground', 'unused') for p in pos) < 1:
        br.append('no ground or unused position')
    runs = []
    i = 0
    while i < n:
        if cls[i] == 'LOGIC':
            j = i
            while j + 1 < n and cls[j + 1] == 'LOGIC':
                j += 1
            runs.append((i + 1, j + 1))
            i = j + 1
        else:
            i += 1
    for s, e in runs:
        left = s - 2 >= 0 and pos[s - 2]['kind'] != 'signal'
        right = e < n and pos[e]['kind'] != 'signal'
        if e > s:
            if s == 1 or e == n:
                br.append(f'logic run at positions {s} to {e} takes an outer position (DS-77)')
            if not (left and right):
                br.append(f'logic run at positions {s} to {e} lacks a ground on each side (DS-77)')
        elif (s == 1 and not right) or (s == n and not left):
            br.append(f'single logic line at outer position {s} has no ground beside it (DS-77)')
    if link['joint'] == 'O-K':
        order = [('AGND' if p['kind'] != 'signal' else p['net'].split('/')[-1]) for p in pos]
        if order != ADAPTER_ORDER:
            br.append(f'adapter order {order} differs from DS-79')
    return {'id': link['id'], 'logic_runs': [list(r) for r in runs if r[1] > r[0]],
            'single_logic': [r[0] for r in runs if r[1] == r[0]], 'breaks': br}


# ---------------------------------------------------------------- gate check 3: the ground share

def ground_paths_at(inp, length_mm):
    pk = inp['ds62']['pitch']
    c = inp['conductor_resistance_mohm'][pk]
    scale = length_mm / 50.0  # the S-FLEX figures are for 50 mm of conductor
    rc = inp['contact'][pk]['resistance_max_ohm']['value']
    rmin = c['min'] * scale / 1000 + 2 * inp['contact']['resistance_min_ohm']['value']
    rmax = c['max'] * scale / 1000 + 2 * rc
    return rmin, rmax


def worst_contact_at(inp, branch, n, posts, length_mm, d):
    """worst_ground_contact of link_electrical with the conductor at length_mm in place of 50 mm."""
    pp = le.pp
    rmin, rmax = ground_paths_at(inp, length_mm)
    rj = pp.joint_ohm(d, pp.branch_gap(branch, d))
    g = (n - 1) / rmax + posts / rj
    alt = pp.v(d, 'return_plane_ohm') + (1 / g if g > 0 else float('inf'))
    i_total = pp.v(d, 'single_return_A')
    return i_total if alt == float('inf') else i_total * alt / (rmin + alt)


def worst_contact_mixed_at(inp, branch, lengths_mm, posts, d):
    """Bound each possible contact with its own path resistance and all other paths at their maxima."""
    if not lengths_mm:
        raise ValueError('ground branch has no contacts')
    paths = [ground_paths_at(inp, length) for length in lengths_mm]
    rj = le.pp.joint_ohm(d, le.pp.branch_gap(branch, d))
    plane = le.pp.v(d, 'return_plane_ohm')
    total = le.pp.v(d, 'single_return_A')
    shares = []
    for i, (rmin, _) in enumerate(paths):
        other_g = sum(1 / rmax for j, (_, rmax) in enumerate(paths) if i != j) + posts / rj
        alt = plane + (1 / other_g if other_g else float('inf'))
        shares.append(total if math.isinf(alt) else total * alt / (rmin + alt))
    return max(shares)


def ground_share(inp, links):
    d = le.pp.load()
    pk = inp['ds62']['pitch']
    ratings = [r['value'] for r in inp['contact'][pk]['ratings_A'] if r['value'] in (0.35, 0.5)]
    by = {}
    for l in links:
        by.setdefault(branch_of(l), []).append(l)
    rows = []
    a2 = max(worst_contact_at(inp, b, 1, inp['ground_current']['posts_cases']['one_post_open'], 50.0, d)
             for b in inp['ground_current']['branches'])
    for b in inp['ground_current']['branches']:
        ls = by[b]
        contacts = [sum(p['kind'] in ('ground', 'unused') for p in l['positions']) for l in ls]
        n = sum(contacts)
        lengths = [l['cable_length_mm'] for l in ls for p in l['positions'] if p['kind'] in ('ground', 'unused')]
        short = min(lengths)
        cases = {case: worst_contact_mixed_at(inp, b, lengths, posts, d)
                 for case, posts in inp['ground_current']['posts_cases'].items()}
        n1 = {case: worst_contact_mixed_at(inp, b, [short], posts, d)
              for case, posts in inp['ground_current']['posts_cases'].items()}
        rows.append({'branch': b, 'links': len(ls), 'contacts': n, 'grounds': sum(l['grounds'] for l in ls),
                     'unused': sum(l['unused'] for l in ls), 'fewest_on_a_link': min(contacts),
                     'shortest_cable_mm': short, 'worst_contact_A': cases, 'one_contact_A': n1,
                     'within': {str(r): all(x <= r for x in cases.values() if x is not None) for r in ratings}})
    return {'branches': rows, 'ratings_A': ratings, 'a2_one_post_open_one_ground_A': a2}


def adapter_return(inp, link):
    """The adapter's one ground contact: no designed return; the step's displacement current is a bound."""
    pos = ordered(link)
    C, _ = matrices(inp, link['circuits'], link['cable_length_mm'])
    s = inp['ds62']['selector_step']
    sel = next(i for i, p in enumerate(pos) if p['kind'] == 'signal' and p['net'].endswith('OCT_SELECTED'))
    g = [i for i, p in enumerate(pos) if p['kind'] != 'signal']
    c_ground = float(-sum(C[sel, j] for j in g))
    c_total = float(C[sel, sel])
    rate = s['swing_V'] / s['edge_s']
    return {'id': link['id'], 'branch': branch_of(link), 'ground_contacts': len(g), 'dc_A': 0.0,
            'step_into_ground_A': c_ground * rate, 'step_all_lines_A': c_total * rate, 'C_sel_to_ground_F': c_ground,
            'C_sel_total_F': c_total, 'step_duration_s': s['edge_s']}


# ---------------------------------------------------------------- outputs

def build(inp, base, root=le.ROOT):
    links = load_record(root)
    rows = [link_row(inp, l, base) for l in links]
    rules = [rule_check(l) for l in links]
    by_cable = {}
    for r in rows:
        if r['ratio'] is not None and (r['cable'] not in by_cable or r['ratio'] > by_cable[r['cable']]['ratio']):
            by_cable[r['cable']] = r
    return {'links': rows, 'rules': rules, 'by_cable': by_cable, 'projection_sha256': projection_sha256(links),
            'ground_share': ground_share(inp, links),
            'adapter_return': [adapter_return(inp, l) for l in links if l['joint'] == 'O-K'],
            'record_signals': sorted((p['site'], p['net'], p['class']) for l in links for p in l['positions'] if p['kind'] == 'signal'),
            'missing_references': sorted({k for r in rows for k in r['pairs_without_reference']})}


def verdict(b):
    above = [r for r in b['links'] if r['ratio'] is not None and r['ratio'] > 1.0]
    broken = [r for r in b['rules'] if r['breaks']]
    invalid = bool(b.get('missing_references')) or any(
        r.get('pairs_without_reference') or
        (r['ratio'] is not None and (not isinstance(r['ratio'], (int, float)) or not math.isfinite(r['ratio'])))
        for r in b['links'])
    return ('DONE' if not above and not broken and not invalid else 'NEEDS_DESIGN'), above, broken


def to_json(inp, b):
    v, above, broken = verdict(b)
    doc = {'schema_version': 1, 'task': 'osc-stack-20261114/ST-04 attempt a4, part 2 (gate checks 3 and 4; DS-77 to DS-79, DS-84, DS-110)',
           'status': inp['status'], 'written_by': 'scripts/stack/link_electrical/link_electrical.py', 'inputs': 'inputs.json',
           'record': RECORD, 'record_projection_sha256': b['projection_sha256'], 'verdict': v,
           'links_above_1': [r['id'] for r in above], 'rule_breaks': {r['id']: r['breaks'] for r in broken},
           'missing_references': b['missing_references'],
           'largest_ratio_per_cable': {k: {'id': r['id'], 'ratio': r['ratio']} for k, r in sorted(b['by_cable'].items())},
           'links': b['links'], 'rules': b['rules'], 'ground_share': b['ground_share'], 'adapter_return': b['adapter_return']}
    return json.dumps(le.rnd(doc), indent=1, ensure_ascii=False) + '\n'


def _pair_text(p):
    rid = '; '.join(f'{n} rides from {f}' for n, f in p['riders'].items())
    return (f'{p["pair"]}: {p["aggressor"]} (pos {p["aggressor_pos"]}) on {p["victim"]} (pos {p["victim_pos"]}), {p["lies"]}'
            + (f'; {rid}' if rid else ''))


def readme_lines(inp, b):
    out = []
    w = out.append
    v, above, broken = verdict(b)
    rows = b['links']
    rated = [r for r in rows if r['ratio'] is not None]
    worst = max(rated, key=lambda r: r['ratio'])
    w(f'## Gate check 4 on the record of the room study ({v}): the largest ratio of the {len(rows)} links is '
      f'{worst["ratio"]:.2f} on {worst["id"]}; {len(above)} links read above 1.0 (attempt a4, part 2, DS-77)')
    w('')
    w(f'Record: `{RECORD}` (ST-02 a8 part 2, DS-110), read only and pinned by the hash of a projection of what is read '
      f'(`inputs.json` → `link_record.projection_sha256`). Each link is solved at its actual order on its actual cable, every '
      'conductor in the 2-D solve, every ground and unused position at AGND (DS-77), every other signal held by its driver. '
      'Every directed pair whose aggressor class has an aggressor term is evaluated, not only neighbours, against the quietest '
      'present harness of the same pair of classes (the references of part 1). The ratio of a link is its largest pair.')
    w('')
    if b['missing_references']:
        w('Pairs of classes without a reference: ' + ', '.join(b['missing_references']) + '.')
    else:
        w('Every pair of classes that shares a link has a reference.')
    w('')
    w('| Cable | Links | Largest ratio | Link |')
    w('| --- | --- | --- | --- |')
    n_cab = Counter(r['cable'] for r in rows)
    for c, r in sorted(b['by_cable'].items()):
        w(f'| {c} ({r["circuits"]}, {r["length_mm"]:g} mm) | {n_cab[c]} | {r["ratio"]:.2f} | {r["id"]} |')
    w('')
    hi = sorted([r for r in rated if r['ratio'] > 0.8], key=lambda r: -r['ratio'])
    w('### Links above 0.8, with their largest pair' if hi else '### No link reads above 0.8')
    w('')
    if hi:
        w('| Link | Cable | Ratio | Largest pair | Host of riders (ratio without them) |')
        w('| --- | --- | --- | --- | --- |')
        for r in hi:
            h = f'yes ({r["ratio_without_riders"]:.2f})' if r['host'] else 'no'
            w(f'| {r["id"]} | {r["cable"]} | {r["ratio"]:.3f} | {_pair_text(r["largest_pair"])} | {h} |')
        w('')
    if above:
        w('### Links above 1.0 and the DS-77 remedy inside their unused positions')
        w('')
        w('The trial moves unused positions of the link as grounds into its logic runs, evenly, at the same size; the record '
          'is not changed and nothing is allocated. A link with no unused position has no remedy on record at its size.')
        w('')
        w('| Link | Circuits | Ratio | Largest pair | Rider | Unused | Grounds moved in | Ratio after |')
        w('| --- | --- | --- | --- | --- | --- | --- | --- |')
        for r in sorted(above, key=lambda r: -r['ratio']):
            x = r['remedy_ds77']
            rid = ', '.join(f'{n} from {f}' for n, f in r['largest_pair']['riders'].items()) or 'none'
            w(f'| {r["id"]} | {r["circuits"]} | {r["ratio"]:.3f} | {_pair_text(r["largest_pair"])} | {rid} | {x["unused_available"]} | '
              f'{x["grounds_moved_in"] if x["grounds_moved_in"] else "does not fit"} | '
              f'{"—" if x["ratio_after"] is None else format(x["ratio_after"], ".3f")} |')
        w('')
    hosts = [r for r in rows if r['host']]
    hosts_above = [r for r in hosts if r['ratio'] is not None and r['ratio'] > 1.0]
    w(f'### {len(hosts)} hosts carry {sum(len(r["riders"]) for r in hosts)} riders; '
      + (f'{len(hosts_above)} of them read above 1.0' if hosts_above else 'none reads above 1.0'))
    w('')
    w('| Host | Riders (from) | Ratio | Without riders |')
    w('| --- | --- | --- | --- |')
    for r in hosts:
        rid = ', '.join(f'{x["net"]} at {x["pos"]} ({x["from"]})' for x in r['riders'])
        rt = '—' if r['ratio'] is None else f'{r["ratio"]:.2f}'
        rw = '—' if r.get('ratio_without_riders') is None else f'{r["ratio_without_riders"]:.2f}'
        w(f'| {r["id"]} | {rid} | {rt} | {rw} |')
    w('')
    rl = b['rules']
    n_logic = sum(1 for r in rl if r['logic_runs'] or r['single_logic'])
    n_runs = sum(len(r['logic_runs']) for r in rl)
    w(f'## The rule per link {"holds on every link" if not broken else f"breaks on {len(broken)} links"}: '
      f'{n_logic} links carry logic, with {n_runs} runs of two or more (DS-62, DS-77, DS-79)')
    w('')
    w('Checked on the record: a ground or unused position between every two signals except LOGIC, WIPER or STATIC beside its '
      'own class; logic and wiper never in one cable; at least one ground or unused position; a logic run of two or more '
      'never on position 1 or the last and with a ground on each side; a single logic line at an outer position with a '
      'ground beside it; the adapter order OSC_OCT0 to OSC_OCT5, AGND, OCT_SELECTED.')
    w('')
    for r in broken:
        w(f'- {r["id"]}: ' + '; '.join(r['breaks']) + '.')
    if broken:
        w('')
    gs = b['ground_share']
    worst_open = max(x['worst_contact_A']['one_post_open'] for x in gs['branches'])
    n1_max = max(x['one_contact_A']['one_post_open'] for x in gs['branches'])
    inside = all(x['within']['0.35'] for x in gs['branches'])
    w(f'## Gate check 3 on the record: the worst link ground contact carries at most {worst_open:.3f} A with one post open, '
      f'{"inside" if inside else "above"} 0.35 A on every branch in all three post cases; one contact alone would carry {n1_max:.3f} A')
    w('')
    w('Per branch as the calculator defines it, with every ground and unused position of its links as a contact in parallel '
      '(DS-77), each possible candidate contact at its own cable length and minimum path resistance, every alternative '
      'at its own cable length and maximum path resistance, and no board term on the link path. The positions of the fields '
      'enter only through the number of contacts and the cable lengths.')
    w('')
    w('| Branch | Links | Contacts (grounds + unused) | Fewest on a link | Shortest cable, mm | Normal, A | One post open, A | All posts open, A | One contact, one post open, A |')
    w('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    for x in gs['branches']:
        c = x['worst_contact_A']
        w(f'| {x["branch"]} | {x["links"]} | {x["contacts"]} ({x["grounds"]} + {x["unused"]}) | {x["fewest_on_a_link"]} | '
          f'{x["shortest_cable_mm"]:g} | {c["normal"]:.4f} | {c["one_post_open"]:.4f} | {c["all_posts_open"]:.4f} | '
          f'{x["one_contact_A"]["one_post_open"]:.4f} |')
    w('')
    w(f'The bound of attempt a2 ({gs["a2_one_post_open_one_ground_A"]:.3f} A with one post open, one ground per link at 50 mm) '
      f'{"still covers" if n1_max <= gs["a2_one_post_open_one_ground_A"] + 1e-12 else "does not cover"} every link: '
      f'every link has at least {min(x["fewest_on_a_link"] for x in gs["branches"])} contact and no cable on JL, JR or P is '
      f'shorter than {min(x["shortest_cable_mm"] for x in gs["branches"]):g} mm.')
    w('')
    ar = b['adapter_return']
    w(f'### Each adapter is a branch of its own whose one ground carries no designed current; a selector step drives at most '
      f'{max(x["step_into_ground_A"] for x in ar) * 1000:.2g} mA into it for {ar[0]["step_duration_s"] * 1e9:g} ns')
    w('')
    w('The O boards carry no supply post and no active part on the adapter: the taps leave K, pass the selector and return on '
      'OCT_SELECTED to the 1 kΩ / 100 nF / 10 MΩ receiver on K, whose 10 MΩ returns on K. The only current in the adapter '
      'ground is the displacement current of OCT_SELECTED to the ground position during a step (ASSUMED 1 V in 5 ns).')
    w('')
    w('| Adapter | Ground contacts | DC, A | Step into the ground, mA | Step into all neighbours, mA |')
    w('| --- | --- | --- | --- | --- |')
    for x in ar:
        w(f'| {x["id"]} | {x["ground_contacts"]} | 0 | {x["step_into_ground_A"] * 1000:.2g} | {x["step_all_lines_A"] * 1000:.2g} |')
    w('')
    return out


__all__ = ['build', 'to_json', 'readme_lines', 'projection_sha256', 'load_record', 'np']
