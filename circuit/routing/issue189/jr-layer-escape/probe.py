"""Compare bounded layer domains on one immutable native JR133 input."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.grid_router import route, copper_rows
from scripts.pcbgen.route_jack_grid import RAILS, neck_kwargs, LAYER_COST

HERE = Path(__file__).parent
p = argparse.ArgumentParser()
p.add_argument('dump', type=Path)
a = p.parse_args()
sha = lambda b: hashlib.sha256(b).hexdigest()
source = 'd25854092d89fa1253d05c95c21a225629f8c3f9'
raw = subprocess.check_output(['git', 'show', source + ':circuit/routing/issue189/jack-post-adoption-neighbours/result.json'], cwd=ROOT)
historical = next(b for b in json.loads(raw)['boards'] if b['board'] == 'osc-jack-right')
assert sha(a.dump.read_bytes()) == '001e5809855b059239408859af16a9700d0af0fe5aae9320c96f266c560bcb5a'
dump = json.loads(a.dump.read_text())
board = ROOT / 'boards/osc-jack-right/osc-jack-right.kicad_pcb'
assert sha(board.read_bytes()) == dump['board_sha256'] == '22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd'
assert dump['open_edges'] == 133
cases = [c for c in historical['cases'] if any(e.get('reason') == 'expansion_limit' for e in c['diagnostics'])]
assert len(cases) == 4
for c in cases:
    current = [set(g) for g in dump['islands'][c['net']]]
    assert all(set(g) in current for g in c['native_groups']), 'Historical obligation changed; reconcile explicitly'
result = dict(status='BOUNDED SEARCH; NO NATIVE ACCEPTANCE', source_commit=source,
    historical_cases_sha256=sha(raw), board_sha256=dump['board_sha256'], dump_sha256=sha(a.dump.read_bytes()),
    router_sha256=sha((ROOT / 'scripts/pcbgen/grid_router.py').read_bytes()),
    method='Same JR133 native input, four obligations, 0.025mm lattice, 300000 expansions and 6mm bounds; compare F/In2/In3/B with F/In2/B and F/In3/B. Preserve every obstacle, existing neck rule and -12V fill guard.', cases=[])
for c in cases:
    for label, layers in [('four-layer', ['F.Cu', 'In2.Cu', 'In3.Cu', 'B.Cu']), ('in2', ['F.Cu', 'In2.Cu', 'B.Cu']), ('in3', ['F.Cu', 'In3.Cu', 'B.Cu'])]:
        d = copy.deepcopy(dump)
        d['islands'][c['net']] = c['native_groups']
        events = []
        started = time.monotonic()
        routed, removed = route(d, [c['net']], allowed_layers=layers, layer_cost=LAYER_COST,
            rail_nets=RAILS, clearance=.2, signal_width=.2, signal_via_diameter=.6,
            res=.025, grow={n: .05 for n in RAILS + ['AGND']}, window_mm=6,
            max_expansions=300000, bounds_mm=c['bounds_mm'], fill_guards={'-12V': 'In3.Cu'},
            diagnostics=events, **neck_kwargs('osc-jack-right'))
        assert not removed
        copper, _ = copper_rows(routed, 'osc-jack-right', 'issue189-jr-layer-' + label + '-' + c['net'])
        complete = bool(copper) and bool(routed) and all(r['path'] for r in routed)
        result['cases'].append(dict(net=c['net'], domain=label, historical=c,
            elapsed_seconds=time.monotonic()-started, complete=complete, diagnostics=events,
            routes=routed, proposal=dict(board_sha256=dump['board_sha256'], removed_uuids=[], copper=copper)))
        (HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
        print(c['net'], label, 'complete', complete, 'seconds', round(time.monotonic()-started, 2), flush=True)
assert sha(board.read_bytes()) == dump['board_sha256']
assert result['router_sha256'] == sha((ROOT / 'scripts/pcbgen/grid_router.py').read_bytes())
result['status'] = 'COMPLETE BOUNDED SEARCH; NO NATIVE ACCEPTANCE'
(HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
