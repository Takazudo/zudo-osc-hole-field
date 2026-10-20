"""Stage56 decoupling re-check with the six retained bypasses (source level only).

Same metrics as Stage55 `decoupling.py`: rail totals, owned-bypass completeness and the
surviving osc-core ICs whose nearest same-rail capacitor (floorplan origins) is removed.
Writes decoupling.json, or checks it with --check.
"""
from pathlib import Path
import importlib.util, json, math, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
S55 = ROOT/'design/architecture-278/implementation/stage55/idle-quad-cleanup'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


d55 = load('stage55_decoupling', S55/'decoupling.py')
c56 = load('stage56_candidate', HERE/'candidate.py')
require = d55.require


def run(check=False):
    s54 = d55.load_stage54()
    families, instances = s54.specification()
    new_families, proposal = s54.prepare(families, instances)
    families56, rows = c56.retained_families(families, instances, new_families)
    kept = {r['ref'] for r in rows}
    removed = set(proposal['removed_refs']) - kept
    partition = json.loads((ROOT/'design/partition/partition.json').read_text())
    assignment = {x['ref']: x['board'] for x in partition['assignment']['components']}
    floor = {x['ref']: x for x in json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())['placements']}
    caps_b, ics_b = d55.inventory(families, instances, assignment)
    caps_a, ics_a = d55.inventory(families56, instances, assignment)
    require({c['ref'] for c in caps_b} - {c['ref'] for c in caps_a} == {r for r in removed if r.startswith('C')}, 'cap removal set')
    missing_b, missing_a = d55.ownership(caps_b, ics_b), d55.ownership(caps_a, ics_a)
    require(missing_a == [r for r in missing_b if r not in removed], 'surviving IC lost owned bypass')
    def dist(a, b): return math.hypot(floor[a]['x_mm']-floor[b]['x_mm'], floor[a]['y_mm']-floor[b]['y_mm'])
    base_caps = [c for c in caps_b if c['board'] == 'K' and c['ref'] in floor]
    surviving = [i for i in ics_a if i['board'] == 'K' and i['ref'] in floor]
    losing = []
    for ic in sorted(surviving, key=lambda i: i['ref']):
        for rail in ic['rails']:
            same = sorted((dist(ic['ref'], c['ref']), c['ref']) for c in base_caps if rail in c['rail'])
            if same and same[0][1] in removed:
                losing.append({'ref': ic['ref'], 'rail': rail, 'removed_cap': same[0][1], 'removed_cap_mm': round(same[0][0], 3)})
    retained = []
    for r in rows:
        owner = next(i['ref'] for i in surviving if i['stem'] == (r['instance'], r['new_decouples']))
        retained.append({**r, 'owner_ref': owner, 'owner_distance_mm': round(dist(owner, r['ref']), 3)})
    before, after = d55.totals(caps_b), d55.totals(caps_a)
    result = {
        'status': 'SOURCE-LEVEL decoupling re-check of an UNADOPTED Stage56 candidate; no PDN, layout or hardware result',
        'retained_bypasses': retained,
        'surviving_ics_without_complete_owned_bypass': {'before': missing_b, 'after': missing_a},
        'rail_nominal_reduction_uF': {r: round(before[r]['nominal_uF']-after[r]['nominal_uF'], 3) for r in d55.RAILS},
        'rail_nominal_capacitance_after_uF': {r: after[r]['nominal_uF'] for r in d55.RAILS},
        'survivors_whose_nearest_rail_cap_is_removed': losing,
        'limits': ('Nominal values only; floorplan-origin distances, not copper paths; ownership is the project '
                        'Decouples attribute, not a PDN impedance model.'),
    }
    path = HERE/'decoupling.json'; body = json.dumps(result, indent=2, sort_keys=True)+'\n'
    if check:
        require(path.read_text() == body, 'decoupling replay drift')
    else:
        path.write_text(body)
    print('PASS Stage56 decoupling: reduction', result['rail_nominal_reduction_uF'], 'uF; survivors losing nearest cap:',
          sorted({x['ref'] for x in losing}))
    return result


if __name__ == '__main__':
    run('--check' in sys.argv)
