"""Stage57 acceptance gate: exact additive /M5B/C819409_SENSE proposal on the Stage53 board.

Reuses the Stage53 identity, snapshot and warning helpers unchanged; only the target,
baseline, open counts, layer rule and rail check differ. No proposal exists yet: until
the route search runs and its proposal is bound here by hash, every evaluation fails.
Usage: accept.py BASELINE_DIR CANDIDATE_DIR PROPOSAL LABEL
"""
from pathlib import Path
from collections import Counter
import importlib.util, json, sys
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[4]
IMPL = ROOT/'design/architecture-278/implementation'
sys.path.insert(0, str(IMPL/'stage41/native-pilot'))
_spec = importlib.util.spec_from_file_location('stage53_accept', IMPL/'stage53/in4-study/accept.py')
s53 = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(s53)
from identity_guard import inventory, compare, structure_matches, digest
read, sha, signature, canonical, contract = s53.read, s53.sha, s53.signature, s53.canonical, s53.contract
validate_snapshot, warning_gate, exact_added_properties = s53.validate_snapshot, s53.warning_gate, s53.exact_added_properties

BASE = '27d2214492f9dd88483be014df4197fdb936cbbc7c445f17c8178cce97126560'
NET = 'X1B64D2A971AB89E1AF19'
SOURCE, TARGET = ('R8248', '2'), ('U8215', '3')
TARGET_SIZE, OPENS_BEFORE, OPENS_AFTER = 162, 115, 114
RAILS = {'+12V': [1025], '-12V': [1015], 'AGND': [1]*11 + [3, 6, 1425]}
# F.Cu/B.Cu frozen; In4.Cu added only for the single owner-approved trial
# (#288 OSC-S57-02 option A, comment 6288473096). Any other inner layer is rejected.
ALLOWED_TRACK_LAYERS = ('F.Cu', 'B.Cu', 'In4.Cu')
PROPOSAL = HERE/'proposal.json'
PROPOSAL_SHA = '149212fd1044c4a39d84af436460a2353a940bad92ce9d6085a5ae54185d8e82'  # search.py in4 (OSC-S57-02 A)


def bound_proposal(proposal):
    if PROPOSAL_SHA is None: raise ValueError('no authorized proposal: route search NOT RUN')
    if not PROPOSAL.exists() or sha(PROPOSAL) != PROPOSAL_SHA or signature(proposal) != signature(read(PROPOSAL)):
        raise ValueError('exact authorized proposal')


def layer_gate(proposal):
    bad = sorted({r['layer'] for r in proposal['copper'] if r['kind'] == 'segment' and r['layer'] not in ALLOWED_TRACK_LAYERS})
    if bad: raise ValueError('inner-layer copper needs a new approval: ' + ','.join(bad))
    if any(r['net'] != NET for r in proposal['copper']): raise ValueError('proposal copper on another net')
    if any(r['kind'] not in ('segment', 'via') for r in proposal['copper']): raise ValueError('proposal kind')


def identity(before_raw, after_raw, proposal):
    if digest(before_raw) != proposal['board_sha256'] or proposal['board_sha256'] != BASE: raise ValueError('baseline binding')
    bound_proposal(proposal); layer_gate(proposal)
    if proposal['removed_uuids']: raise ValueError('retirement forbidden')
    exact_added_properties(after_raw, proposal)
    before, after = inventory(before_raw), inventory(after_raw)
    newids = {r['uuid'] for r in proposal['copper']}
    actual = Counter(canonical(c) for c, n in after['native_contract'].items() if c[1] in newids for _ in range(n))
    if actual != Counter(canonical(contract(r)) for r in proposal['copper']): raise ValueError('proposal geometry/net changed')
    allowed = [list(k) for k, n in after['copper'].items() if k[1] in newids for _ in range(n)]
    result = compare(before, after, [], allowed)
    result['checks']['all_footprints_unchanged'] = structure_matches(before, after, {})
    result['accepted'] = all(result['checks'].values())
    if not result['accepted']: raise ValueError('identity preservation: ' + str(result))
    return result


def rail_gate(snapshot):
    sizes = {r: sorted(len(g) for g in snapshot['groups'].get(r, [])) for r in RAILS}
    if sizes != {r: sorted(v) for r, v in RAILS.items()}: raise ValueError('rail partition sizes: ' + json.dumps(sizes))
    return sizes


def connectivity(old, new, proposal):
    validate_snapshot(old); validate_snapshot(new); rail_gate(old)
    old_objects, new_objects = old['objects'], new['objects']; retained = set(old_objects)
    if not retained <= set(new_objects) or any(new_objects[k] != old_objects[k] for k in retained): raise ValueError('retained native objects')
    added = set(new_objects) - retained
    if {new_objects[k].get('uuid') for k in added} != {r['uuid'] for r in proposal['copper']} or len(added) != len(proposal['copper']):
        raise ValueError('native additions')
    pad = lambda ref, pin: next(k for k, v in old_objects.items() if v.get('kind') == 'pad' and v.get('ref') == ref and v.get('pin') == pin)
    source, target = pad(*SOURCE), pad(*TARGET)
    sg = next(set(g) for g in old['groups'][NET] if source in g); tg = next(set(g) for g in old['groups'][NET] if target in g)
    if sg == tg or sg != {source} or len(tg) != TARGET_SIZE: raise ValueError('baseline target partition')
    expected = {net: [set(g) for g in groups] for net, groups in old['groups'].items()}
    expected[NET] = [g for g in expected[NET] if g not in [sg, tg]] + [sg | tg]
    if set(new['groups']) != set(expected): raise ValueError('native net set')
    for net, groups in new['groups'].items():
        projected = [set(g) & retained for g in groups]
        if any(not g for g in projected): raise ValueError('new-only island')
        if {frozenset(g) for g in projected} != {frozenset(g) for g in expected[net]}: raise ValueError('unexpected partition: ' + net)
    if old['native_open_edges'] != OPENS_BEFORE or new['native_open_edges'] != OPENS_AFTER: raise ValueError('open count')
    for key in added:
        net = new_objects[key]['net']; g = next(set(g) & retained for g in new['groups'][net] if key in g)
        if net != NET or g != sg | tg: raise ValueError('new copper attached to wrong component')
    rails = rail_gate(new)
    return dict(accepted=True, old_opens=OPENS_BEFORE, new_opens=OPENS_AFTER, source_component_size=1,
                target_component_size=TARGET_SIZE, merged_retained_members=TARGET_SIZE + 1, added_objects=len(added),
                source_component_hash=signature(sorted(sg)), target_component_hash=signature(sorted(tg)),
                exact_retained_partition_merge=True, rail_partitions=rails)


def evaluate(baseline, candidate, proposal_path, label):
    proposal = read(proposal_path); before = baseline/'osc-jack-left.kicad_pcb'; after = candidate/'osc-jack-left.kicad_pcb'
    old = read(baseline/'connectivity-passfresh.json'); new = read(candidate/f'connectivity-{label}.json')
    if old['board_sha256'] != sha(before) or new['board_sha256'] != sha(after): raise ValueError('snapshot bytes')
    result = dict(identity=identity(before.read_text(), after.read_text(), proposal), connectivity=connectivity(old, new, proposal),
                  baseline_sha256=sha(before), candidate_sha256=sha(after), proposal_sha256=sha(proposal_path))
    drc = read(candidate/f'drc-{label}.json')
    sys.path.insert(0, str(IMPL/'stage44/b2-specific'))
    from drc_run import validate, dependencies
    validate(s53.receipt_path(candidate/f'drc-{label}.json'), read(candidate/f'drc-{label}.json.execution.json'), sha(after), dependencies(after))
    if dependencies(before) != dependencies(after): raise ValueError('dependency drift')
    if drc['kicad_version'] != '10.0.6' or new['version'] != '10.0.6' or drc['schematic_parity'] or any(v['severity'] == 'error' for v in drc['violations']) or len(drc['unconnected_items']) != OPENS_AFTER:
        raise ValueError('native DRC/parity/open gate')
    old_report = baseline/'drc-passfresh.json'
    validate(s53.receipt_path(old_report), read(baseline/'drc-passfresh.json.execution.json'), sha(before), dependencies(before))
    if baseline.parent.resolve() != candidate.parent.resolve(): raise ValueError('relative library root depth changed')
    result['warning_comparison'] = warning_gate(read(old_report), drc)
    result['drc'] = dict(rule_errors=0, parity=0, opens=OPENS_AFTER, warning_counts=dict(Counter(v['type'] for v in drc['violations'] if v['severity'] == 'warning')))
    result['courtyard'] = 'NOT EVALUATED here; courtyard contact is never clearance or assembly proof'
    result['accepted_bounded_native_repair'] = True
    return result


def run(baseline, candidate, proposal_path, label):
    result = evaluate(baseline, candidate, proposal_path, label)
    output = candidate/f'acceptance-{label}.json'
    if output.exists(): raise ValueError('do not overwrite acceptance')
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n'); print(json.dumps(result))


if __name__ == '__main__':
    run(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4])
