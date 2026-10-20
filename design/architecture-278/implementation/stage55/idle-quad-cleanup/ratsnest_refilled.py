"""Stage55: refill every zone, save a disposable refilled copy, then take the complete native
ratsnest with scripts/pcbgen/ratsnest.py (CLI DRC JSON truncates unconnected items at 499).

Runs in the pinned oracle: ratsnest_refilled.py INPUT_PCB REFILLED_PCB OUTPUT_JSON
"""
import json, sys
from pathlib import Path
import pcbnew
sys.path.insert(0, '/work')
from scripts.pcbgen.ratsnest import inspect

source, refilled, output = map(Path, sys.argv[1:4])
assert not refilled.exists() and not output.exists(), 'refuse overwrite'
board = pcbnew.LoadBoard(str(source))
filler = pcbnew.ZONE_FILLER(board)
assert filler.Fill(board.Zones()), 'zone fill failed'
board.Save(str(refilled))
result = inspect(refilled)
result['refilled_from'] = str(source)
output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print('native ratsnest after refill:', result['native_unconnected_edges'], 'edges')
