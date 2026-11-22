#!/usr/bin/env python3
"""MC04-S8 Revision 5: the link-era re-placement record.

Writes design/stack/geometry/links/link-era-replacements.json from the S8 studies under
scripts/stack/studies/mc04_s8_replacement (Parts A to A5): for every open re-placement of stage 7 that the rulings
place, its IC block pose (face, turn, origin, distance), the other IC blocks and passives it moves, and the ruling; for
any IC left open, the A5 proof and the cheapest option. These poses are a link-era record: they are searched in the
link gate's model and are applied only when the stack links replace the GH headers (Gate A). The interim GH boards do
not change (board_conflicts.py shows the poses do not fit them). links_gate.py copies this record into
link-gate.json. --check verifies it."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'scripts/stack/studies/mc04_s8_replacement'
OUT = ROOT / 'design/stack/geometry/links/link-era-replacements.json'
BRIEF = 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s8-open-replacement-native-brief-20261122.md'
MODEL = ('link-era model (links_gate_part2.Field, GH headers dropped, gate-displaced parts at paper positions); '
         'not checked against the interim boards')
SOURCES = ('result.json', 'result-a2.json', 'result-a3.json', 'result-a4.json', 'result-a5.json', 'board-conflicts.json')
RULED_A = ('U4129', 'U1415', 'U4433', 'U4526', 'U4527', 'U4623', 'U4635', 'U5110')


def read(name):
    return json.loads((STUDY / name).read_text())


def pose(c):
    return {k: c[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm') if k in c} | ({'turn_deg': c.get('turn_deg', 0)})


def build():
    a, a2, a3, a4, a5 = (read(n) for n in SOURCES[:5])
    A = {r['ic']: r for r in a['ics']}
    A2 = {r['ic']: r for r in a2['ics']}
    A3 = {r['ic']: r for r in a3['targets']}
    A4 = {r['ic']: r for r in a4['targets']}
    rows = []
    for ic in RULED_A:
        r = A[ic]
        rows.append({'board': r['board'], 'ic': ic, 'class': r['class'], 'pose': pose(r['chosen']), 'block': r['block']['members'],
                     'blocks_moved': [], 'passives_moved': r.get('displaced_moves', []), 'source': 'result.json (Part A)',
                     'ruling': BRIEF + ', Revision 1 item 1'})
    for ic, rev in (('U4524', 'Revision 2 item 1'), ('U1318', 'Revision 2 item 2'), ('U4417', 'Revision 2 item 3')):
        r = A2[ic]
        rows.append({'board': r['board'], 'ic': ic, 'class': r['class'], 'pose': pose(r['chosen']), 'block': r['block']['members'],
                     'blocks_moved': [], 'passives_moved': r['chosen'].get('displaced_moves', []), 'source': 'result-a2.json (Part A2)',
                     'ruling': BRIEF + ', ' + rev, 'acceptance': None if ic == 'U4524' else 'design/partition/locality-acceptances.json'})
    r = A3['U4647']
    rows.append({'board': r['board'], 'ic': 'U4647', 'class': 'block-on-block', 'pose': pose(r['pose']), 'block': r['block']['members'],
                 'blocks_moved': [dict(pose(b), ic=b['ic'], members=b['members']) for b in r['blocks_moved']],
                 'passives_moved': r['passives_moved'], 'source': 'result-a3.json (Part A3)', 'ruling': BRIEF + ', Revision 3 item 1',
                 'acceptance': 'design/partition/locality-acceptances.json'})
    r = A4['U5209']
    rows.append({'board': r['board'], 'ic': 'U5209', 'class': 'R8263 relaxation', 'pose': pose(r['pose']), 'block': r['block']['members'],
                 'blocks_moved': [], 'passives_moved': r['passives_moved'], 'source': 'result-a4.json (Part A4)',
                 'ruling': BRIEF + ', Revision 4'})
    run = next((x for x in a5['runs'] if x['found'] and set(x['targets']) <= set(a5['placed']) and x['targets']), None)
    for ic in a5['placed']:
        c = run['poses'][ic]
        rows.append({'board': 'K', 'ic': ic, 'class': 'joint search', 'pose': pose(c), 'block': None,
                     'blocks_moved': [dict(pose(v), ic=k) for k, v in sorted(run['poses'].items()) if k not in a5['placed'] and v['moved_mm'] > 0],
                     'passives_moved': run['passives_moved'], 'source': 'result-a5.json (Part A5)', 'ruling': BRIEF + ', Revisions 4 and 5'})
    blocks = {r['ic']: r['block'] for r in a['ics']}
    for row in rows:
        if row['block'] is None:
            row['block'] = blocks[row['ic']]['members']
    placed = {r['ic'] for r in rows}
    open_rows = []
    for r in a['ics']:
        if r['ic'] in placed:
            continue
        opt = next((o for o in a5['options_for_unplaced'] if o['for'] == r['ic']), None)
        open_rows.append({'board': r['board'], 'ic': r['ic'], 'status': 'OPEN (link era)',
                          'proof': {'run': 'joint search of %s within %g mm' % (', '.join(a5['runs'][0]['set']), a5['rules']['limit_mm']),
                                    'found': a5['runs'][0]['found'], 'nodes': a5['runs'][0]['nodes'],
                                    'domain_sizes': a5['runs'][0]['domain_sizes'], 'source': 'result-a5.json'},
                          'cheapest_option': None if opt is None else {
                              'neighbours_beyond_24mm': {k: v['moved_mm'] for k, v in opt.get('poses', {}).items()
                                                         if v['moved_mm'] > a5['rules']['limit_mm']},
                              'smallest_scanned_limit_mm': opt['limit_others_mm'], 'limits_scanned': opt['limits_scanned'],
                              'poses': {k: pose(v) for k, v in opt.get('poses', {}).items()},
                              'alternative_far_pose': opt['a2_far_pose'], 'swap': opt.get('swap')}})
    return {'schema_version': 1, 'model': MODEL,
            'status': 'LINK-ERA RE-PLACEMENT RECORD (MC04-S8 Revision 5): resolved for the link era, pending application when the '
                      'stack links replace the GH headers; the interim boards do not change',
            'generator': 'scripts/stack/geometry/link_era_replacements.py',
            'sources': {('scripts/stack/studies/mc04_s8_replacement/' + n): hashlib.sha256((STUDY / n).read_bytes()).hexdigest() for n in SOURCES},
            'evidence_interim_boards': 'scripts/stack/studies/mc04_s8_replacement/board_conflicts.py (--check): the poses overlap GH headers '
                                       'that exist on the interim boards',
            'placed': rows, 'open': open_rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('link-era-replacements.json is stale; regenerate with: python3 scripts/stack/geometry/link_era_replacements.py')
        print('link-era-replacements.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print('placed', len(d['placed']), 'open', [r['ic'] for r in d['open']])


if __name__ == '__main__':
    main()
