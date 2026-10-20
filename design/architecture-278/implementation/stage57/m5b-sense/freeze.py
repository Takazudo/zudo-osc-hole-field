"""Freeze the Stage57 target record (`target.json`) from retained evidence; host only.

Inputs: the Stage53 fresh connectivity snapshot (bound by hash to the Stage53
settlement), the native target geometry (`evidence/target-geometry.json`), and the
Stage51 / Stage53 proposals for the two exclusion regions.
Usage: freeze.py [--check]
"""
from pathlib import Path
from collections import Counter
import hashlib, json, math, sys
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
IMPL = ROOT/'design/architecture-278/implementation'
BASE_DIR = ROOT/'.circuit-cache/stage53-fresh'
BASE = '27d2214492f9dd88483be014df4197fdb936cbbc7c445f17c8178cce97126560'
NET = 'X1B64D2A971AB89E1AF19'
NAME = '/M5B/C819409_SENSE'
SOURCE = ('R8248', '2')
TARGET_PADS = (('U8215', '3'), ('D8212', '3'))
RAILS = ('+12V', '-12V', 'AGND')


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def signature(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def require(ok, msg):
    if not ok: raise SystemExit('FAIL: ' + msg)


def seg_dist(p, a, b):
    (ax, ay), (bx, by), (px, py) = a, b, p
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy))) if (dx or dy) else 0.0
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


def bbox(rows):
    pts = [p for r in rows for p in ([r['start_nm'], r['end_nm']] if r['kind'] == 'segment' else [r['at_nm']])]
    return [round(min(p[0] for p in pts) / 1e6, 6), round(min(p[1] for p in pts) / 1e6, 6),
            round(max(p[0] for p in pts) / 1e6, 6), round(max(p[1] for p in pts) / 1e6, 6)]


def compute():
    settlement = read(IMPL/'stage53/in4-study/settlement.json')
    snap_path = BASE_DIR/'connectivity-passfresh.json'
    snap = read(snap_path); geo = read(HERE/'evidence/target-geometry.json')
    require(sha(BASE_DIR/'osc-jack-left.kicad_pcb') == BASE == settlement['candidate_sha256'], 'Stage53 board binding')
    require(sha(snap_path) == settlement['complete_snapshot_sha256'] and snap['board_sha256'] == BASE, 'snapshot binding')
    require(geo['board_sha256'] == BASE and geo['net'] == NET and geo['kicad_version'] == '10.0.6', 'geometry binding')
    objs, groups = snap['objects'], snap['groups']
    pad = lambda ref, pin: next(k for k, v in objs.items() if v['kind'] == 'pad' and v['ref'] == ref and v['pin'] == pin)
    src = pad(*SOURCE)
    sg = next(g for g in groups[NET] if src in g)
    tg = next(g for g in groups[NET] if pad(*TARGET_PADS[0]) in g)
    require(len(groups[NET]) == 2 and sg == [src] and pad(*TARGET_PADS[1]) in tg and len(tg) == 162, 'target partition')
    require(snap['native_open_edges'] == 115, 'baseline opens')
    tg_kinds = Counter(objs[k]['kind'] for k in tg)
    tg_uuids = {objs[k]['uuid'] for k in tg if objs[k]['kind'] != 'pad'}
    require(tg_uuids == {c['uuid'] for c in geo['copper']}, 'geometry covers the target group copper')
    sp = next(p for p in geo['pads'] if (p['ref'], p['pin']) == SOURCE)['at_mm']
    dists = []
    for c in geo['copper']:
        d = seg_dist(sp, c['start_mm'], c['end_mm']) if c['kind'] == 'segment' else math.hypot(sp[0]-c['at_mm'][0], sp[1]-c['at_mm'][1])
        dists.append((round(d, 3), c['kind'], c.get('layer', 'F.Cu-B.Cu'), c['uuid']))
    for p in geo['pads']:
        if (p['ref'], p['pin']) != SOURCE:
            dists.append((round(math.hypot(sp[0]-p['at_mm'][0], sp[1]-p['at_mm'][1]), 3), 'pad', p['layers'][0], p['ref']+':'+p['pin']))
    dists.sort()
    s51 = read(IMPL/'stage51/f3-sense/proposal.json')['copper']
    s53 = read(IMPL/'stage53/in4-study/trial1-proposal.json')['copper']
    opens = {n: len(g) - 1 for n, g in groups.items() if len(g) > 1}
    return {
        'status': 'Stage57 frozen target record; setup only, no route search run',
        'net': {'name': NAME, 'native': NET},
        'baseline': {'board_sha256': BASE, 'stage53_settlement_sha256': sha(IMPL/'stage53/in4-study/settlement.json'),
                     'connectivity_snapshot_sha256': sha(snap_path), 'native_object_count': len(objs),
                     'native_open_edges': 115, 'nets_with_opens': len(opens)},
        'source': {'pad': ':'.join(SOURCE), 'component_size': 1, 'component_hash': signature(sorted(sg)),
                   **{k: v for k, v in next(p for p in geo['pads'] if (p['ref'], p['pin']) == SOURCE).items() if k not in ('ref', 'pin')}},
        'target_group': {'size': len(tg), 'kinds': dict(tg_kinds), 'component_hash': signature(sorted(tg)),
                         'pads': [p for p in geo['pads'] if (p['ref'], p['pin']) != SOURCE],
                         'copper_layers': dict(Counter(c.get('layer', 'via') for c in geo['copper']))},
        'nearest_target_objects_mm': [list(d) for d in dists[:8]],
        'rail_partitions': {r: sorted(len(g) for g in groups[r]) for r in RAILS},
        'acceptance': {'opens_before': 115, 'opens_after': 114, 'merge': 'exactly source(1) + target(162) into one 163-member retained component',
                       'other_partitions': 'every other net partition preserved exactly',
                       'drc': 'KiCad 10.0.6 rule errors 0, schematic parity 0, no added uncapped warning, no lib_footprint_issues',
                       'copper_layers_allowed_without_new_approval': ['F.Cu', 'B.Cu'],
                       'courtyard': 'courtyard contact is reported, never used as clearance or assembly proof'},
        'exclusions': {
            'in3_minus12v_necks': {
                'reason': 'Stage51 full In3 route split -12V 1015 -> 15+23+977; Stage52 refill diagnostics located the cuts at Stage51 copper indices 16, 17, 25',
                'stage51_in3_bbox_mm': bbox([r for r in s51 if r['kind'] == 'segment' and r['layer'] == 'In3.Cu']),
                'cut_sections': [{'index': i, 'start_mm': [v/1e6 for v in s51[i]['start_nm']], 'end_mm': [v/1e6 for v in s51[i]['end_nm']]} for i in (16, 17, 25)],
                'rule': 'no new copper on In3.Cu; -12V must stay one 1015-object partition'},
            'stage53_in4_corridor': {
                'reason': 'Stage53 accepted /F3/C945bba_SENSE copper; its In4 use was approved for F3 only and its +12V In4 pour must stay one 1025-object partition',
                'bbox_mm': bbox(s53),
                'rule': 'Stage53 copper unchanged (no removals); no new copper on In4.Cu; +12V stays one 1025-object partition'}},
    }


if __name__ == '__main__':
    result = compute()
    text = json.dumps(result, indent=2, sort_keys=True) + '\n'
    path = HERE/'target.json'
    if '--check' in sys.argv:
        require(path.read_text() == text, 'target replay drift')
    else:
        path.write_text(text)
    print('PASS target:', result['source']['pad'], '->', result['target_group']['size'], 'objects; nearest', result['nearest_target_objects_mm'][0][:3])
