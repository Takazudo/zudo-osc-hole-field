"""Diagnostic output-isolation screen, not an ADG5412F vendor/fault model.

Uses the existing pinned TI amplifier model and KiCad oracle. Switch resistance
and capacitance are sensitivity assumptions: their source test conditions do not
cover the project dual 12 V supply. Results cannot close the protection gate.
"""
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.cells.sweep_precision_vendor import model, deck, measure, LOADS, CAPS


def run():
    model()
    cache = ROOT / '.circuit-cache/sources/protection-58'
    cache.mkdir(parents=True, exist_ok=True)
    init = ROOT / '.spiceinit'
    if init.exists():
        raise RuntimeError('Refusing to replace .spiceinit')
    init.write_text('set ngbehavior=ps\n')
    rows = []
    try:
        for load in LOADS:
            for cap in CAPS:
                text = deck(LOADS[load], CAPS[cap])
                text = text.replace('Risoa drive mid 499', 'Rswdrive drive swout 16.5\nRisoa swout mid 499')
                text = text.replace('Rfb jack fb 100', 'Rfb jack swsense 2740\nRswsense swsense fb 16.5\nRlocal drive fb 10meg\nCsdrive drive 0 24p\nCssense fb 0 24p')
                text = text.replace('Cfast drive fb 1e-09', 'Cfast drive fb 10n')
                if 'Rfb jack fb 100' in text or 'Cfast drive fb 10n' not in text:
                    raise RuntimeError('Source cell changed; review diagnostic deck')
                path = cache / 'output-isolation.cir'
                path.write_text(text)
                result = subprocess.run(['bash', 'scripts/kicad/run.sh', 'ngspice', '-b', str(path.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True, timeout=120)
                if result.returncode:
                    raise RuntimeError(result.stdout + result.stderr)
                m = measure(result.stdout)
                overshoot = max(0, max(m['pmax'], m['p2max']) - 5, -5 - min(m['nmin'], m['n2min'])) / 10 * 100
                error = max(abs(m[k] - (5 if k.startswith('p') else -5)) for k in ('pset', 'p2set', 'nset', 'n2set')) * 1000
                ripple = max(m[a] - m[b] for a, b in [('platmax', 'platmin'), ('p2latmax', 'p2latmin'), ('nlatmax', 'nlatmin'), ('n2latmax', 'n2latmin')]) * 1000
                rows.append({'load': load, 'cable_capacitance': cap, 'overshoot_percent': overshoot, 'settling_error_mV_at_400us': error, 'late_ripple_mVpp': ripple, 'diagnostic_targets_met': overshoot <= 10 and error <= 1 and ripple <= 1})
    finally:
        init.unlink()
    report = {'status': 'DIAGNOSTIC ONLY; protection gate OPEN', 'oracle': 'KiCad 10.0.6 / pinned ngspice', 'amplifier': 'Existing pinned TI OPAx197 Final 1.3 model', 'switch_model': '16.5 ohm and 24 pF lumped sensitivity assumptions; not ADI model; no switching, charge injection, leakage, rail faults or temperature simulation', 'proposed_values': {'sense_resistance_ohm': 2740, 'local_dc_feedback_ohm': 10000000, 'local_compensation_F': 1e-8}, 'cases': rows}
    out = ROOT / 'design/power/protection58-output-model.json'
    out.write_text(json.dumps(report, indent=2) + '\n')
    print(f"DIAGNOSTIC: {sum(r['diagnostic_targets_met'] for r in rows)}/{len(rows)} targets met; not protection proof")


if __name__ == '__main__':
    run()
