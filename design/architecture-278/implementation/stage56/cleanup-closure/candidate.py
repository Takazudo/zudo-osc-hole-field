"""Stage56: close the two Stage55 adoption findings on a disposable osc-core candidate.

1. Retain C144, C128 and C240 (+12 V, 100 nF), the nearest rail capacitors of surviving
   U101 REF5050AIDR, U107 and U207 LM393BIDR. Family keys render in both H1 and H2, so
   their counterparts C244, C228 and C140 are retained too (six caps). `Decouples` is
   re-owned to the survivor's package stem; nothing else about them changes.
2. Remove unit-field ambiguity: for an osc-core package whose units disagree on Role,
   LogicalCellKey or Island, drop that field from every unit of that package in the
   board schematic, mirroring the projector's existing JL/JR rule. The PCB keeps its
   footprint fields; native parity decides whether that is consistent.

Writes only under `.circuit-cache/stage56/`. Canonical files are never written.
"""
from pathlib import Path
from dataclasses import replace
import hashlib, importlib.util, json, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from scripts.schgen.core import designator

S55 = ROOT/'design/architecture-278/implementation/stage55/idle-quad-cleanup'
CACHE = ROOT/'.circuit-cache/stage56'
RETAIN = {'C144': 'U101', 'C128': 'U107', 'C240': 'U207'}
UNIT_FIELDS = ('Role', 'LogicalCellKey', 'Island')


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


c55 = load('stage55_candidate', S55/'candidate.py')
require = c55.require


def retained_families(families, instances, new_families):
    """Stage54 families with the retained bypass keys re-added and re-owned.

    A family part renders once per instance (H1, H2), so retaining the key of C144,
    C128 or C240 also retains its H2/H1 counterpart, owned by the same survivor stem
    in that instance. This keeps H1 and H2 identical.
    """
    old = next(f for f in families if f.name == 'sample_hold')
    new = next(f for f in new_families if f.name == 'sample_hold')
    insts = [i for i in instances if i.family == 'sample_hold']
    stems = {}
    for p in old.parts:
        for i in insts:
            if p.prefix == 'U' and designator(p, i) in RETAIN.values():
                stems.setdefault(designator(p, i), set()).add(p.key.rsplit('.', 1)[0])
    require(set(stems) == set(RETAIN.values()) and all(len(v) == 1 for v in stems.values()), 'survivor stems')
    rows, added = [], []
    for p in old.parts:
        refs = {designator(p, i): i.name for i in insts}
        hit = set(refs) & set(RETAIN)
        if not hit:
            continue
        require(len(hit) == 1 and p not in new.parts, 'retained key was a Stage54 removal')
        require(p.prefix == 'C' and p.value == '100 nF' and p.attributes.get('MPN') == 'GRM188R71H104KA93D', 'retained cap identity')
        require(sorted(p.pins.values()) == ['+12V', 'AGND'], 'retained cap rail')
        owner = next(iter(stems[RETAIN[hit.pop()]]))
        for ref, inst in sorted(refs.items()):
            rows.append({'ref': ref, 'instance': inst, 'key': p.key, 'old_decouples': p.attributes['Decouples'], 'new_decouples': owner})
        added.append(replace(p, attributes={**p.attributes, 'Decouples': owner}))
    require(len(added) == 3 and len(rows) == 6, 'retained key roster')
    candidate = replace(new, parts=new.parts + tuple(added))
    return tuple(candidate if f.name == 'sample_hold' else f for f in new_families), rows


def strip_ambiguous(board_families):
    values = {}
    for f in board_families:
        for p in f.parts:
            for field in UNIT_FIELDS:
                values.setdefault((p.panel_ref, field), set()).add(p.attributes.get(field, ''))
    drop = {k for k, v in values.items() if len(v) > 1}
    out = []
    for f in board_families:
        parts = tuple(replace(p, attributes={k: v for k, v in p.attributes.items() if (p.panel_ref, k) not in drop})
                      for p in f.parts)
        out.append(replace(f, parts=parts))
    strip_ambiguous.dropped = sorted(drop)
    return out


def compute():
    s54 = c55.load_stage54()
    families, instances = s54.specification()
    new_families, proposal = s54.prepare(families, instances)
    s55_removed = set(proposal['removed_refs'])
    families56, rows = retained_families(families, instances, new_families)
    kept = {r['ref'] for r in rows}
    removed = s55_removed - kept
    require(kept <= s55_removed and len(removed) == 30, 'retained caps were Stage54 removals')
    partition = json.loads((ROOT/'design/partition/partition.json').read_text())
    floorplan = json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())
    baseline, canon = c55.board_render(None, partition, floorplan)
    for name, body in baseline.items():
        require((ROOT/'boards/osc-core'/name).read_text() == body, 'canonical board generator drift '+name)
    fpart, ffloor = c55.filtered_partition(removed)
    candidate, canon_after = c55.board_render((families56, instances), fpart, ffloor, transform=strip_ambiguous)
    dropped = strip_ambiguous.dropped
    require(set(candidate) == set(baseline), 'board schematic file roster changed')
    refs_in = lambda tree, refs: {r for r in refs if any(f'"Reference" "{r}"' in b for b in tree.values())}
    require(refs_in(candidate, s55_removed) == kept, 'exactly the retained caps survive')
    removed_tokens = sorted(set(canon) - set(canon_after))
    require(len(removed_tokens) == 48, 'removed board-net roster')
    conflicts = c55.unit_field_conflicts(candidate)
    require(conflicts == {}, 'unit-field ambiguity remains')
    receipt = {
        'status': 'DISPOSABLE Stage56 candidate board schematic; canonical files unchanged',
        'stage54_proposal_sha256': c55.sha(ROOT/'design/architecture-278/implementation/stage54/power-cleanup/proposal.json'),
        'removed_refs': sorted(removed),
        'removed_board_net_tokens': removed_tokens,
        'retained_bypasses': rows,
        'dropped_unit_fields': {'count': len(dropped), 'by_field': {f: sum(1 for _, x in dropped if x == f) for f in UNIT_FIELDS},
                                'pairs': [list(x) for x in dropped]},
        'multi_unit_field_conflicts': {'baseline': c55.unit_field_conflicts(baseline), 'candidate': conflicts},
        'changed_board_schematic_files': sorted(n for n in baseline if baseline[n] != candidate[n]),
        'candidate_schematic_sha256': {n: hashlib.sha256(b.encode()).hexdigest() for n, b in sorted(candidate.items()) if baseline[n] != candidate[n]},
    }
    return baseline, candidate, receipt


def run():
    require(not CACHE.exists(), 'fresh .circuit-cache/stage56 required')
    baseline, candidate, receipt = compute()
    c55.CACHE, saved = CACHE, c55.CACHE
    try:
        c55.write_tree(CACHE/'candidate/osc-core', candidate)
    finally:
        c55.CACHE = saved
    (CACHE/'schematic-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True)+'\n')
    print(f"PASS Stage56 candidate: {len(receipt['removed_refs'])} removed, {len(receipt['retained_bypasses'])} retained, "
          f"{receipt['dropped_unit_fields']['count']} ambiguous unit fields dropped, "
          f"{len(receipt['changed_board_schematic_files'])} sheets changed")
    return receipt


if __name__ == '__main__':
    run()
