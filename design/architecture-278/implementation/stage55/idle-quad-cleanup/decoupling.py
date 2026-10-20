"""Stage55 bypass/decoupling review of the Stage54 idle-quad removal (source-level only).

Facts computed from the current master specification, partition assignment and
locked floorplan. Writes decoupling.json (or checks it with --check). Not a layout,
PDN-impedance, regulator-stability or hardware result.
"""
from pathlib import Path
from collections import defaultdict
import importlib.util, json, math, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from scripts.schgen.core import designator

RAILS = ('+12V', '-12V')
NOMINAL_F = {'100 nF': 100e-9, '1e-07 F': 100e-9, '1 uF': 1e-6}


def load_stage54():
    path = ROOT/'design/architecture-278/implementation/stage54/power-cleanup/proposal.py'
    spec = importlib.util.spec_from_file_location('stage54_proposal', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def require(ok, msg):
    if not ok: raise ValueError(msg)


def inventory(families, instances, assignment):
    fam = {f.name: f for f in families}
    caps, ics = [], []
    for inst in instances:
        f = fam[inst.family]
        stems = defaultdict(list)
        for p in f.parts:
            if p.dnp or not p.on_board:
                continue
            ref = designator(p, inst)
            if p.prefix == 'C' and set(p.pins.values()) & set(RAILS):
                require(p.value in NOMINAL_F, f'unclassified capacitor value {ref} {p.value}')
                caps.append({'ref': ref, 'board': assignment.get(ref), 'rail': sorted(set(p.pins.values()) & set(RAILS)),
                             'value': p.value, 'farad': NOMINAL_F[p.value], 'mpn': p.attributes.get('MPN'),
                             'decouples': (inst.name, p.attributes['Decouples']) if p.attributes.get('Decouples') else None})
            if p.prefix == 'U':
                stems[(p.key.rsplit('.', 1)[0], ref)].append(p)
        for (stem, ref), units in stems.items():
            rails = sorted({n for u in units for n in u.pins.values()} & set(RAILS))
            if rails:
                ics.append({'ref': ref, 'stem': (inst.name, stem), 'board': assignment.get(ref), 'rails': rails,
                            'mpn': units[0].attributes.get('MPN') or units[0].symbol.split(':')[-1]})
    return caps, ics


def totals(caps):
    out = {}
    for rail in RAILS:
        rows = [c for c in caps if rail in c['rail']]
        boards = defaultdict(lambda: [0, 0.0])
        for c in rows:
            boards[c['board']][0] += 1; boards[c['board']][1] += c['farad']
        out[rail] = {'count': len(rows), 'nominal_uF': round(sum(c['farad'] for c in rows)*1e6, 3),
                     'by_board': {b: {'count': n, 'nominal_uF': round(f*1e6, 3)} for b, (n, f) in sorted(boards.items())}}
    return out


def ownership(caps, ics):
    owned = defaultdict(set)
    for c in caps:
        if c['decouples']:
            for r in c['rail']:
                owned[c['decouples']].add(r)
    missing = [i['ref'] for i in ics if not set(i['rails']) <= owned.get(i['stem'], set())]
    return sorted(missing)


def run(check=False):
    s54 = load_stage54()
    families, instances = s54.specification()
    new_families, proposal = s54.prepare(families, instances)
    partition = json.loads((ROOT/'design/partition/partition.json').read_text())
    assignment = {x['ref']: x['board'] for x in partition['assignment']['components']}
    floor = {x['ref']: x for x in json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())['placements']}
    removed = set(proposal['removed_refs'])
    caps_b, ics_b = inventory(families, instances, assignment)
    caps_a, ics_a = inventory(new_families, instances, assignment)
    require({c['ref'] for c in caps_b} - {c['ref'] for c in caps_a} == {r for r in removed if r.startswith('C')}, 'capacitor removal set')
    require({i['ref'] for i in ics_b} - {i['ref'] for i in ics_a} == {r for r in removed if r.startswith('U')}, 'IC removal set')
    require({c['ref'] for c in caps_a} <= {c['ref'] for c in caps_b}, 'no capacitor added')
    missing_before, missing_after = ownership(caps_b, ics_b), ownership(caps_a, ics_a)
    require(missing_after == [r for r in missing_before if r not in removed], 'surviving IC lost owned bypass')
    # Every removed cap was owned by a removed IC, so no survivor names it in Decouples.
    removed_caps = [c for c in caps_b if c['ref'] in removed]
    removed_stems = {i['stem'] for i in ics_b if i['ref'] in removed}
    require(all(c['decouples'] in removed_stems for c in removed_caps), 'removed cap owned by surviving IC')
    # Physical neighbourhood from the locked floorplan: nearest surviving same-rail cap
    # and nearest surviving powered IC to each removed IC footprint origin.
    surviving_caps = [c for c in caps_a if c['board'] == 'K' and c['ref'] in floor]
    surviving_ics = [i for i in ics_a if i['board'] == 'K' and i['ref'] in floor]
    def dist(a, b): return math.hypot(floor[a]['x_mm']-floor[b]['x_mm'], floor[a]['y_mm']-floor[b]['y_mm'])
    neighbourhood = []
    for ic in sorted((i for i in ics_b if i['ref'] in removed), key=lambda i: i['ref']):
        row = {'ref': ic['ref'], 'mpn': ic['mpn'], 'side': floor[ic['ref']]['side'],
               'origin_mm': [floor[ic['ref']]['x_mm'], floor[ic['ref']]['y_mm']]}
        for rail in RAILS:
            same = sorted(((dist(ic['ref'], c['ref']), c['ref']) for c in surviving_caps if rail in c['rail']))
            row[f'nearest_surviving_{rail}_caps'] = [[r, round(d, 3), floor[r]['side']] for d, r in same[:3]]
            row[f'surviving_{rail}_caps_within_10mm'] = sum(1 for d, _ in same if d <= 10.0)
        nearest = sorted((dist(ic['ref'], i['ref']), i['ref']) for i in surviving_ics)
        row['nearest_surviving_powered_ics'] = [[r, round(d, 3), floor[r]['side']] for d, r in nearest[:3]]
        neighbourhood.append(row)
    # Survivors whose nearest same-rail capacitor (by floorplan origin) was a removed one,
    # closer than their own owned bypass: they lose a nearby HF bypass despite ownership.
    baseline_caps = [c for c in caps_b if c['board'] == 'K' and c['ref'] in floor]
    survivors_losing_nearest = []
    for ic in sorted(surviving_ics, key=lambda i: i['ref']):
        for rail in ic['rails']:
            same = sorted((dist(ic['ref'], c['ref']), c['ref']) for c in baseline_caps if rail in c['rail'])
            own = sorted((dist(ic['ref'], c['ref']), c['ref']) for c in baseline_caps if rail in c['rail'] and c['decouples'] == ic['stem'])
            if same and same[0][1] in removed:
                survivors_losing_nearest.append({'ref': ic['ref'], 'mpn': ic['mpn'], 'rail': rail,
                    'removed_cap': same[0][1], 'removed_cap_mm': round(same[0][0], 3),
                    'own_bypass': own[0][1] if own else None, 'own_bypass_mm': round(own[0][0], 3) if own else None})
    before, after = totals(caps_b), totals(caps_a)
    result = {
        'status': 'SOURCE-LEVEL decoupling review of an UNADOPTED candidate; no PDN, layout or hardware result',
        'removed_bypasses': [{k: c[k] for k in ('ref', 'rail', 'value', 'mpn')} | {'owner': c['decouples'][1], 'owner_instance': c['decouples'][0]} for c in sorted(removed_caps, key=lambda c: c['ref'])],
        'every_removed_bypass_owned_by_a_removed_ic': True,
        'surviving_powered_ics_on_rails': {'before': len(ics_b), 'after': len(ics_a)},
        'surviving_ics_without_complete_owned_bypass': {'before': missing_before, 'after': missing_after},
        'rail_nominal_capacitance_before': before,
        'rail_nominal_capacitance_after': after,
        'rail_nominal_reduction_uF': {r: round(before[r]['nominal_uF']-after[r]['nominal_uF'], 3) for r in RAILS},
        'rail_nominal_reduction_fraction': {r: round(1-after[r]['nominal_uF']/before[r]['nominal_uF'], 5) for r in RAILS},
        'removed_ic_neighbourhood_floorplan': neighbourhood,
        'survivors_whose_nearest_rail_cap_is_removed': survivors_losing_nearest,
        'survivors_needing_pdn_layout_review': sorted({r['ref'] for r in survivors_losing_nearest}),
        'limits': ('Nominal values only: no DC-bias, tolerance, temperature or ESL derating. Ownership is the '
                   'project Decouples attribute, not a PDN impedance model. Distances use footprint origins from '
                   'the locked floorplan, not copper path length. Downstream ceramic capacitance seen by the '
                   'zudo-pd regulators changes; regulator/cable stability is a supply-side question, not assessed.'),
    }
    path = HERE/'decoupling.json'
    body = json.dumps(result, indent=2, sort_keys=True)+'\n'
    if check:
        require(path.read_text() == body, 'decoupling replay drift')
    else:
        path.write_text(body)
    print('PASS decoupling review: reduction', result['rail_nominal_reduction_uF'], 'of',
          {r: before[r]['nominal_uF'] for r in RAILS}, 'uF; surviving ownership unchanged')
    return result


if __name__ == '__main__':
    run('--check' in sys.argv)
