"""Bounded additive raster search for /M5B/C819409_SENSE on the Stage53 board; disposable.

Modes coarse/fine: outer layers only (F.Cu, B.Cu, ordinary through vias), per the frozen
Stage57 criteria. Mode in4: the single owner-approved trial (#288 OSC-S57-02, option A,
comment 6288473096) adding In4.Cu (+12V plane) at 0.10 mm; the result must stay outside
the Stage53 In4 corridor.
A successful search is a proposal, not acceptance; native refill/DRC/connectivity decide.
Usage (host, venv with scripts/pcbgen/numerical-requirements.txt):
  search.py DUMP OUTPUT_PROPOSAL [coarse|fine|in4]
"""
from pathlib import Path
import hashlib, json, sys
ROOT = Path(__file__).resolve().parents[5]; sys.path.insert(0, str(ROOT))
from scripts.pcbgen.grid_router import route, copper_rows
BASE = '27d2214492f9dd88483be014df4197fdb936cbbc7c445f17c8178cce97126560'
NET = 'X1B64D2A971AB89E1AF19'
SOURCE = '77be702c-af7d-525a-80c2-039a9b90636e'  # R8248:2 pad uuid in the dump
PARAMS = dict(res=.1, clearance=.2, signal_width=.2, via_diameter=.6, via_drill=.3, hole_clearance=.25, edge_clearance=.5,
              grow={'AGND': .05, '+12V': .05, '-12V': .05, '+5V': .05}, allowed_layers=['F.Cu', 'B.Cu'],
              max_expansions=1500000, bounds_mm=[238, 100, 276, 160], window_mm=40, via_cost=60)


STAGE53_IN4_CORRIDOR_MM = [227.980882, 95.7, 236.0, 113.39]


def outside_corridor(rows):
    x0, y0, x1, y1 = STAGE53_IN4_CORRIDOR_MM
    for r in rows:
        for p in ([r['start_nm'], r['end_nm']] if r['kind'] == 'segment' else [r['at_nm']]):
            if x0 - 1 <= p[0] / 1e6 <= x1 + 1 and y0 - 1 <= p[1] / 1e6 <= y1 + 1: return False
    return True


def run(path, output, mode='coarse'):
    if mode not in ('coarse', 'fine', 'in4'): raise ValueError('bounded mode')
    if output.exists() or output.with_suffix('.search.json').exists(): raise ValueError('refuse overwrite search')
    d = json.loads(path.read_text())
    if d['board_sha256'] != BASE or sorted(map(len, d['islands'][NET])) != [1, 162] or [SOURCE] not in d['islands'][NET]:
        raise ValueError('baseline')
    pad = next(p for p in d['pads'] if p['uuid'] == SOURCE)
    if (pad['ref'], pad['pad']) != ('R8248', '2'): raise ValueError('source pad identity')
    params = dict(PARAMS, res=.05 if mode == 'fine' else .1)
    if mode == 'in4': params['allowed_layers'] = ['F.Cu', 'B.Cu', 'In4.Cu']
    diagnostics = []
    results, removed = route(d, [NET], diagnostics=diagnostics, **params)
    if removed: raise ValueError('retirement')
    rows, links = copper_rows(results, 'osc-jack-left', 'stage57-m5b-sense-' + mode, via_diameter=.6, via_drill=.3)
    if not outside_corridor(rows): raise ValueError('route enters the Stage53 In4 corridor')
    output.with_suffix('.search.json').write_text(json.dumps(dict(parameters=params, results=results, links=links, diagnostics=diagnostics,
        dump_sha256=hashlib.sha256(path.read_bytes()).hexdigest()), indent=2, sort_keys=True) + '\n')
    output.write_text(json.dumps(dict(board_sha256=BASE, removed_uuids=[], copper=rows), indent=2, sort_keys=True) + '\n')
    failed = sum(not r['path'] for r in results)
    print(json.dumps({'objects': len(rows), 'failed_links': failed, 'layers': sorted({r.get('layer', 'via') for r in rows})}))
    return failed


if __name__ == '__main__':
    sys.exit(run(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else 'coarse'))
