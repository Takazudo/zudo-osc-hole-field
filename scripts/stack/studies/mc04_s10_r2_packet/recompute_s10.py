#!/usr/bin/env python3
"""Read-only independent recomputation for the MC04-S10 Revision 2 decision packet.

Reads git objects (git show) and the working-tree interim board files; writes nothing in the repository.
Own board parser (regex), own scene builder; shares only the *definitions* stated in the retained records:
  scene = interim-board pose, overridden by link-gate `replacement` rows, overridden by link-era block poses
  run estimate = 1.5 x HPWL, 0.20 pF/mm (run_estimate_basis in locality-acceptances.json)
Output: JSON on stdout."""
import json, math, re, subprocess, hashlib, sys
import os as _os
REPO = _os.environ.get('OSC_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[4])
BASE = '6e5716e7fc011e2f028982f645d18b8d802acb29'
CAND = '32580f77c9d0aa9c6067cbad965a6f701050ca5d'
HEADC = '557b5a6e92e2600fcb4319bd8528c4f5812d3177'
PAPER = '6093081cc6d1fcbfc4e134e4dfa1861a3de39836'
BOARDS = {'K': 'boards/osc-core/osc-core.kicad_pcb', 'JL': 'boards/osc-jack-left/osc-jack-left.kicad_pcb',
          'JR': 'boards/osc-jack-right/osc-jack-right.kicad_pcb'}
RF, PF = 1.5, 0.20
hashes = {}

def show(rev, path):
    b = subprocess.check_output(['git', '-C', REPO, 'show', f'{rev}:{path}'])
    hashes[f'{rev[:8]}:{path}'] = hashlib.sha256(b).hexdigest()
    return json.loads(b)

def parse_board(path):
    raw = open(f'{REPO}/{path}', 'rb').read()
    hashes['worktree:' + path] = hashlib.sha256(raw).hexdigest()
    txt = raw.decode()
    out = {}
    for m in re.finditer(r'\n\t\(footprint "([^"]+)"', txt):
        end = txt.find('\n\t)\n', m.end())
        blk = txt[m.start():end]
        r = re.search(r'\(property "Reference" "([^"]+)"', blk)
        at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
        lay = re.search(r'\n\t\t\(layer "([^"]+)"\)', blk)
        if not (r and at and lay):
            continue
        ox, oy, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
        a = math.radians(rot)
        pads = {}
        for p in re.finditer(r'\n\t\t\(pad "([^"]*)" \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+)', blk):
            px, py = float(p.group(2)), float(p.group(3))
            pads.setdefault(p.group(1), (round(ox + px * math.cos(a) + py * math.sin(a) - 100, 4),
                                         round(oy - px * math.sin(a) + py * math.cos(a) - 50, 4)))
        out[r.group(1)] = {'origin': (round(ox - 100, 4), round(oy - 50, 4)), 'side': lay.group(1)[0], 'pads': pads}
    return out

fps = {b: parse_board(p) for b, p in BOARDS.items()}
io = show(BASE, 'design/reports/io-partition.json')
pins = {}
for u in io['package_units']:
    pins.setdefault(u['ref'], {}).update(u['pins'])
pk = {p['ref']: p for p in io['physical_packages']}
net_pins = {}
for ref, ps in pins.items():
    for pin, n in ps.items():
        if n:
            net_pins.setdefault(n, []).append((ref, pin))
board_of = {ref: b for b in fps for ref in fps[b]}

def rot(pt, o, deg):
    x, y = pt
    for _ in range(int(deg) // 90):
        x, y = o[0] - (y - o[1]), o[1] + (x - o[0])
    return x, y

def scene(gate, placed):
    """ref -> (origin|None, face, source, turn)"""
    sc = {(b, r): (f['origin'], f['side'], 'board', 0) for b in fps for r, f in fps[b].items()}
    for row in gate['replacement']['footprints']:
        k = (row['board'], row['ref'])
        if k in sc:
            sc[k] = (tuple(row['new']) if row['new'] else None, row['new_face'], 'gate row', 90 if row['turned'] else 0)
    def place(b, ic, members, pose):
        o = fps[b][ic]['origin']
        for ref in members:
            p = fps[b][ref]['origin']
            if pose['face'] != fps[b][ic]['side']:
                p = (2 * o[0] - p[0], p[1])
            x, y = rot(p, o, pose['turn_deg'])
            same = fps[b][ref]['side'] == fps[b][ic]['side']
            face = pose['face'] if same else {'F': 'B', 'B': 'F'}[pose['face']]
            sc[b, ref] = ((x + pose['shift_mm'][0], y + pose['shift_mm'][1]), face, ic + ' block', pose['turn_deg'])
    for e in placed:
        if not e.get('pose'):
            continue
        b = e['board']
        place(b, e['ic'], e.get('members') or e['block'], e['pose'])
        for nb in e.get('blocks_moved', []):
            place(b, nb['ic'], nb['members'], nb)
        for m in e['passives_moved']:
            sc[b, m['ref']] = (tuple(m['origin']), m['face'], e['ic'] + ' displaced passive', 0)
    return sc

def pad(sc, ref, pin):
    b = board_of[ref]
    f = fps[b][ref]
    pos, face, _, turn = sc[b, ref]
    if pos is None:
        return None
    px, py = f['pads'][pin]
    dx, dy = px - f['origin'][0], py - f['origin'][1]
    if face != f['side']:
        dx = -dx
    dx, dy = rot((dx, dy), (0, 0), turn)
    return (pos[0] + dx, pos[1] + dy)

def hpwl(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return (max(xs) - min(xs)) + (max(ys) - min(ys)) if len(pts) > 1 else 0.0

gate_b = show(BASE, 'design/stack/geometry/links/link-gate.json')
gate_c = show(CAND, 'design/stack/geometry/links/link-gate.json')
gate_h = show(HEADC, 'design/stack/geometry/links/link-gate.json')
era_b = show(BASE, 'design/stack/geometry/links/link-era-replacements.json')['placed']
ov = show(CAND, 'scripts/stack/studies/mc04_s10_l13/overlay.json')
ovh = show(HEADC, 'scripts/stack/studies/mc04_s10_l13/overlay.json')
rows_c = {(r['board'], r['ref']): r for r in gate_c['replacement']['footprints']}
retained = [e for e in era_b if (e['board'], e['ic']) in rows_c and rows_c[e['board'], e['ic']]['new'] is None]
S_board = scene({'replacement': {'footprints': []}}, [])
S_base = scene(gate_b, era_b)
S_cand = scene(gate_c, retained + ovh['blocks'])
S_cand_gate_only = scene(gate_c, retained)
res = {'gate_rows_equal_32580f77_vs_557b5a6e': gate_c['replacement']['footprints'] == gate_h['replacement']['footprints'],
       'overlay_blocks_equal_32580f77_vs_557b5a6e': ov['blocks'] == ovh['blocks']}

# A. R5257 / U5210
def d(a, b): return math.dist(a, b)
res['R5257_U5210'] = {}
for name, S in (('interim board (paper)', S_board), ('pre-S10 (6e5716e7)', S_base), ('S10 candidate', S_cand)):
    r, u = S['K', 'R5257'], S['K', 'U5210']
    res['R5257_U5210'][name] = {'R5257': r[:3], 'U5210': u[:3],
                               'centre_distance_mm': d(r[0], u[0]) if r[0] and u[0] else None,
                               'pad2_to_pin6_mm': d(pad(S, 'R5257', '2'), pad(S, 'U5210', '6')) if u[0] else None,
                               'pad1_to_pin7_mm': d(pad(S, 'R5257', '1'), pad(S, 'U5210', '7')) if u[0] else None}
dx = round((180.97 - 174.66) * 100); dy = round((204.70 - 199.89) * 100)
res['integer_check'] = {'dx': dx, 'dy': dy, 'd2': dx * dx + dy * dy, 'cap2': 793 * 793, 'exceeds': dx * dx + dy * dy > 793 * 793,
                        'r2_of_paper_distance': round(math.hypot(dx, dy) / 100, 2)}

# B. protected nets: pad-level extent, three states
SUF = ('_FB', '_SUM', '_SENSE')
moved = {}
for k in S_cand:
    if S_base[k][:2] != S_cand[k][:2] or S_base[k][3] != S_cand[k][3]:
        moved[k] = True
res['effective_movement_count'] = len(moved)
res['effective_face_changes'] = sorted(k[1] for k in moved if S_base[k][0] and S_cand[k][0] and S_base[k][1] != S_cand[k][1])
res['rotation_only'] = sorted(k[1] for k in moved if S_base[k][:2] == S_cand[k][:2])
prot_moved = {}
for (b, ref) in sorted(moved):
    nets = sorted({n for n in pins.get(ref, {}).values() if n and n.endswith(SUF)})
    if nets and not ref.startswith('U'):
        prot_moved[ref] = nets
def state(ref, S):
    b = board_of[ref]; o, f, src, t = S[b, ref]
    return {'origin': o, 'face': f, 'source': src, 'turn': t}
res['protected_passives'] = {}
for ref, nets in prot_moved.items():
    b = board_of[ref]
    e = {'mpn': pk[ref]['mpn'], 'pins': pins[ref], 'board(paper)': state(ref, S_board), 'pre_S10': state(ref, S_base),
         'candidate': state(ref, S_cand),
         'class': 'newly displaced' if S_base[b, ref][2] == 'board' else 'returns to paper' if S_cand[b, ref][2] == 'board' else 'shifted row',
         'moved_from_pre_S10_mm': round(d(S_base[b, ref][0], S_cand[b, ref][0]), 4),
         'moved_from_paper_mm': round(d(S_board[b, ref][0], S_cand[b, ref][0]), 4), 'nets': {}}
    for n in nets:
        ne = {'pins': sorted(net_pins[n])}
        for name, S in (('paper', S_board), ('pre_S10', S_base), ('candidate', S_cand)):
            pts = [pad(S, r, p) for r, p in net_pins[n] if r in board_of]
            ics = [(r, p) for r, p in net_pins[n] if r.startswith('U')]
            mypin = next(p for p, nn in pins[ref].items() if nn == n)
            me = pad(S, ref, mypin)
            ne[name] = {'pad_hpwl_mm': None if None in pts else round(hpwl(pts), 3),
                        'est_pF_1.5xHPWLx0.2': None if None in pts else round(RF * hpwl(pts) * PF, 2),
                        'faces': sorted({S[board_of[r], r][1] for r, _ in net_pins[n] if r in board_of and S[board_of[r], r][0]}),
                        'to_ic_pin_mm': {f'{r}.{p}': (round(d(me, pad(S, r, p)), 3) if pad(S, r, p) else None) for r, p in ics}}
        e['nets'][n] = ne
    res['protected_passives'][ref] = e

# C. locality records
acc = show(BASE, 'design/partition/locality-acceptances.json')['acceptances']
orig = {(p['board'], p['ref']): p for p in show(PAPER, 'design/partition/floorplan-candidate.json')['placements']}
res['locality'] = {}
for x in acc:
    if x.get('ref') not in ('U5113', 'U5112', 'U4646', 'U4417', 'U4526'):
        continue
    b, ref = x['board'], x['ref']
    o = orig[b, ref]
    e = {'kind': x['kind'], 'baseline_6093081c': [o['x_mm'], o['y_mm'], o['side']], 'recorded_pose': x['pose'], 'recorded_distance_mm': x['distance_mm']}
    for name, S in (('pre_S10', S_base), ('candidate', S_cand)):
        p, f, src, _ = S[b, ref]
        e[name] = {'pose': [p[0], p[1], f], 'source': src, 'distance_mm': round(math.hypot(p[0] - o['x_mm'], p[1] - o['y_mm']), 2),
                   'unrounded': math.hypot(p[0] - o['x_mm'], p[1] - o['y_mm'])}
    e['board_pose'] = S_board[b, ref][:2]
    runs = {}
    for run in x.get('input_runs', []):
        n = run['net']
        if 'routed_estimate_mm' not in run:
            continue
        rr = {'recorded': {k: run[k] for k in ('routed_estimate_mm', 'capacitance_estimate_pF', 'input_passives_to_buffer_mm') if k in run}}
        for name, S in (('pre_S10', S_base), ('candidate', S_cand)):
            pp = {(r, p): pad(S, r, p) for r, p in net_pins[n] if r in board_of}
            missing = sorted(r for r, p in net_pins[n] if r not in board_of)
            L = RF * hpwl(list(pp.values()))
            icpin = next(v for (r, p), v in pp.items() if r == ref)
            rr[name] = {'routed_estimate_mm': round(L, 1), 'capacitance_estimate_pF': round(L * PF, 1),
                        'input_passives_to_buffer_mm': {r: round(d(icpin, v), 1) for (r, p), v in sorted(pp.items()) if r != ref},
                        'refs_not_on_boards': missing, 'sources': {r: S[board_of[r], r][2] for r, _ in pp}}
        runs[n] = rr
    for run in x.get('grown_nets', []):
        n = run['net']
        refs = sorted({r for r, _ in net_pins[n] if board_of.get(r) == b})
        rr = {'recorded': {k: run[k] for k in ('added_run_estimate_mm', 'capacitance_estimate_pF')}}
        old = hpwl([fps[b][r]['origin'] for r in refs])
        for name, S in (('pre_S10', S_base), ('candidate', S_cand)):
            pts = [S[b, r][0] for r in refs]
            if None in pts:
                rr[name] = 'net has a footprint without a position'; continue
            L = RF * hpwl(pts)
            rr[name] = {'added_run_estimate_mm': round(L - RF * old, 2), 'capacitance_estimate_pF': round(L * PF, 2)}
        if isinstance(rr.get('pre_S10'), dict) and isinstance(rr.get('candidate'), dict):
            rr['changed_refs_S10'] = [r for r in refs if S_base[b, r][:2] != S_cand[b, r][:2]]
        runs[n] = rr
    e['runs'] = runs
    res['locality'][ref] = e

# D. overlay blocks (withheld poses) and decouplers
res['overlay_blocks'] = {}
for e in ovh['blocks']:
    b, ic = e['board'], e['ic']
    o = {'gate_pose': e['gate_pose'], 'overlay_pose': e['pose'], 'members': e['members'], 'passives_moved': e['passives_moved']}
    for name, S in (('paper', S_board), ('pre_S10', S_base), ('candidate_gate_only', S_cand_gate_only), ('candidate_overlay', S_cand)):
        o[name] = {r: {'origin': [round(v, 4) for v in S[b, r][0]] if S[b, r][0] else None, 'face': S[b, r][1], 'source': S[b, r][2], 'turn': S[b, r][3],
                       'to_ic_mm': round(d(S[b, r][0], S[b, ic][0]), 2) if S[b, r][0] and S[b, ic][0] else None} for r in e['members']}
    o['ic_moved_from_paper_mm'] = round(d(S_board[b, ic][0], S_cand[b, ic][0]), 2)
    o['ic_moved_from_pre_S10_mm'] = round(d(S_base[b, ic][0], S_cand[b, ic][0]), 2)
    res['overlay_blocks'][ic] = o
res['open_after'] = sorted(k[1] for k, v in S_cand.items() if v[0] is None)
res['open_before'] = sorted(k[1] for k, v in S_base.items() if v[0] is None)
res['input_sha256'] = hashes
print(json.dumps(res, indent=1, default=list))

# E. (appended) U4526 nets with the three overlay blocks withheld (gate rows only), origin-HPWL definition
extra = {}
b = 'K'
for n in ('/E5/HOLD_N', '/E5/READY'):
    refs = sorted({r for r, _ in net_pins[n] if board_of.get(r) == b})
    old = hpwl([fps[b][r]['origin'] for r in refs])
    extra[n] = {'refs': refs}
    for name, S in (('pre_S10', S_base), ('candidate_gate_only', S_cand_gate_only), ('candidate_overlay', S_cand)):
        L = RF * hpwl([S[b, r][0] for r in refs])
        extra[n][name] = {'added_run_estimate_mm': round(L - RF * old, 2), 'capacitance_estimate_pF': round(L * PF, 2)}
print(json.dumps({'U4526_nets_overlay_withheld': extra, 'R8456_pins': pins.get('R8456'),
                  'pair8_slot_rect': [176.0 - 2.75, 196.25 - 0.75, 176.0 + 2.75, 196.25 + 0.75]}, indent=1))
