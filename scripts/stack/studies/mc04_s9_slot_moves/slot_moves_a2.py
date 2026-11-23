#!/usr/bin/env python3
"""MC04-S9-A2: joint re-run for U5209, U5110, U5210 and U8409 under the DS-146 rule changes (study only, one run).

Brief: circuit/orchestration/campaigns/osc-stack-20261114/mc04-s9-a2-joint-rerun-brief-20261122.md. Same model, inputs,
fixed items and acceptance as S9-A (slot_moves.py, pinned at 254d1cbf). Only these rules change:

1. Input-buffer parts by kind (replaces the blanket guard). The buffer IC and any part on a *_FB, *_SUM or *_SENSE node
   may not move. A decoupler may move on its IC's face, no farther from its IC than in the current record. An R_ISO
   (touching only *_DRIVE and *_REMOTE) may move no farther from its op-amp than now, its REMOTE site within the class
   distance of that signal. Any other part of an input-buffer cell may not move.
2. A target's block members that a fixed link covers are re-placed (S8 rules) instead of failing the candidate; a
   decoupler of the target stays on the IC's face, no farther from the IC than at its paper position.
3. A re-placed trimmer (RV*, RVO*) keeps its face.
4. No candidate may cover the recorded courtyard (grown 0.35 mm, the obstacle model) of U1415, U5110, U5209, U5210 or
   U8409.

Runs: U5209 variant A (P-K-P-L13.01.01.02 moved, P-K-P-L13.01.02.01 fixed) and, only if A fails, variant B (both
movable); U5110 every accepted P-K-P-L12.02.01.02 candidate; U8409 every accepted P-K-P-L03.01 candidate (cap 200 per
grid, 4 h ceiling); U5210 every accepted P-K-P-L13.01.01.01 candidate on the 2.0, 0.5 and 0.25 mm grids. Every candidate
is evaluated alone against the record scene; then one joint scene takes the cheapest clean candidate of each IC in the
ruled order that stays clean with the moves already taken. Writes result-a2.json; --check verifies it."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import slot_moves as sm  # noqa: E402
from slot_moves import lg, p2, rp, sg, r2  # noqa: E402

OUT = HERE / 'result-a2.json'
BRIEF = 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s9-a2-joint-rerun-brief-20261122.md'
BASE_A = '254d1cbf'
FIVE = ('U1415', 'U5110', 'U5209', 'U5210', 'U8409')
CAP = 200
TIME_CEILING_S = 4 * 3600
PAIR_CAP = 4
TRIMMER_PLAN = 'design/stack/trimmers/relocation-plan.json'
STOP_SUFFIX = ('_FB', '_SUM', '_SENSE')


def is_trimmer(ref):
    return ref.startswith('RV')  # RV* and RVO*


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class S9A2(sm.S9):
    def setup9(self):
        super().setup9()
        self.trimmer_plan = {r['ref']: r for r in json.loads(sm.blob(TRIMMER_PLAN))['records'] if r.get('ref')}

    def evictable2(self, board, ref):
        # rule 1 in the S8 displacement: a part of an input-buffer cell is displaceable only if it is a decoupler (never
        # displaceable in S8) or an R_ISO (checked after the move); rule 3: a trimmer is not displaced across faces
        k = buffer_kind(self, (board, ref))
        if k and k[0] != 'r_iso':
            return False
        return sm.r7.R7.evictable2(self, board, ref)

    def move_within(self, field, board, ref, limit=rp.LIMIT_MM):
        f = self.fps[(board, ref)]
        if not is_trimmer(ref):
            return sm.r7.R7.move_within(self, field, board, ref, limit)
        c = f['courtyard'] or p2.fp_bbox(f)
        for d, dx, dy in rp.offsets(0.25, 0.0, limit):
            cy = [round(v, 4) for v in p2.shift(c, dx, dy)]
            if not field.blocked(board, f['side'], cy, []):
                return {'ref': ref, 'face': f['side'], 'origin': [r2(f['origin'][0] + dx), r2(f['origin'][1] + dy)], 'moved_mm': r2(d)}, cy
        return None, None

    def current_origin(self, key):
        row = self.rows.get(key)
        if row and row.get('new') is not None:
            return row['new']
        return self.fps[key]['origin']


def buffer_kind(s, key):
    """(kind, detail) for a part of an input-buffer cell (the S8 A3 definition), or None. Kinds: 'stop', 'decoupler',
    'r_iso'."""
    if not sm.buffer_part(s, key):
        return None
    b, ref = key
    if ref.startswith('U') and ref in s.buffer_ics:
        return ('stop', 'the buffer IC')
    nets = sorted({n for n in s.pins.get(ref, {}).values() if n not in rp.RAILS})
    bad = [n for n in nets if n.endswith(STOP_SUFFIX)]
    if bad:
        return ('stop', 'on %s' % ', '.join(bad))
    dec = s.pk.get(ref, {}).get('decouples_ref')
    if dec:
        return ('decoupler', dec)
    if nets and all(n.endswith(('_DRIVE', '_REMOTE')) for n in nets) and any(n.endswith('_DRIVE') for n in nets):
        return ('r_iso', [n for n in nets if n.endswith('_DRIVE')][0])
    return ('stop', 'an input-buffer cell part of no movable kind (%s)' % ', '.join(nets))


class Arm1A2(sm.Arm1):
    def __init__(self, s, t0):
        super().__init__(s, t0)
        self.five = {}
        for ic in FIVE:
            fp = s.fps[('K', ic)]
            self.five[ic] = (fp['side'], fp['courtyard'])

    # ------------------------------------------------------------------ rule 4
    def accept_for(self, lid, targets):
        base = super().accept_for(lid, targets)
        front = self.s.byid[lid]['front_board']

        def accept(geo):
            why = base(geo)
            if why:
                return why
            for ic, (face, cy) in self.five.items():
                g = sg.grow(cy, self.gap)
                for b, f, rect, what in sm.link_rects(geo, front, self.latch_field):
                    if b == 'K' and f == face and sg.inter(g, rect):
                        return 'covers the recorded courtyard of %s' % ic
            return None
        return accept

    # ------------------------------------------------------------------ re-placement with conditions
    def conditions(self, key, restore):
        """(faces, check(origin) -> reason or None, reference) for one re-placed part under rules 1 to 3."""
        s = self.s
        b, ref = key
        fp = s.fps[key]
        tht = any(p['type'] in ('thru_hole', 'np_thru_hole') for p in fp['pads'])
        faces = [fp['side']] + (['B' if fp['side'] == 'F' else 'F'] if b == 'K' and not tht and not is_trimmer(ref) else [])
        dec = s.pk.get(ref, {}).get('decouples_ref')
        if dec and (b, dec) in s.fps:
            ic_o = s.fps[(b, dec)]['origin'] if dec in restore else s.current_origin((b, dec))
            ref_d = dist(fp['origin'] if dec in restore else s.current_origin(key), ic_o)
            ic_face = s.fps[(b, dec)]['side']
            return [ic_face], (lambda o: None if dist(o, ic_o) <= ref_d + 1e-6 else 'farther from %s' % dec), \
                {'kind': 'decoupler', 'ic': dec, 'limit_mm': round(ref_d, 2),
                 'basis': 'paper position (target block)' if dec in restore else 'current record'}
        k = buffer_kind(s, key)
        if k and k[0] == 'r_iso':
            drive = k[1]
            amps = sorted(r for r in s.net_refs[drive] if r.startswith('U') and (b, r) in s.fps)
            amp_o = s.current_origin((b, amps[0]))
            ref_d = dist(s.current_origin(key), amp_o)
            remote = [n for n in s.pins[ref].values() if n.endswith('_REMOTE')]
            sites = [(x, x['signals'].index(n)) for x in s.sites for n in remote if n in x['signals']]
            here = s.current_origin(key)

            def site_xy(x):
                return (x.get('K_xy') or x['xy']) if b == 'K' else x['xy']
            # the REMOTE site keeps its class distance: the R_ISO stays within it, or no farther than now where it is
            # already beyond it (the site and its link do not move)
            site_lim = {x['id']: max(s.limits[x['classes'][i]], dist(here, site_xy(x))) for x, i in sites}

            def check(o):
                if dist(o, amp_o) > ref_d + 1e-6:
                    return 'farther from %s' % amps[0]
                for x, i in sites:
                    if dist(o, site_xy(x)) > site_lim[x['id']] + 1e-6:
                        return 'farther from its REMOTE site %s than its class distance allows' % x['id']
                return None
            return faces, check, {'kind': 'R_ISO', 'op_amp': amps[0], 'limit_mm': round(ref_d, 2),
                                  'remote_sites': {x['id']: {'class': x['classes'][i], 'class_mm': s.limits[x['classes'][i]],
                                                             'now_mm': r2(dist(here, site_xy(x)))} for x, i in sites}}
        return faces, (lambda o: None), None

    def replace_c(self, f, key, restore):
        s = self.s
        b, ref = key
        fp = s.fps[key]
        c = fp['courtyard'] or p2.fp_bbox(fp)
        tht = [p['bbox'] for p in fp['pads'] if p['type'] in ('thru_hole', 'np_thru_hole')]
        faces, check, cond = self.conditions(key, restore)
        before = s.current_origin(key)
        for d, dx, dy in self.ring:
            o = [round(fp['origin'][0] + dx, 4), round(fp['origin'][1] + dy, 4)]
            if check(o):
                continue
            for face in faces:
                cy = [round(v, 4) for v in p2.shift(c if face == fp['side'] else rp.mirror(c, fp['origin'][0]), dx, dy)]
                pads = [[round(v, 4) for v in p2.shift(p, dx, dy)] for p in tht]
                if not f.blocked(b, face, cy, pads):
                    f.add(b, face, cy, pads, ref)
                    return self.describe(key, face, [r2(o[0]), r2(o[1])], r2(d), before, cond, restore)
        return self.describe(key, None, None, None, before, cond, restore)

    def describe(self, key, face, origin, moved, before, cond, restore):
        s = self.s
        b, ref = key
        fp = s.fps[key]
        ic = (cond or {}).get('ic') or (cond or {}).get('op_amp') or s.owner.get(key) or self.nearest_ic(key, before)
        out = {'board': b, 'ref': ref, 'face': face, 'face_before': fp['side'], 'origin': origin, 'moved_mm': moved,
               'from_paper_position': fp['origin'], 'position_before': before}
        if cond:
            out['condition'] = cond
        if ic and (b, ic) in s.fps:
            ic_o = s.fps[(b, ic)]['origin'] if ic in restore else s.current_origin((b, ic))
            out['ic'] = ic
            out['distance_to_ic_before_mm'] = r2(dist(before, ic_o))
            out['distance_to_ic_paper_mm'] = r2(dist(fp['origin'], s.fps[(b, ic)]['origin']))
            if origin:
                out['distance_to_ic_after_mm'] = r2(dist(origin, ic_o))
        if is_trimmer(ref):
            plan = s.trimmer_plan.get(ref, {})
            out['trimmer'] = {'verdict': plan.get('verdict'), 'access': plan.get('access'), 'source': TRIMMER_PLAN}
        return out

    def nearest_ic(self, key, before):
        """The IC a passive serves: the nearest IC on its board that shares one of its signal nets."""
        s = self.s
        b, ref = key
        nets = {n for n in s.pins.get(ref, {}).values() if n not in rp.RAILS}
        ics = sorted({r for n in nets for r in s.net_refs[n] if r.startswith('U') and (b, r) in s.fps})
        if not ics:
            return None
        return min(ics, key=lambda r: (dist(before, s.current_origin((b, r))), r))

    # ------------------------------------------------------------------ evaluation under the A2 rules
    def evaluate(self, moves, restore):
        s = self.s
        s.set_links(moves)
        s.lift, s.lift_blocks = set(), set()
        rects = [x for lid, geo in moves.items() for x in sm.link_rects(geo, s.byid[lid]['front_board'], self.latch_field)]
        lifted, why = {}, []
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
        items = s.placed_items()
        for b, face, rect, ref, kind in items:
            g = sg.grow(rect, self.gap)
            if any(bb == b and ff == face and sg.inter(g, rr) for bb, ff, rr, lab in rects):
                lifted.setdefault((b, ref), set()).add('%s under a moved link' % kind)
        for ic in restore:
            face0, sh, frs = s.target_rects(ic)
            for b, face, rect, ref, kind in items:
                if b == 'K' and any(f == face and sg.inter(cy, sg.grow(rect, self.gap)) for f, cy in frs):
                    lifted.setdefault((b, ref), set()).add('%s on the recorded area of %s' % (kind, ic))
        s.lift = set(lifted)
        f = s.build_field()
        shapes, covered = {}, {}
        for ic in restore:
            face0, sh, frs = s.target_rects(ic)
            keep = []
            for (ref, cy), (face, _) in zip(sh, frs):
                g = sg.grow(cy, f.gap)
                hit = sorted({lab for rect, lab in (f.links.get(('K', face)).near(g) if f.links.get(('K', face)) else [])
                              if sg.inter(g, rect)})
                if hit and ref != ic:
                    covered[('K', ref)] = (ic, hit)
                    lifted.setdefault(('K', ref), set()).add('member of %s covered by %s (rule 2)' % (ic, ', '.join(hit)))
                else:
                    keep.append((ref, cy))
            shapes[ic] = (face0, keep)
            fixed, fps = s.obstacles(f, 'K', face0, keep, 0.0, 0.0)
            for ref in sorted(fps):
                lifted.setdefault(('K', ref), set()).add('footprint at paper position on the recorded area of %s' % ic)
        blocks = {}
        for key in sorted(k for k in lifted if k[1].startswith('U') and k not in s.block_of):
            dec, local, _ = s.block(*key)
            blocks[key] = [key[1]] + dec + local
            for m in blocks[key][1:]:
                lifted.setdefault((key[0], m), set()).add('member of the IC block %s' % key[1])
        for key in sorted(lifted):
            if key in s.block_of:
                why.append(('placed link-era block', '%s %s is a member of the placed link-era block %s, which would move'
                            % (key[0], key[1], s.block_of[key])))
            k = buffer_kind(s, key)
            if k and k[0] == 'stop':
                why.append(('input-buffer part (may not move)', '%s %s is %s, which would move' % (key[0], key[1], k[1])))
        restored, moves_out = {}, []
        if why:
            return self.done(False, restored, moves_out, why, lifted, 'not run: a part that may not move would move')
        s.lift = set(lifted)
        f = s.build_field()
        for ic in restore:
            face0, keep = shapes[ic]
            fixed, fps = s.obstacles(f, 'K', face0, keep, 0.0, 0.0)
            restored[ic] = {'legal_at_recorded_position': not fixed and not fps,
                            'members_re_placed_rule_2': sorted(r for (b, r), (t, _) in covered.items() if t == ic),
                            'blocked_by': sorted('%s: %s' % x for x in fixed) + sorted(fps)}
            if fixed or fps:
                why.append(('target not legal', '%s is not legal at its recorded position: %s' % (ic, '; '.join(restored[ic]['blocked_by']))))
            for ref, cy in keep:
                f.add('K', s.mf('K', ref, face0), [round(v, 4) for v in cy], [], ref)
        if why:
            return self.done(False, restored, moves_out, why, lifted, 'not run: a target is not legal at its recorded position')
        for key in sorted(blocks, key=lambda k: (-sm.rp_area(s.fps[k]), k)):
            m, f = self.replace_block(f, key, blocks[key], why)
            m['why'] = sorted(lifted[key])
            m['timing_nodes'] = self.timing(key, m)
            moves_out.append(m)
        in_blocks = {(k[0], r) for k, ms in blocks.items() for r in ms}
        order = sorted((k for k in lifted if k not in in_blocks), key=lambda k: (not k[1].startswith('U'), -sm.rp_area(s.fps[k]), k))
        for key in order:
            m = self.replace_c(f, key, restore)
            m['why'] = sorted(lifted[key])
            moves_out.append(m)
            if m['face'] is None:
                why.append(('no place', '%s %s finds no place within %g mm under its conditions' % (key[0], key[1], sm.LIMIT)))
        return self.done(not why, restored, moves_out, why, lifted, 'run')

    def replace_block(self, f, key, members, why):
        s = self.s
        b, ic = key
        s.members[key] = members
        try:
            legal, disp, trial = s.search(f, b, ic)
        finally:
            del s.members[key]
        best = legal[0] if legal else None
        out = {'board': b, 'ref': ic, 'block': members, 'from_paper_position': s.fps[key]['origin'], 'face_before': s.fps[key]['side']}
        if best and best['moved_mm'] <= sm.LIMIT:
            s.place(f, b, ic, members, s.fps[key]['side'], best)
            out.update({k: best[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')})
            return out, f
        if disp:
            for m in disp['displaced_moves']:
                k = buffer_kind(s, (b, m['ref']))
                if k and k[0] == 'r_iso':
                    faces, check, cond = self.conditions((b, m['ref']), ())
                    bad = check(m['origin'])
                    if bad:
                        why.append(('input-buffer part condition', '%s %s (R_ISO) displaced by the block %s: %s' % (b, m['ref'], ic, bad)))
            out.update({k: disp[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')}, passives_moved=disp['displaced_moves'])
            return out, trial
        why.append(('no place', 'the block of %s %s finds no pose within %g mm (nearest %s mm)' % (b, ic, sm.LIMIT, best and best['moved_mm'])))
        out.update({'face': None, 'origin': None, 'moved_mm': None, 'nearest_mm': best and best['moved_mm']})
        return out, f

    def timing(self, key, m):
        """Clock or RC timing nodes of a moved logic block (from the S8 electrical facts), or []."""
        s = self.s
        b, ic = key
        if m.get('face') is None or not s.pk.get(ic, {}).get('mpn', '').startswith('SN74HC'):
            return []
        s.members[key] = m['block']
        try:
            facts = s.facts(b, ic, {k: m[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')})
        finally:
            del s.members[key]
        return sorted({e['net'] for e in facts for k in e['kind'] if 'timing node' in k})

    # ------------------------------------------------------------------ all candidates of one link
    def all_candidates(self, lid, targets, restore, chosen, cap=CAP):
        log = {'link': lid, 'targets': list(targets), 'grids': []}
        clean = []
        for g in sm.GRIDS:
            if time.time() - self.t0 > TIME_CEILING_S:
                log['time_ceiling'] = True
                self.capped.append('%s: time ceiling before the %g mm grid' % (lid, g))
                break
            found, rejected = self.candidates(lid, targets, chosen, g)
            print(lid, g, len(found), round(time.time() - self.t0), file=sys.stderr, flush=True)
            row = {'grid_mm': g, 'accepted_candidates': len(found), 'rejections_by_reason': rejected, 'evaluated': []}
            log['grids'].append(row)
            for i, (cost, key, geo, disp, d, slot, dist_) in enumerate(found):
                if i >= cap:
                    row['cap_reached'] = True
                    self.capped.append('%s: %d accepted candidates on the %g mm grid, %d evaluated (cap)' % (lid, len(found), g, cap))
                    break
                if time.time() - self.t0 > TIME_CEILING_S:
                    row['time_ceiling'] = True
                    self.capped.append('%s: time ceiling on the %g mm grid after %d candidates' % (lid, g, i))
                    break
                ok, det = self.evaluate(dict(chosen, **{lid: geo}), restore)
                ev = {'cost': round(cost, 4), 'slot_centre': list(slot), 'direction': lg.DIR_NAMES[d],
                      'slot_distance_from_centre_mm': round(dist_, 4), 'clean': ok, 'categories': det['categories'],
                      'not_clean_because': det['not_clean_because'][:12], 'parts_lifted': len(det['lifted'])}
                row['evaluated'].append(ev)
                if ok:
                    clean.append({'grid_mm': g, 'cost': round(cost, 4), 'slot_centre': list(slot), 'direction': lg.DIR_NAMES[d],
                                  'slot_distance_from_centre_mm': round(dist_, 4), 'geometry': geo,
                                  'figures': self.figures(lid, geo), **det})
        uniq = {}
        for c in clean:  # the same geometry can come from two grids
            uniq.setdefault(json.dumps(c['geometry'], sort_keys=True), c)
        clean = sorted(uniq.values(), key=lambda c: (c['cost'], c['slot_centre'], c['direction']))
        log['clean_candidates'] = len(clean)
        return clean, log


def summary(rows):
    cats = {}
    n = 0
    for lg_ in rows:
        for g in lg_.get('grids', []):
            for e in g.get('evaluated', []):
                n += 1
                for c in e['categories']:
                    cats[c] = cats.get(c, 0) + 1
    return n, dict(sorted(cats.items()))


def run_a2(s, a1):
    out = {}
    record = {}
    # U5209 variant A
    va_clean, va_log = a1.all_candidates('P-K-P-L13.01.01.02', ('U5209',), ['U5209'], {})
    u5209 = {'variant_A': {'links_moved': ['P-K-P-L13.01.01.02'], 'fixed': ['P-K-P-L13.01.02.01'], 'search': va_log,
                           'clean': [strip(c) for c in va_clean]}}
    record['U5209'] = [({'P-K-P-L13.01.01.02': c['geometry']}, c) for c in va_clean]
    if not va_clean:
        # variant B: both links movable; clean first-link candidates (without restoring), each tried with the second
        first, second = 'P-K-P-L13.01.01.02', 'P-K-P-L13.01.02.01'
        f_clean, f_log = a1.all_candidates(first, ('U5209',), [], {}, cap=CAP)
        logs, pairs = [f_log], []
        for c in f_clean[:PAIR_CAP]:
            c2, l2 = a1.all_candidates(second, ('U5209',), ['U5209'], {first: c['geometry']})
            l2['with_first_at'] = {k: c[k] for k in ('grid_mm', 'cost', 'slot_centre', 'direction')}
            logs.append(l2)
            for x in c2:
                pairs.append(({first: c['geometry'], second: x['geometry']}, {'first': strip(c), 'second': strip(x),
                                                                               'cost': round(c['cost'] + x['cost'], 4)}))
        u5209['variant_B'] = {'links_moved': [first, second], 'first_link_clean_without_target': len(f_clean),
                              'pair_cap': PAIR_CAP, 'search': logs, 'clean_pairs': [p for _, p in pairs]}
        record['U5209'] = [(m, {'cost': p['cost'], 'pair': p}) for m, p in pairs]
    out['U5209'] = u5209
    for ic, lid in (('U5110', 'P-K-P-L12.02.01.02'), ('U8409', 'P-K-P-L03.01'), ('U5210', 'P-K-P-L13.01.01.01')):
        clean, log = a1.all_candidates(lid, (ic,), [ic], {})
        out[ic] = {'links_moved': [lid], 'search': log, 'clean': [strip(c) for c in clean]}
        record[ic] = [({lid: c['geometry']}, c) for c in clean]
    # joint scene: in the ruled order, the cheapest clean candidate of each IC that stays clean with those already taken
    chosen, restored, joint_log = {}, [], []
    for ic in ('U5209', 'U5110', 'U8409', 'U5210'):
        took = None
        tried = 0
        for moves, c in sorted(record[ic], key=lambda mc: mc[1]['cost']):
            if any(l in chosen for l in moves):
                continue
            tried += 1
            ok, det = a1.evaluate(dict(chosen, **moves), restored + [ic])
            if ok:
                took = (moves, c, det)
                break
            joint_log.append({'ic': ic, 'cost': c['cost'], 'not_clean_with_earlier_moves': det['not_clean_because'][:6]})
        if took:
            chosen.update(took[0])
            restored.append(ic)
        joint_log.append({'ic': ic, 'single_clean_candidates': len(record[ic]), 'tried_jointly': tried,
                          'taken': None if not took else {l: {'slot_centre': g['slot']} for l, g in took[0].items()}})
    joint = None
    if chosen:
        ok, det = a1.evaluate(chosen, restored)
        joint = {'links': sorted(chosen), 'restored': restored, 'clean': ok,
                 'slots': {l: {'K_connector': g['K_connector'], 'slot': g['slot']} for l, g in chosen.items()}, **det}
    excl = exclusions(a1, record)
    return out, joint, joint_log, excl


def exclusions(a1, record):
    """Whether the cheapest clean single result of U5210 and of U8409 can stand together, and which excludes which."""
    if not record['U5210'] or not record['U8409']:
        return {'note': 'not both have a single clean result',
                'U5210_single_clean': len(record['U5210']), 'U8409_single_clean': len(record['U8409'])}
    m10, c10 = record['U5210'][0]
    m09, c09 = record['U8409'][0]
    ok, det = a1.evaluate(dict(m10, **m09), ['U8409', 'U5210'])
    return {'cheapest_together_clean': ok, 'not_clean_because': det['not_clean_because'][:8]}


def strip(c):
    return {k: v for k, v in c.items() if k != 'lifted'}


def build():
    t0 = time.time()
    pins, base = sm.input_pins()
    pins[TRIMMER_PLAN] = hashlib.sha256(sm.blob(TRIMMER_PLAN)).hexdigest()
    prior = {p: hashlib.sha256(sm.git_show(BASE_A, p)).hexdigest() for p in
             ('scripts/stack/studies/mc04_s9_slot_moves/slot_moves.py', 'scripts/stack/studies/mc04_s9_slot_moves/result.json')}
    same_prior = all(prior[p] == hashlib.sha256(sm.blob(p)).hexdigest() for p in prior)
    s = S9A2()
    s.setup9()
    a1 = Arm1A2(s, t0)
    runs, joint, joint_log, excl = run_a2(s, a1)
    table = []
    jt = set(joint['restored']) if joint and joint['clean'] else set()
    for ic in ('U5209', 'U5110', 'U8409', 'U5210'):
        r = runs[ic]
        if ic == 'U5209':
            n = len(r['variant_A']['clean']) + len(r.get('variant_B', {}).get('clean_pairs', []))
            how = 'variant A' if r['variant_A']['clean'] else 'variant B' if n else None
        else:
            n = len(r['clean'])
            how = r['links_moved'][0] if n else None
        logs = ([r['variant_A']['search']] + r.get('variant_B', {}).get('search', [])) if ic == 'U5209' else [r['search']]
        ev, cats = summary(logs)
        table.append({'ic': ic, 'single_clean_candidates': n, 'via': how, 'evaluated': ev, 'not_clean_categories': cats,
                      'in_joint_scene': ic in jt,
                      'outcome': 'R1 clean (joint)' if ic in jt else 'R1 clean alone, excluded in the joint scene' if n else 'R1 not clean'})
    return {'schema_version': 1, 'status': 'STUDY (MC04-S9-A2, DS-146): one run; no canonical change; decision table only',
            'generator': 'scripts/stack/studies/mc04_s9_slot_moves/slot_moves_a2.py', 'brief': BRIEF, 'model': rp.MODEL,
            'inputs': pins, 'base': base,
            'prior_study': {'commit': BASE_A, 'sha256_at_commit': prior, 'unchanged': same_prior,
                            'reproduction': 'slot_moves.py --check rebuilds result.json under the S9-A rules'},
            'rules': {'1': 'input-buffer parts by kind: buffer IC and *_FB, *_SUM, *_SENSE parts stop; decouplers (IC face, no farther '
                           'than the current record) and R_ISO (no farther from the op-amp, REMOTE site within its class distance) may move',
                      '2': "a target's block members covered by a fixed link are re-placed; its decouplers on the IC face, no farther than at paper",
                      '3': 'a re-placed trimmer keeps its face',
                      '4': 'no candidate covers the recorded courtyard (grown 0.35 mm) of U1415, U5110, U5209, U5210 or U8409'},
            'parameters': {'grids_mm': list(sm.GRIDS), 'cap_per_link_and_grid': CAP, 'pair_cap_U5209_variant_B': PAIR_CAP,
                           'time_ceiling_s': TIME_CEILING_S, 'search_radius_mm': s.ctx.radius, 're_placement_limit_mm': sm.LIMIT,
                           'courtyard_growth_mm': a1.gap},
            'runs': runs, 'joint_scene': joint, 'joint_log': joint_log, 'U5210_U8409': excl,
            'caps_reached': a1.capped, 'decision_table': table,
            'not_established': ['c6 (the contract pins the geometry digest)', 'coupling (check 4)', 'current (check 3)',
                                'latch access (check 2)', 'threading', 'routing', 'DRC', 'any electrical acceptance'],
            'oracle_checks': {'c6': 'NOT RUN: a study changes no canonical geometry; c6 runs in the generator task',
                              'link_electrical (checks 3, 4)': 'NOT RUN: rebound once in the generator task (DS-145 item 6)',
                              'latch access, threading procedure': 'NOT RUN: regenerate in the generator task',
                              'routing, DRC': 'NOT RUN: no board change'}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('result-a2.json is stale; regenerate with: python3 scripts/stack/studies/mc04_s9_slot_moves/slot_moves_a2.py')
        print('result-a2.json current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    for r in d['decision_table']:
        print(r['ic'], r['outcome'], r['single_clean_candidates'], r['evaluated'], r['not_clean_categories'])
    print('joint', d['joint_scene'] and (d['joint_scene']['links'], d['joint_scene']['clean']))
    print('caps', d['caps_reached'])


if __name__ == '__main__':
    main()
