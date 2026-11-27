#!/usr/bin/env python3
"""Read-only: trace the W1 F2 feedback network and paper poses from git objects. No repo writes."""
import json, math, subprocess, sys, hashlib
import os as _os
REPO = _os.environ.get('OSC_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[4])
def blob(rev, path):
    return subprocess.check_output(['git', '-C', REPO, 'show', f'{rev}:{path}'])
def js(rev, path):
    b = blob(rev, path); return json.loads(b), hashlib.sha256(b).hexdigest()
REV = sys.argv[1] if len(sys.argv) > 1 else '8243acdf4ef76b18741ce3bcca4794e2abf3fee2'
io, h1 = js(REV, 'design/reports/io-partition.json')
ap, h2 = js(REV, 'design/partition/adopted-placement-pins.json')
print('rev', REV); print('io-partition.json sha256', h1); print('adopted-placement-pins.json sha256', h2)
pk = {p['ref']: p for p in io['physical_packages']}
pins = {}
for u in io['package_units']:
    pins.setdefault(u['ref'], {}).update(u['pins'])
pose = {p['ref']: p for p in ap['pins'] if p['board'] == 'K'}
nets = ['/W1/F1_OUT', '/W1/F2_CLIP', '/W1/F2_SUM', '/W1/F2_OUT', '/W1/F3_SUM', '/W1/F3_CLIP']
u = pose['U5210']
print('U5210 package', {k: v for k, v in pk['U5210'].items() if k not in ('pins',)})
print('U5210 pins', pins['U5210'])
for n in nets:
    print('\nNET', n)
    for ref in sorted(pins):
        for pin, net in sorted(pins[ref].items()):
            if net == n:
                p = pose.get(ref); q = pk.get(ref, {})
                d = math.hypot(p['x_mm'] - u['x_mm'], p['y_mm'] - u['y_mm']) if p else None
                print(f"  {ref}.{pin} value={q.get('value')} mpn={q.get('mpn')} fp={p and p['footprint']} "
                      f"xy=({p and p['x_mm']},{p and p['y_mm']}) rot={p and p['rotation_deg']} side={p and p['side']} "
                      f"d_to_U5210_origin={d!r} role={q.get('role')}")
r = pose['R5257']
dx = round((u['x_mm'] - r['x_mm']) * 100); dy = round((u['y_mm'] - r['y_mm']) * 100)
print('\nR5257', r); print('U5210', u)
print('dx,dy (1/100 mm)', dx, dy, 'd2', dx * dx + dy * dy, 'cap2', 793 * 793, 'isqrt', math.isqrt(dx*dx+dy*dy), 'dist', math.hypot(dx, dy) / 100)
print('R5257 package', pk['R5257'])
