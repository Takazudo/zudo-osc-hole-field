#!/usr/bin/env python3
"""Oracle regressions: reject stale copper and detect a missing ground stitch."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.fixtures.dense_copper import replay, record

path = Path(sys.argv[1])
source = json.loads((ROOT/'scripts/pcbgen/fixtures/dense-evidence/copper.json').read_text())
board = pcbnew.LoadBoard(str(path))
assert replay(board, source) == 0
# Owner copper and graphics not named in the source remain untouched.
owner = pcbnew.PCB_TEXT(board)
owner.SetText('OWNER REGRESSION')
board.Add(owner)
assert replay(board, source) == 0
assert any(t.m_Uuid.AsString() == owner.m_Uuid.AsString() for t in board.GetDrawings())
fp = next(iter(board.GetFootprints()))
fp.SetPosition(fp.GetPosition() + pcbnew.VECTOR2I(pcbnew.FromMM(.1), 0))
try:
    replay(board, source)
except ValueError as exc:
    assert 'placed pads/nets' in str(exc)
else:
    raise AssertionError('changed placement accepted retained routing')
board = pcbnew.LoadBoard(str(path))
track = next(t for t in board.GetTracks() if t.m_Uuid.AsString() == source['items'][0]['uuid'])
track.SetWidth(record(track)['width'] + 1000)
try:
    replay(board, source)
except ValueError as exc:
    assert 'source copper changed' in str(exc)
else:
    raise AssertionError('changed copper accepted')
board = pcbnew.LoadBoard(str(path))
stitches = json.loads((ROOT/'scripts/pcbgen/fixtures/dense-evidence/stitching.json').read_text())
via_id = next(t['uuid'] for t in stitches['items'] if t['kind'] == 'via' and t['start'] == [151800000, 191000000])
via = next(t for t in board.GetTracks() if t.m_Uuid.AsString() == via_id)
board.Remove(via)
mutant = path.parent/'negative-missing-ground.kicad_pcb'
board.SetFileName(str(mutant))
pcbnew.SaveBoard(str(mutant), board)
shutil.copyfile(path.with_suffix('.kicad_pro'), mutant.with_suffix('.kicad_pro'))
report = path.parent/'reports/negative-drc.json'
subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--format', 'json',
                '--severity-all', '-o', str(report), str(mutant)], check=True)
data = json.loads(report.read_text())
assert not any(v['severity'] == 'error' for v in data['violations'])
assert any('C2907' in item['description'] and '[GND]' in item['description']
           for violation in data['unconnected_items'] for item in violation['items']), data['unconnected_items']
print('PASS: stale placement/copper rejected, owner graphic preserved, missing C2907 stitch detected by KiCad')
