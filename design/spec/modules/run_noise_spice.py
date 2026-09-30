"""Bounded AC checks for N1 transfer proposals; ideal amplifiers, no hardware claim."""
from __future__ import annotations
import json
import math
import subprocess
from pathlib import Path
from design.spec.cells._builder import ROOT

DIR = ROOT / 'design/spec/modules/spice'
CACHE = ROOT / '.circuit-cache/noise-spice'
OUT = ROOT / 'design/reports/spice/noise.json'

FRONT = '''VNOISE input 0 DC 0 AC 1
RRECON input recon 1k
CRECON recon 0 10n
CAC recon ac 100n
RBLEED ac 0 100k
EINPUT buffered 0 ac buffered 1e6
'''

CASES = {
    'WHITE': FRONT + 'EOUT out 0 buffered out 1e6\n',
    'PINK': 'ESOURCE source 0 input source 1e6\n' + FRONT.replace('RRECON input', 'RRECON source') + 'EOUT out 0 buffered out 1e6\n',
    'BROWN': FRONT + '''RIN buffered sum 100k
RLEAK out sum 1Meg
CLEAK out sum 10n
EOUT out 0 0 sum 1e6
''',
    'BLUE': 'ESOURCE source 0 input source 1e6\n' + FRONT.replace('RRECON input', 'RRECON source') + '''CDIFF buffered series 100p
RDIFF series sum 100k
RFEEDBACK out sum 100k
CFEEDBACK out sum 33p
EOUT out 0 0 sum 1e6
''',
}
BANDS = {'WHITE': (100, 8000), 'PINK': (100, 8000),
         'BROWN': (100, 5000), 'BLUE': (100, 5000)}


def main():
    DIR.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, circuit in CASES.items():
        path = DIR / f'noise-{name.lower()}-ac.cir'
        data = CACHE / f'{name.lower()}.txt'
        relative = data.relative_to(ROOT)
        deck = f'''N1 {name} small-signal shaping; ideal opamps
{circuit}.control
set wr_singlescale
set wr_vecnames
ac dec 100 1 100k
wrdata {relative} db(v(out))
quit
.endc
.end
'''
        path.write_text(deck)
        result = subprocess.run(['bash', 'scripts/kicad/run.sh', 'ngspice', '-b',
                                 str(path.relative_to(ROOT))], cwd=ROOT,
                                text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        table = []
        for line in data.read_text().splitlines()[1:]:
            values = [float(x) for x in line.split()]
            if len(values) == 2:
                table.append(values)
        if len(table) < 200 or not all(math.isfinite(x) for row in table for x in row):
            raise ValueError(f'{name}: invalid AC data')
        low, high = BANDS[name]
        near = lambda f: min(table, key=lambda row: abs(math.log(row[0] / f)))
        lo, hi = near(low), near(high)
        slope = (hi[1] - lo[1]) / math.log10(hi[0] / lo[0])
        for f in (20, 100, 1000, 5000, 10000, 20000):
            if not math.isfinite(near(f)[1]):
                raise ValueError(f'{name}: nonfinite response')
        target = {'WHITE': (-4, 4), 'PINK': (-4, 4),
                  'BROWN': (-24, -16), 'BLUE': (16, 24)}[name]
        if not target[0] <= slope <= target[1]:
            raise ValueError(f'{name}: unexpected {slope:.2f} dB/decade')
        rows.append({'colour': name, 'deck': str(path.relative_to(ROOT)),
                     'status': 'PASS - ideal-amplifier AC model only',
                     'slope_band_Hz': [low, high],
                     'slope_dB_per_decade': round(slope, 3),
                     'gain_dB': {str(f): round(near(f)[1], 3)
                                 for f in (20, 100, 1000, 5000, 10000, 20000)},
                     'noise_spectrum_included': False})
    report = {'schema_version': 1, 'module': 'noise', 'status': 'PASS - small-signal filters only',
              'oracle': 'pinned KiCad 10 ngspice', 'runs': rows,
              'limits': 'Input AC sources are flat; NOISE2 source spectra, quantization, random RMS, headroom and hardware stability are excluded. BLUE uses pink input; BROWN uses white input.'}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + '\n')
    for row in rows:
        print(row['colour'], row['slope_dB_per_decade'], 'dB/decade')


if __name__ == '__main__':
    main()
