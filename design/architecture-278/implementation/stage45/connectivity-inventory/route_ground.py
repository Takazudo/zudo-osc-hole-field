"""Propose one additive AGND island tie; retain every native obstacle."""
from pathlib import Path
import copy
import json
import sys
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.grid_router import route, copper_rows

SOURCE = 'b9d402b4-b8c4-5ab2-a8c0-3fd450c4809c'  # R8270:2
DESTINATION = '41587408-3396-5f6d-aaa0-c9536a778faa'  # R2305:2
BASE_HASH = 'd1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'


def propose(dump_path, output, rear_only=False):
    original = json.loads(dump_path.read_text())
    if original['board_sha256'] != BASE_HASH:
        raise ValueError('baseline hash')
    groups = original['islands']['AGND']
    if not any(g == [SOURCE] for g in groups) or sum(DESTINATION in g for g in groups) != 1:
        raise ValueError('unexpected target membership')
    d = copy.deepcopy(original)
    d['islands']['AGND'] = [[SOURCE], [DESTINATION]]
    results, removed = route(d, ['AGND'], res=.05, signal_width=.2, clearance=.25,
                            allowed_layers=['B.Cu'] if rear_only else ['F.Cu', 'In2.Cu', 'B.Cu'], rail_nets=['AGND'], rail_width=.4,
                            via_diameter=.7, via_drill=.3, max_expansions=1000000,
                            bounds_mm=[267, 127, 274, 135], window_mm=8,
                            log=lambda s: print(s, flush=True))
    if removed:
        raise ValueError('unexpected removal')
    rows, links = copper_rows(results, 'osc-jack-left', 'stage45-single-ground-island')
    output.write_text(json.dumps({'board_sha256': BASE_HASH, 'removed_uuids': [],
                                  'copper': rows}, indent=2) + '\n')
    output.with_name('ground-search.json').write_text(json.dumps({
        'source': SOURCE, 'destination': DESTINATION, 'baseline_islands': groups,
        'results': results, 'links': links, 'failed_links': sum(not r['path'] for r in results),
        'limits': 'Only source/destination membership narrowed; all obstacles retained. Proposal only; full native partitions and DRC mandatory.'}, indent=2) + '\n')
    if any(not r['path'] for r in results):
        raise SystemExit(1)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('dump', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--rear-only', action='store_true')
    args = parser.parse_args()
    propose(args.dump, args.output, args.rear_only)
