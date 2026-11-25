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
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(S8))
import replacement as rp  # noqa: E402
import replacement_r7 as r7  # noqa: E402

OUT = HERE / 'overlay.json'
RULED = {'R5257': ('U5210', 7.93), 'R5259': ('U5210', None)}
REAR = ('RV4503', 'RV8407', 'RV2310')
STOP_SUFFIX = ('_FB', '_SUM', '_SENSE')


class OV(r7.R7):
    snapshot = None  # current gate


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


def movement(s, before, after, before_turns, after_turns):
    ledger = []
    for (board, ref), (new, face, source) in sorted(after.items()):
        old, old_face, old_source = before[board, ref]
        key = board, ref
        rotation_only = old == new and face == old_face
        if rotation_only and before_turns.get(key, 0) == after_turns.get(key, 0):
            continue
        ledger.append({'board': board, 'ref': ref, 'before': old, 'after': new,
                       'from': old_face, 'to': face, 'before_source': old_source, 'after_source': source,
                       'distance_mm': dist(old, new) if old is not None and new is not None else None,
                       'nets': sorted({n for n in s.pins.get(ref, {}).values() if n})})
        if rotation_only:
            ledger[-1].update(before_turn_deg=before_turns.get(key, 0), after_turn_deg=after_turns.get(key, 0))
    return ledger


def displaced_stops(s, new, changes, blocks):
    overlay_refs = {(e['board'], m) for e in blocks for m in e['members']}
    overlay_refs.update((e['board'], m['ref']) for e in blocks for m in e['passives_moved'])
    displaced = set(new) | {(r['board'], r['ref']) for r in changes if (r['board'], r['ref']) in overlay_refs}
    stops = []
    for k in sorted(displaced):
        why = buffer_stop(s, k)
        if why:
            stops.append(f'newly displaced {k[0]} {k[1]}: {why}')
    return stops


def locality(record, original, scene):
    ref = record['ref']
    b = record['board']
    start = original[b, ref]
    pos, face, source = scene[b, ref]
    initial = [start['x_mm'], start['y_mm'], start['side']]
    actual = [*pos, face + '.Cu'] if pos is not None else None
    measured = dist(initial, pos) if pos is not None else None
    def matches(a, b):
        # Ignore only floating-point representation noise when comparing coordinates.
        return a is not None and b is not None and a[2] == b[2] and math.dist(a[:2], b[:2]) < 1e-9
    valid = (matches(initial, record.get('pre_move_pose')) and matches(actual, record.get('pose'))
             and measured == record.get('distance_mm'))
    return {'baseline_pose': initial, 'effective_pose': actual, 'effective_source': source,
            'distance_mm_recorded': record.get('distance_mm'), 'distance_mm_recomputed': measured,
            'matches_sources': valid}


def verify_locality_inventory(current, accepted):
    """The frozen contract covers every row, its identity, figures and applicability conditions."""
    if current != accepted:
        raise ValueError(f'locality-acceptances.json differs from the complete accepted record at {BASE}')


def candidate_clearance(s, blocks, stop):
    from member_faces import block_rects, part_rect
    lifted = {(e['board'], ref) for e in blocks for ref in e['members']}
    lifted.update((e['board'], m['ref']) for e in blocks for m in e['passives_moved'])
    field = s.build_field(extra=lifted)
    for e in blocks:
        if not e['pose']:
            continue
        b, ic = e['board'], e['ic']
        blocked = []
        rects = block_rects(s, b, ic, e['members'], s.fps[b, ic]['side'], e['pose'])
        # A rigid block's own members form one unit. Check it against the field
        # before adding any member. Subsequent blocks and passives see it.
        for ref, face, rect in rects:
            why = field.blocked(b, face, rect, [])
            if why:
                blocked.append({'ref': ref, 'by': why})
        for ref, face, rect in rects:
            field.add(b, face, rect, [], ref)
        for m in e['passives_moved']:
            rect = part_rect(s, b, m)
            why = field.blocked(b, m['face'], rect, [])
            if why:
                blocked.append({'ref': m['ref'], 'by': why})
            field.add(b, m['face'], rect, [], m['ref'])
        e['candidate_courtyard_check'] = {'clear': not blocked, 'conflicts': blocked}
        if blocked:
            stop.append(f'candidate courtyard conflict in block {ic}')


def effective_turns(rows, placements):
    rotations = {k: 90 for k, r in rows.items() if r['turned']}
    for e in placements:
        if e['pose']:
            rotations.update({(e['board'], ref): e['pose']['turn_deg'] for ref in e.get('members') or e['block']})
        for nested in e.get('blocks_moved', []):
            rotations.update({(e['board'], ref): nested['turn_deg'] for ref in nested['members']})
        for passive in e['passives_moved']:
            rotations[e['board'], passive['ref']] = 0
    return rotations


def ancillary_geometry(s, record, scene, original, rotations, paper_fps):
    """Estimate lengths in the same units and precision as the accepted source."""
    from replacement_a2 import rot_pt
    from scripts.stack.studies.mc04_s7_r4.buffer_runs import pin_xy, ROUTE_FACTOR, PF_PER_MM
    b, ic = record['board'], record['ref']
    key = b, ic
    results = {}
    unavailable = {}
    original_by_ref = {ref: p for (_, ref), p in original.items()}
    lock = {p['uid']: p for p in s.inp['raw']['lock']['placements']}

    def check(label, expected, observed):
        results[label] = {'recorded': expected, 'recomputed': observed, 'matches': expected == observed}

    def current_pad(ref, pin):
        fp = s.fps[b, ref]
        pos, face, _ = scene[b, ref]
        if pos is None:
            return None
        xy = next(p['center'] for p in fp['pads'] if p['number'] == pin)
        dx, dy = xy[0] - fp['origin'][0], xy[1] - fp['origin'][1]
        if face != fp['side']:
            dx = -dx
        dx, dy = rot_pt((dx, dy), (0, 0), rotations.get((b, ref), 0))
        return pos[0] + dx, pos[1] + dy

    for run in record.get('input_runs', []):
        n = run['net']
        if 'input_passives_to_buffer_mm' not in run:
            continue
        pins = sorted((ref, pin) for ref in s.net_refs[n] for pin, net in s.pins[ref].items() if net == n)
        old = [pin_xy(ref, pin, original_by_ref, s.pk, lock) for ref, pin in pins]
        now = {(ref, pin): current_pad(ref, pin) for ref, pin in pins}
        if None in now.values() or None in old:
            unavailable[n] = 'required net pin has no effective or reference pose'
            continue
        old_run, new_run = ROUTE_FACTOR * s.hpwl(old), ROUTE_FACTOR * s.hpwl(list(now.values()))
        check(n + '.routed_estimate_mm', run['routed_estimate_mm'], round(new_run, 1))
        check(n + '.capacitance_estimate_pF', run['capacitance_estimate_pF'], round(new_run * PF_PER_MM, 1))
        check(n + '.pre_move_capacitance_estimate_pF', run['pre_move_capacitance_estimate_pF'], round(old_run * PF_PER_MM, 1))
        input_pin = next(xy for (ref, _), xy in now.items() if ref == ic)
        distances = {ref: round(math.dist(input_pin, xy), 1) for (ref, _), xy in now.items() if ref != ic}
        check(n + '.input_passives_to_buffer_mm', run['input_passives_to_buffer_mm'], distances)

    # The S8 study used footprint origins on each net, not pin centres.
    runs = list(record.get('grown_nets', [])) + [r for r in record.get('input_runs', []) if 'added_run_estimate_mm' in r]
    if 'output_run' in record:
        runs.append(record['output_run'])
    for run in runs:
        n = run['net']
        refs = sorted(r for r in s.net_refs[n] if (b, r) in scene)
        pts = [scene[b, r][0] for r in refs]
        if None in pts:
            unavailable[n] = 'net includes footprint without a candidate position'
            continue
        old_hp = s.hpwl([paper_fps[b, r]['origin'] for r in refs])
        length = ROUTE_FACTOR * s.hpwl(pts)
        check(n + '.added_run_estimate_mm', run['added_run_estimate_mm'], round(length - ROUTE_FACTOR * old_hp, 2))
        if 'routed_estimate_mm' in run:
            check(n + '.routed_estimate_mm', run['routed_estimate_mm'], round(length, 2))
        if 'capacitance_estimate_pF' in run:
            check(n + '.capacitance_estimate_pF', run['capacitance_estimate_pF'], round(length * PF_PER_MM, 2))
    if 'led' in record:
        led = record['led']
        actual = next(x for x in s.leds(b, ic, {'origin': scene[key][0]}) if x['led'] == led['ref'])
        for field in ('distance_before_mm', 'distance_after_mm'):
            check('led.' + field, led[field], actual[field])
    if 'also_moves' in record:
        nested = record['also_moves']
        for ref, expected in [(nested['block'], nested), *((m['ref'], m) for m in nested['passives'])]:
            pos, face, _ = scene[b, ref]
            check(ref + '.moved_mm', expected['moved_mm'], dist(paper_fps[b, ref]['origin'], pos))
            check(ref + '.face', expected['face'].split('.')[0], face)
            if 'origin' in expected:
                check(ref + '.origin', expected['origin'], pos)
            if 'turn_deg' in expected:
                check(ref + '.turn_deg', expected['turn_deg'], rotations.get((b, ref), 0))
    if 'diode_to_protected_pin_mm' in record:
        ref, _, pin = record['protected_pin'].split()[:3]
        pin = pin.rstrip(',')
        old_diode = pin_xy(ic, '3', original_by_ref, s.pk, lock)
        old_buffer = pin_xy(ref, pin, original_by_ref, s.pk, lock)
        check('diode_to_protected_pin_mm.slot', record['diode_to_protected_pin_mm']['slot'], dist(old_diode, old_buffer))
        check('diode_to_protected_pin_mm.pose', record['diode_to_protected_pin_mm']['pose'], dist(current_pad(ic, '3'), current_pad(ref, pin)))
        name, _, pin = record['guarded_gh_contact']['contact'].split()
        connector = next(c for c in s.inp['ci']['partition']['connectors'] if c['id'] == name)
        header = paper_fps[b, connector['pcb_reference']]
        gh = next(p['center'] for p in header['pads'] if p['number'] == pin)
        check('diode_to_gh_contact_mm.slot (interim board)', record['diode_to_gh_contact_mm']['slot'], dist(old_diode, gh))
        board_diode = next(p['center'] for p in paper_fps[key]['pads'] if p['number'] == '3')
        check('diode_to_gh_contact_mm.pose (interim board)', record['diode_to_gh_contact_mm']['pose'], dist(board_diode, gh))

    if 'turn_deg' in record:
        check('turn_deg', record['turn_deg'], rotations.get(key, 0))
    return results, unavailable


class Frozen(OV):
    snapshot = BASE


def build():
    s = OV()
    s.prepare()
    s.load_done()
    frozen = Frozen()
    frozen.prepare()
    ra, rb = frozen.rows, s.rows
    retained = pinned(BASE, 'design/stack/geometry/links/link-era-replacements.json')['placed']
    before = effective_scene(frozen, ra, retained)
    removed, new = sorted(set(ra) - set(rb)), sorted(set(rb) - set(ra))
    shifted = sorted(k for k in set(ra) & set(rb) if any(ra[k][field] != rb[k][field] for field in ('new', 'new_face', 'turned')))
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
    candidate_clearance(s, blocks, stop)
    rotations = effective_turns(rb, current_retained + blocks)
    baseline_turns = effective_turns(ra, retained)
    changes = movement(s, before, after, baseline_turns, rotations)
    stop.extend(displaced_stops(s, new, changes, blocks))
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
    acceptance_path = 'design/partition/locality-acceptances.json'
    current = json.loads((ROOT / acceptance_path).read_text())
    verify_locality_inventory(current, pinned(BASE, acceptance_path))
    for x in current['acceptances']:
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
        figures_checked, unavailable = ancillary_geometry(s, x, after, original, rotations, frozen.fps)
        baseline_figures, _ = ancillary_geometry(frozen, x, before, original, baseline_turns, frozen.fps)
        for label, value in figures_checked.items():
            value['pre_s10_effective'] = baseline_figures[label]['recomputed'] if label in baseline_figures else None
        row['ancillary_geometry'] = figures_checked
        row['not_run'] = unavailable
        if 'diode_to_gh_contact_mm' in x:
            row['scope_note'] = 'GH distances recomputed only for the interim board. The link scene omits the GH header.'
        if any(not v['matches'] for v in figures_checked.values()):
            stop.append(f"ancillary locality figures for {x['ref']} differ from effective geometry")
        if unavailable:
            stop.append(f"ancillary locality verification incomplete for {x['ref']}")
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
