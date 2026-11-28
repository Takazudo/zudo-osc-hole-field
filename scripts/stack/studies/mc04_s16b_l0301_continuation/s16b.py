"""MC04-S16b: one aimed continuation of the L03.01 re-plan study (S16).

Study only. Rows-level evidence on unvalidated drafts; nothing is adopted. Brief:
circuit/orchestration/campaigns/osc-stack-20261114/mc04-s16b-continuation-brief-20261128.md (Revision 2, DS-218).

This module imports S16's replan.py unchanged and calls only its library functions. It never calls replan's drive,
finish, stage1, stage1_one, stage2a, stage2b, search_one, stage3, stage4, stage4_one, block_pool, ck, bulk,
write_pins, write_manifest or a control function that writes a checkpoint, and it does not set S16_DEV_OUT
(Ruling Q5). Every path it writes is under this study directory, .circuit-cache/mc04-s16b/, the durable copy
/mnt/project-files/osc-s16b-cache/ or the system temporary directory.
"""
from __future__ import annotations

import copy
import hashlib
import heapq
import json
import math
import multiprocessing
import os
import re
import shutil
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
S16DIR = HERE.parent / 'mc04_s16_l0301_replan'
if 'S16_DEV_OUT' in os.environ:
    raise SystemExit('S16_DEV_OUT is set; S16b never sets it (Ruling Q5)')
if str(S16DIR) not in sys.path:
    sys.path.insert(0, str(S16DIR))
import replan as R  # noqa: E402

s12, lg = R.s12, R.lg
ROOT = R.ROOT
STATUS = R.STATUS
E1 = 'P-K-E1'
PARTS = ('C8443', 'R7213')  # Ruling Q2: the decoupler of U8413 and R_ISO of U7204 under S16's one passing slot family
TESTS_C = ('S1', 'S2', 'S3', 'R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7')
TESTS_A = R.TESTS_A
DASH = '–'

# ---------------------------------------------------------------- paths
DEV = bool(os.environ.get('S16B_DEV_OUT'))  # development dry runs write only to the scratchpad (before pins)
OUTDIR = Path(os.environ['S16B_DEV_OUT']) if DEV else HERE
CK = OUTDIR / 'checkpoints'
CAND = OUTDIR / 'candidates'
RESULT = OUTDIR / 'result.json'
PINS = OUTDIR / 'pins.json'
BULK = OUTDIR / 'cache' if DEV else ROOT / '.circuit-cache' / 'mc04-s16b'
BULK_MANIFEST = OUTDIR / 'bulk-manifest.json'
SCRATCH = '_scratch'
DURABLE = str(OUTDIR / 'durable') + '/' if DEV else '/mnt/project-files/osc-s16b-cache/'
STOPS = DURABLE + 'stops/'
CAMPAIGN = 'circuit/orchestration/campaigns/osc-stack-20261114/'
DECISIONS = ROOT / CAMPAIGN / 'decisions.md'
BRIEF = CAMPAIGN + 'mc04-s16b-continuation-brief-20261128.md'
BRIEF_SHA = '09e9a22855b141429abb55b842085bb4e9ce2daae696e3bb596579b38100e625'
S16_BRIEF = CAMPAIGN + 'mc04-s16-l0301-replan-brief-20261128.md'
S16_BULK = ROOT / '.circuit-cache' / 'mc04-s16'
S16_MANIFEST = S16DIR / 'bulk-manifest.json'
S16_DURABLE = '/mnt/project-files/osc-s16-cache/'
STUDY = 'scripts/stack/studies/mc04_s16b_l0301_continuation/'
PIN_FILES = (
    STUDY + 's16b.py',
    STUDY + 'k3_heartbeat.py',
    STUDY + 'test_s16b.py',
    'scripts/stack/studies/mc04_s16_l0301_replan/replan.py',
    'scripts/stack/studies/mc04_s16_l0301_replan/test_s16.py',
    'scripts/stack/studies/mc04_s16_l0301_replan/bulk-manifest.json',
    'scripts/stack/studies/mc04_s16_l0301_replan/result.json',
    'scripts/stack/studies/mc04_s12_five_ic_joint/s12.py',
    'scripts/stack/studies/mc04_s12_five_ic_joint/joint_search.py',
    'scripts/stack/studies/mc04_s15_no_growth_moves/guard15.py',
    S16_BRIEF,
    BRIEF,
    # the generator files and S8 to S10 modules are pinned through K1: S12's --check verifies its own input pins
)
PY = '/home/user/venv312/bin/python'
GUARD = ROOT / 'scripts/stack/studies/mc04_s15_no_growth_moves/guard15.py'

# ---------------------------------------------------------------- caps and ceilings (brief: Caps, Run bounds)
CLOCK_S = 4.5 * 3600
STEP_CEIL = {'arm0': 30 * 60, 'stage1': 55 * 60, 'stage2a': 10 * 60, 'stage2b': 90 * 60, 'stage3': 30 * 60,
             'stage4': 20 * 60, 'end': 20 * 60}
STAGE2B_START_BOUND_S = 80 * 60
POOL_SPOTS = 20
LEGAL_CAP = 20000
REPLAY_CAP_STRUCT = 12
REPLAY_CAP = 1800
OVERLAY_CAP = 10
STAGE4_PER_SCENE = 23
WORKERS = 3
RESUME_CAP = 3
CHUNK = 50
K11_N = 12


class Stop(Exception):
    pass


class OverlayCap(Exception):
    """The overlay cap refused a search. Never a TypeError: judge_replan turns a TypeError into an A8 failure."""


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, file=sys.stderr, flush=True)


def utc():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


now = time.time
write_json, read_json, sha_file, _jdefault = R.write_json, R.read_json, R.sha_file, R._jdefault


def ck(name):
    return CK / name


def bk(rel):
    return BULK / rel


def env_nobytecode():
    e = {k: v for k, v in os.environ.items() if not k.startswith('S16B_')}
    e['PYTHONDONTWRITEBYTECODE'] = '1'
    return e


def jclean(o):
    return json.loads(json.dumps(o, default=_jdefault))


# ================================================================ pins

def compute_pins(root=ROOT):
    return {p: sha_file(Path(root) / p) for p in PIN_FILES}


def write_pins():
    pins = compute_pins()
    if pins[BRIEF] != BRIEF_SHA:
        raise SystemExit('the brief hash differs: %s' % pins[BRIEF])
    write_json(PINS, {'written': utc(), 'files': pins, 'commit': s12.git('rev-parse', 'HEAD', text=True).strip()})
    return pins


def verify_pins(root=ROOT, pins_path=None):
    return R.verify_pins(root, pins_path or PINS)


# ================================================================ the STOP tripwire (Ruling Q5)

class StopPaths:
    def __init__(self, ck_dir=None, stops=None, decisions=None):
        self.ck = Path(ck_dir or CK)
        self.stops = str(stops or STOPS)
        self.decisions = Path(decisions or DECISIONS)

    @property
    def stop_json(self):
        return self.ck / 'stop.json'

    @property
    def run_json(self):
        return self.ck / 'run.json'

    @property
    def ruling(self):
        return self.ck / 'ruling.json'


def durable_stops(paths):
    d = Path(paths.stops)
    if not d.is_dir():
        return []
    return sorted(f.name for f in d.iterdir() if f.is_file())


def start_gate(paths=None):
    """Problems that keep the driver from starting (empty: it may start). The three records are checkpoints/stop.json,
    a `stop` in checkpoints/run.json and any file in the durable stops/ folder. A record is cleared only by
    checkpoints/ruling.json naming a decision row and the SHA-256 of the stop record, with a row of that ID in
    decisions.md whose text holds that hash. A tripwire and a record, not a lock: the driver cannot tell who wrote
    a file."""
    p = paths or StopPaths()
    hashes, found = set(), []
    if p.stop_json.exists():
        hashes.add(sha_file(p.stop_json))
        found.append('checkpoints/stop.json')
    if p.run_json.exists():
        r = read_json(p.run_json)
        if r.get('stop'):
            found.append('run.json stop: %s' % r['stop'])
            if r.get('stop_sha256'):
                hashes.add(r['stop_sha256'])
    for name in durable_stops(p):
        found.append('durable %s' % name)
        m = re.search(r'([0-9a-f]{64})', name)
        if m:
            hashes.add(m.group(1))
    if not found:
        return []
    if not p.ruling.exists():
        return ['a STOP record exists and no ruling.json clears it: %s' % '; '.join(found)]
    try:
        rl = read_json(p.ruling)
        row, h = rl['decision_row'], rl['stop_sha256']
    except Exception as e:  # noqa: BLE001
        return ['ruling.json is unreadable or incomplete (%s); records: %s' % (e, '; '.join(found))]
    if not hashes or hashes != {h}:
        return ['ruling.json hash %s does not match the stop records %s' % (h, sorted(hashes))]
    text = p.decisions.read_text() if p.decisions.exists() else ''
    rows = [ln for ln in text.splitlines() if re.match(r'^\|\s*%s\s*\|' % re.escape(row), ln)]
    if not rows:
        return ['decisions.md has no row %s' % row]
    if not any(h in ln for ln in rows):
        return ['decisions.md row %s does not hold the hash %s' % (row, h)]
    return []


def record_stop(reason, detail=None, paths=None, run_rec=None):
    """Write checkpoints/stop.json, set `stop` in run.json and copy stop.json to the durable stops/ folder under a
    name with its SHA-256; re-read the copy about 10 s later."""
    p = paths or StopPaths()
    doc = {'stop': reason, 'at': utc(), 'detail': detail, 'status': STATUS,
           'note': 'A STOP is final for the run (Ruling Q5, STOP 9). Only a decision row reopens it.'}
    write_json(p.stop_json, doc)
    h = sha_file(p.stop_json)
    rec = run_rec if run_rec is not None else (read_json(p.run_json) if p.run_json.exists() else {})
    rec['stop'] = reason
    rec['stop_sha256'] = h
    write_json(p.run_json, rec)
    d = Path(p.stops)
    d.mkdir(parents=True, exist_ok=True)
    dst = d / ('stop-%s.json' % h)
    shutil.copyfile(p.stop_json, dst)
    time.sleep(10)
    ok = sha_file(dst) == h
    rec['stop_durable'] = {'path': str(dst), 'reread_equal': ok, 'reread_at': utc()}
    write_json(p.run_json, rec)
    return h, ok


# ================================================================ the cumulative clock

class Clock:
    def __init__(self, path):
        self.path = path
        self.rec = read_json(path) if path.exists() else {'clock_s': 0.0, 'steps': {}, 'segments': [], 'resumes': [],
                                                          'executor_timed': {}}
        self.mark = now()
        self.step = None
        self.rec['segments'].append({'start': self.mark, 'pid': os.getpid()})

    def total(self):
        return self.rec['clock_s'] + sum(self.rec['executor_timed'].values())

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
        if self.total() > CLOCK_S:
            raise Stop('STOP 6: the cumulative 4.5-hour ceiling is spent (%.0f s)' % self.total())
        if st in STEP_CEIL and self.rec['steps'][st] > STEP_CEIL[st]:
            n = 5 if st in ('stage1', 'stage2a') else 6
            raise Stop('STOP %d: the %s ceiling (%d min) is passed (%.0f s)' % (n, st, STEP_CEIL[st] // 60,
                                                                                self.rec['steps'][st]))

    def begin(self, step):
        self.tick(self.step)
        self.step = step

    def used(self, step):
        return self.rec['steps'].get(step, 0.0)


# ================================================================ rules: R5 strict (Q1), R7 (Q2), pools (Q3)

def on_parts(w, front, geo):
    """{heading: [C8443 / R7213 listed under it]} from links_gate.displaced at the slot geometry."""
    d = lg.displaced(w.model, front, geo, w.ctx.latch)
    return {k: sorted(r for r in v if r in PARTS) for k, v in d.items() if any(r in PARTS for r in v)}


def is_e1(rec_or_sites):
    m = rec_or_sites['members'] if isinstance(rec_or_sites, dict) else rec_or_sites
    return E1 in m


def r7_reason(hit):
    return 'R7: %s' % '; '.join('%s under "%s"' % (', '.join(v), k) for k, v in sorted(hit.items()))


def pool_of16b(survivors, e1):
    """Ruling Q3: one survivor per spot; a spot gives its cheapest survivor clear of C8443 and R7213, or its cheapest
    survivor if none is clear; clear entries first, then (cost, key); at most 20 spots, the E1 block never cut."""
    best = {}
    for e in survivors:
        k = tuple(e['spot'])
        rank = (bool(e['on_parts']), e['cost'], e['key'])
        if k not in best or rank < (bool(best[k]['on_parts']), best[k]['cost'], best[k]['key']):
            best[k] = e
    out = sorted(best.values(), key=lambda e: (bool(e['on_parts']), e['cost'], e['key']))
    return out if e1 else out[:POOL_SPOTS]


def spots_of(survivors):
    return len({tuple(e['spot']) for e in survivors})


# ---------------------------------------------------------------- scene order (Ruling Q3), pure functions

def e1_offsets(order_e1_ids):
    """o for each structure: its index among the live structures that share its E1 block, in stage order."""
    seen = defaultdict(int)
    out = []
    for b in order_e1_ids:
        out.append(seen[b])
        seen[b] += 1
    return out


def spot_visits(cursor, k):
    """The spots one scene visits, in order: cursor, cursor + 1, ... mod k, at most k visits."""
    return [(cursor + v) % k for v in range(k)]


def simulate_scenes(o, k, completions, n):
    """N8: the (spot, completion index) of scenes 0..n-1 of one structure whose spot s has completions[s] completions."""
    cur, done, out = o, defaultdict(int), []
    for _ in range(n):
        got = None
        for v, s in enumerate(spot_visits(cur, k)):
            if done[s] < completions[s]:
                got = (s, done[s])
                done[s] += 1
                cur = cur + v + 1
                break
        if got is None:
            break
        out.append(got)
    return out


def classify_lite(fails):
    """Ruling Q4 on a judge_replan failure dict: 'pass', 'final' or 'undecided' (LITE UNDECIDED)."""
    flat = [(a, x) for a, v in fails.items() for x in v]
    notrun = [x for a, x in flat if a == 'A8' and x.startswith('overlay search not run')]
    other = [(a, x) for a, x in flat if not (a == 'A8' and x.startswith('overlay search not run'))]
    if not other:
        return 'pass'
    if not notrun:
        return 'final'
    if any(a == 'A8' and 'a decoupler row breaks the block rule while the IC row is unchanged' in x for a, x in other):
        return 'final'
    if any(a == 'A5' for a, _ in other):
        return 'final'
    return 'undecided'


# ---------------------------------------------------------------- the overlay counter (Ruling Q4)

class OverlayCounter:
    """Counts S8 block searches on disk; checked and written before each search; refuses the 11th."""

    def __init__(self, path, cap=OVERLAY_CAP):
        self.path = Path(path)
        self.cap = cap
        self.scene = None

    def read(self):
        return read_json(self.path) if self.path.exists() else {'cap': self.cap, 'count': 0, 'before_each': []}

    def wrap(self, fn):
        def counted(*a, **k):
            st = self.read()
            if st['count'] >= self.cap:
                raise OverlayCap('overlay cap of %d block searches reached (count %d)' % (self.cap, st['count']))
            st['before_each'].append({'count_before': st['count'], 'at': utc(), 'scene': self.scene,
                                      'ic': '%s %s' % (a[1], a[2]) if len(a) >= 3 else None})
            st['count'] += 1
            write_json(self.path, st)
            return fn(*a, **k)
        counted.wrapped = fn
        return counted


def judge_full_guarded(fn):
    """Runs one stage 3 full judgement; an OverlayCap makes it STAGE 3 INCOMPLETE (CAP)."""
    try:
        return {'status': 'judged', 'judge': fn()}
    except OverlayCap as e:
        return {'status': 'STAGE 3 INCOMPLETE (CAP)', 'reason': str(e)}


# ================================================================ vectors for the N cases

def vec(c, a):
    return (c + DASH * 10)[:10] + ' ' + (a + DASH * 6)[:6]


def case_vector16b(w, blocks, an=None, placed=None, class_s='strict'):
    """S1 S2 S3 R1 to R7 for blocks given at slots ([{'rec', 'slot_centre', 'direction'}]); no replay, so the
    acceptance tests are not evaluated. Returns (vector, reasons, per-block detail)."""
    out, why = '', {}
    for b in blocks:
        r = R.s1_class(b['rec']['sig_classes'])
        if r:
            why['S1'] = r
            return vec('F', ''), why, None
    out += 'P'
    for b in blocks:
        r = R.s2_order(b['rec'])
        if r:
            why['S2'] = r
            return vec(out + 'F', ''), why, None
    out += 'PP'  # S3: a block given at a slot has no ride set
    an = an or R.Anchors(w)
    placed = placed if placed is not None else R.placed_except(w)
    ctx = w.ctx
    res, detail = {}, []
    for b in blocks:
        rec = b['rec']
        z = lg.rec_size(ctx, rec)
        gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
        d = [k for k, v in lg.DIR_NAMES.items() if v == b['direction']][0]
        dist = math.hypot(b['slot_centre'][0] - rec['centre'][0], b['slot_centre'][1] - rec['centre'][1])
        ctx.model.memo_for(None)
        r, c = lg.candidate(ctx, placed, rec['front_board'], z, lg.rec_own(rec), b['slot_centre'][0],
                            b['slot_centre'][1], d, dist, ctx.spare(rec['front_board'], z), True, gm)
        if r:
            why['R1'] = r[0]
            return vec(out + 'F', ''), why, None
        res[rec['id']] = (c, dist)
    out += 'P'
    first = None
    for b in blocks:
        rec = b['rec']
        (cost, geo, _), dist = res[rec['id']]
        rule, reason, extra = R.Rules(w, rec, an, class_s).check(geo, dist)
        hit = on_parts(w, rec['front_board'], geo)
        dflt = R.Rules(w, rec, an, 'default').check(geo, dist)
        detail.append({'block': rec['id'], 'dist': dist, 'cost': cost, 'rule': rule, 'reason': reason, 'extra': extra,
                       'on_parts': hit, 'default_rule': dflt[0], 'default_extra': dflt[2]})
        if rule is None and is_e1(rec) and hit:
            rule, reason = 'R7', r7_reason(hit)
        if rule is not None and (first is None or int(rule[1]) < int(first[0][1])):
            first = (rule, reason)
    if first:
        n = int(first[0][1])
        why[first[0]] = first[1]
        return vec(out + 'P' * (n - 2) + 'F', ''), why, detail
    return vec(out + 'P' * 6, ''), why, detail


# ================================================================ workers (fork pool)

W = None
CTX = {}


def init_ctx():
    if 'placed' not in CTX:
        CTX['placed'] = R.placed_except(W)
        CTX['an'] = R.Anchors(W)


def census_one(sites):
    """Stage 1 for one site subset: census_block with the strict R5 on the three grids, distinct survivors, then R7
    for a block that holds P-K-E1. Every survivor carries the C8443 / R7213 headings of its slot."""
    w = W
    init_ctx()
    t0 = now()
    rec = R.block_record(w, list(sites))
    per, accs = {}, []
    for g in s12.GRIDS:
        c, a = R.census_block(w, rec, g, CTX['placed'], CTX['an'], 'strict', CTX.get('deadline'))
        per['%g' % g] = c
        accs.append(a)
    dist = R.distinct(accs)
    e1 = is_e1(rec)
    strict, r7_out = [], []
    for e in dist:
        hit = on_parts(w, rec['front_board'], e['geometry'])
        s = {k: e[k] for k in ('cost', 'key', 'direction', 'slot_centre', 'dist', 'ring', 'grid_mm', 'spot', 'class_s',
                               'anchored_covered')}
        s['on_parts'] = hit
        strict.append(s)
        if e1 and hit:
            r7_out.append(s)
    surv = [s for s in strict if not (e1 and s['on_parts'])]
    rings = ('≤ 24 mm', '24–35 mm')
    after = {t: sum(sum(c['after'][t].values()) for c in per.values()) for t in ('R2', 'R3', 'R4', 'R5', 'R6')}
    summ = {'block': rec['id'], 'sites': rec['members'], 'size': rec['circuits'], 'cable': rec['cable'],
            'cable_length_mm': rec['cable_length_mm'], 'centre': rec['centre'], 'holds_E1': e1,
            'complete': all(c['complete'] for c in per.values()),
            'legal_R1': sum(sum(c['legal_R1'].values()) for c in per.values()), 'after': after,
            'distinct_after_R6': len(strict), 'distinct_R7_rejected': len(r7_out),
            'distinct_survivors': len(surv), 'spots': spots_of(surv),
            'distinct_by_ring': {r: sum(1 for e in surv if e['ring'] == r) for r in rings},
            'on_parts_survivors': sum(1 for e in surv if e['on_parts']),
            'class_s_deferred': sum(c['class_s_deferred'] for c in per.values()),
            'cheapest_cost': min((e['cost'] for e in surv), default=None), 'wall_s': round(now() - t0, 1)}
    return summ, strict, surv, per


class LegalCap(Exception):
    pass


def struct_setup(t):
    w = W
    init_ctx()
    brs = [R.block_record(w, b) for b in t['blocks']]
    e1i = next(i for i, r in enumerate(brs) if is_e1(r))
    pools = [CTX['pools'][r['id']] for r in brs]
    rules = {r['id']: R.Rules(w, r, CTX['an'], 'strict') for r in brs}
    return brs, e1i, pools, rules


def legal16b(rec, e, chosen, rules, placed):
    """legal_block with the strict R5, then R7 for a block that holds P-K-E1."""
    m, why = R.legal_block(W, rec, e, chosen, [], CTX['an'], 'strict', rules=rules, placed=placed)
    if m is None:
        return None, why
    hit = on_parts(W, rec['front_board'], m['geometry'])
    if is_e1(rec) and hit:
        return None, r7_reason(hit)
    m['on_parts'] = hit
    return m, None


def nth_completion(t, spot, n, budget):
    """Completion n (0-based) of one E1 spot of a structure, in the key order of Ruling Q3: (blocks on C8443 or
    R7213, summed cost, pool indices in block order). Returns (completion or None, legality calls, illegal tally).
    A function of the structure, the spot and n only; raises LegalCap past `budget` calls."""
    brs, e1i, pools, rules = struct_setup(t)
    calls = [0]
    illegal = defaultdict(int)
    placed0 = CTX['placed']

    def check(rec, e, chosen):
        if calls[0] >= budget:
            raise LegalCap()
        calls[0] += 1
        extra = [dict(r, geometry=m['geometry']) for r, m in chosen]
        placed = placed0 if not extra else R.placed_except(W, extra=extra)
        m, why = legal16b(rec, e, chosen, rules[rec['id']], placed)
        if m is None:
            illegal['%s %s' % (rec['id'], why)] += 1
        return m

    m1 = check(brs[e1i], pools[e1i][spot], [])
    if m1 is None:
        return None, calls[0], dict(illegal)
    others = [i for i in range(len(brs)) if i != e1i]
    if not others:
        return ([(e1i, spot, m1)] if n == 0 else None), calls[0], dict(illegal)
    micro = [[int(round(e['cost'] * 1e6)) for e in pools[i]] for i in others]
    onmin = [min(1 if e['on_parts'] else 0 for e in pools[i]) for i in others]
    cmin = [min(c) for c in micro]
    a_rest = [sum(onmin[d:]) for d in range(len(others) + 1)]
    c_rest = [sum(cmin[d:]) for d in range(len(others) + 1)]
    heap = [(a_rest[0], c_rest[0], (), 0, 0, ())]
    found = 0
    while heap:
        a_lb, c_lb, idx, a_p, c_p, ch = heapq.heappop(heap)
        depth = len(idx)
        if depth == len(others):
            chosen = [(brs[e1i], m1)] + [(brs[others[d]], ch[d]) for d in range(depth)]
            order = sorted(chosen, key=lambda x: brs.index(x[0]))
            bad = R.reverify_blocks(W, order)
            if bad:
                illegal['reverify'] += 1
                continue
            if found == n:
                return [(e1i, spot, m1)] + [(others[d], idx[d], ch[d]) for d in range(depth)], calls[0], dict(illegal)
            found += 1
            continue
        bi = others[depth]
        chosen = [(brs[e1i], m1)] + [(brs[others[d]], ch[d]) for d in range(depth)]
        for j, e in enumerate(pools[bi]):
            m = check(brs[bi], e, chosen)
            if m is None:
                continue
            a2 = a_p + (1 if m['on_parts'] else 0)
            c2 = c_p + micro[depth][j]
            heapq.heappush(heap, (a2 + a_rest[depth + 1], c2 + c_rest[depth + 1], idx + (j,), a2, c2, ch + (m,)))
    return None, calls[0], dict(illegal)


def scene_record(t, comp, brs, e1i):
    blocks = []
    for bi, j, m in sorted(comp, key=lambda x: x[0]):
        blocks.append({'block': brs[bi]['id'], 'pool_index': j, 'slot_centre': m['slot_centre'],
                       'direction': m['direction'], 'dist': m['dist'], 'ring': m['ring'], 'grid_mm': m['grid_mm'],
                       'cost': m['cost'], 'class_s': m['class_s'], 'on_parts': m.get('on_parts') or {},
                       'geometry': m['geometry']})
    return blocks


def chosen_of(t, blocks):
    return [(R.block_record(W, b), {'geometry': x['geometry'], 'slot_centre': x['slot_centre'],
                                    'direction': x['direction'], 'ring': x['ring'], 'dist': x['dist'],
                                    'cost': x['cost']}) for b, x in zip(t['blocks'], blocks)]


def lite_figures(j):
    rule = [x for x in j.get('block_rule', []) if x['block_rule'] != 'holds']
    a9 = [x for x in j.get('placed_ic_blocks', []) if not x.get('ok', True)]
    return {'block_rule': rule, 'placed_ic_blocks_failing': a9}


def scene_one(task):
    """One scene of one structure in one round (Ruling Q3): visit E1 spots from the cursor, take the first completion
    not yet replayed, give it one rows-only replay judged by A0 to A4 and A6, and stage 3 lite on a passer."""
    t0 = now()
    t = task
    out = {'index': t['index'], 'id': t['id'], 'round': t['round']}
    if now() > t['deadline']:
        out['kind'] = 'time'
        return out
    brs, e1i, pools, rules = struct_setup(t)
    k = len(pools[e1i])
    done = {int(s): v for s, v in t['done'].items()}
    calls = {int(s): v for s, v in t['calls'].items()}
    exhausted = set(t['exhausted'])
    visited = []
    for v, s in enumerate(spot_visits(t['cursor'], k)):
        if s in exhausted:
            visited.append({'spot': s, 'result': 'exhausted earlier'})
            continue
        n = done.get(s, 0)
        budget = LEGAL_CAP - sum(c for sp, c in calls.items() if sp != s)
        try:
            comp, nc, ill = nth_completion(t, s, n, budget)
        except LegalCap:
            out.update({'kind': 'legal_cap', 'visited': visited, 'calls': calls})
            return out
        calls[s] = max(calls.get(s, 0), nc)
        if comp is None:
            exhausted.add(s)
            visited.append({'spot': s, 'result': 'no completion left', 'illegal': ill})
            continue
        if now() > t['deadline']:
            out.update({'kind': 'time', 'visited': visited, 'calls': calls})
            return out
        blocks = scene_record(t, comp, brs, e1i)
        chosen = chosen_of(t, blocks)
        t1 = now()
        rows = R.scene_rows(W, chosen, t['plan'])
        f, info = R.check_rows16(W, rows)
        rec = {'spot': s, 'completion': n, 'blocks': blocks, 'vector': R.acceptance_vector(f),
               'fails': {kk: vv[:4] for kk, vv in sorted(f.items())}, 'returned': info['protected']['returned'],
               'digest': s12.digest(rows), 'replay_s': round(now() - t1, 1),
               'non_e1_on_parts': sum(1 for b in blocks if b['on_parts'])}
        if not f:
            t2 = now()
            j = jclean(R.judge_replan(W, {}, rows, chosen, t['plan'], run_overlay_search=False))
            rec['lite'] = {'status': classify_lite(j['fails']), 'fails': j['fails'], 'passes': j['passes'],
                           'figures': lite_figures(j), 'judge_s': round(now() - t2, 1)}
        out.update({'kind': 'scene', 'scene': rec, 'cursor': t['cursor'] + v + 1, 'calls': calls,
                    'exhausted': sorted(exhausted), 'visited': visited, 'wall_s': round(now() - t0, 1)})
        return out
    out.update({'kind': 'none_left', 'calls': calls, 'exhausted': sorted(exhausted), 'visited': visited,
                'wall_s': round(now() - t0, 1)})
    return out


def stage4_one(task):
    """S16's stage 4 test (one S12 survivor of P-K-P-L13.01.01.01 with a scene's links in place), rewritten here
    because replan.stage4_one is not called."""
    w = W
    chosen = [(R.block_record(w, b['sites']), {'geometry': b['geometry'], 'slot_centre': b['slot_centre'],
                                               'direction': b['direction']}) for b in task['blocks']]
    e = task['entry']
    ctx = w.ctx
    rec = w.rec(R.L13)
    placed = R.placed_except(w, skip=(R.L03, R.L13), extra=[dict(r, geometry=m['geometry']) for r, m in chosen])
    z = lg.rec_size(ctx, rec)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    d = [k for k, v in lg.DIR_NAMES.items() if v == e['direction']][0]
    ctx.model.memo_for(None)
    why, c = lg.candidate(ctx, placed, rec['front_board'], z, lg.rec_own(rec), e['slot_centre'][0], e['slot_centre'][1],
                          d, e['dist'], ctx.spare(rec['front_board'], z), True, gm)
    out = {'index': task['index'], 'slot_centre': e['slot_centre'], 'direction': e['direction'], 'grid_mm': e['grid_mm']}
    if why:
        out.update({'legal': False, 'why': why[0]})
        return out
    rows = R.scene_rows(w, chosen, task['plan'], {R.L13: {'geometry': c[1], 'slot_centre': e['slot_centre'],
                                                          'direction': e['direction']}})
    f, info = R.check_rows16(w, rows)
    u = ('K', 'U5210') in s12.rowmap(rows)
    out.update({'legal': True, 'vector': R.acceptance_vector(f), 'U5210_has_row': u,
                'fails': {k: v[:4] for k, v in f.items()}, 'pass': not f and not u, 'digest': s12.digest(rows)})
    return out


def pool_ctx():
    return multiprocessing.get_context('fork')


# ================================================================ controls

def control_record(name, ok, detail, t0):
    rec = {'control': name, 'pass': bool(ok), 'detail': jclean(detail), 'wall_s': round(now() - t0, 1), 'at': utc()}
    write_json(ck('arm0/%s.json' % name), rec)
    log(name, 'PASS' if ok else 'FAIL', rec['wall_s'])
    return rec


def run_guarded(name, cmd, timeout=1800, cwd=None):
    gj = ck('guard/%s.json' % name)
    gj.parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run([PY, str(GUARD), str(gj), '--'] + cmd, capture_output=True, text=True, timeout=timeout,
                       cwd=str(cwd or ROOT), env=env_nobytecode())
    (ck('logs')).mkdir(parents=True, exist_ok=True)
    (ck('logs/%s.log' % name)).write_text(p.stdout + '\n--- stderr ---\n' + p.stderr)
    return p


def s16_state():
    """S16's cache and durable copy against S16's bulk-manifest.json (STOP 10), read-only."""
    present, bad = R.bulk_state(S16_BULK, S16_MANIFEST)
    man = read_json(S16_MANIFEST)['files']
    dur_bad = []
    for r, v in man.items():
        f = Path(S16_DURABLE + r)
        if not f.exists() or f.stat().st_size != v['bytes'] or sha_file(f) != v['sha256']:
            dur_bad.append(r)
    return {'cache_present': present, 'cache_problems': bad, 'durable_files_checked': len(man),
            'durable_problems': dur_bad[:20], 'durable_problem_count': len(dur_bad)}


def s16_git_clean():
    p = subprocess.run(['git', 'status', '--porcelain', '--', 'scripts/stack/studies/mc04_s16_l0301_replan/'],
                       capture_output=True, text=True, cwd=str(ROOT))
    return p.stdout.strip()


def k1_control(tag):
    """K1: S16 is intact. S16's --check with its cache present (rc 0, pins, C3, C3b, C8b, C9, mutation_cases, 219
    digests); S16's unit tests (34, M19 to M21); S12's joint_search.py --check; git status clean under S16's
    directory; S16's cache and durable copy equal S16's manifest."""
    st = s16_state()
    if not st['cache_present'] or st['cache_problems'] or st['durable_problem_count']:
        raise Stop('STOP 10: S16\'s cache or its durable copy is absent or differs from S16\'s manifest: %s' % st)
    a = run_guarded('k1-%s-s16-check' % tag, [PY, 'replan.py', '--check'], cwd=S16DIR)
    want = 'result.json current: pins verified, offline controls and the mutations re-run equal, 219 digests, ' \
           '3 stage 2b replays and 0 scenes re-run (189 cached files verified against the manifest)'
    a_ok = a.returncode == 0 and want in a.stdout and 'SOURCE CHANGED' not in a.stdout
    b = run_guarded('k1-%s-s16-unittest' % tag, [PY, '-m', 'unittest', 'test_s16'], cwd=S16DIR)
    b_ok = b.returncode == 0 and re.search(r'Ran 34 tests', b.stderr) is not None and '\nOK' in b.stderr
    c = run_guarded('k1-%s-s12-check' % tag, [PY, 'scripts/stack/studies/mc04_s12_five_ic_joint/joint_search.py',
                                              '--check'])
    c_ok = c.returncode == 0 and 'input pins, P3, P4, P11, 0 scenes and 6 checkpoint digests verified' in c.stdout
    g = s16_git_clean()
    st2 = s16_state()
    ok = a_ok and b_ok and c_ok and not g and not st2['cache_problems'] and not st2['durable_problem_count']
    return ok, {'s16_check': {'rc': a.returncode, 'tail': a.stdout.strip()[-400:]},
                's16_unittest': {'rc': b.returncode, 'tail': b.stderr.strip()[-200:]},
                's12_check': {'rc': c.returncode, 'tail': c.stdout.strip()[-300:]},
                'git_status_s16_dir': g, 's16_cache_and_durable': st2}


def full_replay_child(out_json):
    t = now()
    doc, reads = s12.full_replay(None)
    write_json(out_json, {'doc': doc, 'working_tree_reads': reads, 'wall_s': round(now() - t, 1)})


def k2_control():
    """K2: S12 P8, the full base replay in a child process, equal to the base."""
    base_doc = s12.gjson(s12.BASE, s12.GATE)
    op = bk(SCRATCH + '/k2-full.json')
    op.parent.mkdir(parents=True, exist_ok=True)
    p = run_guarded('k2-full-replay', [PY, str(HERE / 's16b.py'), '--full-replay', str(op)])
    if p.returncode:
        return False, {'returncode': p.returncode, 'stderr_tail': p.stderr[-1500:]}
    d = read_json(op)
    op.unlink()
    shutil.rmtree(bk(SCRATCH), ignore_errors=True)
    doc = d['doc']
    diffs = s12.compare_links(doc['links'], base_doc['links'])
    rows_eq = json.dumps(doc['replacement']) == json.dumps(base_doc['replacement']['footprints'])
    ways = doc['ways_out'] == base_doc['ways_out']
    cons = doc['consolidation'] == base_doc['consolidation']
    ok = not diffs and rows_eq and ways and cons and not doc['hold_errors']
    return ok, {'link_differences': diffs, 'rows_equal': rows_eq, 'ways_out_equal': ways, 'consolidation_equal': cons,
                'hold_errors': doc['hold_errors'], 'working_tree_reads': len(d['working_tree_reads']),
                'child_wall_s': d['wall_s']}


def k3_control():
    """K3: detachment and guard, as S16's C13, on this container: a detached 5-minute heartbeat under the guard
    outlives its wrapper, killed at 120 s, and the guard's per-sample file keeps growing."""
    d = ck('k3')
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    wrapper = d / 'k3_wrapper.sh'
    wrapper.write_text(
        '#!/bin/bash\n'
        '# K3 wrapper: starts the guarded heartbeat detached, then reports itself alive every 10 s until killed.\n'
        'D=%s\n' % d +
        'echo "wrapper_start $(date +%%s.%%N) pid $$" > $D/wrapper.txt\n'
        'setsid nohup %s %s $D/guard.json -- %s %s $D/heartbeat.txt > /dev/null 2>&1 < /dev/null &\n'
        % (PY, GUARD, PY, HERE / 'k3_heartbeat.py') +
        'echo "child_started $(date +%s.%N)" >> $D/wrapper.txt\n'
        'while true; do echo "wrapper_alive $(date +%s.%N)" >> $D/wrapper.txt; sleep 10; done\n')
    t0 = now()
    p = subprocess.run(['timeout', '-s', 'KILL', '120', 'bash', str(wrapper)], capture_output=True, text=True)
    t1 = now()
    deadline = t0 + 300 + 60
    while now() < deadline:
        g = d / 'guard.json'
        if g.exists() and read_json(g).get('finished'):
            break
        time.sleep(5)
    hb = [float(x) for x in (d / 'heartbeat.txt').read_text().split()] if (d / 'heartbeat.txt').exists() else []
    samples = (d / 'guard.json.samples.jsonl').read_text().splitlines() if (d / 'guard.json.samples.jsonl').exists() else []
    after = [x for x in samples if json.loads(x)['t'] > t1]
    g = read_json(d / 'guard.json') if (d / 'guard.json').exists() else {}
    hb_after = sum(1 for x in hb if x > t1)
    detail = {'tool_limit_s': 120, 'wrapper_rc': p.returncode, 'wrapper_s': round(t1 - t0, 1),
              'heartbeat_lines': len(hb), 'heartbeat_lines_after_wrapper_end': hb_after,
              'guard_samples': len(samples), 'guard_samples_after_wrapper_end': len(after),
              'guard_finished': g.get('finished'), 'child_returncode': g.get('returncode')}
    return k3_accept(detail), detail


def k3_accept(d):
    """K3 acceptance on its detail record (brief erratum 1, E1; DS-219). A SIGKILL from `timeout -s KILL` reads 137
    through a shell and -9 through subprocess.run; both mean the kill at the 120 s limit ended the wrapper."""
    return d['wrapper_rc'] in (137, -9) and d['wrapper_s'] >= 119 and d['heartbeat_lines_after_wrapper_end'] >= 150 \
        and bool(d['guard_finished']) and d['child_returncode'] == 0 and d['guard_samples_after_wrapper_end'] > 0


def k4_control():
    """K4: pins.json verified; a scratch copy of the pinned sources with one byte of s16b.py changed is refused."""
    bad = verify_pins()
    scratch = bk(SCRATCH + '/k4')
    shutil.rmtree(scratch, ignore_errors=True)
    try:
        for p_ in PIN_FILES:
            d = scratch / p_
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / p_, d)
        f = scratch / PIN_FILES[0]
        b = bytearray(f.read_bytes())
        b[0] ^= 1
        f.write_bytes(bytes(b))
        bad2 = verify_pins(scratch)
    finally:
        shutil.rmtree(bk(SCRATCH), ignore_errors=True)
    ok = not bad and bad2 == ['%s changed' % PIN_FILES[0]]
    return ok, {'problems': bad, 'scratch_copy_problems': bad2}


def n_control():
    """The N cases of the brief in test_s16b.py; STOP 3 when a vector or reason differs."""
    p = run_guarded('n-cases-test-s16b', [PY, '-m', 'unittest', '-v', 'test_s16b'], cwd=HERE, timeout=2400)
    ok = p.returncode == 0 and '\nOK' in p.stderr and 'skipped' not in p.stderr.split('Ran ')[-1]
    return ok, {'rc': p.returncode, 'tail': p.stderr.strip()[-2500:]}


# ---------------------------------------------------------------- K7, K8: S16's records under the new rules

def s16_logs():
    out = []
    for f in sorted((S16_BULK / 'stage2b').glob('*.json')):
        out.append(read_json(f))
    return out


def s16_plans():
    return {r['id']: r for r in read_json(S16_BULK / 'stage2a' / 'structures.json')['structures']}


def blocks_of_id(sid):
    return [b.split('+') for b in sid.split('|')[1:]]


def k7_control(w):
    """K7: the 24 rows-level passers of S16, replayed again; R7 on the E1 block; stage 3 lite."""
    plans = s16_plans()
    an = R.Anchors(w)
    out = []
    for lg_ in s16_logs():
        if not lg_.get('passed'):
            continue
        rp = lg_['replays'][lg_['passed'] - 1]
        sid = lg_['id']
        bl = blocks_of_id(sid)
        chosen = [(R.block_record(w, b), {'geometry': x['geometry'], 'slot_centre': x['slot_centre'],
                                          'direction': x['direction'], 'ring': x['ring']}) for b, x in zip(bl, rp['blocks'])]
        plan = plans[sid]['plan'] or []
        rows = R.scene_rows(w, chosen, plan)
        dg = s12.digest(rows)
        e1hits = [on_parts(w, r['front_board'], m['geometry']) for r, m in chosen if is_e1(r)]
        j = jclean(R.judge_replan(w, {}, rows, chosen, plan, run_overlay_search=False))
        c8443 = None
        for x in j.get('block_rule', []):
            for d in x['decouplers']:
                if d['ref'] == 'C8443' and x['ic'] == 'U8413':
                    c8443 = {'face_after': d['face_after'], 'other_face_after': d['other_face_after'],
                             'distance_after_mm': round(d['distance_after_mm'], 3),
                             'distance_before_mm': round(d['distance_before_mm'], 3), 'kind': x['block_rule']}
        r7213 = [{'after_mm': round(x['after_mm'], 3), 'before_mm': round(x['before_mm'], 3)}
                 for x in j.get('placed_ic_blocks', []) if x.get('r_iso') == 'R7213']
        out.append({'structure': sid, 'digest_equal': dg == rp['digest'], 'e1_on': e1hits,
                    'lite': classify_lite(j['fails']), 'fails': j['fails'], 'C8443': c8443,
                    'R7213': r7213[0] if r7213 else None})
    face_f = sum(1 for x in out if x['C8443'] and x['C8443']['other_face_after'])
    at16 = sum(1 for x in out if x['C8443'] and not x['C8443']['other_face_after'] and
               x['C8443']['distance_after_mm'] == 16.672)
    r49 = sum(1 for x in out if x['R7213'] and x['R7213']['after_mm'] == 49.858)
    r50 = sum(1 for x in out if x['R7213'] and x['R7213']['after_mm'] == 50.567)
    both = all(x['e1_on'] and set(sum(x['e1_on'][0].values(), [])) == set(PARTS) for x in out)
    a8 = all(any('U8413' in s and 'decoupler row breaks' in s for s in x['fails'].get('A8', [])) for x in out)
    a9 = all(any('R7213' in s for s in x['fails'].get('A9', [])) for x in out)
    ok = len(out) == 24 and all(x['digest_equal'] for x in out) and both and a8 and a9 and \
        (face_f, at16, r49, r50) == (12, 12, 8, 16)
    return ok, {'scenes': len(out), 'digests_equal': sum(x['digest_equal'] for x in out), 'R7_both_parts_all': both,
                'A8_U8413_all': a8, 'A9_R7213_all': a9, 'C8443_face_F': face_f, 'C8443_at_16.672': at16,
                'R7213_49.858': r49, 'R7213_50.567': r50,
                'lite_reading': {s: sum(1 for x in out if x['lite'] == s) for s in ('pass', 'final', 'undecided')},
                'per_scene': out}


def k8_control(w):
    """K8: S16's 1200 replays under the strict R5 and R7 (from the logged geometries; no replay)."""
    an = R.Anchors(w)
    rules = {}
    n = s_rej = 0
    rest = []
    for lg_ in s16_logs():
        bl = blocks_of_id(lg_['id'])
        for rp in lg_['replays']:
            n += 1
            rej = False
            info = []
            for b, x in zip(bl, rp['blocks']):
                rec = R.block_record(w, b)
                if rec['id'] not in rules:
                    rules[rec['id']] = R.Rules(w, rec, an, 'strict')
                bad, _, _ = rules[rec['id']].t1(x['geometry'])
                if bad:
                    rej = True
                info.append({'e1': is_e1(rec), 'on': on_parts(w, rec['front_board'], x['geometry'])})
            if rej:
                s_rej += 1
                continue
            rest.append({'id': lg_['id'], 'n': rp['n'], 'pass': rp['vector'] == 'PPPPPP', 'blocks': info})
    passed = [x for x in rest if x['pass']]
    failed = [x for x in rest if not x['pass']]
    r7 = lambda x: any(b['e1'] and b['on'] for b in x['blocks'])  # noqa: E731
    dom = [x for x in rest if not r7(x)]
    dom_non_e1_on = sum(1 for x in dom if any(b['on'] for b in x['blocks'] if not b['e1']))
    dom_clear = sum(1 for x in dom if not any(b['on'] for b in x['blocks']))
    got = {'replays': n, 'strict_R5_rejects': s_rej, 'other': len(rest), 'other_pass': len(passed),
           'other_fail': len(failed), 'R7_rejects_pass': sum(1 for x in passed if r7(x)),
           'R7_rejects_fail': sum(1 for x in failed if r7(x)), 'in_domain': len(dom),
           'in_domain_failed': sum(1 for x in dom if not x['pass']), 'in_domain_non_e1_on': dom_non_e1_on,
           'in_domain_all_clear': dom_clear, 'in_domain_scenes': [(x['id'], x['n']) for x in dom]}
    ok = (n, s_rej, len(rest), len(passed), len(failed), got['R7_rejects_pass'], got['R7_rejects_fail'], len(dom),
          got['in_domain_failed'], dom_non_e1_on, dom_clear) == (1200, 1087, 113, 24, 89, 24, 74, 15, 15, 14, 1)
    return ok, got


# ---------------------------------------------------------------- K5, K6, K9, K10

def k5_control(st1):
    s16 = {}
    for f in sorted((S16_BULK / 'stage1').glob('*.json')):
        d = read_json(f)
        s16[d['summary']['block']] = d['survivors']
    diffs = []
    tot = blocks = 0
    for bid, d in st1.items():
        mine = read_json(bk('stage1/%s.json' % bid))['strict_survivors']
        want = [e for e in s16[bid] if not e['class_s']]
        a = sorted((tuple(e['slot_centre']), e['direction'], tuple(e['key'])) for e in mine)
        b = sorted((tuple(e['slot_centre']), e['direction'], tuple(e['key'])) for e in want)
        if a != b:
            diffs.append(bid)
        tot += len(mine)
        blocks += bool(mine)
    e1 = read_json(bk('stage1/%s.json' % R.block_id([E1])))['strict_survivors']
    got = {'blocks_compared': len(st1), 'differences': diffs, 'blocks_with_survivor': blocks, 'survivors': tot,
           's16_survivors': sum(len(v) for v in s16.values()), 'P-K-E1': [len(e1), spots_of(e1)]}
    ok = len(st1) == 63 and not diffs and blocks == 40 and tot == 8665 and got['s16_survivors'] == 15836 and \
        got['P-K-E1'] == [179, 19]
    return ok, got


def k6_control(st1):
    e1b = {k: v for k, v in st1.items() if v['holds_E1']}
    keep = {k: v for k, v in e1b.items() if v['distinct_after_R6']}
    tot = sum(v['distinct_after_R6'] for v in keep.values())
    on = sum(v['distinct_R7_rejected'] for v in keep.values())
    clear = sum(v['distinct_survivors'] for v in keep.values())
    one = st1[R.block_id([E1])]
    pairs = [st1[R.block_id(['K-P-16', E1])], st1[R.block_id(['K-P-20', E1])]]
    non = {k: v for k, v in st1.items() if not v['holds_E1']}
    non_tot = sum(v['distinct_survivors'] for v in non.values())
    non_on = sum(v['on_parts_survivors'] for v in non.values())
    got = {'E1_blocks': len(e1b), 'E1_blocks_with_strict_survivor': len(keep), 'strict': tot, 'on': on,
           'clear': clear, 'P-K-E1': [one['distinct_survivors'], one['spots']],
           'pairs': [[p['distinct_survivors'], p['spots']] for p in pairs], 'non_E1': [non_on, non_tot],
           'E1_blocks_emptied_by_R7': sorted(k for k, v in keep.items() if not v['distinct_survivors'])}
    ok = len(e1b) == 32 and len(keep) == 14 and (tot, on, clear) == (1000, 285, 715) and \
        got['P-K-E1'] == [132, 14] and got['pairs'] == [[154, 18], [154, 18]] and got['non_E1'] == [748, 7665]
    return ok, got


K9_TABLE = {(1, 3): 2, (2, 0): 9, (2, 1): 43, (2, 2): 53, (2, 3): 15, (3, 0): 66, (3, 1): 114, (3, 2): 54, (3, 3): 5,
            (4, 0): 61, (4, 1): 50, (4, 2): 9, (5, 0): 15, (5, 1): 5, (6, 0): 1}


def k9_control(recs):
    live = [r for r in recs if r['live']]
    s3 = sum(1 for r in recs if r['dead_at'] == 'S3')
    cen = sum(1 for r in recs if r['dead_at'] == 'census')
    tab = defaultdict(int)
    for r in live:
        tab[(r['links'], len(r['rides']))] += 1
    e1a = sum(1 for r in live if [E1] in r['blocks'])
    got = {'structures': len(recs), 'live': len(live), 'dead_S3': s3, 'dead_census': cen,
           'by_links_ride_sites': {'%d,%d' % k: v for k, v in sorted(tab.items())}, 'E1_alone': e1a,
           'other_dead': sorted({r['dead_at'] for r in recs if r['dead_at'] not in (None, 'S3', 'census')})}
    ok = len(recs) == 876 and len(live) == 502 and s3 == 254 and cen == 120 and dict(tab) == K9_TABLE and e1a == 170
    return ok, got


def k10_control(pools_all, st1):
    with_surv = [b for b, v in st1.items() if v['distinct_survivors']]
    above = sorted(b for b in with_surv if not st1[b]['holds_E1'] and st1[b]['spots'] > POOL_SPOTS)
    above_all = sorted(b for b in with_surv if st1[b]['spots'] > POOL_SPOTS)
    e1max = max(len(pools_all[b]) for b in with_surv if st1[b]['holds_E1'])
    got = {'blocks_with_survivor': len(with_surv), 'above_20_spots': above_all, 'cut': above,
           'max_E1_pool': e1max}
    ok = len(with_surv) == 40 and len(above_all) == 12 and above == above_all and e1max <= 18
    return ok, got


# ================================================================ stages

def all_subsets():
    return R.all_subsets()


def stage1(w, clock):
    subs = all_subsets()
    todo = [x for x in subs if not bk('stage1/%s.json' % R.block_id(x)).exists()]
    CTX['deadline'] = now() + (STEP_CEIL['stage1'] - clock.used('stage1'))
    done = len(subs) - len(todo)
    if todo:
        with pool_ctx().Pool(WORKERS) as pool:
            for summ, strict, surv, per in pool.imap(census_one, todo):
                write_json(bk('stage1/%s.json' % summ['block']), {'summary': summ, 'strict_survivors': strict,
                                                                   'survivors': surv, 'per_grid': per})
                done += 1
                if not summ['complete']:
                    raise Stop('STOP 5: stage 1 cannot complete inside its ceiling (%s incomplete)' % summ['block'])
                if done % 8 == 0 or done == len(subs):
                    write_json(ck('stage1/progress.json'), {'blocks_done': done, 'of': len(subs)})
                    clock.tick()
    out = {R.block_id(x): read_json(bk('stage1/%s.json' % R.block_id(x)))['summary'] for x in subs}
    write_json(ck('stage1/summary.json'), {'status': STATUS, 'blocks': out})
    clock.tick()
    return out


def load_pools(st1):
    pools = {}
    for bid, v in st1.items():
        surv = read_json(bk('stage1/%s.json' % bid))['survivors']
        pools[bid] = pool_of16b(surv, v['holds_E1'])
    return pools


def stage2a(w, clock, rides, st1):
    recs = []
    n = 0
    for st in R.structures():
        if R.is_present(st):
            continue
        n += 1
        dead, why, brs = R.screen_s123(w, st, rides)
        r = {'id': R.struct_id(st), 'rides': st['rides'], 'blocks': st['blocks'], 'links': len(brs),
             'circuits': sum(b['circuits'] for b in brs), 'sizes': sorted(b['circuits'] for b in brs)}
        t = rides[R.ride_key(st['rides'])] if st['rides'] else None
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
        r['e1_block'] = next((b['id'] for b in brs if is_e1(b)), None)
        recs.append(r)
        if n % 100 == 0:
            write_json(ck('stage2a/progress.json'), {'structures_done': n})
            clock.tick()
    write_json(ck('stage2a/progress.json'), {'structures_done': n})
    write_json(bk('stage2a/structures.json'), {'status': STATUS, 'structures': recs})
    clock.tick()
    return recs


def rides_census(w):
    rd = R.Rides(w)
    res = {}
    import itertools
    for k in range(1, 7):
        for rs in itertools.combinations(R.SITES, k):
            res[R.ride_key(rs)] = rd.test(rs)
    return res


def new_state(order):
    offs = e1_offsets([r['e1_block'] for r in order])
    return {'round': 1, 'position': 0, 'replays': 0, 'bound': [], 'discarded': [], 'chunks': [], 'scenes_in_round': 0,
            'rounds': [], 'structures': [{'index': i, 'id': r['id'], 'e1_block': r['e1_block'], 'o': o, 'cursor': o,
                                          'done': {}, 'calls': {}, 'exhausted': [], 'replays': 0, 'finished': None,
                                          'scenes': []} for i, (r, o) in enumerate(zip(order, offs))]}


def task_of(order, s, rnd, deadline):
    r = order[s['index']]
    return {'index': s['index'], 'id': r['id'], 'blocks': r['blocks'], 'plan': r['plan'] or [], 'round': rnd,
            'cursor': s['cursor'], 'done': s['done'], 'calls': s['calls'], 'exhausted': s['exhausted'],
            'deadline': deadline}


def round_todo(state):
    """The unfinished structures in stage order, from the round's resume position."""
    return [s for s in state['structures'][state['position']:] if s['finished'] is None]


def apply_result(state, s, res, scene_no):
    """Fold one structure's round result into the state. Returns the scene record (or None)."""
    s['calls'] = {str(k): v for k, v in (res.get('calls') or s['calls']).items()}
    if 'exhausted' in res:
        s['exhausted'] = res['exhausted']
    kind = res['kind']
    if kind == 'legal_cap':
        s['finished'] = 'legality cap of 20 000 calls'
        return None
    if kind == 'none_left':
        s['finished'] = 'no legal scene left'
        return None
    if kind == 'time':
        return None
    sc = res['scene']
    s['cursor'] = res['cursor']
    s['done'][str(sc['spot'])] = s['done'].get(str(sc['spot']), 0) + 1
    s['replays'] += 1
    s['scenes'].append(scene_no)
    lite = (sc.get('lite') or {}).get('status')
    if lite == 'pass':
        s['finished'] = 'lite passer'
    elif lite == 'undecided':
        s['finished'] = 'LITE UNDECIDED'
    elif s['replays'] >= REPLAY_CAP_STRUCT:
        s['finished'] = '12 rows-only replays per structure'
    return sc


def stage2b(w, clock, recs, pools):
    live = [r for r in recs if r['live']]
    order = sorted(live, key=lambda r: (r['links'], r['circuits'], r['cheapest_sum'], r['id']))
    sp = bk('stage2b/state.json')
    state = read_json(sp) if sp.exists() else new_state(order)
    deadline = now() + (STAGE2B_START_BOUND_S - clock.used('stage2b'))
    CTX['pools'] = pools
    k11p = ck('arm0/K11.json')
    pending = []  # scene records not yet in a chunk

    def save(final=False):
        if pending:
            n = len(state['chunks'])
            name = 'stage2b/scenes-%04d.json' % n
            write_json(bk(name), {'status': STATUS, 'scenes': list(pending)})
            state['chunks'].append({'file': name, 'scenes': len(pending)})
            pending.clear()
        write_json(sp, state)
        write_json(ck('stage2b/progress.json'), {k: state[k] for k in ('round', 'position', 'replays', 'bound',
                                                                         'rounds')} | {'at': utc()})
        clock.tick()

    seq = None
    if not k11p.exists() and state['round'] == 1 and state['position'] == 0 and not state['chunks']:
        # K11 first: the first 12 scenes of round 1 in sequence in this process, before the pool starts
        seq, t0 = [], now()
        for s in state['structures']:
            if len([x for x in seq if x['kind'] == 'scene']) >= K11_N:
                break
            seq.append(scene_one(task_of(order, s, 1, deadline)))
        write_json(ck('stage2b/k11-sequential.json'), {'results': [{'index': x['index'], 'kind': x['kind'],
                                                                    'digest': x.get('scene', {}).get('digest')}
                                                                   for x in seq], 'wall_s': round(now() - t0, 1)})
        clock.tick()
    stop_all = False
    while not stop_all:
        todo = round_todo(state)
        if not todo:
            break
        if now() > deadline:
            state['bound'].append('80 min stage 2b start bound: round %d not started or not finished' % state['round'])
            break
        rnd = state['round']
        rinfo = state['rounds'][-1] if state['rounds'] and state['rounds'][-1]['round'] == rnd else None
        if rinfo is None:
            rinfo = {'round': rnd, 'tried': 0, 'replays': 0, 'rows_passers': 0, 'lite_passers': 0, 'undecided': 0,
                     'no_scene_left': 0, 'not_started_time': 0}
            state['rounds'].append(rinfo)
        tasks = [task_of(order, s, rnd, deadline) for s in todo]
        with pool_ctx().Pool(WORKERS) as pool:
            it = pool.imap(scene_one, tasks)
            for s, t in zip(todo, tasks):
                res = next(it)
                if seq is not None and len(seq) and res['index'] == seq[0]['index']:
                    x = seq.pop(0)
                    if x['kind'] != res['kind'] or x.get('scene', {}).get('digest') != res.get('scene', {}).get('digest'):
                        write_json(k11p, {'control': 'K11', 'pass': False, 'at': utc(),
                                          'detail': {'index': res['index'], 'sequential': x.get('scene', {}).get('digest'),
                                                     'pool': res.get('scene', {}).get('digest')}})
                        pool.terminate()
                        raise Stop('STOP 1: control K11 fails at structure %d' % res['index'])
                    if not seq:
                        write_json(k11p, {'control': 'K11', 'pass': True, 'at': utc(),
                                          'detail': {'scenes_compared': K11_N, 'note': 'sequential replays are not counted'}})
                        log('K11 PASS')
                if res['kind'] == 'time':
                    rinfo['not_started_time'] += 1
                    if not any('80 min' in b for b in state['bound']):
                        state['bound'].append('80 min stage 2b start bound')
                    state['position'] = s['index'] + 1
                    continue
                if res['kind'] == 'scene' and state['replays'] >= REPLAY_CAP:
                    state['discarded'].append({'index': s['index'], 'round': rnd, 'digest': res['scene']['digest']})
                    if not any('1800' in b for b in state['bound']):
                        state['bound'].append('1800 rows-only replays in stage 2b')
                    pool.terminate()
                    stop_all = True
                    break
                rinfo['tried'] += 1
                scene_no = state['replays'] + 1 if res['kind'] == 'scene' else None
                sc = apply_result(state, s, res, scene_no)
                if sc is not None:
                    state['replays'] += 1
                    rinfo['replays'] += 1
                    sc.update({'scene_no': scene_no, 'index': s['index'], 'id': s['id'], 'round': rnd})
                    if sc['vector'] == 'PPPPPP':
                        rinfo['rows_passers'] += 1
                        st_ = sc['lite']['status']
                        rinfo['lite_passers'] += st_ == 'pass'
                        rinfo['undecided'] += st_ == 'undecided'
                    pending.append(sc)
                elif res['kind'] == 'none_left':
                    rinfo['no_scene_left'] += 1
                state['position'] = s['index'] + 1
                if len(pending) >= CHUNK:
                    save()
                if state['replays'] >= REPLAY_CAP:
                    if not any('1800' in b for b in state['bound']):
                        state['bound'].append('1800 rows-only replays in stage 2b')
                    rest = len(todo) - (todo.index(s) + 1)
                    state['in_flight_at_cap'] = min(WORKERS, rest)
                    pool.terminate()
                    stop_all = True
                    break
            else:
                state['round'] += 1
                state['position'] = 0
        save()
        if any('80 min' in b for b in state['bound']):
            break
    save(final=True)
    return order, state


def all_scenes(state):
    out = []
    for c in state['chunks']:
        out += read_json(bk(c['file']))['scenes']
    return out


def k12_control(order, state):
    """K12: every S16b scene equal to an S16 replayed scene (same structure, slots and directions) gives its digest."""
    s16 = {}
    for lg_ in s16_logs():
        for rp in lg_['replays']:
            key = (lg_['id'], tuple((tuple(b['slot_centre']), b['direction']) for b in rp['blocks']))
            s16[key] = rp['digest']
    same, diff = 0, []
    for sc in all_scenes(state):
        key = (sc['id'], tuple((tuple(b['slot_centre']), b['direction']) for b in sc['blocks']))
        if key in s16:
            same += 1
            if s16[key] != sc['digest']:
                diff.append(sc['scene_no'])
    return not diff, {'overlapping_scenes': same, 'differences': diff}


def rank_key(w, sc, order_by_index):
    r = order_by_index[sc['index']]
    t = {'structure': {'blocks': r['blocks']}, 'id': r['id']}
    return R.scene_rank_key(w, None, t, {'blocks': sc['blocks']})


def stage3(w, clock, order, state):
    by = {r_i: r for r_i, r in enumerate(order)}
    scenes = all_scenes(state)
    lite = [sc for sc in scenes if sc.get('lite', {}).get('status') == 'pass']
    und = [sc for sc in scenes if sc.get('lite', {}).get('status') == 'undecided']
    groups = [('lite passer', sorted(lite, key=lambda sc: rank_key(w, sc, by))),
              ('LITE UNDECIDED', sorted(und, key=lambda sc: rank_key(w, sc, by)))]
    counter = OverlayCounter(ck('stage3/overlay-count.json'))
    orig = w.s.search
    w.s.search = counter.wrap(orig)
    info = {'lite_passers': len(lite), 'undecided': len(und), 'judged': [], 'incomplete_cap': 0, 'passed_full': 0}
    kept = []
    try:
        for gname, grp in groups:
            for sc in grp:
                f = ck('stage3/scene-%04d.json' % sc['scene_no'])
                if f.exists():
                    res = read_json(f)
                else:
                    r = by[sc['index']]
                    chosen = chosen_of({'blocks': r['blocks']}, sc['blocks'])
                    rows = R.scene_rows(w, chosen, r['plan'] or [])
                    counter.scene = sc['scene_no']
                    g = judge_full_guarded(lambda: jclean(R.judge_replan(w, {}, rows, chosen, r['plan'] or [],
                                                                         run_overlay_search=True)))
                    f0, _ = R.check_rows16(w, rows)
                    res = {'scene_no': sc['scene_no'], 'structure': sc['id'], 'group': gname,
                           'rank': rank_key(w, sc, by), 'status': g['status'], 'rows_digest': s12.digest(rows),
                           'digest_equal_stage2b': s12.digest(rows) == sc['digest'], 'A0': not f0.get('A0')}
                    if g['status'] == 'judged':
                        j = g['judge']
                        res.update({'passes': j['passes'], 'fails': j['fails'],
                                    'overlay_blocks': len(j.get('overlay_blocks') or []),
                                    'pass': not f0.get('A0') and all(j['passes'].values()),
                                    'figures': lite_figures(j),
                                    'judge': {k: j[k] for k in ('passes', 'fails', 'protected_effective', 'rows',
                                                                'link_figures')}})
                    else:
                        res.update({'pass': None, 'reason': g['reason']})
                    write_json(f, res)
                    clock.tick()
                info['judged'].append({k: res.get(k) for k in ('scene_no', 'structure', 'group', 'rank', 'status',
                                                               'pass', 'fails')})
                if res['status'] != 'judged':
                    info['incomplete_cap'] += 1
                elif res['pass']:
                    info['passed_full'] += 1
                    kept.append((sc, res))
    finally:
        w.s.search = orig
    info['overlay_count'] = counter.read()
    CAND.mkdir(exist_ok=True)
    for n, (sc, res) in enumerate(kept, 1):
        r = by[sc['index']]
        t = {'id': r['id'], 'structure': {'rides': r['rides'], 'blocks': r['blocks']}, 'plan': r['plan'] or []}
        chosen = chosen_of({'blocks': r['blocks']}, sc['blocks'])
        rows = R.scene_rows(w, chosen, r['plan'] or [])
        body = R.scene_body(w, n, t, {'blocks': sc['blocks'], 'returned': sc['returned']}, res['judge'],
                            'P' * 10 + ' ' + 'P' * 6, rows)
        write_json(CAND / ('scene-%d.json' % n), body)
    info['kept'] = len(kept)
    write_json(ck('stage3/summary.json'), info)
    return kept, info


def stage4(w, clock, order, kept):
    by = {i: r for i, r in enumerate(order)}
    cen = read_json(R.S12CENSUS)['accepted'][R.L13]
    seen, ents = set(), []
    for e in cen:
        k = (tuple(e['slot_centre']), e['direction'])
        if k not in seen:
            seen.add(k)
            ents.append(e)
    out = {'survivors': len(ents), 'scenes': []}
    jobs = []
    for n, (sc, res) in enumerate(kept, 1):
        r = by[sc['index']]
        blocks = [{'sites': b, 'geometry': x['geometry'], 'slot_centre': x['slot_centre'], 'direction': x['direction']}
                  for b, x in zip(r['blocks'], sc['blocks'])]
        for k, e in enumerate(ents[:STAGE4_PER_SCENE]):
            jobs.append({'scene': n, 'index': k, 'blocks': blocks, 'plan': r['plan'] or [],
                         'entry': {x: e[x] for x in ('slot_centre', 'direction', 'dist', 'grid_mm')}})
    results = []
    if jobs:
        with pool_ctx().Pool(WORKERS) as pool:
            for job, r in zip(jobs, pool.imap(stage4_one, jobs)):
                r['scene'] = job['scene']
                results.append(r)
                if r['index'] == min(len(ents), STAGE4_PER_SCENE) - 1:
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


EXCLUSIONS = {
    'a': 'the 40-way size and any size larger than needed',
    'b': 'a block as a host',
    'c': 'a ride that divides a site',
    'd': 'a slot beyond 35 mm from its block centre',
    'e': 'a block slot with a member site beyond its class distance',
    'f': 'a slot of the block that holds P-K-E1 on C8443 or R7213 (Ruling Q2, R7); for R7213 alone the evidence is '
         'indirect: no S16 scene had the E1 block on R7213 only and passed rows',
}


def verdict_of(st1, pools, state, info3, kept):
    if kept:
        return 'RE-PLAN SCENE AT ROWS LEVEL, GATE REPLAY NOT RUN, NOT ADOPTED', [], None
    cut = sorted(b for b, v in st1.items() if not v['holds_E1'] and v['spots'] > POOL_SPOTS)
    bounds = ['pool of 20 spots per block, cutting %d blocks (the E1 block is never cut)' % len(cut)]
    fin = defaultdict(int)
    for s in state['structures']:
        fin[s['finished'] or 'unfinished'] += 1
    bounds += list(state['bound'])
    if fin.get('12 rows-only replays per structure'):
        bounds.append('12 rows-only replays per structure, reached in %d structures' % fin['12 rows-only replays per structure'])
    if fin.get('legality cap of 20 000 calls'):
        bounds.append('20 000 legality calls per structure, reached in %d structures' % fin['legality cap of 20 000 calls'])
    if fin.get('unfinished'):
        bounds.append('%d live structures unfinished when stage 2b ended' % fin['unfinished'])
    nf = sum(1 for x in info3['judged'] if x['status'] == 'judged' and not x['pass'])
    if nf:
        bounds.append('a structure finished at its first lite passer or LITE UNDECIDED scene: %d such scenes failed '
                      'stage 3 full and their structures were not searched further' % nf)
    if info3['incomplete_cap']:
        bounds.append('10 overlay block searches: %d scenes STAGE 3 INCOMPLETE (CAP)' % info3['incomplete_cap'])
    complete = not state['bound'] and not fin.get('unfinished') and not info3['incomplete_cap']
    rule = ('Ruling Q6 applies: the run reached its end with a verdict of Ruling P6, no STOP, no STAGE 3 INCOMPLETE '
            '(CAP) scene and no LITE UNDECIDED scene unjudged, and no scene passes stage 3 full; the design authority '
            'will propose no further placement study for U8409, whatever bounds the verdict names'
            if not info3['incomplete_cap'] else
            'Ruling Q6 does not apply: a scene is STAGE 3 INCOMPLETE (CAP); the result returns to the design authority')
    return 'NO RE-PLAN FOUND (BOUNDED)', bounds, {'stop_rule': rule, 'finished_by': dict(fin),
                                                   'every_structure_finished': complete}


# ================================================================ the bulk cache

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


def durable_copy():
    """Copy the cache and the manifest to the durable folder, then re-read every file about 10 s later."""
    man = read_json(BULK_MANIFEST)['files']
    for r in man:
        dst = Path(DURABLE + r)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BULK / r, dst)
    shutil.copyfile(BULK_MANIFEST, DURABLE + 'bulk-manifest.json')
    copied = utc()
    time.sleep(10)
    bad = [r for r, v in man.items() if not Path(DURABLE + r).exists() or sha_file(DURABLE + r) != v['sha256']]
    rec = {'location': DURABLE, 'copied_utc': copied, 'reread_utc': utc(), 'files_verified': len(man) - len(bad),
           'problems': bad, 'manifest_copy_identical': sha_file(DURABLE + 'bulk-manifest.json') == sha_file(BULK_MANIFEST)}
    write_json(ck('durable-copy.json'), rec)
    return rec


# ================================================================ the driver

def guard_env():
    bad = [k for k in os.environ if k.startswith('S16B_') and k != 'S16B_RESUME_REASON']
    if bad and not DEV:
        raise SystemExit('S16B_* variables are for tests and dry runs only: %s' % bad)


def drive(resume=False):
    global W
    guard_env()
    CK.mkdir(parents=True, exist_ok=True)
    gate = start_gate()
    if gate:
        raise SystemExit('the driver refuses to start (Ruling Q5): %s' % '; '.join(gate))
    run_path = ck('run.json')
    if run_path.exists() and not resume:
        raise SystemExit('run.json exists: use --resume')
    if not run_path.exists() and resume:
        raise SystemExit('nothing to resume')
    bad = verify_pins()
    if bad:
        raise SystemExit('STOP 1: the sources differ from pins.json, the driver does not start: %s' % bad)
    clock = Clock(run_path)
    rec = clock.rec
    if resume:
        rec['resumes'].append({'at': utc(), 'reason': os.environ.get('S16B_RESUME_REASON', 'interrupted')})
        if len(rec['resumes']) > RESUME_CAP:
            write_json(run_path, rec)
            record_stop('STOP 6: a fourth resume', run_rec=rec)
            sys.exit(3)
    else:
        rec['started'] = utc()
        rec['commit'] = s12.git('rev-parse', 'HEAD', text=True).strip()
        gd = HERE / 'checkpoints' / 'guard'
        for f in sorted(gd.glob('start-*.json')) if gd.exists() else ():
            rec['executor_timed'][f.stem] = read_json(f)['wall_s']
    rec['stop'] = None
    write_json(run_path, rec)

    def control(name, fn, *a, stop_n=1):
        f = ck('arm0/%s.json' % name)
        if f.exists() and read_json(f)['pass']:
            return read_json(f)['detail']
        t0 = now()
        ok, detail = fn(*a)
        control_record(name, ok, detail, t0)
        clock.tick()
        if not ok:
            raise Stop('STOP %d: control %s fails' % (stop_n, name))
        return detail

    try:
        clock.begin('arm0')
        control('K1-start', k1_control, 'start')
        control('K4', k4_control)
        control('N', n_control, stop_n=3)
        control('K3', k3_control)
        w = s12.World()
        W = w
        clock.tick()
        control('K7', k7_control, w)
        control('K8', k8_control, w)
        control('K2', k2_control)
        clock.begin('stage1')
        st1 = stage1(w, clock)
        control('K5', k5_control, st1)
        control('K6', k6_control, st1)
        clock.begin('stage2a')
        rp = ck('stage2a/rides.json')
        if rp.exists():
            rides = read_json(rp)
        else:
            rides = rides_census(w)
            write_json(rp, rides)
        if bk('stage2a/structures.json').exists():
            recs = read_json(bk('stage2a/structures.json'))['structures']
        else:
            recs = stage2a(w, clock, rides, st1)
        pools = load_pools(st1)
        write_json(ck('stage2a/pools.json'), {b: {'spots': len(p), 'clear': sum(1 for e in p if not e['on_parts']),
                                                  'holds_E1': st1[b]['holds_E1'], 'spots_before_cut': st1[b]['spots']}
                                              for b, p in pools.items() if p})
        control('K9', k9_control, recs)
        control('K10', k10_control, pools, st1)
        clock.begin('stage2b')
        order, state = stage2b(w, clock, recs, pools)
        control('K12', k12_control, order, state)
        clock.begin('stage3')
        kept, info3 = stage3(w, clock, order, state)
        clock.begin('stage4')
        info4 = stage4(w, clock, order, kept)
        clock.begin('end')
        write_manifest()
        dc = durable_copy()
        if dc['problems'] or not dc['manifest_copy_identical']:
            raise Stop('STOP 8: the durable copy differs after re-reading: %s' % dc['problems'][:5])
        clock.tick()
        control('K1-end', k1_control, 'end')
        clock.begin(None)
        v, bounds, extra = verdict_of(st1, pools, state, info3, kept)
        rec.update({'verdict': v, 'bounds': bounds, 'verdict_extra': extra, 'finished': utc()})
        write_json(run_path, rec)
        finish(st1, order, state, info3, info4, v, bounds, extra)
    except Stop as e:
        log(str(e))
        try:
            clock.tick(save=False)
        except Stop:
            pass
        rec['ended'] = utc()
        write_json(run_path, rec)
        h, ok = record_stop(str(e), run_rec=rec)
        log('stop recorded', h, 'durable re-read', ok)
        sys.exit(3)
    try:
        clock.tick(save=False)
    except Stop:
        pass
    rec['ended'] = utc()
    write_json(run_path, rec)
    log('driver end', rec.get('verdict'))


def finish(st1, order, state, info3, info4, v, bounds, extra):
    res = {'status': STATUS, 'brief': BRIEF, 'brief_sha256': BRIEF_SHA, 'pins': read_json(PINS),
           'run': read_json(ck('run.json')), 'verdict': v, 'bounds': bounds, 'exclusions': EXCLUSIONS,
           'verdict_extra': extra,
           'controls': {f.stem: read_json(f)['pass'] for f in sorted((CK / 'arm0').glob('*.json'))},
           'stage1': {b: {k: s[k] for k in ('size', 'distinct_after_R6', 'distinct_R7_rejected', 'distinct_survivors',
                                            'spots', 'on_parts_survivors', 'cheapest_cost')} for b, s in st1.items()},
           'stage2b': {k: state[k] for k in ('replays', 'bound', 'rounds', 'discarded')} |
           {'in_flight_at_cap': state.get('in_flight_at_cap'),
            'finished_by': extra['finished_by'] if extra else None},
           'stage3': {k: info3[k] for k in ('lite_passers', 'undecided', 'incomplete_cap', 'passed_full',
                                             'overlay_count')},
           'stage4': info4, 'candidates': sorted(p.name for p in CAND.glob('scene-*.json')) if CAND.exists() else []}
    dig = {}
    for f in sorted(CK.rglob('*.json')):
        rel = str(f.relative_to(OUTDIR))
        if rel in ('checkpoints/run.json',) or rel.startswith('checkpoints/k3/'):
            continue
        dig[rel] = sha_file(f)
    man = read_json(BULK_MANIFEST)['files']
    for r, x in man.items():
        dig[r] = x['sha256']
    res['digests'] = dig
    res['bulk'] = {'manifest': 'bulk-manifest.json', 'files': len(man), 'durable_copy': DURABLE}
    write_json(RESULT, res)


def check():
    """Pins (SOURCE CHANGED AFTER RUN), every checkpoint digest, the cache against its manifest (PARTIAL CHECK when
    absent, CHECK FAILED when partial or altered), and three stage 2b scenes replayed again when the cache is here."""
    global W
    errs, changed = [], verify_pins()
    if changed:
        print('SOURCE CHANGED AFTER RUN: %s' % changed)
    res = read_json(RESULT)
    present, bad = R.bulk_state(BULK, BULK_MANIFEST)
    if bad:
        raise SystemExit('CHECK FAILED: the bulky intermediates in %s are partly present or differ from the manifest: %s'
                         % (BULK, bad[:10]))
    man = read_json(BULK_MANIFEST)['files']
    n = 0
    for path, want in res['digests'].items():
        if path in man:
            if man[path]['sha256'] != want:
                errs.append('manifest and result.json disagree on %s' % path)
            continue
        n += 1
        f = OUTDIR / path
        if not f.exists() or sha_file(f) != want:
            errs.append('digest of %s differs' % path)
    reran = 0
    if present and (BULK / 'stage2b' / 'state.json').exists():
        w = s12.World()
        W = w
        recs = read_json(bk('stage2a/structures.json'))['structures']
        live = sorted([r for r in recs if r['live']], key=lambda r: (r['links'], r['circuits'], r['cheapest_sum'], r['id']))
        state = read_json(bk('stage2b/state.json'))
        for sc in all_scenes(state)[:3]:
            r = live[sc['index']]
            rows = R.scene_rows(w, chosen_of({'blocks': r['blocks']}, sc['blocks']), r['plan'] or [])
            if s12.digest(rows) != sc['digest']:
                errs.append('scene %d replays differently' % sc['scene_no'])
            reran += 1
    if errs or changed:
        raise SystemExit('CHECK FAILED: %s' % '; '.join(errs + ['source changed: %s' % changed] if changed else errs))
    if not present:
        print('PARTIAL CHECK (bulky intermediates absent from %s; the copy is at %s): %d checkpoint digests; the %d '
              'cached digests were compared with the manifest only, and the stage 2b replays were NOT RUN'
              % (BULK, DURABLE, n, len(man)))
        return
    print('result.json current: pins verified, %d checkpoint digests, %d stage 2b scenes re-run (%d cached files '
          'verified against the manifest)' % (n, reran, len(man)))


def main():
    a = sys.argv[1:]
    if not a:
        raise SystemExit('usage: s16b.py --write-pins | --run | --resume | --check | --gate | --full-replay OUT')
    if a[0] == '--full-replay':
        full_replay_child(a[1])
    elif a[0] == '--write-pins':
        guard_env()
        if PINS.exists():
            raise SystemExit('pins.json exists; pins are written once, before the recorded run')
        print(json.dumps(write_pins(), indent=1))
    elif a[0] == '--run':
        drive(False)
    elif a[0] == '--resume':
        drive(True)
    elif a[0] == '--check':
        check()
    elif a[0] == '--gate':
        p = StopPaths(os.environ.get('S16B_GATE_CK'), os.environ.get('S16B_GATE_STOPS'),
                      os.environ.get('S16B_GATE_DECISIONS'))
        g = start_gate(p)
        print('REFUSE: ' + '; '.join(g) if g else 'START')
        sys.exit(2 if g else 0)
    else:
        raise SystemExit('unknown option %s' % a[0])


if __name__ == '__main__':
    main()
