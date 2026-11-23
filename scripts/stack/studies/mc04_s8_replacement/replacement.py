#!/usr/bin/env python3
"""MC04-S8 Part A: a study of the 15 ICs that have no position after stage 7 (no board change).

For each open re-placement of design/stack/gate-a-open-items.json the IC moves as one rigid block with its decouplers
and its cell-local passives (resistors and capacitors on its board whose signal nets all touch the IC, within
BLOCK_RADIUS_MM of it). The search uses the link gate's re-placement obstacle model (links_gate_part2.Field: board
outlines, footprints at the obstacle model's courtyard growth, panel hardware, the fixing keep-outs including the
ruled sleeves, and every placed link's field, tail, slot and latch margin), with the parts the gate re-placed at
their new courtyards. Blocks are placed one after another in the gate's DS-97 order; each found pose is fixed
before the next block. Classification (MC04-S8 brief, Part A item 3):
  (i)   a legal pose within 24 mm, nothing displaced;
  (ii)  a legal pose only beyond 24 mm;
  (iii) within 24 mm only by displacing small passives (listed, with their own nearest moves);
  (iv)  no legal pose on the board (free-area shortfall).
Writes result.json beside this file; --check verifies it. Courtyard level on unvalidated drafts."""
from __future__ import annotations
import argparse
from collections import defaultdict
import io
import json
import math
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parents[4]
GEOM = ROOT / 'scripts/stack/geometry'
sys.path.insert(0, str(GEOM))
import links_gate as lg  # noqa: E402
import links_gate_part2 as p2  # noqa: E402
import stackgeom as sg  # noqa: E402

OUT = Path(__file__).with_name('result.json')
MODEL = ('link-era model (links_gate_part2.Field, GH headers dropped, gate-displaced parts at paper positions); '
         'not checked against the interim boards')
LIMIT_MM = 24.0
BLOCK_RADIUS_MM = 12.0
NEAR_STEP, NEAR_MM = 0.5, 40.0
FAR_STEP, FAR_MM = 1.0, 160.0
RAILS = {'AGND', '+12V', '-12V', '+5V', 'GND', None}
BOARD_FILE = {'K': 'osc-core', 'JL': 'osc-jack-left', 'JR': 'osc-jack-right'}
EVICTABLE_MAX_AREA_MM2 = 12.0
# MC04-S10 Revision 1: the S8 and S9 studies are records of the link-era model before the S10 link moves. They read
# the gate, the Gate A list and every link-gate input as of this commit (the last before S10 changed them), so their
# --check stays reproducible; the checks of the current record (member_faces.py, board_conflicts.py, the S10 overlay)
# set `snapshot = None` and read the current files.
SNAPSHOT = '8243acdf'
SNAPSHOT_PATHS = ('design/partition', 'design/grid', 'design/mechanical', 'design/stack', 'design/power', 'design/reports',
                  'circuit/routing/osc-pcb-current-checkpoint.json') + tuple(sg.BOARD_FILES.values())


def snapshot_root(rev=SNAPSHOT):
    """A read-only copy of the inputs at `rev` (git archive), made once per machine and commit."""
    d = Path(tempfile.gettempdir()) / f'zudo-osc-hole-field-snapshot-{rev}'
    if not (d / '.complete').exists():
        d.mkdir(parents=True, exist_ok=True)
        tar = subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar', rev, '--', *SNAPSHOT_PATHS],
                             capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(tar)) as t:
            t.extractall(d)
        (d / '.complete').write_text(rev + '\n')
    return d


def r2(v):
    return round(v, 2)


def offsets(step, rmin, rmax):
    n = int(math.ceil(rmax / step))
    out = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            d = math.hypot(i * step, j * step)
            if rmin - 1e-9 <= d <= rmax + 1e-9 and not (rmin > 0 and d < rmin - 1e-9):
                out.append((round(d, 4), round(i * step, 4), round(j * step, 4)))
    return sorted(out)


def mirror(rect, ox):
    return [2 * ox - rect[2], rect[1], 2 * ox - rect[0], rect[3]]


class Study:
    snapshot = SNAPSHOT  # None: the current files (the checks of the current record)

    def __init__(self):
        self.root = root = snapshot_root(self.snapshot) if self.snapshot else ROOT
        self.inp = inp = lg.load_inputs(root)
        p2.load_part2_inputs(inp)
        sites = lg.gate_sites(inp, lg.RECORD['allocation'])
        model = lg.GateModel(inp, sites, fixings=lg.RECORD['fixings'], compliance=lg.RECORD['compliance'])
        self.ctx = lg.Ctx(inp, model, dict(lg.RECORD))
        self.gate = json.loads((root / 'design/stack/geometry/links/link-gate.json').read_text())
        self.out = self.gate['links']
        io = json.loads((root / 'design/reports/io-partition.json').read_text())
        self.pk = {p['ref']: p for p in io['physical_packages']}
        self.pins = defaultdict(dict)
        for u in io['package_units']:
            self.pins[u['ref']].update(u['pins'])
        self.net_refs = defaultdict(set)
        for r, ps in self.pins.items():
            for n in ps.values():
                self.net_refs[n].add(r)
        self.fps = {(b, f['ref']): f for b in p2.SCOPE_BOARDS for f in inp['ci']['boards'][b]}
        self.items = [i for i in json.loads((root / 'design/stack/gate-a-open-items.json').read_text())['items']
                      if i['kind'] == 'open re-placement (re-route)']
        self.rows = {(r['board'], r['ref']): r for r in self.gate['replacement']['footprints']}

    # ------------------------------------------------------------------ blocks
    def block(self, board, ic):
        sig = {n for n in self.pins[ic].values() if n not in RAILS}
        o = self.fps[(board, ic)]['origin']
        dec = sorted(r for r, q in self.pk.items() if q.get('decouples_ref') == ic and (board, r) in self.fps)
        local, left = [], []
        for n in sorted(sig):
            for r in sorted(self.net_refs[n]):
                if r == ic or r in dec or (board, r) not in self.fps:
                    continue
                other = {m for m in self.pins[r].values() if m not in RAILS}
                d = math.dist(self.fps[(board, r)]['origin'], o)
                if r[0] in 'RC' and other <= sig and d <= BLOCK_RADIUS_MM:
                    local.append(r)
                else:
                    left.append(r)
        return dec, sorted(set(local)), sorted(set(left) - set(local))

    ROLES = {  # from the IC's nets (listed in each row) and its MPN
        'U1318': 'input buffer (precision OPA4197: O3 1V/oct sense buffer)',
        'U1415': 'signal stage (O4 sine shaper: sum, difference and gain)',
        'U4129': 'logic (E1 gate logic, SN74HC00)', 'U4417': 'logic (E4 gate logic, SN74HC00)',
        'U4433': 'logic (E4 loop/clock synchroniser, SN74HC74)', 'U4524': 'logic (E5 gate logic, SN74HC00)',
        'U4526': 'logic (E5 hold/ready logic, SN74HC00)', 'U4527': 'logic (E5 curve/rise logic, SN74HC00)',
        'U4623': 'logic (E6 gate logic, SN74HC00)', 'U4635': 'logic (E6 top/bottom synchroniser, SN74HC74)',
        'U4647': 'output stages and indicator driver (E6 general outputs 1-3 through 499 ohm isolation pairs; unit 4 the '
                 'magnitude indicator driving LED D1801 from SIG_BUFFER)',
        'U5110': 'signal stage (W2 fold cells F1-F4)', 'U5209': 'signal stage (W1 pre-gain, drive and folder sum)',
        'U5210': 'signal stage (W1 fold cells F1-F4)',
        'U8409': 'input buffer and VCA drive (M4B channel 1/2 input buffers, wiper sense, drive and feedback)'}

    def function(self, ic):
        p = self.pk[ic]
        sig = sorted({n for n in self.pins[ic].values() if n not in RAILS})
        role = self.ROLES[ic]
        kind = role.split(' (')[0]
        return {'mpn': p['mpn'], 'instance': p['instance'], 'family': p['family'], 'role': role,
                'input_buffer': kind.startswith('input buffer'), 'nets': sig}

    # ------------------------------------------------------------------ search
    def field(self, moving_extra):
        scope = p2.replacement_scope(self.ctx, self.inp, self.out)
        moving = set(scope) | set(moving_extra)
        f = p2.Field(self.ctx, self.inp, self.out, moving)
        for (b, ref), r in self.rows.items():
            if r['new'] is not None and (b, ref) not in moving_extra:
                f.add(b, r['new_face'], r['new_courtyard'], [], ref)
        return f

    face_aware = False  # MC04-S8 Revision 7: True keeps each member on its own face relative to the IC

    def mf(self, board, ref, face):
        """The face of block member `ref` when its block lies on `face`: a member on the IC's face follows the block, a
        member on the other face takes the other face (face-aware mode only; otherwise every member takes `face`)."""
        if self.face_aware and getattr(self, 'rel', {}).get((board, ref)):
            return 'B' if face == 'F' else 'F'
        return face

    def shapes(self, board, refs, face0, ic):
        """Member courtyards about the IC origin on the IC's own face, and mirrored for the other face. Records, per
        member, whether it sits on the other face than the IC (used by mf)."""
        o = self.fps[(board, ic)]['origin']
        if not hasattr(self, 'rel'):
            self.rel = {}
        for r in refs:
            self.rel[(board, r)] = self.fps[(board, r)]['side'] != self.fps[(board, ic)]['side']
        own = [(r, self.fps[(board, r)]['courtyard'] or p2.fp_bbox(self.fps[(board, r)])) for r in refs]
        return {face0: own, ('B' if face0 == 'F' else 'F'): [(r, mirror(c, o[0])) for r, c in own]}

    def legal(self, field, board, face, rects, dx, dy):
        for ref, c in rects:
            if field.blocked(board, self.mf(board, ref, face), [round(v, 4) for v in p2.shift(c, dx, dy)], []):
                return False
        return True

    def blockers(self, field, board, face, rects, dx, dy):
        """Every obstacle a pose meets: ('fp', ref) entries are footprints, anything else is fixed."""
        hits = set()
        block_face = face
        for ref, c in rects:
            face = self.mf(board, ref, block_face)
            cy = [round(v, 4) for v in p2.shift(c, dx, dy)]
            if not field.model.inside(board, cy, field.margin):
                return None
            g = sg.grow(cy, field.gap)
            for rect, payload in field.idx[(board, face)].near(cy):
                if payload[0] == 'circle':
                    x, y, rad = payload[1]
                    if sg.circle_rect_depth(x, y, rad, cy) > 1e-9:
                        return None
                elif sg.inter(cy, rect):
                    if payload[0] == 'fp' and not payload[2].startswith('re-placed'):
                        hits.add(payload[2].split(' ')[-1])
                    else:
                        return None
            lk = field.links.get((board, face))
            if lk and any(sg.inter(g, rect) for rect, _ in lk.near(g)):
                return None
        return hits

    def evictable(self, board, ref):
        f = self.fps.get((board, ref))
        if f is None or ref[:1] not in ('R', 'C', 'D') or any(p['type'] in ('thru_hole', 'np_thru_hole') for p in f['pads']):
            return False
        c = f['courtyard'] or p2.fp_bbox(f)
        return (c[2] - c[0]) * (c[3] - c[1]) <= EVICTABLE_MAX_AREA_MM2

    def nearest(self, field, board, sh, faces, offs):
        for d, dx, dy in offs:
            for face in faces:
                if self.legal(field, board, face, sh[face], dx, dy):
                    return d, face, dx, dy
        return None

    def run(self):
        order = [(i['board'], i['ref']) for i in self.items]
        blocks = {k: self.block(*k) for k in order}
        members = {k: [k[1]] + blocks[k][0] + blocks[k][1] for k in order}
        extra = {(b, r) for (b, _), ms in members.items() for r in ms}
        field = self.field(extra)
        near = offsets(NEAR_STEP, 0.0, NEAR_MM)
        far = offsets(FAR_STEP, NEAR_MM, FAR_MM)
        lim = [o for o in near if o[0] <= LIMIT_MM + 1e-9]
        results = []
        for board, ic in order:
            dec, local, left = blocks[(board, ic)]
            refs = members[(board, ic)]
            fp = self.fps[(board, ic)]
            face0 = fp['side']
            other = 'B' if face0 == 'F' else 'F'
            sh = self.shapes(board, refs, face0, ic)
            area = sum((c[2] - c[0]) * (c[3] - c[1]) for _, c in sh[face0])
            row = {'board': board, 'ic': ic, 'function': self.function(ic), 'old': [r2(v) for v in fp['origin']],
                   'face': face0, 'why': self.rows[(board, ic)]['why'],
                   'block': {'decouplers': dec, 'cell_local': local, 'members': refs, 'courtyard_area_mm2': r2(area)},
                   'stays': [{'ref': r, 'distance_from_ic_mm': r2(math.dist(self.fps[(board, r)]['origin'], fp['origin']))} for r in left]}
            cands = {}
            for face in (face0, other):
                hit = self.nearest(field, board, sh, [face], near) or self.nearest(field, board, sh, [face], far)
                if hit:
                    d, f, dx, dy = hit
                    cands[f] = {'face': f, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                                'moved_mm': r2(d), 'shift_mm': [dx, dy]}
            row['nearest_legal'] = [cands[f] for f in (face0, other) if f in cands]
            best = min(cands.values(), key=lambda c: (c['moved_mm'], c['face'] != face0)) if cands else None
            disp = None
            if best is None or best['moved_mm'] > LIMIT_MM:
                opts = []
                for d, dx, dy in lim:
                    for face in (face0, other):
                        h = self.blockers(field, board, face, sh[face], dx, dy)
                        if h and all(self.evictable(board, r) for r in h):
                            opts.append((len(h), d, face, dx, dy, sorted(h)))
                    if opts and d > min(o[1] for o in opts) + 6.0:
                        break
                if opts:
                    n, d, face, dx, dy, h = min(opts)
                    disp = {'face': face, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                            'moved_mm': r2(d), 'shift_mm': [dx, dy], 'displaces': h}
            if best and best['moved_mm'] <= LIMIT_MM:
                cls, chosen = '(i)', best
            elif disp:
                cls, chosen = '(iii)', disp
            elif best:
                cls, chosen = '(ii)', best
            else:
                cls, chosen = '(iv)', None
            row['class'] = cls
            if disp:
                row['displacing_option'] = disp
            if cls == '(ii)':
                row['locality_condition'] = ('input-buffer conditions of Revision 2 item 3 (input passives at the cell end, '
                                             'ground-flanked run, added run capacitance under 50 pF)'
                                             if row['function']['input_buffer']
                                             else 'an interim-GH locality acceptance beyond 24 mm (Revision 6 item 4 pattern)')
            if cls == '(iv)':
                free = self.free_area(field, board)
                row['shortfall'] = {'block_area_mm2': r2(area), 'note': 'no legal block pose on either face within %g mm' % FAR_MM,
                                    'largest_free_window_mm2': free}
            if chosen:
                dx, dy = chosen['shift_mm']
                row['chosen'] = chosen
                row['stays_after'] = [{'ref': s['ref'], 'distance_from_ic_mm': r2(math.dist(self.fps[(board, s['ref'])]['origin'],
                                                                                             (fp['origin'][0] + dx, fp['origin'][1] + dy)))}
                                      for s in row['stays']]
                if cls == '(iii)':
                    for r in chosen['displaces']:
                        field_moves = row.setdefault('displaced_moves', [])
                        field_moves.append(self.single_move(field, board, r))
                for ref, c in sh[chosen['face']]:
                    field.add(board, self.mf(board, ref, chosen['face']), [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)
            results.append(row)
        return results

    def single_move(self, field, board, ref):
        f = self.fps[(board, ref)]
        c = f['courtyard'] or p2.fp_bbox(f)
        for d, dx, dy in offsets(0.25, 0.0, 25.0):
            for face in (f['side'], 'B' if f['side'] == 'F' else 'F'):
                cy = [round(v, 4) for v in p2.shift(c if face == f['side'] else mirror(c, f['origin'][0]), dx, dy)]
                if not field.blocked(board, face, cy, []):
                    field.add(board, face, cy, [], ref)
                    return {'ref': ref, 'face': face, 'origin': [r2(f['origin'][0] + dx), r2(f['origin'][1] + dy)], 'moved_mm': r2(d)}
        return {'ref': ref, 'face': None, 'origin': None, 'moved_mm': None}

    def free_area(self, field, board):
        return None

    # ------------------------------------------------------------------ region fill
    def fill(self, results):
        out = {}
        for board, bid in BOARD_FILE.items():
            regions = json.loads((ROOT / 'design/boards' / f'{bid}.json').read_text())['regions']
            fps = [f for f in self.inp['ci']['boards'][board]]
            moved = {}
            for r in results:
                if r['board'] == board and r.get('chosen'):
                    dx, dy = r['chosen']['shift_mm']
                    for ref in r['block']['members']:
                        moved[ref] = (dx, dy, r['chosen']['face'])
            for reg in regions:
                inst = reg['instance']
                if not any(r['function']['instance'] == inst and r['board'] == board for r in results):
                    continue
                x0, y0, x1, y1 = reg['rect']; side = reg['side'][0]
                def occ(shift):
                    a = 0.0
                    for f in fps:
                        c = f['courtyard'] or p2.fp_bbox(f)
                        if not c:
                            continue
                        s = f['side']
                        if shift and f['ref'] in moved:
                            dx, dy, s = moved[f['ref']]
                            c = p2.shift(c, dx, dy)
                        if s != side:
                            continue
                        ix = max(0.0, min(c[2], x1) - max(c[0], x0)); iy = max(0.0, min(c[3], y1) - max(c[1], y0))
                        a += ix * iy
                    return a
                area = (x1 - x0) * (y1 - y0)
                b, a = occ(False), occ(True)
                out.setdefault(board, []).append({'instance': inst, 'side': reg['side'], 'rect': [r2(v) for v in reg['rect']],
                                                  'area_mm2': r2(area), 'occupied_before_mm2': r2(b), 'occupied_after_mm2': r2(a),
                                                  'fill_before_percent': r2(100 * b / area), 'fill_after_percent': r2(100 * a / area)})
        return out


def build():
    s = Study()
    res = s.run()
    counts = defaultdict(int)
    for r in res:
        counts[r['class']] += 1
    return {'schema_version': 1, 'model': MODEL,
            'status': 'STUDY (MC04-S8 Part A): courtyard level on unvalidated drafts; no board changed; nothing adopted',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/replacement.py',
            'rules': {'limit_mm': LIMIT_MM, 'block': 'IC + decouplers + cell-local R/C (signal nets all on the IC) within %g mm' % BLOCK_RADIUS_MM,
                      'search': 'grid offsets %g mm to %g mm, then %g mm to %g mm, both faces (other face mirrored about the IC origin)'
                                % (NEAR_STEP, NEAR_MM, FAR_STEP, FAR_MM),
                      'obstacles': 'links_gate_part2.Field (outline, footprints at courtyard growth, panel hardware, fixing and sleeve '
                                   'keep-outs, link fields, tails, slots and latch margins) with the gate re-placements; blocks placed in order',
                      'evictable': 'R, C and D footprints (RB/RV/DH included by prefix) up to %g mm2, not through-hole; holes, ICs, connectors and hardware never' % EVICTABLE_MAX_AREA_MM2},
            'counts': dict(sorted(counts.items())), 'ics': res, 'region_fill': s.fill(res)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s8_replacement/replacement.py')
        print('result.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print(d['counts'])
    for r in d['ics']:
        print(r['board'], r['ic'], r['function']['role'][:40], r['class'], r.get('chosen', {}).get('moved_mm'), r.get('chosen', {}).get('displaces'))


if __name__ == '__main__':
    main()
