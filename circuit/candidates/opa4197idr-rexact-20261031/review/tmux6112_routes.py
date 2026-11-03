#!/usr/bin/env python3
"""S2b envelope-switch route comparison for the TMUX6112 SEL-before-VDD row (UNADOPTED).

Prices come from the retained 2026-10-31 JLC cache through the cost study's price();
scenario totals come from design/readiness/cost-reduction-study.json. Run from the
repository root: python3 circuit/candidates/opa4197idr-rexact-20261031/review/tmux6112_routes.py
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.checks.cost_reduction_study import price  # noqa: E402

OUT = Path(__file__).with_name('tmux6112-routes.json')
SEL_PER_ENVELOPE = 6   # SLOPE_SELECT 4 driven SEL + STORAGE_CLAMP HOLD_ENABLE/RESET_CAP; 2 SEL are tied to AGND
ENVELOPES = 6
S2 = {'per_unit_usd': 1298.49, 'per_lot_usd': 5942.93}    # cost study section 4, ADG5412F envelope switches
S2B = {'per_unit_usd': 1196.19, 'per_lot_usd': 5410.57}   # cost study section 4, TMUX6112PWR envelope switches


def main():
    bat = json.loads((ROOT / '.claude/skills/component-nexperia-bat54s-215/facts.json').read_text())
    vf = next(f for f in bat['facts'] if f['fact_id'] == 'fact-clamp-diode-forward-voltage')['value']
    ir = next(f for f in bat['facts'] if f['fact_id'] == 'fact-clamp-diode-reverse-current')['value']
    n = SEL_PER_ENVELOPE * ENVELOPES
    diode, resistor = price('BAT54S_215', n), price('RC0603FR-07100KL', n)
    add_unit = round(diode['per_unit_usd'] + resistor['per_unit_usd'], 2)
    add_lot = round(diode['per_lot_usd'] + resistor['per_lot_usd'], 2)
    r = 100e3
    i_def1 = 0.8 / r * 1e3          # mA, SEL source <= 0.8 V under PD definition 1
    i_unseq = 5.5 / r * 1e3         # mA, PROPOSED 5.5 V +5 V ceiling with VDD = 0 V
    report = {
        'schema_version': 1,
        'status': 'UNADOPTED CANDIDATE; route comparison and 25 C source arithmetic only; no schematic change made',
        'routes': [
            {'id': 'ADG-envelope', 'content': 'S2: envelope switches stay on ADG5412FBRUZ (12 per unit)',
             'per_unit_usd': S2['per_unit_usd'], 'per_lot_usd': S2['per_lot_usd'],
             'delta_vs_S2b_per_unit_usd': round(S2['per_unit_usd'] - S2B['per_unit_usd'], 2),
             'blocker': 'ADG5412FBRUZ stock 0 against 60 parts per 5-unit lot',
             'TMUX6112_row': 'not applicable (ADG5412F logic rows already PASS with the existing sequencing)'},
            {'id': 'SEL-hold', 'content': 'S2b plus, per SEL: 100 kOhm series RC0603FR-07100KL and BAT54S,215 (pin 3 = SEL, pin 2 = +12 V, pin 1 = AGND)',
             'added_parts_per_unit': {'BAT54S_215': n, 'RC0603FR-07100KL': n}, 'added_placements_per_unit': 2 * n,
             'added_per_unit_usd': add_unit, 'added_per_lot_usd': add_lot,
             'per_unit_usd': round(S2B['per_unit_usd'] + add_unit, 2), 'per_lot_usd': round(S2B['per_lot_usd'] + add_lot, 2),
             'stock': {'BAT54S_215': diode['stock'], 'RC0603FR-07100KL': resistor['stock']},
             'TMUX6112_row': {
                 'verdict': 'CONDITIONAL PASS at 25 C',
                 'basis': f'Under definition 1 the clamp current is <= {i_def1:.3f} mA, so SEL <= VDD + {vf["at_0p1mA_max_mV"]} mV maximum (BAT54S VF at 0.1 mA, 25 C). '
                          f'Unsequenced with +5 V at the PROPOSED 5.5 V ceiling: <= {i_unseq:.3f} mA, also inside the 0.1 mA row. Both stay below VDD + 0.3 V.',
                 'open': ['BAT54S VF has no maximum away from 25 C (fact-clamp-diode-forward-voltage-temperature); the 60 mV margin at cold is UNKNOWN',
                          f'Both BAT54S diodes leak <= {ir["max_uA"]} uA each at {ir["VR_V"]} V: <= {2*ir["max_uA"]*1e-6*r:.2f} V drop in 100 kOhm, plus 1.6 % into the 6 MOhm typical pull-down; SEL high stays about 4.5 V at +5 V, above VIH 2 V',
                          'Series RC with the SEL and diode capacitance adds roughly microsecond delay; envelope clock is 50 us; not simulated',
                          'Board K placement and the #293 fill/DRC would need a rerun']}},
            {'id': 'PD-0.3V', 'content': 'S2b with the PD definition-1 bound tightened from 0.8 V to 0.3 V',
             'per_unit_usd': S2B['per_unit_usd'], 'per_lot_usd': S2B['per_lot_usd'],
             'saving_vs_SEL_hold_per_unit_usd': add_unit,
             'blocker': 'PD contract change; not clearly cheapest (saves only the SEL-hold parts)'}],
        'recommendation': 'SEL-hold: lowest-cost route that does not need a PD change; it avoids the ADG5412F stock-0 blocker',
        'sources': {'scenario_totals': 'design/readiness/cost-reduction-study.json and doc research page section 4',
                    'prices': [diode['receipt'], resistor['receipt']],
                    'tmux6112': 'SCDS383F 6.1 (index 4) VDIG GND-0.3..VDD+0.3 V, IDIG +/-30 mA; 6.5 (index 5) RPD 6 MOhm'}}
    OUT.write_text(json.dumps(report, indent=1) + '\n')
    for route in report['routes']:
        print(route['id'], route['per_unit_usd'], route['per_lot_usd'])


if __name__ == '__main__':
    main()
