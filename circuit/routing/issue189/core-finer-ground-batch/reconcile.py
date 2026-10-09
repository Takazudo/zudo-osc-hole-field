"""Reconcile the saved rejected native trial; never promote its candidate."""
import collections
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import connectivity_signature, promotion_gate

root = Path('.circuit-cache/issue189-downloaded/core-finer-ground-batch/.circuit-cache')
out = Path(__file__).parent
stages = {s: root / ('osc-core-grid-shards-' + s) for s in ('start', 'merge', 'fresh')}
dumps = {s: json.loads((p / 'dump.json').read_text()) for s, p in stages.items()}
drcs = {s: json.loads((p / 'drc.json').read_text()) for s, p in stages.items()}
boards = {s: (p / 'osc-core.kicad_pcb').read_text() for s, p in stages.items()}
groups = {s: copper_block_groups(b) for s, b in boards.items()}
counts = {s: collections.Counter(b for bs in g.values() for b in bs) for s, g in groups.items()}
a, b = counts['start'], counts['merge']
assert not a - b
assert sum(a.values()) == 133169 and sum((b-a).values()) == 382
assert connectivity_signature(dumps['merge']) == connectivity_signature(dumps['fresh'])
gate = promotion_gate(dumps['start'], dumps['merge'], drcs['start'], drcs['merge'])
assert not gate['adopted'] and not gate['split_pad_groups'] and not gate['native_errors']
pair = ['8b23aee3-f7be-588d-bfd3-d3c8b6ccdb70', 'f3f839da-7140-5261-8465-5d0f95deef46']
assert gate['new_warning_identities'] == [('hole_to_hole', tuple(pair))]
for u in pair:
    assert groups['start'][u] == groups['merge'][u] == groups['fresh'][u]
for key in ('pads', 'edges', 'keepouts', 'layers'):
    assert dumps['start'][key] == dumps['merge'][key] == dumps['fresh'][key], key
for suffix in ('kicad_pro', 'kicad_dru'):
    assert len({(p / ('osc-core.' + suffix)).read_bytes() for p in stages.values()}) == 1
proof = dict(gate, run_id=37950004600, before_objects=sum(a.values()),
             after_objects=sum(b.values()), identical_objects=sum((a & b).values()),
             added_objects=sum((b-a).values()), removed_objects=sum((a-b).values()),
             native_edges_before=dumps['start']['open_edges'],
             native_edges_after=dumps['merge']['open_edges'], fresh_agrees=True,
             warning_pair_full_blocks_unchanged=pair,
             warning_pair_native_geometry=[v for v in dumps['start']['vias'] if v['uuid'] in pair],
             physical_geometry_and_project_rules_unchanged=True,
             board_sha256={s: hashlib.sha256(b.encode()).hexdigest() for s,b in boards.items()},
             warnings_by_type={s: dict(collections.Counter(v['type'] for v in d['violations'] if v['severity']=='warning')) for s,d in drcs.items()})
(out / 'retention.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2))
