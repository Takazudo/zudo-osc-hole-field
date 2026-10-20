"""Bounded DRC confirmation for the types KiCad caps at 199 markers (hole_to_hole,
silk_over_copper, silk_overlap), canonical copy vs Stage56 candidate.

KiCad 10.0.6 stops reporting a violation type after 199 markers and kicad-cli cannot
raise that limit. `capped_diff.py` shows the candidate equals the canonical board minus
30 footprints, 77 segments and 18 vias, with no added item and no changed geometry
(only hidden fields and zone whitespace differ). These three checks compare pairs of
existing items, so outside the removed items' bounding box the candidate's violations
equal the canonical ones by construction, and nowhere can a new pair appear.

This script confirms that on the one region where geometry changed. It runs one DRC
per side on a single X tile covering the removed-item box plus margin. The tile's rules
append `severity ignore` for hole_to_hole and silk_clearance, at the board's own minimum
values, to every pair with neither item inside the tile. Inputs are the zone-refilled
boards used for the ratsnest (no refill or parity here; zones are copper-only and
none of the three checks use zone fill). Runs are hard-capped at MAX_RUNS; a tile that
reaches 199 for a type leaves that type NOT ESTABLISHED for the tile instead of splitting.

Usage: capped_tiles.py run | check
"""
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib, json, math, os, subprocess, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CACHE = ROOT/'.circuit-cache/stage56/tiles'
EVIDENCE = HERE/'evidence'
TYPES = ('hole_to_hole', 'silk_over_copper', 'silk_overlap')
CAP = 199
SIDES = {
    'baseline': (ROOT/'.circuit-cache/stage55/baseline-refilled.kicad_pcb', ROOT/'.circuit-cache/stage55/baseline-refilled.kicad_pro',
                 ROOT/'design/architecture-278/implementation/stage55/idle-quad-cleanup/evidence/baseline-drc.json'),
    'candidate': (ROOT/'.circuit-cache/stage56/candidate-refilled.kicad_pcb', ROOT/'.circuit-cache/stage56/candidate-refilled.kicad_pro',
                  HERE/'evidence/candidate-drc.json'),
}
REFILLED_SHA = {'baseline': ('design/architecture-278/implementation/stage55/idle-quad-cleanup/evidence/baseline-ratsnest.json'),
                'candidate': ('design/architecture-278/implementation/stage56/cleanup-closure/evidence/candidate-ratsnest.json')}
DRU = ROOT/'boards/osc-core/osc-core.kicad_dru'
MAX_RUNS = 8
DIFF = HERE/'evidence/capped-diff.json'


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p): return Path(p).resolve().relative_to(ROOT).as_posix()


def require(ok, msg):
    if not ok:
        raise SystemExit('FAIL: '+msg)


def tile_rules(x0, x1):
    inside = lambda o: f"({o}.Position_X >= {x0}mm && {o}.Position_X < {x1}mm)"
    cond = f"!({inside('A')} || {inside('B')})"
    return ('\n'
            f'(rule "stage56-tile-ignore-hole" (constraint hole_to_hole (min 0.25mm)) (condition "{cond}") (severity ignore))\n'
            f'(rule "stage56-tile-ignore-silk" (constraint silk_clearance (min 0mm)) (condition "{cond}") (severity ignore))\n')


def changed_tile():
    diff = json.loads(DIFF.read_text())
    x0, _, x1, _ = diff['removed_union_bbox_mm']
    return (float(math.floor(x0 - 1)), float(math.ceil(x1 + 1)))


def tile_name(t): return f'x{t[0]:g}_{t[1]:g}'.replace('-', 'm')


def run_tile(side, t):
    pcb, pro, _ = SIDES[side]
    d = CACHE/side/tile_name(t); d.mkdir(parents=True, exist_ok=True)
    for name, src in (('osc-core.kicad_pcb', pcb), ('osc-core.kicad_pro', pro)):
        dst = d/name
        if not dst.exists():
            os.link(src, dst)
    (d/'osc-core.kicad_dru').write_text(DRU.read_text() + tile_rules(*t))
    out = d/'drc.json'
    if out.exists():
        out.unlink()
    cmd = ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'pcb', 'drc', '--format', 'json', '--severity-all',
           '-o', rel(out), rel(d/'osc-core.kicad_pcb')]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    require(r.returncode == 0 and out.exists(), f'{side} {tile_name(t)} DRC failed: {r.stderr[-500:]}')
    rep = json.loads(out.read_text())
    counts = Counter(v['type'] for v in rep['violations'] if v['type'] in TYPES)
    return {'side': side, 'tile': list(t), 'command': cmd, 'kicad_version': rep['kicad_version'],
            'input_pcb_sha256': sha(d/'osc-core.kicad_pcb'), 'dru_sha256': sha(d/'osc-core.kicad_dru'),
            'output_sha256': sha(out), 'counts': {k: counts.get(k, 0) for k in TYPES}}


def key(v): return (v['type'], tuple(sorted(i['uuid'] for i in v['items'])))
def signature(v): return (v['type'], tuple(sorted(i['description'] for i in v['items'])))


def merge(side, receipts):
    seen = {}
    for r in receipts:
        rep = json.loads((CACHE/side/tile_name(tuple(r['tile']))/'drc.json').read_text())
        require(sha(CACHE/side/tile_name(tuple(r['tile']))/'drc.json') == r['output_sha256'], 'tile output binding')
        for v in rep['violations']:
            if v['type'] in TYPES:
                seen.setdefault(key(v), v)
    return list(seen.values())


def execute():
    require(not (EVIDENCE/'capped-tiles.json').exists(), 'refuse overwrite of evidence/capped-tiles.json')
    for side, (pcb, pro, _) in SIDES.items():
        ratsnest = json.loads((ROOT/REFILLED_SHA[side]).read_text())
        require(sha(pcb) == ratsnest['refilled_board_sha256_host'], f'{side} refilled board is the ratsnest input')
    tile = changed_tile()
    jobs = [(s, tile) for s in SIDES]
    require(len(jobs) <= MAX_RUNS, 'run cap')
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda st: run_tile(*st), jobs))
    write({r['side']: [r] for r in results})


def write(final):
    out = {}
    for side, receipts in final.items():
        merged = merge(side, receipts)
        sigs = Counter(signature(v) for v in merged)
        out[side] = {'tiles': sorted(receipts, key=lambda r: (r['tile'][0], r['tile'][1])),
                     'complete_counts': {t: sum(1 for v in merged if v['type'] == t) for t in TYPES},
                     'signatures': sorted([[t, list(items), n] for (t, items), n in sigs.items()])}
    (EVIDENCE/'capped-tiles.json').write_text(json.dumps(out, indent=2, sort_keys=True)+'\n')
    evaluate()


def evaluate():
    data = json.loads((EVIDENCE/'capped-tiles.json').read_text())
    diff = json.loads(DIFF.read_text())
    require(diff['added_counts'] == {} and diff['changed_unexplained'] == [], 'diff shows added or altered geometry')
    tile = changed_tile()
    result = {'status': 'Bounded DRC confirmation of the three 199-capped types on the changed region; '
                        'disposable Stage56 candidate; not validation', 'tile_mm': list(tile),
              'runs': sum(len(d['tiles']) for d in data.values()), 'max_runs': MAX_RUNS,
              'diff_sha256': sha(DIFF)}
    require(result['runs'] <= MAX_RUNS, 'run cap exceeded')
    sigs, complete = {}, {}
    for side in SIDES:
        d = data[side]
        require(all(r['kicad_version'] == '10.0.6' for r in d['tiles']), 'oracle')
        require([tuple(r['tile']) for r in d['tiles']] == [tile], f'{side}: tile is the changed region')
        ratsnest = json.loads((ROOT/REFILLED_SHA[side]).read_text())
        require(all(r['input_pcb_sha256'] == ratsnest['refilled_board_sha256_host'] for r in d['tiles']), f'{side}: tile input binding')
        counts = d['tiles'][0]['counts']
        complete[side] = {t: counts[t] < CAP for t in TYPES}
        sigs[side] = Counter({(t, tuple(items)): n for t, items, n in d['signatures']})
        result[side] = {'tile_counts': counts}
    new = sigs['candidate'] - sigs['baseline']
    gone = sigs['baseline'] - sigs['candidate']
    per = {}
    for t in TYPES:
        n_new = sum(n for (tt, _), n in new.items() if tt == t)
        established = complete['baseline'][t] and complete['candidate'][t]
        per[t] = {'complete_in_tile': established, 'new_signatures_in_tile': n_new,
                  'removed_signatures_in_tile': sum(n for (tt, _), n in gone.items() if tt == t),
                  'verdict': ('FAIL' if n_new else 'PASS') if established else 'NOT ESTABLISHED (tile capped at 199)'}
    result['by_type'] = per
    result['new_signatures'] = sorted([[t, list(i), n] for (t, i), n in new.items()])
    result['outside_tile'] = ('geometry identical by capped-diff.json (no added item, only hidden fields and zone '
                              'whitespace changed); pairwise checks cannot change there by construction')
    body = json.dumps(result, indent=2, sort_keys=True)+'\n'
    path = HERE/'capped-audit.json'
    if sys.argv[1:] == ['check']:
        require(path.read_text() == body, 'capped audit replay drift')
    else:
        path.write_text(body)
    print(json.dumps({t: v['verdict'] for t, v in per.items()}), {s: result[s]['tile_counts'] for s in SIDES})
    return result


if __name__ == '__main__':
    if sys.argv[1:] == ['run']:
        execute()
    elif sys.argv[1:] == ['check']:
        evaluate()
    else:
        raise SystemExit('usage: capped_tiles.py run|check')
