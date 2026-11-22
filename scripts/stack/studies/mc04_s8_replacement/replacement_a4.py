#!/usr/bin/env python3
"""MC04-S8 Part A4: the three narrow relaxations of Revision 3 (no board change).

Every pose ruled so far is applied first: Part A's eight, U4524, U1318 and U4417 (A2), and U4647 with the U4502 block
and R4516 (A3). The three remaining targets are then searched as in Part A3, each with one relaxation only:
- U5209: R8263 (already re-placed by the link gate) may move again, ending within 24 mm of its 6093081c position and
  no farther from its cell partner (U8211, the buffer on its W_SENSE net) than before the gate moved it;
- U5210: C5210 (1206 AC-coupling capacitor) may be displaced within 24 mm, with the added run on its high-impedance
  side (/W1/AC_NODE, the U5211 non-inverting input) under 10 mm (1.5 x HPWL);
- U8409: a chain of up to three IC blocks (the target, U8412 and one more), each rigid within 24 mm under its own
  rules, none an input buffer.
Writes result-a4.json; --check verifies it. Courtyard level on unvalidated drafts."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a2 as a2  # noqa: E402
import replacement_a3 as a3  # noqa: E402
from replacement import p2, r2  # noqa: E402

OUT = Path(__file__).with_name('result-a4.json')
TARGETS = ('U5209', 'U5210', 'U8409')
R8263_PARTNER = 'U8211'
C5210_HIZ_NET = '/W1/AC_NODE'
HIZ_LIMIT_MM = 10.0


class A4(a3.A3):
    def prepare(self):
        super().prepare()
        self.a3 = {r['ic']: r for r in json.loads(a3.OUT.read_text())['targets']}
        u = self.a3['U4647']
        b = u['board']
        self.u4502 = u['blocks_moved'][0]
        self.base_extra |= {(b, m) for m in self.u4502['members']} | {(b, m['ref']) for m in u['passives_moved']}
        self.locked_moves |= {(b, m['ref']) for m in u['passives_moved']}
        base = json.loads(subprocess.run(['git', '-C', str(rp.ROOT), 'show', '6093081c:design/partition/floorplan-candidate.json'],
                                         capture_output=True, check=True, text=True).stdout)
        self.p0 = {p['ref']: p for p in base['placements']}
        self.mode = None

    def build_field(self, extra=frozenset()):
        f = super().build_field(extra)
        u = self.a3['U4647']
        board = u['board']
        self.place(f, board, 'U4647', self.members[(board, 'U4647')], self.a2['U4647']['face'], u['pose'])
        b = self.u4502
        self.place(f, board, b['ic'], b['members'], self.fps[(board, b['ic'])]['side'], b)
        for m in u['passives_moved']:
            self.add_part(f, board, m)
        return f

    # ------------------------------------------------------------------ relaxations
    def obstacles(self, field, board, face, rects, dx, dy):
        fixed, fps = super().obstacles(field, board, face, rects, dx, dy)
        if self.mode == 'U5209' and ('ruled or re-placed part', 'R8263') in fixed:
            fixed.discard(('ruled or re-placed part', 'R8263'))
            fps.add('R8263')
        return fixed, fps

    def evictable2(self, board, ref):
        if self.mode == 'U5209' and ref == 'R8263':
            return True
        if self.mode == 'U5210' and ref == 'C5210':
            return True
        return super().evictable2(board, ref)

    def trial_extra(self, board, blocks, small):
        extra = {(board, m) for b in blocks for m in self.ic_members[(board, b)]}
        if self.mode == 'U5209' and 'R8263' in small:
            extra.add((board, 'R8263'))
        return extra

    def partner_ok(self, board, ref, xy):
        p0 = self.p0[ref]
        if math.dist(xy, (p0['x_mm'], p0['y_mm'])) > rp.LIMIT_MM + 1e-9:
            return False, None
        partner = self.fps[(board, R8263_PARTNER)]['origin']
        before = math.dist(self.fps[(board, ref)]['origin'], partner)
        return math.dist(xy, partner) <= before + 1e-9, {'from_6093081c_mm': r2(math.dist(xy, (p0['x_mm'], p0['y_mm']))),
                                                         'to_%s_before_mm' % R8263_PARTNER: r2(before),
                                                         'to_%s_after_mm' % R8263_PARTNER: r2(math.dist(xy, partner))}

    def hiz_added(self, board, ref, xy):
        refs = sorted(r for r in self.net_refs[C5210_HIZ_NET] if (board, r) in self.fps)
        pts = [tuple(self.fps[(board, r)]['origin']) for r in refs]
        after = [xy if r == ref else tuple(self.fps[(board, r)]['origin']) for r in refs]
        return r2(a2.ROUTE_FACTOR * (self.hpwl(after) - self.hpwl(pts)))

    def move_within(self, field, board, ref, limit=rp.LIMIT_MM):
        if not ((self.mode == 'U5209' and ref == 'R8263') or (self.mode == 'U5210' and ref == 'C5210')):
            return super().move_within(field, board, ref, limit)
        f = self.fps[(board, ref)]
        c = f['courtyard'] or p2.fp_bbox(f)
        for d, dx, dy in rp.offsets(0.25, 0.0, limit + 24.0 if ref == 'R8263' else limit):
            xy = (f['origin'][0] + dx, f['origin'][1] + dy)
            if ref == 'R8263':
                ok, facts = self.partner_ok(board, ref, xy)
            else:
                add = self.hiz_added(board, ref, xy)
                ok, facts = add < HIZ_LIMIT_MM, {'hiz_net': C5210_HIZ_NET, 'added_run_estimate_mm': add}
            if not ok:
                continue
            for face in (f['side'], 'B' if f['side'] == 'F' else 'F'):
                cy = [round(v, 4) for v in p2.shift(c if face == f['side'] else rp.mirror(c, f['origin'][0]), dx, dy)]
                if not field.blocked(board, face, cy, []):
                    return dict({'ref': ref, 'face': face, 'origin': [r2(xy[0]), r2(xy[1])], 'moved_mm': r2(d)}, relaxation=facts), cy
        return None, None

    def move_block(self, f, board, ic, limit=rp.LIMIT_MM):
        pose = super().move_block(f, board, ic, limit)
        if pose is not None or self.mode != 'U8409' or ic != 'U8412' or self.chain_used:
            return pose
        # the third block of the chain: U8412 may displace one more non-buffer IC block (and small passives)
        ms = self.ic_members[(board, ic)]
        fp = self.fps[(board, ic)]
        for d, dx, dy in rp.offsets(rp.NEAR_STEP, 0.0, limit):
            for face, k, rects in self.orients(board, ic, ms, fp['side']):
                fixed, fps = self.obstacles(f, board, face, rects, dx, dy)
                blocks, small, hard = self.classify_fps(board, fps)
                if fixed or hard or len(blocks) != 1 or (blocks & self.buffer_ics) or blocks & self.chain_busy:
                    continue
                self.chain_candidates.append((d, face, k, sorted(blocks)[0], sorted(small)))
        return None

    def target(self, board, ic):
        self.mode = ic
        self.chain_used = False
        self.chain_candidates = []
        self.chain_busy = set()
        res = super().target(board, ic)
        if ic == 'U8409' and res['result'] != 'fits within 24 mm':
            res = self.chain(board, ic, res)
        self.mode = None
        return res

    def chain(self, board, ic, res0):
        """Target -> U8412 -> one more block: try the target poses that only U8412 (and passives) block, then U8412 poses
        that only one more block (and passives) blocks, then that block's own move."""
        ms = self.members[(board, ic)]
        fp = self.fps[(board, ic)]
        field = self.build_field()
        near = [o for o in rp.offsets(rp.NEAR_STEP, 0.0, rp.NEAR_MM) if o[0] <= rp.LIMIT_MM + 1e-9]
        tposes = []
        for d, dx, dy in near:
            for face, k, rects in self.orients(board, ic, ms, fp['side']):
                fixed, fps = self.obstacles(field, board, face, rects, dx, dy)
                blocks, small, hard = self.classify_fps(board, fps)
                if fixed or hard or blocks != {'U8412'}:
                    continue
                tposes.append((len(small), d, face, k, dx, dy, sorted(small)))
        tposes.sort()
        fails = Counter()
        tried = 0
        for ns, d, face, k, dx, dy, small in tposes[:a3.MAX_TRIALS]:
            tried += 1
            f = self.build_field({(board, m) for m in self.ic_members[(board, 'U8412')]})
            rects = next(r for fc, kk, r in self.orients(board, ic, ms, fp['side']) if (fc, kk) == (face, k))
            if not self.legal_except(f, board, face, rects, dx, dy, set(small)):
                fails['target pose not free once U8412 is lifted'] += 1
                continue
            for ref, c in rects:
                f.add(board, face, [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)
            u12 = self.ic_members[(board, 'U8412')]
            f12 = self.fps[(board, 'U8412')]
            done = None
            for d2, dx2, dy2 in rp.offsets(rp.NEAR_STEP, 0.0, rp.LIMIT_MM):
                for face2, k2, rects2 in self.orients(board, 'U8412', u12, f12['side']):
                    fixed, fps = self.obstacles(f, board, face2, rects2, dx2, dy2)
                    blocks, small2, hard = self.classify_fps(board, fps)
                    if fixed or hard or len(blocks) > 1 or (blocks & self.buffer_ics) or blocks & {ic, 'U8412'}:
                        continue
                    done = (d2, face2, k2, dx2, dy2, sorted(blocks), sorted(small2), rects2)
                    break
                if done:
                    break
            if not done:
                fails['U8412 has no pose within 24 mm even with one more block displaced'] += 1
                continue
            d2, face2, k2, dx2, dy2, blocks, small2, rects2 = done
            g = self.build_field({(board, m) for m in self.ic_members[(board, 'U8412')]} |
                                 {(board, m) for b in blocks for m in self.ic_members[(board, b)]})
            for ref, c in rects:
                g.add(board, face, [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)
            if not self.legal_except(g, board, face2, rects2, dx2, dy2, set(small2) | set(small)):
                fails['U8412 pose not free once the third block is lifted'] += 1
                continue
            for ref, c in rects2:
                g.add(board, face2, [round(v, 4) for v in p2.shift(c, dx2, dy2)], [], ref)
            moved = [{'ic': 'U8412', 'face': face2, 'turn_deg': k2, 'origin': [r2(f12['origin'][0] + dx2), r2(f12['origin'][1] + dy2)],
                      'moved_mm': r2(d2), 'shift_mm': [dx2, dy2], 'members': u12}]
            ok = True
            for b in blocks:
                bp = a3.A3.move_block(self, g, board, b)
                if bp is None:
                    fails['third block %s has no legal pose within 24 mm' % b] += 1
                    ok = False
                    break
                moved.append(dict(bp, ic=b, members=self.ic_members[(board, b)]))
            if not ok:
                continue
            parts = []
            for ref in sorted(set(small) | set(small2)):
                m, cy = self.move_within(g, board, ref)
                if m is None:
                    fails['passive %s has no legal pose within 24 mm' % ref] += 1
                    ok = False
                    break
                g.add(board, m['face'], cy, [], ref)
                parts.append(m)
            if ok:
                return {'result': 'fits within 24 mm', 'pose': {'face': face, 'turn_deg': k, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                                                                'moved_mm': r2(d), 'shift_mm': [dx, dy]},
                        'blocks_moved': moved, 'passives_moved': parts, 'chain': True, 'candidates': len(tposes), 'trials': tried}
        out = dict(res0)
        out['chain_search'] = {'candidates': len(tposes), 'trials': tried, 'failures': dict(sorted(fails.items(), key=lambda x: (-x[1], x[0])))}
        return out

    def run(self):
        self.prepare()
        out = []
        for ic in TARGETS:
            row = self.a2[ic]
            res = self.target(row['board'], ic)
            out.append({'board': row['board'], 'ic': ic, 'function': row['function'], 'block': row['block'], **res})
        return out


def build():
    s = A4()
    res = s.run()
    return {'schema_version': 1, 'model': rp.MODEL,
            'status': 'STUDY (MC04-S8 Part A4): courtyard level on unvalidated drafts; no board changed; nothing adopted',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/replacement_a4.py',
            'rules': {'ruled_first': list(a2.RULED) + list(a3.RULED_A2) + ['U4647 (with U4502 and R4516)'],
                      'relaxations': {'U5209': 'R8263 may move again: within 24 mm of its 6093081c position, no farther from %s than before the gate moved it' % R8263_PARTNER,
                                      'U5210': 'C5210 may be displaced within 24 mm; added run on %s under %g mm' % (C5210_HIZ_NET, HIZ_LIMIT_MM),
                                      'U8409': 'a chain of up to three IC blocks (target, U8412, one more), each within 24 mm, none an input buffer'}},
            'all_within_rules': all(r['result'] == 'fits within 24 mm' for r in res),
            'targets': res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result-a4.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s8_replacement/replacement_a4.py')
        print('result-a4.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print('all within rules', d['all_within_rules'])
    for r in d['targets']:
        print(r['ic'], r['result'], r.get('pose', {}).get('moved_mm'), [(b['ic'], b['moved_mm']) for b in r.get('blocks_moved', [])],
              [(m['ref'], m['moved_mm'], m.get('relaxation')) for m in r.get('passives_moved', [])], r.get('trial_failures'), r.get('chain_search'))


if __name__ == '__main__':
    main()
