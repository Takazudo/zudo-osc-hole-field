#!/usr/bin/env python3
"""MC04-S7 Revision 5 item 2: pin the floorplan's unpinned parts to their poses before the K block move.

Before stage 7 the floorplan re-placed every package that design/partition/adopted-placement-pins.json does not pin
(added passives and diodes) on each regeneration, so any change in occupancy re-flowed them. This writes
design/partition/reflow-pins.json: each such package on JL, JR and K at its pose in the floorplan of the source commit
below, so only packages a moved block, a new GH header or an eviction displaces move. A swapped IC and its bypass
capacitors are recorded as one swapped cluster at their pre-move poses, which the floorplan takes before searching
from the swapped slot, and a pin the floorplan evicted keeps its pre-move re-placed pose when that pose is free. A protection diode (placed by
its locality rule) records its pre-move pose, which the floorplan tries first. Fixed panel parts, headers (from the
connector packing) and the K block members are left out. --check fails on drift."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'design/partition/reflow-pins.json'
SOURCE_COMMIT = '6093081c'  # the floorplan reviewed before the stage 7 move (Revision 5)
SOURCE_PATH = 'design/partition/floorplan-candidate.json'
BOARDS = ('JL', 'JR', 'K')
PROTECTION_DIODES = ('BAV199,215', 'BAT54S,215')


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def build():
    source = json.loads(git('show', f'{SOURCE_COMMIT}:{SOURCE_PATH}'))
    blob = git('rev-parse', f'{SOURCE_COMMIT}:{SOURCE_PATH}').strip()
    adopted = json.loads((ROOT / 'design/partition/adopted-placement-pins.json').read_text())
    pinned_rows = {(r['board'], r['ref']): r for r in adopted['pins']}
    pinned = set(pinned_rows)
    swapped = {r['ref'] for r in adopted['swapped_slots']}
    io = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    pk = {p['ref']: p for p in io['physical_packages']}
    reloc = json.loads((ROOT / 'design/partition/k-block-relocation.json').read_text())
    moved = {r for b in reloc['blocks'] for r in b['members']}
    rows = []
    for p in source['placements']:
        ref = p['ref']
        if p['board'] not in BOARDS or ref in moved:
            continue
        if p.get('fixed') or ref.startswith('J') or ref not in pk or pk[ref]['panel_uid']:
            continue
        if pk[ref]['mpn'] in PROTECTION_DIODES:
            # placed by its locality rule; the floorplan tries this pre-move pose first
            rows.append({'footprint': pk[ref]['footprint'], 'ref': ref, 'board': p['board'], 'fixed': False,
                         'x_mm': p['x_mm'], 'y_mm': p['y_mm'], 'rotation_deg': p['rotation_deg'], 'side': p['side'],
                         'courtyard_mm': p['courtyard_mm'], 'protection_pose': True})
            continue
        owner = ref if ref in swapped else pk[ref].get('decouples_ref') if pk[ref].get('decouples_ref') in swapped else None
        if owner:
            # a swapped cluster keeps its pre-move pose as one unit (the floorplan tries it before searching)
            rows.append({'footprint': pk[ref]['footprint'], 'ref': ref, 'board': p['board'], 'fixed': False,
                         'x_mm': p['x_mm'], 'y_mm': p['y_mm'], 'rotation_deg': p['rotation_deg'], 'side': p['side'],
                         'courtyard_mm': p['courtyard_mm'], 'swapped_cluster': owner})
            continue
        if (p['board'], ref) in pinned:
            pin = pinned_rows[(p['board'], ref)]
            if (pin['x_mm'], pin['y_mm'], pin['side'], pin['rotation_deg']) != (p['x_mm'], p['y_mm'], p['side'], p['rotation_deg']):
                # an evicted pin: the floorplan tries its pre-move re-placed pose first
                rows.append({'footprint': pin['footprint'], 'ref': ref, 'board': p['board'], 'fixed': False,
                             'x_mm': p['x_mm'], 'y_mm': p['y_mm'], 'rotation_deg': p['rotation_deg'], 'side': p['side'],
                             'courtyard_mm': p['courtyard_mm'], 'evicted_pose': True})
            continue
        rows.append({'footprint': pk[ref]['footprint'], 'ref': ref, 'board': p['board'], 'fixed': False,
                     'x_mm': p['x_mm'], 'y_mm': p['y_mm'], 'rotation_deg': p['rotation_deg'], 'side': p['side'],
                     'courtyard_mm': p['courtyard_mm'], 'reflow_pin': True})
    rows.sort(key=lambda r: (r['board'], r['ref']))
    return {'schema_version': 1,
            'status': 'REVIEWED SOURCE INPUT (MC04-S7 Revision 5 item 2): minimal reflow pins',
            'source': {'commit': SOURCE_COMMIT, 'path': SOURCE_PATH, 'git_blob': blob},
            'generator': 'scripts/partition/reflow_pins.py',
            'rule': __doc__.split('\n\n', 1)[1].replace('\n', ' ').strip(),
            'counts': {b: sum(1 for r in rows if r['board'] == b and r.get('reflow_pin')) for b in BOARDS},
            'evicted_pose_counts': {b: sum(1 for r in rows if r['board'] == b and r.get('evicted_pose')) for b in BOARDS},
            'swapped_cluster_counts': {b: sum(1 for r in rows if r['board'] == b and 'swapped_cluster' in r) for b in BOARDS},
            'protection_pose_counts': {b: sum(1 for r in rows if r['board'] == b and r.get('protection_pose')) for b in BOARDS},
            'pins': rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('reflow pins drift')
    else:
        OUT.write_text(text)
    print('reflow pins', json.loads(text)['counts'])


if __name__ == '__main__':
    main()
