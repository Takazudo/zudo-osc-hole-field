#!/usr/bin/env python3
"""MC04-S9-A: slot-move (R1) and package-room (R2) study for U1415, U5110, U5209, U5210 and U8409.

Study only (DS-145): no canonical geometry, spec, BOM, board or gate change. Brief:
circuit/orchestration/campaigns/osc-stack-20261114/mc04-s9-a-slot-move-study-brief-20261122.md.

Model: link-era (links_gate_part2.Field, GH headers dropped, gate-displaced parts at paper positions), with every
placed link-era pose applied as replacement_r7.R7 applies them (the confirmed poses, the Revision 7 poses, the Revision 8
acceptance and the DS-144 acceptance).

Arm 0 (premise): the Field holds no keep-out of a dissolved (`gone`) link, and replacement_r7 rebuilds result-r7.json
byte for byte (its five OPEN results included).

Arm 1 (R1): for each target IC in the ruled order, the named P-K link(s) are searched again with the retained search
(links_gate.search, the record's size, cable and connector, the retained 24 mm search radius about the link's recorded
search centre) on the 2.0, 0.5 and 0.25 mm grids. A candidate is accepted when it keeps the retained class-distance accept
of its members, every hosted rider within its class distance, the cable within its stock length (loop >= 0), the K-field
compliance at or below the DS-87 limit, and clears the target block at its recorded position (members at the courtyard
growth of the obstacle model). Accepted candidates are evaluated cheapest first, up to CAP per grid, in the full scene:
every footprint the moved link newly covers on K or P (the retained displaced rule for footprints at their paper
position; the courtyard growth for re-placed parts) and every part on the target's recorded area is re-placed under the
S8 rules (own face, then the other face for a surface-mount part on K, within 24 mm of its paper position, each placed
part an obstacle). A candidate is clean when every such part finds a place, no placed link-era block and no input-buffer
block moves, and the target block is legal at its recorded position. The first clean candidate of a link is fixed before
the next link. The chosen moves are verified together in one scene.

Arm 2 (R2, room only): the links stay at the record. The target IC's courtyard is swapped for the repository TSSOP-14
courtyard (same origin, angle and side), its block kept, and the S8 search (Revision 1 class (iii) rules with the A2 turns
and displacement, face-aware) runs within 24 mm. Rows are labelled ROOM ONLY, NO PART SELECTED. A combined column (arms 1
and 2) runs only for ICs that fail both.

Writes result.json beside this file; --check verifies it."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
S8 = ROOT / 'scripts/stack/studies/mc04_s8_replacement'
sys.path.insert(0, str(S8))
import replacement as rp  # noqa: E402
import replacement_r7 as r7  # noqa: E402
from replacement import lg, p2, sg, r2  # noqa: E402

OUT = HERE / 'result.json'
BRIEF = 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s9-a-slot-move-study-brief-20261122.md'
BASE = '5c8e23b9'
GATE = 'design/stack/geometry/links/link-gate.json'
ERA = 'design/stack/geometry/links/link-era-replacements.json'
TSSOP = 'footprints/kicad/zudo-osc-hole-field.pretty/TSSOP-14_4.4x5mm_P0.65mm.kicad_mod'
SOIC = 'footprints/kicad/zudo-osc-hole-field.pretty/SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod'
INPUT_FILES = (GATE, ERA, 'scripts/stack/geometry/links_gate.py', 'scripts/stack/geometry/links_gate_part2.py',
               'design/partition/locality-acceptances.json', 'design/grid/placements.lock.json', TSSOP, SOIC)
INPUT_DIRS = ('scripts/stack/studies/mc04_s8_replacement', 'scripts/stack/studies/mc04_c2b_link_shift_replace',
              'scripts/stack/studies/mc04_c2c_moved_link_checks')
TARGETS = (('U5209', ('P-K-P-L13.01.01.02',)), ('U5110', ('P-K-P-L12.02.01.02',)), ('U8409', ('P-K-P-L03.01',)),
           ('U5210', ('P-K-P-L13.01.01.01',)), ('U1415', ('P-K-P-L07', 'P-K-P-L08')))
R2_ORDER = ('U8409', 'U5210', 'U1415')  # DS-145: R2 is weighed after R1 for these three; the room check runs for all five
GRIDS = (2.0, 0.5, 0.25)
CAP = 24          # accepted candidates evaluated in the full scene per link and grid, cheapest first
PAIR_CAP = 4      # U1415: clean P-K-P-L07 candidates each tried with a P-K-P-L08 search
TIME_CEILING_S = 4 * 3600
LIMIT = rp.LIMIT_MM


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git_show(rev, path):
    return subprocess.run(['git', '-C', str(ROOT), 'show', f'{rev}:{path}'], capture_output=True, check=True).stdout


def blob(path):
    """A file as of the study's snapshot (MC04-S10: this study is a record of the model before the S10 link moves)."""
    return git_show(rp.SNAPSHOT, path)


def input_pins():
    """SHA-256 of every input (as of the snapshot), and the comparison of the two record files against the ruled commit."""
    pins = {p: hashlib.sha256(blob(p)).hexdigest() for p in INPUT_FILES}
    for d in INPUT_DIRS:
        names = subprocess.run(['git', '-C', str(ROOT), 'ls-tree', '--name-only', rp.SNAPSHOT, d + '/'],
                               capture_output=True, check=True, text=True).stdout.split()
        for f in sorted(names):
            if Path(f).suffix in ('.py', '.json', '.md'):
                pins[f] = hashlib.sha256(blob(f)).hexdigest()
    gate_now, gate_base = json.loads(blob(GATE)), json.loads(git_show(BASE, GATE))
    era_now, era_base = json.loads(blob(ERA)), json.loads(git_show(BASE, ERA))
    same_links = gate_now['links'] == gate_base['links'] and gate_now['replacement'] == gate_base['replacement']
    strip = lambda rows: [r for r in rows if r['ic'] != 'U4433']  # noqa: E731
    plain = lambda rows: [{k: v for k, v in r.items() if k != 'member_face_check'} for r in rows]  # noqa: E731
    era_diff = sorted({r['ic'] for r in era_now['placed']} ^ {r['ic'] for r in era_base['placed']})
    same_era = (plain(strip(era_now['placed'])) == plain(strip(era_base['placed'])) and
                strip(era_now['open']) == [{k: v for k, v in r.items()} for r in strip(era_base['open'])])
    return pins, {'commit': BASE,
                  'link_gate_sha256_at_commit': hashlib.sha256(git_show(BASE, GATE)).hexdigest(),
                  'link_era_sha256_at_commit': hashlib.sha256(git_show(BASE, ERA)).hexdigest(),
                  'links_and_replacement_unchanged': same_links,
                  'link_era_rows_changed': era_diff,
                  'link_era_other_rows_unchanged': same_era,
                  'note': ('since the ruled commit the link-gate links and gate re-placement are unchanged; the record differs only by '
                           'U4433, recorded as its own exception (DS-144) by the separate commit this brief orders, and the Gate A '
                           'list no longer cites dissolved links')}


# ---------------------------------------------------------------- footprint geometry (arm 2)

def kicad_geometry(path):
    text = (ROOT / path).read_text()
    pads = {}
    for m in re.finditer(r'\(pad "(\d+)" smd \w+\s*\(at ([-\d.]+) ([-\d.]+)', text):
        pads[m.group(1)] = (float(m.group(2)), float(m.group(3)))
    xs, ys = [], []
    for m in re.finditer(r'\(fp_line \(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(layer "F.CrtYd"\)', text):
        xs += [float(m.group(1)), float(m.group(3))]
        ys += [float(m.group(2)), float(m.group(4))]
    return pads, [min(xs), min(ys), max(xs), max(ys)]


MAPS = [((a, b), (c, d)) for a, b, c, d in ((1, 0, 0, 1), (-1, 0, 0, 1), (1, 0, 0, -1), (-1, 0, 0, -1),
                                            (0, 1, 1, 0), (0, -1, 1, 0), (0, 1, -1, 0), (0, -1, -1, 0))]


def placement_map(fp, local_pads):
    """The signed axis map (local -> board, about the origin) that carries the library pad centres onto the board pads."""
    o = fp['origin']
    board = {p['number']: ((p['bbox'][0] + p['bbox'][2]) / 2 - o[0], (p['bbox'][1] + p['bbox'][3]) / 2 - o[1]) for p in fp['pads']}
    for (a, b), (c, d) in MAPS:
        if all(abs(a * x + b * y - board[n][0]) < 0.02 and abs(c * x + d * y - board[n][1]) < 0.02 for n, (x, y) in local_pads.items()):
            return (a, b), (c, d)
    raise ValueError('no axis map for %s' % fp['ref'])


def mapped_rect(rect, m, origin):
    (a, b), (c, d) = m
    pts = [(a * x + b * y, c * x + d * y) for x in (rect[0], rect[2]) for y in (rect[1], rect[3])]
    return [round(origin[0] + min(p[0] for p in pts), 4), round(origin[1] + min(p[1] for p in pts), 4),
            round(origin[0] + max(p[0] for p in pts), 4), round(origin[1] + max(p[1] for p in pts), 4)]


# ---------------------------------------------------------------- scene

class Collector:
    def __init__(self):
        self.items = []

    def add(self, board, face, rect, pads, ref):
        self.items.append((board, face, [round(v, 4) for v in rect], ref))


def link_rects(geo, front, latch):
    """The keep-outs a placed link puts into links_gate_part2.Field (board, face, rect, what)."""
    return [(front, 'B', geo['front_connector'], 'front field'), (front, 'B', geo['front_tail'], 'front tail'),
            (front, 'B', geo['slot'], 'slot'), ('K', 'B', geo['K_connector'], 'K field'), ('K', 'B', geo['K_tail'], 'K tail'),
            ('K', 'B', geo['slot'], 'slot'), ('K', 'B', sg.grow(geo['K_connector'], latch), 'latch margin'), ('K', 'F', geo['slot'], 'slot')]


class S9(r7.R7):
    """R7 with replaceable link geometry and lifted parts or blocks."""

    def setup9(self):
        self.prepare()
        self.load_done()
        self.out0 = copy.deepcopy(self.out)
        self.lift, self.lift_blocks = set(), set()
        self.sites = lg.gate_sites(self.inp, lg.RECORD['allocation'])
        self.site_by = {x['id']: x for x in self.sites}
        self.limits = p2.limits_of(self.ctx.gopts)
        self.byid = {r['id']: r for r in self.out0}
        self.dropped = {b: set(v) for b, v in self.ctx.model.dropped.items()}
        # who owns each placed link-era footprint
        self.block_of = {}
        for b, ic, ms, f0, pose in self.confirmed_blocks():
            for m in ms:
                self.block_of[(b, m)] = ic
        for b, ic, ms, f0, pose, passives, blocks in self.done:
            for m in ms:
                self.block_of[(b, m)] = ic
            for x in blocks:
                for m in x['members']:
                    self.block_of[(b, m)] = x['ic']
        self.scope = p2.replacement_scope(self.ctx, self.inp, self.out0)

    buffer_guard = False  # True: the S8 displacement may not move an input-buffer part (the arm 1 rule)

    def evictable2(self, board, ref):
        if self.buffer_guard and buffer_part(self, (board, ref)):
            return False
        return r7.R7.evictable2(self, board, ref)

    def set_links(self, moves):
        self.out = [dict(r, geometry=moves[r['id']]) if r['id'] in moves else r for r in self.out0]

    def add_part(self, f, board, m):
        if (board, m['ref']) in self.lift:
            return
        r7.R7.add_part(self, f, board, m)

    def place(self, f, board, ic, members, face0, pose):
        if (board, ic) in self.lift_blocks:
            return
        r7.R7.place(self, f, board, ic, members, face0, pose)

    def field(self, moving_extra):
        return rp.Study.field(self, set(moving_extra) | self.lift)

    def placed_items(self):
        """(board, face, rect, ref, kind) of every re-placed part: gate rows, link-era blocks and their passives."""
        out = [(b, r['new_face'], r['new_courtyard'], ref, 'gate re-placed part') for (b, ref), r in self.rows.items()
               if r['new'] is not None and (b, ref) not in self.base_extra]
        col = Collector()
        self.apply_confirmed(col)
        self.apply_done(col)
        for b, face, rect, ref in col.items:
            out.append((b, face, rect, ref, 'link-era block member (%s)' % self.block_of[(b, ref)] if (b, ref) in self.block_of
                        else 'link-era displaced passive'))
        return out

    def target_rects(self, ic):
        ms = self.members[('K', ic)]
        face0 = self.fps[('K', ic)]['side']
        sh = self.shapes('K', ms, face0, ic)
        return face0, sh[face0], [(self.mf('K', r, face0), c) for r, c in sh[face0]]


def ring(limit):
    return rp.offsets(0.25, 0.0, limit)


class Arm1:
    def __init__(self, s, t0):
        self.s, self.t0 = s, t0
        self.ctx = s.ctx
        self.gap = s.build_field().gap
        self.latch_field = s.build_field().latch
        self.ring = ring(LIMIT)
        self.capped = []
        self.rider_rejects = {}

    # ---------------------------------------------------------- accept
    def accept_for(self, lid, targets):
        s = self.s
        r = s.byid[lid]
        base = p2.class_accept(r, s.site_by, s.limits)
        size = lg.rec_size(self.ctx, r)
        cm = self.ctx.cmap
        rects = {ic: s.target_rects(ic)[2] for ic in targets}

        def accept(geo):
            why = base(geo)
            if why:
                return why
            for y in r.get('riders_in', []):
                if p2.rider_distance(s.site_by[y['site']], {'geometry': geo}) > s.limits[y['class']] + 1e-9:
                    return 'rider %s beyond its class distance' % y['net']
            if size['cable_length_mm'] - self.ctx.need(r['front_board'], geo['a_mm'], geo['b_mm']) < -1e-9:
                return 'cable longer than its stock length'
            c = lg.cvalue(cm, geo['K_connector'])
            if c is None or c > cm.limit + 1e-12:
                return 'K-field compliance above the DS-87 limit'
            for ic, rs in rects.items():
                for face, cy in rs:
                    g = sg.grow(cy, self.gap)
                    for b, f, rect, what in link_rects(geo, r['front_board'], self.latch_field):
                        if b == 'K' and f == face and sg.inter(g, rect):
                            return 'still covers ' + ic
            return None
        return accept

    def candidates(self, lid, targets, chosen, grid):
        s = self.s
        r = s.byid[lid]
        live = [dict(x, geometry=chosen[x['id']]) if x['id'] in chosen else x for x in p2.live(s.out0)]
        placed = lg.placed_index(live, skip=(lid,))
        self.ctx.model.memo_for(None)
        acc = self.accept_for(lid, targets)

        def accept(geo):
            why = acc(geo)
            if why and why.startswith('rider') and lid not in self.rider_rejects:
                self.rider_rejects[lid] = {'grid_mm': grid, 'why': why, 'geometry': geo}
            return why
        found, tally = lg.search(self.ctx, placed, r['front_board'], r['centre'], lg.rec_size(self.ctx, r), lg.rec_own(r),
                                 offsets=self.ctx.grid(grid, radius=self.ctx.radius), collect=10 ** 6, accept=accept)
        rejected = {k: v[0] for k, v in sorted(tally.items())}
        return found, rejected

    # ---------------------------------------------------------- figures
    def figures(self, lid, geo):
        s, ctx = self.s, self.ctx
        r = s.byid[lid]
        f = r['front_board']
        need = ctx.need(f, geo['a_mm'], geo['b_mm'])
        comp = lg.cvalue(ctx.cmap, geo['K_connector'])
        cm = ctx.cmap
        return {
            'recorded': {'slot_centre': r['slot_centre'], 'direction': r['direction'], 'loop_mm': r['loop_mm'],
                         'compliance_mm_per_N': r['compliance_mm_per_N'], 'trim_leads': r['trim_leads'], 'cost': r['cost']},
            'moved': {'loop_mm': round(lg.rec_size(ctx, r)['cable_length_mm'] - need, 4), 'cable_needed_mm': round(need, 4),
                      'compliance_mm_per_N': comp, 'trim_leads': lg.trim_list(ctx.model, f, geo),
                      'front_extension_mm': geo['front_extension_mm'], 'K_extension_mm': geo['K_extension_mm']},
            'size_kept': {'size': r['size'], 'connector': r['connector'], 'cable': r['cable'], 'cable_length_mm': r['cable_length_mm'],
                          'circuits': r['circuits'], 'circuits_needed': r['circuits_needed']},
            'compliance_within_limit': comp is not None and comp <= cm.limit + 1e-12,
            'hold_K_by_hand': comp is None or comp > cm.list_above,
            'class_accept': 'ACCEPT',
            'riders': [{'net': y['net'], 'class': y['class'], 'recorded_mm': p2.rider_distance(s.site_by[y['site']], r),
                        'moved_mm': p2.rider_distance(s.site_by[y['site']], {'geometry': geo}), 'limit_mm': s.limits[y['class']]}
                       for y in r.get('riders_in', [])],
            'members': [{'site': m, 'classes': sorted(set(s.site_by[m]['classes'])),
                         'recorded_mm': site_distance(s.site_by[m], r['geometry']), 'moved_mm': site_distance(s.site_by[m], geo),
                         'limit_mm': min(s.limits[c] for c in s.site_by[m]['classes'])} for m in r['members']]}

    # ---------------------------------------------------------- scene evaluation
    def evaluate(self, moves, restore):
        """Apply `moves` (link id -> geometry), restore the blocks in `restore` at their recorded position, re-place what
        that covers. Returns (clean, detail)."""
        s = self.s
        s.set_links(moves)
        s.lift, s.lift_blocks = set(), set()
        latch = self.latch_field
        rects = [x for lid, geo in moves.items() for x in link_rects(geo, s.byid[lid]['front_board'], latch)]
        lifted, why = {}, []
        # parts at paper position the moved links displace (retained rule), not already displaced or lifted
        for lid, geo in moves.items():
            front = s.byid[lid]['front_board']
            d = lg.displaced(self.ctx.model, front, geo, self.ctx.latch)
            for k, refs in d.items():
                b = front if k == 'front B' else 'K'
                for ref in refs:
                    key = (b, ref)
                    if key in s.scope or key in s.base_extra or ref in s.dropped.get(b, ()) or key not in s.fps:
                        continue
                    lifted.setdefault(key, set()).add('newly covered by %s (%s)' % (lid, k))
        # re-placed parts the moved links now cover (courtyard growth)
        items = s.placed_items()
        for b, face, rect, ref, kind in items:
            g = sg.grow(rect, self.gap)
            hit = [lab for bb, ff, rr, lab in rects if bb == b and ff == face and sg.inter(g, rr)]
            if hit:
                lifted.setdefault((b, ref), set()).add('%s under a moved link' % kind)
        # parts on the recorded area of the restored blocks
        for ic in restore:
            face0, sh, frs = s.target_rects(ic)
            for b, face, rect, ref, kind in items:
                if b == 'K' and any(f == face and sg.inter(cy, sg.grow(rect, self.gap)) for f, cy in frs):
                    lifted.setdefault((b, ref), set()).add('%s on the recorded area of %s' % (kind, ic))
        s.lift = set(lifted)
        f = s.build_field()
        for ic in restore:
            face0, sh, frs = s.target_rects(ic)
            fixed, fps = s.obstacles(f, 'K', face0, sh, 0.0, 0.0)
            for ref in sorted(fps):
                lifted.setdefault(('K', ref), set()).add('footprint at paper position on the recorded area of %s' % ic)
        # an IC newly covered moves as its S8 block (decouplers and cell-local passives)
        blocks = {}
        for key in sorted(k for k in lifted if k[1].startswith('U') and k not in s.block_of):
            dec, local, _ = s.block(*key)
            blocks[key] = [key[1]] + dec + local
            for m in blocks[key][1:]:
                lifted.setdefault((key[0], m), set()).add('member of the IC block %s' % key[1])
        # what may not move
        for key in sorted(lifted):
            if key in s.block_of:
                why.append(('placed link-era block', '%s %s is a member of the placed link-era block %s, which would move'
                            % (key[0], key[1], s.block_of[key])))
            b = self.buffer_part(key)
            if b:
                why.append(('input-buffer cell', '%s %s %s, which would move' % (key[0], key[1], b)))
        restored, moves_out = {}, []
        if any(c in ('placed link-era block', 'input-buffer cell') for c, _ in why):
            return self.done(False, restored, moves_out, why, lifted, 'not run: a part that may not move would move')
        s.lift = set(lifted)
        s.lift_blocks = set()
        f = s.build_field()
        for ic in restore:
            face0, sh, frs = s.target_rects(ic)
            fixed, fps = s.obstacles(f, 'K', face0, sh, 0.0, 0.0)
            restored[ic] = {'legal_at_recorded_position': not fixed and not fps,
                            'blocked_by': sorted('%s: %s' % x for x in fixed) + sorted(fps)}
            if fixed or fps:
                why.append(('target not legal', '%s is not legal at its recorded position: %s' % (ic, '; '.join(restored[ic]['blocked_by']))))
            for ref, cy in sh:
                f.add('K', s.mf('K', ref, face0), [round(v, 4) for v in cy], [], ref)
        if why:
            return self.done(False, restored, moves_out, why, lifted, 'not run: a target is not legal at its recorded position')
        for key in sorted(blocks, key=lambda k: (-rp_area(s.fps[k]), k)):
            m, f = self.replace_block(f, key, blocks[key], why)
            m['why'] = sorted(lifted[key])
            moves_out.append(m)
        in_blocks = {(k[0], r) for k, ms in blocks.items() for r in ms}
        order = sorted((k for k in lifted if k not in in_blocks), key=lambda k: (not k[1].startswith('U'), -rp_area(s.fps[k]), k))
        for key in order:
            m = self.replace(f, key)
            m['why'] = sorted(lifted[key])
            moves_out.append(m)
            if m['face'] is None:
                why.append(('no place', '%s %s finds no place within %g mm' % (key[0], key[1], LIMIT)))
        return self.done(not why, restored, moves_out, why, lifted, 'run')

    def done(self, clean, restored, moves_out, why, lifted, replacement):
        s = self.s
        s.set_links({})
        s.lift, s.lift_blocks = set(), set()
        return clean, {'restored': restored, 'lifted': ['%s %s' % k for k in sorted(lifted)], 're_placement': replacement,
                       'parts_re_placed': moves_out, 'not_clean_because': [t for _, t in why],
                       'categories': sorted({c for c, _ in why})}

    def buffer_part(self, key):
        return buffer_part(self.s, key)

    def replace_block(self, f, key, members, why):
        """The S8 search (Revision 1 class (iii) rules with the A2 turns and displacement, face-aware) for one IC block."""
        s = self.s
        b, ic = key
        s.members[key] = members
        s.buffer_guard = True
        try:
            legal, disp, trial = s.search(f, b, ic)
        finally:
            del s.members[key]
            s.buffer_guard = False
        best = legal[0] if legal else None
        out = {'board': b, 'ref': ic, 'block': members, 'from_paper_position': s.fps[key]['origin']}
        if best and best['moved_mm'] <= LIMIT:
            s.place(f, b, ic, members, s.fps[key]['side'], best)
            out.update({k: best[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')})
            return out, f
        if disp:
            for m in disp['displaced_moves']:
                bp = self.buffer_part((b, m['ref']))
                if bp:
                    why.append(('input-buffer cell', '%s %s %s, which would move (displaced by the block %s)' % (b, m['ref'], bp, ic)))
            out.update({k: disp[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')}, passives_moved=disp['displaced_moves'])
            return out, trial
        why.append(('no place', 'the block of %s %s finds no pose within %g mm (nearest %s mm)' % (b, ic, LIMIT, best and best['moved_mm'])))
        out.update({'face': None, 'origin': None, 'moved_mm': None, 'nearest_mm': best and best['moved_mm']})
        return out, f

    def replace(self, f, key):
        s = self.s
        b, ref = key
        fp = s.fps[key]
        c = fp['courtyard'] or p2.fp_bbox(fp)
        tht = [p['bbox'] for p in fp['pads'] if p['type'] in ('thru_hole', 'np_thru_hole')]
        faces = [fp['side']] + (['B' if fp['side'] == 'F' else 'F'] if b == 'K' and not tht else [])
        for d, dx, dy in self.ring:
            for face in faces:
                cy = [round(v, 4) for v in p2.shift(c if face == fp['side'] else rp.mirror(c, fp['origin'][0]), dx, dy)]
                pads = [[round(v, 4) for v in p2.shift(p, dx, dy)] for p in tht]
                if not f.blocked(b, face, cy, pads):
                    f.add(b, face, cy, pads, ref)
                    return {'board': b, 'ref': ref, 'face': face, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                            'moved_mm': r2(d), 'from_paper_position': fp['origin']}
        return {'board': b, 'ref': ref, 'face': None, 'origin': None, 'moved_mm': None, 'from_paper_position': fp['origin']}

    # ---------------------------------------------------------- per link
    def run_link(self, lid, targets, restore, chosen, evaluate=True):
        """Search one link; evaluate accepted candidates cheapest first (up to CAP per grid); return the first clean one
        (or None) and the log."""
        log = {'link': lid, 'targets': list(targets), 'grids': []}
        for g in GRIDS:
            if time.time() - self.t0 > TIME_CEILING_S:
                log['time_ceiling'] = True
                self.capped.append('%s: time ceiling before the %g mm grid' % (lid, g))
                return None, log
            found, rejected = self.candidates(lid, targets, chosen, g)
            print(lid, g, len(found), round(time.time() - self.t0), file=sys.stderr, flush=True)
            row = {'grid_mm': g, 'accepted_candidates': len(found), 'rejections_by_reason': rejected, 'evaluated': []}
            log['grids'].append(row)
            if not evaluate:
                continue
            for i, (cost, key, geo, disp, d, slot, dist) in enumerate(found):
                if i >= CAP:
                    row['cap_reached'] = True
                    self.capped.append('%s: %d accepted candidates on the %g mm grid, %d evaluated (cap)' % (lid, len(found), g, CAP))
                    break
                clean, det = self.evaluate(dict(chosen, **{lid: geo}), restore)
                row['evaluated'].append({'cost': round(cost, 4), 'slot_centre': list(slot), 'direction': lg.DIR_NAMES[d],
                                         'slot_distance_from_centre_mm': round(dist, 4), 'clean': clean,
                                         'categories': det['categories'], 'not_clean_because': det['not_clean_because'][:12],
                                         'parts_lifted': len(det['lifted'])})
                if clean:
                    return {'grid_mm': g, 'cost': round(cost, 4), 'slot_centre': list(slot), 'direction': lg.DIR_NAMES[d],
                            'slot_distance_from_centre_mm': round(dist, 4), 'geometry': geo,
                            'figures': self.figures(lid, geo), **det}, log
        return None, log

    def run_target(self, ic, lids, restored, chosen):
        """One target: its link (or, for U1415, its pair of links). Returns the row and the chosen moves."""
        s = self.s
        row = {'ic': ic, 'links': list(lids)}
        f = s.build_field()
        face0, sh, frs = s.target_rects(ic)
        fixed, fps = s.obstacles(f, 'K', face0, sh, 0.0, 0.0)
        row['recorded_area_obstacles'] = sorted('%s: %s' % x for x in fixed) + sorted(fps)
        others = sorted({lab.rsplit(' of ', 1)[1] for k, lab in fixed if ' of ' in lab} - set(lids))
        row['other_links_on_recorded_area'] = others
        occ = sorted({lab.split(' ')[-1] for k, lab in fixed if k == 'ruled or re-placed part'} | set(fps))
        row['recorded_area_parts_that_may_not_move'] = [
            '%s %s' % (r, self.buffer_part(('K', r)) or 'is a member of the placed link-era block %s' % s.block_of[('K', r)])
            for r in occ if self.buffer_part(('K', r)) or ('K', r) in s.block_of]
        if others:
            row['note'] = ('the recorded area stays under %s, which the brief keeps fixed: candidates are counted, not evaluated'
                           % ', '.join(others))
        if len(lids) == 1:
            best, log = self.run_link(lids[0], (ic,), restored + [ic], chosen, evaluate=not others)
            row['search'] = [log]
            if best:
                row.update({'result': 'R1 clean', 'moves': {lids[0]: best}})
                return row, {lids[0]: best['geometry']}
            row['result'] = 'R1 not clean'
            row['reason'] = self.reason(row)
            return row, {}
        first, second = lids
        found1, log1 = [], {'link': first, 'targets': [ic], 'grids': [], 'pair_first': True,
                            'note': 'evaluated without restoring %s (%s must move too)' % (ic, second)}
        for g in GRIDS:
            cands, rejected = self.candidates(first, (ic,), chosen, g)
            print(first, g, len(cands), round(time.time() - self.t0), file=sys.stderr, flush=True)
            grow = {'grid_mm': g, 'accepted_candidates': len(cands), 'rejections_by_reason': rejected, 'evaluated': []}
            log1['grids'].append(grow)
            for cost, key, geo, disp, d, slot, dist in cands[:CAP]:
                clean, det = self.evaluate(dict(chosen, **{first: geo}), restored)
                grow['evaluated'].append({'cost': round(cost, 4), 'slot_centre': list(slot), 'direction': lg.DIR_NAMES[d], 'clean': clean,
                                          'categories': det['categories'], 'not_clean_because': det['not_clean_because'][:12]})
                if clean:
                    found1.append((g, cost, geo, d, slot, dist))
                if len(found1) >= PAIR_CAP:
                    break
            if found1:
                break
        row['search'] = [log1]
        pair = None
        for g, cost, geo, d, slot, dist in found1:
            best, log = self.run_link(second, (ic,), restored + [ic], dict(chosen, **{first: geo}))
            log['with_first_at'] = {'grid_mm': g, 'cost': round(cost, 4), 'slot_centre': list(slot), 'direction': lg.DIR_NAMES[d]}
            row['search'].append(log)
            if best:
                pair = ({'grid_mm': g, 'cost': round(cost, 4), 'slot_centre': list(slot), 'direction': lg.DIR_NAMES[d],
                         'slot_distance_from_centre_mm': round(dist, 4), 'geometry': geo, 'figures': self.figures(first, geo)}, best)
                break
        if not found1:
            best2, log2 = self.run_link(second, (ic,), restored + [ic], chosen, evaluate=False)
            log2['note'] = 'searched with %s at the record (%s has no clean candidate), candidates counted only' % (first, first)
            row['search'].append(log2)
        if pair:
            row.update({'result': 'R1 clean', 'moves': {first: pair[0], second: pair[1]}})
            return row, {first: pair[0]['geometry'], second: pair[1]['geometry']}
        row['result'] = 'R1 not clean'
        row['reason'] = self.reason(row)
        return row, {}

    def run(self):
        chosen, rows, restored = {}, [], []
        for ic, lids in TARGETS:
            row, moves = self.run_target(ic, lids, restored, chosen)
            if moves:
                chosen.update(moves)
                restored.append(ic)
            rows.append(row)
        joint = None
        if chosen:
            clean, det = self.evaluate(chosen, restored)
            joint = {'links': sorted(chosen), 'restored': restored, 'clean': clean, **det}
        return rows, chosen, restored, joint

    def reason(self, row):
        out = []
        if row['other_links_on_recorded_area']:
            out.append('the recorded area is also under %s, which the brief keeps fixed' % ', '.join(row['other_links_on_recorded_area']))
        if row['recorded_area_parts_that_may_not_move']:
            out.append('parts on the recorded area that may not move, whatever the link candidate: %s'
                       % '; '.join(row['recorded_area_parts_that_may_not_move']))
        seen = set()
        for lg_ in row['search']:
            grids = lg_.get('grids', [])
            if lg_.get('pair_first'):
                ev = [e for g in grids for e in g.get('evaluated', [])]
                out.append('%s: %d clean candidates (without restoring the target), each tried with %s'
                           % (lg_['link'], sum(1 for e in ev if e['clean']), row['links'][1]))
                continue
            if grids and all(g['accepted_candidates'] == 0 for g in grids) and lg_['link'] not in seen:
                seen.add(lg_['link'])
                top = {}
                for g in grids:
                    for k, v in g['rejections_by_reason'].items():
                        top[k] = top.get(k, 0) + v
                worst = sorted(top.items(), key=lambda kv: -kv[1])[:4]
                out.append('%s: no accepted candidate on the %s mm grids within the %g mm radius (most frequent: %s)'
                           % (lg_['link'], '/'.join('%g' % g['grid_mm'] for g in grids), self.ctx.radius, '; '.join('%s %d' % kv for kv in worst)))
            ev = [e for g in grids for e in g.get('evaluated', [])]
            if ev:
                cats = {}
                for e in ev:
                    for c in e['categories']:
                        cats[c] = cats.get(c, 0) + 1
                out.append('%s: %d candidates evaluated, none clean (%s); the cheapest: %s'
                           % (lg_['link'], len(ev), ', '.join('%s in %d' % kv for kv in sorted(cats.items())), '; '.join(ev[0]['not_clean_because'][:4])))
        return list(dict.fromkeys(out))


def buffer_part(s, key):
    """Why `key` belongs to an input-buffer block (the S8 A3 definition: a package with a high-impedance-input or
    remote-buffer unit, its decouplers and cell-local passives, and the cell parts of those roles), or None."""
    own = s.owner.get(key)
    if key[1].startswith('U') and key[1] in s.buffer_ics:
        return 'is an input-buffer IC'
    if own in s.buffer_ics:
        return 'is in the block of the input buffer %s' % own
    if key[1] in s.buffer_ics:
        return 'is an input-buffer cell part (%s)' % ', '.join(sorted({u['role'] for u in s.io_units if u['ref'] == key[1]}))
    return None


def site_distance(site, geo):
    """The class-accept distance of a member site: the larger of its distances to the front and K connector centres."""
    return p2.rider_distance(site, {'geometry': geo})


def rp_area(fp):
    c = fp['courtyard'] or p2.fp_bbox(fp) or [0, 0, 0, 0]
    return (c[2] - c[0]) * (c[3] - c[1])


# ---------------------------------------------------------------- arm 2

def tssop_courtyard(fp):
    """The repository TSSOP-14 courtyard placed as the board's SOIC-14 is (same origin, angle and side)."""
    m = placement_map(fp, kicad_geometry(SOIC)[0])
    return mapped_rect(kicad_geometry(TSSOP)[1], m, fp['origin'])


def arm2(s, targets, moves=None):
    """TSSOP-14 room only: swap the IC courtyard, keep the block, run the S8 search within 24 mm. Each IC runs under the
    S8 rules as ruled, and again with the arm 1 input-buffer guard (no input-buffer part displaced)."""
    tpads, tcy = kicad_geometry(TSSOP)
    spads, scy = kicad_geometry(SOIC)
    rows = []

    def once(ic, guard):
        s.set_links(moves or {})
        s.lift, s.lift_blocks = set(), set()
        s.buffer_guard = guard
        try:
            legal, disp, _ = s.search(s.build_field(), 'K', ic)
        finally:
            s.buffer_guard = False
            s.set_links({})
        best = legal[0] if legal else None
        out = {'nearest_legal_mm': best['moved_mm'] if best else None, 'nearest_legal': best}
        if best and best['moved_mm'] <= LIMIT:
            out.update({'result': 'R2 room', 'pose': best, 'passives_moved': []})
        elif disp:
            out.update({'result': 'R2 room', 'pose': {k: disp[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')},
                        'passives_moved': disp['displaced_moves'],
                        'input_buffer_parts_moved': ['%s %s' % (m['ref'], buffer_part(s, ('K', m['ref'])))
                                                     for m in disp['displaced_moves'] if buffer_part(s, ('K', m['ref']))]})
        else:
            out['result'] = 'none'
        return out

    for ic in targets:
        fp = s.fps[('K', ic)]
        m = placement_map(fp, spads)
        saved = fp['courtyard']
        fp['courtyard'] = mapped_rect(tcy, m, fp['origin'])
        try:
            plain = once(ic, False)
            census = s.census
            guarded = once(ic, True)
        finally:
            new, fp['courtyard'] = fp['courtyard'], saved
        row = {'ic': ic, 'label': 'ROOM ONLY, NO PART SELECTED', 'courtyard_soic': saved,
               'courtyard_soic_from_library': mapped_rect(scy, m, fp['origin']), 'courtyard_tssop': new,
               'rules': 'Revision 1 class (iii) with the A2 turns and displacement, face-aware', **plain,
               'census_within_24mm': census, 'with_input_buffer_guard': guarded}
        if plain.get('input_buffer_parts_moved'):
            row['note'] = ('room under the S8 rules only by displacing input-buffer parts; with the arm 1 input-buffer guard: %s'
                           % (guarded['result'] if guarded['result'] == 'none' else 'R2 room at %s mm' % guarded['pose']['moved_mm']))
        rows.append(row)
    return rows


# ---------------------------------------------------------------- arm 0

def arm0(s):
    f = s.build_field()
    gone = sorted(r['id'] for r in s.out0 if r.get('gone'))
    labels = {lab for ix in f.links.values() for _, lab in ix.items}
    cited = sorted({lab for lab in labels if lab.rsplit(' of ', 1)[1] in gone})
    text = json.dumps(r7.build(), indent=1) + '\n'
    same = text == r7.OUT.read_text()
    doc = json.loads(text)
    five = {r['ic']: r['result'] for r in doc['research'] if r['ic'] in ('U1415', 'U5110', 'U5209')}
    five.update({t: 'OPEN (link era)' if t not in doc['joint']['placed'] else 'placed' for t in ('U5210', 'U8409')})
    return {'gone_links': gone, 'gone_keepouts_in_field': cited, 'premise_holds': not cited,
            'result_r7_reproduced_byte_for_byte': same, 'result_r7_sha256': hashlib.sha256(text.encode()).hexdigest(),
            'five_open': five}


def build():
    t0 = time.time()
    pins, base = input_pins()
    s = S9()
    s.setup9()
    a0 = arm0(s)
    if not (a0['premise_holds'] and a0['result_r7_reproduced_byte_for_byte'] and base['links_and_replacement_unchanged']
            and base['link_era_other_rows_unchanged']):
        return {'status': 'STOPPED AT ARM 0', 'inputs': pins, 'base': base, 'arm0': a0}
    s = S9()
    s.setup9()
    a1 = Arm1(s, t0)
    rows1, chosen, restored, joint = a1.run()
    r1 = {r['ic']: r for r in rows1}
    rows2 = arm2(s, [ic for ic, _ in TARGETS])
    r2_ = {r['ic']: r for r in rows2}
    both = [ic for ic, _ in TARGETS if r1[ic]['result'] != 'R1 clean' and r2_[ic]['with_input_buffer_guard']['result'] != 'R2 room']
    combined = []
    for ic in both:
        fp = s.fps[('K', ic)]
        saved = fp['courtyard']
        fp['courtyard'] = tssop_courtyard(fp)
        try:
            row, _ = a1.run_target(ic, dict(TARGETS)[ic], restored, chosen)
        finally:
            fp['courtyard'] = saved
        row.update({'label': 'ROOM ONLY, NO PART SELECTED', 'package': 'repository TSSOP-14 courtyard in place of the SOIC-14',
                    'result': row['result'].replace('R1', 'R1 with R2')})
        combined.append(row)
    rc = {r['ic']: r for r in combined}
    table = []
    for ic, lids in TARGETS:
        a, b = r1[ic], r2_[ic]
        g = b['with_input_buffer_guard']
        if a['result'] == 'R1 clean':
            outcome = 'R1 clean'
        elif g['result'] == 'R2 room':
            outcome = 'R2 room'
        elif b['result'] == 'R2 room':
            outcome = 'R2 room only by displacing input-buffer parts'
        elif ic in rc and rc[ic]['result'] == 'R1 with R2 clean':
            outcome = 'R1 with R2 clean (room only)'
        else:
            outcome = 'none'
        table.append({'ic': ic, 'links': list(lids), 'R1': a['result'], 'R1_reason': a.get('reason', []),
                      'R2': b['result'] + ('' if b['result'] == 'none' else ' (ROOM ONLY, NO PART SELECTED)'),
                      'R2_nearest_mm': b['nearest_legal_mm'], 'R2_note': b.get('note'),
                      'R2_with_input_buffer_guard': g['result'],
                      'R1_with_R2': rc[ic]['result'] + ' (ROOM ONLY, NO PART SELECTED)' if ic in rc else 'not run (an arm passed)',
                      'R1_with_R2_reason': rc[ic].get('reason', []) if ic in rc else [],
                      'outcome': outcome})
    return {'schema_version': 1, 'status': 'STUDY (MC04-S9-A, DS-145): no canonical change; decision table only',
            'generator': 'scripts/stack/studies/mc04_s9_slot_moves/slot_moves.py', 'brief': BRIEF, 'model': rp.MODEL,
            'inputs': pins, 'base': base,
            'parameters': {'grids_mm': list(GRIDS), 'candidate_cap_per_link_and_grid': CAP, 'pair_cap_U1415': PAIR_CAP,
                           'search_radius_mm': s.ctx.radius, 'join_radius_mm': lg.val(s.ctx.opts['clustering']['join_radius_mm']),
                           're_placement_limit_mm': LIMIT, 'courtyard_growth_mm': a1.gap, 'latch_margin_mm': a1.latch_field,
                           'class_limits_mm': s.limits, 'compliance_limit_mm_per_N': s.ctx.cmap.limit,
                           'hold_by_hand_above_mm_per_N': s.ctx.cmap.list_above, 'time_ceiling_s': TIME_CEILING_S},
            'arm0': a0, 'arm1': {'targets': rows1, 'joint_verification': joint, 'caps_reached': a1.capped,
                                 'rider_rejection_examples': a1.rider_rejects},
            'arm2': rows2, 'combined': combined, 'decision_table': table,
            'not_established': ['c6 (the contract pins the geometry digest)', 'coupling (check 4)', 'current (check 3)',
                                'latch access (check 2)', 'threading', 'routing', 'DRC', 'any electrical acceptance'],
            'oracle_checks': {'c6': 'NOT RUN: a study changes no canonical geometry; c6 runs on adoption',
                              'link_electrical (checks 3, 4)': 'NOT RUN: rebound once after the S9 link moves (DS-145 item 6)',
                              'latch access, threading procedure': 'NOT RUN: regenerate on adoption',
                              'routing, DRC': 'NOT RUN: no board change'}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s9_slot_moves/slot_moves.py')
        print('result.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    for r in d.get('decision_table', []):
        print(r['ic'], r['R1'], '|', r['R2'], r['R2_nearest_mm'], '|', r['outcome'], r['R1_reason'][:2])


if __name__ == '__main__':
    main()
