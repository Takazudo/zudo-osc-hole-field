#!/usr/bin/env python3
"""MC04-S8 Revision 7: face-aware re-search of the mixed-face blocks (link-era model; no board change).

Model: link-era (links_gate_part2.Field, GH headers dropped, gate-displaced parts at paper positions); not checked
against the interim boards.

Face-aware: every block member keeps its face relative to the block's IC and flips with the block (Study.face_aware).
The confirmed poses that pass the member check are applied first (Part A: U4129; A2: U4524, U1318, U4417; A3: U4647
with U4502 and R4516) with their displaced passives. The member check also failed five Part A class (iii) poses (U4433,
U4526, U4527, U4623, U4635): Part A moved their displaced passives before placing the block, so passives landed on the
block's own pose. Those are re-searched the same way. Then, in order, under the rules each was ruled with:
- U1415, U4433, U4526, U4527, U4623, U4635 and U5110: the Revision 1 class (iii) rules with the A2 turns and
  displacement (within 24 mm), the block placed before its displaced passives move;
- U5209: the A3 block-on-block rules with the Revision 3 R8263 relaxation;
- U5210 with the U8409 neighbourhood: the A5 joint search, and the U8409 cheapest option (neighbour limit scan).
A block that lands replaces its old pose ("face-aware re-search, Revision 7"); one that does not goes back to OPEN
(link era) with its proof and cheapest option. Writes result-r7.json; --check verifies it."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a2 as a2  # noqa: E402
import replacement_a3 as a3  # noqa: E402
import replacement_a5 as a5  # noqa: E402
from replacement import p2, r2  # noqa: E402

OUT = Path(__file__).with_name('result-r7.json')
CONFIRMED_A2 = ('U4524', 'U1318', 'U4417')
ACCEPTED_R8 = ('U4433', 'U4526')  # Revision 8 item 1: accepted beyond 24 mm unless a clock or RC timing node is found
ACCEPTED_DS144 = ('U4433',)  # DS-144: its own interim exception (clock input accepted, with conditions)
REASON = 'face-aware re-search, Revision 7'


def timing_nodes(row):
    """Nets of a re-search row's cheapest option that are clock or RC timing nodes."""
    return sorted({e['net'] for e in (row.get('cheapest_option') or {}).get('electrical', []) for k in e['kind'] if 'timing node' in k})


def accepted(row):
    """A re-search row left OPEN whose cheapest option is accepted: Revision 8 (no timing node) or DS-144 (U4433)."""
    return row['result'] != 'lands' and (row['ic'] in ACCEPTED_DS144 or (row['ic'] in ACCEPTED_R8 and not timing_nodes(row)))


class R7(a5.A5):
    face_aware = True

    def prepare(self):
        a3.A3.prepare(self)  # blocks, members, owners, buffers (A3); the lifted set is rebuilt below
        self.mixed, self.overlap = self.withdrawn_checks()
        bad = set(self.mixed) | set(self.overlap)
        self.confirmed_a = tuple(ic for ic in a2.RULED if ic not in bad)
        self.research_order = tuple(r['ic'] for r in self.a['ics'] if r['ic'] in bad)
        self.a3 = {r['ic']: r for r in json.loads(a3.OUT.read_text())['targets']}
        self.a4 = {r['ic']: r for r in json.loads(a5.a4.OUT.read_text())['targets']}
        base = json.loads(__import__('subprocess').run(['git', '-C', str(rp.ROOT), 'show', '6093081c:design/partition/floorplan-candidate.json'],
                                                       capture_output=True, check=True, text=True).stdout)
        self.p0 = {p['ref']: p for p in base['placements']}
        self.mode = None
        u = self.a3['U4647']
        self.u4502 = u['blocks_moved'][0]
        passives = set()
        for ic in self.confirmed_a:
            passives |= {(self.arow[ic]['board'], m['ref']) for m in self.arow[ic].get('displaced_moves', [])}
        for ic in CONFIRMED_A2:
            passives |= {(self.a2[ic]['board'], m['ref']) for m in self.a2[ic]['chosen'].get('displaced_moves', [])}
        passives |= {('JR', m['ref']) for m in u['passives_moved']}
        self.locked_moves = passives
        self.base_extra = {(b, r) for (b, _), ms in self.members.items() for r in ms} | passives | \
            {('JR', m) for m in self.u4502['members']}
        self.done = []  # re-searched blocks placed so far: (board, ic, members, face0, pose, passives, blocks)

    def build_field(self, extra=frozenset(), skip=frozenset()):
        f = self.field(self.base_extra | set(extra))
        self.apply_confirmed(f, skip)
        self.apply_done(f, extra, skip)
        return f

    def confirmed_blocks(self):
        """(board, ic, members, IC face, pose) of the ten confirmed blocks and the U4502 block, in placing order."""
        out = [(self.arow[ic]['board'], ic, self.members[(self.arow[ic]['board'], ic)], self.arow[ic]['face'],
                dict(self.arow[ic]['chosen'], turn_deg=0)) for ic in self.confirmed_a]
        out += [(self.a2[ic]['board'], ic, self.members[(self.a2[ic]['board'], ic)], self.a2[ic]['face'], self.a2[ic]['chosen'])
                for ic in CONFIRMED_A2]
        out.append(('JR', 'U4647', self.members[('JR', 'U4647')], self.a2['U4647']['face'], self.a3['U4647']['pose']))
        out.append(('JR', self.u4502['ic'], self.u4502['members'], self.fps[('JR', self.u4502['ic'])]['side'], self.u4502))
        return out

    def apply_confirmed(self, f, skip=frozenset()):
        """Place the confirmed blocks (and their displaced passives); a (board, ic) in `skip` is left out."""
        for board, ic, members, face0, pose in self.confirmed_blocks():
            if (board, ic) not in skip:
                self.place(f, board, ic, members, face0, pose)
        for ic in self.confirmed_a:
            for m in self.arow[ic].get('displaced_moves', []):
                self.add_part(f, self.arow[ic]['board'], m)
        for ic in CONFIRMED_A2:
            for m in self.a2[ic]['chosen'].get('displaced_moves', []):
                self.add_part(f, self.a2[ic]['board'], m)
        for m in self.a3['U4647']['passives_moved']:
            self.add_part(f, 'JR', m)

    def apply_done(self, f, extra=frozenset(), skip=frozenset()):
        for board, ic, members, face0, pose, passives, blocks in self.done:
            if (board, ic) in skip:
                continue
            if (board, ic) not in extra:
                self.place(f, board, ic, members, face0, pose)
            for b in blocks:
                if (board, b['ic']) not in extra:
                    self.place(f, board, b['ic'], b['members'], self.fps[(board, b['ic'])]['side'], b)
            for m in passives:
                if (board, m['ref']) not in extra:
                    self.add_part(f, board, m)

    def withdrawn_checks(self):
        """The Part A class (iii) poses that fail the face-aware check: blocks with members on the other face than their
        IC (mixed), and blocks whose displaced passives were re-placed onto the block itself (Part A moved them before
        placing the block). Both lists follow the Part A order."""
        mixed, overlap = [], []
        for r in self.a['ics']:
            ic, b = r['ic'], r['board']
            if ic not in a2.RULED or r['class'] != '(iii)':
                continue
            ms = self.members[(b, ic)]
            if any(self.fps[(b, m)]['side'] != self.fps[(b, ic)]['side'] for m in ms):
                mixed.append(ic)
            pose = dict(r['chosen'], turn_deg=0)
            rects = dict(((fc, k), rr) for fc, k, rr in self.orients(b, ic, ms, r['face']))[(pose['face'], 0)]
            block = [(self.mf(b, ref, pose['face']), p2.shift(c, *pose['shift_mm'])) for ref, c in rects]
            for m in r.get('displaced_moves', []):
                fp = self.fps[(b, m['ref'])]
                cy = fp['courtyard'] or p2.fp_bbox(fp)
                if m['face'] != fp['side']:
                    cy = rp.mirror(cy, fp['origin'][0])
                mr = p2.shift(cy, m['origin'][0] - fp['origin'][0], m['origin'][1] - fp['origin'][1])
                if any(face == m['face'] and a5.sg.inter(rect, mr) for face, rect in block):
                    overlap.append(ic)
                    break
        return mixed, overlap

    def load_done(self):
        """The Revision 7 poses that landed, the Revision 8 acceptance and the DS-144 acceptance, from result-r7.json
        (for the checks)."""
        doc = json.loads(OUT.read_text())
        self.done = []
        for r in doc['research']:
            if r['result'] == 'lands':
                self.done.append((r['board'], r['ic'], self.members[(r['board'], r['ic'])], self.fps[(r['board'], r['ic'])]['side'],
                                  r['pose'], r.get('passives_moved', []), r.get('blocks_moved', [])))
        for r in doc['research']:
            if accepted(r):
                self.done.append((r['board'], r['ic'], self.members[(r['board'], r['ic'])], self.fps[(r['board'], r['ic'])]['side'],
                                  r['cheapest_option']['pose'], [], []))
        # S10 study output is diagnostic. A candidate cannot add placements to the accepted S8 scene.
        return doc

    def evictable2(self, board, ref):
        # C5210 (Revision 3) is displaceable only in the U5210/U8409 joint search; R8263 only for U5209 (A4 mode)
        if ref == 'C5210':
            return getattr(self, 'in_joint', False)
        return a5.a4.A4.evictable2(self, board, ref)

    # ------------------------------------------------------------------ re-searches
    def research_a(self, board, ic):
        field = self.build_field()
        legal, disp, _ = self.search(field, board, ic)
        best = legal[0] if legal else None
        row = {'board': board, 'ic': ic, 'rules': 'Revision 1 class (iii) with the A2 turns and displacement',
               'old_pose': {k: self.arow[ic]['chosen'][k] for k in ('face', 'origin', 'moved_mm')},
               'nearest_legal_by_orientation': legal, 'within_24mm': self.census}
        if best and best['moved_mm'] <= rp.LIMIT_MM:
            row.update({'result': 'lands', 'class': '(i)', 'pose': best, 'passives_moved': [], 'reason': REASON})
            self.done.append((board, ic, self.members[(board, ic)], self.arow[ic]['face'], best, [], []))
        elif disp:
            row.update({'result': 'lands', 'class': '(iii)', 'pose': {k: disp[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')},
                        'passives_moved': disp['displaced_moves'], 'reason': REASON})
            self.done.append((board, ic, self.members[(board, ic)], self.arow[ic]['face'], disp, disp['displaced_moves'], []))
        else:
            row.update({'result': 'OPEN (link era)', 'class': None,
                        'proof': {'grid_caveat': a5.GRID_CAVEAT, 'nearest_legal_mm': best['moved_mm'] if best else None,
                                  'displacement_options_tried': self.census.get('displacement_options'),
                                  'note': 'no pose within 24 mm with the A2 displacement rule on this grid (the displacement options '
                                          'are tried fewest-displaced first up to %d)' % a2.MAX_OPTIONS},
                        'cheapest_option': None if not best else {'pose': best, 'electrical': self.facts(board, ic, best)}})
        return row

    def research_u5209(self):
        self.mode = 'U5209'
        res = self.target('K', 'U5209')
        self.mode = None
        row = {'board': 'K', 'ic': 'U5209', 'rules': 'A3 block-on-block rules with the Revision 3 R8263 relaxation',
               'old_pose': {k: self.a4['U5209']['pose'][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')}}
        if res['result'] == 'fits within 24 mm':
            row.update({'result': 'lands', 'pose': res['pose'], 'blocks_moved': res['blocks_moved'],
                        'passives_moved': res['passives_moved'], 'reason': REASON})
            self.done.append(('K', 'U5209', self.members[('K', 'U5209')], self.fps[('K', 'U5209')]['side'], res['pose'],
                              res['passives_moved'], res['blocks_moved']))
        else:
            row.update({'result': 'OPEN (link era)', 'proof': dict({k: res.get(k) for k in ('candidates', 'trials', 'trial_failures')},
                                                                  grid_caveat=a5.GRID_CAVEAT),
                        'smallest_obstacle_set': res.get('smallest_obstacle_set'),
                        'cheapest_option': self.far_option('K', 'U5209')})
        return row

    def far_option(self, board, ic):
        """The nearest legal block pose beyond 24 mm (nothing displaced, face-aware, any turn), with its run estimates."""
        field = self.build_field()
        legal, _, _ = self.search(field, board, ic)
        best = legal[0] if legal else None
        return None if best is None else {'pose': best, 'electrical': self.facts(board, ic, best),
                                          'note': 'nearest legal pose with nothing displaced; beyond the 24 mm limit'}

    def run(self):
        self.prepare()
        rows = [self.research_a('K', ic) for ic in self.research_order]
        rows.append(self.research_u5209())
        runs, placed, options, far = self.joint_section()
        return rows, runs, placed, options, far

    def joint_section(self):
        self.in_joint = True
        runs = [self.joint(a5.TARGETS)]
        placed = list(a5.TARGETS) if runs[0]['found'] else []
        if not placed:
            alone = [self.joint((t,)) for t in a5.TARGETS]
            runs += alone
            placed = [next(r['targets'][0] for r in alone if r['found'])] if any(r['found'] for r in alone) else []
        options = []
        for t in a5.TARGETS:
            if t in placed:
                continue
            tried = []
            r = None
            for lim in a5.OPTION_LIMITS:
                r = self.joint(a5.TARGETS, limit_others=lim)
                tried.append({'limit_others_mm': lim, 'found': r['found'], 'nodes': r['nodes']})
                if r['found']:
                    break
            r['for'] = t
            r['limits_scanned'] = tried
            r['grid_caveat'] = a5.GRID_CAVEAT
            if r['found']:
                r['farthest_neighbour_mm'] = max(c['moved_mm'] for ic, c in r['poses'].items() if ic not in a5.TARGETS)
                first = next((x for x in runs if x['found'] and x['targets'] == placed), None)
                if first:
                    r['supersedes'] = {ic: {'recorded': {k: first['poses'][ic][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')},
                                            'option': {k: r['poses'][ic][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')}}
                                       for ic in placed}
                r['neighbour_electrical'] = {}
                for ic, c in sorted(r['poses'].items()):
                    if ic in a5.TARGETS or c['moved_mm'] <= rp.LIMIT_MM:
                        continue
                    self.members[('K', ic)] = self.set_members(ic)
                    r['neighbour_electrical'][ic] = self.facts('K', ic, c)
                    del self.members[('K', ic)]
                prev = [x['limit_others_mm'] for x in tried if not x['found']]
                r['first_found'] = ('the scanned limits %s mm are proved infeasible on the grid; this assignment is the first one found at '
                                    '%g mm, so the true minimum farthest neighbour move on this grid lies in (%s, %s] mm'
                                    % (', '.join('%g' % v for v in prev), r['limit_others_mm'], '%g' % prev[-1] if prev else '24', r['farthest_neighbour_mm']))
            r['fourth_block_alternative'] = 'not evaluated'
            options.append(r)
        self.in_joint = False
        far = {t: self.far_option('K', t) for t in a5.TARGETS if t not in placed}
        return runs, placed, options, far


def build():
    s = R7()
    rows, runs, placed, options, far = s.run()
    return {'schema_version': 1, 'model': rp.MODEL, 'face_aware': True,
            'status': 'STUDY (MC04-S8 Revision 7): face-aware re-search; link-era record; no board changed',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/replacement_r7.py',
            'confirmed_first': list(s.confirmed_a) + list(CONFIRMED_A2) + ['U4647 (with U4502 and R4516)'],
            'withdrawn_mixed_face': s.mixed, 'withdrawn_for_passive_overlap': s.overlap,
            'research': rows, 'joint': {'placed': placed, 'runs': runs, 'options_for_unplaced': options, 'far_poses': far}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result-r7.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s8_replacement/replacement_r7.py')
        print('result-r7.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    for r in d['research']:
        print(r['ic'], r['result'], r.get('class'), (r.get('pose') or {}).get('moved_mm'), (r.get('pose') or {}).get('face'),
              [m['ref'] for m in r.get('passives_moved', [])], [b['ic'] for b in r.get('blocks_moved', [])])
    print('joint placed', d['joint']['placed'])
    for x in d['joint']['runs'] + d['joint']['options_for_unplaced']:
        print(x['targets'], x['limit_others_mm'], x['found'], x['nodes'], {k: (v['moved_mm'], v['face'], v['turn_deg']) for k, v in x.get('poses', {}).items()})


if __name__ == '__main__':
    main()
