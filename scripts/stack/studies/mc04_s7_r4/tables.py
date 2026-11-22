"""Part A tables from the regenerated floorplan against HEAD."""
import json
import math
import subprocess
import sys
from pathlib import Path
R = Path.home() / 'repos/circuits/zudo-osc-hole-field'
sys.path.insert(0, str(R))


def head(path):
    return json.loads(subprocess.run(['git', '-C', str(R), 'show', 'HEAD:' + path], capture_output=True, text=True, check=True).stdout)


new = json.loads((R / 'design/partition/floorplan-candidate.json').read_text())
old = head('design/partition/floorplan-candidate.json')
P1 = {p['ref']: p for p in new['placements']}
P0 = {p['ref']: p for p in old['placements']}
reloc = json.loads((R / 'design/partition/k-block-relocation.json').read_text())
io = json.loads((R / 'design/reports/io-partition.json').read_text())
pk = {p['ref']: p for p in io['physical_packages']}
out = {}
d = lambda a, b: round(math.hypot(a['x_mm'] - b['x_mm'], a['y_mm'] - b['y_mm']), 2)  # noqa: E731
blocks = []
for b in reloc['blocks']:
    ms = list(b['members'])
    oc = (sum(P0[m]['x_mm'] for m in ms) / len(ms), sum(P0[m]['y_mm'] for m in ms) / len(ms))
    ic1, ic0 = P1[b['ic']], P0[b['ic']]
    far = max(math.hypot(P1[m]['x_mm'] - ic1['x_mm'], P1[m]['y_mm'] - ic1['y_mm']) for m in ms)
    blocks.append({'ic': b['ic'], 'from': b['from_board'], 'old_board': ic0['board'], 'new_board': ic1['board'],
                   'k_pose': [ic1['x_mm'], ic1['y_mm'], ic1['side'], ic1.get('rotation_deg', ic1.get('rot_deg'))],
                   'ic_distance_from_old_ic_mm': d(ic1, ic0),
                   'ic_distance_from_old_block_centre_mm': round(math.hypot(ic1['x_mm'] - oc[0], ic1['y_mm'] - oc[1]), 2),
                   'members': len(ms), 'all_members_on_K': all(P1[m]['board'] == 'K' for m in ms),
                   'farthest_member_from_ic_mm': round(far, 2)})
out['blocks'] = blocks
kics = ['U1415', 'U4324', 'U4417', 'U4433', 'U4524', 'U4526', 'U4527', 'U4623', 'U4635', 'U5110', 'U5209', 'U5210', 'U8409', 'U4341']
out['k_ics'] = [{'ic': r, 'pose': [P1[r]['x_mm'], P1[r]['y_mm'], P1[r]['side']], 'moved_mm': d(P1[r], P0[r])} for r in kics]
moved = []
for r, p in P1.items():
    q = P0.get(r)
    if q is None:
        moved.append({'ref': r, 'note': 'new'}); continue
    if (p['board'], p['x_mm'], p['y_mm'], p['side']) != (q['board'], q['x_mm'], q['y_mm'], q['side']):
        moved.append({'ref': r, 'from': [q['board'], q['x_mm'], q['y_mm'], q['side']], 'to': [p['board'], p['x_mm'], p['y_mm'], p['side']],
                      'moved_mm': d(p, q) if p['board'] == q['board'] or {p['board'], q['board']} <= {'JL', 'JR', 'K'} else None})
out['moved_parts'] = sorted(moved, key=lambda m: -(m.get('moved_mm') or 0))
out['adopted'] = {b: {k: v for k, v in r.items() if k in ('released_by_k_block_move', 'released_under_gh_headers', 'release_rounds', 'window_released')}
                  for b, r in new['adopted_placement_pins']['boards'].items()}
pc = json.loads((R / 'design/partition/connector-packing-candidate.json').read_text())
sites = {(142, 122), (159, 122), (193, 24), (244, 24), (295, 24)}
out['new_headers'] = [{'id': h['id'], 'board': h['board'], 'center': h['center_mm'], 'side': h['side'], 'land': h['land_courtyard_mm']}
                      for h in pc['headers'] if tuple(h['center_mm']) in sites]
out['headers'] = {'by_board': pc['headers_by_board'], 'jack_sites_used': pc['jack_sites_used'], 'status': pc['status']}
Path(__file__).with_name('tables.json').write_text(json.dumps(out, indent=1))
print(json.dumps(out['blocks'], indent=0))
print(json.dumps(out['k_ics']))
print('moved parts', len(moved), [m['ref'] for m in out['moved_parts'][:60]])
print(json.dumps(out['adopted']))
print(json.dumps(out['new_headers']))
print(out['headers'])
