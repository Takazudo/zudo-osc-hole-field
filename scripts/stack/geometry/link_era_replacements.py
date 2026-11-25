#!/usr/bin/env python3
"""MC04-S8 Revisions 5 to 8, DS-144 and MC04-S10 (DS-148): the link-era re-placement record.

Writes design/stack/geometry/links/link-era-replacements.json from the S8 studies under
scripts/stack/studies/mc04_s8_replacement: the ten confirmed poses (Parts A, A2 and A3) and, from the face-aware
re-search of Revision 7 (result-r7.json), the blocks that went back to OPEN (link era) with their proof and cheapest
option. These poses are a link-era record: searched in the link gate's model, applied only when the stack links
replace the GH headers (Gate A); the interim GH boards do not change (board_conflicts.py). links_gate.py copies this
record into link-gate.json. --check verifies it.

The S10 study is diagnostic. Only earlier ruled poses belong in placed. This generator records the S10
disposition and withheld blocks separately for Gate A."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / 'scripts/stack/studies/mc04_s8_replacement'
OVERLAY = ROOT / 'scripts/stack/studies/mc04_s10_l13/overlay.json'
GATE = ROOT / 'design/stack/geometry/links/link-gate.json'
DS148 = 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s10-l13-link-moves-generator-brief-20261122.md, Revision 1 (DS-148)'
OUT = ROOT / 'design/stack/geometry/links/link-era-replacements.json'
BRIEF = 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s8-open-replacement-native-brief-20261122.md'
MODEL = ('link-era model (links_gate_part2.Field, GH headers dropped, gate-displaced parts at paper positions); '
         'not checked against the interim boards')
SOURCES = ('result.json', 'result-a2.json', 'result-a3.json', 'result-a4.json', 'result-a5.json', 'result-r7.json',
           'board-conflicts.json', 'member-faces.json')
ACCEPTED_R8 = ('U4433', 'U4526')  # Revision 8 item 1: accepted unless a clock or RC timing node is found
ANALOG_R8 = ('U1415', 'U5110', 'U5209', 'U5210', 'U8409')
ACCEPTED_DS144 = ('U4433',)  # its own interim exception, recorded only when its member-face and board-conflict checks pass
DS144 = 'circuit/orchestration/campaigns/osc-stack-20261114/decisions.md, DS-144'
DS144_CONDITIONS = ['the /E4/CLOCK edge is checked against fact-flipflop-input-transition45 (component-ti-sn74hc74dr) at re-route',
                    'no E4 clock-load budget exists',
                    '25.5 mm exceeds the DS-88 25 mm radius, so it is an interim Gate A item (GA-LOC-U4433)']
REMEDIES = ['a slot move', 'a package split', 'a partition change', 'the far pose with an electrical budget']


def read(name):
    return json.loads((STUDY / name).read_text())


def pose(c):
    out = {k: c[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm') if k in c}
    out.setdefault('turn_deg', 0)
    return out


def status_of(ic):
    return 'OPEN (link era): NEEDS_DESIGN for Gate A-paper' if ic in ANALOG_R8 else 'OPEN (link era)'


def ds144_checks(ic, members):
    """DS-144 condition 1: the member-face check (member-faces.json) and the board-conflict check (board-conflicts.json)
    of the accepted pose. The board check passes when the block meets only GH headers the link model drops."""
    mf = next((x for x in read('member-faces.json')['blocks'] if x['ic'] == ic), None)
    hits = [h for h in read('board-conflicts.json')['overlaps'] if h['board'] == 'K' and h['moved'] in members]
    other = [h for h in hits if not h['kind'].startswith('GH header')]
    return {'member_faces': {'checked': mf is not None, 'all_clear': bool(mf and mf['all_clear']), 'source': 'member-faces.json (computed)'},
            'board_conflicts': {'gh_headers_met': sorted({h['overlaps'] for h in hits if h['kind'].startswith('GH header')}),
                                'other_conflicts': other, 'pass': not other, 'source': 'board-conflicts.json'},
            'pass': bool(mf and mf['all_clear']) and not other}


def build():
    a, a2, a3, a4, a5, r7 = (read(n) for n in SOURCES[:6])
    PASSIVE_OVERLAP = tuple(r7['withdrawn_for_passive_overlap'])  # derived by the check in replacement_r7.py
    CONFIRMED_A = tuple(ic for ic in r7['confirmed_first'] if ic in {x['ic'] for x in a['ics']} and ic not in
                        set(r7['withdrawn_mixed_face']) | set(PASSIVE_OVERLAP) and ic not in ('U4524', 'U1318', 'U4417') and ' ' not in ic)
    A = {r['ic']: r for r in a['ics']}
    A2 = {r['ic']: r for r in a2['ics']}
    A3 = {r['ic']: r for r in a3['targets']}
    A4 = {r['ic']: r for r in a4['targets']}
    A5 = a5
    rows = []
    for ic in CONFIRMED_A:
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
    # Revision 7: the face-aware re-search; any block that does not land goes back to OPEN
    previous = {ic: ('result.json (Part A)', A[ic]['chosen']) for ic in tuple(r7['withdrawn_mixed_face']) + PASSIVE_OVERLAP}
    previous.update({
                'U5209': ('result-a4.json (Part A4)', A4['U5209']['pose']),
                'U5210': ('result-a5.json (Part A5)', next(x for x in A5['runs'] if x['found'] and x['targets'] == ['U5210'])['poses']['U5210'])})
    reasons = {'mixed': 'other-face block members collide at that pose (member-faces check, Revision 6)',
               'overlap': 'Part A moved its displaced passives before placing the block, so they landed on the block (member check, Revision 7)'}
    why = {ic: '; '.join(([reasons['mixed']] if ic in r7['withdrawn_mixed_face'] else []) +
                         ([reasons['overlap']] if ic in PASSIVE_OVERLAP else []))
           for ic in set(r7['withdrawn_mixed_face']) | set(PASSIVE_OVERLAP)}
    open_rows = []
    for r in r7['research']:
        prev = previous[r['ic']]
        if r['result'] != 'lands' and r['ic'] in ACCEPTED_R8:
            timing = sorted({e['net'] for e in r['cheapest_option']['electrical'] for k in e['kind'] if 'timing node' in k})
            if not timing:
                rows.append({'board': r['board'], 'ic': r['ic'], 'class': 'link-era logic locality exception', 'pose': pose(r['cheapest_option']['pose']),
                             'block': A[r['ic']]['block']['members'], 'blocks_moved': [], 'passives_moved': [],
                             'source': 'result-r7.json (Revision 7 cheapest option)', 'reason': 'accepted beyond 24 mm, Revision 8 item 1',
                             'timing_check': 'no clock input and no RC timing node', 'acceptance': 'design/partition/locality-acceptances.json',
                             'replaces': {'source': prev[0], 'pose': pose(prev[1]),
                                          'why': 'Part A moved its displaced passives before placing the block, so they landed on the block (member check, Revision 7)'},
                             'ruling': BRIEF + ', Revision 8 item 1',
    })
                continue
            checks = ds144_checks(r['ic'], A[r['ic']]['block']['members']) if r['ic'] in ACCEPTED_DS144 else None
            if checks and checks['pass']:
                rows.append({'board': r['board'], 'ic': r['ic'], 'class': 'link-era logic exception (DS-144, its own exception)',
                             'pose': pose(r['cheapest_option']['pose']), 'block': A[r['ic']]['block']['members'], 'blocks_moved': [],
                             'passives_moved': [], 'source': 'result-r7.json (Revision 7 cheapest option)',
                             'reason': 'accepted beyond 24 mm as its own interim exception (DS-144), not on the U4417 terms',
                             'timing_check': 'timing nodes %s: clock input accepted by DS-144 with conditions' % ', '.join(timing),
                             'conditions': DS144_CONDITIONS, 'ds144_checks': checks,
                             'acceptance': 'design/partition/locality-acceptances.json',
                             'replaces': {'source': prev[0], 'pose': pose(prev[1]),
                                          'why': 'Part A moved its displaced passives before placing the block, so they landed on the block (member check, Revision 7)'},
                             'ruling': DS144})
                continue
            r = dict(r, not_accepted='timing node on %s (Revision 8 item 1: left OPEN%s)' % (
                ', '.join(timing), '; DS-144 checks did not pass' if checks else ''))
        if r['result'] == 'lands':
            rows.append({'board': r['board'], 'ic': r['ic'], 'class': r.get('class') or 'block-on-block', 'pose': pose(r['pose']),
                         'block': A[r['ic']]['block']['members'], 'blocks_moved': r.get('blocks_moved', []),
                         'passives_moved': r.get('passives_moved', []), 'source': 'result-r7.json (Revision 7)', 'reason': r['reason'],
                         'replaces': {'source': prev[0], 'pose': pose(prev[1]),
                                      'why': why.get(r['ic'], 'other-face block members collide at that pose (member-faces check, Revision 6)')},
                         'ruling': BRIEF + ', Revision 7'})
            continue
        open_rows.append({'board': r['board'], 'ic': r['ic'], 'status': status_of(r['ic']), 'rules': r['rules'],
                          **({'not_accepted': r['not_accepted']} if r.get('not_accepted') else {}),
                          **({'gate_a_paper': {'remedies_to_weigh': REMEDIES, 'evaluated': False}} if r['ic'] in ANALOG_R8 else {}),
                          'withdrawn_pose': {'source': prev[0], 'pose': pose(prev[1]),
                                             'why': why.get(r['ic'], 'other-face block members collide at that pose (member-faces check, Revision 6)')},
                          'proof': r['proof'], 'smallest_obstacle_set': r.get('smallest_obstacle_set'),
                          'cheapest_option': r.get('cheapest_option'), 'source': 'result-r7.json (Revision 7)'})
    j = r7['joint']
    run0 = j['runs'][0]
    for t in ('U5210', 'U8409'):
        if t in j['placed']:
            continue
        opt = next((o for o in j['options_for_unplaced'] if o['for'] == t), None)
        row = {'board': 'K', 'ic': t, 'status': status_of(t), 'rules': 'the A5 joint search (Revision 4), face-aware',
               'gate_a_paper': {'remedies_to_weigh': REMEDIES, 'evaluated': False},
               'proof': {'run': 'joint search of %s within 24 mm' % ', '.join(run0['set']), 'grid_caveat': opt['grid_caveat'] if opt else None,
                         'found': run0['found'], 'nodes': run0['nodes'], 'domain_sizes': run0['domain_sizes'],
                         'alone': [{'targets': x['targets'], 'found': x['found'], 'domain_sizes': x['domain_sizes']} for x in j['runs'][1:]],
                         'neighbour_limits_scanned': opt['limits_scanned'] if opt else None, 'source': 'result-r7.json'},
               'cheapest_option': j['far_poses'].get(t), 'source': 'result-r7.json (Revision 7)'}
        if t == 'U5210':
            row['withdrawn_pose'] = {'source': previous['U5210'][0], 'pose': pose(previous['U5210'][1]),
                                     'why': 'other-face block members collide at that pose (member-faces check, Revision 6)'}
        open_rows.append(row)
    ov = json.loads(OVERLAY.read_text())
    if ov.get('disposition') != ('STOP' if ov['stop'] else 'REVIEW_REQUIRED'):
        raise ValueError('S10 diagnostic has an unknown or inconsistent disposition')
    gate_rows = {(r['board'], r['ref']): r for r in json.loads(GATE.read_text())['replacement']['footprints']}
    open_now = {k for k, r in gate_rows.items() if r['new'] is None}
    resolved = [{'board': o['board'], 'ic': o['ic'], 'status': 'At paper position in the S10 candidate gate',
                 'ruling': DS148} for o in open_rows if (o['board'], o['ic']) not in open_now]
    open_rows = [o for o in open_rows if (o['board'], o['ic']) in open_now]
    rows = [r for r in rows if (r['board'], r['ic']) in open_now]
    mfd = read('member-faces.json')
    faces = {(x['board'], x['ic']): x for x in mfd['blocks']}
    for row in rows:
        mf = faces[(row['board'], row['ic'])]
        row['member_face_check'] = {'other_face_members': len(mf['other_face_members']), 'all_clear': mf['all_clear'],
                                    'blocked': mf['blocked_members'] + [p for p in mf['passives'] if p['blocked_by']],
                                    'source': 'member-faces.json (computed)'}
    for o in open_rows:
        o['far_option_overlaps'] = [p['b'] if p['a'] == o['ic'] else p['a'] for p in mfd['far_option_overlaps'] if o['ic'] in (p['a'], p['b'])]
        if o['far_option_overlaps']:
            o['far_option_note'] = ('this far option overlaps the far options of %s: the options are alternatives, not one joint solution'
                                    % ', '.join(o['far_option_overlaps']))
    for row in rows:
        for m in row['passives_moved']:
            if m['ref'] == 'C5210':
                m['note'] = 'F to B flip adds a via on /W1/AC_NODE, which the HPWL run metric does not count'
    return {'schema_version': 1, 'model': MODEL,
            'status': 'S8 link-era placements checked against the S10 candidate gate. S10 overlay poses are withheld pending independent acceptance.',
            'generator': 'scripts/stack/geometry/link_era_replacements.py',
            'sources': {('scripts/stack/studies/mc04_s8_replacement/' + n): hashlib.sha256((STUDY / n).read_bytes()).hexdigest() for n in SOURCES},
            'evidence_interim_boards': 'scripts/stack/studies/mc04_s8_replacement/board_conflicts.py (--check): the poses overlap GH headers '
                                       'that exist on the interim boards',
            'overlay_source': {'scripts/stack/studies/mc04_s10_l13/overlay.json': hashlib.sha256(OVERLAY.read_bytes()).hexdigest()},
            'placed': rows, 'open': open_rows, 'not_displaced_after_s10': resolved,
            's10': {'disposition': ov['disposition'], 'stop': ov['stop'],
                    'withheld_overlay_ics': sorted(e['ic'] for e in ov['blocks']),
                    'row_changes': ov['row_changes']['counts'], 'face_changes': ov['face_changes'], 'ruled_parts': ov['ruled_parts'],
                    'knock_on_block_rule': [r for r in ov['block_rule'] if r['pose'].startswith('knock-on')]}}


def checked_record(path):
    """Validate before embedding placements in the gate or resolving a Gate A item from them."""
    record = json.loads(path.read_text())
    if record != build():
        raise ValueError('Stale or unapproved placement in link-era-replacements.json')
    return record


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
