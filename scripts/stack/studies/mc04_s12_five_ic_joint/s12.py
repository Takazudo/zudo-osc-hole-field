"""MC04-S12 (DS-151): the library of the five-IC joint link search (study only).

Brief: circuit/orchestration/campaigns/osc-stack-20261114/mc04-s12-five-ic-joint-search-brief-20261127.md (Revision 2).
Every design input is read from the snapshot 6e5716e7 (a git archive into a scratch root), never from the working tree.
Nothing here writes outside this study directory. Courtyard level on unvalidated drafts; nothing is adopted.
"""
from __future__ import annotations
import copy
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
S8 = ROOT / 'scripts/stack/studies/mc04_s8_replacement'
S9 = ROOT / 'scripts/stack/studies/mc04_s9_slot_moves'
S10 = ROOT / 'scripts/stack/studies/mc04_s10_l13'
for p in (str(ROOT), str(S8), str(S9), str(S10)):
    if p not in sys.path:
        sys.path.insert(0, p)
import replacement as rp  # noqa: E402
import slot_moves as sm  # noqa: E402
import slot_moves_a2 as sa2  # noqa: E402
import overlay as ov  # noqa: E402
import member_faces as mfc  # noqa: E402
from replacement import lg, p2, sg  # noqa: E402

BASE = '6e5716e7fc011e2f028982f645d18b8d802acb29'
RETURNED = '32580f77c9d0aa9c6067cbad965a6f701050ca5d'
PAPER = ov.PAPER
GATE = 'design/stack/geometry/links/link-gate.json'
GOPTS = 'design/stack/geometry/links/link-gate-options.json'
ERA = 'design/stack/geometry/links/link-era-replacements.json'
LOCALITY = 'design/partition/locality-acceptances.json'
RADIUS = 35.0
INNER = 24.0
GRIDS = (2.0, 0.5, 0.25)
FIVE = ('U1415', 'U5110', 'U8409', 'U5209', 'U5210')
SEARCHED = ('P-K-P-L07', 'P-K-P-L08', 'P-K-P-L12.02.01.02', 'P-K-P-L03.01', 'P-K-P-L13.01.01.01',
            'P-K-P-L13.01.01.02', 'P-K-P-L13.01.02.01', 'P-K-P-L15.02.01.01')
UNTOUCHED = ('JL', 'JR', 'O1', 'O3', 'O5')
STOP_SUFFIX = ('_FB', '_SUM', '_SENSE')
STATUS = 'CANDIDATE SCENE, STUDY ONLY, NOT ADOPTED, UNVALIDATED DRAFT'

PINNED_INPUTS = {
    'design/stack/geometry/links/link-gate.json': 'bcbee2ca955ae06f0d42031899cb3d74501916545893f9454eaa18c89ccbecc3',
    'design/stack/geometry/links/link-gate-options.json': '441c998f7801136ebb68e124ae4ac0c1c948533676c815560f716fc7afac2aad',
    'design/stack/geometry/links/link-era-replacements.json': 'a9af0e8ca4162822dc0608943c8c0813f347b9e5f8ca2b7b612a522ecd25f4d0',
    'design/stack/geometry/links/link-options.json': 'b0a60bf721b155200fc6a5b9304b20b84767638959c7f009a794f93f4e7bb4c9',
    'design/stack/geometry/stack-candidate.json': '22e817eae2af189119ff0a751a8f08099edd735b690954f7c3fbe6e66ff4004d',
    'design/stack/fixings/fixing-sites.json': 'da13bede1a49ac047540c2236e88659a93f17f74567225dad9d9490f087d92a5',
    'design/stack/gate-a-open-items.json': '235619a3c916db1bf9f3eb7a49c79d2df21f0b51a9f877dafe4bf567b9ca9a63',
    'design/stack/trimmers/relocation-plan.json': '56ce0dac92688e2a1d7a2844a8a56b1c122c04e92bd03a3db4463600d20075dd',
    'design/stack/connectors/flex-links.json': '68700f7190c3e0d86ec942b4811aee470ce3a71b7a15a1599500c9a732094339',
    'design/partition/locality-acceptances.json': '54f2c5a5fd64314a4cfee812fe7e781013c3a11bef176d1c31408bed7da45dc7',
    'design/partition/floorplan-candidate.json': '12083ea177cad1492f07fa96ad6dbfea8e5f8d2d347199bb555475c5b9e75a38',
    'design/partition/adopted-placement-pins.json': '9e827879ebcccea57d247e433a496db71ee1213c87af27b90c81fada2d1218b2',
    'design/reports/io-partition.json': '235277959121d8599cbe1b6c6ae65ed4cd3fd3813cf2a8db05d2951ce5b633ce',
    'design/grid/placements.lock.json': '297300b067fd646624b9e501791163fa2d60702862b61568753bf92e5b88dbe8',
}
PINNED_TREES = {'design/partition': 'c4fb824f', 'design/grid': 'a07b5141', 'design/mechanical': '673070f1',
                'design/stack': '80917ba4', 'design/power': '6c384211', 'design/reports': '97a4c5ad', 'boards': 'f97cf1a3'}
PINNED_CODE = {
    'scripts/stack/geometry/links_gate.py': 'f4960081d667cc3852cdadb431ba280e11bfae5d0a96cbc3da788514327edf44',
    'scripts/stack/geometry/links_gate_part2.py': 'e0d584c55f823ceb4743e5cd51ad181b505ac751b7bd71641652ab9397de12ca',
    'scripts/stack/geometry/links.py': '928814c730d87538e3eadcb03394bfd7ccc53fd45a86ea92e20c1149d0715f50',
    'scripts/stack/geometry/stackgeom.py': '70db6b0833512a20029b743c49d9adf0fe1b69ef8bb4d0063afc3515cb07d7ab',
    'scripts/stack/studies/mc04_s8_replacement/replacement.py': '543b02b7baf9d0a1ed531985c4b584fb1a254cc0507903e1c08b95e0ab07916e',
    'scripts/stack/studies/mc04_s8_replacement/replacement_r7.py': '81398e90be87f58640f67252dfa5057a9747f4ecae6f7154ffa3a8a5c4091d94',
    'scripts/stack/studies/mc04_s8_replacement/member_faces.py': '90f094da93fdeb8c177104d28648c42d1b6b1b16b11cdf01dc788c92df196e81',
    'scripts/stack/studies/mc04_s9_slot_moves/slot_moves.py': '7fcbcd8fa5e0d19e8ecd309d6e15a1f94caad6eee237fb635b1ca908b1b16898',
    'scripts/stack/studies/mc04_s9_slot_moves/slot_moves_a2.py': '26874e1f7d1e71923ccc88d977f6097bbf1a0c226cd9c9f54c8f00a5c58708d1',
    'scripts/stack/studies/mc04_s10_l13/overlay.py': '8acf3bb86873612fed99daf798435fff8301bdd6302a83df2d67ec3b731f3519',
}
RESULT_A2_SHA = '9d524988'
BASE_LINKS = {  # the brief's base table: search centre, recorded slot, direction, size, cable, circuits used / size
    'P-K-P-L07': ((29.375, 215.9375), (47.375, 213.9375), '+y', 'FH12-N40', 'C26618', 50.0, 23, 40),
    'P-K-P-L08': ((67.3889, 211.6056), (73.3889, 213.6056), '+y', 'FH12-N40', 'C26618', 50.0, 27, 40),
    'P-K-P-L12.02.01.02': ((150.5, 241.0), (159.0, 237.0), '+y', 'FH12-N8', 'C29534', 50.0, 6, 8),
    'P-K-P-L03.01': ((232.6667, 184.3333), (214.6667, 192.3333), '-y', 'FH12-N26', 'C32128', 60.0, 25, 26),
    'P-K-P-L13.01.01.01': ((190.1667, 189.6667), (184.1667, 193.6667), '+y', 'FH12-N8', 'C29534', 50.0, 8, 8),
    'P-K-P-L13.01.01.02': ((167.5, 185.0), (167.5, 195.0), '+y', 'FH12-N8', 'C29534', 50.0, 7, 8),
    'P-K-P-L13.01.02.01': ((167.5, 199.0), (159.0, 198.5), '-y', 'FH12-N8', 'C29534', 50.0, 8, 8),
    'P-K-P-L15.02.01.01': ((184.5, 213.0), (193.0, 213.0), '+y', 'FH12-N8', 'C29534', 50.0, 7, 8),
}
BASE_ICS = {  # paper pose, recorded courtyard, link rectangles on it at the base
    'U1415': ((62.95, 222.97), 'B', [58.0, 219.27, 67.63, 226.67],
              {'P-K-P-L07': {'K field', 'latch margin'}, 'P-K-P-L08': {'K field', 'K tail', 'latch margin'}}),
    'U5110': ((157.93, 247.72), 'B', [153.25, 244.02, 162.88, 251.42], {'P-K-P-L12.02.01.02': {'K field', 'latch margin'}}),
    'U8409': ((203.2, 192.47), 'B', [198.25, 188.77, 207.88, 196.17], {'P-K-P-L03.01': {'slot', 'K tail'}}),
    'U5209': ((157.95, 206.58), 'B', [153.0, 202.88, 162.63, 210.28], {'P-K-P-L13.01.01.02': {'K field', 'latch margin'}}),
    'U5210': ((180.97, 204.70), 'B', [177.27, 199.75, 184.67, 209.38],
              {'P-K-P-L13.01.01.01': {'K field', 'K tail', 'latch margin'}}),
}
CLUSTERS = (('West', ('P-K-P-L07', 'P-K-P-L08'), ('U1415',)),
            ('South', ('P-K-P-L12.02.01.02',), ('U5110',)),
            ('East', ('P-K-P-L03.01', 'P-K-P-L15.02.01.01', 'P-K-P-L13.01.01.01', 'P-K-P-L13.01.02.01',
                      'P-K-P-L13.01.01.02'), ('U8409', 'U5210', 'U5209')))


# ---------------------------------------------------------------- inputs

def git(*args, text=False):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, check=True, text=text).stdout


def git_show(rev, path):
    return git('show', f'{rev}:{path}')


def gjson(rev, path):
    return json.loads(git_show(rev, path))


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    return sha_bytes(Path(p).read_bytes())


def canon(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


def digest(obj):
    return sha_bytes(canon(obj).encode())


def input_pins():
    """(pins, problems): the input SHA-256 and tree hashes at the snapshot, and the code hashes in the working tree."""
    out, bad = {'inputs': {}, 'trees': {}, 'code': {}}, []
    for p, want in PINNED_INPUTS.items():
        got = sha_bytes(git_show(BASE, p))
        out['inputs'][p] = got
        if got != want:
            bad.append('input %s: %s != %s' % (p, got, want))
    for p, want in PINNED_TREES.items():
        got = git('rev-parse', f'{BASE}:{p}', text=True).strip()
        out['trees'][p] = got
        if not got.startswith(want):
            bad.append('tree %s: %s != %s' % (p, got, want))
        snap = git('rev-parse', f'8243acdf:{p}', text=True).strip()
        if snap != got:
            bad.append('tree %s differs from 8243acdf' % p)
    for p, want in PINNED_CODE.items():
        got = sha_file(ROOT / p)
        out['code'][p] = got
        if got != want:
            bad.append('code %s: %s != %s' % (p, got, want))
    return out, bad


def scratch_root(gopts_override=None, tag='replay'):
    """A git archive of the snapshot paths at BASE in a new temporary directory, with only link-gate-options.json
    rewritten when `gopts_override` is given. The caller removes it."""
    d = Path(tempfile.mkdtemp(prefix=f's12-{tag}-'))
    tar = git('archive', '--format=tar', BASE, '--', *rp.SNAPSHOT_PATHS)
    with tarfile.open(fileobj=io.BytesIO(tar)) as t:
        t.extractall(d, filter='data')
    if gopts_override is not None:
        (d / GOPTS).write_text(json.dumps(gopts_override, indent=1) + '\n')
    return d


class ReadLog:
    """Records every file under the working tree that is opened while active (the scratch root is elsewhere)."""

    def __init__(self):
        self.paths = set()
        self._open = None

    def __enter__(self):
        import builtins
        self._open = builtins.open
        root = str(ROOT) + os.sep
        log = self.paths

        def hooked(file, *a, **k):
            try:
                p = os.path.abspath(os.fspath(file))
                if p.startswith(root) and '/.git/' not in p and '__pycache__' not in p:
                    log.add(os.path.relpath(p, ROOT))
            except TypeError:
                pass
            return self._open(file, *a, **k)
        builtins.open = hooked
        io.open = hooked
        return self

    def __exit__(self, *exc):
        import builtins
        builtins.open = self._open
        io.open = self._open
        return False


# ---------------------------------------------------------------- the study context

class Ctx12(sm.S9):
    """The S9 model class, reading every input at the snapshot BASE (tree-equal to 8243acdf)."""
    snapshot = BASE


class World:
    """One prepared snapshot: model, base links and rows, protected set, base tails and anchors."""

    def __init__(self):
        rp.snapshot_root(BASE)  # makes the scratch copy once
        s = Ctx12()
        s.setup9()
        self.s = s
        self.ctx, self.model, self.inp = s.ctx, s.ctx.model, s.inp
        self.base_out = copy.deepcopy(s.out0)
        self.byid = {r['id']: r for r in self.base_out}
        self.base_rows_list = copy.deepcopy(s.gate['replacement']['footprints'])
        self.base_rows = {(r['board'], r['ref']): r for r in self.base_rows_list}
        self.site_by = {x['id']: x for x in s.sites}
        self.arm1 = sm.Arm1(s, 0.0)
        self.arm1a2 = sa2.Arm1A2(s, 0.0)
        self.gap = self.arm1.gap
        self.latch_field = self.arm1.latch_field
        self.protected = protected_set(s)
        self.era = json.loads((s.root / ERA).read_text())
        self.retained = self.era['placed']
        self.fixings = json.loads((s.root / 'design/stack/fixings/fixing-sites.json').read_text())
        live = p2.live(self.base_out)
        self.anchor = defaultdict(set)   # (board, ref) -> non-searched links (or fixings) that displace it at the base
        self.searched_disp = defaultdict(set)
        for r in live:
            if not r['placed']:
                continue
            for k, v in r['displaced'].items():
                b = r['front_board'] if k == 'front B' else 'K'
                for ref in v:
                    (self.searched_disp if r['id'] in SEARCHED else self.anchor)[(b, ref)].add(r['id'])
        for f in self.inp['fixing_list']['fixings']:
            if f.get('active'):
                for m in f.get('part_moves', []):
                    self.anchor[(m['board'], m['ref'])].add('fixing ' + f['id'])
        self.base_tail = set()
        for r in live:
            if r['placed']:
                ut = r.get('under_tails') or {}
                self.base_tail |= {(r['front_board'], x) for x in ut.get('front tail', [])}
                self.base_tail |= {('K', x) for x in ut.get('K tail', [])}
        self.recs26 = {}
        self._base_scene = None

    # -------------------------------------------------------- link records and sizes
    def rec(self, lid, size=None):
        r = self.byid[lid]
        if size in (None, r['circuits']):
            return r
        if (lid, size) not in self.recs26:
            z = lg.fh12_size(size, self.ctx.gopts)
            rec = lg.link_record(self.ctx, lid, r['joint'], r['front_board'], r['members'], self.site_by, z)
            for k in ('centre', 'riders_in'):
                rec[k] = copy.deepcopy(r.get(k, []))
            rec['placed'] = True
            self.recs26[(lid, size)] = rec
        return self.recs26[(lid, size)]

    def size_of(self, rec):
        return lg.rec_size(self.ctx, rec)

    # -------------------------------------------------------- the rules of stage 1
    def rule2(self, lid, geo, size=None):
        a = self.with_rec(lid, size, lambda: self.arm1.accept_for(lid, ()))
        return a(geo)

    def rule4(self, lid, geo, size=None):
        a = self.with_rec(lid, size, lambda: self.arm1a2.accept_for(lid, ()))
        why = a(geo)
        return why if why and why.startswith('covers the recorded courtyard') else None

    def with_rec(self, lid, size, fn):
        r = self.rec(lid, size)
        old = self.s.byid[lid]
        self.s.byid[lid] = r
        try:
            return fn()
        finally:
            self.s.byid[lid] = old

    def t1(self, lid, geo, size=None):
        """(violations [(ref, class)], anchored-covered [(board, ref, anchors)]) of preflight T1."""
        front = self.byid[lid]['front_board']
        d = lg.displaced(self.model, front, geo, self.ctx.latch)
        bad, anch = [], []
        for k, refs in d.items():
            b = front if k == 'front B' else 'K'
            for ref in refs:
                key = (b, ref)
                if key not in self.protected:
                    continue
                if self.anchor.get(key):
                    anch.append((b, ref, sorted(self.anchor[key])))
                else:
                    bad.append((ref, 'S' if self.searched_disp.get(key) else 'N'))
        return sorted(set(bad)), sorted({(b, r, tuple(a)) for b, r, a in anch})

    def t2(self, lid, geo):
        """Anchored protected footprints whose base row courtyard (grown on its face) a rectangle of the link meets."""
        front = self.byid[lid]['front_board']
        rects = sm.link_rects(geo, front, self.latch_field)
        hits = []
        for key in sorted(self.anchor):
            if key not in self.protected:
                continue
            row = self.base_rows.get(key)
            if not row or row['new'] is None:
                continue
            g = sg.grow(row['new_courtyard'], self.gap)
            for b, f, rect, what in rects:
                if b == key[0] and f == row['new_face'] and sg.inter(g, rect):
                    hits.append((key[0], key[1], what))
                    break
        return hits

    def tails(self, lid, geo):
        front = self.byid[lid]['front_board']
        ut = sm.links.under_tails(self.model, front, geo) if hasattr(sm, 'links') else None
        if ut is None:
            import links as _links
            ut = _links.under_tails(self.model, front, geo)
        out = [(front, x, 'front tail') for x in ut['front tail']] + [('K', x, 'K tail') for x in ut['K tail']]
        return sorted({(b, x, w) for b, x, w in out if (b, x) in self.protected})

    def check_rules(self, lid, geo, dist, size=None):
        """Rules 2 to 6 for one candidate geometry: (first failing rule number or None, reason, extra)."""
        why = self.rule2(lid, geo, size)
        if why:
            return 2, why, None
        if dist > RADIUS + 1e-9:
            return 3, 'slot centre %.4f mm from the search centre, beyond %.1f mm' % (dist, RADIUS), None
        why = self.rule4(lid, geo, size)
        if why:
            return 4, why, None
        bad, anch = self.t1(lid, geo, size)
        if bad:
            return 5, 'T1: ' + ', '.join('%s (%s)' % x for x in bad), bad
        hits = self.t2(lid, geo)
        if hits:
            return 6, 'T2: ' + ', '.join('%s %s under %s' % h for h in hits), hits
        return None, None, anch

    # -------------------------------------------------------- scenes
    def scene_links(self, moves):
        """The link list of a scene. `moves`: lid -> {'geometry', 'slot_centre', 'direction', 'size'}."""
        out = []
        for r in self.base_out:
            m = moves.get(r['id'])
            if m is None or m.get('stay'):
                out.append(r)
                continue
            rec = dict(self.rec(r['id'], m.get('size')))
            front = rec['front_board']
            geo = m['geometry']
            rec.update({'geometry': geo, 'slot_centre': list(m['slot_centre']), 'direction': m['direction'],
                        'displaced': lg.displaced(self.model, front, geo, self.ctx.latch)})
            out.append(rec)
        return out

    def rows_only(self, links_out):
        rows = p2.replace_all(self.ctx, self.inp, links_out)
        return rows

    def placed_index(self, moves, skip=()):
        """links.Placed with every live link at its scene geometry, except `skip`."""
        live = p2.live(self.scene_links(moves))
        return lg.placed_index(live, skip=skip)


def protected_set(s):
    """Ruling 4: every footprint with a pin on a *_FB, *_SUM or *_SENSE net, and every IC with a unit whose role starts
    high_impedance_input or remote_buffer (io-partition package_units). Returns {(board, ref)}."""
    refs = set()
    for u in s.io_units:
        if any(n and n.endswith(STOP_SUFFIX) for n in u['pins'].values()):
            refs.add(u['ref'])
        if (u.get('role') or '').startswith(('high_impedance_input', 'remote_buffer')) and u['ref'].startswith('U'):
            refs.add(u['ref'])
    return {k for k in s.fps if k[1] in refs}


def protected_counts(w):
    by = defaultdict(int)
    for b, _ in w.protected:
        by[b] += 1
    rows = [k for k in w.base_rows if k in w.protected]
    by_row = defaultdict(int)
    for b, _ in rows:
        by_row[b] += 1
    return {'total': len(w.protected), 'by_board': dict(sorted(by.items())), 'with_base_row': len(rows),
            'with_base_row_by_board': dict(sorted(by_row.items())),
            'positionless_base_rows': sorted(k[1] for k in rows if w.base_rows[k]['new'] is None)}


# ---------------------------------------------------------------- base tables (P1)

def base_tables(w):
    links_t, ics_t, bad = {}, {}, []
    for lid in SEARCHED:
        r = w.byid[lid]
        links_t[lid] = {'centre': r['centre'], 'slot_centre': r['slot_centre'], 'direction': r['direction'], 'size': r['size'],
                        'cable': r['cable'], 'cable_length_mm': r['cable_length_mm'], 'circuits_needed': r['circuits_needed'],
                        'circuits': r['circuits'], 'members': r['members'],
                        'riders': [(y['net'], y['class']) for y in r.get('riders_in', [])]}
        c, sl, d, size, cab, L, need, n = BASE_LINKS[lid]
        if [round(v, 4) for v in r['centre']] != list(c) or [round(v, 4) for v in r['slot_centre']] != list(sl) or \
                r['direction'] != d or r['size'] != size or r['cable'] != cab or r['cable_length_mm'] != L or \
                r['circuits_needed'] != need or r['circuits'] != n:
            bad.append('link %s differs from the brief table' % lid)
    live = p2.live(w.base_out)
    for ic, (pose, face, cy, meets) in BASE_ICS.items():
        fp = w.s.fps[('K', ic)]
        got = {}
        for r in live:
            if not r['placed']:
                continue
            for b, f, rect, what in sm.link_rects(r['geometry'], r['front_board'], w.latch_field):
                if b == "K" and f == fp["side"] and sg.inter(sg.grow(fp["courtyard"], w.gap), rect):
                    got.setdefault(r['id'], set()).add(what)
        ics_t[ic] = {'paper': [round(v, 2) for v in fp['origin']], 'face': fp['side'], 'courtyard': fp['courtyard'],
                     'links_on_it': {k: sorted(v) for k, v in sorted(got.items())}}
        if [round(v, 2) for v in fp['origin']] != [round(v, 2) for v in pose] or fp['side'] != face or \
                [round(v, 2) for v in fp['courtyard']] != cy or {k: v for k, v in got.items()} != meets:
            bad.append('IC %s differs from the brief table: %s' % (ic, ics_t[ic]))
    counts = {'records': len(w.base_out), 'live': len(live), 'dissolved': sum(1 for r in w.base_out if r.get('gone')),
              'holds': [h['link'] for h in lg.slot_holds(w.ctx.gopts)],
              'L03.02.02.01 dissolved': bool(w.byid.get('P-K-P-L03.02.02.01', {}).get('gone'))}
    if (counts['records'], counts['live'], counts['dissolved'], counts['holds']) != (72, 62, 10, ['JL-K-JL-L02']) or \
            not counts['L03.02.02.01 dissolved']:
        bad.append('link record counts differ: %s' % counts)
    return {'links': links_t, 'ics': ics_t, 'counts': counts}, bad


def must_move(w, ics):
    """Links whose base rectangles meet the courtyard of an IC in `ics` (recomputed)."""
    live = p2.live(w.base_out)
    out = set()
    for ic in ics:
        fp = w.s.fps[('K', ic)]
        for r in live:
            if r['placed'] and any(b == 'K' and f == fp['side'] and sg.inter(sg.grow(fp['courtyard'], w.gap), rect)
                                   for b, f, rect, _ in sm.link_rects(r['geometry'], r['front_board'], w.latch_field)):
                out.add(r['id'])
    return out


# ---------------------------------------------------------------- the scene checker

def rowmap(rows):
    return {(r['board'], r['ref']): r for r in rows}


def rowsig(r):
    return (r['new'], r['new_face'], r['turned'])


def row_changes(ra, rb):
    removed = sorted(set(ra) - set(rb))
    new = sorted(set(rb) - set(ra))
    shifted = sorted(k for k in set(ra) & set(rb) if rowsig(ra[k]) != rowsig(rb[k]))
    return removed, new, shifted


def check_rows(w, rows, claim_ok=True):
    """A1 to A4 and A6 on one scene's rows. Returns ({item: [failures]}, info)."""
    ra, rb = w.base_rows, rowmap(rows)
    removed, new, shifted = row_changes(ra, rb)
    fails = defaultdict(list)
    s = w.s
    claimed = [ic for ic in FIVE if ('K', ic) not in rb]
    for ic in FIVE:
        k = ('K', ic)
        if k in rb and rb[k] != ra.get(k):
            fails['A1'].append('%s is not claimed and its row differs from the base row' % ic)
    prot = {'new': [], 'shifted': [], 'returned': [], 'lost_position': []}
    for k in sorted(w.protected):
        a, b = ra.get(k), rb.get(k)
        if b is None:
            if a is not None:
                prot['returned'].append(k)
            continue
        if a is None:
            prot['new'].append(k)
            fails['A2'].append('%s %s: new protected row (%s)' % (k[0], k[1], 'no position' if b['new'] is None else b['step']))
        elif rowsig(a) != rowsig(b):
            if b['new'] is None:
                prot['lost_position'].append(k)
                fails['A2'].append('%s %s: protected footprint loses its base position' % k)
            else:
                prot['shifted'].append(k)
                fails['A2'].append('%s %s: shifted or turned protected row' % k)
    for k, b in rb.items():
        a = ra.get(k)
        if b['new'] is None and (a is None or a['new'] is not None):
            fails['A3'].append('%s %s: %s without a position' % (k[0], k[1], 'new row' if a is None else 'row'))
    for k in new + shifted:
        ref = k[1]
        if not ref.startswith('RV'):
            continue
        b = rb[k]
        paper_face = s.fps[k]['side']
        before_face = ra[k]['new_face'] if k in ra and ra[k]['new'] is not None else paper_face
        if b['new_face'] is not None and b['new_face'] != paper_face:
            fails['A4'].append('%s %s: trimmer row changes face from paper %s to %s' % (k[0], ref, paper_face, b['new_face']))
        if k[0] == 'K' and b['new_face'] == 'F' and before_face != 'F':
            fails['A4'].append('%s %s: trimmer newly lands on K front face' % k)
    for board in UNTOUCHED:
        a = sorted((canon(r) for kk, r in ra.items() if kk[0] == board))
        b = sorted((canon(r) for kk, r in rb.items() if kk[0] == board))
        if a != b:
            fails['A6'].append('rows on %s differ from the base' % board)
    info = {'claimed': claimed, 'counts': {'removed': len(removed), 'new': len(new), 'shifted': len(shifted)},
            'protected': {k: ['%s %s' % x for x in v] for k, v in prot.items()},
            'removed': removed, 'new': new, 'shifted': shifted}
    return dict(fails), info


def link_figures(w, lid, m):
    """A5: the link's figures against their limits."""
    if m.get('stay'):
        return {'stay': True}, []
    rec = w.rec(lid, m.get('size'))
    fig = w.with_rec(lid, m.get('size'), lambda: w.arm1.figures(lid, m['geometry']))
    fails = []
    mv = fig['moved']
    if mv['loop_mm'] < -1e-9:
        fails.append('%s loop %.4f mm < 0' % (lid, mv['loop_mm']))
    if not fig['compliance_within_limit']:
        fails.append('%s K-field compliance above the limit' % lid)
    for x in fig['riders'] + fig['members']:
        if x['moved_mm'] > x['limit_mm'] + 1e-9:
            fails.append('%s %s beyond its class distance' % (lid, x.get('net') or x.get('site')))
    c = rec['centre']
    dist = math.hypot(m['slot_centre'][0] - c[0], m['slot_centre'][1] - c[1])
    if dist > RADIUS + 1e-9:
        fails.append('%s slot beyond %.1f mm' % (lid, RADIUS))
    fig.update({'slot_distance_from_centre_mm': round(dist, 4), 'ring': ring_of(dist),
                'direction_change': None if m['direction'] == w.byid[lid]['direction'] else
                [w.byid[lid]['direction'], m['direction']], 'size': rec['size'], 'circuits': rec['circuits'],
                'cable': rec['cable'], 'cable_length_mm': rec['cable_length_mm']})
    return fig, fails


def ring_of(d):
    return '≤ 24 mm' if d <= INNER + 1e-9 else '24–35 mm'


def eff_turns_list(scene_turns):
    return scene_turns


def judge(w, moves, rows, overlay_blocks=None, run_overlay_search=True):
    """A1 to A11 on one scene (rows from the rows-only replay). `overlay_blocks`: fixed overlay placements (P6) instead
    of the A8 search. Returns a dict with per-item failures and the ledgers."""
    s = w.s
    fails, info = check_rows(w, rows)
    fails = defaultdict(list, fails)
    figs = {}
    for lid, m in sorted(moves.items()):
        f, bad = link_figures(w, lid, m)
        figs[lid] = f
        fails['A5'] += bad
    ra, rb = w.base_rows, rowmap(rows)
    scene_out = w.scene_links(moves)
    old_rows, old_out = s.rows, s.out
    s.rows, s.out = rb, scene_out
    try:
        res = overlay_part(w, ra, rb, info, fails, overlay_blocks, run_overlay_search)
    finally:
        s.rows, s.out = old_rows, old_out
    res.update({'fails': {k: v for k, v in sorted(fails.items()) if v}, 'rows': info, 'link_figures': figs})
    res['passes'] = {a: not fails.get(a) for a in ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11')}
    return res


def base_effective(w):
    if w._base_scene is None:
        s = w.s
        ra = w.base_rows
        old = s.rows
        s.rows = ra
        try:
            w._base_scene = (ov.effective_scene(s, ra, w.retained), ov.effective_turns(ra, w.retained))
        finally:
            s.rows = old
    return w._base_scene


def overlay_part(w, ra, rb, info, fails, overlay_blocks, run_search):
    """A7 to A11 with s.rows / s.out set to the scene (the DS-148 overlay rules of overlay.py)."""
    s = w.s
    before, before_turns = base_effective(w)
    new, shifted = info['new'], info['shifted']
    dec_of = defaultdict(list)
    for ref, p in s.pk.items():
        if p.get('decouples_ref'):
            dec_of[p['decouples_ref']].append(ref)
    current_retained = [e for e in w.retained if (e['board'], e['ic']) in rb and rb[e['board'], e['ic']]['new'] is None]
    mid = ov.effective_scene(s, rb, current_retained)
    touched = sorted({k for k in new + shifted if k[1].startswith('U')} |
                     {(k[0], s.pk[k[1]]['decouples_ref']) for k in new + shifted if s.pk.get(k[1], {}).get('decouples_ref')})
    rule, need = [], []
    for key in touched:
        if key not in s.fps:
            continue
        b, ic = key
        io0, if0, _ = before[key]
        io1, if1, _ = mid[key]
        decs = []
        for d in sorted(dec_of.get(ic, [])):
            dk = (b, d)
            if dk not in s.fps:
                continue
            o0, f0, _ = before[dk]
            o1, f1, _ = mid[dk]
            if None in (o0, o1, io0, io1):
                decs.append({'ref': d, 'unavailable': 'no position'})
                continue
            d0, d1 = math.dist(o0, io0), math.dist(o1, io1)
            decs.append({'ref': d, 'face_before': f0, 'face_after': f1, 'distance_before_mm': d0, 'distance_after_mm': d1,
                         'other_face_after': f1 != if1, 'farther': d1 > d0 + 1e-9})
        breaks = [d for d in decs if d.get('unavailable') or d['other_face_after'] or d['farther']]
        own = key in set(new) | set(shifted)
        kind = 'holds' if not breaks else ('overlay pose (searched)' if own and rb[key]['new'] is not None else 'knock-on break')
        rule.append({'board': b, 'ic': ic, 'ic_row': 'new' if key in new else 'shifted' if key in shifted else 'unchanged',
                     'decouplers': decs, 'block_rule': kind})
        if kind == 'knock-on break':
            fails['A8'].append('%s %s: a decoupler row breaks the block rule while the IC row is unchanged '
                               '(stricter reading: no knock-on exemption)' % key)
        elif kind.startswith('overlay'):
            need.append(key)
    blocks = []
    if overlay_blocks is not None:
        blocks = copy.deepcopy(overlay_blocks)
    elif need and run_search:
        members = {}
        for key in need:
            dec, local, _ = s.block(*key)
            members[key] = [key[1]] + dec + local
        lifted = {(b, m) for (b, ic), ms in members.items() for m in ms}
        for key in need:
            b, ic = key
            f = s.build_field(extra=lifted)
            for e in blocks:
                s.place(f, e['board'], e['ic'], e['members'], s.fps[(e['board'], e['ic'])]['side'], e['pose'])
                for m in e['passives_moved']:
                    s.add_part(f, e['board'], m)
            s.members[key] = members[key]
            try:
                legal, disp, _ = s.search(f, b, ic)
            finally:
                if key not in {(i['board'], i['ref']) for i in s.items}:
                    s.members.pop(key, None)
            best = legal[0] if legal else None
            e = {'board': b, 'ic': ic, 'members': members[key]}
            if best and best['moved_mm'] <= rp.LIMIT_MM:
                e.update({'pose': {k: best[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')}, 'passives_moved': []})
            elif disp:
                e.update({'pose': {k: disp[k] for k in ('face', 'turn_deg', 'origin', 'moved_mm', 'shift_mm')},
                          'passives_moved': disp['displaced_moves']})
            else:
                fails['A8'].append('%s %s: no S8 block pose within 24 mm (nearest %s mm)' % (b, ic, best and best['moved_mm']))
                e.update({'pose': None, 'passives_moved': []})
            blocks.append(e)
    elif need:
        fails['A8'].append('overlay search not run for %s' % need)
    stop = []
    if blocks:
        ov.candidate_clearance(s, blocks, stop)
        for x in stop:
            fails['A8'].append(x)
    after = ov.effective_scene(s, rb, current_retained + blocks)
    rotations = ov.effective_turns(rb, current_retained + blocks)
    ledger = ov.movement(s, before, after, before_turns, rotations)
    # A10: protected footprints in the effective scene
    overlay_refs = {(e['board'], m) for e in blocks for m in e['members']} | \
        {(e['board'], m['ref']) for e in blocks for m in e['passives_moved']}
    prot_ledger = {'returned_to_paper': [], 'overlay_moved': [], 'differs': []}
    for k in sorted(w.protected):
        a, b = before[k], after[k]
        ta, tb = before_turns.get(k, 0), rotations.get(k, 0)
        same = (a[0] == b[0] or (a[0] is not None and b[0] is not None and math.dist(a[0], b[0]) < 1e-9)) and a[1] == b[1] and ta == tb
        if same:
            continue
        paper = s.fps[k]
        if b[2] == 'paper' and b[1] == paper['side'] and tb == 0:
            prot_ledger['returned_to_paper'].append('%s %s' % k)
            continue
        tag = 'overlay_moved' if k in overlay_refs else 'differs'
        prot_ledger[tag].append('%s %s' % k)
        fails['A10'].append('%s %s: effective pose differs from its base effective pose (%s)' % (k[0], k[1], tag))
    # A7: the ten link-era poses in the Field built from the scene rows
    a7 = []
    for board, ic, members, face0, pose in s.confirmed_blocks():
        a7.append(check_block(s, board, ic, members, face0, pose, []))
    for board, ic, members, face0, pose, passives, _ in s.done:
        a7.append(check_block(s, board, ic, members, face0, pose, passives))
    for x in a7:
        if not x['all_clear']:
            fails['A7'].append('link-era pose of %s %s is not legal in the scene Field' % (x['board'], x['ic']))
    # A9: placed ICs' blocks
    a9 = []
    for ic in info['claimed']:
        key = ('K', ic)
        ms = s.members.get(key) or ([ic] + s.block('K', ic)[0] + s.block('K', ic)[1])
        io = s.fps[key]['origin']
        for m in ms[1:]:
            mk = ('K', m)
            pos, face, src = after[mk]
            if src == 'paper':
                continue
            isdec = s.pk.get(m, {}).get('decouples_ref') == ic
            ok = isdec and pos is not None and face == s.fps[key]['side'] and \
                math.dist(pos, io) <= math.dist(s.fps[mk]['origin'], io) + 1e-9
            a9.append({'ic': ic, 'ref': m, 'source': src, 'ok': ok})
            if not ok:
                fails['A9'].append('%s block member %s is not at paper (%s)' % (ic, m, src))
    for k in sorted(set(new) | set(shifted)):
        kind = sa2.buffer_kind(s, k)
        if kind and kind[0] == 'r_iso':
            amps = sorted(r for r in s.net_refs[kind[1]] if r.startswith('U') and (k[0], r) in s.fps)
            ak = (k[0], amps[0])
            if None in (after[k][0], after[ak][0], before[k][0], before[ak][0]):
                fails['A9'].append('R_ISO %s: no position' % k[1])
                continue
            d0, d1 = math.dist(before[k][0], before[ak][0]), math.dist(after[k][0], after[ak][0])
            a9.append({'r_iso': k[1], 'op_amp': amps[0], 'before_mm': d0, 'after_mm': d1, 'ok': d1 <= d0 + 1e-9})
            if d1 > d0 + 1e-9:
                fails['A9'].append('R_ISO %s farther from %s than at the base' % (k[1], amps[0]))
    loc = locality_table(w, after, rotations)
    for x in loc['figures']:
        if x['verdict'] == 'ABOVE LIMIT':
            fails['A11'].append('%s %s: %s above its limit %s' % (x['entry'], x['figure'], x['scene'], x['limit']))
    return {'block_rule': rule, 'overlay_blocks': blocks, 'effective_movements': ledger,
            'face_changes': [r for r in ledger if r['from'] and r['to'] and r['from'] != r['to']],
            'protected_effective': prot_ledger, 'link_era_poses': a7, 'placed_ic_blocks': a9, 'locality': loc}


def check_block(s, board, ic, members, face0, pose, passives):
    f = s.build_field(extra={(board, m['ref']) for m in passives}, skip={(board, ic)})
    bad = []
    for ref, face, rect in mfc.block_rects(s, board, ic, members, face0, pose):
        why = f.blocked(board, face, rect, [])
        if why:
            bad.append({'ref': ref, 'blocked_by': why})
    for ref, face, rect in mfc.block_rects(s, board, ic, members, face0, pose):
        f.add(board, face, rect, [], ref)
    pas = []
    for m in passives:
        why = f.blocked(board, m['face'], mfc.part_rect(s, board, m), [])
        if why:
            pas.append({'ref': m['ref'], 'blocked_by': why})
        f.add(board, m['face'], mfc.part_rect(s, board, m), [], m['ref'])
    return {'board': board, 'ic': ic, 'blocked_members': bad, 'blocked_passives': pas, 'all_clear': not bad and not pas}


# ---------------------------------------------------------------- locality (Ruling 1)

class _Unrounded:
    """Temporarily replaces `round` in the overlay module so its figures come out unrounded (reported beside)."""

    def __enter__(self):
        self.had = 'round' in ov.__dict__
        ov.round = lambda v, n=None: v
        return self

    def __exit__(self, *e):
        if not self.had:
            del ov.round
        return False


def _figures(w, entry, scene, rotations):
    s = w.s
    original = w.original
    loc = ov.locality(entry, original, scene) if 'study_pose' not in entry else None
    figs, unavailable = ov.ancillary_geometry(s, entry, scene, original, rotations, s.fps)
    out = {}
    if loc:
        out['distance_mm'] = loc['distance_mm_recomputed']
        out['effective_pose'] = loc['effective_pose']
    for k, v in figs.items():
        out[k] = v['recomputed']
    return out, unavailable


def flatten(prefix, v):
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            out.update(flatten('%s.%s' % (prefix, k), x))
        return out
    return {prefix: v}


def locality_table(w, scene, rotations):
    """Every figure of the 16 entries: accepted, base, scene, limit and label (Ruling 1)."""
    if not hasattr(w, 'original'):
        w.original = {(p['board'], p['ref']): p for p in gjson(PAPER, 'design/partition/floorplan-candidate.json')['placements']}
        w.locality_doc = json.loads((w.s.root / LOCALITY).read_text())
        w.loc_base = {}
    before, bt = base_effective(w)
    rows = []
    for i, x in enumerate(w.locality_doc['acceptances']):
        if 'ref' not in x:
            continue
        tag = '%s %s #%d' % (x.get('board', 'K'), x['ref'], i)
        if tag not in w.loc_base:
            b, _ = _figures(w, x, before, bt)
            with _Unrounded():
                bu, _ = _figures(w, x, before, bt)
            rec, _ = ov.ancillary_geometry(w.s, x, before, w.original, bt, w.s.fps)
            recorded = {k: v['recorded'] for k, v in rec.items()}
            if 'distance_mm' in b:
                recorded['distance_mm'] = x.get('distance_mm')
            w.loc_base[tag] = (b, bu, recorded)
        b, bu, recorded = w.loc_base[tag]
        sc, unavail = _figures(w, x, scene, rotations)
        with _Unrounded():
            su, _ = _figures(w, x, scene, rotations)
        fb, fbu, fs, fsu, fr = (flatten('', v) for v in (b, bu, sc, su, recorded))
        for label in sorted(fb):
            name = label[1:]
            if name.startswith('effective_pose'):
                continue
            base_v, scene_v, acc = fb[label], fs.get(label), fr.get(label)
            row = {'entry': tag, 'figure': name, 'accepted': acc, 'base': base_v, 'base_unrounded': fbu.get(label),
                   'scene': scene_v, 'scene_unrounded': fsu.get(label)}
            numeric = all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (base_v, scene_v)) and \
                not name.endswith(('turn_deg', '.face'))
            if numeric:
                lim = max(base_v, acc) if isinstance(acc, (int, float)) and not isinstance(acc, bool) else base_v
                row['limit'] = lim
                row['label'] = 'INHERITED EXCESS, UNRULED' if isinstance(acc, (int, float)) and base_v > acc + 1e-12 else None
                row['verdict'] = 'ABOVE LIMIT' if scene_v > lim + 1e-12 else 'within'
            else:
                row['limit'] = 'equal to base'
                row['label'] = None
                row['verdict'] = 'within' if scene_v == base_v else 'ABOVE LIMIT'
            rows.append(row)
        if unavail:
            rows.append({'entry': tag, 'figure': 'unavailable', 'scene': unavail, 'verdict': 'ABOVE LIMIT',
                         'limit': None, 'label': None, 'accepted': None, 'base': None})
    return {'figures': rows, 'inherited_excess': sorted({(r['entry'], r['figure']) for r in rows if r.get('label')}),
            'above_limit': [r for r in rows if r['verdict'] == 'ABOVE LIMIT']}


# ---------------------------------------------------------------- full gate replay

def full_replay(holds=None, extra_holds=()):
    """links_gate.gate_run then links_gate_part2.run in a scratch root whose options carry `holds` (replacing the
    base list when given). Returns (doc, files read in the working tree)."""
    gopts = gjson(BASE, GOPTS)
    if holds is not None:
        gopts = copy.deepcopy(gopts)
        gopts['slot_holds']['value'] = list(holds) + list(extra_holds)
    root = scratch_root(gopts if holds is not None else None, 'gate')
    try:
        with ReadLog() as rl:
            inp = lg.load_inputs(root)
            sites, model, ctx, out, s1, _ = lg.gate_run(inp, {})
            part2 = p2.run(ctx, inp, out, {x['id']: x for x in sites})
            errs = lg.hold_errors(inp['gopts'], out)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    return {'links': out, 'ways_out': part2['ways_out'], 'consolidation': part2['consolidation'],
            'replacement': part2['replacement'], 'hold_errors': errs}, sorted(rl.paths)


LINK_KEYS = ('centre', 'slot_centre', 'direction', 'geometry', 'size', 'members')


def compare_links(a_links, b_links, keys=LINK_KEYS):
    A = {r['id']: r for r in a_links}
    B = {r['id']: r for r in b_links}
    diffs = []
    for i in sorted(set(A) | set(B)):
        if i not in A or i not in B:
            diffs.append('%s only in %s' % (i, 'replay' if i in A else 'base'))
            continue
        if bool(A[i].get('gone')) != bool(B[i].get('gone')) or bool(A[i].get('placed')) != bool(B[i].get('placed')):
            diffs.append('%s gone/placed differs' % i)
            continue
        for k in keys:
            if A[i].get(k) != B[i].get(k):
                diffs.append('%s %s differs' % (i, k))
    return diffs


def hold_entry(w, lid, m, why):
    r = w.byid[lid]
    sc = r['slot_centre'] if m.get('stay') else m['slot_centre']
    d = r['direction'] if m.get('stay') else m['direction']
    return {'link': lid, 'front_board': r['front_board'], 'centre': r['centre'], 'slot_centre': [round(v, 4) for v in sc],
            'direction': d, 'reason': why, 'ruling': 'MC04-S12 study scratch hold (candidate data, not an options entry)'}


# ---------------------------------------------------------------- stage 1: the census of one link and grid

def spot_of(sx, sy, d):
    return (d, math.floor(sx / 2.0 + 1e-9), math.floor(sy / 2.0 + 1e-9))


def census(w, lid, grid, size=None, memo_every=4000, deadline=None):
    """Every candidate of one link on one grid within 35 mm (rule 1 as links_gate.search evaluates it, every other
    searched link out of `placed`), then rules 2 to 6 in order. Returns (counts, accepted candidates)."""
    ctx = w.ctx
    rec = w.rec(lid, size)
    front, centre, own = rec['front_board'], rec['centre'], lg.rec_own(rec)
    z = w.size_of(rec)
    placed = w.placed_index({}, skip=SEARCHED)
    spare = ctx.spare(front, z)
    gm = lg.GeoMaker(z, ctx.opts, ctx.hard)
    offsets = ctx.grid(grid, radius=RADIUS)
    counts = {'offsets': len(offsets), 'evaluated': 0,
              'legal_rule1': {'≤ 24 mm': 0, '24–35 mm': 0},
              'after_rule': {str(n): {'≤ 24 mm': 0, '24–35 mm': 0} for n in (2, 3, 4, 5, 6)},
              'rejections_rule1': {}, 'rejections_by_rule': {str(n): {} for n in (2, 3, 4, 5, 6)},
              't1_by_class': {'N': 0, 'S': 0}, 't1_by_footprint': {}, 'rejected_for_class_S_alone': 0,
              'complete': True}
    acc = []
    ctx.model.memo_for(None)
    for i, off in enumerate(offsets):
        if deadline is not None and time.time() > deadline:
            counts['complete'] = False
            break
        if i % memo_every == 0:
            ctx.model.memo_for(None)
        dist = math.hypot(*off)
        ring = ring_of(dist)
        sx, sy = lg.r4(centre[0] + off[0]), lg.r4(centre[1] + off[1])
        for di, d in enumerate(lg.DIRS):
            counts['evaluated'] += 1
            why, c = lg.candidate(ctx, placed, front, z, own, sx, sy, d, dist, spare, True, gm)
            if why:
                k = why[0]
                counts['rejections_rule1'][k] = counts['rejections_rule1'].get(k, 0) + 1
                continue
            counts['legal_rule1'][ring] += 1
            cost, geo, disp = c
            rule, reason, extra = w.check_rules(lid, geo, dist, size)
            if rule is not None:
                t = counts['rejections_by_rule'][str(rule)]
                key = reason if rule in (2, 3, 4) else 'T1' if rule == 5 else 'T2'
                t[key] = t.get(key, 0) + 1
                if rule == 5:
                    classes = {c2 for _, c2 in extra}
                    for cl in classes:
                        counts['t1_by_class'][cl] += 1
                    if classes == {'S'}:
                        counts['rejected_for_class_S_alone'] += 1
                    for ref, cl in extra:
                        e = counts['t1_by_footprint'].setdefault(ref, {'class': cl, 'candidates': 0})
                        e['candidates'] += 1
                if rule == 6:
                    for b, ref, what in extra:
                        k2 = 'T2 ' + ref
                        t[k2] = t.get(k2, 0) + 1
            for n in (2, 3, 4, 5, 6):
                if rule is None or rule > n:
                    counts['after_rule'][str(n)][ring] += 1
            if rule is None:
                key = (round(cost, 6), round(dist, 6), di, geo['front_extension_mm'], geo['K_extension_mm'], sx, sy)
                acc.append({'cost': cost, 'key': list(key), 'geometry': geo, 'direction': lg.DIR_NAMES[d],
                            'slot_centre': [sx, sy], 'dist': dist, 'ring': ring, 'grid_mm': grid, 'size': rec['circuits'],
                            'spot': list(spot_of(sx, sy, lg.DIR_NAMES[d])), 'anchored_covered': [list(x) for x in extra],
                            'tails': [list(x) for x in w.tails(lid, geo)]})
    ctx.model.memo_for(None)
    acc.sort(key=lambda c: c['key'])
    return counts, acc
