"""Revision 4 site report: each new GH header site against pads, outline, reserves, other headers, the K block pins,
the floorplan placements and the committed link gate (fields, slots and the gate's re-placed footprints)."""
import json
import math
import sys
from pathlib import Path
R = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R))
sys.path.insert(0, str(R / 'scripts/stack/studies/mc04_c1_capacity'))
import capacity as cap  # noqa: E402
import scripts.checks.connector_packing35 as cp  # noqa: E402

cap.stale_inputs = lambda a, b: []  # the gate predates this partition change; geometry of links and boards is unchanged
scene, unresolved, accepted, _ = cap.current_scene()
pc = json.loads((R / 'design/partition/connector-packing-candidate.json').read_text())
fp = json.loads((R / 'design/partition/floorplan-candidate.json').read_text())
io = json.loads((R / 'design/reports/io-partition.json').read_text())
gate = json.loads((R / 'design/stack/geometry/links/link-gate.json').read_text())
lock = {p['uid']: p for p in json.loads((R / 'design/grid/placements.lock.json').read_text())['placements']}
parts = {p['ref']: p for p in io['physical_packages']}
spec = cp.source()
SITES = [(142, 122), (159, 122), (193, 24), (227, 24), (295, 24)]


def gapd(a, b):
    return max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3])


rows = []
for h in pc['headers']:
    if tuple(h['center_mm']) not in SITES:
        continue
    board, side, land = h['board'], h['side'], h['land_courtyard_mm']
    face = side[0]
    cands = []
    if board != 'K':
        for p in parts.values():
            if p['panel_uid'] and cp.board_for(p) == board:
                for ref, pad in cp.pads(p, lock):
                    cands.append((gapd(land, pad), 'panel pad ' + ref))
        poly = spec['boards'][board]['outline']
        xs = [q[0] for q in poly]
        cands.append((min(land[0] - min(xs), max(xs) - land[2], land[1] - 20, 164 - land[3]), 'outline'))
    for res in spec['boards'][board].get('reserves', []):
        if side in res['sides']:
            cands.append((gapd(land, res['rect']), 'reserve ' + res['id']))
    for o in pc['headers']:
        if o['board'] == board and o['id'] != h['id'] and o['side'] == side:
            cands.append((gapd(land, o['land_courtyard_mm']), 'header ' + o['id']))
    for p in fp['placements']:
        if p['board'] == board and p['side'] == side and not p['ref'].startswith('J9'):
            cands.append((gapd(land, p['courtyard_mm']), 'floorplan ' + p['ref']))
    links = scene.field.links.get((board, face))
    for rect, lab in (links.items if links else []):
        cands.append((gapd(land, rect), 'link field/slot ' + lab))
    cands.sort()
    gate_moved = [r['ref'] for r in gate['replacement']['footprints'] if r['board'] == board and r['new'] is not None
                  and r.get('new_face', r['face']) == face and gapd(land, r['new_courtyard']) < 0]
    link_hits = sorted({lab for d, lab in cands if lab.startswith('link') and d < 0.25})
    rows.append({'header': h['id'], 'board': board, 'side': side, 'centre_mm': h['center_mm'], 'land_mm': land,
                 'nearest': [{'obstacle': lab, 'clearance_mm': round(d, 2)} for d, lab in cands[:3]],
                 'overlaps': [lab for d, lab in cands if d < 0],
                 'link_fields_within_0_25_mm': link_hits,
                 'gate_replaced_footprints_under_it': gate_moved})
released = {b: r.get('displaced_by_gh_headers', []) for b, r in fp['adopted_placement_pins']['boards'].items()}
out = {'sites': rows, 'released_under_gh_headers': released}
Path(__file__).with_name('sites.json').write_text(json.dumps(out, indent=1))
for r in rows:
    print(r['header'], r['centre_mm'], r['side'], 'nearest', r['nearest'][:2], 'overlaps', r['overlaps'], 'links', r['link_fields_within_0_25_mm'], 'gate', r['gate_replaced_footprints_under_it'])
print(released)
