#!/usr/bin/env python3
"""Audit electrical proposal references and recompute its planning arithmetic.

This is an offline design consistency check, not ERC, SPICE or hardware evidence.
"""
import json
from collections import Counter
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'design/standard'


def read(name):
    return json.loads((DIRECTORY / name).read_text())


def check():
    standard = read('electrical-standard.json')
    shortlist = read('parts-shortlist.json')
    budget = read('rail-budget-preliminary.json')
    parts = {part['id']: part for part in shortlist['parts']}
    cells = {cell['id']: cell for cell in standard['cells']}
    assert len(parts) == len(shortlist['parts']), 'Duplicate part IDs'
    assert len(cells) == len(standard['cells']), 'Duplicate cell IDs'
    assert sum(p['count'] for p in standard['pot_roles']) == 101
    bindings = standard['pot_bindings']
    assert len({p['panel_uid'] for p in bindings}) == 101
    assert Counter(p['role'] for p in bindings) == {p['role']: p['count'] for p in standard['pot_roles']}
    for binding in bindings:
        policy = next(p for p in standard['pot_roles'] if p['role'] == binding['role'])
        assert binding['part_id'] == policy['part_id']
    assert len(standard['defaults_disposition']) == 14
    for role in standard['roles'].values():
        part = parts[role['part_id']]
        assert role['package'] == part['package']
        assert role['units_per_package'] == 4
    for cell in cells.values():
        assert cell['authority'] == standard['authority']
        assert cell['verification_status'] == 'NEEDS BENCH'
        assert len({p['ref'] for p in cell['parts']}) == len(cell['parts']), cell['id']
        for dependency in cell['uses']:
            assert dependency in cells, dependency
        for part in cell['parts']:
            if 'part_id' in part:
                assert part['part_id'] in parts, part
            else:
                assert part['opamp_role'] in standard['roles'], part
            if 'value' in part:
                assert part['value'] > 0 and part['unit'] in ('F', 'ohm')
            assert part['terminals'], part
    for part in parts.values():
        assert part['manufacturer'] and part['mpn'] and part['package']
        assert part['sourcing']['checked_date'] == standard['date']
        assert part['sourcing']['status']
        assert not part['lcsc'] or (part['lcsc'][0] == 'C' and part['lcsc'][1:].isdigit())
    for source in read('source-receipts.json')['sources']:
        assert len(source['sha256']) == 64
        if source['availability'] == 'SOURCE UNAVAILABLE':
            assert source['sha256'] == '0' * 64
        else:
            assert source['sha256'] != '0' * 64

    totals = dict.fromkeys(standard['roles'], 0)
    assert sum(m['instances'] for m in budget['modules']) == 33
    assert sum(m['input_jacks'] for m in budget['modules']) == 98
    assert sum(m['instances'] * m['planning_sections_per_instance'] for m in budget['modules']) == 225
    for module in budget['modules']:
        assert sum(module['sections_per_instance'].values()) == module['planning_sections_per_instance']
        for role, count in module['sections_per_instance'].items():
            expected = math.ceil(count / 4) * module['instances']
            assert module['quads_by_role'][role] == expected
            totals[role] += expected
    for extra in budget['additional_allocations']:
        assert extra['packages'] == math.ceil(extra['sections'] / 4)
        totals[extra['role']] += extra['packages']
    assert totals == budget['whole_quad_packages_by_role']
    for role, count in totals.items():
        allocation = next(x for x in budget['loads'] if x['id'] == 'opamp_' + role)
        assert allocation['quantity'] == count
        expected_iq = 6 if role == 'precision' else 1
        assert allocation['planning_unit_mA']['+12V'] == expected_iq
        assert allocation['planning_unit_mA']['-12V'] == expected_iq
    failures = []
    for rail, row in budget['rails'].items():
        for key, output in [('typical_unit_mA', 'typical_estimate_mA'), ('planning_unit_mA', 'planning_estimate_mA')]:
            value = sum(x['quantity'] * x[key][rail] for x in budget['loads'])
            assert abs(value - row[output]) < 1e-6, (rail, output)
        assert row['ceiling_mA'] == row['supply_target_mA'] * 0.8
        assert abs(row['headroom_mA'] - (row['ceiling_mA'] - row['planning_estimate_mA'])) < 1e-6
        assert row['within_ceiling'] == (row['headroom_mA'] >= 0)
        if not row['within_ceiling']:
            failures.append(rail)
        print(f"BUDGET {rail}: {row['planning_estimate_mA']:.3f} mA / {row['ceiling_mA']:.3f} mA; "
              + ('WITHIN planning ceiling' if row['within_ceiling'] else 'OVER planning ceiling'))
    assert failures == ['-12V'], 'Revise documented budget resolution when the rail result changes'
    assert budget['ceiling_resolution'], 'An overage requires a recorded decision path'

    def values(cell):
        return {p['ref']: p['value'] for p in cells[cell]['parts'] if 'value' in p}

    gate = values('gate_trigger_input')
    ref = values('reference_generator')
    vref = 5 * ref['R_GBOT'] / (ref['R_GTOP'] + ref['R_GBOT'])
    rref, rhys, rpull = (gate[k] for k in ['R_REF', 'R_HYS', 'R_PULL'])
    threshold_low = vref * rhys / (rhys + rref)  # ideal comparator VOL = 0
    threshold_high = (vref / rref + 5 / (rhys + rpull)) / (1 / rref + 1 / (rhys + rpull))
    ratio = gate['R_SHIFT_IN'] / gate['R_SHIFT_REF']
    falling = threshold_low * (1 + ratio) - 5 * ratio
    rising = threshold_high * (1 + ratio) - 5 * ratio
    assert 0.85 <= falling <= 1.15 and 1.35 <= rising <= 1.65 and rising > falling
    # Comparator's low rail is its output emitter potential, so gate logic needs ground.
    comparator = next(p for p in cells['gate_trigger_input']['parts'] if p['ref'] == 'U')
    assert comparator['terminals']['GND'] == 'AGND'
    print(f'CALCULATED gate: rising {rising:.6f} V, falling {falling:.6f} V (ideal VOL=0)')
    for cell in ['general_output', 'precision_output']:
        resistors = values(cell)
        series = resistors['R_ISO_A'] + resistors['R_ISO_B']
        assert series == standard['signals']['output_series_ohm']
        current = 24 / series
        assert all(current * current * resistors[k] < 0.5 for k in ['R_ISO_A', 'R_ISO_B'])
    print(f'CALCULATED external ±12 V fault: {current * 1000:.6f} mA, {current**2 * 499:.6f} W per 499 ohm resistor')
    attenuation = values('bipolar_attenuverter')
    gain = attenuation['R_FB'] / attenuation['R_IN']
    endpoints = [(1 + gain) * position - gain for position in [0, 0.5, 1]]
    assert endpoints == [-1, 0, 1]
    print(f'CALCULATED unloaded ideal attenuverter gains: {endpoints}; remote/wiper loading requires simulation')
    magnitude = 5 / values('magnitude_indicator')['R_SENSE']
    assert abs(magnitude - standard['signals']['magnitude_5V_current_A']) < 1e-12
    slew = values('slew_island')
    capacitance = sum(v for k, v in slew.items() if k.startswith('C'))
    assert math.isclose(capacitance, 0.5e-6)
    assert math.isclose(slew['R_MIN'] * capacitance, 0.0011)
    print(f'CALCULATED slew tau: {slew["R_MIN"] * capacitance:.6f}..{(slew["R_MIN"] + 500000) * capacitance:.6f} s')
    assert {p['ref'] for p in cells['magnitude_indicator']['parts'] if p.get('part_id') == 'signal_diode'} == {'D1', 'D2', 'D3', 'D4'}
    print(f'PASS: {len(cells)} proposal cell definitions and {len(parts)} shortlist identities consistent; electrical qualification remains OPEN')
    print('HISTORICAL DEFICIT: original -12 V estimate exceeds its ceiling by 72.655 mA; #48 external requirement supersedes source intent. #52 captures a non-orderable boundary; exact circuit #59 and physical qualification #57 remain open.')


if __name__ == '__main__':
    check()
