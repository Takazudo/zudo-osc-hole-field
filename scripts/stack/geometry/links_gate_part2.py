"""Part 2 of the gate option of record (ST-02 attempt a8, part 2): the ways out of DS-84 and DS-85 for the links
without a place, the consolidation pass, and the re-placement search of the displaced footprints (DS-60, DS-88,
DS-97). links_gate.generate() runs it on the placement of part 1; the rules and figures are read from
link-gate-options.json (`ways_out`, `consolidation`, `replacement`). Courtyard level on unvalidated drafts: no count
is a minimum, no position is a fit, nothing is routed, selected or adopted.
"""
import itertools
import json
import math
import re

import stackgeom as sg
import links
import links_gate as lg
from links import r4, val, FRONTS

RAIL_LEDGER = 'design/power/rail-ledger.json'
FLOORPLAN = 'design/partition/floorplan-candidate.json'
SCOPE_BOARDS = ('K', 'JL', 'JR', 'P') + lg.ADAPTERS
SENSITIVE_FUNCTION = {'AS3340D': 'VCO core (AS3340D)', 'LF398M_NOPB': 'sample and hold (LF398M_NOPB)',
                      'REF5050AIDR': 'voltage reference (REF5050AIDR)'}
COUNTED_SYMBOLS = ('AS3340D', 'OPA4197IDR', 'OPA4197IPWR', 'LF398M_NOPB', 'LM13700M_NOPB')


def load_part2_inputs(inp):
    root = inp['root']
    inp.setdefault('rail_ledger', json.loads((root / RAIL_LEDGER).read_text()))
    inp.setdefault('floorplan', json.loads((root / FLOORPLAN).read_text()))
    return inp


def part2_hashes(inp):
    root = inp['root']
    return {p: sg.sha256_file(root / p) for p in (RAIL_LEDGER, FLOORPLAN)}


def _c(rect):
    return ((rect[0] + rect[2]) / 2.0, (rect[1] + rect[3]) / 2.0)


def rider_distance(site, host):
    """The larger of the distances from the site to the host connector centre on the front board and on K."""
    g = host['geometry']
    f, k = _c(g['front_connector']), _c(g['K_connector'])
    kx = site.get('K_xy') or site['xy']
    return r4(max(math.hypot(site['xy'][0] - f[0], site['xy'][1] - f[1]), math.hypot(kx[0] - k[0], kx[1] - k[1])))


def limits_of(gopts):
    return val(gopts['ways_out']['rider_distance_mm'])


def link_signals(r):
    return [(p['net'], p['class'], p['site']) for p in r['positions'] if p['kind'] == 'signal']


def live(out):
    return [r for r in out if not r.get('gone')]


def ride(ctx, link, signals, hosts, state, site_by, limits):
    """Way 1 for one link: each signal to the nearest host of the same joint and front board within its class distance
    whose allocation stays legal at its own size. Returns the riders [(signal, host id, distance)] and the new host
    signal lists, or None when a signal cannot ride (then nothing moves)."""
    tmp = {}
    plan = []
    for sig in signals:
        site = site_by[sig[2]]
        opts = sorted((rider_distance(site, h), h['id'], h) for h in hosts
                      if h['id'] != link['id'] and h['joint'] == link['joint'] and h['front_board'] == link['front_board'])
        host = None
        for d, hid, h in opts:
            if d > limits[sig[1]] + 1e-9:
                break
            cur = tmp.get(hid, state[hid])
            need = lg.circuits_needed([s[1] for s in cur] + [sig[1]], ctx.rule)
            if need is not None and need <= h['circuits']:
                host = (hid, d, cur)
                break
        if host is None:
            return None
        tmp[host[0]] = host[2] + [sig]
        plan.append((sig, host[0], host[1]))
    return plan, tmp


def reallocate(ctx, host, sigs, origin):
    """The host keeps size, place and cable and is allocated again (DS-62, DS-77, DS-78); riders are marked."""
    pos = lg.allocation(sigs, host['circuits'], ctx.rule, ctx.adapter_order)
    for p in pos:
        if p['kind'] == 'signal' and (p['site'], p['net']) in origin:
            p['rider_from'] = origin[(p['site'], p['net'])]
    host.update({'positions': pos, 'signals': len(sigs), 'grounds': sum(1 for p in pos if p['kind'] == 'ground'),
                 'unused': sum(1 for p in pos if p['kind'] == 'unused'),
                 'circuits_needed': lg.circuits_needed([s[1] for s in sigs], ctx.rule)})


def apply_ride(ctx, out, link, plan, tmp, origin, gone):
    by = {r['id']: r for r in out}
    for sig, hid, d in plan:
        origin[(sig[2], sig[0])] = link['id']
        by[hid].setdefault('riders_in', []).append({'net': sig[0], 'class': sig[1], 'site': sig[2], 'from': link['id'],
                                                    'distance_mm': d})
    for hid, sigs in sorted(tmp.items()):
        reallocate(ctx, by[hid], sigs, origin)
    link['riders_out'] = [{'net': s[0], 'class': s[1], 'site': s[2], 'host': h, 'distance_mm': d} for s, h, d in plan]
    link['gone'] = gone
    link['positions'] = []
    link['signals_before'] = link['signals']
    link['signals'] = link['grounds'] = link['unused'] = 0


def way1(ctx, out, site_by, limits, ids):
    """Way 1 over the links `ids` in the record's order first; when a link is left without riders the other orders are
    tried and the first order in which the most links ride is kept."""
    hosts = [r for r in live(out) if r['placed']]
    base = {h['id']: link_signals(h) for h in hosts}
    by = {r['id']: r for r in out}
    best = None
    tried = 0
    for order in itertools.permutations(ids):
        tried += 1
        state = dict(base)
        rides = {}
        for lid in order:
            res = ride(ctx, by[lid], link_signals(by[lid]), hosts, state, site_by, limits)
            if res:
                rides[lid] = res
                state.update(res[1])
        if best is None or len(rides) > len(best[1]):
            best = (list(order), rides)
        if len(rides) == len(ids):
            break
    order, rides = best
    origin = {}
    for h in hosts:
        for p in h['positions']:
            if p.get('rider_from'):
                origin[(p['site'], p['net'])] = p['rider_from']
    # apply in the kept order, recomputing against the applied state (the same as the trial)
    for lid in order:
        if lid not in rides:
            continue
        state = {h['id']: link_signals(h) for h in hosts}
        plan, tmp = ride(ctx, by[lid], link_signals(by[lid]), hosts, state, site_by, limits)
        apply_ride(ctx, out, by[lid], plan, tmp, origin, 'riders (way 1)')
    return {'record_order': list(ids), 'order_used': order, 'orders_tried': tried,
            'links_riding': [x for x in order if x in rides]}


def class_accept(link, site_by, limits):
    sites = [site_by[m] for m in link['members']]

    def accept(geo):
        f, k = _c(geo['front_connector']), _c(geo['K_connector'])
        for s in sites:
            lim = min(limits[c] for c in s['classes'])
            kx = s.get('K_xy') or s['xy']
            if max(math.hypot(s['xy'][0] - f[0], s['xy'][1] - f[1]), math.hypot(kx[0] - k[0], kx[1] - k[1])) > lim + 1e-9:
                return 'a site beyond its class distance of the connector centres'
        return None
    return accept


def search_grids(ctx, placed, r, radius, accept=None):
    """The record's grids (2.0 mm, then 0.5 mm, then 0.25 mm where the smallest miss on 0.5 mm is below 0.5 mm)."""
    rg = ctx.gopts['refinement']
    g1, g2 = val(rg['grids_mm'])
    thr = val(rg['quarter_grid_below_mm'])
    front, own, centre, size = r['front_board'], lg.rec_own(r), r['centre'], lg.rec_size(ctx, r)
    tried, miss = [], None
    ctx.model.memo_for(r['id'])
    for g in (ctx.step0, g1, g2):
        if g == g2 and (miss is None or miss >= thr):
            break
        offs = ctx.grid(g, radius=radius)
        best, tally = lg.search(ctx, placed, front, centre, size, own, offsets=offs, accept=accept)
        tried.append(g)
        if best:
            lg.place(ctx, placed, r, size, centre, own, offsets=offs, grid=g, best=best)
            return True, tried
        miss = lg.smallest_miss(tally)
    ctx.model.drop_memo(r['id'])
    return False, tried


def way3_holds(ctx, r, radius):
    """Whether a place could exist once the keep-out of SLV-L1 or SLV-L2 is left out: False when every candidate of
    the widest search lies farther from the keep-out than its radius (the keep-out cannot be the blocker)."""
    out = {}
    size = lg.rec_size(ctx, r)
    reach = lg.reach_of(ctx, r['front_board'], size, 0.0)
    for f in ctx.model.fixings:
        if f['id'] not in ('SLV-L1', 'SLV-L2'):
            continue
        rad = max(f['r_K'], f.get('r_front') or 0.0)
        far = []
        for xy in (f['K'], f['front']):
            far.append(math.hypot(xy[0] - r['centre'][0], xy[1] - r['centre'][1]))
        d = min(far)
        out[f['id']] = {'distance_mm': r4(d), 'reach_mm': r4(radius + reach + rad),
                        'holds': None if d <= radius + reach + rad else False}
    return out


def without_keepout(ctx, out, r, fid, radius, accept):
    """Whether the link has a place under way 2 (radius, class distance) once the keep-out of fixing `fid` is left out
    on every board. Only slot centres whose candidates can reach the keep-out are searched: no other candidate changes."""
    model = ctx.model
    label = 'fixing keep-out %s' % fid
    f = next(x for x in model.fixings if x['id'] == fid)
    saved = {}
    for key, idx in model.forb.items():
        if any(p[2] == label for _, p in idx.items):
            saved[key] = idx
            ni = sg.RectIndex()
            for rect, p in idx.items:
                if p[2] != label:
                    ni.add(rect, p)
            model.forb[key] = ni
    rad = max(f['r_K'], f.get('r_front') or 0.0)
    boxes = [sg.circle_rect(xy[0], xy[1], 2 * rad) for xy in (f['K'], f['front'])]
    rg = ctx.gopts['refinement']
    grids = [ctx.step0] + list(val(rg['grids_mm']))
    size, front, own, centre = lg.rec_size(ctx, r), r['front_board'], lg.rec_own(r), r['centre']
    placed = lg.placed_index(live(out))
    found, searched = None, 0
    try:
        for g in grids:
            reach = lg.reach_of(ctx, front, size, g)
            offs = [o for o in ctx.grid(g, radius=radius)
                    if any(sg.inter([centre[0] + o[0] - reach, centre[1] + o[1] - reach, centre[0] + o[0] + reach,
                                     centre[1] + o[1] + reach], b) for b in boxes)]
            searched += len(offs)
            if not offs:
                continue
            model.memo_for(None)
            best, _ = lg.search(ctx, placed, front, centre, size, own, offsets=offs, accept=accept)
            if best:
                found = {'grid_mm': g, 'slot_centre': list(best[5])}
                break
    finally:
        model.forb.update(saved)
        model.memo_for(None)
    return {'holds': bool(found), 'test': 'way 2 search (radius %g mm, class distance) without the keep-out of %s over '
            'the %d slot centres whose candidates can reach it, on grids %s mm' % (radius, fid, searched,
                                                                              ', '.join('%g' % x for x in grids)),
            'place_without_the_keepout': found}


def pad_distance(model, front, fc, shrink):
    """Separation from the field at the reduced growth to the nearest panel-hardware obstacle (pad grown by the obstacle
    model), within 5 mm."""
    f = sg.grow(fc, -shrink)
    best = None
    for _, (kind, g, label) in model.forb[(front, 'B')].near(sg.grow(f, 5.0)):
        if kind != 'rect' or not label.startswith('panel hardware'):
            continue
        dx = max(g[0] - f[2], f[0] - g[2], 0.0)
        dy = max(g[1] - f[3], f[1] - g[3], 0.0)
        d = math.hypot(dx, dy)
        if best is None or d < best[0]:
            best = (r4(d), label.split(' ')[-1])
    return best


def ways_out(ctx, out, site_by):
    """Point 1: ways 1 to 5 for every link without a place (oversize links are not among them in the record)."""
    gopts = ctx.gopts
    wo = gopts['ways_out']
    limits = limits_of(gopts)
    ids = [r['id'] for r in out if not r['placed'] and not r.get('oversize') and not r.get('gone')]
    rec = {'links_without_a_place': list(ids), 'limits_mm': limits}
    by0 = {r['id']: r for r in out}
    for lid in ids:
        r = by0[lid]
        r['part_1_analysis'] = {k: r.get(k) for k in ('signals', 'nearest_misses', 'most_frequent_blockers', 'why_no_place')}
    w1 = way1(ctx, out, site_by, limits, ids)
    rec['way_1'] = w1
    by = {r['id']: r for r in out}
    for lid in w1['links_riding']:
        by[lid]['way_out'] = {'way': 1, 'riders': len(by[lid]['riders_out']),
                              'hosts': sorted({x['host'] for x in by[lid]['riders_out']})}
    left = [lid for lid in ids if lid not in w1['links_riding']]
    for lid in left:
        r = by[lid]
        r['way_out'] = {'way': None, 'way_1': 'no: %s' % why_no_ride(ctx, out, r, site_by, limits)}
    # way 2
    r2 = val(wo['way_2_radius_mm'])
    for lid in left:
        r = by[lid]
        placed = lg.placed_index(live(out))
        ok, tried = search_grids(ctx, placed, r, r2, class_accept(r, site_by, limits))
        r['way_out']['way_2'] = {'radius_mm': r2, 'grids_tried_mm': tried, 'found': ok}
        if ok:
            r['way_out']['way'] = 2
    left = [lid for lid in left if not by[lid]['placed']]
    # way 3
    for lid in left:
        r = by[lid]
        h = way3_holds(ctx, r, max(r2, ctx.radius))
        r['way_out']['way_3'] = h
        for fid, v in h.items():
            if v['holds'] is None:
                v.update(without_keepout(ctx, out, r, fid, r2, class_accept(r, site_by, limits)))
        if any(v['holds'] for v in h.values()):
            raise NotImplementedError('way 3 trial needed for %s' % lid)
    rec['way_3_trials'] = []
    # way 4
    g4 = val(wo['way_4_field_growth_mm'])
    shrink = r4(val(gopts['field']['growth_mm']) - g4)
    n4 = 0
    for lid in left:
        r = by[lid]
        if n4 >= val(wo['way_4_max_links']):
            r['way_out']['way_4'] = {'found': False, 'why': 'the limit of %d links is taken' % val(wo['way_4_max_links'])}
            continue
        placed = lg.placed_index(live(out))
        ctx.panel_shrink = shrink
        try:
            ok, tried = search_grids(ctx, placed, r, None)
        finally:
            ctx.panel_shrink = 0.0
        r['way_out']['way_4'] = {'field_growth_against_panel_pads_mm': g4, 'grids_tried_mm': tried, 'found': ok}
        if ok:
            n4 += 1
            r['way_out']['way'] = 4
            r['field_growth_against_panel_pads_mm'] = g4
            d = pad_distance(ctx.model, r['front_board'], r['geometry']['front_connector'], shrink)
            r['way_out']['way_4']['distance_from_field_to_pad_mm'] = d[0] if d else None
            r['way_out']['way_4']['nearest_pad_of'] = d[1] if d else None
    for lid in left:
        r = by[lid]
        if not r['placed']:
            r['way_out']['way'] = 5
    rec['per_link'] = {lid: by[lid]['way_out'] for lid in ids}
    return rec


def why_no_ride(ctx, out, r, site_by, limits):
    hosts = [h for h in live(out) if h['placed']]
    state = {h['id']: link_signals(h) for h in hosts}
    for sig in link_signals(r):
        site = site_by[sig[2]]
        near = sorted((rider_distance(site, h), h['id'], h) for h in hosts
                      if h['joint'] == r['joint'] and h['front_board'] == r['front_board'] and h['id'] != r['id'])
        within = [(d, hid, h) for d, hid, h in near if d <= limits[sig[1]] + 1e-9]
        ok = [hid for d, hid, h in within
              if (lambda n: n is not None and n <= h['circuits'])(lg.circuits_needed([s[1] for s in state[hid]] + [sig[1]], ctx.rule))]
        if not ok:
            return '%s (%s, site %s) has %s' % (sig[0], sig[1], sig[2], 'no host within %g mm' % limits[sig[1]] if not within else
                                                 'only full hosts within %g mm: %s' % (limits[sig[1]], ', '.join(
                                                     '%s at %s mm' % (hid, lg._g(d) if hasattr(lg, '_g') else d) for d, hid, _ in within)))
    return 'the signals cannot all ride together'


def consolidate(ctx, out, site_by):
    """Point 2: only when every link has a place."""
    if any(not r['placed'] for r in live(out)):
        return {'run': False, 'why': 'NOT RUN: %d link(s) without a place (scope point 2 runs only when every link has a '
                                     'place)' % sum(1 for r in live(out) if not r['placed'])}
    limits = limits_of(ctx.gopts)
    before = [r['id'] for r in live(out)]
    order = sorted([r for r in live(out) if r['placed'] and r['circuits'] == 8], key=lambda r: (r['signals'], r['id']))
    start = {r['id']: r['signals'] for r in order}
    disp_before = displaced_set(out)
    log = []
    origin = {}
    for h in live(out):
        for p in h['positions']:
            if p.get('rider_from'):
                origin[(p['site'], p['net'])] = p['rider_from']
    for r in order:
        hosts = [h for h in live(out) if h['placed'] and h['id'] != r['id']]
        state = {h['id']: link_signals(h) for h in hosts}
        res = ride(ctx, r, link_signals(r), hosts, state, site_by, limits)
        log.append({'link': r['id'], 'signals': start[r['id']], 'signals_when_tried': r['signals'], 'dissolved': bool(res)})
        if res:
            apply_ride(ctx, out, r, res[0], res[1], origin, 'dissolved (consolidation)')
            r['placed_before_consolidation'] = True
            r['placed'] = False
    after = [r['id'] for r in live(out)]
    freed = sorted(disp_before - displaced_set(out))
    n = sum(1 for x in log if x['dissolved'])
    per = {}
    for b, ref in freed:
        per[b] = per.get(b, 0) + 1
    return {'run': True, 'links_before': len(before), 'links_after': len(after), 'pass': log,
            'order_rule': 'the order is fixed at the start of the pass by the signals each link then carries; a link '
                          'tried later carries any riders it received earlier in the pass',
            'dissolved': [x['link'] for x in log if x['dissolved']],
            'freed': {'slots': n, 'connectors': 2 * n, 'latches': 2 * n, 'displaced_footprints': len(freed),
                      'displaced_footprints_per_board': dict(sorted(per.items()))},
            'freed_footprints': ['%s %s' % x for x in freed]}


def displaced_set(out):
    return {(r['front_board'] if k == 'front B' else 'K', ref) for r in live(out) if r['placed']
            for k, v in r['displaced'].items() for ref in v}


# ---------------------------------------------------------------- re-placement search (point 3)

def module_of_q(ref):
    m = re.match(r'Q(\d+)$', ref)
    if not m:
        return None
    return {21: 'F1', 22: 'F2', 23: 'F3'}.get(int(m.group(1)) // 100)


def _area(r):
    return (r[2] - r[0]) * (r[3] - r[1]) if r else 0.0


def replacement_scope(ctx, inp, out):
    """(board, ref) of every displaced footprint of the final record on K, the front boards and the adapters, and the
    part_moves of the active fixings; with the reason of each."""
    why = {}
    for r in live(out):
        if not r['placed']:
            continue
        for k, v in r['displaced'].items():
            board = r['front_board'] if k == 'front B' else 'K'
            for ref in v:
                why.setdefault((board, ref), set()).add('latch neighbour' if k == 'K B (latch)' else
                                                       'under a slot' if 'slot' in k else 'under a field')
    fx = inp['fixing_list']
    for f in fx['fixings']:
        if not f.get('active'):
            continue
        for m in f.get('part_moves', []):
            if m['board'] in SCOPE_BOARDS:
                why.setdefault((m['board'], m['ref']), set()).add('part move of %s' % f['id'])
    return {k: sorted(v) for k, v in why.items()}


def ds97_key(fp, board, ics, ledger_sym):
    ref = fp['ref']
    sym = ledger_sym.get(ref)
    area = _area(fp['courtyard'] or fp_bbox(fp))
    if (board == 'K' and sym in SENSITIVE_FUNCTION) or module_of_q(ref):
        tier = 0
    elif ref in ics or ref.startswith('U'):
        tier = 1
    else:
        tier = 2
    return (tier, -round(area, 6), ref, board)


def fp_bbox(fp):
    ps = [p['bbox'] for p in fp['pads']]
    return [min(p[0] for p in ps), min(p[1] for p in ps), max(p[2] for p in ps), max(p[3] for p in ps)] if ps else None


def turn(rect, origin):
    """The rectangle turned 90 degrees about the footprint origin."""
    ox, oy = origin
    xs = [ox - (rect[3] - oy), ox - (rect[1] - oy)]
    ys = [oy + (rect[0] - ox), oy + (rect[2] - ox)]
    return [r4(min(xs)), r4(min(ys)), r4(max(xs)), r4(max(ys))]


def shift(rect, dx, dy):
    return [rect[0] + dx, rect[1] + dy, rect[2] + dx, rect[3] + dy]


class Field:
    """Obstacles of the re-placement search per board face, cumulative."""

    def __init__(self, ctx, inp, out, moving):
        model = ctx.model
        self.model = model
        om = inp['ci']['parameters']['obstacle_model']
        self.gap = om['own_face_courtyard_growth_mm']
        self.pad_gap = om['opposite_face_through_hole_pad_growth_mm']
        self.margin = model.margin
        self.latch = val(ctx.opts['latch_access_margin_mm'])
        self.idx = {}
        for b in SCOPE_BOARDS:
            obs = sg.Obstacles(inp['ci']['boards'][b], om, drop=frozenset(model.dropped.get(b, ())))
            for face in 'FB':
                ix = sg.RectIndex()
                for rect, (ref, kind) in obs.index[face].items:
                    if (b, ref) in moving:
                        continue
                    ix.add(rect, ('fp', rect, '%s %s' % (kind, ref)))
                for rect, payload in model.forb[(b, face)].items:
                    if payload[0] == 'circle' or not payload[2].startswith(('panel hardware', 'hole')):
                        ix.add(rect, payload)
                self.idx[(b, face)] = ix
        self.links = {}
        for r in live(out):
            if not r['placed']:
                continue
            g = r['geometry']
            f = r['front_board']
            for key, face, rect, what in ((f, 'B', g['front_connector'], 'front field'), (f, 'B', g['front_tail'], 'front tail'),
                                          (f, 'B', g['slot'], 'slot'), ('K', 'B', g['K_connector'], 'K field'),
                                          ('K', 'B', g['K_tail'], 'K tail'), ('K', 'B', g['slot'], 'slot'),
                                          ('K', 'B', sg.grow(g['K_connector'], self.latch), 'latch margin'),
                                          ('K', 'F', g['slot'], 'slot')):
                self.links.setdefault((key, face), sg.RectIndex()).add(rect, '%s of %s' % (what, r['id']))

    def blocked(self, board, face, cy, pads_other):
        if not self.model.inside(board, cy, self.margin):
            return 'outline'
        for rect, payload in self.idx[(board, face)].near(cy):
            if payload[0] == 'circle':
                x, y, rad = payload[1]
                if sg.circle_rect_depth(x, y, rad, cy) > 1e-9:
                    return payload[2]
            elif sg.inter(cy, rect):
                return payload[2]
        g = sg.grow(cy, self.gap)
        lk = self.links.get((board, face))
        if lk:
            for rect, label in lk.near(g):
                if sg.inter(g, rect):
                    return label
        other = 'B' if face == 'F' else 'F'
        for p in pads_other:
            for rect, payload in self.idx[(board, other)].near(p):
                if payload[0] == 'circle':
                    x, y, rad = payload[1]
                    if sg.circle_rect_depth(x, y, rad, p) > 1e-9:
                        return payload[2]
                elif sg.inter(p, rect):
                    return payload[2]
        return None

    def add(self, board, face, cy, pads_other, ref):
        g = [r4(v) for v in sg.grow(cy, self.gap)]
        self.idx[(board, face)].add(g, ('fp', g, 're-placed %s' % ref))
        other = 'B' if face == 'F' else 'F'
        for p in pads_other:
            gp = [r4(v) for v in sg.grow(p, self.pad_gap)]
            self.idx[(board, other)].add(gp, ('fp', gp, 're-placed pad %s' % ref))


def ring_offsets(step, dirs, max_mm):
    out = [(0.0, 0.0, 0.0)]
    n = int(round(max_mm / step))
    for i in range(1, n + 1):
        r = i * step
        for k in range(dirs):
            a = 2 * math.pi * k / dirs
            out.append((r4(r), r4(r * math.cos(a)), r4(r * math.sin(a))))
    return out


def steps_for(board, ref, tht, opts, start3):
    steps = val(opts['steps'])
    out = []
    for s in steps:
        if start3 and s['step'] < 3:
            continue
        if s['step'] == 2 and (board != 'K' or tht):
            continue
        out.append(s)
    return out


def replace_all(ctx, inp, out):
    """Point 3: the cumulative re-placement search in the DS-97 order."""
    opts = ctx.gopts['replacement']
    pat = val(opts['search_pattern'])
    ledger = inp['rail_ledger']['physical_ic_packages']
    ledger_sym = {x['ref']: x['symbol'] for x in ledger}
    ics = set(ledger_sym)
    scope = replacement_scope(ctx, inp, out)
    fps = {(b, f['ref']): f for b in SCOPE_BOARDS for f in inp['ci']['boards'][b]}
    missing = sorted(k for k in scope if k not in fps)
    if missing:
        raise ValueError('displaced footprints not on their boards: %s' % missing[:5])
    field = Field(ctx, inp, out, set(scope))
    start3 = set(val(opts['start_at_step_3']))
    ctx.model.memo_for('re-placement')
    order = sorted(scope, key=lambda k: ds97_key(fps[k], k[0], ics, ledger_sym))
    rings = {}
    rows = []
    for board, ref in order:
        fp = fps[(board, ref)]
        cy0 = fp['courtyard'] or fp_bbox(fp)
        tht = [p['bbox'] for p in fp['pads'] if p['type'] in ('thru_hole', 'np_thru_hole')]
        face0 = fp['side']
        found = None
        for turned in (False, True):
            cy = turn(cy0, fp['origin']) if turned else cy0
            pads = [turn(p, fp['origin']) for p in tht] if turned else tht
            for st in steps_for(board, ref, bool(tht), opts, ref in start3):
                key = st['max_mm']
                if key not in rings:
                    rings[key] = ring_offsets(pat['step_mm'], pat['directions'], key)
                faces = [face0] if st['faces'] == 'own' else ['B' if face0 == 'F' else 'F'] if st['faces'].startswith('other') \
                    else [face0] + ([] if tht else ['B' if face0 == 'F' else 'F'])
                for dist, dx, dy in rings[key]:
                    for face in faces:
                        c = [r4(v) for v in shift(cy, dx, dy)]
                        ps = [[r4(v) for v in shift(p, dx, dy)] for p in pads]
                        if not field.blocked(board, face, c, ps):
                            found = (st['step'], face, dx, dy, dist, c, ps, turned)
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break
        row = {'board': board, 'ref': ref, 'package': fp['lib'], 'face': face0, 'why': scope[(board, ref)],
               'old': [r4(v) for v in fp['origin']], 'courtyard': [r4(v) for v in cy0]}
        if found:
            stp, face, dx, dy, dist, c, ps, turned = found
            field.add(board, face, c, ps, ref)
            row.update({'new': [r4(fp['origin'][0] + dx), r4(fp['origin'][1] + dy)], 'new_face': face,
                        'shift_mm': [dx, dy], 'moved_mm': dist, 'step': stp, 'turned': turned, 'new_courtyard': c})
        else:
            row.update({'new': None, 'new_face': None, 'shift_mm': None, 'moved_mm': None, 'step': 'no position',
                        'turned': False})
        rows.append(row)
    ctx.model.drop_memo('re-placement')
    return rows


def displaced_k_ic_packages(inp, rows):
    """One object per displaced IC package of K (the refs of physical_ic_packages that sit on K), at the reference point
    x_mm/y_mm of the floorplan (the keys are fixed by the scope of a8 part 2 point 3)."""
    sym = {x['ref']: x['symbol'] for x in inp['rail_ledger']['physical_ic_packages']}
    fp = {(p['board'], p['ref']): p for p in inp['floorplan']['placements']}
    out = []
    for r in rows:
        if r['board'] != 'K' or r['ref'] not in sym:
            continue
        p = fp[('K', r['ref'])]
        side = {'F': 'F.Cu', 'B': 'B.Cu'}
        old = {'xy': [r4(p['x_mm']), r4(p['y_mm'])], 'side': p['side']}
        if r['new'] is None:
            new = None
        else:
            new = {'xy': [r4(p['x_mm'] + r['shift_mm'][0]), r4(p['y_mm'] + r['shift_mm'][1])], 'side': side[r['new_face']]}
        out.append({'ref': r['ref'], 'symbol': sym[r['ref']], 'old': old, 'new': new, 'moved_mm': r['moved_mm'],
                    'step': r['step']})
    return out


def ds97_summary(inp, rows):
    sym = {x['ref']: x['symbol'] for x in inp['rail_ledger']['physical_ic_packages']}
    sens = {}
    for r in rows:
        fn = SENSITIVE_FUNCTION.get(sym.get(r['ref'])) if r['board'] == 'K' else None
        if fn is None and module_of_q(r['ref']):
            fn = 'transistors of module %s' % module_of_q(r['ref'])
        if fn:
            sens.setdefault(fn, []).append(_move(r))
    trim = [_move(r) for r in rows if re.match(r'RVO?\d', r['ref'])]
    return {'sensitive_by_function': dict(sorted(sens.items())),
            'displaced_counts': {s: sum(1 for r in rows if sym.get(r['ref']) == s) for s in COUNTED_SYMBOLS},
            'trimmers': trim,
            'sensitive_without_a_position': sorted(m['ref'] for v in sens.values() for m in v if m['step'] == 'no position')}


def _move(r):
    return {'board': r['board'], 'ref': r['ref'], 'package': r['package'], 'old': r['old'], 'face': r['face'],
            'new': r['new'], 'new_face': r['new_face'], 'moved_mm': r['moved_mm'], 'step': r['step'], 'turned': r['turned']}


def replacement_totals(rows):
    per = {}
    for r in rows:
        e = per.setdefault('%s %s' % (r['board'], r['face']), {'displaced': 0, 'step 1': 0, 'step 2': 0, 'step 3': 0,
                                                              'no position': 0, 'turned': 0})
        e['displaced'] += 1
        e['no position' if r['step'] == 'no position' else 'step %d' % r['step']] += 1
        e['turned'] += 1 if r['turned'] else 0
    cls = {}
    for r in rows:
        k = cls_of(r['ref'])
        e = cls.setdefault(k, {'displaced': 0, 'step 1': 0, 'step 2': 0, 'step 3': 0, 'no position': 0})
        e['displaced'] += 1
        e['no position' if r['step'] == 'no position' else 'step %d' % r['step']] += 1
    return {'per_board_face': dict(sorted(per.items())), 'per_class': dict(sorted(cls.items())),
            'without_a_position': [{'board': r['board'], 'ref': r['ref'], 'package': r['package']} for r in rows
                                   if r['step'] == 'no position']}


def cls_of(ref):
    p = re.match(r'[A-Z]+', ref).group(0)
    return 'ICs' if p == 'U' else 'resistors' if p == 'R' else 'capacitors' if p == 'C' else 'other'


def run(ctx, inp, out, site_by):
    load_part2_inputs(inp)
    w = ways_out(ctx, out, site_by)
    final = lg.placed_index(live(out))
    for r in live(out):
        if not r['placed']:
            ctx.model.memo_for(r['id'])
            r['nearest_misses'], r['most_frequent_blockers'] = lg.misses_and_blockers(ctx, final, r)
            r['why_no_place'] = lg.why_no_place(ctx, final, r)
            ctx.model.drop_memo(r['id'])
    c = consolidate(ctx, out, site_by)
    ctx.model.memos.clear()
    ctx.model.memo_for(None)
    lg._latch(ctx, live(out))
    rows = replace_all(ctx, inp, out)
    return {'ways_out': w, 'consolidation': c, 'replacement': rows}


# ---------------------------------------------------------------- checker (point 6)

def check_riders(ctx, doc, site_by):
    """Rider legality: each rider sits on a placed link of the same joint and front board, within its class distance of
    the host's connector centres, recorded identically on both links and in the host's order; the host's allocation is
    checked with every other link by links_gate.check (every signal on exactly one link, DS-62/77/78)."""
    errs = []
    limits = limits_of(ctx.gopts)
    by = {r['id']: r for r in doc['links']}
    for r in doc['links']:
        for x in r.get('riders_out', []):
            h = by.get(x['host'])
            tag = '%s: rider %s of %s' % (r['id'], x['net'], x['site'])
            # a host may itself dissolve later in the consolidation; the signal then rides on from it
            moved_on = h is not None and h.get('gone') and any(
                y['site'] == x['site'] and y['net'] == x['net'] for y in h.get('riders_out', []))
            if h is None or not (h['placed'] or moved_on):
                errs.append('%s goes to %s, which is not a placed link' % (tag, x['host']))
                continue
            if h['joint'] != r['joint'] or h['front_board'] != r['front_board']:
                errs.append('%s goes to %s of another joint' % (tag, h['id']))
            if not any(y['site'] == x['site'] and y['net'] == x['net'] and y['from'] == r['id']
                       for y in h.get('riders_in', [])):
                errs.append('%s is not recorded on its host %s' % (tag, h['id']))
            d = rider_distance(site_by[x['site']], h)
            if abs(d - x['distance_mm']) > 1e-6:
                errs.append('%s: recorded distance %s mm differs from the recomputed %s mm' % (tag, x['distance_mm'], d))
            if d > limits[x['class']] + 1e-9:
                errs.append('%s: %s mm from %s, beyond the %s distance of %g mm' % (tag, d, h['id'], x['class'],
                                                                                   limits[x['class']]))
            if not h.get('gone'):
                if not any(p['kind'] == 'signal' and p['site'] == x['site'] and p['net'] == x['net'] and
                           p.get('rider_from') for p in h['positions']):
                    errs.append('%s is not a marked rider position of %s' % (tag, h['id']))
        for y in r.get('riders_in', []):
            src = by.get(y['from'])
            if src is None or not any(x['site'] == y['site'] and x['net'] == y['net'] and x['host'] == r['id']
                                      for x in src.get('riders_out', [])):
                errs.append('%s: rider %s of %s is not sent by %s' % (r['id'], y['net'], y['site'], y['from']))
    return errs


def check_ways(ctx, doc, site_by):
    errs = []
    by = {r['id']: r for r in doc['links']}
    limits = limits_of(ctx.gopts)
    for lid, w in doc['ways_out'].get('per_link', {}).items():
        r = by[lid]
        way = w['way']
        if way == 1 and r.get('gone') != 'riders (way 1)':
            errs.append('%s: way 1 recorded but the link is not carried by riders' % lid)
        if way in (2, 4) and not r['placed']:
            errs.append('%s: way %d recorded without a place' % (lid, way))
        if way == 2:
            why = class_accept(r, site_by, limits)(r['geometry'])
            if why:
                errs.append('%s: way 2 place with %s' % (lid, why))
        if way == 5 and (r['placed'] or r.get('gone')):
            errs.append('%s: way 5 recorded but the link has a place or riders' % lid)
    n4 = sum(1 for w in doc['ways_out'].get('per_link', {}).values() if w['way'] == 4)
    if n4 > val(ctx.gopts['ways_out']['way_4_max_links']):
        errs.append('%d links take way 4, above the limit' % n4)
    for r in doc['links']:
        if 'field_growth_against_panel_pads_mm' in r and (doc['ways_out']['per_link'].get(r['id']) or {}).get('way') != 4:
            errs.append('%s: a reduced field growth outside way 4' % r['id'])
    return errs


def check_consolidation(ctx, doc):
    """The pass runs exactly when every link has a place; its order is fewest signals first, ties by id, over the
    8-circuit links; a dissolved link is gone with every one of its signals on riders."""
    errs = []
    c = doc['consolidation']
    un = [r for r in doc['links'] if not r.get('gone') and not r['placed']]
    if bool(c['run']) == bool(un):
        errs.append('consolidation %s although %d link(s) have no place' % ('ran' if c['run'] else 'did not run', len(un)))
    if not c['run']:
        if any(r.get('gone') == 'dissolved (consolidation)' for r in doc['links']):
            errs.append('a link dissolved by a consolidation that did not run')
        return errs
    keys = [(x['signals'], x['link']) for x in c['pass']]
    if keys != sorted(keys):
        errs.append('consolidation pass not in the order fewest signals first, ties by id')
    by = {r['id']: r for r in doc['links']}
    for x in c['pass']:
        r = by[x['link']]
        if r['circuits'] != 8:
            errs.append('%s: consolidation over a link of %d circuits' % (r['id'], r['circuits']))
        if x['dissolved'] != (r.get('gone') == 'dissolved (consolidation)'):
            errs.append('%s: consolidation verdict differs from the link record' % r['id'])
    return errs


def check_replacement(ctx, inp, doc):
    """Every re-placement: the scope is the displaced footprints of the final record and the part moves, the order is
    that of DS-97, each shift lies within its step and face rule, and no new courtyard meets an obstacle, a link or an
    earlier re-placed footprint (each pair is screened once, the later against the earlier)."""
    load_part2_inputs(inp)
    errs = []
    rows = doc['replacement']['footprints']
    links_ = doc['links']
    scope = replacement_scope(ctx, inp, links_)
    if sorted(scope) != sorted((r['board'], r['ref']) for r in rows):
        errs.append('re-placement scope differs from the displaced footprints of the record')
        return errs
    ledger_sym = {x['ref']: x['symbol'] for x in inp['rail_ledger']['physical_ic_packages']}
    fps = {(b, f['ref']): f for b in SCOPE_BOARDS for f in inp['ci']['boards'][b]}
    keys = [ds97_key(fps[(r['board'], r['ref'])], r['board'], set(ledger_sym), ledger_sym) for r in rows]
    if keys != sorted(keys):
        errs.append('re-placement not in the DS-97 order')
    opts = ctx.gopts['replacement']
    steps = {s['step']: s for s in val(opts['steps'])}
    start3 = set(val(opts['start_at_step_3']))
    field = Field(ctx, inp, links_, set(scope))
    ctx.model.memo_for(None)
    for r in rows:
        tag = '%s %s' % (r['board'], r['ref'])
        if r['step'] == 'no position':
            if r['new'] is not None:
                errs.append('%s: no position but a new place' % tag)
            continue
        fp = fps[(r['board'], r['ref'])]
        st = steps.get(r['step'])
        if st is None:
            errs.append('%s: unknown step %s' % (tag, r['step']))
            continue
        dx, dy = r['shift_mm']
        dist = math.hypot(dx, dy)
        if dist > st['max_mm'] + 1e-3 or abs(dist - r['moved_mm']) > 1e-3:
            errs.append('%s: shift %.4f mm outside step %d (%g mm) or differs from the recorded %s mm'
                        % (tag, dist, r['step'], st['max_mm'], r['moved_mm']))
        if r['ref'] in start3 and r['step'] < 3:
            errs.append('%s: starts at step 3 but is placed in step %d' % (tag, r['step']))
        tht = [p['bbox'] for p in fp['pads'] if p['type'] in ('thru_hole', 'np_thru_hole')]
        other = r['new_face'] != r['face']
        if (st['faces'] == 'own' and other) or (st['faces'].startswith('other') and (not other or r['board'] != 'K')) \
                or (other and tht):
            errs.append('%s: face %s not allowed in step %d' % (tag, r['new_face'], r['step']))
        cy0 = fp['courtyard'] or fp_bbox(fp)
        cy = turn(cy0, fp['origin']) if r['turned'] else cy0
        pads = [turn(p, fp['origin']) for p in tht] if r['turned'] else tht
        c = [r4(v) for v in shift(cy, dx, dy)]
        ps = [[r4(v) for v in shift(p, dx, dy)] for p in pads]
        hit = field.blocked(r['board'], r['new_face'], c, ps)
        if hit:
            errs.append('%s: new place meets %s' % (tag, hit))
        field.add(r['board'], r['new_face'], c, ps, r['ref'])
    if displaced_k_ic_packages(inp, rows) != doc['displaced_k_ic_packages']:
        errs.append('displaced_k_ic_packages differs from the re-placement rows')
    return errs


def check_part2(ctx, inp, doc, site_by):
    if 'ways_out' not in doc:
        return ['no record of part 2']
    return check_riders(ctx, doc, site_by) + check_ways(ctx, doc, site_by) + check_consolidation(ctx, doc) + \
        check_replacement(ctx, inp, doc)
