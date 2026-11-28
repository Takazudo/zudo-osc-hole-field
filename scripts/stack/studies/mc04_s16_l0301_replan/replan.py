"""MC04-S16: can the 15 signals of P-K-P-L03.01 be re-planned so that U8409 stands at its paper pose.

Study only. Rows-level evidence on unvalidated drafts; nothing is adopted. Brief:
circuit/orchestration/campaigns/osc-stack-20261114/mc04-s16-l0301-replan-brief-20261128.md (Revision 4).
"""
from __future__ import annotations

import copy
import hashlib
import heapq
import itertools
import json
import math
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
S12DIR = HERE.parent / 'mc04_s12_five_ic_joint'
if str(S12DIR) not in sys.path:
    sys.path.insert(0, str(S12DIR))
import s12  # noqa: E402
import joint_search as js  # noqa: E402
from s12 import lg, p2, sg, sm  # noqa: E402
import links  # noqa: E402
import links_gate_c6 as c6  # noqa: E402

ROOT = s12.ROOT
L03 = 'P-K-P-L03.01'
SITES = ('K-P-16', 'K-P-18', 'K-P-20', 'P-K-E1', 'P-K-E2', 'P-K-E3')
STOCK = (8, 14, 26)
CLASS_S_PARTS = ('C7205', 'C8405', 'R8420', 'R8444', 'U8409', 'U8411')
RADIUS = s12.RADIUS
TESTS_C = ('S1', 'S2', 'S3', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6')
TESTS_A = ('A0', 'A1', 'A2', 'A3', 'A4', 'A6')
STATUS = 'ROWS-LEVEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT'


def r4(v):
    return round(v + 0.0, 4)


def now():
    return time.time()


# ================================================================ Ruling P7: the order builder

def ground(pos=None):
    return {'pos': pos, 'kind': 'ground'}


def capped_order(signals, size, rule='a8', adapter_order=None):
    """Positions 1..size for `signals` [(net, class, site)], or None. The sequence `links_gate.allocation` gives on 60
    positions without its unused positions; each run of n > 3 LOGIC lines split into ceil(n/3) runs as equal as
    possible, the longer first, one ground between runs (DS-120, DS-122); padded with unused positions."""
    try:
        pos = lg.allocation(list(signals), 60, rule, adapter_order)
    except ValueError:
        return None
    seq = [p for p in pos if p['kind'] != 'unused']
    out, i = [], 0
    while i < len(seq):
        p = seq[i]
        if p['kind'] == 'signal' and p['class'] == 'LOGIC':
            j = i
            while j < len(seq) and seq[j]['kind'] == 'signal' and seq[j]['class'] == 'LOGIC':
                j += 1
            run = seq[i:j]
            n = len(run)
            if n > 3:
                k = -(-n // 3)
                sizes = [n // k + 1] * (n % k) + [n // k] * (k - n % k)
                at = 0
                for t, z in enumerate(sizes):
                    if t:
                        out.append(ground())
                    out += run[at:at + z]
                    at += z
            else:
                out += run
            i = j
        else:
            out.append(p)
            i += 1
    if len(out) > size:
        return None
    res = []
    for n_, p in enumerate(out, 1):
        q = {k: v for k, v in p.items() if k in ('kind', 'net', 'class', 'site')}
        q['pos'] = n_
        res.append(q)
    for n_ in range(len(out) + 1, size + 1):
        res.append({'pos': n_, 'kind': 'unused'})
    return res


def proj(positions):
    return [(p['pos'], p['kind'], p.get('net'), p.get('class'), p.get('site')) for p in positions]


def order_ok(lid, positions):
    """links_gate_c6.order_errors on a built order, with no `original`."""
    return not c6.order_errors({'id': lid, 'positions': positions})


def built_size(signals, rule='a8'):
    """The smallest stock size with a built order that order_errors accepts, and that order."""
    for n in STOCK:
        o = capped_order(signals, n, rule)
        if o is not None:
            return n, o
    return None, None


def host_signals(h, site_by):
    """The signals on the host's recorded positions: member signals first (member sites in order, each site's signals
    in site order), then its recorded riders in record order. A line that rode out is not in the list."""
    on = [(p['net'], p['class'], p['site']) for p in h['positions'] if p['kind'] == 'signal']
    onset = set(on)
    mem = [(n, c, m) for m in h['members'] for n, c in zip(site_by[m]['signals'], site_by[m]['classes'])
           if (n, c, m) in onset]
    seen = set(mem)
    rid = []
    for y in h.get('riders_in', []):
        t = (y['net'], y['class'], y['site'])
        if t in onset and t not in seen:
            rid.append(t)
            seen.add(t)
    if seen != onset:
        raise ValueError('STOP 4: host_signals of %s misses %s' % (h['id'], sorted(onset - seen)))
    return mem + rid


def eligible_hosts(hosts, site_by):
    """Hosts whose recorded order the builder reproduces (Ruling P7), and the others with their reason."""
    ok, no = set(), {}
    for h in hosts:
        o = capped_order(host_signals(h, site_by), h['circuits'])
        if o is not None and proj(o) == proj(h['positions']):
            ok.add(h['id'])
        else:
            no[h['id']] = 'no built order' if o is None else 'the built order differs from the recorded order'
    return ok, no


# ================================================================ way 1 under the cap

def ride_capped(ctx, link, signals, hosts, state, site_by, limits, eligible, why=None):
    """links_gate_part2.ride with the host test of Ruling P7: the host is eligible and a built order exists at its own
    size with no order_errors. Host state from host_signals. Reason texts unchanged."""
    tmp = {}
    plan = []
    for sig in signals:
        if sig[1] not in limits:
            if why is not None:
                why.append('%s (%s, site %s) is a %s line, which rides on no other link (DS-79)'
                           % (sig[0], sig[1], sig[2], sig[1].lower()))
            return None
        site = site_by[sig[2]]
        opts = sorted((p2.rider_distance(site, h), h['id'], h) for h in hosts
                      if h['id'] != link['id'] and h['joint'] == link['joint'] and h['front_board'] == link['front_board'])
        host, full = None, []
        for d, hid, h in opts:
            if d > limits[sig[1]] + 1e-9:
                break
            cur = tmp.get(hid, state[hid])
            fits = False
            if hid in eligible:
                o = capped_order(cur + [sig], h['circuits'], ctx.rule, ctx.adapter_order)
                fits = o is not None and order_ok(hid, o)
            if fits:
                host = (hid, d, cur)
                break
            full.append((d, hid))
        if host is None:
            if why is not None:
                lim = limits[sig[1]]
                why.append('%s (%s, site %s) has %s' % (sig[0], sig[1], sig[2], 'no host within %g mm' % lim if not full else
                                                       'only full hosts within %g mm: %s' % (lim, ', '.join(
                                                           '%s at %s mm' % (hid, d) for d, hid in full))))
            return None
        tmp[host[0]] = host[2] + [sig]
        plan.append((sig, host[0], host[1]))
    return plan, tmp


def rehost(ctx, host, sigs, origin):
    """links_gate_part2.reallocate with positions from capped_order; riders marked as before."""
    pos = capped_order(sigs, host['circuits'], ctx.rule, ctx.adapter_order)
    if pos is None:
        raise ValueError('STOP 4: no built order for host %s' % host['id'])
    for p in pos:
        if p['kind'] == 'signal' and (p['site'], p['net']) in origin:
            p['rider_from'] = origin[(p['site'], p['net'])]
    host.update({'positions': pos, 'signals': len(sigs), 'grounds': sum(1 for p in pos if p['kind'] == 'ground'),
                 'unused': sum(1 for p in pos if p['kind'] == 'unused'),
                 'circuits_needed': lg.circuits_needed([s[1] for s in sigs], ctx.rule)})


def site_signals(site_by, order):
    return [(n, c, m) for m in order for n, c in zip(site_by[m]['signals'], site_by[m]['classes'])]


class Rides:
    """The ride test of S3 over every order of a ride set's sites (Ruling P1)."""

    def __init__(self, w, fn='capped', hosts=None):
        self.w = w
        self.ctx = w.ctx
        self.site_by = w.site_by
        self.limits = w.s.limits
        self.l03 = w.byid[L03]
        self.hosts = hosts if hosts is not None else [r for r in p2.live(w.base_out) if r['placed'] and r['id'] != L03]
        pk = [h for h in self.hosts if h['joint'] == 'P-K' and h['front_board'] == 'P']
        self.eligible, self.not_eligible = eligible_hosts(pk, self.site_by)
        self.fn = fn
        self.state0 = {h['id']: (host_signals(h, self.site_by) if fn == 'capped' else p2.link_signals(h)) for h in self.hosts}

    def one(self, order, why=None):
        sigs = site_signals(self.site_by, order)
        state = dict(self.state0)
        if self.fn == 'capped':
            return ride_capped(self.ctx, self.l03, sigs, self.hosts, state, self.site_by, self.limits, self.eligible, why)
        return p2.ride(self.ctx, self.l03, sigs, self.hosts, state, self.site_by, self.limits, why)

    def test(self, rset):
        """Every order of the sites of `rset`, in lexicographic order of site id: (rides, first legal order, plan,
        number of distinct host plans, legal orders, orders tried, first reason)."""
        rset = sorted(rset)
        if not rset:
            return {'rides': True, 'first_order': [], 'plan': [], 'host_plans': 1, 'legal_orders': 1, 'orders': 1,
                    'member_order_rides': True, 'reason': None}
        first, plans, legal, n, reason, member = None, set(), 0, 0, None, None
        for order in itertools.permutations(rset):
            n += 1
            w_ = []
            res = self.one(list(order), w_)
            if n == 1:
                member = res is not None
            if res is None:
                reason = reason or w_[0]
                continue
            legal += 1
            plan = res[0]
            plans.add(tuple(sorted((s[0], s[2], h) for s, h, d in plan)))
            if first is None:
                first = (list(order), [[s[0], s[1], s[2], h, d] for s, h, d in plan])
        return {'rides': first is not None, 'first_order': first[0] if first else None, 'plan': first[1] if first else None,
                'host_plans': len(plans), 'legal_orders': legal, 'orders': n, 'member_order_rides': member,
                'reason': None if first else reason}


# ================================================================ blocks and structures

def partitions(items):
    items = list(items)
    if not items:
        yield []
        return
    first, rest = items[0], items[1:]
    for p in partitions(rest):
        for i in range(len(p)):
            yield p[:i] + [[first] + p[i]] + p[i + 1:]
        yield [[first]] + p


def structures():
    """Every (ride set, partition of the rest) of the six sites: 877, the present plan first."""
    out = []
    for k in range(len(SITES) + 1):
        for rset in itertools.combinations(SITES, k):
            rest = [s for s in SITES if s not in rset]
            for part in partitions(rest):
                blocks = sorted(tuple(sorted(b)) for b in part)
                out.append({'rides': list(rset), 'blocks': [list(b) for b in blocks]})
    out.sort(key=lambda x: (len(x['rides']), len(x['blocks']), x['rides'], x['blocks']))
    return out


def struct_id(st):
    return 'R[%s]|%s' % (','.join(st['rides']), '|'.join('+'.join(b) for b in st['blocks']))


def is_present(st):
    return not st['rides'] and st['blocks'] == [list(SITES)]


def block_id(sites):
    return 'S16-B[%s]' % '+'.join(sorted(sites))


def block_record(w, sites, size=None):
    """A link record for a site subset (block_record, Ruling P7): members in id order, positions from capped_order at
    the smallest stock size that holds them (or at `size`), the options file's cable for that size, the gate's centroid."""
    ctx = w.ctx
    members = sorted(sites)
    sig = site_signals(w.site_by, members)
    classes = [c for _, c, _ in sig]
    need = lg.circuits_needed(classes, ctx.rule)
    if size is None:
        size, pos = built_size(sig, ctx.rule)
    else:
        pos = capped_order(sig, size, ctx.rule)
    n = size or STOCK[-1]
    z = lg.fh12_size(n, ctx.gopts)
    cx, cy = links._centroid([w.site_by[m] for m in members])
    rec = {'id': block_id(members), 'joint': 'P-K', 'front_board': 'P', 'members': members, 'signals': len(sig),
           'grounds': sum(1 for p in pos or [] if p['kind'] == 'ground'),
           'unused': sum(1 for p in pos or [] if p['kind'] == 'unused'), 'circuits_needed': need,
           'size': z['id'], 'circuits': n, 'connector': z['connector'], 'cable': z['cable'],
           'cable_length_mm': z['cable_length_mm'], 'positions': pos or [], 'centre': [r4(cx), r4(cy)],
           'riders_in': [], 'placed': True, 'block': True, 'built': pos is not None, 'sig_classes': classes}
    return rec


def record_block(w, lid):
    """Ruling P9: the recorded link as a block, with its members, centre, size and cable, and the signals on its
    recorded positions (host_signals) built by capped_order at its own size. Controls and mutations only."""
    ctx = w.ctx
    h = w.byid[lid]
    sig = host_signals(h, w.site_by)
    n = h['circuits']
    pos = capped_order(sig, n, ctx.rule)
    z = lg.fh12_size(n, ctx.gopts)
    return {'id': 'S16-RB[%s]' % lid, 'record': lid, 'joint': h['joint'], 'front_board': h['front_board'],
            'members': list(h['members']), 'signals': len(sig),
            'grounds': sum(1 for p in pos or [] if p['kind'] == 'ground'),
            'unused': sum(1 for p in pos or [] if p['kind'] == 'unused'),
            'circuits_needed': lg.circuits_needed([c for _, c, _ in sig], ctx.rule), 'size': z['id'], 'circuits': n,
            'connector': z['connector'], 'cable': z['cable'], 'cable_length_mm': z['cable_length_mm'],
            'positions': pos or [], 'centre': list(h['centre']), 'riders_in': [], 'placed': True, 'block': True,
            'built': pos is not None, 'sig_classes': [c for _, c, _ in sig]}


def s1_class(classes):
    """S1: circuits_needed gives a number; no STATIC line beside another class."""
    if lg.circuits_needed(classes) is None:
        return 'circuits_needed gives none (LOGIC with WIPER)'
    if 'STATIC' in classes and set(classes) != {'STATIC'}:
        return 'a STATIC line beside another class'
    return None


def s2_order(rec):
    if not rec['built'] or not rec['positions']:
        return 'no built order at %d circuits' % rec['circuits']
    errs = c6.order_errors({'id': rec['id'], 'positions': rec['positions']})
    if errs:
        return '; '.join(errs)
    return None


# ================================================================ the census of a block (rules R1 to R6)

class Anchors:
    """Which protected parts are anchored, class S or class N (Ruling P3), and the strict S12 setting."""

    def __init__(self, w, mode='s16'):
        self.mode = mode
        self.protected = w.protected
        if mode == 's12':
            self.anchor = w.anchor
            self.cls_s = {k for k, v in w.searched_disp.items() if v}
            return
        anchor = defaultdict(set)
        by03 = set()
        for r in p2.live(w.base_out):
            if not r['placed']:
                continue
            for k, v in r['displaced'].items():
                b = r['front_board'] if k == 'front B' else 'K'
                for ref in v:
                    if r['id'] == L03:
                        by03.add((b, ref))
                    else:
                        anchor[(b, ref)].add(r['id'])
        for f in w.inp['fixing_list']['fixings']:
            if f.get('active'):
                for m in f.get('part_moves', []):
                    anchor[(m['board'], m['ref'])].add('fixing ' + f['id'])
        self.anchor = anchor
        self.cls_s = {k for k in by03 if not anchor.get(k)}

    def classify(self, key):
        if key not in self.protected:
            return None
        if self.anchor.get(key):
            return 'A'
        return 'S' if key in self.cls_s else 'N'


def with_byid(w, rec, fn):
    old = w.s.byid.get(rec['id'])
    w.s.byid[rec['id']] = rec
    try:
        return fn()
    finally:
        if old is None:
            w.s.byid.pop(rec['id'], None)
        else:
            w.s.byid[rec['id']] = old


class Rules:
    """R2 to R6 for one block record."""

    def __init__(self, w, rec, anchors, class_s='default', exempt_record=False):
        self.w, self.rec, self.an, self.class_s = w, rec, anchors, class_s
        self.front = rec['front_board']
        self.acc2 = with_byid(w, rec, lambda: w.arm1.accept_for(rec['id'], ()))
        self.acc4 = with_byid(w, rec, lambda: w.arm1a2.accept_for(rec['id'], ()))
        self.exempt_record = exempt_record

    def r2(self, geo):
        if self.exempt_record:
            return self.r2_record(geo)
        return self.acc2(geo)

    def r2_record(self, geo):
        """Ruling P8: R2 at a record slot without its class-distance clause; the cable and compliance clauses of
        slot_moves.Arm1.accept_for, unchanged."""
        ctx = self.w.ctx
        z = lg.rec_size(ctx, self.rec)
        if z['cable_length_mm'] - ctx.need(self.front, geo['a_mm'], geo['b_mm']) < -1e-9:
            return 'cable longer than its stock length'
        c = lg.cvalue(ctx.cmap, geo['K_connector'])
        if c is None or c > ctx.cmap.limit + 1e-12:
            return 'K-field compliance above the DS-87 limit'
        return None

    def r4(self, geo):
        why = self.acc4(geo)
        return why if why and why.startswith('covers the recorded courtyard') else None

    def t1(self, geo):
        w = self.w
        d = lg.displaced(w.model, self.front, geo, w.ctx.latch)
        bad, cls_s, anch = [], [], []
        for k, refs in d.items():
            b = self.front if k == 'front B' else 'K'
            for ref in refs:
                c = self.an.classify((b, ref))
                if c == 'A':
                    anch.append((b, ref))
                elif c == 'S':
                    cls_s.append(ref)
                elif c == 'N':
                    bad.append((ref, 'N'))
        if self.class_s == 'strict':
            bad += [(r, 'S') for r in cls_s]
        return sorted(set(bad)), sorted(set(cls_s)), sorted(set(anch))

    def t2(self, geo):
        w = self.w
        rects = sm.link_rects(geo, self.front, w.latch_field)
        hits = []
        for key in sorted(self.an.anchor):
            if key not in w.protected or not self.an.anchor[key]:
                continue
            row = w.base_rows.get(key)
            if not row or row['new'] is None:
                continue
            g = sg.grow(row['new_courtyard'], w.gap)
            for b, f, rect, what in rects:
                if b == key[0] and f == row['new_face'] and sg.inter(g, rect):
                    hits.append((key[0], key[1], what))
                    break
        return hits

    def check(self, geo, dist):
        """(first failing rule or None, reason, extra) of R2 to R6."""
        why = self.r2(geo)
        if why:
            return 'R2', why, None
        if dist > RADIUS + 1e-9:
            return 'R3', 'slot centre %.4f mm from the block centre, beyond %.1f mm' % (dist, RADIUS), None
        if self.exempt_record:
            return None, None, {'class_s': [], 'anchored': []}
        why = self.r4(geo)
        if why:
            return 'R4', why, None
        bad, cls_s, anch = self.t1(geo)
        if bad:
            return 'R5', 'T1: ' + ', '.join('%s (%s)' % x for x in bad), {'bad': bad, 'class_s': cls_s}
        hits = self.t2(geo)
        if hits:
            return 'R6', 'T2: ' + ', '.join('%s %s under %s' % h for h in hits), {'hits': hits}
        return None, None, {'class_s': cls_s, 'anchored': ['%s %s' % a for a in anch]}


def placed_except(w, skip=(L03,), extra=()):
    live = [r for r in p2.live(w.base_out) if r['id'] not in skip] + list(extra)
    return lg.placed_index(live)


def census_block(w, rec, grid, placed, anchors, class_s='default', deadline=None, first_of=None):
    """One block on one grid within 35 mm of its centre: R1 (`links_gate.candidate`), then R2 to R6 in order.
    Returns (counts, accepted). `first_of`: also record the first candidate rejected at each rule (mutations)."""
    ctx = w.ctx
    front, centre, own = rec['front_board'], rec['centre'], lg.rec_own(rec)
    z = lg.rec_size(ctx, rec)
    spare = ctx.spare(front, z)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    rules = Rules(w, rec, anchors, class_s)
    offsets = ctx.grid(grid, radius=RADIUS)
    rings = ('≤ 24 mm', '24–35 mm')
    counts = {'offsets': len(offsets), 'evaluated': 0, 'legal_R1': {r: 0 for r in rings},
              'after': {t: {r: 0 for r in rings} for t in ('R2', 'R3', 'R4', 'R5', 'R6')},
              'rejections_R1': {}, 'rejections': {t: {} for t in ('R2', 'R3', 'R4', 'R5', 'R6')},
              'class_s_deferred': 0, 'class_s_parts': {}, 'complete': True}
    acc, firsts = [], {}
    ctx.model.memo_for(None)
    for i, off in enumerate(offsets):
        if deadline is not None and now() > deadline:
            counts['complete'] = False
            break
        if i % 4000 == 0:
            ctx.model.memo_for(None)
        dist = math.hypot(*off)
        ring = s12.ring_of(dist)
        sx, sy = lg.r4(centre[0] + off[0]), lg.r4(centre[1] + off[1])
        for di, d in enumerate(lg.DIRS):
            counts['evaluated'] += 1
            why, c = lg.candidate(ctx, placed, front, z, own, sx, sy, d, dist, spare, True, gm)
            if why:
                k = why[0]
                counts['rejections_R1'][k] = counts['rejections_R1'].get(k, 0) + 1
                if first_of is not None and 'R1' not in firsts:
                    firsts['R1'] = {'slot_centre': [sx, sy], 'direction': lg.DIR_NAMES[d], 'dist': dist, 'why': k}
                continue
            counts['legal_R1'][ring] += 1
            cost, geo, disp = c
            rule, reason, extra = rules.check(geo, dist)
            if rule is not None:
                t = counts['rejections'][rule]
                key = reason if rule in ('R2', 'R3', 'R4') else rule
                t[key] = t.get(key, 0) + 1
                if first_of is not None and rule not in firsts:
                    firsts[rule] = {'slot_centre': [sx, sy], 'direction': lg.DIR_NAMES[d], 'dist': dist, 'why': reason,
                                    'extra': extra, 'cost': cost}
            for n_, t in enumerate(('R2', 'R3', 'R4', 'R5', 'R6'), 2):
                if rule is None or int(rule[1]) > n_:
                    counts['after'][t][ring] += 1
            if rule is None or int(rule[1]) > 5:
                if extra and extra.get('class_s'):
                    counts['class_s_deferred'] += 1
                    for ref in extra['class_s']:
                        counts['class_s_parts'][ref] = counts['class_s_parts'].get(ref, 0) + 1
            if rule is None:
                key = (round(cost, 6), round(dist, 6), di, geo['front_extension_mm'], geo['K_extension_mm'], sx, sy)
                acc.append({'cost': cost, 'key': list(key), 'geometry': geo, 'direction': lg.DIR_NAMES[d],
                            'slot_centre': [sx, sy], 'dist': dist, 'ring': ring, 'grid_mm': grid,
                            'spot': list(s12.spot_of(sx, sy, lg.DIR_NAMES[d])), 'class_s': extra['class_s'],
                            'anchored_covered': extra['anchored']})
    ctx.model.memo_for(None)
    acc.sort(key=lambda c: c['key'])
    if first_of is not None:
        counts['firsts'] = firsts
    return counts, acc


def distinct(acc_by_grid):
    """Distinct (slot, direction) pairs, the finest grid kept (grids in 2.0, 0.5, 0.25 order)."""
    d = {}
    for acc in acc_by_grid:
        for e in acc:
            d[(tuple(e['slot_centre']), e['direction'])] = e
    return sorted(d.values(), key=lambda e: e['key'])


# ================================================================ scenes with a changed link set

def scene_links_replan(w, blocks, ride_plan, moves=None):
    """The link list of a re-planned scene: L03.01 removed, the blocks added at their slots, riders re-hosted.
    `blocks`: [(record, {'geometry', 'slot_centre', 'direction'})]; `ride_plan`: [[net, class, site, host, d]]."""
    ctx = w.ctx
    base = w.scene_links(moves or {})
    out = [copy.deepcopy(r) if r['id'] != L03 else None for r in base]
    out = [r for r in out if r is not None]
    by = {r['id']: r for r in out}
    origin = {}
    for h in out:
        for p in h.get('positions', []):
            if p.get('rider_from'):
                origin[(p['site'], p['net'])] = p['rider_from']
    tmp = {}
    for net, cls, site, hid, d in ride_plan:
        h = by[hid]
        if hid not in tmp:
            tmp[hid] = host_signals(h, w.site_by)
        tmp[hid].append((net, cls, site))
        origin[(site, net)] = L03
        h.setdefault('riders_in', []).append({'net': net, 'class': cls, 'site': site, 'from': L03, 'distance_mm': d,
                                              'reason': 'S16 re-plan ride'})
    for hid, sigs in sorted(tmp.items()):
        rehost(ctx, by[hid], sigs, origin)
    for rec, m in blocks:
        b = copy.deepcopy(rec)
        geo = m['geometry']
        b.update({'geometry': geo, 'slot_centre': list(m['slot_centre']), 'direction': m['direction'],
                  'displaced': lg.displaced(w.model, b['front_board'], geo, ctx.latch)})
        out.append(b)
    return out


def check_rows16(w, rows):
    """A0 and S12's check_rows (A1 to A4, A6) unchanged."""
    fails, info = s12.check_rows(w, rows)
    rb = s12.rowmap(rows)
    if ('K', 'U8409') in rb:
        fails = dict(fails)
        fails['A0'] = ['U8409 has a row (%s)' % ('no position' if rb[('K', 'U8409')]['new'] is None else
                                                   rb[('K', 'U8409')]['step'])]
    return fails, info


def acceptance_vector(fails):
    return ''.join('F' if fails.get(a) else 'P' for a in TESTS_A)


def block_figures(w, rec, m):
    """A5 for a block: loop on the stock cable, K-field compliance, member class distances, radius."""
    ctx = w.ctx
    geo = m['geometry']
    need = ctx.need(rec['front_board'], geo['a_mm'], geo['b_mm'])
    comp = lg.cvalue(ctx.cmap, geo['K_connector'])
    z = lg.rec_size(ctx, rec)
    loop = round(z['cable_length_mm'] - need, 4)
    mem = [{'site': s, 'moved_mm': sm.site_distance(w.site_by[s], geo),
            'limit_mm': min(w.s.limits[c] for c in w.site_by[s]['classes'])} for s in rec['members']]
    c = rec['centre']
    dist = math.hypot(m['slot_centre'][0] - c[0], m['slot_centre'][1] - c[1])
    fails = []
    if loop < -1e-9:
        fails.append('%s loop %.4f mm < 0' % (rec['id'], loop))
    if comp is None or comp > ctx.cmap.limit + 1e-12:
        fails.append('%s K-field compliance above the limit' % rec['id'])
    for x in mem:
        if x['moved_mm'] > x['limit_mm'] + 1e-9:
            fails.append('%s %s beyond its class distance' % (rec['id'], x['site']))
    if dist > RADIUS + 1e-9:
        fails.append('%s slot beyond %.1f mm' % (rec['id'], RADIUS))
    return {'loop_mm': loop, 'cable_needed_mm': round(need, 4), 'compliance_mm_per_N': comp,
            'hold_K_by_hand': comp is None or comp > ctx.cmap.list_above, 'members': mem,
            'trim_leads': lg.trim_list(ctx.model, rec['front_board'], geo), 'slot_distance_from_centre_mm': round(dist, 4),
            'ring': s12.ring_of(dist), 'size': rec['size'], 'cable': rec['cable'],
            'cable_length_mm': rec['cable_length_mm']}, fails


def judge_replan(w, moves, rows, blocks=(), ride_plan=(), overlay_blocks=None, run_overlay_search=True):
    """s12.judge for a scene whose link set may differ from the base: the same rules; link figures of the blocks by
    block_figures; the overlay part on the re-planned link list."""
    s = w.s
    fails, info = s12.check_rows(w, rows)
    fails = defaultdict(list, fails)
    figs = {}
    for lid, m in sorted(moves.items()):
        f, bad = s12.link_figures(w, lid, m)
        figs[lid] = f
        fails['A5'] += bad
    for rec, m in blocks:
        f, bad = block_figures(w, rec, m)
        figs[rec['id']] = f
        fails['A5'] += bad
    ra, rb = w.base_rows, s12.rowmap(rows)
    scene_out = scene_links_replan(w, list(blocks), list(ride_plan), moves) if (blocks or ride_plan) else w.scene_links(moves)
    old_rows, old_out = s.rows, s.out
    s.rows, s.out = rb, scene_out
    crashed = None
    try:
        try:
            res = s12.overlay_part(w, ra, rb, info, fails, overlay_blocks, run_overlay_search)
        except TypeError as e:
            # s12.overlay_part places every earlier overlay block, also one with no pose (an A8 failure already); the
            # S8 search then cannot run. Stricter reading: the scene fails A8, the other items are evaluated without
            # the search.
            crashed = 'S8 block search stopped: an earlier overlay block has no pose (%s)' % e
            fails = defaultdict(list, {k: v for k, v in fails.items() if k not in ('A7', 'A8', 'A9', 'A10', 'A11')})
            res = s12.overlay_part(w, ra, rb, info, fails, overlay_blocks, False)
            fails['A8'].append(crashed)
    finally:
        s.rows, s.out = old_rows, old_out
    if crashed:
        res['overlay_search_stopped'] = crashed
    res.update({'fails': {k: v for k, v in sorted(fails.items()) if v}, 'rows': info, 'link_figures': figs})
    res['passes'] = {a: not fails.get(a) for a in ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11')}
    return res


def legal_block(w, rec, e, chosen, later_ids, anchors, class_s='default', rules=None, placed=None):
    """(entry or None, reason): a block at a pool entry's slot with every other live link at its record (L03.01 out) and
    the earlier chosen blocks of the structure placed; R1 to R6. `rules` and `placed` may be passed prebuilt (the
    same objects this function would build) so a search does not rebuild them per call."""
    ctx = w.ctx
    if placed is None:
        extra = [dict(r, geometry=m['geometry']) for r, m in chosen]
        placed = placed_except(w, extra=extra)
    front, own = rec['front_board'], lg.rec_own(rec)
    z = lg.rec_size(ctx, rec)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    d = [k for k, v in lg.DIR_NAMES.items() if v == e['direction']][0]
    ctx.model.memo_for(None)
    why, c = lg.candidate(ctx, placed, front, z, own, e['slot_centre'][0], e['slot_centre'][1], d, e['dist'],
                          ctx.spare(front, z), True, gm)
    if why:
        return None, 'R1: ' + why[0]
    cost, geo, disp = c
    rule, reason, extra2 = (rules or Rules(w, rec, anchors, class_s)).check(geo, e['dist'])
    if rule is not None:
        return None, '%s: %s' % (rule, reason if rule in ('R2', 'R3', 'R4') else reason.split(':')[0])
    return {'geometry': geo, 'slot_centre': e['slot_centre'], 'direction': e['direction'], 'cost': cost,
            'dist': e['dist'], 'ring': e['ring'], 'grid_mm': e.get('grid_mm'), 'class_s': extra2['class_s'],
            'spot': e.get('spot')}, None


def reverify_blocks(w, chosen):
    """Every block of a complete scene legal (R1) with every other block of the structure placed."""
    ctx = w.ctx
    bad = []
    for i, (rec, m) in enumerate(chosen):
        others = [dict(r, geometry=mm['geometry']) for j, (r, mm) in enumerate(chosen) if j != i]
        placed = placed_except(w, extra=others)
        why = ctx.evaluate(placed, rec['front_board'], m['geometry'], lg.rec_own(rec))
        if why:
            bad.append('%s: %s' % (rec['id'], why[0]))
    return bad


# ================================================================ run infrastructure

import subprocess  # noqa: E402

DEV = bool(os.environ.get('S16_DEV_OUT'))
OUTDIR = Path(os.environ['S16_DEV_OUT']) if DEV else HERE  # development dry runs write only to the scratchpad
CK = OUTDIR / 'checkpoints'
CAND = OUTDIR / 'candidates'
RESULT = OUTDIR / 'result.json'
PINS = OUTDIR / 'pins.json'
# Bulky intermediates stay out of git (owner rule: no Git LFS, no large intermediate dumps; ORCHESTRATION.md section 6)
BULK = OUTDIR / 'cache' if DEV else ROOT / '.circuit-cache' / 'mc04-s16'
BULK_MANIFEST = OUTDIR / 'bulk-manifest.json'
SCRATCH = '_scratch'  # short-lived copies inside the cache (C14, tests); removed after use and never in the manifest
DURABLE = '/mnt/project-files/osc-s16-cache/'  # project file storage (network mount) holding a verified copy
PY = sys.executable
CAMPAIGN = 'circuit/orchestration/campaigns/osc-stack-20261114/'
BRIEF = CAMPAIGN + 'mc04-s16-l0301-replan-brief-20261128.md'
BRIEF_SHA = 'a638d4b8d6d20def85c63ed51e236153d889da790dee7e7cc0bebe657d36e7b4'
PIN_FILES = (
    'scripts/stack/studies/mc04_s16_l0301_replan/replan.py',
    'scripts/stack/studies/mc04_s16_l0301_replan/c13_heartbeat.py',
    'scripts/stack/studies/mc04_s16_l0301_replan/test_s16.py',
    'scripts/stack/studies/mc04_s12_five_ic_joint/s12.py',
    'scripts/stack/studies/mc04_s12_five_ic_joint/joint_search.py',
    'scripts/stack/studies/mc04_s15_no_growth_moves/guard15.py',
    BRIEF,
    # the generator files and S8 to S10 modules are pinned through C1: S12's --check verifies its own input pins
)
CLOCK_S = 4.5 * 3600
STEP_CEIL = {'arm0': 30 * 60, 'stage1': 60 * 60, 'stage2a': 10 * 60, 'stage2b': 90 * 60, 'stage3': 30 * 60,
             'stage4': 20 * 60}
POOL_SPOTS = 20
LEGAL_CAP = 20000
REPLAY_CAP_STRUCT = 12
REPLAY_CAP = 1200
KEEP = 5
OVERLAY_CAP = 10
STAGE4_CAP = 115
WORKERS = 3
RESUME_CAP = 3


class Stop(Exception):
    pass


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, file=sys.stderr, flush=True)


def _jdefault(o):
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if isinstance(o, tuple):
        return list(o)
    raise TypeError(type(o))


def write_json(path, obj, indent=1):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + '.tmp')
    tmp.write_text(json.dumps(obj, indent=indent, ensure_ascii=False, default=_jdefault) + '\n')
    os.replace(tmp, path)


def read_json(path):
    return json.loads(Path(path).read_text())


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def ck(name):
    return CK / name


def env_nobytecode():
    e = dict(os.environ)
    e['PYTHONDONTWRITEBYTECODE'] = '1'
    return e


# ---------------------------------------------------------------- source pins (written before arm 0)

def compute_pins(root=ROOT):
    return {p: sha_file(Path(root) / p) for p in PIN_FILES}


def write_pins():
    pins = compute_pins()
    if pins[BRIEF] != BRIEF_SHA:
        raise SystemExit('the brief hash differs: %s' % pins[BRIEF])
    write_json(PINS, {'written': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'files': pins,
                      'commit': s12.git('rev-parse', 'HEAD', text=True).strip()})
    return pins


def verify_pins(root=ROOT, pins_path=None):
    """Problems of the sources at `root` against pins.json (empty when every hash matches)."""
    pins_path = pins_path or PINS
    if not Path(pins_path).exists():
        return ['pins.json missing']
    want = read_json(pins_path)['files']
    bad = []
    for p, h in want.items():
        f = Path(root) / p
        if not f.exists():
            bad.append('%s missing' % p)
        elif sha_file(f) != h:
            bad.append('%s changed' % p)
    return bad


# ---------------------------------------------------------------- the cumulative clock

class Clock:
    def __init__(self, path):
        self.path = path
        self.rec = read_json(path) if path.exists() else {'clock_s': 0.0, 'steps': {}, 'segments': [], 'resumes': [],
                                                          'executor_timed': {}}
        self.mark = now()
        self.step = None
        self.rec['segments'].append({'start': self.mark, 'pid': os.getpid()})

    def tick(self, step=None, save=True):
        t = now()
        dt = t - self.mark
        self.mark = t
        self.rec['clock_s'] += dt
        st = step or self.step
        if st:
            self.rec['steps'][st] = self.rec['steps'].get(st, 0.0) + dt
        self.rec['segments'][-1]['end'] = t
        if save:
            write_json(self.path, self.rec)
        total = self.rec['clock_s'] + sum(self.rec['executor_timed'].values())
        if total > CLOCK_S:
            raise Stop('STOP 6: the cumulative 4.5-hour ceiling is spent (%.0f s)' % total)
        if st in STEP_CEIL and self.rec['steps'][st] > STEP_CEIL[st]:
            n = 5 if st in ('stage1', 'stage2a') else 6
            raise Stop('STOP %d: the %s ceiling (%d min) is passed (%.0f s)' % (n, st, STEP_CEIL[st] // 60,
                                                                                self.rec['steps'][st]))

    def begin(self, step):
        self.tick(self.step)
        self.step = step

    def left(self, step):
        return STEP_CEIL[step] - self.rec['steps'].get(step, 0.0)


# ---------------------------------------------------------------- the bulk cache and its manifest

def bulk_files(bulk=None):
    bulk = Path(bulk or BULK)
    if not bulk.exists():
        return []
    return sorted(str(f.relative_to(bulk)) for f in bulk.rglob('*.json') if SCRATCH not in f.relative_to(bulk).parts)


def write_manifest():
    files = {r: {'sha256': sha_file(BULK / r), 'bytes': (BULK / r).stat().st_size} for r in bulk_files()}
    write_json(BULK_MANIFEST, {
        'why': 'The owner rule forbids Git LFS and committed large intermediate dumps (circuit/ORCHESTRATION.md '
               'section 6: large intermediates as budgeted artifacts, recovery-critical bytes outside the VM).',
        'cache': str(BULK.relative_to(ROOT)) if BULK.is_relative_to(ROOT) else str(BULK),
        'durable_copy': {'location': DURABLE, 'layout': 'same relative paths, with a copy of this manifest'},
        'reproducibility': 'a re-run does not reproduce these hashes: records carry wall times',
        'files': files, 'total_bytes': sum(v['bytes'] for v in files.values())})


def bulk_state(bulk=None, manifest=None):
    """(present, problems): the cache against the manifest. Absent: (False, []). Partly present or altered: problems."""
    bulk, manifest = Path(bulk or BULK), Path(manifest or BULK_MANIFEST)
    if not manifest.exists():
        return False, ['bulk-manifest.json missing']
    man = read_json(manifest)['files']
    missing = [r for r in man if not (bulk / r).exists()]
    if man and len(missing) == len(man):
        return False, []
    bad = ['%s absent from the cache' % r for r in missing]
    for r, v in man.items():
        f = bulk / r
        if f.exists() and (f.stat().st_size != v['bytes'] or sha_file(f) != v['sha256']):
            bad.append('%s differs from the manifest' % r)
    bad += ['%s in the cache but not in the manifest' % r for r in sorted(set(bulk_files(bulk)) - set(man))]
    return True, bad


def bulk(rel):
    return BULK / rel


# ================================================================ test vectors (mutations)

DASH = '–'


def vec(c, a):
    c = (c + DASH * 9)[:9]
    a = (a + DASH * 6)[:6]
    return c + ' ' + a


def case_vector(w, blocks=(), ride=None, rows=None, placed=None, anchors=None, class_s='default'):
    """The vector of one case: S1 S2 S3 R1 to R6, then A0 A1 A2 A3 A4 A6. `blocks`: [{'rec', 'slot' (slot_centre,
    direction, dist) or None, 'geo' (a given geometry in place of the candidate's), 'dist', 'exempt'}]. `ride`: a
    callable giving (rides, reason). `rows`: a rows-only case. Returns (vector, reasons)."""
    if rows is not None:
        f, _ = check_rows16(w, rows)
        return vec('', acceptance_vector(f)), {k: v[:4] for k, v in f.items()}
    out, why = '', {}
    for b in blocks:
        r = s1_class(b['rec'].get('sig_classes') or [p[1] for p in site_signals(w.site_by, b['rec']['members'])])
        if r:
            why['S1'] = r
            return vec('F', ''), why
    out += 'P'
    for b in blocks:
        r = s2_order(b['rec'])
        if r:
            why['S2'] = r
            return vec(out + 'F', ''), why
    out += 'P'
    if ride is not None:
        ok, r = ride()
        if not ok:
            why['S3'] = r
            return vec(out + 'F', ''), why
    out += 'P'
    if not blocks:
        return vec(out, ''), why
    anchors = anchors or Anchors(w)
    placed = placed if placed is not None else placed_except(w)
    ctx = w.ctx
    chosen = []
    res = {}
    for b in blocks:
        rec = b['rec']
        z = lg.rec_size(ctx, rec)
        gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
        sl = b['slot']
        d = [k for k, v in lg.DIR_NAMES.items() if v == sl['direction']][0]
        ctx.model.memo_for(None)
        r, c = lg.candidate(ctx, placed, rec['front_board'], z, lg.rec_own(rec), sl['slot_centre'][0], sl['slot_centre'][1],
                            d, sl['dist'], ctx.spare(rec['front_board'], z), True, gm)
        if r:
            why['R1'] = r[0]
            return vec(out + 'F', ''), why
        res[rec['id']] = c
    out += 'P'
    first = None
    for b in blocks:
        rec = b['rec']
        cost, geo, disp = res[rec['id']]
        geo = b.get('geo') or geo
        rule, reason, extra = Rules(w, rec, anchors, class_s, exempt_record=b.get('exempt', False)).check(
            geo, b.get('dist', b['slot']['dist']))
        if rule is not None and (first is None or rule < first[0]):
            first = (rule, reason, extra)
        chosen.append((rec, {'geometry': geo, 'slot_centre': b['slot']['slot_centre'], 'direction': b['slot']['direction']}))
    if first:
        n = int(first[0][1])
        why[first[0]] = first[1]
        return vec(out + 'P' * (n - 2) + 'F', ''), why
    out += 'PPPPP'
    rows = w.rows_only(scene_links_replan(w, chosen, []))
    f, _ = check_rows16(w, rows)
    why.update({k: v[:4] for k, v in f.items()})
    return vec(out, acceptance_vector(f)), why


MUTATIONS = {
    'M1': 'PPPPPPPPP FPPPPP', 'M2': '––––––––– PPPPPP', 'M3': 'F–––––––– ––––––', 'M4': 'PF––––––– ––––––',
    'M5': 'PPF–––––– ––––––', 'M6': 'PPF–––––– ––––––', 'M7': 'PPPF––––– ––––––', 'M8': 'PPPPF–––– ––––––',
    'M9': 'PPPPPF––– ––––––', 'M10': 'PPPPPPF–– ––––––', 'M11': 'PPPPPPPF– ––––––', 'M12': 'PPPPPPPPF ––––––',
    'M13': '––––––––– FPFPPP', 'M14': '––––––––– FPPFPP', 'M15': '––––––––– FPPPFP', 'M16': '––––––––– FPPPPF',
    'M22': '––––––––– FFFPPP', 'M23': 'PPF–––––– ––––––', 'M24': 'PF––––––– ––––––', 'M25': 'PF––––––– ––––––',
    'M27a': 'PPF–––––– ––––––', 'M28': 'PF––––––– ––––––',
}
REASONS = {
    'M5': '/E1/REF5 (PRECISION, site K-P-18) has no host within 40 mm',
    'M6': '/E1/ASR_RAW (LOGIC, site K-P-16) has only full hosts within 55 mm: P-K-P-L13.01.01.01 at 52.6683 mm',
    'M23': '/O1/OCT_SELECTED (STATIC, site K-O1-1) is a static line, which rides on no other link (DS-79)',
    'M25': 'logic run 19-23 has 5 lines, above DA-03 c6 cap',
    'M27a': '/E2/NOT_FALL (ANALOGUE, site P-K-E2) has only full hosts within 45 mm: P-K-P-L05.01.01 at 40.9004 mm',
}


def slot_of(e):
    return {'slot_centre': list(e['slot_centre']), 'direction': e['direction'], 'dist': e['dist']}


def mutation_cases(w, slots):
    """Every mutation with its computed result. `slots`: the census slots of arm 0 (C4, C5), written before stage 1."""
    out = {}
    rd = Rides(w)
    an16 = Anchors(w)
    an12 = Anchors(w, 's12')
    pl12 = w.placed_index({}, skip=s12.SEARCHED)
    six26 = block_record(w, list(SITES), 26)
    l13 = record_block(w, 'P-K-P-L13.01.01.01')
    rec03 = w.byid[L03]
    rslot = {'slot_centre': rec03['slot_centre'], 'direction': rec03['direction'], 'dist': rec03['slot_distance_from_centre_mm']}

    def put(k, v, why, extra=None):
        out[k] = {'vector': v, 'expected': MUTATIONS.get(k), 'why': why, **(extra or {})}

    v, why = case_vector(w, [{'rec': six26, 'slot': rslot, 'exempt': True}])
    put('M1', v, why, {'R2_without_exemption': Rules(w, six26, an16).acc2(rec03['geometry'])})
    put('M28', *case_vector(w, [{'rec': block_record(w, w.byid['P-K-P-L13.01.01.01']['members'], 8), 'slot': None}]),
        {'block_size_by_block_record': block_record(w, w.byid['P-K-P-L13.01.01.01']['members'])['circuits']})
    rows = [r for r in w.base_rows_list if (r['board'], r['ref']) != ('K', 'U8409')]
    put('M2', *case_vector(w, rows=rows))
    m3 = block_record(w, ['K-P-16', 'K-P-1'])
    put('M3', *case_vector(w, [{'rec': m3, 'slot': None}]), {'classes': [p[1] for p in site_signals(w.site_by, ['K-P-16', 'K-P-1'])]})
    put('M4', *case_vector(w, [{'rec': block_record(w, list(SITES), 8), 'slot': None}]))

    def ride_one(sigs, hosts):
        def f():
            why = []
            r = ride_capped(w.ctx, rec03, sigs, hosts, rd.state0, w.site_by, w.s.limits, rd.eligible, why)
            return r is not None, why[0] if why else None
        return f
    put('M5', *case_vector(w, ride=ride_one([('/E1/REF5', 'PRECISION', 'K-P-18')], [w.byid['P-K-P-L15.01.02.01']])),
        {'host_distance_mm': p2.rider_distance(w.site_by['K-P-18'], w.byid['P-K-P-L15.01.02.01'])})
    sig16 = site_signals(w.site_by, ['K-P-16'])
    h13 = w.byid['P-K-P-L13.01.01.01']
    st_plain = {h13['id']: p2.link_signals(h13)}
    plain_asr = p2.ride(w.ctx, rec03, sig16[:1], [h13], dict(st_plain), w.site_by, w.s.limits) is not None
    wp = []
    plain_cur = p2.ride(w.ctx, rec03, sig16, [h13], dict(st_plain), w.site_by, w.s.limits, wp) is not None
    put('M6', *case_vector(w, ride=ride_one(sig16, [h13])),
        {'plain_ride_accepts_ASR_RAW': plain_asr, 'plain_ride_refuses_CURVED': (not plain_cur) and '/E1/CURVED' in (wp or [''])[0],
         'eligible': h13['id'] in rd.eligible})
    for k in ('M7', 'M8', 'M11'):
        put(k, *case_vector(w, [{'rec': six26, 'slot': slots[k]}], placed=pl12, anchors=an12, class_s='strict'),
            {'slot': slots[k]})
    e9 = dict(slots['C5_accepted'])
    put('M9', *case_vector(w, [{'rec': l13, 'slot': slot_of(e9), 'dist': 35.01}], placed=pl12, anchors=an12,
                           class_s='strict'), {'slot': slot_of(e9)})
    put('M10', *case_vector(w, [{'rec': l13, 'slot': slots['M10']}], placed=pl12, anchors=an12, class_s='strict'),
        {'slot': slots['M10']})
    geo12 = copy.deepcopy(e9['geometry'])
    geo12['K_tail'] = list(slots['M12_rect']['courtyard'])
    put('M12', *case_vector(w, [{'rec': l13, 'slot': slot_of(e9), 'geo': geo12}], placed=pl12, anchors=an12,
                            class_s='strict'), {'footprint': slots['M12_rect']})
    moves, _ = js.returned_moves(w)
    put('M13', *case_vector(w, rows=w.rows_only(w.scene_links(moves))))
    k14 = slots['M14']
    rows = copy.deepcopy(w.base_rows_list)
    for r in rows:
        if [r['board'], r['ref']] == k14:
            r.update({'new': None, 'new_face': None, 'shift_mm': None, 'moved_mm': None, 'step': 'no position', 'turned': False})
    put('M14', *case_vector(w, rows=rows), {'footprint': k14})
    rows = copy.deepcopy(w.base_rows_list)
    hit = [r for r in rows if (r['board'], r['ref']) == ('K', 'RV2113')]
    for r in hit:
        r['new_face'] = 'F'
    put('M15', *case_vector(w, rows=rows), {'row_found': bool(hit), 'paper_face': w.s.fps[('K', 'RV2113')]['side'],
                                            'protected': ('K', 'RV2113') in w.protected})
    rows = copy.deepcopy(w.base_rows_list)
    hit = [r for r in rows if (r['board'], r['ref']) == ('JL', 'U1217')]
    for r in hit:
        r['new'] = [r4(r['new'][0] + 0.25), r['new'][1]]
    put('M16', *case_vector(w, rows=rows), {'row_found': bool(hit), 'protected': ('JL', 'U1217') in w.protected})
    for k, st in (('M17_strict', 'strict'), ('M17_default', 'default')):
        v, why = case_vector(w, [{'rec': six26, 'slot': slots['M11']}], placed=pl12, anchors=an12, class_s=st)
        out[k] = {'R5': v[7], 'vector': v, 'why': why}
    rul = {}
    for st in ('strict', 'default'):
        bad, cls_s, anch = Rules(w, six26, an16, st).t1(rec03['geometry'])
        rul[st] = {'R5': 'F' if bad else 'P', 'class_N': [x for x in bad if x[1] == 'N'], 'class_S': sorted(cls_s),
                   'bad': bad}
    out['M18'] = rul
    rows = copy.deepcopy(w.base_rows_list)
    src = next(r for r in rows if (r['board'], r['ref']) == ('K', 'U1405'))
    for r in rows:
        if (r['board'], r['ref']) == ('K', 'U5110'):
            r.update({'new': copy.deepcopy(src['new']), 'new_face': src['new_face'], 'step': src['step']})
    put('M22', *case_vector(w, rows=rows))
    o1 = w.site_by['K-O1-1']
    put('M23', *case_vector(w, ride=ride_one([(o1['signals'][0], o1['classes'][0], 'K-O1-1')], rd.hosts)))
    put('M24', *case_vector(w, [{'rec': block_record(w, ['K-P-16', 'K-P-18', 'K-P-20'], 8), 'slot': None}]),
        {'circuits_needed': lg.circuits_needed([p[1] for p in site_signals(w.site_by, ['K-P-16', 'K-P-18', 'K-P-20'])])})
    m25 = dict(six26)
    lr = lg.link_record(w.ctx, 'x', 'P-K', 'P', list(SITES), w.site_by, lg.fh12_size(26, w.ctx.gopts))
    m25['positions'] = lr['positions']
    put('M25', *case_vector(w, [{'rec': m25, 'slot': None}]))
    st0 = {h['id']: p2.link_signals(h) for h in rd.hosts}
    a = p2.ride(w.ctx, rec03, [('/E1/REF5', 'PRECISION', 'K-P-18')], rd.hosts, st0, w.site_by, w.s.limits)
    b = ride_capped(w.ctx, rec03, [('/E1/REF5', 'PRECISION', 'K-P-18')], rd.hosts, rd.state0, w.site_by, w.s.limits,
                    rd.eligible)
    out['M26'] = {'ride': [a[0][0][1], a[0][0][2]] if a else None, 'ride_capped': [b[0][0][1], b[0][0][2]] if b else None}

    def one27():
        why = []
        r = rd.one(['K-P-16', 'K-P-20', 'P-K-E2'], why)
        return r is not None, why[0] if why else None
    put('M27a', *case_vector(w, ride=one27))
    t = rd.test(['K-P-16', 'K-P-20', 'P-K-E2'])
    out['M27b'] = {'S3': 'P' if t['rides'] else 'F', 'legal_orders': t['legal_orders'], 'orders': t['orders'],
                   'first_order': t['first_order'], 'K-P-16': [p[3:] for p in t['plan'] if p[2] == 'K-P-16']}
    return out


def mutation_problems(res):
    bad = []
    if res['M1'].get('R2_without_exemption') != 'a site beyond its class distance of the connector centres':
        bad.append('M1: R2 without the exemption gives %r' % res['M1'].get('R2_without_exemption'))
    if res['M28'].get('block_size_by_block_record') != 14:
        bad.append('M28: block_record size %s, expected 14' % res['M28'].get('block_size_by_block_record'))
    for k, want in MUTATIONS.items():
        if res[k]['vector'] != want:
            bad.append('%s: %s, expected %s' % (k, res[k]['vector'], want))
    for k, txt in REASONS.items():
        got = ' '.join(str(v) for v in res[k]['why'].values())
        if txt not in got:
            bad.append('%s: reason %r not in %r' % (k, txt, got))
    if not (res['M6'].get('plain_ride_accepts_ASR_RAW') and res['M6'].get('plain_ride_refuses_CURVED')):
        bad.append('M6: the unchanged ride does not accept /E1/ASR_RAW and refuse /E1/CURVED')
    if res['M17_strict']['R5'] != 'F' or res['M17_default']['R5'] != 'F':
        bad.append('M17: R5 %s / %s' % (res['M17_strict']['R5'], res['M17_default']['R5']))
    m18 = res['M18']
    if m18['strict']['R5'] != 'F' or m18['default']['R5'] != 'P' or m18['default']['class_N'] or \
            sorted(m18['default']['class_S']) != sorted(CLASS_S_PARTS):
        bad.append('M18: %s' % m18)
    if res['M26']['ride'] != ['P-K-P-L03.02.01', 34.6434] or res['M26']['ride_capped'] != ['P-K-P-L05.01.01', 38.103]:
        bad.append('M26: %s' % res['M26'])
    m = res['M27b']
    if m['S3'] != 'P' or (m['legal_orders'], m['orders']) != (2, 6) or m['first_order'] != ['K-P-20', 'P-K-E2', 'K-P-16'] or \
            m['K-P-16'] != [['P-K-P-L01.01.02', 54.376]] * 2:
        bad.append('M27b: %s' % m)
    for k in ('M15', 'M16'):
        if not res[k]['row_found'] or res[k]['protected']:
            bad.append('%s: the named row is missing or protected' % k)
    return bad


def choose_m14(w):
    """M14's row: the first K row in (board, ref) order that is not protected, not a trimmer, not one of the five
    ICs, and has a position."""
    for r in sorted(w.base_rows_list, key=lambda r: (r['board'], r['ref'])):
        k = (r['board'], r['ref'])
        if r['board'] == 'K' and k not in w.protected and not r['ref'].startswith('RV') and r['ref'] not in s12.FIVE \
                and r['new'] is not None:
            return [r['board'], r['ref']]
    raise Stop('STOP 4: no row for M14')


def choose_m12(w, rec, e, placed, anchors):
    """M12's footprint: the first anchored protected K footprint, in (board, ref) order, with a face-B base row, whose
    base-row courtyard put in place of the K tail of the accepted C5 slot passes R1 to R5 (meets none of the five
    IC courtyards and newly displaces no class N part). The selection uses only the rules before R6."""
    rules = Rules(w, rec, anchors, 'strict')
    for key in sorted(anchors.anchor):
        if key[0] != 'K' or key not in w.protected or not anchors.anchor[key]:
            continue
        row = w.base_rows.get(key)
        if not row or row['new'] is None or row['new_face'] != 'B':
            continue
        geo = copy.deepcopy(e['geometry'])
        geo['K_tail'] = list(row['new_courtyard'])
        if rules.r2(geo) or rules.r4(geo) or rules.t1(geo)[0]:
            continue
        return {'board': key[0], 'ref': key[1], 'courtyard': list(row['new_courtyard']), 'face': row['new_face'],
                'anchored_by': sorted(anchors.anchor[key])}
    raise Stop('STOP 4: no footprint for M12')


def mutation_slots(w, c4_firsts, c5_firsts, c5_accepted, l13):
    """The coordinates the mutations use, from the C4 and C5 census enumeration (grid 2.0 mm); written to
    checkpoints/ before stage 1."""
    pl12 = w.placed_index({}, skip=s12.SEARCHED)
    an12 = Anchors(w, 's12')
    sl = {'M7': c4_firsts['R1'], 'M8': c4_firsts['R2'], 'M11': c4_firsts['R5'], 'M10': c5_firsts['R4'],
          'C5_accepted': c5_accepted[0]}
    sl = {k: (dict(slot_of(v), why=v.get('why')) if k != 'C5_accepted' else v) for k, v in sl.items()}
    sl['M12_rect'] = choose_m12(w, l13, c5_accepted[0], pl12, an12)
    sl['M14'] = choose_m14(w)
    return sl


# ================================================================ arm 0: controls

import shutil  # noqa: E402

S12CENSUS = S12DIR / 'census.json'
C3B_LINKS = ('P-K-P-L03.01', 'P-K-P-L01.02.01', 'P-K-P-L05.01.01', 'P-K-P-L03.02.01', 'P-K-P-L01.01.02')
L13 = 'P-K-P-L13.01.01.01'
M_FIRST = ('M7', 'M8', 'M10', 'M11')


def control_record(name, ok, detail, t0):
    rec = {'control': name, 'pass': bool(ok), 'detail': detail, 'wall_s': round(now() - t0, 1)}
    write_json(CK / 'arm0' / ('%s.json' % name), rec)
    log(name, 'PASS' if ok else 'FAIL', rec['wall_s'])
    return rec


def c14_control():
    """C14: pins.json verified; a scratch copy of the pinned sources with one byte of replan.py changed is refused."""
    bad = verify_pins()
    scratch = BULK / SCRATCH / 'c14'
    if scratch.exists():
        shutil.rmtree(scratch)
    try:
        for p in PIN_FILES:
            d = scratch / p
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / p, d)
        f = scratch / PIN_FILES[0]
        b = bytearray(f.read_bytes())
        b[0] ^= 1
        f.write_bytes(bytes(b))
        bad2 = verify_pins(scratch)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        try:
            scratch.parent.rmdir()
        except OSError:
            pass
    ok = not bad and bad2 == ['%s changed' % PIN_FILES[0]]
    return ok, {'problems': bad, 'scratch_copy_problems': bad2, 'scratch_removed': not scratch.exists()}


def c13_control():
    r = read_json(HERE / 'checkpoints' / 'c13' / 'result.json')
    return r['pass'], r


def c1_control():
    p = subprocess.run([PY, str(S12DIR / 'joint_search.py'), '--check'], capture_output=True, text=True, cwd=str(ROOT),
                       env=env_nobytecode())
    ok = p.returncode == 0 and 'input pins, P3, P4, P11, 0 scenes and 6 checkpoint digests verified' in p.stdout
    return ok, {'returncode': p.returncode, 'stdout_tail': p.stdout.strip()[-400:], 'stderr_tail': p.stderr[-400:]}


def c3_control(w):
    ctx = w.ctx
    rec03 = w.byid[L03]
    lr = lg.link_record(ctx, 'x', 'P-K', 'P', list(SITES), w.site_by, lg.fh12_size(26, ctx.gopts))
    lr_err = c6.order_errors({'id': 'x', 'positions': lr['positions']})
    b = block_record(w, list(SITES), 26)
    b_err = c6.order_errors({'id': b['id'], 'positions': b['positions']})
    z = lg.rec_size(ctx, b)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    d = [k for k, v in lg.DIR_NAMES.items() if v == rec03['direction']][0]
    placed = placed_except(w)
    ctx.model.memo_for(None)
    why, c = lg.candidate(ctx, placed, 'P', z, lg.rec_own(b), rec03['slot_centre'][0], rec03['slot_centre'][1], d,
                          rec03['slot_distance_from_centre_mm'], ctx.spare('P', z), True, gm)
    geo_eq = disp_eq = None
    rows_n = rows_eq = None
    if not why:
        geo = c[1]
        geo_eq = s12.canon(geo) == s12.canon(rec03['geometry'])
        disp = lg.displaced(w.model, 'P', geo, ctx.latch)
        disp_eq = s12.canon(disp) == s12.canon(rec03['displaced'])
        rows = w.rows_only(scene_links_replan(w, [(b, {'geometry': geo, 'slot_centre': rec03['slot_centre'],
                                                       'direction': rec03['direction']})], []))
        rows_n = len(rows)
        rows_eq = s12.digest(rows) == s12.digest(w.base_rows_list)
    got = {'link_record': {'signals': lr['signals'], 'grounds': lr['grounds'], 'unused': lr['unused'],
                           'circuits_needed': lr['circuits_needed'], 'order_errors': lr_err},
           'block_record': {'signals': b['signals'], 'grounds': b['grounds'], 'unused': b['unused'],
                            'positions_equal_record': proj(b['positions']) == proj(rec03['positions']),
                            'order_errors': b_err},
           'record_slot': {'candidate': why[0] if why else 'legal', 'geometry_equal': geo_eq, 'displaced_equal': disp_eq},
           'rows_only': {'rows': rows_n, 'base_rows': len(w.base_rows_list), 'digest_equal_base': rows_eq}}
    ok = (got['link_record']['signals'], got['link_record']['grounds'], got['link_record']['unused'],
          got['link_record']['circuits_needed']) == (15, 10, 1, 25) and \
        any('logic run 19-23 has 5 lines' in e for e in lr_err) and len(lr_err) == 1 and \
        (b['signals'], b['grounds'], b['unused']) == (15, 11, 0) and got['block_record']['positions_equal_record'] and \
        not b_err and not why and geo_eq and disp_eq and rows_n == 452 and rows_eq
    return ok, got


def c3b_control(w):
    out = {}
    for lid in C3B_LINKS:
        h = w.byid[lid]
        o = capped_order(host_signals(h, w.site_by), h['circuits'])
        out[lid] = {'circuits': h['circuits'], 'built': o is not None,
                    'equal_record': o is not None and proj(o) == proj(h['positions']),
                    'order_errors': c6.order_errors({'id': lid, 'positions': o}) if o else None}
    return all(v['equal_record'] for v in out.values()), out


def census_control(w, rec, lid, want_tot):
    """C4 / C5: census_block with S12's settings on the three grids, against census.json."""
    cen = read_json(S12CENSUS)
    pl = w.placed_index({}, skip=s12.SEARCHED)
    an = Anchors(w, 's12')
    per, acc, firsts, counts = {}, [], None, {}
    for g in s12.GRIDS:
        c, a = census_block(w, rec, g, pl, an, 'strict', first_of=(g == s12.GRIDS[0]))
        if g == s12.GRIDS[0]:
            firsts = c.pop('firsts')
        want = cen['links'][lid]['%g' % g]
        eq = c['legal_R1'] == want['legal_rule1'] and all(c['after']['R%d' % n] == want['after_rule'][str(n)]
                                                           for n in (2, 3, 4, 5, 6))
        per['%g' % g] = {'legal_R1': sum(c['legal_R1'].values()),
                         'after': {t: sum(v.values()) for t, v in c['after'].items()}, 'equal_census_json': eq,
                         'complete': c['complete']}
        counts['%g' % g] = c
        acc += a  # census.json order: grid by grid, each grid sorted by key
    tot = [sum(p['legal_R1'] for p in per.values())] + [sum(p['after'][t] for p in per.values()) for t in ('R2', 'R4', 'R5', 'R6')]
    wacc = cen['accepted'].get(lid, [])
    acc_eq = [(a['slot_centre'], a['direction'], a['key']) for a in acc] == \
        [(a['slot_centre'], a['direction'], a['key']) for a in wacc]
    ok = all(p['equal_census_json'] for p in per.values()) and tot == list(want_tot) and acc_eq
    return ok, {'per_grid': per, 'totals_legal_R2_R4_R5_R6': tot, 'expected': list(want_tot), 'accepted': len(acc),
                'accepted_equal_census_json': acc_eq}, firsts, acc, counts


def l13_block(w):
    """The C5 block: the record block of P-K-P-L13.01.01.01 (Ruling P9; 8 circuits)."""
    return record_block(w, L13)


def arm0_mutations(w, clock):
    """The mutation control. Its slots come from C4 and C5 and are written to checkpoints/ before any vector."""
    slots = read_json(ck('mutation-slots.json'))
    res = mutation_cases(w, slots)
    bad = mutation_problems(res)
    write_json(ck('arm0/mutations.json'), {'results': res, 'problems': bad,
                                           'first_four_directly_after_C4_C5': {k: res[k]['vector'] for k in M_FIRST}})
    return not bad, bad


# ================================================================ arm 0: the remaining controls

import multiprocessing  # noqa: E402

L13B = 'P-K-P-L13.01.01.02'
L0322 = 'P-K-P-L03.02.02.01'
C9_SIZES = {(26,): 1, (14, 26): 7, (8, 26): 15, (14, 14): 9, (8, 14, 14): 27, (8, 8, 26): 24, (8, 8, 14): 39,
            (8, 8, 14, 14): 3, (8, 8, 8, 26): 4, (8, 8, 8, 14): 46, (8, 8, 8, 8): 12, (8, 8, 8, 8, 14): 6,
            (8, 8, 8, 8, 8): 9, (8, 8, 8, 8, 8, 8): 1}


def full_replay_child(out_json):
    t = now()
    doc, reads = s12.full_replay(None)
    write_json(out_json, {'doc': doc, 'working_tree_reads': reads, 'wall_s': round(now() - t, 1)})


def c2_control(w):
    """C2: S12 P8, the full base replay in a child process, equal to the base."""
    base_doc = s12.gjson(s12.BASE, s12.GATE)
    op = BULK / SCRATCH / 'c2-full.json'
    op.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([PY, str(HERE / 'replan.py'), '--full-replay', str(op)], capture_output=True, text=True,
                       timeout=1800, env=env_nobytecode(), cwd=str(ROOT))
    if p.returncode:
        return False, {'returncode': p.returncode, 'stderr_tail': p.stderr[-1500:]}
    d = read_json(op)
    op.unlink()
    try:
        op.parent.rmdir()
    except OSError:
        pass
    doc = d['doc']
    diffs = s12.compare_links(doc['links'], base_doc['links'])
    rows_eq = json.dumps(doc['replacement']) == json.dumps(base_doc['replacement']['footprints'])
    ways = doc['ways_out'] == base_doc['ways_out']
    cons = doc['consolidation'] == base_doc['consolidation']
    ok = not diffs and rows_eq and ways and cons and not doc['hold_errors']
    return ok, {'link_differences': diffs, 'rows_equal': rows_eq, 'ways_out_equal': ways, 'consolidation_equal': cons,
                'hold_errors': doc['hold_errors'], 'working_tree_reads': len(d['working_tree_reads']),
                'child_wall_s': d['wall_s']}


def c6_control(w):
    sb = w.site_by

    def gc(ids, n):
        return sorted(sorted(c['members']) for c in lg.gate_cluster([sb[i] for i in ids], n, 35.0, 'X'))
    eleven = sorted(set(w.byid[L03]['members']) | set(w.byid['P-K-P-L03.02.01']['members']) |
                    set(w.byid[L0322]['members']))
    five = [m for m in eleven if m not in SITES]
    got = {'eleven_at_26': gc(eleven, 26), 'five_at_14': gc(five, 14), 'six_at_14': gc(list(SITES), 14)}
    got['each_at_8'] = [gc(x, 8) for x in got['six_at_14']]
    got['six_at_8_one_step'] = gc(list(SITES), 8)
    want = {'eleven_at_26': sorted([sorted(SITES), ['K-P-22', 'K-P-24', 'K-P-34', 'K-P-55', 'K-P-63']]),
            'five_at_14': sorted([['K-P-22', 'K-P-24', 'K-P-34', 'K-P-55'], ['K-P-63']]),
            'six_at_14': sorted([['K-P-16', 'P-K-E2', 'P-K-E3'], ['K-P-18', 'K-P-20', 'P-K-E1']]),
            'six_at_8_one_step': sorted([['K-P-16', 'P-K-E3'], ['K-P-18', 'K-P-20'], ['P-K-E1'], ['P-K-E2']])}
    want['each_at_8'] = [sorted([['K-P-16', 'P-K-E2'], ['P-K-E3']]) if 'K-P-16' in x else
                         sorted([['K-P-18', 'K-P-20'], ['P-K-E1']]) for x in want['six_at_14']]
    rec_members = sorted([sorted(w.byid['P-K-P-L03.02.01']['members']), sorted(w.byid[L0322]['members'])])
    ladder = sorted(x for y in got['each_at_8'] for x in y)
    ok = got == want and got['five_at_14'] == rec_members and got['six_at_8_one_step'] != ladder
    return ok, {'got': got, 'recorded_members_L03_02': rec_members, 'one_step_differs_from_ladder':
                got['six_at_8_one_step'] != ladder}


def c7_control(w):
    sb = w.site_by
    h = w.byid[L13B]
    riders = [{'net': y['net'], 'class': y['class'], 'site': y['site'], 'from': y.get('from')} for y in h['riders_in']]
    d = p2.rider_distance(sb['K-P-63'], h)
    hs = host_signals(h, sb)
    al = lg.allocation(hs, 8)
    want_r = [{'net': n, 'class': 'ANALOGUE', 'site': 'K-P-63', 'from': L0322} for n in ('/M4B/1_REMOTE', '/M4B/2_REMOTE')]
    rd = Rides(w)
    mem = [x for x in hs if (x[0], x[1], x[2]) not in {(r['net'], r['class'], r['site']) for r in riders}]
    st = dict(rd.state0)
    st[h['id']] = mem
    why = []
    sigs = [(r['net'], r['class'], r['site']) for r in want_r]
    obs = ride_capped(w.ctx, w.byid[L0322], sigs, rd.hosts, st, sb, w.s.limits, rd.eligible, why)
    ok = all(r in riders for r in want_r) and round(d, 4) == 39.1702 and al is not None and proj(al) == proj(h['positions'])
    return ok, {'riders': riders, 'rider_distance_mm': round(d, 4), 'allocation_equals_record':
                al is not None and proj(al) == proj(h['positions']),
                'observation_ride_capped': {'plan': [[s_[0], hid, dd] for s_, hid, dd in obs[0]] if obs else None,
                                            'reason': why[0] if why else None,
                                            'note': 'host state = the host member signals only; the state at '
                                                    'consolidation time is not on record'}}


def c8_control(w):
    moves, _ = js.returned_moves(w)
    rows = w.rows_only(w.scene_links(moves))
    a = json.loads(json.dumps(judge_replan(w, moves, rows), default=_jdefault))
    b = json.loads(json.dumps(s12.judge(w, moves, rows), default=_jdefault))
    f, info = s12.check_rows(w, rows)
    new = sorted(x.split(' ', 1)[1] for x in info['protected']['new'])
    shifted = sorted(x.split(' ', 1)[1] for x in info['protected']['shifted'])
    ok = s12.canon(a) == s12.canon(b) and len(f.get('A2', [])) == 9 and \
        new == ['R5249', 'R5256', 'R8221', 'R8331', 'R8356'] and shifted == ['C8405', 'R5148', 'R5253', 'R8431']
    return ok, {'judge_replan_equals_s12_judge': s12.canon(a) == s12.canon(b), 'A2_rows': len(f.get('A2', [])),
                'new': new, 'shifted': shifted, 'rows_digest': s12.digest(rows)}


def c8b_control(w):
    sb = w.site_by
    live = [r for r in p2.live(w.base_out) if r['placed'] and r['id'] != L03 and r['joint'] == 'P-K' and
            r['front_board'] == 'P']
    got = {}
    for s_ in ('P-K-E1', 'P-K-E2', 'P-K-E3'):
        got[s_] = round(min(p2.rider_distance(sb[s_], x) for x in live
                            if sum(1 for p in x['positions'] if p['kind'] == 'unused') > 0), 4)
    return got == {'P-K-E1': 50.3968, 'P-K-E2': 40.9004, 'P-K-E3': 37.2}, got


def c9_control(w):
    sts = structures()
    empty = [s_ for s_ in sts if not s_['rides']]
    sizes = defaultdict(int)
    built = 0
    for s_ in empty:
        recs = [block_record(w, b) for b in s_['blocks']]
        built += all(r['built'] for r in recs)
        sizes[tuple(sorted(r['circuits'] for r in recs))] += 1
    tri = block_record(w, ['K-P-16', 'K-P-18', 'K-P-20'])['circuits']
    got = {'structures': len(sts), 'empty_ride_set': len(empty), 'built': built,
           'sizes': {'+'.join(map(str, k)): v for k, v in sorted(sizes.items())}, 'K-P-16+K-P-18+K-P-20': tri}
    ok = len(sts) == 877 and len(empty) == 203 and built == 203 and dict(sizes) == C9_SIZES and tri == 14
    return ok, got


def c10_control(w):
    rows = w.rows_only(w.scene_links({}))
    j = judge_replan(w, {}, rows)
    f0, info = check_rows16(w, rows)
    ok = all(j['passes'].values()) and bool(f0.get('A0')) and s12.digest(rows) == s12.digest(w.base_rows_list)
    return ok, {'passes': j['passes'], 'A0': f0.get('A0'), 'rows_equal_base': s12.digest(rows) == s12.digest(w.base_rows_list),
                'claimed': info['claimed']}


def c11_control(w, c4_ok):
    """C11: C4 holds with class_s='strict'; the count of candidates passing R5 only because class S is deferred is
    reported (here for the 26-way block on the 2.0 mm grid, then per block in stage 1)."""
    rec = block_record(w, list(SITES), 26)
    pl = placed_except(w)
    out = {}
    for st in ('default', 'strict'):
        c, _ = census_block(w, rec, s12.GRIDS[0], pl, Anchors(w), st)
        out[st] = {'class_s_deferred': c['class_s_deferred'], 'class_s_parts': c['class_s_parts'],
                   'after_R5': sum(c['after']['R5'].values())}
    ok = c4_ok and out['strict']['class_s_deferred'] == 0 and set(out['default']['class_s_parts']) <= set(CLASS_S_PARTS)
    return ok, {'C4_strict_holds': c4_ok, 'grid_2_mm_26_way': out}


def ride_key(rset):
    return '+'.join(sorted(rset))


def c15_control(w):
    rd = Rides(w)
    rd0 = Rides(w, fn='plain')
    res, plain = {}, {}
    for k in range(1, 7):
        for rs in itertools.combinations(SITES, k):
            res[ride_key(rs)] = rd.test(rs)
            plain[ride_key(rs)] = rd0.test(rs)
    rides = [k for k, v in res.items() if v['rides']]
    partial = sorted(k for k, v in res.items() if v['rides'] and v['legal_orders'] < v['orders'])
    two = {k: v['host_plans'] for k, v in res.items() if v['host_plans'] > 1}
    hosts = sorted({p[3] for v in res.values() if v['plan'] for p in v['plan']})
    got = {'ride': len(rides), 'none': len(res) - len(rides), 'member_order': sum(bool(v['member_order_rides'])
                                                                                for v in res.values()),
           'some_orders_only': partial, 'host_plans_above_1': two, 'hosts': hosts,
           'with_E1_rides': sorted(k for k in rides if 'P-K-E1' in k),
           'plain': [sum(v['rides'] for v in plain.values()), sum(bool(v['member_order_rides']) for v in plain.values())],
           'eligible_hosts': len(rd.eligible), 'not_eligible': sorted(rd.not_eligible)}
    want_p = sorted(['K-P-16+K-P-18+P-K-E2', 'K-P-16+K-P-18+P-K-E3', 'K-P-16+K-P-20+P-K-E2', 'K-P-16+K-P-20+P-K-E3'])
    ok = (got['ride'], got['none'], got['member_order']) == (19, 44, 16) and partial == want_p and \
        two == {'K-P-16+K-P-20+P-K-E3': 2} and hosts == ['P-K-P-L01.01.02', 'P-K-P-L05.01.01'] and \
        not got['with_E1_rides'] and got['plain'] == [27, 24]
    return ok, {'summary': got, 'sets': res}


def screen_s123(w, st, rides):
    """S1, S2 and S3 of one structure: (dead test or None, reason, block records)."""
    brs = [block_record(w, b) for b in st['blocks']]
    for b in brs:
        r = s1_class(b['sig_classes'])
        if r:
            return 'S1', '%s: %s' % (b['id'], r), brs
    for b in brs:
        r = s2_order(b)
        if r:
            return 'S2', '%s: %s' % (b['id'], r), brs
    if st['rides']:
        t = rides[ride_key(st['rides'])]
        if not t['rides']:
            return 'S3', t['reason'], brs
    return None, None, brs


def c16_control(w, rides):
    by = defaultdict(lambda: [0, 0])
    fail_at = defaultdict(int)
    for st in structures():
        if is_present(st):
            continue
        dead, _, _ = screen_s123(w, st, rides)
        by[len(st['rides'])][0 if dead is None else 1] += 1
        if dead:
            fail_at[dead] += 1
    passed = sum(v[0] for v in by.values())
    failed = sum(v[1] for v in by.values())
    got = {'pass': passed, 'fail': failed, 'fail_at': dict(fail_at), 'pass_by_ride_size': {str(k): by[k][0] for k in sorted(by)}}
    ok = passed == 622 and failed == 254 and dict(fail_at) == {'S3': 254} and \
        [by[k][0] for k in range(4)] == [202, 260, 135, 25] and all(by[k][0] == 0 for k in by if k > 3)
    return ok, got


# ================================================================ workers (fork pool)

_W = None
_CTX = {}


def _init_ctx():
    if 'placed' not in _CTX:
        _CTX['placed'] = placed_except(_W)
        _CTX['an'] = Anchors(_W)


def stage1_one(sites):
    w = _W
    _init_ctx()
    t0 = now()
    rec = block_record(w, list(sites))
    per, accs = {}, []
    for g in s12.GRIDS:
        c, a = census_block(w, rec, g, _CTX['placed'], _CTX['an'], 'default', _CTX.get('deadline'))
        per['%g' % g] = c
        accs.append(a)
    dist = distinct(accs)
    rings = ('≤ 24 mm', '24–35 mm')
    after = {t: sum(sum(c['after'][t].values()) for c in per.values()) for t in ('R2', 'R3', 'R4', 'R5', 'R6')}
    parts = defaultdict(int)
    for c in per.values():
        for k, v in c['class_s_parts'].items():
            parts[k] += v
    summ = {'block': rec['id'], 'sites': rec['members'], 'size': rec['circuits'], 'cable': rec['cable'],
            'cable_length_mm': rec['cable_length_mm'], 'centre': rec['centre'],
            'complete': all(c['complete'] for c in per.values()),
            'legal_R1': sum(sum(c['legal_R1'].values()) for c in per.values()), 'after': after,
            'after_R6_by_ring': {r: sum(c['after']['R6'][r] for c in per.values()) for r in rings},
            'distinct_survivors': len(dist), 'distinct_by_ring': {r: sum(1 for e in dist if e['ring'] == r) for r in rings},
            'class_s_deferred': sum(c['class_s_deferred'] for c in per.values()), 'class_s_parts': dict(parts),
            'cheapest_cost': dist[0]['cost'] if dist else None, 'wall_s': round(now() - t0, 1)}
    slim = [{k: e[k] for k in ('cost', 'key', 'direction', 'slot_centre', 'dist', 'ring', 'grid_mm', 'spot', 'class_s',
                               'anchored_covered')} for e in dist]
    return summ, slim, per


def pool_of(survivors):
    """Cheapest survivor per spot (a direction and a 2.0 mm cell), at most POOL_SPOTS spots."""
    best = {}
    for e in survivors:
        k = tuple(e['spot'])
        if k not in best or (e['cost'], e['key']) < (best[k]['cost'], best[k]['key']):
            best[k] = e
    return sorted(best.values(), key=lambda e: (e['cost'], e['key']))[:POOL_SPOTS]


def block_pool(bid):
    pools = _CTX.setdefault('pools', {})
    if bid not in pools:
        pools[bid] = pool_of(read_json(bulk('stage1/%s.json' % bid))['survivors'])
    return pools[bid]


def scene_rows(w, chosen, plan, moves=None):
    return w.rows_only(scene_links_replan(w, chosen, plan, moves))


def search_one(task):
    """Best-first search of one live structure; stops at its first passing scene or a bound."""
    w = _W
    _init_ctx()
    t0 = now()
    st, plan = task['structure'], task['plan']
    brs = [block_record(w, b) for b in st['blocks']]
    pl = [(r, block_pool(r['id'])) for r in brs]
    rules = {r['id']: Rules(w, r, _CTX['an']) for r in brs}
    mins = [p[0]['cost'] for _, p in pl]
    rest = [sum(mins[i:]) for i in range(len(pl) + 1)]
    log_ = {'structure': struct_id(st), 'pool_sizes': [len(p) for _, p in pl], 'legality_calls': 0, 'replays': [],
            'complete_scenes': 0, 'rejected_scenes': [], 'illegal': {}, 'bound': None, 'passed': None}
    heap = [(round(rest[0], 6), 0, ())]
    seq = itertools.count(1)
    placed_memo = {}
    while heap:
        cost, _, choice = heapq.heappop(heap)
        depth = len(choice)
        chosen = [(pl[i][0], m) for i, (j, m) in enumerate(choice)]
        if depth == len(pl):
            log_['complete_scenes'] += 1
            bad = reverify_blocks(w, chosen) if len(pl) > 1 else []
            if bad:
                log_['rejected_scenes'].append({'choice': [j for j, _ in choice], 'reverify': bad})
                continue
            if len(log_['replays']) >= REPLAY_CAP_STRUCT:
                log_['bound'] = '12 rows-only replays per structure'
                break
            t1 = now()
            rows = scene_rows(w, chosen, plan)
            f, info = check_rows16(w, rows)
            rec = {'n': len(log_['replays']) + 1, 'choice': [j for j, _ in choice],
                   'blocks': [{'block': r['id'], 'slot_centre': m['slot_centre'], 'direction': m['direction'],
                               'dist': m['dist'], 'ring': m['ring'], 'grid_mm': m['grid_mm'], 'cost': m['cost'],
                               'class_s': m['class_s'], 'geometry': m['geometry']} for r, m in chosen],
                   'vector': acceptance_vector(f), 'fails': {k: v[:4] for k, v in sorted(f.items())},
                   'returned': info['protected']['returned'], 'digest': s12.digest(rows),
                   'legality_calls_before': log_['legality_calls'], 'wall_s': round(now() - t1, 1)}
            log_['replays'].append(rec)
            if not f:
                log_['passed'] = rec['n']
                break
            continue
        rec_b, pool = pl[depth]
        key = tuple((pl[i][0]['id'], j) for i, (j, m) in enumerate(choice))
        if key not in placed_memo:
            placed_memo[key] = placed_except(w, extra=[dict(r, geometry=m['geometry']) for r, m in chosen])
        later = [x[0]['id'] for x in pl[depth + 1:]]
        for j, e in enumerate(pool):
            if log_['legality_calls'] >= LEGAL_CAP:
                log_['bound'] = '20 000 legality calls per structure'
                break
            log_['legality_calls'] += 1
            m, why = legal_block(w, rec_b, e, chosen, later, _CTX['an'], rules=rules[rec_b['id']],
                                 placed=placed_memo[key])
            if m is None:
                k = '%s %s' % (rec_b['id'], why)
                log_['illegal'][k] = log_['illegal'].get(k, 0) + 1
                continue
            c2 = sum(mm['cost'] for _, mm in chosen) + m['cost'] + rest[depth + 1]
            heapq.heappush(heap, (round(c2, 6), next(seq), choice + ((j, m),)))
        if log_['bound']:
            break
    log_['exhausted'] = not heap and log_['bound'] is None and log_['passed'] is None
    log_['rejected_scenes'] = log_['rejected_scenes'][:40]
    log_['wall_s'] = round(now() - t0, 1)
    return task['index'], log_


def stage4_one(task):
    """One S12 survivor of P-K-P-L13.01.01.01 with a kept scene's links in place: R1, then one rows-only replay."""
    w = _W
    chosen = [(block_record(w, b['sites']), {'geometry': b['geometry'], 'slot_centre': b['slot_centre'],
                                             'direction': b['direction']}) for b in task['blocks']]
    e = task['entry']
    ctx = w.ctx
    rec = w.rec(L13)
    placed = placed_except(w, skip=(L03, L13), extra=[dict(r, geometry=m['geometry']) for r, m in chosen])
    z = lg.rec_size(ctx, rec)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    d = [k for k, v in lg.DIR_NAMES.items() if v == e['direction']][0]
    ctx.model.memo_for(None)
    why, c = lg.candidate(ctx, placed, rec['front_board'], z, lg.rec_own(rec), e['slot_centre'][0], e['slot_centre'][1],
                          d, e['dist'], ctx.spare(rec['front_board'], z), True, gm)
    out = {'index': task['index'], 'slot_centre': e['slot_centre'], 'direction': e['direction'], 'grid_mm': e['grid_mm']}
    if why:
        out['legal'] = False
        out['why'] = why[0]
        return out
    geo = c[1]
    rows = scene_rows(w, chosen, task['plan'], {L13: {'geometry': geo, 'slot_centre': e['slot_centre'],
                                                      'direction': e['direction']}})
    f, info = check_rows16(w, rows)
    u = ('K', 'U5210') in s12.rowmap(rows)
    out.update({'legal': True, 'vector': acceptance_vector(f), 'U5210_has_row': u, 'fails': {k: v[:4] for k, v in f.items()},
                'pass': not f and not u, 'digest': s12.digest(rows)})
    return out


def pool_ctx():
    return multiprocessing.get_context('fork')


# ================================================================ stages

def all_subsets():
    return [list(rs) for k in range(1, 7) for rs in itertools.combinations(SITES, k)]


def stage1(w, clock):
    subs = all_subsets()
    todo = [x for x in subs if not bulk('stage1/%s.json' % block_id(x)).exists()]
    _CTX['deadline'] = now() + clock.left('stage1')
    done = len(subs) - len(todo)
    if todo:
        with pool_ctx().Pool(WORKERS) as pool:
            for summ, slim, per in pool.imap(stage1_one, todo):
                write_json(bulk('stage1/%s.json' % summ['block']), {'summary': summ, 'survivors': slim, 'per_grid': per})
                done += 1
                if not summ['complete']:
                    raise Stop('STOP 5: stage 1 cannot complete inside its ceiling (%s incomplete)' % summ['block'])
                if done % 8 == 0 or done == len(subs):
                    write_json(ck('stage1/progress.json'), {'blocks_done': done, 'of': len(subs)})
                    clock.tick()
    out = {}
    for x in subs:
        out[block_id(x)] = read_json(bulk('stage1/%s.json' % block_id(x)))['summary']
    write_json(ck('stage1/summary.json'), {'status': STATUS, 'reference_only': block_id(list(SITES)), 'blocks': out})
    clock.tick()
    return out


def stage2a(w, clock, rides, st1):
    recs = []
    n = 0
    for st in structures():
        if is_present(st):
            continue
        n += 1
        dead, why, brs = screen_s123(w, st, rides)
        r = {'id': struct_id(st), 'rides': st['rides'], 'blocks': st['blocks'], 'links': len(brs),
             'circuits': sum(b['circuits'] for b in brs), 'sizes': sorted(b['circuits'] for b in brs)}
        t = rides[ride_key(st['rides'])] if st['rides'] else None
        if t:
            r.update({'first_order': t['first_order'], 'host_plans': t['host_plans'], 'plan': t['plan']})
        else:
            r.update({'first_order': [], 'host_plans': 1, 'plan': []})
        if dead is None:
            empty = [b['id'] for b in brs if st1[b['id']]['distinct_survivors'] == 0]
            if empty:
                dead, why = 'census', 'no census survivor for %s' % ', '.join(empty)
        r['dead_at'], r['reason'] = dead, why
        r['live'] = dead is None
        r['cheapest_sum'] = round(sum(st1[b['id']]['cheapest_cost'] for b in brs), 6) if dead is None else None
        recs.append(r)
        if n % 100 == 0:
            write_json(ck('stage2a/progress.json'), {'structures_done': n})
            clock.tick()
    write_json(ck('stage2a/progress.json'), {'structures_done': n})
    write_json(bulk('stage2a/structures.json'), {'status': STATUS, 'structures': recs})
    clock.tick()
    return recs


def stage2b(w, clock, recs):
    live = [r for r in recs if r['live']]
    order = sorted(live, key=lambda r: (r['links'], r['circuits'], r['cheapest_sum'], r['id']))
    tasks = [{'index': i, 'structure': {'rides': r['rides'], 'blocks': r['blocks']}, 'plan': r['plan'] or [],
              'id': r['id']} for i, r in enumerate(order)]
    logs = {}
    for t in tasks:
        f = bulk('stage2b/%04d.json' % t['index'])
        if f.exists():
            logs[t['index']] = read_json(f)
    total = sum(len(l_['replays']) for l_ in logs.values())
    bound = next((l_['global_bound'] for l_ in logs.values() if l_.get('global_bound')), None)
    todo = [t for t in tasks if t['index'] not in logs]
    discarded = {'structures_in_flight_at_stop': 0}
    if todo and not bound and total < REPLAY_CAP:
        with pool_ctx().Pool(WORKERS) as pool:
            it = pool.imap(search_one, todo)
            for t in todo:
                i, lg_ = next(it)
                n = len(lg_['replays'])
                if total + n > REPLAY_CAP:
                    keep = REPLAY_CAP - total
                    cut = lg_['replays'][keep:]
                    lg_['replays'] = lg_['replays'][:keep]
                    if lg_['passed'] and lg_['passed'] > keep:
                        lg_['passed'] = None
                    lg_['discarded_replays_after_global_cap'] = len(cut)
                    bound = '1200 rows-only replays in stage 2b'
                total += len(lg_['replays'])
                if total >= REPLAY_CAP and not bound:
                    bound = '1200 rows-only replays in stage 2b'
                lg_['global_bound'] = bound
                lg_['id'] = t['id']
                write_json(bulk('stage2b/%04d.json' % i), lg_)
                logs[i] = lg_
                write_json(ck('stage2b/progress.json'), {'structures_done': len(logs), 'of': len(tasks),
                                                         'replays': total, 'bound': bound})
                clock.tick()
                if bound:
                    discarded['structures_in_flight_at_stop'] = min(WORKERS, len(todo) - (todo.index(t) + 1))
                    pool.terminate()
                    break
    # C12: the first 12 complete legal scenes, replayed again in sequence in this process
    first = []
    for i in sorted(logs):
        for rp in logs[i]['replays']:
            if len(first) < 12:
                first.append((i, rp))
    c12 = {'scenes': len(first)}
    if not first:
        c12.update({'pass': None, 'status': 'NOT RUN: no replay exists; no pool result is used'})
    else:
        diffs = []
        for i, rp in first:
            t = tasks[i]
            chosen = [(block_record(w, b), {'geometry': x['geometry'], 'slot_centre': x['slot_centre'],
                                           'direction': x['direction']}) for b, x in zip(t['structure']['blocks'], rp['blocks'])]
            if s12.digest(scene_rows(w, chosen, t['plan'])) != rp['digest']:
                diffs.append('%s replay %d' % (t['id'], rp['n']))
        c12.update({'pass': not diffs, 'differences': diffs})
    write_json(ck('arm0/C12.json'), {'control': 'C12', 'pass': c12['pass'], 'detail': c12})
    clock.tick()
    if c12['pass'] is False:
        raise Stop('STOP 1: control C12 fails: %s' % c12['differences'])
    summary = []
    for i in sorted(logs):
        l_ = logs[i]
        summary.append({'index': i, 'id': tasks[i]['id'], 'legality_calls': l_['legality_calls'],
                        'replays': len(l_['replays']), 'passed': l_['passed'], 'bound': l_['bound'],
                        'exhausted': l_['exhausted'], 'pool_sizes': l_['pool_sizes'], 'wall_s': l_['wall_s']})
    info = {'live': len(live), 'searched': len(logs), 'not_searched': len(tasks) - len(logs), 'replays': total,
            'bound': bound, 'discarded': discarded, 'C12': c12}
    write_json(ck('stage2b/summary.json'), {'status': STATUS, 'info': info, 'structures': summary})
    return tasks, logs, info


def scene_rank_key(w, rec_by, t, rp):
    disp_k = trims = newt = 0
    for b, x in zip(t['structure']['blocks'], rp['blocks']):
        geo = x['geometry']
        disp_k += len(lg.k_union(lg.displaced(w.model, 'P', geo, w.ctx.latch)))
        trims += len(lg.trim_list(w.model, 'P', geo))
        ut = links.under_tails(w.model, 'P', geo)
        tails = {('P', r) for r in ut['front tail']} | {('K', r) for r in ut['K tail']}
        newt += sum(1 for k in tails if k in w.protected and k not in w.base_tail)
    cost = round(sum(x['cost'] for x in rp['blocks']), 6)
    return [len(rp['blocks']), disp_k, trims, newt, cost, t['id']]


def neighbours(positions):
    out = []
    for i, p in enumerate(positions):
        if p['kind'] != 'signal':
            continue
        nb = []
        for j in (i - 1, i + 1):
            if 0 <= j < len(positions):
                q = positions[j]
                nb.append(q['net'] if q['kind'] == 'signal' else q['kind'])
        out.append({'net': p['net'], 'class': p['class'], 'site': p['site'], 'neighbours': nb})
    return out


def scene_body(w, n, t, rp, judge, vec_c, rows):
    chosen = [(block_record(w, b), x) for b, x in zip(t['structure']['blocks'], rp['blocks'])]
    out = scene_links_replan(w, [(r, x) for r, x in chosen], t['plan'])
    by = {r['id']: r for r in out}
    hosts = sorted({p[3] for p in t['plan']})
    host_tab = []
    for h in hosts:
        old = w.byid[h]['positions']
        new = by[h]['positions']
        host_tab.append({'host': h, 'old_order': proj(old), 'new_order': proj(new),
                         'neighbours_changed': [x for x in neighbours(new) if x not in neighbours(old)]})
    blocks = []
    for (r, x) in chosen:
        f, _ = block_figures(w, r, x)
        blocks.append({'block': r['id'], 'sites': r['members'], 'size': r['circuits'], 'cable': r['cable'],
                       'cable_length_mm': r['cable_length_mm'], 'slot_centre': x['slot_centre'],
                       'direction': x['direction'], 'ring': x['ring'], 'conductor_order': proj(r['positions']),
                       'figures': f, 'check4_input': neighbours(r['positions'])})
    return {'status': STATUS + '; DS-122 pair ratio of every built order NOT RUN; A12 NOT RUN', 'scene': n,
            'structure': t['id'], 'ride_set': t['structure']['rides'], 'ride_plan': t['plan'], 'hosts': host_tab,
            'blocks': blocks, 'vector': vec_c, 'judge': {k: judge[k] for k in ('passes', 'fails', 'protected_effective',
                                                                               'rows')},
            'returned_to_paper': rp['returned'],
            'P4_against_record': {'links_before': 1, 'links_after': len(blocks),
                                  'connectors_before': 2, 'connectors_after': 2 * len(blocks),
                                  'cables_before': [w.byid[L03]['cable']], 'cables_after': [b['cable'] for b in blocks],
                                  'trim_leads': {b['block']: b['figures']['trim_leads'] for b in blocks},
                                  'hold_K_by_hand': {b['block']: b['figures']['hold_K_by_hand'] for b in blocks},
                                  'host_orders_changed': hosts},
            'digest': s12.digest(rows)}


def stage3(w, clock, tasks, logs):
    passes = []
    for i in sorted(logs):
        l_ = logs[i]
        if l_['passed']:
            rp = l_['replays'][l_['passed'] - 1]
            passes.append((scene_rank_key(w, None, tasks[i], rp), i, rp))
    passes.sort(key=lambda x: x[0])
    info = {'passing_stage2b': len(passes), 'kept_cap_reached': len(passes) > KEEP, 'overlay_searches': 0,
            'overlay_cap_reached': False, 'judged': []}
    kept = []
    for rank, i, rp in passes[:KEEP]:
        t = tasks[i]
        f = ck('stage3/%s.json' % i)
        if f.exists():
            res = read_json(f)
        else:
            chosen = [(block_record(w, b), {'geometry': x['geometry'], 'slot_centre': x['slot_centre'],
                                           'direction': x['direction'], 'ring': x['ring']})
                      for b, x in zip(t['structure']['blocks'], rp['blocks'])]
            rows = scene_rows(w, chosen, t['plan'])
            can = info['overlay_searches'] < OVERLAY_CAP
            j = judge_replan(w, {}, rows, chosen, t['plan'], run_overlay_search=can)
            nsearch = len(j.get('overlay_blocks') or []) if can else 0
            f0, _ = check_rows16(w, rows)
            j = json.loads(json.dumps(j, default=_jdefault))
            res = {'structure': t['id'], 'rank': rank, 'A0': not f0.get('A0'), 'passes': j['passes'],
                   'fails': j['fails'], 'overlay_searches': nsearch, 'overlay_search_run': can,
                   'pass': not f0.get('A0') and all(j['passes'].values()), 'rows_digest': s12.digest(rows),
                   'judge': {k: j[k] for k in ('passes', 'fails', 'protected_effective', 'rows', 'link_figures')}}
            write_json(f, res)
        info['overlay_searches'] += res['overlay_searches']
        if not res['overlay_search_run']:
            info['overlay_cap_reached'] = True
        info['judged'].append({k: res[k] for k in ('structure', 'rank', 'A0', 'passes', 'pass', 'overlay_searches')})
        clock.tick()
        if res['pass']:
            kept.append((i, rp, res))
    CAND.mkdir(exist_ok=True)
    for n, (i, rp, res) in enumerate(kept, 1):
        t = tasks[i]
        chosen = [(block_record(w, b), {'geometry': x['geometry'], 'slot_centre': x['slot_centre'],
                                       'direction': x['direction'], 'ring': x['ring']})
                  for b, x in zip(t['structure']['blocks'], rp['blocks'])]
        rows = scene_rows(w, chosen, t['plan'])
        body = scene_body(w, n, t, dict(rp, blocks=[dict(x, geometry=x['geometry']) for x in rp['blocks']]),
                          res['judge'], 'PPPPPPPPP ' + 'P' * 6, rows)
        write_json(CAND / ('scene-%d.json' % n), body)
    info['kept'] = len(kept)
    write_json(ck('stage3/summary.json'), info)
    return kept, info


def stage4(w, clock, tasks, kept):
    cen = read_json(S12CENSUS)['accepted'][L13]
    seen, ents = set(), []
    for e in cen:
        k = (tuple(e['slot_centre']), e['direction'])
        if k not in seen:
            seen.add(k)
            ents.append(e)
    out = {'survivors': len(ents), 'scenes': []}
    jobs = []
    for n, (i, rp, res) in enumerate(kept, 1):
        t = tasks[i]
        blocks = [{'sites': b, 'geometry': x['geometry'], 'slot_centre': x['slot_centre'], 'direction': x['direction']}
                  for b, x in zip(t['structure']['blocks'], rp['blocks'])]
        for k, e in enumerate(ents):
            jobs.append({'scene': n, 'index': k, 'blocks': blocks, 'plan': t['plan'],
                         'entry': {x: e[x] for x in ('slot_centre', 'direction', 'dist', 'grid_mm')}})
    results = []
    if jobs:
        with pool_ctx().Pool(WORKERS) as pool:
            for job, r in zip(jobs, pool.imap(stage4_one, jobs)):
                r['scene'] = job['scene']
                results.append(r)
                if r['index'] == len(ents) - 1:
                    write_json(ck('stage4/scene-%d.json' % job['scene']), [x for x in results if x['scene'] == job['scene']])
                    clock.tick()
    for n in range(1, len(kept) + 1):
        rs = [x for x in results if x['scene'] == n]
        out['scenes'].append({'scene': n, 'legal': sum(1 for x in rs if x['legal']),
                              'replays': sum(1 for x in rs if x['legal']), 'pass': sum(1 for x in rs if x.get('pass')),
                              'reading': 'U5210 FOLLOW-ON SEEN AT ROWS LEVEL' if any(x.get('pass') for x in rs)
                              else 'U5210 FOLLOW-ON NOT SEEN'})
    out['replays'] = sum(s_['replays'] for s_ in out['scenes'])
    write_json(ck('stage4/summary.json'), out)
    return out


def verdict_of(recs, info2b, info3, kept, st_bounds):
    if kept:
        return 'RE-PLAN SCENE AT ROWS LEVEL, GATE REPLAY NOT RUN, NOT ADOPTED', []
    live = [r for r in recs if r['live']]
    if not live and not st_bounds:
        return 'NO RE-PLAN ON THIS DOMAIN (CENSUS-COMPLETE)', []
    bounds = ['pool of 20 spots per block']
    if info2b:
        if info2b.get('bound'):
            bounds.append(info2b['bound'])
        if info2b.get('not_searched'):
            bounds.append('%d live structures not searched' % info2b['not_searched'])
    if info3 and info3.get('kept_cap_reached'):
        bounds.append('5 kept scenes')
    if info3 and info3.get('overlay_cap_reached'):
        bounds.append('10 overlay block searches')
    return 'NO RE-PLAN FOUND (BOUNDED)', bounds


# ================================================================ the driver

def drive(resume=False):
    global _W
    CK.mkdir(parents=True, exist_ok=True)
    run_path = ck('run.json')
    if run_path.exists() and not resume:
        raise SystemExit('run.json exists: use --resume')
    bad = verify_pins()
    if bad:
        raise SystemExit('STOP 1: the sources differ from pins.json, the driver does not start: %s' % bad)
    clock = Clock(run_path)
    rec = clock.rec
    if resume:
        rec['resumes'].append({'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                               'reason': os.environ.get('S16_RESUME_REASON', 'interrupted')})
        if len(rec['resumes']) > RESUME_CAP:
            rec['stop'] = 'STOP 6: a fourth resume'
            write_json(run_path, rec)
            finish(rewrite_manifest=True)
            return
    else:
        rec['started'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        rec['commit'] = s12.git('rev-parse', 'HEAD', text=True).strip()
        gd = HERE / 'checkpoints' / 'guard'
        for f in sorted(gd.glob('start-*.json')) if gd.exists() else ():
            rec['executor_timed'][f.stem] = read_json(f)['wall_s']
        c13g = HERE / 'checkpoints' / 'c13' / 'guard.json'
        if c13g.exists():
            rec['executor_timed']['c13-detachment-test'] = read_json(c13g)['wall_s']
    rec['stop'] = None
    write_json(run_path, rec)

    def control(name, fn, *a):
        f = CK / 'arm0' / ('%s.json' % name)
        if f.exists() and read_json(f)['pass']:
            return read_json(f)['detail']
        t0 = now()
        ok, detail = fn(*a)
        control_record(name, ok, detail, t0)
        clock.tick()
        if not ok:
            raise Stop('STOP 1: control %s fails' % name)
        return detail

    stage_bounds = []
    try:
        clock.begin('arm0')
        control('C14', c14_control)
        control('C13', c13_control)
        control('C1', c1_control)
        w = s12.World()
        _W = w
        clock.tick()
        control('C3', c3_control, w)
        control('C3b', c3b_control, w)
        six = block_record(w, list(SITES), 26)
        l13 = l13_block(w)
        for name, rb, lid, tot in (('C4', six, L03, (813, 183, 183, 0, 0)), ('C5', l13, L13, (9464, 8841, 6903, 27, 27))):
            f = CK / 'arm0' / ('%s.json' % name)
            if not (f.exists() and read_json(f)['pass']):
                t0 = now()
                ok, detail, fi, acc, cnt = census_control(w, rb, lid, tot)
                write_json(bulk('arm0/%s-census.json' % name.lower()), {'counts': cnt, 'firsts_grid_2': fi, 'accepted': acc})
                control_record(name, ok, detail, t0)
                clock.tick()
                if not ok:
                    raise Stop('STOP 1: control %s fails' % name)
        if not ck('mutation-slots.json').exists():
            c4 = read_json(bulk('arm0/c4-census.json'))
            c5 = read_json(bulk('arm0/c5-census.json'))
            write_json(ck('mutation-slots.json'), mutation_slots(w, c4['firsts_grid_2'], c5['firsts_grid_2'],
                                                                 c5['accepted'], l13))
        if not (ck('arm0/mutation-control.json').exists() and read_json(ck('arm0/mutation-control.json'))['pass']):
            t0 = now()
            ok, bad = arm0_mutations(w, clock)
            write_json(ck('arm0/mutation-control.json'), {'control': 'mutations', 'pass': ok, 'problems': bad,
                                                          'wall_s': round(now() - t0, 1)})
            log('mutations', 'PASS' if ok else 'FAIL', bad)
            clock.tick()
            if not ok:
                raise Stop('STOP 3: computed mutation vectors differ from the brief: %s' % '; '.join(bad))
        control('C6', c6_control, w)
        control('C7', c7_control, w)
        control('C8', c8_control, w)
        control('C8b', c8b_control, w)
        control('C9', c9_control, w)
        control('C10', c10_control, w)
        control('C11', c11_control, w, read_json(CK / 'arm0' / 'C4.json')['pass'])
        rides = control('C15', c15_control, w)['sets']
        control('C16', c16_control, w, rides)
        control('C2', c2_control, w)
        clock.begin('stage1')
        st1 = stage1(w, clock)
        clock.begin('stage2a')
        if bulk('stage2a/structures.json').exists():
            recs = read_json(bulk('stage2a/structures.json'))['structures']
        else:
            recs = stage2a(w, clock, rides, st1)
        clock.begin('stage2b')
        tasks, logs, info2b = stage2b(w, clock, recs)
        clock.begin('stage3')
        kept, info3 = stage3(w, clock, tasks, logs)
        clock.begin('stage4')
        info4 = stage4(w, clock, tasks, kept)
        clock.begin(None)
        clock.tick()
        v, bounds = verdict_of(recs, info2b, info3, kept, stage_bounds)
        rec['verdict'] = v
        rec['bounds'] = bounds
        rec['finished'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    except Stop as e:
        rec['stop'] = str(e)
        log(str(e))
    try:
        clock.tick(save=False)
    except Stop:
        pass
    rec['ended'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    write_json(run_path, rec)
    finish(rewrite_manifest=True)
    log('driver end', rec.get('stop') or rec.get('verdict'))


def tallies(recs, s2b):
    """Per structure class (links, ride set size): dead at S1, S2, S3, at the census, live, searched, passing."""
    done = {x['id']: x for x in (s2b or {}).get('structures', [])}
    t = {}
    for r in recs:
        k = '%d links, %d ride sites' % (r['links'], len(r['rides']))
        d = t.setdefault(k, {'S1': 0, 'S2': 0, 'S3': 0, 'census': 0, 'live': 0, 'searched': 0, 'passing': 0})
        if r['dead_at']:
            d[r['dead_at']] += 1
        else:
            d['live'] += 1
            if r['id'] in done:
                d['searched'] += 1
                d['passing'] += bool(done[r['id']]['passed'])
    return dict(sorted(t.items()))


def finish(rewrite_manifest=False):
    if rewrite_manifest or not BULK_MANIFEST.exists():
        write_manifest()
    present, bad = bulk_state()
    if bad or (read_json(BULK_MANIFEST)['files'] and not present):
        raise SystemExit('finish needs the bulky intermediates in %s, matching the manifest: %s' % (BULK, bad or 'absent'))
    run = read_json(ck('run.json'))
    res = {'status': STATUS, 'brief': BRIEF, 'brief_sha256': BRIEF_SHA, 'pins': read_json(PINS), 'run': run,
           'stop': run.get('stop'), 'verdict': run.get('verdict'), 'bounds': run.get('bounds')}
    res['controls'] = {f.stem: read_json(f)['pass'] for f in sorted((CK / 'arm0').glob('C*.json'))}
    if ck('arm0/mutations.json').exists():
        m = read_json(ck('arm0/mutations.json'))
        res['mutations'] = {k: v.get('vector', 'not a vector') for k, v in m['results'].items()}
        res['mutation_problems'] = m['problems']
    if ck('stage1/summary.json').exists():
        res['stage1'] = {k: {x: v[x] for x in ('size', 'centre', 'legal_R1', 'after', 'distinct_survivors',
                                                'distinct_by_ring', 'class_s_deferred')}
                         for k, v in read_json(ck('stage1/summary.json'))['blocks'].items()}
    s2b = read_json(ck('stage2b/summary.json')) if ck('stage2b/summary.json').exists() else None
    if bulk('stage2a/structures.json').exists():
        recs = read_json(bulk('stage2a/structures.json'))['structures']
        res['stage2a'] = {'structures': len(recs), 'live': sum(r['live'] for r in recs),
                          'dead_at': {k: sum(1 for r in recs if r['dead_at'] == k) for k in ('S1', 'S2', 'S3', 'census')},
                          'by_class': tallies(recs, s2b),
                          'outcomes': [[r['id'], r['dead_at'] or 'live'] for r in recs]}
    if s2b:
        res['stage2b'] = s2b['info']
    for k in ('stage3', 'stage4'):
        if ck('%s/summary.json' % k).exists():
            res[k] = read_json(ck('%s/summary.json' % k))
    res['candidates'] = sorted(({'scene': int(f.stem.split('-')[1]), 'digest': read_json(f)['digest']}
                                for f in CAND.glob('scene-*.json')), key=lambda x: x['scene']) if CAND.exists() else []
    guards = {}
    gd = HERE / 'checkpoints' / 'guard'
    for f in sorted(gd.glob('*.json')) if gd.exists() else ():
        g = read_json(f)
        guards[f.stem] = {k: g.get(k) for k in ('returncode', 'finished', 'wall_s', 'peak_tree_rss_mib',
                                                'min_mem_available_mib', 'peak_docker_container_mem_mib', 'watchdog_fired')}
    res['guards'] = guards
    cks = {}
    for f in sorted(CK.rglob('*.json')):
        rel = f.relative_to(OUTDIR)
        if 'guard' in rel.parts or 'c13' in rel.parts or f.name in ('run.json', 'durable-copy.json') or \
                'progress' in f.name:
            continue
        cks[str(rel)] = sha_file(f)
    for f in sorted(CAND.glob('*.json')) if CAND.exists() else ():
        cks[str(f.relative_to(OUTDIR))] = sha_file(f)
    for r in bulk_files():
        cks[r] = sha_file(BULK / r)
    res['digests'] = dict(sorted(cks.items()))
    res['bulk_intermediates'] = {'cache': str(BULK.relative_to(ROOT)) if BULK.is_relative_to(ROOT) else str(BULK),
                                 'manifest': BULK_MANIFEST.name, 'files': len(bulk_files()), 'durable_copy': DURABLE}
    write_json(RESULT, res)
    return res


# ================================================================ check

def check():
    """Source pins (SOURCE CHANGED AFTER RUN), offline controls against their records, the mutations re-run, every
    digest, three stage 2b replays and every kept scene re-run; the cache against its manifest (PARTIAL CHECK when
    absent, CHECK FAILED when partial or altered)."""
    global _W
    errs, changed = [], verify_pins()
    if changed:
        print('SOURCE CHANGED AFTER RUN: %s' % changed)
    res = read_json(RESULT)
    present, bad = bulk_state()
    if bad:
        raise SystemExit('CHECK FAILED: the bulky intermediates in %s are partly present or differ from the manifest: %s'
                         % (BULK, bad))
    w = s12.World()
    _W = w
    for name, fn in (('C3', c3_control), ('C3b', c3b_control), ('C8b', c8b_control), ('C9', c9_control)):
        if not (CK / 'arm0' / ('%s.json' % name)).exists():
            continue
        ok, detail = fn(w)
        want = read_json(CK / 'arm0' / ('%s.json' % name))
        if ok != want['pass'] or s12.canon(json.loads(json.dumps(detail, default=_jdefault))) != s12.canon(want['detail']):
            errs.append('%s differs from its record' % name)
    slots = read_json(ck('mutation-slots.json')) if ck('mutation-slots.json').exists() else None
    if slots is not None and ck('arm0/mutations.json').exists():
        again = json.loads(json.dumps(mutation_cases(w, slots), default=_jdefault))
        if s12.canon(again) != s12.canon(read_json(ck('arm0/mutations.json'))['results']):
            errs.append('the mutation results differ on re-run')
    man = read_json(BULK_MANIFEST)['files']
    checked = 0
    for path, want in res.get('digests', {}).items():
        if path in man:
            if man[path]['sha256'] != want:
                errs.append('manifest and result.json disagree on %s' % path)
            if not present:
                continue
            f = BULK / path
        else:
            f = OUTDIR / path
        checked += 1
        if not f.exists() or sha_file(f) != want:
            errs.append('digest of %s differs' % path)
    reran = 0
    if present and bulk('stage2a/structures.json').exists():
        recs = read_json(bulk('stage2a/structures.json'))['structures']
        live = sorted([r for r in recs if r['live']], key=lambda r: (r['links'], r['circuits'], r['cheapest_sum'], r['id']))
        for i, r in enumerate(live):
            f = bulk('stage2b/%04d.json' % i)
            if reran >= 3 or not f.exists():
                break
            lg_ = read_json(f)
            for rp in lg_['replays'][:1]:
                chosen = [(block_record(w, b), {'geometry': x['geometry'], 'slot_centre': x['slot_centre'],
                                               'direction': x['direction']}) for b, x in zip(r['blocks'], rp['blocks'])]
                if s12.digest(scene_rows(w, chosen, r['plan'] or [])) != rp['digest']:
                    errs.append('stage 2b replay of %s differs' % r['id'])
                reran += 1
    for f in sorted(CAND.glob('scene-*.json')) if CAND.exists() else ():
        body = read_json(f)
        chosen = [(block_record(w, b['sites']), {'geometry': None, 'slot_centre': b['slot_centre'], 'direction': b['direction'],
                                                 'dist': math.hypot(b['slot_centre'][0] - block_record(w, b['sites'])['centre'][0],
                                                                    b['slot_centre'][1] - block_record(w, b['sites'])['centre'][1]),
                                                 'ring': b['ring']}) for b in body['blocks']]
        placed_chosen = []
        for r, e in chosen:
            m, why = legal_block(w, r, e, placed_chosen, [], Anchors(w))
            if m is None:
                errs.append('%s: block %s not legal: %s' % (f.name, r['id'], why))
                break
            placed_chosen.append((r, m))
        else:
            if s12.digest(scene_rows(w, placed_chosen, body['ride_plan'])) != body['digest']:
                errs.append('%s: rows digest differs' % f.name)
    if errs or changed:
        raise SystemExit('CHECK FAILED: %s' % ((errs + ['SOURCE CHANGED AFTER RUN: %s' % changed]) if changed else errs))
    head = 'offline controls and the mutations re-run equal, %d digests, %d stage 2b replays and %d scenes re-run' % (
        checked, reran, len(list(CAND.glob('scene-*.json'))) if CAND.exists() else 0)
    if not present:
        print('PARTIAL CHECK (bulky intermediates absent from %s; the copy is at %s): %s; the %d cached digests were '
              'compared with the manifest only, and the stage 2b replays were NOT RUN' % (BULK, DURABLE, head, len(man)))
        return
    print('result.json current: pins verified, %s (%d cached files verified against the manifest)' % (head, len(man)))


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--pin', action='store_true')
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--finish', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--full-replay', metavar='OUT')
    a = ap.parse_args()
    if a.pin:
        print(json.dumps(write_pins(), indent=1))
    elif a.full_replay:
        full_replay_child(a.full_replay)
    elif a.run or a.resume:
        drive(resume=a.resume)
    elif a.finish:
        finish()
    elif a.check:
        check()
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
