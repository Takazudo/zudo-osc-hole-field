#!/usr/bin/env python3
"""MC04-S7 Revisions 13 and 14: the Gate A open list, built from its sources.

Writes design/stack/gate-a-open-items.json from:
- design/partition/locality-acceptances.json: protection-locality items and interim-GH locality exceptions;
- design/stack/geometry/fixing-reach-exceptions.json: the four interim-GH reach exceptions and the sleeves-as-fixings
  candidate (option (b), not applied);
- scripts/checks/connector_packing35.py KNOWN_FIXING_CONFLICTS: header/fixing conflicts deferred to Gate A;
- design/stack/geometry/links/link-gate.json: the displaced footprints with no position (open re-placements, with
  their overlap on each link keep-out) and the slot drift of baseline links against the link gate of 93197a3e.
--check verifies the committed file."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = ROOT / 'design/stack/gate-a-open-items.json'
ACCEPT = 'design/partition/locality-acceptances.json'
REACH = 'design/stack/geometry/fixing-reach-exceptions.json'
GATE = 'design/stack/geometry/links/link-gate.json'
LINK_ERA = 'design/stack/geometry/links/link-era-replacements.json'
BASELINE_GATE = '93197a3e'  # the link gate before the stage 7 move (link-cluster-baseline.json)
GROWTH = json.loads((ROOT / 'design/stack/geometry/parameters.json').read_text())['obstacle_model']['own_face_courtyard_growth_mm']
RULINGS = 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-k-block-move-native-brief-20261121.md'


def read(path):
    return json.loads((ROOT / path).read_text())


def overlaps(rec, links):
    """Overlap (dx, dy) of a displaced courtyard with each keep-out rectangle of a link on its board."""
    c = rec['courtyard']
    out = []
    for l in links:
        g = l.get('geometry') or {}
        if rec['board'] == 'K':
            keys = [k for k in g if k.startswith('K_') or k == 'slot']
        elif rec['board'] == l['front_board']:
            keys = [k for k in g if k.startswith('front_') and k != 'front_tail_first' or k == 'slot']
        else:
            continue
        for k in sorted(keys):
            b = g[k]
            if not (isinstance(b, list) and len(b) == 4):
                continue
            dx = min(c[2], b[2]) - max(c[0], b[0]); dy = min(c[3], b[3]) - max(c[1], b[1])
            if dx > 1e-9 and dy > 1e-9:
                out.append({'link': l['id'], 'keepout': k, 'overlap_mm': [round(dx, 2), round(dy, 2)]})
            else:
                gap = (max(-dx, 0) ** 2 + max(-dy, 0) ** 2) ** 0.5
                if gap < GROWTH - 1e-9:
                    out.append({'link': l['id'], 'keepout': k, 'within_courtyard_growth_mm': round(gap, 2)})
    return out


def build():
    from scripts.checks.connector_packing35 import KNOWN_FIXING_CONFLICTS
    acc = read(ACCEPT)['acceptances']
    reach = read(REACH)
    gate = read(GATE)
    base = json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', f'{BASELINE_GATE}:{GATE}'], capture_output=True,
                                     check=True, text=True).stdout)
    items = []
    for a in acc:
        if a.get('kind') == 'interim_gh_protection_locality':
            items.append({'id': 'GA-PROT-' + a['ref'], 'kind': 'protection-locality', 'board': a['board'], 'ref': a['ref'],
                          'distance_from_slot_mm': a['distance_mm'], 'protected_pin': a['protected_pin'],
                          'diode_to_protected_pin_mm': a['diode_to_protected_pin_mm']['pose'], 'source': ACCEPT, 'ruling': a['ruling']})
    for a in acc:
        if a.get('kind') == 'interim_gh_led_drive_distance':
            items.append({'id': 'GA-LED-' + a['ref'], 'kind': 'interim-GH LED-drive distance', 'board': a['board'], 'ref': a['ref'],
                          'led': a['led'], 'distance_from_slot_mm': a['distance_mm'], 'source': ACCEPT, 'ruling': a['ruling']})
    for a in acc:
        if a.get('kind') == 'interim_gh_locality_exception':
            items.append({'id': 'GA-LOC-' + a['ref'], 'kind': 'interim-GH locality exception', 'board': a['board'], 'ref': a['ref'],
                          'distance_from_slot_mm': a['distance_mm'], 'cause': a['cause'], 'source': ACCEPT, 'ruling': a['ruling']})
    for r in reach['interim_gh_exceptions']:
        items.append({'id': 'GA-REACH-' + r['pair'], 'kind': 'interim-GH reach exception', 'pair': r['pair'], 'worst_mm': r['worst_mm'],
                      'nearest_fixing': r['K_side_nearest'][1], 'source': REACH, 'ruling': RULINGS + ', Revision 11'})
    b = reach['option_b_gate_a_candidate']
    items.append({'id': 'GA-REACH-SLEEVES', 'kind': 'fixing reach candidate', 'summary': b['proposal'], 'status': b['status'],
                  'figure': b['figure'], 'source': REACH, 'ruling': RULINGS + ', Revision 11'})
    for header, fixing in sorted(KNOWN_FIXING_CONFLICTS):
        items.append({'id': 'GA-FIX-%s-%s' % (header, fixing), 'kind': 'header/fixing conflict', 'header': header, 'fixing': fixing,
                      'source': 'scripts/checks/connector_packing35.py KNOWN_FIXING_CONFLICTS', 'ruling': RULINGS + ', Revision 8'})
    era = read(LINK_ERA) if (ROOT / LINK_ERA).exists() else {'placed': [], 'open': [], 'model': None}
    era_placed = {(x['board'], x['ic']): x for x in era['placed']}
    era_open = {(x['board'], x['ic']): x for x in era['open']}
    for r in gate['replacement']['footprints']:
        if r['new'] is None:
            row = {'id': 'GA-REPLACE-%s-%s' % (r['board'], r['ref']), 'kind': 'open re-placement (re-route)', 'board': r['board'],
                   'ref': r['ref'], 'package': r['package'], 'face': r['face'], 'old': r['old'], 'why': r['why'],
                   'overlaps': overlaps(r, gate['links']), 'source': GATE, 'ruling': RULINGS + ', Revisions 12 to 14'}
            k = (r['board'], r['ref'])
            if k in era_placed:
                row.update({'status': 'RESOLVED FOR THE LINK ERA (pending application when the links replace the GH headers)',
                            'link_era_pose': era_placed[k]['pose'], 'model': era['model'], 'record': LINK_ERA})
            elif k in era_open:
                row.update({'status': 'OPEN (link era)', 'proof': era_open[k]['proof'], 'cheapest_option': era_open[k]['cheapest_option'],
                            'model': era['model'], 'record': LINK_ERA})
            else:
                row['status'] = 'OPEN'
            items.append(row)
    bl = {x['id']: x for x in base['links']}
    for l in gate['links']:
        o = bl.get(l['id'])
        if o is None or (o.get('slot_centre'), o.get('direction')) == (l.get('slot_centre'), l.get('direction')):
            continue
        items.append({'id': 'GA-SLOT-' + l['id'], 'kind': 'slot drift', 'link': l['id'],
                      'baseline': {'slot_centre': o.get('slot_centre'), 'direction': o.get('direction')},
                      'current': {'slot_centre': l.get('slot_centre'), 'direction': l.get('direction')},
                      'members_unchanged': sorted(o['members']) == sorted(l['members']),
                      'note': 'stable_clusters keeps IDs and members, not slots; new pairs join within the 35 mm gate radius',
                      'source': GATE + ' against ' + BASELINE_GATE, 'ruling': RULINGS + ', Revision 14 item 6'})
    kinds = {}
    for i in items:
        kinds[i['kind']] = kinds.get(i['kind'], 0) + 1
    status = {}
    for i in items:
        if 'status' in i:
            status[i['status']] = status.get(i['status'], 0) + 1
    return {'schema_version': 1, 'status': 'OPEN LIST for the Gate A review (MC04-S7); items stay open until Gate A rules them',
            'generator': 'scripts/stack/gate_a_open_items.py', 'counts': kinds, 're_placement_status': status, 'items': items}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('gate-a-open-items.json is stale; regenerate with: python3 scripts/stack/gate_a_open_items.py')
    else:
        OUT.write_text(text)
    print('Gate A open items', json.loads(text)['counts'])


if __name__ == '__main__':
    main()
