#!/usr/bin/env python3
"""Read-only re-verification of the review defects (Revision 2 of the packet). No repo writes, no search:
only rectangles and records already retained in result-a2.json are read."""
import json, re, math, subprocess, collections
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
import os as _os
REPO = _os.environ.get('OSC_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[4])
# ---- defect 1: copper connectivity by geometry on the interim K board
txt = open(REPO + '/boards/osc-core/osc-core.kicad_pcb').read()
NETS = {'/W1/F2_SUM': ('X82F8CC6DADB4E000D2FE', {'R5256.2': (276.14, 246.16, 'F.Cu', 0.9, 0.95), 'R5257.2': (274.66, 249.14, 'B.Cu', 0.95, 0.9), 'U5210.6': (283.445, 257.24, 'B.Cu', 1.95, 0.6)}),
        '/W1/F2_OUT': ('X27F28C7F6EDF0DF87603', {'R5257.1': (274.66, 250.64, 'B.Cu', 0.95, 0.9), 'R5259.1': (278.64, 244.16, 'B.Cu', 0.9, 0.95), 'R5258.1': (268.41, 246.14, 'B.Cu', 0.95, 0.9), 'U5210.7': (283.445, 258.51, 'B.Cu', 1.95, 0.6)})}
m = re.search(r'\(footprint "[^"]*SOIC-14[^"]*"(?:(?!\n\t\(footprint ).)*?"Reference" "U5210".*?\n\t\)\n', txt, re.S)
print('U5210 pad 6 size in board file:', re.search(r'\(pad "6" smd \w+\s*\(at [^)]*\)\s*\(size ([-\d. ]+)\)', m.group(0)).group(1))
out = {}
for net, (tok, pads) in NETS.items():
    segs = re.findall(r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\(width ([-\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "%s"\)' % tok, txt)
    vias = re.findall(r'\(via\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\(size ([-\d.]+)\)\s*\(drill ([-\d.]+)\)\s*\(layers ([^)]*)\)(?:\s*\([^()]*\))*?\s*\(net "%s"\)' % tok, txt)
    shapes = []  # (geometry, layers)
    for a, b, c, d, w, l in segs:
        shapes.append((LineString([(float(a), float(b)), (float(c), float(d))]).buffer(float(w) / 2), {l}))
    for x, y, s, dr, ls in vias:
        shapes.append((Point(float(x), float(y)).buffer(float(s) / 2), {'F.Cu', 'B.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu'}))
    for name, (x, y, l, w, h) in pads.items():
        shapes.append((box(x - w / 2, y - h / 2, x + w / 2, y + h / 2), {l}))
    par = list(range(len(shapes)))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    for i in range(len(shapes)):
        for j in range(i):
            if shapes[i][1] & shapes[j][1] and shapes[i][0].intersects(shapes[j][0]): par[f(i)] = f(j)
    n = len(segs) + len(vias)
    comp = {name: f(n + k) for k, name in enumerate(pads)}
    ends = []
    px, py, pl, pw, ph = pads['U5210.6' if 'SUM' in net else 'U5210.7']
    for a, b, c, d, w, l in segs:
        for (x, y) in ((float(a), float(b)), (float(c), float(d))):
            if l == pl and abs(x - px) <= pw / 2 and abs(y - py) <= ph / 2: ends.append((round(x - 100, 3), round(y - 50, 3), l, w))
    out[net] = {'components': len({f(i) for i in range(len(shapes))}), 'all_pads_one_component': len(set(comp.values())) == 1, 'track_ends_inside_U5210_pad_paper_frame': sorted(set(ends))}
print(json.dumps(out, indent=1))
# ---- defects 2 and 4: retained S9-A2 record
r = json.load(open(REPO + '/scripts/stack/studies/mc04_s9_slot_moves/result-a2.json'))
print('caps_reached', r['caps_reached'], 'parameters', r['parameters'])
fl = {p['ref']: p for p in json.loads(subprocess.check_output(['git', '-C', REPO, 'show', '6e5716e7:design/partition/floorplan-candidate.json']))['placements'] if p['board'] == 'K'}
def hit(a, b): return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]
u = r['runs']['U5210']
print('U5210 search keys', list(u['search'].keys()), [(g['grid_mm'], g['accepted_candidates'], g['rejections_by_reason']) for g in u['search']['grids']])
cl = u['clean']
print('clean', len(cl), 'geometry keys', list(cl[0]['geometry'].keys()), 'x', min(c['slot_centre'][0] for c in cl), max(c['slot_centre'][0] for c in cl), 'y', min(c['slot_centre'][1] for c in cl), max(c['slot_centre'][1] for c in cl), {c['direction'] for c in cl})
cy = fl['R8356']['courtyard_mm']; print('R8356 courtyard', cy)
cnt = collections.Counter()
for c in cl:
    for k, rect in c['geometry'].items():
        if isinstance(rect, list) and len(rect) == 4 and hit(rect, cy): cnt[k] += 1
    cnt['any'] += any(isinstance(v, list) and len(v) == 4 and hit(v, cy) for v in c['geometry'].values())
print('R8356 under', dict(cnt))
mv = collections.Counter()
for c in cl:
    refs = {p['ref'] for p in c['parts_re_placed']}
    rep = json.dumps(c['re_placement'])
    for ref in ('R8356', 'R8456', 'R4238', 'C8408', 'R7215', 'R7219', 'R8471'):
        mv[ref + ' in parts_re_placed'] += ref in refs
        mv[ref + ' anywhere in re_placement'] += ('"%s"' % ref) in rep
print(dict(mv))
v = r['runs']['U5209']['variant_B']['search'][0]
g = [x for x in v['grids'] if x['grid_mm'] == 0.25][0]
print(v['link'], [(x['grid_mm'], x['accepted_candidates'], x.get('rejections_by_reason')) for x in v['grids']])
print('candidate keys', list(g['evaluated'][0].keys()))
# ---- x = 176.0 row: geometric, slot rectangle (5.5 x 1.5 mm) and K tail against ungrown floorplan courtyards
ys = sorted({c['slot_centre'][1] for c in g['evaluated'] if c['slot_centre'][0] == 176.0})
print('x=176 candidates', len(ys), ys)
for ref in ('R5254', 'R5256', 'R5257', 'R5259'):
    cyr = fl[ref]['courtyard_mm']
    print(ref, [round(v, 2) for v in cyr], 'slot over it for y =', [y for y in ys if hit([173.25, y - 0.75, 178.75, y + 0.75], cyr)])
dirty = [c for c in g['evaluated'] if c['slot_centre'][0] != 176.0]
print('other candidates', [(c['slot_centre'], c['not_clean_because']) for c in dirty])
pair = r['runs']['U5209']['variant_B']['clean_pairs']
print('K_tail of paired first links over R5259:', [(p['first']['slot_centre'][1], hit(p['first']['geometry']['K_tail'], fl['R5259']['courtyard_mm'])) for p in pair[::4]])
# ---- knock-on moves inside each U5210 candidate
c0 = cl[0]
print('re_placement type', type(c0['re_placement']).__name__, (list(c0['re_placement'].keys()) if isinstance(c0['re_placement'], dict) else json.dumps(c0['re_placement'])[:600]))
mv = collections.Counter()
for c in cl:
    s = json.dumps(c)
    for ref in ('R8456', 'R4238', 'C8408', 'R7215', 'R7219', 'R8471'):
        mv[ref] += ('"%s"' % ref) in s
print('ref named anywhere in candidate record', dict(mv))
