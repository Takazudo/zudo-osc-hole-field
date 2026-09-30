#!/usr/bin/env python3
"""Check the full dense fixture against retained copper, fixed centres, and DRC."""
import hashlib
import json
import sys
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.definition import load_definition, load_lock, selected_hardware
from scripts.geometry.panel_frame import to_kicad
from scripts.pcbgen.fixtures.dense_copper import geometry, record
from scripts.pcbgen.route import drc_summary, drc_passes

board_path, drc_path = map(Path, sys.argv[1:])
board = pcbnew.LoadBoard(str(board_path))
definition = load_definition(ROOT/'design/boards/fixture-route-dense.json')
footprints = {f.GetReference(): f for f in board.GetFootprints()}
assert len(footprints) == 211
assert board.GetCopperLayerCount() == 4
selected = selected_hardware(definition, load_lock(ROOT/'design/grid/placements.lock.json'))
assert len(selected) == 30
for hardware in selected:
    fp = footprints[hardware['ref']]
    expected = to_kicad(hardware['x_mm'], hardware['y_mm'])
    actual = tuple(pcbnew.ToMM(v) for v in (fp.GetPosition().x, fp.GetPosition().y))
    assert actual == expected, (hardware['ref'], actual, expected)
    assert fp.IsLocked(), hardware['ref']
assert len(list(footprints['J3101'].Pads())) == 40
current = {t.m_Uuid.AsString(): record(t) for t in board.GetTracks()}
for name in ('copper', 'stitching'):
    source = json.loads((ROOT/f'scripts/pcbgen/fixtures/dense-evidence/{name}.json').read_text())
    assert source['placed_pad_geometry_sha256'] == geometry(board)
    for item in source['items']:
        assert current.get(item['uuid']) == item, item['uuid']
preserved = json.loads((ROOT/'scripts/pcbgen/fixtures/dense-evidence/preservation.json').read_text())
records = [current[u] for u in preserved['preexisting_uuids']]
assert len(records) == 1080
assert hashlib.sha256(json.dumps(records, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == preserved['copper_records_sha256']
data = json.loads(drc_path.read_text())
assert data['kicad_version'] == '10.0.6'
summary = drc_summary(data)
assert drc_passes(summary), summary
print(f'PASS: 211 footprints, 30 fixed hardware centres, 40 connector pads, 4 layers; {len(current)} preserved copper items; {summary}')
