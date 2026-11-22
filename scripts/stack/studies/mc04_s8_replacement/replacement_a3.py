#!/usr/bin/env python3
"""MC04-S8 Part A3: block-on-block moves for the last four ICs (Revision 2 of the S8 brief; no board change).

Every pose ruled so far is applied first: the eight of Revision 1 (Part A), U4524 (A2, with its three resistors), and
U1318 and U4417 at their A2 poses. Each target (U5209, U5210, U8409, U4647) may then displace up to two other IC blocks
(IC, decouplers and cell-local R/C as in Part A) and small SMD passives (the A2 rule). Each displaced block moves
rigidly within 24 mm of its own position, at any turn on either face, and must land legal without displacing anything
further. Input buffers (units with a high_impedance_input or remote_buffer role) are never displaced. Panel hardware,
jacks, locked parts, link fields, tails and slots, sleeves and fixing keep-outs, the outline and the ruled poses stay.
For a target still beyond 24 mm the poses within 24 mm are scanned for the smallest set of fixed obstacles, by type.
Writes result-a3.json; --check verifies it. Courtyard level on unvalidated drafts."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a2 as a2  # noqa: E402
from replacement import p2, r2, sg  # noqa: E402

OUT = Path(__file__).with_name('result-a3.json')
TARGETS = ('U5209', 'U5210', 'U8409', 'U4647')
RULED_A2 = ('U4524', 'U1318', 'U4417')
MAX_BLOCKS = 2
MAX_TRIALS = 120


class A3(a2.A2):
    def prepare(self):
        io = json.loads((rp.ROOT / 'design/reports/io-partition.json').read_text())
        self.io_units = io['package_units']
        self.a = json.loads(rp.OUT.read_text())
        self.arow = {r['ic']: r for r in self.a['ics']}
        self.a2 = {r['ic']: r for r in json.loads(a2.OUT.read_text())['ics']}
        order = [(i['board'], i['ref']) for i in self.items]
        self.blocks = {k: self.block(*k) for k in order}
        self.members = {k: [k[1]] + self.blocks[k][0] + self.blocks[k][1] for k in order}
        disp = {(self.arow[ic]['board'], m['ref']) for ic in a2.RULED for m in self.arow[ic].get('displaced_moves', [])}
        disp |= {(self.a2['U4524']['board'], m['ref']) for m in self.a2['U4524']['chosen']['displaced_moves']}
        self.locked_moves = disp
        self.base_extra = {(b, r) for (b, _), ms in self.members.items() for r in ms} | disp
        self.buffer_ics = {u['ref'] for u in self.io_units if (u.get('role') or '').startswith(('high_impedance_input', 'remote_buffer'))}
        self.owner = {}
        self.ic_members = {}
        for b in ('K', 'JL', 'JR'):
            for f in self.inp['ci']['boards'][b]:
                ic = f['ref']
                if not ic.startswith('U') or (b, ic) in self.members:
                    continue
                dec, local, _ = self.block(b, ic)
                ms = [ic] + dec + local
                self.ic_members[(b, ic)] = ms
                for m in ms:
                    self.owner.setdefault((b, m), ic) if m != ic else self.owner.__setitem__((b, m), ic)

    def place(self, f, board, ic, members, face0, pose):
        sh = dict(((fc, k), r) for fc, k, r in self.orients(board, ic, members, face0))[(pose['face'], pose['turn_deg'])]
        dx, dy = pose['shift_mm']
        for ref, c in sh:
            f.add(board, pose['face'], [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)

    def orients(self, board, ic, members, face0):
        o = self.fps[(board, ic)]['origin']
        sh = self.shapes(board, members, face0, ic)
        return [(face, k, [(r, [round(v, 4) for v in a2.rot(c, o, k)]) for r, c in sh[face]])
                for face in (face0, 'B' if face0 == 'F' else 'F') for k in a2.TURNS]

    def build_field(self, extra=frozenset()):
        f = self.field(self.base_extra | set(extra))
        for ic in a2.RULED:
            row = self.arow[ic]
            board = row['board']
            c = dict(row['chosen'], turn_deg=0)
            self.place(f, board, ic, self.members[(board, ic)], row['face'], c)
            for m in row.get('displaced_moves', []):
                self.add_part(f, board, m)
        for ic in RULED_A2:
            row = self.a2[ic]
            board = row['board']
            self.place(f, board, ic, self.members[(board, ic)], row['face'], row['chosen'])
            for m in row['chosen'].get('displaced_moves', []):
                self.add_part(f, board, m)
        return f

    def add_part(self, f, board, m):
        fp = self.fps[(board, m['ref'])]
        cy = fp['courtyard'] or p2.fp_bbox(fp)
        if m['face'] != fp['side']:
            cy = rp.mirror(cy, fp['origin'][0])
        f.add(board, m['face'], [round(v, 4) for v in p2.shift(cy, m['origin'][0] - fp['origin'][0], m['origin'][1] - fp['origin'][1])], [], m['ref'])

    # ------------------------------------------------------------------ obstacle census of one pose
    def obstacles(self, field, board, face, rects, dx, dy):
        """(fixed obstacles by type, footprints met). Fixed: outline, link keep-out, sleeve or fixing keep-out, panel
        hardware or hole, locked part, jack, ruled pose."""
        fixed, fps = set(), set()
        for _, c in rects:
            cy = [round(v, 4) for v in p2.shift(c, dx, dy)]
            if not field.model.inside(board, cy, field.margin):
                fixed.add(('outline', 'board outline'))
            g = sg.grow(cy, field.gap)
            for rect, payload in field.idx[(board, face)].near(cy):
                if payload[0] == 'circle':
                    x, y, rad = payload[1]
                    if sg.circle_rect_depth(x, y, rad, cy) > 1e-9:
                        lab = payload[2]
                        fixed.add(('sleeve' if 'SLV' in lab else 'fixing keep-out', lab))
                elif sg.inter(cy, rect):
                    lab = payload[2]
                    if payload[0] == 'fp' and lab.startswith('re-placed'):
                        fixed.add(('ruled or re-placed part', lab.split(' ')[-1]))
                    elif payload[0] == 'fp':
                        ref = lab.split(' ')[-1]
                        p = self.pk.get(ref, {})
                        if ref.startswith('J'):
                            fixed.add(('jack', ref))
                        elif p.get('panel_uid'):
                            fixed.add(('locked part', ref))
                        else:
                            fps.add(ref)
                    else:
                        fixed.add(('panel hardware or hole', lab))
            lk = field.links.get((board, face))
            if lk:
                for rect, lab in lk.near(g):
                    if sg.inter(g, rect):
                        fixed.add(('link slot' if lab.startswith('slot') else 'link field, tail or latch margin', lab))
        return fixed, fps

    def classify_fps(self, board, fps):
        """Footprints met: IC blocks (by owning IC), small evictable passives, or blocking (anything else)."""
        blocks, small, hard = set(), set(), set()
        for r in fps:
            ic = self.owner.get((board, r))
            if ic:
                blocks.add(ic)
            elif self.evictable2(board, r):
                small.add(r)
            else:
                hard.add(r)
        return blocks, small, hard

    def move_block(self, f, board, ic, limit=rp.LIMIT_MM):
        ms = self.ic_members[(board, ic)]
        fp = self.fps[(board, ic)]
        orients = self.orients(board, ic, ms, fp['side'])
        for d, dx, dy in [o for o in rp.offsets(rp.NEAR_STEP, 0.0, limit)]:
            for face, k, rects in orients:
                if self.legal(f, board, face, rects, dx, dy):
                    pose = {'face': face, 'turn_deg': k, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                            'moved_mm': r2(d), 'shift_mm': [dx, dy]}
                    for ref, c in rects:
                        f.add(board, face, [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)
                    return pose
        return None

    def target(self, board, ic):
        ms = self.members[(board, ic)]
        fp = self.fps[(board, ic)]
        field = self.build_field()
        orients = self.orients(board, ic, ms, fp['side'])
        near = [o for o in rp.offsets(rp.NEAR_STEP, 0.0, rp.NEAR_MM) if o[0] <= rp.LIMIT_MM + 1e-9]
        cands, census = [], []
        for d, dx, dy in near:
            for face, k, rects in orients:
                fixed, fps = self.obstacles(field, board, face, rects, dx, dy)
                blocks, small, hard = self.classify_fps(board, fps)
                census.append((fixed, blocks, small, hard, d, face, k, dx, dy))
                if fixed or hard or len(blocks) > MAX_BLOCKS or (blocks & self.buffer_ics):
                    continue
                cands.append((len(blocks), len(small), d, face, k, dx, dy, sorted(blocks), sorted(small)))
        cands.sort()
        tried = 0
        fails = Counter()
        for nb, ns, d, face, k, dx, dy, blocks, small in cands:
            if tried >= MAX_TRIALS:
                break
            tried += 1
            extra = self.trial_extra(board, blocks, small)
            f = self.build_field(extra)
            pose = {'face': face, 'turn_deg': k, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                    'moved_mm': r2(d), 'shift_mm': [dx, dy]}
            rects = next(r for fc, kk, r in orients if (fc, kk) == (face, k))
            if not self.legal_except(f, board, face, rects, dx, dy, set(small)):
                fails['target pose not free once the blocks are lifted'] += 1
                continue
            for ref, c in rects:
                f.add(board, face, [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)
            moved = []
            for b in blocks:
                bp = self.move_block(f, board, b)
                if bp is None:
                    fails['block %s has no legal pose within 24 mm' % b] += 1
                    break
                moved.append(dict(bp, ic=b, members=self.ic_members[(board, b)]))
            else:
                parts = []
                for ref in small:
                    m, cy = self.move_within(f, board, ref)
                    if m is None:
                        fails['passive %s has no legal pose within 24 mm' % ref] += 1
                        break
                    f.add(board, m['face'], cy, [], ref)
                    parts.append(m)
                else:
                    return {'result': 'fits within 24 mm', 'pose': pose, 'blocks_moved': moved, 'passives_moved': parts,
                            'candidates': len(cands), 'trials': tried}
        # still beyond 24 mm: the pose with the smallest set of obstacles that the rule cannot move. A block met by a
        # candidate pose that found no legal pose of its own within 24 mm counts as one obstacle of type 'IC block'.
        stuck = {k.split(' ')[1] for k in fails if k.startswith('block ')}
        best = None
        for fixed, blocks, small, hard, d, face, k, dx, dy in census:
            extra_blocks = sorted((blocks & self.buffer_ics) | (blocks & stuck))
            rest = sorted(blocks - set(extra_blocks))
            extra_blocks += rest[MAX_BLOCKS:]
            n = len(fixed) + len(hard) + len(extra_blocks)
            if n == 0:
                continue
            key = (n, d)
            if best is None or key < best[0]:
                best = (key, fixed, blocks, small, hard, d, face, k, dx, dy, extra_blocks)
        _, fixed, blocks, small, hard, d, face, k, dx, dy, extra_blocks = best
        types = Counter(t for t, _ in fixed)
        return {'result': 'no pose within 24 mm under the rule', 'candidates': len(cands), 'trials': tried,
                'trial_failures': dict(sorted(fails.items(), key=lambda x: (-x[1], x[0]))),
                'smallest_obstacle_set': {
                    'pose': {'face': face, 'turn_deg': k, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)], 'moved_mm': r2(d)},
                    'fixed_by_type': dict(sorted(types.items())),
                    'fixed': sorted([{'type': t, 'what': w} for t, w in fixed], key=lambda x: (x['type'], x['what'])),
                    'non_evictable_footprints': sorted(hard), 'input_buffer_blocks': sorted(blocks & self.buffer_ics),
                    'ic_blocks_the_rule_cannot_move': extra_blocks,
                    'ic_blocks_met': sorted(blocks), 'small_passives_met': sorted(small),
                    'count': len(fixed) + len(hard) + len(extra_blocks),
                    'by_type': dict(sorted(Counter([t for t, _ in fixed] + ['non-evictable footprint'] * len(hard)
                                                   + ['IC block'] * len(extra_blocks)).items()))}}

    def trial_extra(self, board, blocks, small):
        """Parts lifted from the obstacles for one trial: the members of the displaced blocks."""
        return {(board, m) for b in blocks for m in self.ic_members[(board, b)]}

    def legal_except(self, f, board, face, rects, dx, dy, allowed):
        fixed, fps = self.obstacles(f, board, face, rects, dx, dy)
        return not fixed and fps <= allowed

    def run(self):
        self.prepare()
        out = []
        for ic in TARGETS:
            row = self.a2[ic]
            res = self.target(row['board'], ic)
            out.append({'board': row['board'], 'ic': ic, 'function': row['function'], 'block': row['block'],
                        'a2_rejected_pose': {k: row['chosen'][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')}, **res})
        return out


def build():
    s = A3()
    res = s.run()
    return {'schema_version': 1,
            'status': 'STUDY (MC04-S8 Part A3): courtyard level on unvalidated drafts; no board changed; nothing adopted',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/replacement_a3.py',
            'rules': {'ruled_first': list(a2.RULED) + list(RULED_A2), 'max_ic_blocks_displaced': MAX_BLOCKS,
                      'displaced_block': 'rigid, any turn on either face, within %g mm, legal without further displacement; '
                                         'input-buffer ICs never displaced' % rp.LIMIT_MM,
                      'small_passives': 'the A2 rule (unlocked SMD R/C/D up to 12 mm2, not a decoupler, within 24 mm)',
                      'fixed': 'outline, panel hardware and holes, jacks, locked parts, link fields/tails/slots/latch margins, '
                               'sleeves and fixing keep-outs, ruled poses'},
            'targets': res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result-a3.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s8_replacement/replacement_a3.py')
        print('result-a3.json current')
    else:
        OUT.write_text(text)
    for r in json.loads(text)['targets']:
        print(r['board'], r['ic'], r['result'], r.get('pose', {}).get('moved_mm'), [b['ic'] for b in r.get('blocks_moved', [])],
              r.get('smallest_obstacle_set', {}).get('by_type'), r.get('candidates'), r.get('trial_failures'))


if __name__ == '__main__':
    main()
