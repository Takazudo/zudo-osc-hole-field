#!/usr/bin/env python3
"""MC04-S10 Revision 1 (DS-148): the link-era overlay rules over the canonical gate rows.

The gate replacement rows (link-gate.json `replacement`) are canonical for every displaced footprint. This generator
derives where the link-era record must overlay a block pose, in the current gate record:
1. ICs the gate leaves without a position: the ten link-era poses (S8 studies, DS-144) and the open ICs, re-checked in
   the new Field (member_faces.py repeats the check with the overlay applied);
2. ICs whose gate pose breaks the block rule (a decoupler on the other face, or farther from its IC than before) among
   the rows S10 added or shifted: their block is searched under the S8 rules (Revision 1 class (iii) with the A2 turns
   and displacement, face-aware, within 24 mm of its paper position) and the pose is recorded here;
3. the ruled parts (R5257, R5259, RV4503, RV8407) and RV2310: their positions and faces in the gate rows.

It also tabulates every row S10 changed against the snapshot record (8243acdf): removed, new and shifted rows with
face, distance from their own origin and DS-97 step, and the block rule for each IC they touch. Writes overlay.json;
--check verifies it. A stop condition sets `stop`."""
from __future__ import annotations
import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
S8 = ROOT / 'scripts/stack/studies/mc04_s8_replacement'
sys.path.insert(0, str(S8))
import replacement as rp  # noqa: E402
import replacement_r7 as r7  # noqa: E402
from replacement import p2, r2  # noqa: E402

OUT = HERE / 'overlay.json'
GATE = 'design/stack/geometry/links/link-gate.json'
RULED = {'R5257': ('U5210', 7.93), 'R5259': ('U5210', None)}
REAR = ('RV4503', 'RV8407', 'RV2310')
STOP_SUFFIX = ('_FB', '_SUM', '_SENSE')


class OV(r7.R7):
    snapshot = None       # the current gate record
    with_overlay = False  # this generator writes the overlay


def rows_of(gate):
    return {(r['board'], r['ref']): r for r in gate['replacement']['footprints']}


def where(s, rows, key):
    """(origin, face, how) of a footprint in a gate record: its gate row if it has a position, else its paper pose."""
    r = rows.get(key)
    if r and r['new'] is not None:
        return r['new'], r['new_face'], 'gate row'
    fp = s.fps[key]
    return fp['origin'], fp['side'], 'paper' if not r else 'no position'


def dist(a, b):
    return round(math.hypot(a[0] - b[0], a[1] - b[1]), 2)


def buffer_stop(s, key):
    """Why a newly displaced part is a stop under DS-148 (an input-buffer IC or a part on an FB/SUM/SENSE node), or None."""
    ref = key[1]
    if ref.startswith('U') and ref in s.buffer_ics:
        return 'input-buffer IC'
    nets = sorted({n for n in s.pins.get(ref, {}).values() if n and n.endswith(STOP_SUFFIX)})
    if nets:
        return 'part on %s' % ', '.join(nets)
    return None


BASE = '6e5716e7fc011e2f028982f645d18b8d802acb29'
PAPER = '6093081cc6d1fcbfc4e134e4dfa1861a3de39836'


def pinned(rev, path):
    return json.loads(subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{rev}:{path}']))


def effective_scene(s, rows, placements):
    """Resolve paper, gate, and retained block/passive placements in precedence order."""
    scene = {k: (fp['origin'], fp['side'], 'paper') for k, fp in s.fps.items()}
    for k, row in rows.items():
        scene[k] = (row['new'], row['new_face'], 'gate row')

    def place(b, ic, members, pose):
        if not pose:
            return
        for ref in members:
            same = s.fps[(b, ref)]['side'] == s.fps[(b, ic)]['side']
            face = pose['face'] if same else {'F': 'B', 'B': 'F'}[pose['face']]
            scene[b, ref] = (list(s.new_origin(b, ic, ref, pose)), face, f'{ic} block')

    for e in placements:
        b = e['board']
        place(b, e['ic'], e.get('members') or e['block'], e['pose'])
        for block in e.get('blocks_moved', []):
            place(b, block['ic'], block['members'], block)
        for m in e['passives_moved']:
            scene[b, m['ref']] = (m['origin'], m['face'], f"{e['ic']} displaced passive")
    return scene


def movement(s, before, after):
    ledger = []
    for (board, ref), (new, face, source) in sorted(after.items()):
        old, old_face, old_source = before[board, ref]
        if old == new and face == old_face:
            continue
        ledger.append({'board': board, 'ref': ref, 'before': old, 'after': new,
                       'from': old_face, 'to': face, 'before_source': old_source, 'after_source': source,
                       'distance_mm': dist(old, new) if old is not None and new is not None else None,
                       'nets': sorted({n for n in s.pins.get(ref, {}).values() if n})})
    return ledger


def locality(record, original, scene):
    ref = record['ref']
    b = record['board']
    start = original[b, ref]
    pos, face, source = scene[b, ref]
    initial = [start['x_mm'], start['y_mm'], start['side']]
    actual = [*pos, face + '.Cu'] if pos is not None else None
    measured = dist(initial, pos) if pos is not None else None
    def matches(a, b):
        # Gate records serialize XY to 0.01 mm. Ignore floating-point representation noise only.
        return a is not None and b is not None and a[2] == b[2] and math.dist(a[:2], b[:2]) < 1e-9
    valid = (matches(initial, record.get('pre_move_pose')) and matches(actual, record.get('pose'))
             and measured == record.get('distance_mm'))
    return {'baseline_pose': initial, 'effective_pose': actual, 'effective_source': source,
            'distance_mm_recorded': record.get('distance_mm'), 'distance_mm_recomputed': measured,
            'matches_sources': valid}


class Frozen(OV):
    snapshot = BASE


def build():
    s = OV()
    s.prepare()
    s.load_done()
    frozen = Frozen()
    ra, rb = frozen.rows, s.rows
    retained = pinned(BASE, 'design/stack/geometry/links/link-era-replacements.json')['placed']
    before = effective_scene(frozen, ra, retained)
    removed, new = sorted(set(ra) - set(rb)), sorted(set(rb) - set(ra))
    shifted = sorted(k for k in set(ra) & set(rb) if (ra[k]['new'], ra[k]['new_face']) != (rb[k]['new'], rb[k]['new_face']))
    stop = []

    def row(k, kind):
        r = rb.get(k) or ra.get(k)
        out = {'board': k[0], 'ref': k[1], 'change': kind, 'paper_face': s.fps[k]['side'], 'why': r['why']}
        if k in ra:
            out['before'] = {'face': ra[k]['new_face'], 'origin': ra[k]['new'], 'moved_mm': ra[k]['moved_mm'], 'step': ra[k]['step']}
        if k in rb:
            out['after'] = {'face': rb[k]['new_face'], 'origin': rb[k]['new'], 'moved_mm': rb[k]['moved_mm'], 'step': rb[k]['step']}
        return out
    table = [row(k, 'removed') for k in removed] + [row(k, 'new') for k in new] + [row(k, 'shifted') for k in shifted]
    for k in new:
        if rb[k]['new'] is None:
            stop.append('newly displaced %s %s has no gate position' % k)
    # the block rule for every IC with a new or shifted row, and every IC whose decoupler has one
    dec_of = {}
    for ref, p in s.pk.items():
        if p.get('decouples_ref'):
            dec_of.setdefault(p['decouples_ref'], []).append(ref)
    touched = sorted({k for k in new + shifted if k[1].startswith('U')} |
                     {(k[0], s.pk[k[1]]['decouples_ref']) for k in new + shifted if s.pk.get(k[1], {}).get('decouples_ref')})
    rule = []
    for key in touched:
        if key not in s.fps:
            continue
        b, ic = key
        io0, if0, h0 = where(s, ra, key)
        io1, if1, h1 = where(s, rb, key)
        decs = []
        for d in sorted(dec_of.get(ic, [])):
            dk = (b, d)
            if dk not in s.fps:
                continue
            o0, f0, _ = where(s, ra, dk)
            o1, f1, _ = where(s, rb, dk)
            decs.append({'ref': d, 'face_before': f0, 'face_after': f1, 'distance_before_mm': dist(o0, io0), 'distance_after_mm': dist(o1, io1),
                         'other_face_after': f1 != if1, 'farther': dist(o1, io1) > dist(o0, io0) + 1e-6})
        own_row = key in set(new) | set(shifted)
        breaks = [d for d in decs if d['other_face_after'] or d['farther']]
        rule.append({'board': b, 'ic': ic, 'ic_row': 'new' if key in new else 'shifted' if key in shifted else 'unchanged',
                     'ic_before': {'origin': io0, 'face': if0, 'how': h0}, 'ic_after': {'origin': io1, 'face': if1, 'how': h1},
                     'decouplers': decs, 'block_rule': 'holds' if not breaks else 'breaks',
                     'pose': 'overlay pose (searched below)' if breaks and own_row and h1 == 'gate row' else
                             'knock-on decoupler row, accepted as generated (DS-148)' if breaks else 'gate pose'})
    # overlay searches for the ICs whose own gate pose breaks the rule
    need = [(r['board'], r['ic']) for r in rule if r['pose'].startswith('overlay')]
    members = {}
    for key in need:
        dec, local, _ = s.block(*key)
        members[key] = [key[1]] + dec + local
    lifted = {(b, m) for (b, ic), ms in members.items() for m in ms}
    blocks = []
    for key in need:
        b, ic = key
        f = s.build_field(extra=lifted)
        for e in blocks:
            s.place(f, e['board'], e['ic'], e['members'], s.fps[(e['board'], e['ic'])]['side'], e['pose'])
            for m in e['passives_moved']:
                s.add_part(f, e['board'], m)
        s.members[key] = members[key]
        legal, disp, _ = s.search(f, b, ic)
        best = legal[0] if legal else None
        e = {'board': b, 'ic': ic, 'members': members[key], 'gate_pose': {'face': rb[key]['new_face'], 'origin': rb[key]['new'],
                                                                          'moved_mm': rb[key]['moved_mm'], 'step': rb[key]['step']},
             'rules': 'Revision 1 class (iii) with the A2 turns and displacement, face-aware, within 24 mm (MC04-S8)',
             'reason': next(r for r in rule if (r['board'], r['ic']) == key)['decouplers']}
        if best and best['moved_mm'] <= rp.LIMIT_MM:
            e.update({'pose': best, 'passives_moved': []})
        elif disp:
            e.update({'pose': {k: disp[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')}, 'passives_moved': disp['displaced_moves']})
        else:
            stop.append('the overlay search finds no pose within 24 mm for %s %s (nearest %s mm)' % (b, ic, best and best['moved_mm']))
            e.update({'pose': None, 'passives_moved': [], 'nearest_mm': best and best['moved_mm']})
        if e['pose']:
            e['pose'] = {k: e['pose'][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')}
            e['decouplers_after'] = [{'ref': d, 'face': s.mf(b, d, e['pose']['face']),
                                      'distance_mm': dist(s.new_origin(b, ic, d, e['pose']), e['pose']['origin'])}
                                     for d in members[key] if d in dec_of.get(ic, [])]
            e['electrical'] = s.facts(b, ic, e['pose'])
            e['timing_nodes'] = sorted({x['net'] for x in e['electrical'] for k in x['kind'] if 'timing node' in k})
        blocks.append(e)
    # S10 keeps the ten accepted S8 poses. Only unresolved gate rows may inherit them.
    current_retained = [e for e in retained if (e['board'], e['ic']) in rb and rb[e['board'], e['ic']]['new'] is None]
    after = effective_scene(s, rb, current_retained + blocks)
    changes = movement(s, before, after)
    overlay_refs = {(e['board'], m) for e in blocks for m in e['members']}
    overlay_refs.update((e['board'], m['ref']) for e in blocks for m in e['passives_moved'])
    displaced = set(new) | {(r['board'], r['ref']) for r in changes if (r['board'], r['ref']) in overlay_refs}
    for k in sorted(displaced):
        why = buffer_stop(s, k)
        if why:
            stop.append(f'newly displaced {k[0]} {k[1]}: {why}')
    # the ruled parts and the rear trimmers
    ruled = {}
    for ref, (ic, lim) in RULED.items():
        o, f, how = after['K', ref]
        io, ifc, _ = after['K', ic]
        ruled[ref] = {'position': o, 'face': f, 'how': how, 'ic': ic, 'ic_face': ifc, 'distance_to_ic_mm': math.dist(o, io),
                      'paper_distance_mm': math.dist(frozen.fps['K', ref]['origin'], frozen.fps['K', ic]['origin']),
                      'on_ic_face': f == ifc, 'limit_mm': lim,
                      'meets': f == ifc and (lim is None or math.dist(o, io) <= lim)}
        if not ruled[ref]['meets']:
            stop.append('%s does not meet its DS-147 condition' % ref)
    for ref in REAR:
        o, f, how = after['K', ref]
        ruled[ref] = {'position': o, 'face': f, 'how': how, 'rear': f == 'B'}
        if f != 'B':
            stop.append('%s is not on the rear face' % ref)
    trimmers = [{'ref': x['ref'], 'face_after': (x.get('after') or {}).get('face'), 'rear': (x.get('after') or {}).get('face') in (None, 'B')}
                for x in table if x['ref'].startswith('RV')]
    open_now = sorted(ref for (_, ref), (pos, _, _) in after.items() if pos is None)
    original = {(p['board'], p['ref']): p for p in pinned(PAPER, 'design/partition/floorplan-candidate.json')['placements']}
    studies = {r['ic']: r for r in pinned(BASE, 'scripts/stack/studies/mc04_s7_a0/blocks-function.json')['local_replacement']}
    changed = {(r['board'], r['ref']) for r in changes}
    figures = []
    for x in json.loads((ROOT / 'design/partition/locality-acceptances.json').read_text())['acceptances']:
        if 'ref' not in x:
            continue
        b = x.get('board', 'K')
        refs = {x['ref']} | set(x.get('moves_with', [])) | set((x.get('also_moves') or {}).get('members', [])) | \
            {p['ref'] for p in (x.get('also_moves') or {}).get('passives', [])}
        hit = sorted(r for r in refs if (b, r) in changed)
        row = {'ref': x['ref'], 'kind': x.get('kind'), 'parts_in_changed_rows': hit}
        if 'study_pose' in x:
            source = studies[x['ref']]
            row['scope'] = 'historical S7 study pose'
            row['matches_sources'] = (x['study_pose'] == {'origin_mm': source['legal_pose'],
                                    'turn_deg': source['turn_deg'], 'distance_mm': dist(source['current_origin'], source['legal_pose'])}
                                    and x['face'] == source['face'])
        else:
            row.update(locality(x, original, after))
            row['pre_s10_effective_pose'] = locality(x, original, before)['effective_pose']
        if not row['matches_sources']:
            stop.append(f"locality evidence for {x['ref']} differs from independent geometry")
        if hit:
            stop.append('acceptance %s names parts in changed rows: %s' % (x['ref'], ', '.join(hit)))
        figures.append(row)
    return {'schema_version': 1, 'model': rp.MODEL + ' (current gate record)',
            'status': 'MC04-S10 Revision 1 candidate diagnostic (DS-148)',
            'generator': 'scripts/stack/studies/mc04_s10_l13/overlay.py', 'base_commit': BASE, 'locality_baseline_commit': PAPER,
            'row_changes': {'counts': {'removed': len(removed), 'new': len(new), 'shifted': len(shifted)}, 'rows': table},
            'effective_movements': changes,
            'face_changes': [r for r in changes if r['from'] and r['to'] and r['from'] != r['to']],
            'disposition': 'STOP' if stop else 'REVIEW_REQUIRED',
            'block_rule': rule, 'blocks': blocks, 'ruled_parts': ruled, 'trimmers_in_changed_rows': trimmers,
            'without_a_position': open_now, 'acceptance_figures': figures, 'stop': stop}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('overlay.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s10_l13/overlay.py')
        print('overlay.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print(d['row_changes']['counts'], 'open', d['without_a_position'])
    for r in d['block_rule']:
        print(r['ic'], r['ic_row'], r['block_rule'], r['pose'], [(x['ref'], x['distance_before_mm'], x['distance_after_mm'], x['face_after']) for x in r['decouplers']])
    for e in d['blocks']:
        print('overlay', e['ic'], e['pose'], [m['ref'] for m in e['passives_moved']], e.get('decouplers_after'), e.get('timing_nodes'))
    print('ruled', {k: (v.get('face'), v.get('distance_to_ic_mm'), v.get('meets', v.get('rear'))) for k, v in d['ruled_parts'].items()})
    print('face changes', [(x['ref'], x['from'], x['to']) for x in d['face_changes']])
    print('STOP' if d['stop'] else 'no stop', d['stop'])


if __name__ == '__main__':
    main()
