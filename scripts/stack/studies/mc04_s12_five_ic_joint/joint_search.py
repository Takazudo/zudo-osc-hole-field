#!/usr/bin/env python3
"""MC04-S12 (DS-151): one joint link search for U1415, U5110, U8409, U5209 and U5210 (study only, one run).

    python joint_search.py --run              # the driver: arm 0, pilot, stages 1 to 4, outputs (stages as children)
    python joint_search.py --check            # verification without a search re-run (see README)
    python joint_search.py --verify-scene N   # rows-only replay, A1 to A12 and digest of candidates/scene-N.json
    python joint_search.py --rebuild          # a full re-run (a separate admitted run)

Brief: circuit/orchestration/campaigns/osc-stack-20261114/mc04-s12-five-ic-joint-search-brief-20261127.md (Revision 2).
Inputs are read from the snapshot 6e5716e7; writes go only to this directory. Every scene is a candidate at most:
CANDIDATE SCENE, STUDY ONLY, NOT ADOPTED, UNVALIDATED DRAFT.
"""
from __future__ import annotations
import argparse
import copy
import heapq
import itertools
import json
import math
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s12  # noqa: E402
from s12 import lg, p2, sg, sm  # noqa: E402

PY = sys.executable
OUTDIR = Path(os.environ['S12_DEV_OUT']) if os.environ.get('S12_DEV_OUT') else HERE  # development dry runs only
CK = OUTDIR / 'checkpoints'
CAND = OUTDIR / 'candidates'
CENSUS = OUTDIR / 'census.json'
RESULT = OUTDIR / 'result.json'
BRIEF = 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s12-five-ic-joint-search-brief-20261127.md'
BRIEF_SHA = '1ecf7da618924bf1a21b825ad1ce682ffa057b66cc950b0285f110e9e2069a2a'
CEIL = {'arm0': 45 * 60, 'pilot': 10 * 60, 'stage1': 45 * 60, 'stage2': 45 * 60, 'West': 20 * 60, 'South': 10 * 60,
        'East': 75 * 60, 'stage4': 60 * 60}
EAST_SLICES = ((('U8409', 'U5210', 'U5209'), 25), (('U5209', 'U5210'), 15), (('U8409', 'U5210'), 7),
               (('U8409', 'U5209'), 7), (('U8409',), 7), (('U5210',), 7), (('U5209',), 7))
POOL_CAP = 60
REPLAY_CAP = 400
LEGAL_CAP = 100000
CLEAN_CAP = 3
JOINT_CAP = 27
OVERLAY_CAP = 6
FULL_CAP = 8
EXTRA_HOLD_CAP = 3
EXPECT_P5_N = ['R5249', 'R5256', 'R8221', 'R8331', 'R8356']
EXPECT_P5_S = ['R5253']
EXPECT_P6_SHIFTED = ['C8405', 'R5148', 'R5253', 'R8431']
EXPECT_P6_REMOVED = ['R5226', 'R5228', 'R5247', 'R5250', 'R5251', 'R5260', 'R5263', 'U5207', 'U5209', 'U5210']
EXPECT_P6_FACE = ['R5251', 'R5260', 'R5263', 'U5207']
S10_MOVED = ('P-K-P-L13.01.01.01', 'P-K-P-L13.01.01.02', 'P-K-P-L13.01.02.01')


def now():
    return time.time()


def maxrss_mib():
    return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=False, ensure_ascii=False) + '\n')


def read_json(path):
    return json.loads(path.read_text())


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, file=sys.stderr, flush=True)


# ---------------------------------------------------------------- arm 0

def returned_moves(w):
    """The 32580f77 geometries of the three moved S10 links, as scene moves."""
    doc = s12.gjson(s12.RETURNED, s12.GATE)
    L = {r['id']: r for r in doc['links']}
    return {lid: {'geometry': L[lid]['geometry'], 'slot_centre': L[lid]['slot_centre'], 'direction': L[lid]['direction']}
            for lid in S10_MOVED}, doc


def arm0(w, skip_p2=False):
    t0 = now()
    res, stop = {}, []

    def control(name, ok, detail):
        res[name] = {'pass': bool(ok), 'detail': detail}
        log(name, 'PASS' if ok else 'FAIL')
        if not ok:
            stop.append(name)

    pins, bad = s12.input_pins()
    tables, tbad = s12.base_tables(w)
    control('P1', not bad and not tbad, {'pins': pins, 'tables': tables, 'differences': bad + tbad})
    if skip_p2:
        res['P2'] = {'pass': None, 'detail': 'NOT RUN in this mode (--check)'}
    else:
        t = now()
        p = subprocess.run([PY, str(s12.S9 / 'slot_moves_a2.py'), '--check'], capture_output=True, text=True, cwd=str(s12.ROOT))
        a2sha = s12.sha_file(s12.S9 / 'result-a2.json')
        control('P2', p.returncode == 0 and 'current' in p.stdout and a2sha.startswith(s12.RESULT_A2_SHA[:8]),
                {'returncode': p.returncode, 'stdout_tail': p.stdout[-400:], 'stderr_tail': p.stderr[-400:],
                 'result_a2_sha256': a2sha, 'wall_s': round(now() - t, 1)})
    t = now()
    rows = w.rows_only(w.base_out)
    control('P3', len(rows) == 452 and json.dumps(rows) == json.dumps(w.base_rows_list),
            {'rows': len(rows), 'byte_equal': json.dumps(rows) == json.dumps(w.base_rows_list), 'wall_s': round(now() - t, 1)})
    moves, rdoc = returned_moves(w)
    out = w.scene_links(moves)
    L = {r['id']: r for r in out}
    R = {r['id']: r for r in rdoc['links']}
    disp_eq = {lid: L[lid]['displaced'] == R[lid]['displaced'] for lid in S10_MOVED}
    t = now()
    rrows = w.rows_only(out)
    rrec = rdoc['replacement']['footprints']
    control('P4', all(disp_eq.values()) and json.dumps(rrows) == json.dumps(rrec),
            {'displaced_equal': disp_eq, 'rows_byte_equal': json.dumps(rrows) == json.dumps(rrec), 'wall_s': round(now() - t, 1)})
    n, s_ = set(), set()
    for lid in S10_MOVED:
        bad5, _ = w.t1(lid, moves[lid]['geometry'])
        for ref, cl in bad5:
            (n if cl == 'N' else s_).add(ref)
    p5 = {'class_N': sorted(n), 'class_S': sorted(s_)}
    if sorted(n) != EXPECT_P5_N:
        control('P5', False, p5)
    else:
        p5['class_S_matches'] = sorted(s_) == EXPECT_P5_S
        control('P5', True, p5)
    ovl = s12.gjson(s12.RETURNED, 'scripts/stack/studies/mc04_s10_l13/overlay.json')
    j = s12.judge(w, moves, rrows, overlay_blocks=ovl['blocks'])
    pr = j['rows']['protected']
    newp = sorted(x.split(' ')[1] for x in pr['new'])
    shp = sorted(x.split(' ')[1] for x in pr['shifted'])
    rem = sorted(x.split(' ')[1] for x in pr['returned'])
    face = sorted(r for r in rem if w.base_rows[('K', r)]['new_face'] not in (None, w.s.fps[('K', r)]['side']))
    cls = {r: ('open IC placed' if r in s12.FIVE else 'return to paper') for r in rem}
    ovm = sorted(x.split(' ')[1] for x in j['protected_effective']['overlay_moved'])
    p6 = {'new_protected_rows': newp, 'shifted_protected_rows': shp, 'removed_protected_rows': rem, 'removed_classes': cls,
          'removed_with_face_change': face, 'overlay_moved_protected': ovm,
          'effective_movements': len(j['effective_movements']), 'face_changes': len(j['face_changes'])}
    control('P6', newp == EXPECT_P5_N and shp == EXPECT_P6_SHIFTED and ovm == ['R4238'] and rem == EXPECT_P6_REMOVED
            and face == EXPECT_P6_FACE and len(j['effective_movements']) == 56 and len(j['face_changes']) == 16, p6)
    base_loc = s12.locality_table(w, *s12.base_effective(w))
    pick = lambda tab, pred: [(x['entry'], x['figure'], x['scene'], x['verdict']) for x in tab['figures'] if pred(x)]  # noqa: E731
    u5113 = pick(base_loc, lambda x: 'U5113' in x['entry'] and x['figure'] == 'distance_mm')
    e5 = pick(base_loc, lambda x: '/E5/' in x['figure'] and 'added_run' in x['figure'])
    ret_loc = j['locality']
    flagged = sorted({(x['figure'], x['scene']) for x in ret_loc['above_limit']}, key=str)
    ok7 = (any(abs(v[2] - 84.77) < 1e-9 for v in u5113)
           and any('/E5/READY' in v[1] and abs(v[2] - 22.39) < 1e-9 for v in e5)
           and any('/E5/HOLD_N' in v[1] and abs(v[2] - 39.81) < 1e-9 for v in e5)
           and any('/E5/HOLD_N' in f and abs(v - 65.25) < 1e-9 for f, v in flagged if isinstance(v, (int, float)))
           and any('/E5/READY' in f and abs(v - 30.64) < 1e-9 for f, v in flagged if isinstance(v, (int, float)))
           and not base_loc['above_limit']
           and sorted({e.split(' ')[1] for e, _ in base_loc['inherited_excess']}) == ['U4417', 'U4526', 'U4646', 'U5112', 'U5113'])
    control('P7', ok7, {'inherited_excess_entries': sorted({e.split(' ')[1] for e, _ in base_loc['inherited_excess']}),
                        'base_U5113': u5113, 'base_E5': e5, 'base_inherited_excess': base_loc['inherited_excess'],
                        'base_above_limit': base_loc['above_limit'], 'returned_above_limit': flagged})
    res['_pending_full'] = True
    pc = s12.protected_counts(w)
    control('P10', pc['total'] == 1734 and pc['by_board'] == {'JL': 287, 'JR': 265, 'K': 1182} and
            sum(1 for b, _ in w.protected if b == 'P') == 0 and pc['with_base_row'] == 131 and
            pc['positionless_base_rows'] == sorted(['U1318', 'U4647', 'U1415', 'U5110', 'U5209', 'U5210', 'U8409']), pc)
    t = now()
    allstay = s12.judge(w, {}, w.base_rows_list)
    rc = allstay['rows']['counts']
    control('P11', not allstay['fails'] and allstay['rows']['claimed'] == [] and rc == {'removed': 0, 'new': 0, 'shifted': 0}
            and not allstay['locality']['above_limit'],
            {'fails': allstay['fails'], 'claimed': allstay['rows']['claimed'], 'row_changes': rc,
             'locality_above_limit': allstay['locality']['above_limit'],
             'inherited_excess': allstay['locality']['inherited_excess'], 'wall_s': round(now() - t, 1)})
    res.pop('_pending_full')
    return res, stop, round(now() - t0, 1)


def full_replay_child(holds_json, out_json):
    """Child process: one full gate replay; writes its doc and the working-tree files it read."""
    holds = None if holds_json == '-' else read_json(Path(holds_json))
    t = now()
    doc, reads = s12.full_replay(holds)
    write_json(Path(out_json), {'doc': doc, 'working_tree_reads': reads, 'wall_s': round(now() - t, 1), 'maxrss_mib': maxrss_mib()})


def run_full(holds, tag):
    hp = CK / ('holds-%s.json' % tag)
    op = Path(os.environ.get('S12_SCRATCH', '/tmp')) / ('s12-full-%s.json' % tag)
    if holds is not None:
        write_json(hp, holds)
    p = subprocess.run([PY, __file__, '--full-replay', str(hp) if holds is not None else '-', str(op)], capture_output=True,
                       text=True, timeout=1800)
    if p.returncode:
        raise RuntimeError('full replay %s failed: %s' % (tag, p.stderr[-2000:]))
    d = read_json(op)
    op.unlink()
    return d


def arm0_full(w, res, stop):
    base_doc = s12.gjson(s12.BASE, s12.GATE)
    t = now()
    d = run_full(None, 'P8')
    doc = d['doc']
    diffs = s12.compare_links(doc['links'], base_doc['links'])
    rows_eq = json.dumps(doc['replacement']) == json.dumps(base_doc['replacement']['footprints'])
    ways = doc['ways_out'] == base_doc['ways_out']
    cons = doc['consolidation'] == base_doc['consolidation']
    ok = not diffs and rows_eq and ways and cons and not doc['hold_errors']
    res['P8'] = {'pass': ok, 'detail': {'link_differences': diffs, 'rows_equal': rows_eq, 'ways_out_equal': ways,
                                         'consolidation_equal': cons, 'hold_errors': doc['hold_errors'],
                                         'working_tree_reads': d['working_tree_reads'], 'wall_s': d['wall_s'],
                                         'child_maxrss_mib': d['maxrss_mib']}}
    log('P8', 'PASS' if ok else 'FAIL', round(now() - t))
    if not ok:
        stop.append('P8')
    rg = s12.gjson(s12.RETURNED, s12.GOPTS)['slot_holds']['value']
    rdoc = s12.gjson(s12.RETURNED, s12.GATE)
    t = now()
    d = run_full(rg, 'P9')
    doc = d['doc']
    L = {r['id']: r for r in doc['links']}
    R = {r['id']: r for r in rdoc['links']}
    held = {lid: (L[lid]['slot_centre'], L[lid]['direction']) == (R[lid]['slot_centre'], R[lid]['direction']) for lid in S10_MOVED}
    rows_eq = json.dumps(doc['replacement']) == json.dumps(rdoc['replacement']['footprints'])
    diffs = s12.compare_links(doc['links'], rdoc['links'])
    detail = {'held_slots_reached': held, 'rows_equal_32580f77': rows_eq, 'link_differences_vs_32580f77': diffs,
              'hold_errors': doc['hold_errors'], 'working_tree_reads': d['working_tree_reads'], 'wall_s': d['wall_s'],
              'child_maxrss_mib': d['maxrss_mib']}
    slot_ok = all(held.values())
    cls_ok = True
    if not rows_eq:
        w_rows = doc['replacement']
        f, info = s12.check_rows(w, w_rows)
        rf, rinfo = s12.check_rows(w, rdoc['replacement']['footprints'])
        cls_ok = info['protected'] == rinfo['protected']
        detail['protected_classes_equal'] = cls_ok
    ok = slot_ok and cls_ok and not doc['hold_errors']
    res['P9'] = {'pass': ok, 'detail': detail, 'note': None if rows_eq else 'rows differ from the 32580f77 record (reported)'}
    log('P9', 'PASS' if ok else 'FAIL', round(now() - t))
    if not ok:
        stop.append('P9')


# ---------------------------------------------------------------- stage 1 (and the pilot)

def census_runs():
    runs = [(lid, None) for lid in s12.SEARCHED]
    runs.append(('P-K-P-L07', 26))
    return runs


def stage1(w, deadline):
    out = {'links': {}, 'accepted': {}, 'complete': True}
    for lid, size in census_runs():
        tag = lid if size is None else '%s@%d' % (lid, size)
        out['links'][tag] = {}
        acc_all = []
        for g in s12.GRIDS:
            t = now()
            c, acc = s12.census(w, lid, g, size, deadline=deadline)
            c['wall_s'] = round(now() - t, 2)
            out['links'][tag]['%g' % g] = c
            acc_all += acc
            log('census', tag, g, sum(c['legal_rule1'].values()), sum(c['after_rule']['6'].values()), c['wall_s'])
            if not c['complete']:
                out['complete'] = False
        tot = {'legal_rule1': 0, 'after_rule_6': 0}
        for c in out['links'][tag].values():
            tot['legal_rule1'] += sum(c['legal_rule1'].values())
            tot['after_rule_6'] += sum(c['after_rule']['6'].values())
        out['links'][tag]['totals'] = tot
        out['accepted'][tag] = acc_all
    return out


def l07_26_evidence(w):
    r = w.byid['P-K-P-L07']
    rec = w.rec('P-K-P-L07', 26)
    sig = [(n, c, m) for m in r['members'] for n, c in zip(w.site_by[m]['signals'], w.site_by[m]['classes'])]
    need = lg.circuits_needed([c for _, c, _ in sig], w.ctx.rule)
    errs = lg.allocation_errors(rec['positions'], w.ctx.rule, w.ctx.adapter_order)
    sizes = [z for z in w.ctx.gopts['sizes'] if z['circuits'] == 26]
    flex = json.loads((w.s.root / 'design/stack/connectors/flex-links.json').read_text())
    cited = 'C202113' in json.dumps(flex) and 'C32128' in json.dumps(flex)
    return {'signals': len(sig), 'circuits_needed': need, 'fits_26': need is not None and need <= 26 and not errs,
            'allocation_errors': errs, 'size_entry': sizes, 'connector': rec['connector'], 'cable': rec['cable'],
            'cable_length_mm': rec['cable_length_mm'], 'flex_links_cites_C202113_and_C32128': cited,
            'also_used_by': 'P-K-P-L03.01 (FH12-N26, C32128 60 mm)',
            'gate_a_check_1': 'the 26-way variant closes nothing in Gate A check 1'}


# ---------------------------------------------------------------- stage 2

def stay_entry(w, lid):
    r = w.byid[lid]
    return {'stay': True, 'cost': r['cost'], 'key': [r['cost']], 'geometry': r['geometry'], 'slot_centre': r['slot_centre'],
            'direction': r['direction'], 'dist': r['slot_distance_from_centre_mm'], 'ring': s12.ring_of(r['slot_distance_from_centre_mm']),
            'size': r['circuits'], 'screen': {'clean': True, 'protected_changes': []}, 'tails': [], 'anchored_covered': []}


def build_pool(acc):
    best = {}
    for c in acc:
        sp = tuple(c['spot'])
        if sp not in best or c['key'] < best[sp]['key']:
            best[sp] = c
    entries = sorted(best.values(), key=lambda c: (c['cost'], c['key']))
    return entries[:POOL_CAP], len(entries) > POOL_CAP, len(entries)


def stage2(w, st1, deadline):
    pools, caps, screened, unscreened = {}, [], 0, 0
    for tag, acc in st1['accepted'].items():
        lid = tag.split('@')[0]
        size = int(tag.split('@')[1]) if '@' in tag else None
        entries, capped, nspots = build_pool(acc)
        if capped:
            caps.append('%s: %d spots, pool cut at %d' % (tag, nspots, POOL_CAP))
        for e in entries:
            e['stay'] = False
            if now() > deadline:
                e['screen'] = None
                unscreened += 1
                continue
            m = {lid: {'geometry': e['geometry'], 'slot_centre': e['slot_centre'], 'direction': e['direction'], 'size': size}}
            rows = w.rows_only(w.scene_links(m))
            f, info = s12.check_rows(w, rows)
            e['screen'] = {'clean': not f.get('A2'), 'protected_changes': f.get('A2', [])[:20]}
            screened += 1
        pools[tag] = [stay_entry(w, lid)] + entries if size is None else entries
        log('pool', tag, nspots, len(entries))
    return {'pools': pools, 'caps': caps, 'screened': screened, 'unscreened_at_ceiling': unscreened}


# ---------------------------------------------------------------- stage 3

class Budget:
    def __init__(self, seconds):
        self.end = now() + seconds
        self.replays = 0
        self.legal = 0
        self.reason = None

    def out(self):
        if self.reason:
            return True
        if now() > self.end:
            self.reason = 'time slice'
        elif self.replays >= REPLAY_CAP:
            self.reason = '400 rows-only replays'
        elif self.legal >= LEGAL_CAP:
            self.reason = '100 000 legality calls'
        return self.reason is not None


def legal_entry(w, lid, e, chosen, later, size):
    """(moves entry or None, reason): the pool entry at its slot with fixed and earlier chosen links placed."""
    ctx = w.ctx
    rec = w.rec(lid, size)
    front, own = rec['front_board'], lg.rec_own(rec)
    placed = w.placed_index(chosen, skip=(lid,) + tuple(later))
    if e['stay']:
        why = ctx.evaluate(placed, front, rec['geometry'], own)
        if why:
            return None, 'stay illegal: %s' % why[0]
        return {'stay': True}, None
    z = w.size_of(rec)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    d = [k for k, v in lg.DIR_NAMES.items() if v == e['direction']][0]
    ctx.model.memo_for(None)
    why, c = lg.candidate(ctx, placed, front, z, own, e['slot_centre'][0], e['slot_centre'][1], d, e['dist'],
                          ctx.spare(front, z), True, gm)
    if why:
        return None, why[0]
    cost, geo, disp = c
    rule, reason, _ = w.check_rules(lid, geo, e['dist'], size)
    if rule is not None:
        return None, 'rule %d: %s' % (rule, reason)
    return {'geometry': geo, 'slot_centre': e['slot_centre'], 'direction': e['direction'], 'size': size, 'cost': cost,
            'dist': e['dist'], 'ring': e['ring'], 'grid_mm': e.get('grid_mm')}, None


def reverify(w, moves):
    ctx = w.ctx
    bad = []
    for lid, m in moves.items():
        if m.get('stay'):
            continue
        rec = w.rec(lid, m.get('size'))
        placed = w.placed_index(moves, skip=(lid,))
        why = ctx.evaluate(placed, rec['front_board'], m['geometry'], lg.rec_own(rec))
        if why:
            bad.append('%s: %s' % (lid, why[0]))
    return bad


def scene_rank(w, moves, info, tails_new):
    ring = sum(1 for m in moves.values() if not m.get('stay') and m['ring'] != '≤ 24 mm')
    cost = sum((w.byid[l]['cost'] if m.get('stay') else m['cost']) for l, m in moves.items())
    rows = info['counts']['new'] + info['counts']['shifted']
    slots = sorted((l, tuple(w.byid[l]['slot_centre'] if m.get('stay') else m['slot_centre'])) for l, m in moves.items())
    return (-len(info['claimed']), len(tails_new), ring, round(cost, 6), rows, slots)


def tails_of(w, moves):
    """Protected footprints under a tail of a moved searched link: all, and those newly under a tail."""
    allt, newt = [], []
    for lid, m in sorted(moves.items()):
        if m.get('stay'):
            continue
        for b, ref, what in w.tails(lid, m['geometry']):
            nets = sorted({n for n in w.s.pins.get(ref, {}).values() if n})
            item = {'link': lid, 'board': b, 'ref': ref, 'under': what, 'nets': nets}
            allt.append(item)
            if (b, ref) not in w.base_tail:
                newt.append(item)
    return allt, newt


def cluster_search(w, links, targets, pools, budget, size07=None):
    """Best-first enumeration over the pools in the fixed link order. Returns (clean scenes, log)."""
    need = s12.must_move(w, targets) & set(links)
    pl = []
    for lid in links:
        tag = '%s@%d' % (lid, size07) if (lid == 'P-K-P-L07' and size07) else lid
        es = [e for e in pools[tag] if not (e['stay'] and lid in need)]
        if size07 and lid == 'P-K-P-L07':
            pass
        es = sorted(es, key=lambda e: (not (e['screen'] or {}).get('clean', False), e['cost'], e['key']))
        pl.append((lid, es, size07 if lid == 'P-K-P-L07' else None))
    logd = {'targets': list(targets), 'must_move': sorted(need), 'pool_sizes': {lid: len(es) for lid, es, _ in pl},
            'replays': 0, 'legality_calls': 0, 'complete_scenes': 0, 'rejected_scenes': [], 'bound': None, 'illegal': {}}
    empty = [lid for lid, es, _ in pl if not es]
    if empty:
        logd['bound'] = 'none: no pool entry for %s (census zero after rules 1 to 6)' % ', '.join(empty)
        logd['exhausted'] = True
        return [], logd
    hmin = []
    for lid, es, _ in pl:
        hmin.append((min(int(not (e['screen'] or {}).get('clean', False)) for e in es), min(e['cost'] for e in es)))
    rest = [(sum(h[0] for h in hmin[i:]), sum(h[1] for h in hmin[i:])) for i in range(len(pl) + 1)]
    heap = [(rest[0][0], rest[0][1], 0, ())]
    seq = itertools.count()
    clean = []
    while heap:
        if budget.out():
            logd['bound'] = budget.reason
            break
        un, cost, _, choice = heapq.heappop(heap)
        depth = len(choice)
        chosen = {}
        for (lid, es, sz), (i, m) in zip(pl, choice):
            chosen[lid] = m
        if depth == len(pl):
            logd['complete_scenes'] += 1
            moves = {l: m for l, m in chosen.items()}
            bad = reverify(w, moves)
            if bad:
                logd['rejected_scenes'].append({'choice': [i for i, _ in choice], 'reverify': bad})
                continue
            budget.replays += 1
            logd['replays'] += 1
            rows = w.rows_only(w.scene_links(moves))
            fails, info = s12.check_rows(w, rows)
            for lid, m in moves.items():
                _, bad5 = s12.link_figures(w, lid, m)
                if bad5:
                    fails.setdefault('A5', []).extend(bad5)
            miss = [ic for ic in targets if ic not in info['claimed']]
            if fails or miss:
                logd['rejected_scenes'].append({'choice': [i for i, _ in choice], 'fails': {k: v[:6] for k, v in fails.items()},
                                                'targets_not_claimed': miss})
                continue
            allt, newt = tails_of(w, moves)
            clean.append({'moves': moves, 'rows_digest': s12.digest(rows), 'claimed': info['claimed'], 'row_info': info,
                          'tails_all': allt, 'tails_new': newt, 'rank': scene_rank(w, moves, info, newt)})
            if len(clean) >= CLEAN_CAP:
                logd['bound'] = 'three clean scenes'
                break
            continue
        lid, es, sz = pl[depth]
        later = [x[0] for x in pl[depth + 1:]]
        for i, e in enumerate(es):
            if budget.out():
                break
            budget.legal += 1
            logd['legality_calls'] += 1
            m, why = legal_entry(w, lid, e, chosen, later, sz)
            if m is None:
                k = '%s: %s' % (lid, why)
                logd['illegal'][k] = logd['illegal'].get(k, 0) + 1
                continue
            if not m.get('stay'):
                m['screen_clean'] = bool((e['screen'] or {}).get('clean'))
            un2 = sum(0 if (mm.get('stay') or mm.get('screen_clean')) else 1 for mm in list(chosen.values()) + [m]) + rest[depth + 1][0]
            c2 = sum((w.byid[l]['cost'] if mm.get('stay') else mm['cost']) for l, mm in list(chosen.items()) + [(lid, m)]) + rest[depth + 1][1]
            heapq.heappush(heap, (un2, round(c2, 6), next(seq), choice + ((i, m),)))
    else:
        logd['exhausted'] = True
    logd.setdefault('exhausted', False)
    logd['rejected_scenes'] = logd['rejected_scenes'][:40]
    return sorted(clean, key=lambda c: c['rank']), logd


def single_move_legality(w, census_acc, targets):
    """Diagnostic only (not a search): for each link the target ICs need moved, how many of its stage 1 candidates (the
    whole census, not the pool) are legal with every other live link at its record."""
    out = {}
    for lid in sorted(s12.must_move(w, targets)):
        acc = census_acc.get(lid, [])
        ok, why = 0, {}
        for e in acc:
            e = dict(e, stay=False)
            m, r = legal_entry(w, lid, e, {}, (), None)
            if m:
                ok += 1
            else:
                why[r] = why.get(r, 0) + 1
        out[lid] = {'census_candidates': len(acc), 'legal_with_all_others_at_record': ok,
                    'reasons': dict(sorted(why.items(), key=lambda x: -x[1])[:8])}
    return out


def stage3(w, pools, t_start, census_acc=None):
    out = {}
    # West
    t = now()
    b = Budget(CEIL['West'])
    west, lw = cluster_search(w, s12.CLUSTERS[0][1], ('U1415',), pools, b)
    out['West'] = {'40-way': {'scenes': west, 'log': lw, 'wall_s': round(now() - t, 1)}}
    if not west:
        lw26 = None
        if b.out():
            out['West']['26-way'] = {'not_searched': 'West ceiling reached'}
        else:
            w26, lw26 = cluster_search(w, s12.CLUSTERS[0][1], ('U1415',), pools, b, size07=26)
            for sc in w26:
                sc['label'] = ('ROWS-CLEAN 26-WAY SCENE; gate replay NOT RUN: slot holds carry no size selector; '
                               'NOT A CANDIDATE WITHOUT A GENERATOR CHANGE')
            out['West']['26-way'] = {'scenes': w26, 'log': lw26}
    out['West']['wall_s'] = round(now() - t, 1)
    # South
    t = now()
    b = Budget(CEIL['South'])
    south, ls = cluster_search(w, s12.CLUSTERS[1][1], ('U5110',), pools, b)
    out['South'] = {'scenes': south, 'log': ls, 'wall_s': round(now() - t, 1)}
    # East, in slices with carry-forward
    t = now()
    east_end = now() + CEIL['East']
    carry = 0.0
    sets = []
    placed = set()
    for targets, minutes in EAST_SLICES:
        if all(ic in placed for ic in targets):
            sets.append({'targets': list(targets), 'skipped': 'every IC of the set already has a clean scene'})
            continue
        if now() >= east_end:
            sets.append({'targets': list(targets), 'not_searched': 'East ceiling reached'})
            continue
        ts = now()
        b = Budget(min(minutes * 60 + carry, east_end - now()))
        sc, lg_ = cluster_search(w, s12.CLUSTERS[2][1], targets, pools, b)
        used = now() - ts
        carry = max(0.0, minutes * 60 + carry - used)
        sets.append({'targets': list(targets), 'scenes': sc, 'log': lg_, 'wall_s': round(used, 1)})
        if sc:
            placed |= set(targets)
    out['East'] = {'sets': sets, 'wall_s': round(now() - t, 1)}
    if census_acc is not None:
        out['diagnostic_single_move_legality'] = {ic: single_move_legality(w, census_acc, (ic,)) for ic in s12.FIVE}
    return out


# ---------------------------------------------------------------- stage 4

def cluster_options(st3):
    """Per cluster: its clean scenes (best first), then the all-stay option."""
    west = st3['West']['40-way']['scenes']
    south = st3['South']['scenes']
    east = []
    for s_ in st3['East']['sets']:
        east += s_.get('scenes', [])
    east = sorted(east, key=lambda c: c['rank'])
    return [west + [None], south + [None], east + [None]]


def stage4(w, st3, deadline):
    opts = cluster_options(st3)
    combos = []
    for cw, cs, ce in itertools.product(*opts):
        if cw is None and cs is None and ce is None:
            continue
        moves = {}
        for c in (cw, cs, ce):
            if c:
                moves.update(c['moves'])
        claimed = sum(len(c['claimed']) for c in (cw, cs, ce) if c)
        combos.append((-claimed, sum(c['rank'][1] for c in (cw, cs, ce) if c), moves, [c is not None for c in (cw, cs, ce)]))
    combos.sort(key=lambda x: (x[0], x[1], s12.canon({k: (v.get('slot_centre'), v.get('direction')) for k, v in x[2].items()})))
    capped = len(combos) > JOINT_CAP
    combos = combos[:JOINT_CAP]
    log_ = {'combinations': len(combos), 'combination_cap_reached': capped, 'kept': [], 'rejected': []}
    kept = []
    for neg, _, moves, which in combos:
        if now() > deadline:
            log_['bound'] = 'stage 4 ceiling'
            break
        bad = reverify(w, moves)
        if bad:
            log_['rejected'].append({'links': sorted(moves), 'reverify': bad})
            continue
        rows = w.rows_only(w.scene_links(moves))
        fails, info = s12.check_rows(w, rows)
        if fails:
            log_['rejected'].append({'links': sorted(moves), 'fails': {k: v[:6] for k, v in fails.items()}})
            continue
        kept.append((moves, rows, info))
        if len(kept) >= OVERLAY_CAP:
            break
    survivors = []
    full_used = 0
    for moves, rows, info in kept:
        if now() > deadline:
            log_['bound'] = 'stage 4 ceiling'
            break
        j = s12.judge(w, moves, rows)
        rec = {'moves': moves, 'rows': rows, 'judge': j}
        if j['fails']:
            rec['verdict'] = 'fails %s' % ', '.join(sorted(j['fails']))
            log_['rejected'].append({'links': sorted(moves), 'fails': {k: v[:6] for k, v in j['fails'].items()}})
            continue
        if full_used >= FULL_CAP:
            rec['A12'] = 'NOT RUN: full replay cap (8) reached'
            rec['verdict'] = 'rows clean, A12 NOT RUN (cap)'
            survivors.append(rec)
            continue
        a12, used = gate_check(w, moves, rows, FULL_CAP - full_used)
        full_used += used
        rec['A12'] = a12
        rec['verdict'] = 'candidate' if a12['pass'] else 'rows clean, gate replay differs'
        survivors.append(rec)
    log_['full_replays'] = full_used
    return survivors, log_


def gate_check(w, moves, rows, allowance):
    """A12: one full replay with one hold per searched link of the scene; up to three retries with a hold at the
    recorded pose of an unheld live link that moved. Returns (result, replays used)."""
    holds0 = [h for h in s12.gjson(s12.BASE, s12.GOPTS)['slot_holds']['value']]
    holds = holds0 + [s12.hold_entry(w, lid, moves.get(lid, {'stay': True}), 'S12 scene slot')
                      for lid in s12.SEARCHED]
    extra = []
    used = 0
    base_doc = s12.gjson(s12.BASE, s12.GATE)
    B = {r['id']: r for r in base_doc['links']}
    history = []
    while used < allowance:
        used += 1
        d = run_full(holds + extra, 'A12-%d' % int(now()))
        doc = d['doc']
        L = {r['id']: r for r in doc['links']}
        errs = list(doc['hold_errors'])
        at = {}
        for lid in s12.SEARCHED:
            m = moves.get(lid, {'stay': True})
            want = (B[lid]['slot_centre'], B[lid]['direction']) if m.get('stay') else (m['slot_centre'], m['direction'])
            at[lid] = L.get(lid) is not None and (L[lid]['slot_centre'], L[lid]['direction']) == (want[0], want[1])
        held_ids = {h['link'] for h in holds + extra}
        moved_unheld = sorted(i for i, r in B.items() if not r.get('gone') and i not in held_ids and
                              s12.compare_links([L[i]] if i in L else [], [r], ('centre', 'slot_centre', 'direction', 'geometry')))
        live = sum(1 for r in doc['links'] if not r.get('gone'))
        gone_eq = sorted(i for i, r in L.items() if r.get('gone')) == sorted(i for i, r in B.items() if r.get('gone'))
        rows_eq = json.dumps(doc['replacement']) == json.dumps(rows)
        ways_eq = doc['ways_out'] == base_doc['ways_out']
        hist = {'holds_extra': [h['link'] for h in extra], 'hold_errors': errs, 'at_scene_slot': at,
                'moved_unheld_links': moved_unheld, 'live': live, 'dissolved_equal': gone_eq, 'ways_out_equal': ways_eq,
                'rows_equal_rows_only': rows_eq, 'wall_s': d['wall_s'], 'working_tree_reads': d['working_tree_reads']}
        history.append(hist)
        if moved_unheld and len(extra) < EXTRA_HOLD_CAP and used < allowance:
            for i in moved_unheld[:EXTRA_HOLD_CAP - len(extra)]:
                extra.append(s12.hold_entry(w, i, {'stay': True}, 'S12 retry: unheld live link moved in the replay'))
            continue
        ok = not errs and all(at.values()) and not moved_unheld and live == 62 and gone_eq and ways_eq and rows_eq
        return {'pass': ok, 'attempts': history, 'extra_holds': extra}, used
    return {'pass': False, 'attempts': history, 'extra_holds': extra, 'note': 'full replay allowance exhausted'}, used


# ---------------------------------------------------------------- outputs

def scene_file(w, n, rec, label=None):
    moves = rec['moves']
    j = rec['judge']
    slots = []
    for lid in s12.SEARCHED:
        m = moves.get(lid, {'stay': True})
        h = s12.hold_entry(w, lid, m, 'S12 candidate slot')
        h.update({'stay': bool(m.get('stay')), 'size': (w.byid[lid]['circuits'] if m.get('stay') else w.rec(lid, m.get('size'))['circuits'])})
        slots.append(h)
    ra = w.base_rows
    rb = s12.rowmap(rec['rows'])
    ch = []
    for kind, keys in (('removed', j['rows']['removed']), ('new', j['rows']['new']), ('shifted', j['rows']['shifted'])):
        for k in keys:
            a, b = ra.get(k), rb.get(k)
            ch.append({'change': kind, 'board': k[0], 'ref': k[1], 'protected': k in w.protected,
                       'before': a and {'face': a['new_face'], 'origin': a['new'], 'moved_mm': a['moved_mm'], 'step': a['step']},
                       'after': b and {'face': b['new_face'], 'origin': b['new'], 'moved_mm': b['moved_mm'], 'step': b['step']}})
    allt, newt = tails_of(w, moves)
    anchored = []
    for lid, m in sorted(moves.items()):
        if not m.get('stay'):
            _, an = w.t1(lid, m['geometry'], m.get('size'))
            anchored += [{'link': lid, 'board': b, 'ref': r, 'anchored_by': list(a)} for b, r, a in an]
    workload = workload_change(w, moves)
    logic = [b for b in j['overlay_blocks'] if b.get('timing_nodes')]
    body = {'status': s12.STATUS, 'slots': slots, 'extra_recorded_pose_holds': (rec.get('A12') or {}).get('extra_holds', []),
            'link_figures': j['link_figures'], 'row_changes': ch, 'effective_movements': j['effective_movements'],
            'protected_ledger': {'returns_to_paper': j['rows']['protected']['returned'],
                                 'inherited_rows_kept': sorted('%s %s' % k for k in w.base_rows if k in w.protected and k in rb and rb[k] == w.base_rows[k]),
                                 'under_a_tail': allt, 'newly_under_a_tail': newt, 'anchored_covered_by_moved_link': anchored},
            'overlay_blocks': j['overlay_blocks'], 'locality': j['locality'], 'workload_vs_ds128': workload,
            'logic_blocks_with_timing_nodes': logic,
            'direction_changes': {l: f['direction_change'] for l, f in j['link_figures'].items() if f.get('direction_change')},
            'ring_24_35': sorted(l for l, f in j['link_figures'].items() if f.get('ring') == '24–35 mm'),
            'adoption_note': ('a link in the 24–35 mm ring cannot be adopted by holds alone: links_gate.check_placement_terms '
                              'rejects a recorded slot beyond 24 mm') if any(f.get('ring') == '24–35 mm' for f in j['link_figures'].values()) else None,
            'acceptance': {**j['passes'], 'A12': (rec.get('A12') or {}).get('pass')}, 'verdict': rec['verdict'],
            'label': label}
    body['digest'] = s12.digest({'slots': slots, 'rows': rec['rows']})
    return body


def workload_change(w, moves):
    out = {'links_moved': [], 'trim_leads': {}, 'hold_by_hand': [], 'lengthened_tails': [], 'connectors_by_size': {}}
    for lid, m in sorted(moves.items()):
        if m.get('stay'):
            continue
        r = w.byid[lid]
        geo = m['geometry']
        out['links_moved'].append(lid)
        out['trim_leads'][lid] = {'before': r['trim_leads'], 'after': lg.trim_list(w.model, r['front_board'], geo)}
        c = lg.cvalue(w.ctx.cmap, geo['K_connector'])
        if c is None or c > w.ctx.cmap.list_above:
            out['hold_by_hand'].append(lid)
        if geo['front_extension_mm'] > 0 or geo['K_extension_mm'] > 0:
            out['lengthened_tails'].append({'link': lid, 'front_extension_mm': geo['front_extension_mm'], 'K_extension_mm': geo['K_extension_mm']})
        z = w.rec(lid, m.get('size'))['size']
        out['connectors_by_size'][z] = out['connectors_by_size'].get(z, 0) + 1
    out['latches'] = 'unchanged in count: one latch per link; latch access NOT RUN (generator task)'
    return out


def fingerprint():
    def sh(cmd):
        try:
            return subprocess.run(cmd, capture_output=True, text=True, timeout=60).stdout.strip()
        except Exception as e:  # noqa: BLE001
            return 'unavailable: %s' % e
    mem = {l.split(':')[0]: l.split(':')[1].strip() for l in open('/proc/meminfo') if l.startswith(('MemTotal', 'MemAvailable', 'SwapTotal', 'SwapFree'))}
    cg = {}
    for f in ('memory.max', 'memory.current', 'cpu.max'):
        p = Path('/sys/fs/cgroup') / f
        cg[f] = p.read_text().strip() if p.exists() else 'not present (no cgroup v2 file)'
    import numpy, scipy, shapely
    return {'os': platform.platform(), 'arch': platform.machine(), 'nproc': os.cpu_count(),
            'cpu_affinity': sorted(os.sched_getaffinity(0)), 'cgroup': cg, 'meminfo': mem,
            'disk': sh(['df', '-h', str(s12.ROOT)]).splitlines()[-1:],
            'interpreter': sys.executable, 'python': platform.python_version(),
            'packages': {'numpy': numpy.__version__, 'scipy': scipy.__version__, 'shapely': shapely.__version__},
            'kicad_image': 'kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec',
            'kicad_image_present': sh(['docker', 'images', '--digests', '--format', '{{.Repository}}@{{.Digest}} {{.ID}}']),
            'kicad_cli_version': sh(['docker', 'run', '--rm', 'kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec',
                                     'kicad-cli', 'version']),
            'docker_daemon': sh(['docker', 'info', '--format', 'server {{.ServerVersion}}, driver {{.Driver}}, containers {{.Containers}} (running {{.ContainersRunning}})']),
            'processes': sh(['ps', '-eo', 'pid,rss,etime,comm', '--sort=-rss']).splitlines()[:15],
            'commit': s12.git('rev-parse', 'HEAD', text=True).strip(),
            'tree_clean_at_start': s12.git('status', '--porcelain', text=True).strip() == '',
            'brief_sha256': s12.sha_file(s12.ROOT / BRIEF)}


# ---------------------------------------------------------------- the driver

def child(stage):
    """One stage as a child process; reads earlier checkpoints, writes its own."""
    t0 = now()
    w = s12.World()
    setup = round(now() - t0, 1)
    if stage == 'arm0':
        res, stop, wall = arm0(w)
        if not stop:
            arm0_full(w, res, stop)
        write_json(CK / 'arm0.json', {'controls': res, 'stop': stop, 'wall_s': round(now() - t0, 1), 'setup_s': setup,
                                      'maxrss_mib': maxrss_mib()})
    elif stage == 'pilot':
        t = now()
        times = {}
        for g in (2.0, 0.5):
            tt = now()
            c, acc = s12.census(w, 'P-K-P-L13.01.01.01', g)
            times['%g' % g] = round(now() - tt, 2)
        per_link = times['2'] + times['0.5'] + 4 * times['0.5']
        proj = round(per_link * len(census_runs()), 1)
        write_json(CK / 'pilot.json', {'times_s': times, 'projection_rule': '(t2.0 + t0.5 + 4 x t0.5) x 9 census runs',
                                       'projected_stage1_s': proj, 'ceiling_s': CEIL['stage1'],
                                       'stop': proj > CEIL['stage1'], 'wall_s': round(now() - t, 1), 'maxrss_mib': maxrss_mib()})
    elif stage == 'stage1':
        t = now()
        st = stage1(w, now() + CEIL['stage1'] - setup)
        st['l07_26_way'] = l07_26_evidence(w)
        st['wall_s'] = round(now() - t, 1)
        st['maxrss_mib'] = maxrss_mib()
        write_json(CENSUS, st)
    elif stage == 'stage2':
        t = now()
        st1 = read_json(CENSUS)
        st = stage2(w, st1, now() + CEIL['stage2'] - setup)
        st['wall_s'] = round(now() - t, 1)
        st['maxrss_mib'] = maxrss_mib()
        write_json(CK / 'stage2.json', st)
    elif stage == 'stage3':
        t = now()
        pools = read_json(CK / 'stage2.json')['pools']
        st = stage3(w, pools, t, read_json(CENSUS)['accepted'])
        st['wall_s'] = round(now() - t, 1)
        st['maxrss_mib'] = maxrss_mib()
        write_json(CK / 'stage3.json', st)
    elif stage == 'stage4':
        t = now()
        st3 = read_json(CK / 'stage3.json')
        surv, lg4 = stage4(w, st3, now() + CEIL['stage4'] - setup)
        write_json(CK / 'stage4.json', {'survivors': surv, 'log': lg4, 'wall_s': round(now() - t, 1), 'maxrss_mib': maxrss_mib()})
    log('stage', stage, 'done', round(now() - t0, 1), 's', maxrss_mib(), 'MiB')


STAGES = ('arm0', 'pilot', 'stage1', 'stage2', 'stage3', 'stage4')
HARD = {'arm0': CEIL['arm0'] + 600, 'pilot': CEIL['pilot'], 'stage1': CEIL['stage1'] + 600, 'stage2': CEIL['stage2'] + 600,
        'stage3': CEIL['West'] + CEIL['South'] + CEIL['East'] + 600, 'stage4': CEIL['stage4'] + 600}


def drive(resume=False):
    CK.mkdir(exist_ok=True)
    done = []
    if resume:
        # a resume is allowed only from a finished stage with unchanged input pins (brief, Run bounds)
        runlog = read_json(CK / 'run.json')
        a0 = read_json(CK / 'arm0.json')
        pins, bad = s12.input_pins()
        if bad or pins != a0['controls']['P1']['detail']['pins']:
            raise SystemExit('resume refused: input pins changed: %s' % bad)
        done = [st for st in STAGES if st in runlog['stages'] and runlog['stages'][st]['returncode'] == 0]
        runlog.setdefault('resumes', []).append({
            'at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'finished_stages_kept': done,
            'reason': os.environ.get('S12_RESUME_REASON', 'interrupted'), 'input_pins_unchanged': True,
            'fingerprint': fingerprint()})
    else:
        runlog = {'fingerprint': fingerprint(), 'stages': {}, 'stop': None}
    write_json(CK / 'run.json', runlog)
    for st in STAGES:
        if st in done:
            continue
        t = now()
        log('start', st)
        p = subprocess.run([PY, __file__, '--stage', st], timeout=HARD[st])
        runlog['stages'][st] = {'returncode': p.returncode, 'wall_s': round(now() - t, 1)}
        write_json(CK / 'run.json', runlog)
        if p.returncode:
            runlog['stop'] = 'stage %s failed (returncode %d)' % (st, p.returncode)
            break
        if st == 'arm0' and read_json(CK / 'arm0.json')['stop']:
            runlog['stop'] = 'STOP 2: arm 0 controls failed: %s' % read_json(CK / 'arm0.json')['stop']
            break
        if st == 'pilot' and read_json(CK / 'pilot.json')['stop']:
            runlog['stop'] = 'STOP 4: the pilot projects stage 1 beyond its ceiling'
            break
    write_json(CK / 'run.json', runlog)
    log('driver end', runlog['stop'])
    finish()


def finish():
    """result.json and candidates/ from the checkpoints."""
    w = None
    runlog = read_json(CK / 'run.json')
    res = {'schema_version': 1, 'study': 'MC04-S12 (DS-151), study only', 'status': 'STUDY ONLY, NOTHING ADOPTED, UNVALIDATED DRAFTS',
           'brief': BRIEF, 'brief_sha256': BRIEF_SHA, 'snapshot': s12.BASE, 'generator': 'scripts/stack/studies/mc04_s12_five_ic_joint/joint_search.py',
           'fingerprint': runlog['fingerprint'], 'stages': runlog['stages'], 'stop': runlog['stop'],
           'resumes': runlog.get('resumes', [])}
    guards = {}
    for f in sorted((CK / 'guard').glob('*.json')) if (CK / 'guard').exists() else []:
        g = read_json(f)
        guards[f.stem] = {k: g[k] for k in ('command', 'returncode', 'wall_s', 'peak_tree_rss_mib', 'min_mem_available_mib',
                                             'peak_docker_container_mem_mib', 'watchdog_fired')}
    res['run_bounds'] = {'memory_measure': ('guard.py: RSS of the whole process tree sampled every 5 s against the 8 GiB '
                                            'budget, plus an abort when system MemAvailable drops below 7 GiB (15 GiB - 8 GiB), '
                                            'because an oracle container runs under dockerd outside the tree; docker stats '
                                            'sampled every 30 s for the container peak. No cgroup v2 memory files exist in '
                                            'this container, so no cgroup scope was used'),
                         'guarded_steps': guards}
    cks = {}
    for f in ('arm0.json', 'pilot.json', 'stage2.json', 'stage3.json', 'stage4.json'):
        if (CK / f).exists():
            cks['checkpoints/' + f] = s12.sha_file(CK / f)
    if CENSUS.exists():
        cks['census.json'] = s12.sha_file(CENSUS)
    res['checkpoint_sha256'] = cks
    if (CK / 'arm0.json').exists():
        a0 = read_json(CK / 'arm0.json')
        res['arm0'] = {k: v['pass'] for k, v in a0['controls'].items()}
    if runlog['stop'] is None:
        w = s12.World()
        res.update(summarise(w))
    write_json(RESULT, res)


def summarise(w):
    st1 = read_json(CENSUS)
    st2 = read_json(CK / 'stage2.json')
    st3 = read_json(CK / 'stage3.json')
    st4 = read_json(CK / 'stage4.json')
    census_summary = {tag: {g: {'legal_rule1': v['legal_rule1'], 'after_rule': v['after_rule'],
                                'rejected_for_class_S_alone': v['rejected_for_class_S_alone'], 't1_by_class': v['t1_by_class']}
                            for g, v in d.items() if g != 'totals'} | {'totals': d['totals']} for tag, d in st1['links'].items()}
    zero = sorted(tag for tag, d in st1['links'].items() if d['totals']['after_rule_6'] == 0)
    caps = list(st2['caps'])
    # candidates
    CAND.mkdir(exist_ok=True)
    for f in CAND.glob('scene-*.json'):
        f.unlink()
    surv = [x for x in st4['survivors'] if x['verdict'] == 'candidate']
    others = [x for x in st4['survivors'] if x['verdict'] != 'candidate']
    ranked = sorted(surv, key=lambda x: scene_rank_from(w, x))
    written = []
    for n, rec in enumerate(ranked[:3], 1):
        body = scene_file(w, n, rec)
        write_json(CAND / ('scene-%d.json' % n), body)
        written.append({'scene': n, 'digest': body['digest'], 'claimed': rec['judge']['rows']['claimed']})
    verdicts = ic_verdicts(w, st1, st3, st4, written)
    return {'census': census_summary, 'census_zero_links': zero, 'pool_caps': caps,
            'stage3': stage3_summary(st3), 'stage4': st4['log'],
            'diagnostic_single_move_legality': st3.get('diagnostic_single_move_legality'), 'rows_clean_not_candidates': [
                {'links': sorted(x['moves']), 'verdict': x['verdict'], 'A12': x.get('A12')} for x in others],
            'candidates': written, 'verdicts': verdicts, 'l07_26_way': st1.get('l07_26_way')}


def scene_rank_from(w, rec):
    info = rec['judge']['rows']
    _, newt = tails_of(w, rec['moves'])
    return scene_rank(w, rec['moves'], info, newt)


def stage3_summary(st3):
    def one(x):
        if not x or 'log' not in x:
            return x
        lg_ = dict(x['log'])
        lg_.pop('rejected_scenes', None)
        return {'clean_scenes': len(x.get('scenes', [])), 'log': lg_, 'wall_s': x.get('wall_s')}
    return {'West': {'40-way': one(st3['West']['40-way']), '26-way': one(st3['West'].get('26-way'))},
            'South': one(st3['South']), 'East': [dict(one(s_) or {}, targets=s_['targets'], **{k: s_[k] for k in ('skipped', 'not_searched') if k in s_})
                                                 for s_ in st3['East']['sets']]}


def ic_verdicts(w, st1, st3, st4, written):
    out = {}
    joint = written[0]['claimed'] if written else []
    partial = sorted({ic for x in written for ic in x['claimed']})
    nz = {tag.split('@')[0] for tag, d in st1['links'].items() if d['totals']['after_rule_6'] > 0}
    zero = {tag.split('@')[0] for tag in st1['links']} - nz
    bounds = {}
    for s_ in st3['East']['sets']:
        if 'not_searched' in s_:
            for ic in s_['targets']:
                bounds.setdefault(ic, set()).add('the East stage ceiling (set %s not searched)' % '+'.join(s_['targets']))
    if 'not_searched' in (st3['West'].get('26-way') or {}):
        bounds.setdefault('U1415', set()).add('the West stage ceiling (26-way not searched)')
    for x in [st3['West']['40-way'], st3['West'].get('26-way') or {}, st3['South']] + st3['East']['sets']:
        lg_ = x.get('log') or {}
        for ic in x.get('targets', lg_.get('targets', [])):
            if lg_.get('bound') and not lg_.get('exhausted'):
                bounds.setdefault(ic, set()).add(lg_['bound'])
    for ic in s12.FIVE:
        need = sorted(s12.must_move(w, (ic,)))
        if ic in joint:
            out[ic] = {'verdict': 'PLACED IN THE JOINT SCENE'}
        elif ic in partial:
            out[ic] = {'verdict': 'PLACED ONLY IN A PARTIAL SCENE'}
        elif any(l in zero for l in need):
            out[ic] = {'verdict': 'NO CANDIDATE ON THIS DOMAIN (EXHAUSTIVE)',
                       'reason': 'census zero after rules 1 to 6 on the 2.0, 0.5 and 0.25 mm grids within 35 mm for %s' %
                                 ', '.join(l for l in need if l in zero), 'links_needed': need}
        elif bounds.get(ic):
            out[ic] = {'verdict': 'NO SCENE FOUND (BOUNDED BY %s)' % ', '.join(sorted(bounds[ic])).upper(), 'links_needed': need}
        else:
            out[ic] = {'verdict': 'NO SCENE FOUND (BOUNDED BY THE POOL REDUCTION)', 'links_needed': need}
    return out


# ---------------------------------------------------------------- check / verify

def check():
    """Recompute the input pins, re-run P3, P4 and P11, re-run the rows-only replay and A1 to A11 for every written
    scene, and compare the scene and checkpoint digests recorded in result.json."""
    res = read_json(RESULT)
    errs = []
    pins, bad = s12.input_pins()
    errs += bad
    w = s12.World()
    r0, stop, _ = arm0(w, skip_p2=True)
    for k in ('P3', 'P4', 'P11'):
        if not r0[k]['pass']:
            errs.append('%s fails' % k)
    for path, want in res.get('checkpoint_sha256', {}).items():
        if s12.sha_file(OUTDIR / path) != want:
            errs.append('checkpoint %s digest differs' % path)
    for c in res.get('candidates', []):
        errs += verify_scene(w, c['scene'], full=False)
    if errs:
        raise SystemExit('CHECK FAILED: %s' % errs)
    print('result.json current: input pins, P3, P4, P11, %d scenes and %d checkpoint digests verified'
          % (len(res.get('candidates', [])), len(res.get('checkpoint_sha256', {}))))


def moves_from_scene(w, body):
    moves = {}
    # geometry is recomputed with the scene's links placed in the fixed cluster order
    for name, links, _ in s12.CLUSTERS:
        chosen = {}
        for lid in links:
            h = next(x for x in body['slots'] if x['link'] == lid)
            if h['stay']:
                chosen[lid] = {'stay': True}
                continue
            c = w.byid[lid]['centre']
            dist = math.hypot(h['slot_centre'][0] - c[0], h['slot_centre'][1] - c[1])
            e = {'stay': False, 'slot_centre': h['slot_centre'], 'direction': h['direction'], 'dist': dist,
                 'ring': s12.ring_of(dist)}
            later = links[links.index(lid) + 1:]
            m, why = legal_entry(w, lid, e, {k: v for k, v in chosen.items()}, later,
                                 None if h['size'] == w.byid[lid]['circuits'] else h['size'])
            if m is None:
                raise ValueError('scene slot of %s not legal: %s' % (lid, why))
            chosen[lid] = m
        moves.update({k: v for k, v in chosen.items() if not v.get('stay')})
    return moves


def verify_scene(w, n, full=True):
    errs = []
    body = read_json(CAND / ('scene-%d.json' % n))
    moves = moves_from_scene(w, body)
    rows = w.rows_only(w.scene_links(moves))
    slots = body['slots']
    if s12.digest({'slots': slots, 'rows': rows}) != body['digest']:
        errs.append('scene %d: digest differs' % n)
    j = s12.judge(w, moves, rows)
    if j['fails']:
        errs.append('scene %d fails %s' % (n, sorted(j['fails'])))
    if full:
        a12, _ = gate_check(w, moves, rows, 1 + s12_extra(body))
        if not a12['pass']:
            errs.append('scene %d: A12 fails' % n)
    return errs


def s12_extra(body):
    return min(len(body.get('extra_recorded_pose_holds', [])), EXTRA_HOLD_CAP)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', action='store_true')
    ap.add_argument('--rebuild', action='store_true')
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--verify-scene', type=int)
    ap.add_argument('--stage')
    ap.add_argument('--finish', action='store_true')
    ap.add_argument('--full-replay', nargs=2)
    a = ap.parse_args()
    if a.full_replay:
        full_replay_child(*a.full_replay)
    elif a.stage:
        child(a.stage)
    elif a.run or a.rebuild:
        drive()
    elif a.resume:
        drive(resume=True)
    elif a.finish:
        finish()
    elif a.check:
        check()
    elif a.verify_scene:
        w = s12.World()
        e = verify_scene(w, a.verify_scene)
        print('scene %d: %s' % (a.verify_scene, 'verified' if not e else e))
        sys.exit(1 if e else 0)


if __name__ == '__main__':
    main()
