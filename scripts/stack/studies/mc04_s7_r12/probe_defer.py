"""Probe: place evicted parts whose HEAD pose lies in a sleeve keep-out after the others (no repository change)."""
import json, math, subprocess, sys
from pathlib import Path
ROOT = Path.home() / 'repos/circuits/zudo-osc-hole-field'
sys.path.insert(0, str(ROOT))
import scripts.checks.partition35_floorplan as fp
DEFER = {'D4101', 'D4102', 'R8425', 'R8426'}
src = Path(fp.__file__).read_text()
old = "        for ref in sorted(evicted):\n            part=by_ref[ref];row=rows[ref];members[ref]=[]"
assert old in src
src = src.replace(old, "        for ref in sorted(evicted,key=lambda r:(r in DEFER,r)):\n            part=by_ref[ref];row=rows[ref];members[ref]=[]")
ns = {'__name__': 'probe', '__file__': fp.__file__}
code = compile(src, fp.__file__, 'exec')
ns['DEFER'] = DEFER
exec(code, ns)
report = ns['build']()
new = {p['ref']: p for p in report['placements']}
old = {p['ref']: p for p in json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', 'HEAD:design/partition/floorplan-candidate.json'], capture_output=True, text=True, check=True).stdout)['placements']}
base = {p['ref']: p for p in json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', '6093081c:design/partition/floorplan-candidate.json'], capture_output=True, text=True, check=True).stdout)['placements']}
for r in sorted(set(new) | set(old)):
    a, b = old.get(r), new.get(r)
    if (a['board'], a['x_mm'], a['y_mm'], a['side'], a.get('rotation_deg')) != (b['board'], b['x_mm'], b['y_mm'], b['side'], b.get('rotation_deg')):
        s = base.get(r)
        print(r, 'OLD', (a['x_mm'], a['y_mm'], a['side']), 'NEW', (b['x_mm'], b['y_mm'], b['side']), 'move', round(math.hypot(a['x_mm'] - b['x_mm'], a['y_mm'] - b['y_mm']), 2),
              'from slot', s and round(math.hypot(s['x_mm'] - b['x_mm'], s['y_mm'] - b['y_mm']), 2))
print('errors', report['errors'])
