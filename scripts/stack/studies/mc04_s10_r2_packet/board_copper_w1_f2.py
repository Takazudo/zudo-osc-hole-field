#!/usr/bin/env python3
"""Read-only: what copper the interim K board (boards/osc-core/osc-core.kicad_pcb, working-tree bytes) holds on the
W1 F2 nets. Reports pad centres (board frame and paper frame = board - (100, 50)), segment length and vias per net."""
import json, re, math, hashlib, sys
import os as _os
REPO = _os.environ.get('OSC_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[4])
PCB = REPO + '/boards/osc-core/osc-core.kicad_pcb'
raw = open(PCB, 'rb').read()
print('osc-core.kicad_pcb sha256', hashlib.sha256(raw).hexdigest(), 'bytes', len(raw))
txt = raw.decode()
tok = json.load(open(REPO + '/design/reports/board-net-tokens.json'))
print('board-net-tokens.json sha256', hashlib.sha256(open(REPO + '/design/reports/board-net-tokens.json', 'rb').read()).hexdigest())
WANT = ['/W1/F1_OUT', '/W1/F2_CLIP', '/W1/F2_SUM', '/W1/F2_OUT', '/W1/F3_SUM']
name = {}
for k, v in tok.items():
    s = json.dumps(v)
    for w in WANT:
        if ('"' + w + '"') in s:
            name.setdefault(w, []).append(k)
print('tokens', name)
t2n = {ts[0]: n for n, ts in name.items()}
# footprints
REFS = ['U5210', 'R5256', 'R5257', 'R5259', 'R5258']
for m in re.finditer(r'\n\t\(footprint "([^"]+)"', txt):
    end = txt.find('\n\t)\n', m.end())
    blk = txt[m.start():end]
    r = re.search(r'\(property "Reference" "([^"]+)"', blk)
    if not r or r.group(1) not in REFS:
        continue
    at = re.search(r'\n\t\t\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)', blk)
    ox, oy, rot = float(at.group(1)), float(at.group(2)), float(at.group(3) or 0)
    lay = re.search(r'\n\t\t\(layer "([^"]+)"\)', blk).group(1)
    print(f'{r.group(1)} {m.group(1)} at=({ox},{oy}) rot={rot} layer={lay} paper=({ox-100:.4f},{oy-50:.4f})')
    for p in re.finditer(r'\(pad "([^"]+)" (\w+) (\w+)\s*\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)(.*?)\n\t\t\)', blk, re.S):
        net = re.search(r'\(net "([^"]+)"\)', p.group(7))
        nn = net.group(1) if net else None
        if nn in t2n:
            px, py = float(p.group(4)), float(p.group(5))
            a = math.radians(-rot)  # KiCad: pad offset rotated by footprint angle (y down, CCW positive)
            gx = ox + px * math.cos(a) - py * math.sin(a)
            gy = oy + px * math.sin(a) + py * math.cos(a)
            print(f'   pad {p.group(1)} {t2n[nn]} board=({gx:.4f},{gy:.4f}) paper=({gx-100:.4f},{gy-50:.4f})')
for n, ts in name.items():
    for t in ts:
        segs = re.findall(r'\(segment\s*\(start ([-\d.]+) ([-\d.]+)\)\s*\(end ([-\d.]+) ([-\d.]+)\)\s*\(width ([-\d.]+)\)\s*\(layer "([^"]+)"\)\s*\(net "%s"\)' % re.escape(t), txt)
        vias = len(re.findall(r'\(via\s*(?:\([^()]*\)\s*)*?\(net "%s"\)' % re.escape(t), txt))
        vias2 = len(re.findall(r'\(via\b[^\n]*\n(?:\t\t[^\n]*\n)*?\t\t\(net "%s"\)' % re.escape(t), txt))
        L = sum(math.hypot(float(a) - float(c), float(b) - float(d)) for a, b, c, d, w, l in segs)
        print(f'{n} token {t}: segments={len(segs)} length_mm={L:.3f} layers={sorted({s[5] for s in segs})} widths={sorted({s[4] for s in segs})} vias={vias}/{vias2} total_refs={txt.count(chr(34)+t+chr(34))}')
