"""Source comparison arithmetic and optional retained download checks, no fit oracle."""
import hashlib
import json
from pathlib import Path
import sys

p = Path(__file__).resolve().parent
s = json.loads((p / 'sources.json').read_text())
items = {x['id']: x for x in s['sources']}
for pins, expected in [(8, 48.58), (16, 58.74)]:
    power = items[f'612{pins:03}21621']
    signal = items['61201021621']
    length = sum(x['length_mm'] + x['length_tolerance_mm'] for x in [power, signal]) + 6 + 4
    if abs(length - expected) > 1e-9:
        raise ValueError('Comparison interval arithmetic drift')
if s['adopted'] or any(s[k] is not None for k in ['cable_selection', 'mated_height_mm', 'bend_radius_mm']):
    raise ValueError('Unknowns were promoted without a new review')
if '--cache' in sys.argv:
    for item in s['sources']:
        if hashlib.sha256(Path(item['cache']).read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(item['id'] + ': download hash mismatch')
print('PASS source arithmetic / unresolved-state checks; fit, native and physical NOT RUN')
