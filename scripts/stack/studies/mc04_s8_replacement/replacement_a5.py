#!/usr/bin/env python3
"""MC04-S8 Part A5: one joint search for the U8412 neighbourhood (Revision 4 item 1; link-era model; no board change).

Model: link-era (links_gate_part2.Field: GH headers dropped, gate-displaced parts at their paper positions); not checked
against the interim boards (board_conflicts.py shows the poses do not fit there).

Every ruled pose is applied first (Parts A to A4: U4129, the seven class (iii) ICs, U4524, U1318, U4417, U4647 with U4502,
U5209). The set SET (the two targets and the blocks the A3/A4 censuses name) is then searched jointly: each block takes a
candidate pose within 24 mm of its own position (0.5 mm grid, turns 0/90/180/270, either face) whose only obstacles
are other blocks of the set (resolved jointly) and displaceable passives (the A2 rule; C5210 under the Revision 3 rule);
a non-target block may also stay where it is. The search is a complete depth-first search with forward checking
(`solve`): it returns the first assignment in which no two blocks overlap, or proves that none exists over the
candidate grid. Displaced passives are re-placed after an assignment is found (nearest legal pose within 24 mm); an
assignment whose passives cannot all be re-placed is rejected and the search continues. If no assignment places both
targets, each target is searched alone (the other target stays at its position), and the cheapest option for an
unplaced target is measured: the joint search again with the non-target blocks allowed up to OPTION_MM.
Writes result-a5.json; --check verifies it. Courtyard level on unvalidated drafts."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a2 as a2  # noqa: E402
import replacement_a4 as a4  # noqa: E402
from replacement import p2, r2, sg  # noqa: E402

OUT = Path(__file__).with_name('result-a5.json')
TARGETS = ('U5210', 'U8409')
NEIGHBOURS = ('U8412', 'U5208', 'U8408')
OPTION_MM = 40.0
GRID_CAVEAT = ('proof over a 0.5 mm shift grid about each block\'s original origin, with 4 turns and both faces; '
               'continuous poses are not covered')
OPTION_LIMITS = (25.0, 26.0, 27.0, 28.0, 30.0, 32.0, 36.0, 40.0)
MODEL = rp.MODEL


# ---------------------------------------------------------------------- generic complete search
def solve(variables, domains, compatible, accept=lambda assignment: True, stats=None):
    """Complete depth-first search with forward checking. variables: names; domains: {name: [candidate, ...]} in
    preference order; compatible(a, ca, b, cb) -> bool for two variables' candidates; accept(assignment) -> bool for a
    full assignment. Returns the first accepted assignment {name: candidate} in the search order, or None when no
    accepted assignment exists. stats (dict) counts the nodes visited."""
    stats = stats if stats is not None else {}
    stats.setdefault('nodes', 0)

    def rec(assigned, doms):
        if len(assigned) == len(variables):
            return dict(assigned) if accept(dict(assigned)) else None
        var = min((v for v in variables if v not in assigned), key=lambda v: (len(doms[v]), variables.index(v)))
        for cand in doms[var]:
            stats['nodes'] += 1
            nd = {}
            ok = True
            for w in variables:
                if w in assigned or w == var:
                    continue
                nd[w] = [c for c in doms[w] if compatible(var, cand, w, c)]
                if not nd[w]:
                    ok = False
                    break
            if not ok:
                continue
            assigned[var] = cand
            res = rec(assigned, nd)
            del assigned[var]
            if res is not None:
                return res
        return None

    return rec({}, {v: list(domains[v]) for v in variables})


def rects_conflict(ra, rb, gap):
    for fa, a in ra:
        ga = sg.grow(a, gap)
        for fb, b in rb:
            if fa == fb and sg.inter(ga, b):
                return True
    return False


class A5(a4.A4):
    def prepare(self):
        super().prepare()
        self.a4 = {r['ic']: r for r in json.loads(a4.OUT.read_text())['targets']}
        u = self.a4['U5209']
        self.base_extra |= {('K', m['ref']) for m in u['passives_moved']}
        self.locked_moves |= {('K', m['ref']) for m in u['passives_moved']}

    def build_field(self, extra=frozenset()):
        f = super().build_field(extra)
        u = self.a4['U5209']
        self.place(f, 'K', 'U5209', self.members[('K', 'U5209')], self.a2['U5209']['face'], u['pose'])
        for m in u['passives_moved']:
            if ('K', m['ref']) not in extra:
                self.add_part(f, 'K', m)
        return f

    def set_members(self, ic):
        return self.members[('K', ic)] if ('K', ic) in self.members else self.ic_members[('K', ic)]

    def evictable2(self, board, ref):
        if ref == 'C5210':
            return True  # Revision 3 rule (high-impedance side checked when it is re-placed)
        return super().evictable2(board, ref)

    def domain(self, field, ic, limit, sset, target):
        ms = self.set_members(ic)
        fp = self.fps[('K', ic)]
        out = []
        for d, dx, dy in [o for o in rp.offsets(rp.NEAR_STEP, 0.0, max(rp.NEAR_MM, limit)) if o[0] <= limit + 1e-9]:
            for face, k, rects in self.orients('K', ic, ms, fp['side']):
                fixed, fps = self.obstacles(field, 'K', face, rects, dx, dy)
                if fixed:
                    continue
                blocks, small, hard = self.classify_fps('K', fps)
                if hard or blocks - set(sset):
                    continue
                placed = tuple((face, tuple(round(v, 4) for v in p2.shift(c, dx, dy))) for _, c in rects)
                out.append({'ic': ic, 'members': ms, 'face': face, 'turn_deg': k, 'moved_mm': r2(d), 'shift_mm': [dx, dy],
                            'origin': [r2(fp['origin'][0] + dx), r2(fp['origin'][1] + dy)], 'rects': placed,
                            'small': tuple(sorted(small))})
        return out

    def joint(self, targets, limit_others=rp.LIMIT_MM):
        sset = list(targets) + [n for n in NEIGHBOURS]
        others = [t for t in TARGETS if t not in targets]
        lift = {('K', m) for ic in sset for m in self.set_members(ic)}
        field = self.build_field(lift)
        if others:  # an unplaced target stays at its position
            for t in others:
                fp = self.fps[('K', t)]
                for ref, c in self.shapes('K', self.set_members(t), fp['side'], t)[fp['side']]:
                    field.add('K', fp['side'], [round(v, 4) for v in c], [], ref)
        doms = {ic: self.domain(field, ic, rp.LIMIT_MM if ic in targets else limit_others, sset, ic in targets) for ic in sset}
        gap = field.gap
        stats = {'nodes': 0, 'rejected_for_passives': 0}
        passive_moves = {}

        def compatible(a, ca, b, cb):
            return not rects_conflict(ca['rects'], cb['rects'], gap)

        def accept(assign):
            f = self.build_field(lift | {('K', p) for c in assign.values() for p in c['small']})
            for t in others:
                fp = self.fps[('K', t)]
                for ref, c in self.shapes('K', self.set_members(t), fp['side'], t)[fp['side']]:
                    f.add('K', fp['side'], [round(v, 4) for v in c], [], ref)
            for c in assign.values():
                for face, r in c['rects']:
                    f.add('K', face, list(r), [], c['ic'])
            moves = []
            for p in sorted({p for c in assign.values() for p in c['small']}):
                self.mode = 'U5210' if p == 'C5210' else None
                m, cy = self.move_within(f, 'K', p)
                self.mode = None
                if m is None:
                    stats['rejected_for_passives'] += 1
                    return False
                f.add('K', m['face'], cy, [], p)
                moves.append(m)
            passive_moves['moves'] = moves
            return True

        variables = sset
        sol = solve(variables, doms, compatible, accept, stats)
        res = {'set': sset, 'targets': list(targets), 'limit_others_mm': limit_others,
               'domain_sizes': {ic: len(doms[ic]) for ic in sset}, 'nodes': stats['nodes'],
               'rejected_for_passives': stats['rejected_for_passives'], 'found': sol is not None}
        if sol:
            res['poses'] = {ic: {k: v for k, v in c.items() if k != 'rects'} for ic, c in sol.items()}
            res['passives_moved'] = passive_moves.get('moves', [])
        return res

    def run(self):
        self.prepare()
        runs = [self.joint(TARGETS)]
        placed = list(TARGETS) if runs[0]['found'] else []
        if not placed:
            alone = [self.joint((t,)) for t in TARGETS]
            runs += alone
            placed = [next(r['targets'][0] for r in alone if r['found'])] if any(r['found'] for r in alone) else []
        options = []
        for t in TARGETS:
            if t in placed:
                continue
            # cheapest option: both targets searched jointly again with the smallest neighbour limit (scanned in
            # OPTION_LIMITS) at which the complete search finds an assignment. The placed target's pose is searched
            # again too, so the option supersedes its recorded pose (reported as 'supersedes').
            tried = []
            for lim in OPTION_LIMITS:
                r = self.joint(TARGETS, limit_others=lim)
                tried.append({'limit_others_mm': lim, 'found': r['found'], 'nodes': r['nodes']})
                if r['found']:
                    break
            r['for'] = t
            if r['found']:
                r['farthest_neighbour_mm'] = max(c['moved_mm'] for ic, c in r['poses'].items() if ic not in TARGETS)
            r['limits_scanned'] = tried
            r['option'] = 'both targets placed, neighbour blocks allowed up to the smallest scanned limit that works'
            if r['found']:
                first = next(x for x in runs if x['found'] and x['targets'] == placed)
                r['supersedes'] = {ic: {'recorded': {k: first['poses'][ic][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')},
                                        'option': {k: r['poses'][ic][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')}}
                                   for ic in placed}
                r['neighbour_electrical'] = {}
                for ic, c in sorted(r['poses'].items()):
                    if ic in TARGETS or c['moved_mm'] <= rp.LIMIT_MM:
                        continue
                    self.members[('K', ic)] = self.set_members(ic)
                    r['neighbour_electrical'][ic] = self.facts('K', ic, c)
                    del self.members[('K', ic)]
                r['fourth_block_alternative'] = 'not evaluated'
            r['grid_caveat'] = GRID_CAVEAT
            r['first_found'] = ('the scanned limits 25, 26, 27 and 28 mm are proved infeasible on the grid; the 30 mm assignment is '
                                'the first one found, so the true minimum farthest neighbour move on this grid lies in (28, %s] mm'
                                % (r.get('farthest_neighbour_mm') if r['found'] else '?'))
            r['a2_far_pose'] = {k: self.a2[t]['chosen'][k] for k in ('face', 'turn_deg', 'origin', 'moved_mm')}
            r['a2_far_pose_electrical'] = self.a2[t].get('electrical')
            swap = next((x for x in runs if x['targets'] == [t]), None)
            if swap is not None:
                r['swap'] = {'note': 'place %s instead of %s' % (t, ', '.join(placed)), 'found': swap['found']}
            options.append(r)
        return runs, placed, options


def build():
    s = A5()
    runs, placed, options = s.run()
    return {'schema_version': 1, 'model': MODEL,
            'status': 'STUDY (MC04-S8 Part A5): link-era re-placement; no board changed; nothing applied',
            'generator': 'scripts/stack/studies/mc04_s8_replacement/replacement_a5.py',
            'rules': {'set': list(TARGETS) + list(NEIGHBOURS), 'limit_mm': rp.LIMIT_MM, 'grid_mm': rp.NEAR_STEP, 'turns_deg': list(a2.TURNS),
                      'search': 'complete depth-first search with forward checking over the candidate poses (solve); '
                                'a failure is a proof over this grid for this set', 'grid_caveat': GRID_CAVEAT,
                      'passives': 'A2 rule; C5210 under the Revision 3 rule; re-placed nearest-first after an assignment'},
            'placed': placed, 'runs': runs, 'options_for_unplaced': options}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result-a5.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s8_replacement/replacement_a5.py')
        print('result-a5.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print('placed', d['placed'])
    for r in d['runs'] + d['options_for_unplaced']:
        print(r['targets'], r['limit_others_mm'], r['found'], r['domain_sizes'], r['nodes'], r.get('farthest_neighbour_mm'),
              {k: (v['moved_mm'], v['face'], v['turn_deg']) for k, v in r.get('poses', {}).items()})


if __name__ == '__main__':
    main()
