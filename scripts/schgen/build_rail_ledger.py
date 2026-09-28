#!/usr/bin/env python3
"""Audit physical rail connections and allocate whole module planning loads."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from design.spec.cells._builder import load_symbol
from design.spec.instrument import specification
from design.spec.modules.sample_hold import family as sample_hold_family
from scripts.schgen.build_master_budget import RAILS, build as master_budget
from scripts.schgen.core import designator

INPUT = ROOT / 'design/power/rail-allocation-input.json'
OUTPUT = ROOT / 'design/power/rail-ledger.json'
RAIL_ALIASES = {'NOISE_VDD': '+5V', 'VEE5': '-12V'}
FEEDS = ('A', 'B')
# Exact package supply pins from design/standard/pin-maps/*.json and the
# retained symbol/source pairing. Signal inputs tied to a rail are excluded.
SUPPLY_PIN_NUMBERS = {
    'REF5050AIDR': ('2', '4'), 'OPA4197IPWR': ('4', '11'),
    'OPA4196IDR': ('4', '11'), 'ADG5412FBRUZ': ('13', '4', '5'),
    'LM393BIDR': ('8', '4'), 'SN74HC14DR': ('14', '7'),
    'CD74HC221M96': ('16', '8'), 'LF398M_NOPB': ('12', '3', '10'),
    'AS3340D': ('16', '3', '12'), 'LM13700M_NOPB': ('11', '6'),
    'NOISE2': ('1', '8'), 'SN74HC00DR': ('14', '7'),
    'SN74HC74DR': ('14', '7'),
}


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate allocation key: {key}')
        result[key] = value
    return result


def read_allocation():
    return json.loads(INPUT.read_text(), object_pairs_hook=no_duplicate_keys)


@lru_cache(maxsize=1)
def physical_packages():
    families, instances = specification()
    family_by_name = {f.name: f for f in families}
    packages = {}
    for inst in instances:
        if inst.name == 'POWER':
            continue
        for part in family_by_name[inst.family].parts:
            if part.prefix != 'U' or part.dnp:
                continue
            ref = designator(part, inst)
            symbol = part.symbol.rsplit(':', 1)[-1]
            if symbol not in SUPPLY_PIN_NUMBERS:
                raise ValueError(f'IC supply pin map missing: {symbol}')
            package = packages.setdefault(ref, {'ref': ref, 'instance': inst.name,
                                                'symbol': symbol, 'supply_pins': {}})
            if package['symbol'] != symbol or package['instance'] != inst.name:
                raise ValueError(f'physical package collision: {ref}')
            library = load_symbol(symbol)
            pins = {p.number: p for p in library.units[part.unit]}
            for number, net in part.pins.items():
                if number not in SUPPLY_PIN_NUMBERS[symbol]:
                    continue
                if number not in pins or net is None:
                    raise ValueError(f'missing physical supply pin {ref}.{number}')
                if number in package['supply_pins'] and package['supply_pins'][number] != net:
                    raise ValueError(f'conflicting supply pin {ref}.{number}')
                package['supply_pins'][number] = net
    # Every fitted IC is a physical package. Sections of a multi-unit symbol share its ref.
    for p in packages.values():
        if set(p['supply_pins']) != set(SUPPLY_PIN_NUMBERS[p['symbol']]):
            raise ValueError(f"incomplete supply pin trace {p['ref']}: {p['supply_pins']}")
    return [{**p, 'supply_pins': dict(sorted(p['supply_pins'].items())),
             'rails': sorted({RAIL_ALIASES.get(n, n) for n in p['supply_pins'].values() if n != 'AGND'})}
            for p in sorted(packages.values(), key=lambda p: p['ref'])]


def worksheet_loads(report):
    """Expand each worksheet line once per fitted module, preserving its source unit."""
    loads = []
    for row in report['instances']:
        source_path = ROOT / row['source']
        source = json.loads(source_path.read_text())
        sheet = next((s for s in source['sheets'] if row['instance'] in s['instances']), None) if 'sheets' in source else source
        if sheet is None:
            raise ValueError(f"missing worksheet sheet {row['instance']}")
        subtotal = {r: 0.0 for r in RAILS}
        for index, item in enumerate(sheet['breakdown']):
            count = item.get('whole_packages', item.get('count', item.get('quantity', 1)))
            unit = item.get('planning_unit_mA', item.get('planning_maximum_unit_mA'))
            typical = item.get('typical_unit_mA')
            if unit is None or typical is None or not isinstance(count, (int, float)) or count <= 0:
                raise ValueError(f"invalid worksheet load {row['source']}:{index}")
            label = item.get('symbol', item.get('dynamic_load', item.get('load')))
            if not label:
                raise ValueError(f"unlabelled worksheet load {row['source']}:{index}")
            for rail in RAILS:
                if rail not in unit or rail not in typical:
                    raise ValueError(f"missing worksheet rail {row['source']}:{index}:{rail}")
                subtotal[rail] += count * unit[rail]
            loads.append({'id': f"{row['instance']}:{index}", 'instance': row['instance'],
                          'label': label, 'source': row['source'], 'source_row': index,
                          'count': count, 'unit': 'whole package' if 'whole_packages' in item or 'whole package' in label.lower() or label in
                          ('OPA4196IDR', 'OPA4197IPWR', 'ADG5412FBRUZ') else 'worksheet unit',
                          'reported_assumed_typical_mA': {r: round(count * typical[r], 6) for r in RAILS},
                          'planning_allowance_mA': {r: round(count * unit[r], 6) for r in RAILS},
                          'manufacturer_guaranteed_quiescent_only_mA':
                          {r: round(count * unit[r], 6) for r in RAILS}
                          if label in ('OPA4196IDR', 'OPA4197IPWR', 'OPA4196IDR whole quad package')
                          else None,
                          'quiescent_condition': 'Full-temperature zero-output-current, four channels per package; retained TI PDF physical page 7, printed page 8'
                          if label in ('OPA4196IDR', 'OPA4197IPWR', 'OPA4196IDR whole quad package') else None,
                          'guaranteed_complete_load_maximum_mA': {r: None for r in RAILS},
                          'guaranteed_maximum_reason': 'Worksheet source and operating conditions do not bound the complete dynamic/startup/fault load.',
                          'basis': item.get('basis', item.get('source', 'Worksheet planning assumption; see source row'))})
        for rail in RAILS:
            if abs(subtotal[rail] - row['planning_upper_subtotal_mA'][rail]) > 0.000002:
                raise ValueError(f"worksheet breakdown mismatch {row['instance']} {rail}: {subtotal[rail]} != {row['planning_upper_subtotal_mA'][rail]}")
    return loads


def build(allocation=None):
    source = read_allocation() if allocation is None else allocation
    budget = master_budget()
    packages = physical_packages()
    by_instance = defaultdict(list)
    for package in packages:
        by_instance[package['instance']].append(package)
    # Compare fitted IC identities to each report's package count. This catches omitted
    # multi-unit sections and stale worksheets without charging their quiescent draw twice.
    for row in budget['instances']:
        data = json.loads((ROOT / row['source']).read_text())
        sheet = next((s for s in data['sheets'] if row['instance'] in s['instances']), None) if 'sheets' in data else data
        declared = sheet.get('fitted_IC_packages_per_instance', sheet.get('IC_packages_per_instance',
                    sheet.get('fitted_package_count_per_instance', {})))
        actual = Counter(p['symbol'] for p in by_instance[row['instance']])
        for symbol, count in declared.items():
            if symbol in SUPPLY_PIN_NUMBERS and actual[symbol] != count:
                raise ValueError(f"package count mismatch {row['instance']} {symbol}: {actual[symbol]} != {count}")
        if not set(actual).issubset(declared):
            raise ValueError(f"unbudgeted IC package {row['instance']}: {set(actual)-set(declared)}")
    expected = {r['instance'] for r in budget['instances']}
    assignment = source['module_feed_assignment']
    if set(assignment) != expected or any(feed not in FEEDS for feed in assignment.values()):
        raise ValueError(f"missing/extra/invalid complete-module feed assignment: {expected ^ set(assignment)}")
    if set(source['inlet_count_by_feed']) != set(FEEDS) or any(source['inlet_count_by_feed'][f] != 1 for f in FEEDS):
        raise ValueError('each provisional feed needs exactly one complete inlet')
    loads = worksheet_loads(budget)
    assigned_loads = source['load_domain_assignment']
    expected_load_ids = {load['id'] for load in loads}
    if set(assigned_loads) != expected_load_ids:
        raise ValueError(f'missing/extra per-load allocation: {expected_load_ids ^ set(assigned_loads)}')
    for load in loads:
        entry = assigned_loads[load['id']]
        expected_rails = sorted(r for r in RAILS if load['planning_allowance_mA'][r] != 0)
        if entry.get('feed') != assignment[load['instance']] or sorted(entry.get('rails', [])) != expected_rails:
            raise ValueError(f"wrong feed or rail for load {load['id']}: {entry}")
        load['feed'] = entry['feed']
        load['active_rails'] = expected_rails
        if load['label'] in SUPPLY_PIN_NUMBERS:
            package_rails = {r for p in by_instance[load['instance']] if p['symbol'] == load['label'] for r in p['rails']}
            if not set(expected_rails).issubset(package_rails):
                raise ValueError(f"worksheet IC load assigned off actual supply pin: {load['id']}")
    noise_loads = [x for x in loads if x['instance'] == 'N1' and x['label'] == 'NOISE2 filtered digital supply']
    if (len(noise_loads) != 1 or noise_loads[0]['planning_allowance_mA']['+5V'] != 10 or
            noise_loads[0]['active_rails'] != ['+5V'] or
            len([p for p in by_instance['N1'] if p['symbol'] == 'NOISE2' and p['supply_pins'].get('1') == 'NOISE_VDD']) != 1):
        raise ValueError('NOISE2 +5 V filtered supply planning trace incomplete')
    if source.get('noise2_sensitivity', {}).get('extra_plus_5V_mA') != 10 or not source['noise2_sensitivity'].get('basis'):
        raise ValueError('NOISE2 20 mA sensitivity assumption missing')
    adjustments = source['required_draft_allowances']
    required = {f'{i}:{kind}' for i in ('H1', 'H2') for kind in ('reference', 'logic')}
    required |= {f'inlet:{f}:{r}' for f in FEEDS for r in RAILS}
    if set(adjustments) != required:
        raise ValueError(f'missing/extra required allowances: {required ^ set(adjustments)}')
    for key, item in adjustments.items():
        if item.get('planning_mA') is None or item['planning_mA'] < 0 or not item.get('basis') or item.get('sensitivity_multiplier', 0) < 1:
            raise ValueError(f'allowance requires finite planning value, basis and sensitivity: {key}')
        expected_rail = '+12V' if key.endswith(':reference') else '+5V' if key.endswith(':logic') else key.rsplit(':', 1)[1]
        if item.get('rail') != expected_rail:
            raise ValueError(f'wrong rail for {key}: {item.get("rail")} != {expected_rail}')
        if key.endswith(':reference'):
            if not any(p['symbol'] == 'REF5050AIDR' and expected_rail in p['rails'] for p in by_instance[key.split(':')[0]]):
                raise ValueError(f'REF5050 reference lacks {expected_rail} supply pin: {key}')
        if key.endswith(':logic'):
            if not any(p['symbol'] in ('SN74HC14DR', 'CD74HC221M96') and expected_rail in p['rails'] for p in by_instance[key.split(':')[0]]):
                raise ValueError(f'S&H logic lacks {expected_rail} supply pin: {key}')
    for p in packages:
        if not p['rails']:
            raise ValueError(f"powered IC lacks supply rail trace: {p['ref']} {p['symbol']}")
    per_feed = {f: {r: 0.0 for r in RAILS} for f in FEEDS}
    for row in budget['instances']:
        for rail in RAILS:
            per_feed[assignment[row['instance']]][rail] += row['planning_upper_subtotal_mA'][rail]
    # The original master total already includes one inlet. Move it to feed A,
    # then add the second complete inlet explicitly.
    bleeder = budget['synth_inlet']['worst_voltage_and_resistance_bleeder_current_mA']
    for feed in FEEDS:
        for rail in RAILS:
            per_feed[feed][rail] += bleeder[rail] * source['inlet_count_by_feed'][feed]
    for key, item in adjustments.items():
        feed = key.split(':')[1] if key.startswith('inlet:') else assignment[key.split(':')[0]]
        per_feed[feed][item['rail']] += item['planning_mA']
    totals = {r: round(sum(per_feed[f][r] for f in FEEDS), 6) for r in RAILS}
    excess = {r: round(max(0, totals[r] - len(FEEDS) * budget['design_ceiling_mA'][r]), 6) for r in RAILS}
    per_feed = {f: {r: round(v, 6) for r, v in per_feed[f].items()} for f in FEEDS}
    ramp = source['case_envelope']['startup_ramp']['increment_mA_per_inlet']
    startup = {f: {r: round(per_feed[f][r] + ramp[r] * source['inlet_count_by_feed'][f], 6)
                   for r in RAILS} for f in FEEDS}
    sensitivity = {f: dict(per_feed[f]) for f in FEEDS}
    for key, item in adjustments.items():
        feed = key.split(':')[1] if key.startswith('inlet:') else assignment[key.split(':')[0]]
        sensitivity[feed][item['rail']] = round(sensitivity[feed][item['rail']] +
                                         item['planning_mA'] * (item['sensitivity_multiplier'] - 1), 6)
    sensitivity[assignment['N1']]['+5V'] = round(sensitivity[assignment['N1']]['+5V'] +
                                              source['noise2_sensitivity']['extra_plus_5V_mA'], 6)
    sh_parts = {p.key: p for p in sample_hold_family().parts}
    prefix = 'precision_output_J_H1_OUT___R_ISO_'
    first, second = (sh_parts[prefix + suffix + '.0'] for suffix in ('A', 'B'))
    if first.value != '499 Ω' or second.value != '499 Ω' or first.pins['2'] != second.pins['1'] or second.pins['2'] != 'OUT_TIP':
        raise ValueError('S&H conditional short resistor path changed')
    short_current = round(12 / (499 + 499) * 1000, 6)
    if source['case_envelope']['fault_short']['conditional_resistor_path_current_mA'] != short_current:
        raise ValueError('S&H conditional short arithmetic drift')
    short_case = {f: dict(per_feed[f]) for f in FEEDS}
    for instance in ('H1', 'H2'):
        feed = assignment[instance]
        for rail in ('+12V', '-12V'):
            short_case[feed][rail] = round(short_case[feed][rail] + short_current, 6)
    return {'schema_version': 1, 'status': 'UNVALIDATED DRAFT; conditional planning cases only',
            'source': str(INPUT.relative_to(ROOT)), 'worksheet_loads': loads,
            'physical_ic_packages': packages, 'physical_package_count': len(packages),
            'module_feed_assignment': assignment, 'inlet_count_by_feed': source['inlet_count_by_feed'],
            'original_single_inlet_planning_mA': budget['reported_planning_upper_subtotal_mA'],
            'original_single_source_ceiling_mA': budget['design_ceiling_mA'],
            'original_single_source_excess_mA': budget['planning_subtotal_overshoot_mA'],
            'draft_allowances': adjustments, 'two_feed_planning_mA': per_feed,
            'conditional_startup_1ms_mA': startup, 'sensitivity_case_mA': sensitivity,
            'conditional_SH_short_resistor_case_mA': short_case,
            'two_feed_total_mA': totals, 'two_feed_total_excess_over_two_source_ceilings_mA': excess,
            'per_feed_excess_over_original_ceiling_mA': {f: {r: round(max(0, per_feed[f][r]-budget['design_ceiling_mA'][r]), 6) for r in RAILS} for f in FEEDS},
            'measured_source_capacity_mA': {r: None for r in RAILS},
            'guaranteed_whole_instrument_maximum_mA': {r: None for r in RAILS},
            'unknown_maximum_reasons': source['unknown_maximum_reasons'],
            'case_envelope': source['case_envelope'], 'excluded_combinations': source['excluded_combinations']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = build()
    body = json.dumps(report, indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if OUTPUT.read_text() != body:
            raise ValueError('rail-ledger.json drift')
    else:
        OUTPUT.write_text(body)
    print('PASS: physical IC packages', report['physical_package_count'], 'worksheet loads', len(report['worksheet_loads']))
    print('Two-feed conditional planning:', report['two_feed_planning_mA'])


if __name__ == '__main__':
    main()
