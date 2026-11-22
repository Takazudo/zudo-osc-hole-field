#!/usr/bin/env python3
"""MC04-S8 Part A2: the seven class (ii) ICs searched again (Revision 1 of the S8 brief; no board change).

The board is first set up as Part B would leave it: the eight poses ruled in Revision 1 item 1 (K:U4129 and the seven
class (iii) ICs) are placed with their displaced passives, from Part A's result.json. Each class (ii) IC is then
searched again, in the same order, with:
- block turns of 0, 90, 180 and 270 degrees on both faces (the other face mirrored about the IC origin);
- displacement of any unlocked SMD R, C or D footprint up to 12 mm2 that is not a decoupler, provided each displaced
  part finds its own legal pose within 24 mm of where it was (both faces, nearest first).
Blocks are as in Part A (decouplers plus cell-local R/C within 12 mm). For an IC still beyond 24 mm the electrical
facts of Revision 1 item 3 are given: per signal net the added on-board run (1.5 x the change in half-perimeter
length over the part origins on its board) and its capacitance at an ASSUMED 0.20 pF/mm, with the node kind.
Writes result-a2.json; --check verifies it. Courtyard level on unvalidated drafts."""
from __future__ import annotations
import argparse
import copy
from collections import defaultdict
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
from replacement import p2, r2  # noqa: E402

OUT = Path(__file__).with_name('result-a2.json')
CLASS_II = ('U1318', 'U4417', 'U4524', 'U5209', 'U5210', 'U8409', 'U4647')
RULED = ('U4129', 'U1415', 'U4433', 'U4526', 'U4527', 'U4623', 'U4635', 'U5110')
TURNS = (0, 90, 180, 270)
PF_PER_MM, ROUTE_FACTOR, LIMIT_PF = 0.20, 1.5, 50.0
LED_MPNS = ('APHHS1005QWF/D', 'APG1005SEC/E-T')
MAX_OPTIONS = 60


def rot(rect, origin, k):
    for _ in range(k // 90):
        rect = p2.turn(rect, origin)
    return rect


def rot_pt(pt, origin, k):
    x, y = pt
    for _ in range(k // 90):
        x, y = origin[0] - (y - origin[1]), origin[1] + (x - origin[0])
    return x, y


class A2(rp.Study):
    def setup(self):
        self.a = json.loads(rp.OUT.read_text())
        self.arow = {r['ic']: r for r in self.a['ics']}
        order = [(i['board'], i['ref']) for i in self.items]
        self.blocks = {k: self.block(*k) for k in order}
        self.members = {k: [k[1]] + self.blocks[k][0] + self.blocks[k][1] for k in order}
        disp = {(self.arow[ic]['board'], m['ref']) for ic in RULED for m in self.arow[ic].get('displaced_moves', [])}
        self.locked_moves = disp
        extra = {(b, r) for (b, _), ms in self.members.items() for r in ms} | disp
        f = self.field(extra)
        for ic in RULED:
            row = self.arow[ic]
            board = row['board']
            c = row['chosen']
            sh = self.shapes(board, self.members[(board, ic)], row['face'], ic)
            dx, dy = c['shift_mm']
            for ref, rect in sh[c['face']]:
                f.add(board, c['face'], [round(v, 4) for v in p2.shift(rect, dx, dy)], [], ref)
            for m in row.get('displaced_moves', []):
                fp = self.fps[(board, m['ref'])]
                cy = fp['courtyard'] or p2.fp_bbox(fp)
                if m['face'] != fp['side']:
                    cy = rp.mirror(cy, fp['origin'][0])
                f.add(board, m['face'], [round(v, 4) for v in p2.shift(cy, m['origin'][0] - fp['origin'][0], m['origin'][1] - fp['origin'][1])], [], m['ref'])
        return f

    def orientations(self, board, ic, face0):
        o = self.fps[(board, ic)]['origin']
        sh = self.shapes(board, self.members[(board, ic)], face0, ic)
        out = []
        for face in (face0, 'B' if face0 == 'F' else 'F'):
            for k in TURNS:
                out.append((face, k, [(r, [round(v, 4) for v in rot(c, o, k)]) for r, c in sh[face]]))
        return out

    def evictable2(self, board, ref):
        if not self.evictable(board, ref) or (board, ref) in self.locked_moves:
            return False
        p = self.pk.get(ref, {})
        return not p.get('decouples_ref') and not p.get('panel_uid')

    def move_within(self, field, board, ref, limit=rp.LIMIT_MM):
        f = self.fps[(board, ref)]
        c = f['courtyard'] or p2.fp_bbox(f)
        for d, dx, dy in rp.offsets(0.25, 0.0, limit):
            for face in (f['side'], 'B' if f['side'] == 'F' else 'F'):
                cy = [round(v, 4) for v in p2.shift(c if face == f['side'] else rp.mirror(c, f['origin'][0]), dx, dy)]
                if not field.blocked(board, face, cy, []):
                    return {'ref': ref, 'face': face, 'origin': [r2(f['origin'][0] + dx), r2(f['origin'][1] + dy)],
                            'moved_mm': r2(d)}, cy
        return None, None

    def search(self, field, board, ic):
        fp = self.fps[(board, ic)]
        orients = self.orientations(board, ic, fp['side'])
        near = rp.offsets(rp.NEAR_STEP, 0.0, rp.NEAR_MM)
        far = rp.offsets(rp.FAR_STEP, rp.NEAR_MM, rp.FAR_MM)
        best = {}
        for face, k, rects in orients:
            for offs in (near, far):
                hit = next(((d, dx, dy) for d, dx, dy in offs if self.legal(field, board, face, rects, dx, dy)), None)
                if hit:
                    d, dx, dy = hit
                    best[(face, k)] = {'face': face, 'turn_deg': k, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                                       'moved_mm': r2(d), 'shift_mm': [dx, dy]}
                    break
        legal = sorted(best.values(), key=lambda c: (c['moved_mm'], c['face'] != fp['side'], c['turn_deg']))
        opts = []
        for d, dx, dy in [o for o in near if o[0] <= rp.LIMIT_MM + 1e-9]:
            for face, k, rects in orients:
                h = self.blockers(field, board, face, rects, dx, dy)
                if h and all(self.evictable2(board, r) for r in h):
                    opts.append((len(h), d, face, k, dx, dy, sorted(h)))
        opts.sort()
        self.census = self.count_blockers(field, board, orients, near)
        self.census['displacement_options'] = len(opts)
        tried = 0
        for n, d, face, k, dx, dy, h in opts:
            if tried >= MAX_OPTIONS:
                break
            tried += 1
            trial = copy.deepcopy(field)
            rects = next(r for f, kk, r in orients if (f, kk) == (face, k))
            for ref, c in rects:
                trial.add(board, face, [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)
            moves = []
            for ref in h:
                m, cy = self.move_within(trial, board, ref)
                if m is None:
                    break
                trial.add(board, m['face'], cy, [], ref)
                moves.append(m)
            else:
                return legal, {'face': face, 'turn_deg': k, 'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)],
                               'moved_mm': r2(d), 'shift_mm': [dx, dy], 'displaces': h, 'displaced_moves': moves,
                               'options_tried': tried}, trial
        return legal, None, None

    def count_blockers(self, field, board, orients, near):
        """What blocks the poses within 24 mm: the first obstacle met at each offset and turn."""
        tally = defaultdict(int)
        fps = defaultdict(int)
        for d, dx, dy in [o for o in near if o[0] <= rp.LIMIT_MM + 1e-9]:
            for face, k, rects in orients:
                why = None
                for _, c in rects:
                    why = field.blocked(board, face, [round(v, 4) for v in p2.shift(c, dx, dy)], [])
                    if why:
                        break
                if why is None:
                    tally['free'] += 1
                elif why == 'outline':
                    tally['outline'] += 1
                elif any(t in why for t in ('field of', 'tail of', 'slot of', 'latch margin of')):
                    tally['link keep-out'] += 1
                elif 'fixing keep-out' in why or 'hardware' in why or why.startswith('hole'):
                    tally['fixing, hardware or hole'] += 1
                elif why.startswith('re-placed'):
                    tally['a re-placed or ruled part'] += 1
                else:
                    tally['footprint'] += 1
                    fps[why.split(' ')[-1]] += 1
        top = sorted(fps.items(), key=lambda x: (-x[1], x[0]))[:8]
        return {'poses_checked': sum(tally.values()), 'first_obstacle': dict(sorted(tally.items())),
                'most_frequent_footprints': [{'ref': r, 'poses': n, 'evictable': self.evictable2(board, r)} for r, n in top]}

    # ------------------------------------------------------------------ electrical facts
    def new_origin(self, board, ic, ref, pose):
        o = self.fps[(board, ic)]['origin']
        p = self.fps[(board, ref)]['origin']
        if pose['face'] != self.fps[(board, ic)]['side']:
            p = (2 * o[0] - p[0], p[1])
        x, y = rot_pt(p, o, pose['turn_deg'])
        return x + pose['shift_mm'][0], y + pose['shift_mm'][1]

    def hpwl(self, pts):
        xs = [x for x, _ in pts]; ys = [y for _, y in pts]
        return (max(xs) - min(xs)) + (max(ys) - min(ys)) if len(pts) > 1 else 0.0

    def facts(self, board, ic, pose):
        units = [u for u in self.io_units if u['ref'] == ic]
        kinds = {}
        mpn = self.pk[ic]['mpn']
        if mpn.startswith('SN74HC'):
            outs = {'SN74HC00DR': {'3', '6', '8', '11'}, 'SN74HC74DR': {'5', '6', '8', '9'}}.get(mpn, set())
            clocks = {'SN74HC74DR': {'3', '11'}}.get(mpn, set())
            for u in units:
                for pin, n in u['pins'].items():
                    if n and n not in rp.RAILS:
                        kinds.setdefault(n, set()).add('logic output' if pin in outs else 'logic input')
                        if pin in clocks:
                            kinds[n].add('timing node (clock input)')
            units = []
        for u in units:
            role = u.get('role') or ''
            pins = u['pins']
            plus = {'1': '3', '2': '5', '3': '10', '4': '12'}.get(str(u['unit']))
            minus = {'1': '2', '2': '6', '3': '9', '4': '13'}.get(str(u['unit']))
            out = {'1': '1', '2': '7', '3': '8', '4': '14'}.get(str(u['unit']))
            if plus and pins.get(plus):
                kinds.setdefault(pins[plus], set()).add('high-impedance input' if role.startswith('high_impedance_input')
                                                        else 'non-inverting input')
            if minus and pins.get(minus) and pins.get(minus) != pins.get(out):
                kinds.setdefault(pins[minus], set()).add('feedback/summing node')
            if minus and pins.get(minus) and pins.get(minus) == pins.get(out):
                kinds.setdefault(pins[out], set()).add('follower output')
            elif out and pins.get(out):
                kinds.setdefault(pins[out], set()).add('output')
        members = set(self.members[(board, ic)])
        rows = []
        for n in sorted(kinds):
            if n in rp.RAILS:
                continue
            refs = sorted(r for r in self.net_refs[n] if (board, r) in self.fps)
            before = [tuple(self.fps[(board, r)]['origin']) for r in refs]
            after = [self.new_origin(board, ic, r, pose) if r in members else tuple(self.fps[(board, r)]['origin']) for r in refs]
            k = set(kinds[n])
            if any(r[:1] == 'C' and r not in members for r in refs) and any(x.startswith('logic') for x in k):
                k.add('timing node (RC on the net)')
            if any(w in n for w in ('CLOCK', 'SYNC')):
                k.add('timing node (clock/sync)')
            hb, ha = self.hpwl(before), self.hpwl(after)
            add = ROUTE_FACTOR * (ha - hb)
            rows.append({'net': n, 'kind': sorted(k), 'parts_on_board': refs, 'hpwl_before_mm': r2(hb), 'hpwl_after_mm': r2(ha),
                         'added_run_estimate_mm': r2(add), 'run_after_estimate_mm': r2(ROUTE_FACTOR * ha),
                         'capacitance_after_estimate_pF': r2(ROUTE_FACTOR * ha * PF_PER_MM),
                         'added_capacitance_estimate_pF': r2(add * PF_PER_MM)})
        return rows

    def leds(self, board, ic, pose):
        """LEDs reached from the IC's DRIVE nets through at most one series part, with their distance to the IC. Units
        whose DRIVE net reaches no LED (output stages through series isolation resistors) are listed as such."""
        out = []
        o_new = (pose['origin'][0], pose['origin'][1])
        o_old = self.fps[(board, ic)]['origin']
        lock = {p['uid']: p for p in json.loads((rp.ROOT / 'design/grid/placements.lock.json').read_text())['placements']}
        fl = {p['ref']: p for p in json.loads((rp.ROOT / 'design/partition/floorplan-candidate.json').read_text())['placements']}
        for u in [u for u in self.io_units if u['ref'] == ic]:
            for pin, n in u['pins'].items():
                if not n or not n.endswith('_DRIVE'):
                    continue
                seen = set()
                for r in self.net_refs[n]:
                    for m in ([r] + [x for nn in self.pins[r].values() if nn not in rp.RAILS and nn != n for x in self.net_refs[nn]]):
                        if m in seen or self.pk.get(m, {}).get('mpn') not in LED_MPNS:
                            continue
                        seen.add(m)
                        p = self.pk[m]
                        if p.get('panel_uid') in lock:
                            xy = (lock[p['panel_uid']]['x_mm'], lock[p['panel_uid']]['y_mm']); where = 'panel lock'
                        elif m in fl:
                            xy = (fl[m]['x_mm'], fl[m]['y_mm']); where = fl[m]['board']
                        else:
                            continue
                        out.append({'unit': u['unit'], 'drive_net': n, 'led': m, 'led_at': [r2(v) for v in xy], 'where': where,
                                    'distance_before_mm': r2(math.dist(xy, o_old)), 'distance_after_mm': r2(math.dist(xy, o_new))})
        led_units = {x['unit'] for x in out}
        for u in [u for u in self.io_units if u['ref'] == ic and u['unit'] not in led_units]:
            nets = [n for n in u['pins'].values() if n and n.endswith('_DRIVE')]
            if nets:
                out.append({'unit': u['unit'], 'drive_net': nets[0], 'led': None, 'role': u.get('role'),
                            'note': 'no LED on this unit: the drive net leaves through series isolation resistors '
                                    + ', '.join(sorted(r for r in self.net_refs[nets[0]] if r != ic))})
        return sorted(out, key=lambda x: (x['unit'], x['led'] or ''))

    def run(self):
        io = json.loads((rp.ROOT / 'design/reports/io-partition.json').read_text())
        self.io_units = io['package_units']
        field = self.setup()
        out = []
        for ic in CLASS_II:
            row0 = self.arow[ic]
            board = row0['board']
            legal, disp, trial = self.search(field, board, ic)
            best = legal[0] if legal else None
            if best and best['moved_mm'] <= rp.LIMIT_MM:
                cls, chosen = '(i)', best
            elif disp:
                cls, chosen = '(iii)', disp
                field = trial
            elif best:
                cls, chosen = '(ii)', best
            else:
                cls, chosen = '(iv)', None
            row = {'board': board, 'ic': ic, 'function': row0['function'], 'block': row0['block'], 'old': row0['old'],
                   'face': row0['face'], 'part_a': {'class': row0['class'], 'moved_mm': row0['chosen']['moved_mm']},
                   'class': cls, 'nearest_legal_by_orientation': legal, 'chosen': chosen, 'within_24mm': self.census}
            if disp and cls != '(iii)':
                row['displacing_option'] = disp
            if chosen and cls in ('(i)', '(ii)'):
                sh = dict(((f, k), r) for f, k, r in self.orientations(board, ic, row0['face']))[(chosen['face'], chosen['turn_deg'])]
                dx, dy = chosen['shift_mm']
                for ref, c in sh:
                    field.add(board, chosen['face'], [round(v, 4) for v in p2.shift(c, dx, dy)], [], ref)
            if chosen and chosen['moved_mm'] > rp.LIMIT_MM:
                row['electrical'] = self.facts(board, ic, chosen)
                if row0['function']['input_buffer'] or any(x['net'].endswith('_SENSE') for x in row['electrical']):
                    hi = [x for x in row['electrical'] if 'high-impedance input' in x['kind'] or x['net'].endswith('_SENSE')]
                    row['input_buffer_conditions'] = {
                        'sense_nets': [x['net'] for x in hi],
                        'capacitance_after_estimate_pF': {x['net']: x['capacitance_after_estimate_pF'] for x in hi},
                        'under_50pF': all(x['capacitance_after_estimate_pF'] <= LIMIT_PF for x in hi),
                        'note': 'input passives at the cell end and a ground-flanked run are routing conditions for Part C; the '
                                'capacitance figure is the paper estimate of stage 7 (1.5 x HPWL, 0.20 pF/mm)'}
                if ic == 'U4647':
                    row['leds'] = self.leds(board, ic, chosen)
            out.append(row)
        return out


def build():
    s = A2()
    res = s.run()
    counts = defaultdict(int)
    for r in res:
        counts[r['class']] += 1
    return {'schema_version': 1, 'model': rp.MODEL,
            'status': 'STUDY (MC04-S8 Part A2): courtyard level on unvalidated drafts; no board changed; nothing adopted',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/replacement_a2.py',
            'rules': {'ruled_first': list(RULED), 'turns_deg': list(TURNS), 'limit_mm': rp.LIMIT_MM,
                      'displacement': 'unlocked SMD R/C/D up to %g mm2, not a decoupler, each landing within %g mm of its own position'
                                      % (rp.EVICTABLE_MAX_AREA_MM2, rp.LIMIT_MM),
                      'block': 'as Part A (not shrunk)', 'run_estimate': '1.5 x HPWL over part origins on the board; 0.20 pF/mm ASSUMED'},
            'counts': dict(sorted(counts.items())), 'ics': res}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result-a2.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s8_replacement/replacement_a2.py')
        print('result-a2.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print(d['counts'])
    for r in d['ics']:
        c = r['chosen'] or {}
        print(r['board'], r['ic'], r['class'], c.get('face'), c.get('turn_deg'), c.get('moved_mm'), c.get('displaces'))


if __name__ == '__main__':
    main()
