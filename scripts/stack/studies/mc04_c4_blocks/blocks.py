"""Task C step 4: can each unplaced JR IC move to K with its functional block, and what does it cost in links?

A block is the IC, its declared decouplers and its one-hop passive/diode signal neighbours that sit on JR, as in the
MC02 analog remedy brief (panel jacks and other ICs stay).
On K the IC goes nearest its original x/y (JR and K share the stack x/y frame) and each member nearest the IC, with
earlier parts blocking later ones. Signals: a non-power net crosses JR-K when it
has members on both boards; the change in crossing nets is counted for each block and for all six. Room and count
only: no electrical review, no allocation, no canonical write.

Current-scene mode (MC04-S7 Revision 1): --current uses the committed link gate scene (capacity.current_scene),
takes the block assignment from the command line (--move SRC:TGT:IC,IC[:FRAGMENT,FRAGMENT] and
--local BOARD:IC,IC), and refuses an assignment that does not name every unresolved IC of the current gate exactly
once or that names any other part. --local ICs stay on their own board and face and are re-placed nearest their
current position after the moved blocks have left. The pinned MC04-R1 path (no flag) is unchanged."""
import argparse
import collections
import copy
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_c1_capacity'))
import capacity as cap  # noqa: E402

CASES = (('JR', 'K', ('U4346', 'U4347', 'U4348', 'U8314', 'U8318', 'U8417')),
         ('JL', 'K', ('U1216', 'U1416', 'U1417', 'U1518', 'U2119', 'U2218')),
         ('JL', 'JL', ('U1216', 'U1416', 'U1417', 'U1518', 'U2119', 'U2218')),
         ('K', 'K', ('U1415', 'U4324', 'U4341', 'U4417', 'U4433', 'U4524', 'U4526', 'U4527', 'U4623', 'U4635',
                     'U5110', 'U5209', 'U5210', 'U8409')))
POWER = {'+12V', '-12V', '+5V', 'AGND'}  # the only global rails in io-partition.json
KEEP_FRONT = ()  # net-name fragments: a one-hop neighbour on any matching net stays on the source board (variant study)


def run():
    scene, unresolved, accepted = cap.scene_and_rows()
    want = {(c[0], ic) for c in CASES if c[0] != 'JL' or c[1] == 'K' for ic in c[2]}
    if accepted != 412 or {(r['board'], r['ref']) for r in unresolved} != want:
        raise ValueError('cumulative scene or unresolved set changed')
    cases = [case(scene, *c) for c in CASES]
    # All blocks onto K together: K's own blocks first (vacated), then JR's, then JL's, on one shared raster.
    shared = {}
    together = [case(scene, 'K', 'K', CASES[3][2], shared), case(scene, 'JR', 'K', CASES[0][2], shared),
                case(scene, 'JL', 'K', CASES[1][2], shared)]
    out = {'status': 'TASK_C_STEP_4_BLOCK_RELOCATION', 'cases': cases, 'all_on_K_together': together,
           'all_on_K_together_packed': all(c['all_blocks_packed'] for c in together)}
    if KEEP_FRONT:
        out['keep_front_net_fragments'] = list(KEEP_FRONT)
    return out


def parse_move(spec):
    """'SRC:TGT:IC,IC[:FRAG,FRAG]' -> (src, tgt, ics, keep_front fragments)."""
    parts = spec.split(':')
    if len(parts) not in (3, 4) or not all(parts[:3]):
        raise ValueError('bad --move: ' + spec)
    ics = tuple(x for x in parts[2].split(',') if x)
    kf = tuple(x for x in parts[3].split(',') if x) if len(parts) == 4 else ()
    return parts[0], parts[1], ics, kf


def parse_local(spec):
    board, _, ics = spec.partition(':')
    if not board or not ics:
        raise ValueError('bad --local: ' + spec)
    return board, tuple(x for x in ics.split(',') if x)


def check_assignment(unresolved, moves, local):
    """Every unresolved (board, IC) exactly once across moves and local; nothing else."""
    want = {(r['board'], r['ref']) for r in unresolved}
    named = [(src, ic) for src, _, ics, _ in moves for ic in ics] + [(b, ic) for b, ics in local for ic in ics]
    dup = sorted({x for x in named if named.count(x) > 1})
    extra = sorted(set(named) - want)
    missing = sorted(want - set(named))
    if dup or extra or missing:
        raise ValueError('assignment does not match the unresolved list of the current gate: duplicated %s, '
                         'not unresolved %s, unassigned %s' % (dup, extra, missing))


def turned(fp, turns):
    """The footprint turned by 90 degrees about its origin `turns` times (the gate's own turn)."""
    out = copy.deepcopy(fp)
    for _ in range(turns):
        if out['courtyard']:
            out['courtyard'] = [round(v, 4) for v in cap.r1.rp.turn(out['courtyard'], fp['origin'])]
        for pad in out['pads']:
            pad['bbox'] = [round(v, 4) for v in cap.r1.rp.turn(pad['bbox'], fp['origin'])]
    return out


def local_replacement(scene, board, ics, vacated, limit=4000):
    """Nearest pose on its own board and face for each IC in turn (earlier ones block later ones on the raster), at
    each of the four 90-degree turns; every pose confirmed by the exact predicate except the displacement cap."""
    own = {(board, ic) for ic in ics}
    masks = {}
    rows = []
    for ic in ics:
        fp = scene.bodies[(board, ic)]
        face = fp['side']
        if face not in masks:
            m, o = cap.blocked_mask(scene, board, face, vacated | own)
            masks[face] = (m.copy(), o)
        m, o = masks[face]
        ox, oy = fp['origin']
        per_turn, best = [], None
        for t in range(4):
            tfp = turned(fp, t)
            box = cap.footprint_box(tfp, 0)
            cands = sorted(cap.fits(m, o, box), key=lambda q: math.hypot(q[0] - ox, q[1] - oy))
            hit, tried = None, 0
            for x, y in cands[:limit]:
                tried += 1
                v = [h for h in scene._violations(board, tfp, x - ox, y - oy, vacated | own) if h != 'displacement cap']
                if not v:
                    hit = (x, y)
                    break
            d = math.hypot(hit[0] - ox, hit[1] - oy) if hit else None
            per_turn.append({'turn_deg': 90 * t, 'raster_candidates': len(cands), 'exact_checked': tried,
                             'pose': [round(hit[0], 3), round(hit[1], 3)] if hit else None,
                             'distance_mm': round(d, 2) if hit else None})
            if hit and (best is None or d < best[0]):
                best = (d, t, hit, box)
        box0 = cap.footprint_box(fp, 0)
        row = {'ic': ic, 'board': board, 'face': face, 'package': fp['lib'], 'current_origin': fp['origin'],
               'courtyard_mm': [round(box0[2] - box0[0], 2), round(box0[3] - box0[1], 2)], 'by_turn': per_turn}
        if best is None:
            row.update(legal_pose=None, turn_deg=None, distance_mm=None, within_24mm=False)
        else:
            d, t, (x, y), box = best
            i0 = max(0, int((x + box[0] - 0.35 - o[0]) / cap.STEP)); i1 = int(math.ceil((x + box[2] + 0.35 - o[0]) / cap.STEP))
            j0 = max(0, int((y + box[1] - 0.35 - o[1]) / cap.STEP)); j1 = int(math.ceil((y + box[3] + 0.35 - o[1]) / cap.STEP))
            m[i0:i1 + 1, j0:j1 + 1] = True
            row.update(legal_pose=[round(x, 3), round(y, 3)], turn_deg=90 * t, distance_mm=round(d, 2),
                       within_24mm=d <= 24.0)
        rows.append(row)
    return rows


def run_current(moves, local):
    scene, unresolved, accepted, hashes = cap.current_scene()
    check_assignment(unresolved, moves, local)
    cases = [case(scene, src, tgt, ics, keep_front=kf) for src, tgt, ics, kf in moves]
    shared = {}
    order = [m for m in moves if m[0] == m[1]] + [m for m in moves if m[0] != m[1]]
    together = [case(scene, src, tgt, ics, shared, keep_front=kf) for src, tgt, ics, kf in order]
    vacated = set(shared.get('_vacated', set()))
    for c in together:
        if c['from'] != c['to']:
            for b in c['blocks']:
                if b.get('k_face') and not b['members_without_room']:
                    vacated |= {(c['from'], r) for r in b['members']}
    loc = []
    for board, ics in local:
        loc += local_replacement(scene, board, ics, {v for v in vacated if v[0] == board})
    return {'status': 'MC04_S7_A0_BLOCKS_CURRENT_SCENE', 'scene': 'current committed link gate',
            'accepted_moves': accepted, 'unresolved': [r['board'] + ':' + r['ref'] for r in unresolved],
            'inputs_sha256': hashes,
            'assignment': {'moves': [{'from': a, 'to': b, 'ics': list(c), 'keep_front_net_fragments': list(d)}
                                     for a, b, c, d in moves],
                           'local': [{'board': b, 'ics': list(i)} for b, i in local]},
            'cases': cases, 'all_on_K_together': together,
            'all_on_K_together_packed': all(c['all_blocks_packed'] for c in together),
            'local_replacement': loc,
            'local_scope': ('Own board and face, each 90-degree turn, raster 0.25 mm with every block that moved off '
                            'that board vacated; nearest to the current position; exact predicate except the '
                            'displacement cap; room only.')}


def case(scene, src, tgt, ICS, shared=None, keep_front=None):
    kf = KEEP_FRONT if keep_front is None else tuple(keep_front)
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    pp = {x['ref']: x for x in part['physical_packages']}
    net_refs, ref_nets = collections.defaultdict(set), collections.defaultdict(set)
    for u in part['package_units']:
        for n in (u.get('pins') or {}).values():
            if n and n not in POWER:
                net_refs[n].add(u['ref']); ref_nets[u['ref']].add(n)
    board_of = {}
    for (b, ref), fp in scene.bodies.items():
        if ref not in scene.model.dropped.get(b, ()):
            board_of.setdefault(ref, set()).add(b)

    def block(ic):
        g = {ic} | {x['ref'] for x in part['physical_packages'] if x.get('decouples_ref') == ic}
        for n in ref_nets[ic]:
            for r in net_refs[n]:
                if any(k in m for m in ref_nets[r] for k in kf):
                    continue  # a part touching a kept net stays on the source board
                if r != ic and r in pp and r[0] in 'RCD' and not r.startswith('RV') and not pp[r]['courtyard'].get('through_hole'):
                    g.add(r)
        return sorted(r for r in g if board_of.get(r) == {src})

    def crossing_set(moved):
        out = set()
        for n, refs in net_refs.items():
            boards = set()
            for r in refs:
                for b in board_of.get(r, ()):
                    boards.add(tgt if (b == src and r in moved) else b)
            if src != tgt and {src, tgt} <= boards:
                out.add(n)
        return out

    def crossing(moved):
        n_cross = 0
        for n, refs in net_refs.items():
            boards = set()
            for r in refs:
                for b in board_of.get(r, ()):
                    boards.add(tgt if (b == src and r in moved) else b)
            n_cross += src != tgt and {src, tgt} <= boards
        return n_cross

    base = crossing(set())
    vacate = {(src, r) for ic in ICS for r in block(ic)} if src == tgt else set()
    taken = shared.setdefault('_taken', set()) if shared is not None else set()
    gone = shared.setdefault('_vacated', set()) if shared is not None else set()
    gone |= vacate
    if shared and 'F' in shared:
        masks = shared
    else:
        masks = {f: cap.blocked_mask(scene, tgt, f, vacate) for f in 'FB'}
        masks = {f: (m.copy(), o) for f, (m, o) in masks.items()}
        if shared is not None:
            shared.update(masks)
    def put(m, o, box, target):
        pts = cap.fits(m, o, box)
        if not pts:
            return None
        x, y = min(pts, key=lambda p: math.hypot(p[0] - target[0], p[1] - target[1]))
        i0 = max(0, int((x + box[0] - 0.35 - o[0]) / cap.STEP)); i1 = int(math.ceil((x + box[2] + 0.35 - o[0]) / cap.STEP))
        j0 = max(0, int((y + box[1] - 0.35 - o[1]) / cap.STEP)); j1 = int(math.ceil((y + box[3] + 0.35 - o[1]) / cap.STEP))
        m[i0:i1 + 1, j0:j1 + 1] = True
        return x, y

    rows, moved_all = [], set()
    for ic in ICS:
        members = block(ic)
        fp = scene.bodies[(src, ic)]
        ox, oy = fp['origin']
        orig_span = max(math.hypot(scene.bodies[(src, r)]['origin'][0] - ox, scene.bodies[(src, r)]['origin'][1] - oy)
                        for r in members)
        row = {'ic': ic, 'members': members, 'crossing_change_alone': crossing(set(members)) - base,
               'original_max_member_distance_mm': round(orig_span, 2)}
        best = None
        for f in 'BF':
            m, o = masks[f]
            pts = cap.fits(m, o, cap.footprint_box(fp, 0))
            if pts:
                x, y = min(pts, key=lambda p: math.hypot(p[0] - ox, p[1] - oy))
                d = math.hypot(x - ox, y - oy)
                if best is None or d < best[0]:
                    best = (d, f)
        if best is None:
            row['k_face'] = None; rows.append(row); continue
        f = best[1]
        m, o = masks[f]
        x, y = put(m, o, cap.footprint_box(fp, 0), (ox, oy))
        dist, missing, where, exact = [], [], {ic: [round(x, 3), round(y, 3)]}, []
        taken.add((src, ic))
        for r in members:
            if r == ic or (src, r) in taken:
                continue
            q = put(m, o, cap.footprint_box(scene.bodies[(src, r)], 0), (x, y))
            if q is None:
                missing.append(r)
            else:
                taken.add((src, r))
                where[r] = [round(q[0], 3), round(q[1], 3)]
                dist.append(math.hypot(q[0] - x, q[1] - y))
        for r, (px, py) in where.items():
            bfp = scene.bodies[(src, r)]
            hits = [h for h in scene._violations(tgt, dict(bfp, side=f), px - bfp['origin'][0], py - bfp['origin'][1],
                                                 gone | vacate | {(src, r)}) if h != 'displacement cap']
            if hits:
                exact.append({'ref': r, 'violations': hits})
        row.update(k_face=f, ic_k_origin=[round(x, 2), round(y, 2)], ic_shift_mm=round(best[0], 2),
                   positions=where, exact_predicate_violations=exact,
                   members_without_room=missing, max_member_distance_mm=round(max(dist), 2) if dist else 0.0,
                   mean_member_distance_mm=round(sum(dist) / len(dist), 2) if dist else 0.0)
        if not missing:
            moved_all |= set(members)
        rows.append(row)
    links = [l for l in json.loads((ROOT / 'design/stack/geometry/links/link-gate.json').read_text())['links']
             if not l.get('gone') and l['id'].startswith(src + '-K-')]
    after = crossing_set(moved_all)
    before = crossing_set(set())
    out = {'from': src, 'to': tgt, 'blocks': rows, 'all_blocks_packed': all(r.get('k_face') and not r['members_without_room'] for r in rows),
            'crossing_nets_before': base, 'crossing_change_all_placed_blocks': crossing(moved_all) - base,
            'src_link_unused_positions': sum(l['unused'] for l in links),
            'nets_newly_crossing': sorted(after - before), 'nets_no_longer_crossing': sorted(before - after),
            'scope': ('Greedy raster packing on K (0.25 mm, obstacles as the capacity census, 0.35 mm between placed '
                      'parts, no rotation; every position re-checked with the scene exact predicate except the displacement cap): the IC nearest its original x/y on the better face, then each '
                      'member nearest the IC on the same face; one-hop block boundary from the remedy brief (trimmers stay with the trimmer plan; a part shared by two blocks is placed once), not a '
                      'stability model; crossing-net count is not an allocation (class and ground rules not applied). '
                      'Room and count only.')}
    if keep_front is not None:
        out['keep_front_net_fragments'] = list(kf)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    ap.add_argument('--keep-front', nargs='*', default=[],
                    help='net-name fragments: one-hop neighbours on a matching net stay on the source board')
    ap.add_argument('--current', action='store_true', help='the committed gate scene; needs --move/--local')
    ap.add_argument('--move', action='append', default=[], help='SRC:TGT:IC,IC[:FRAGMENT,FRAGMENT] (--current)')
    ap.add_argument('--local', action='append', default=[], help='BOARD:IC,IC re-placed on their own board (--current)')
    a = ap.parse_args()
    KEEP_FRONT = tuple(a.keep_front)
    if a.current:
        if a.keep_front:
            ap.error('--current takes keep-front fragments per --move')
        result = run_current([parse_move(x) for x in a.move], [parse_local(x) for x in a.local])
    elif a.move or a.local:
        ap.error('--move/--local need --current')
    else:
        result = run()
    text = json.dumps(result, indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
