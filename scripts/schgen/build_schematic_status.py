#!/usr/bin/env python3
"""Render planning-current sections from the master budget, preserving unknowns."""
from __future__ import annotations

import argparse
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.schgen.build_master_budget import RAILS
from scripts.schgen.build_supply_documentation import render

REPORT = ROOT / 'design/power/rail-budget.json'
PAGE = ROOT / 'doc/src/content/docs/verification/osc-schematic-status.mdx'


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f'expected a numeric current, got {value!r}')
    result = Decimal(str(value))
    if not result.is_finite() or result < 0:
        raise ValueError(f'invalid current: {value!r}')
    return result


def display(value):
    return f'{number(value):,.3f}'


def maximum(values):
    # Validate every known entry, even if another entry is unknown.
    known = [number(value) for value in values if value is not None]
    return 'NOT ESTABLISHED' if len(known) != len(values) else f'{sum(known):,.3f}'


def sections(report):
    if report['units'] != 'mA':
        raise ValueError('expected mA master budget')
    rows = report['instances']
    expected = report['module_instance_count'] + report['shared_reference_count']
    if len(rows) != expected or len({r['instance'] for r in rows}) != expected:
        raise ValueError('missing or duplicate master current instance')
    families = defaultdict(list)
    for row in rows:
        if type(row['partial']) is not bool:
            raise ValueError('partial-current scope must be explicit')
        for rail in RAILS:
            number(row['planning_upper_subtotal_mA'][rail])
        families[row['family']].append(row)
    rail_table = [
        'Rounded display of reported arithmetic (mA); complete values remain in `design/power/rail-budget.json`. These planning upper subtotals are not certified upper bounds.', '',
        '| Rail | Reported/assumed typical subtotal | Planning upper subtotal | Historical 80% source ceiling | Planning subtotal excess |',
        '| --- | ---: | ---: | ---: | ---: |',
    ]
    for rail in RAILS:
        fields = ('reported_assumed_typical_subtotal_mA', 'reported_planning_upper_subtotal_mA', 'design_ceiling_mA', 'planning_subtotal_overshoot_mA')
        rail_table.append('| ' + rail + ' | ' + ' | '.join(display(report[key][rail]) for key in fields) + ' |')
    rail_table += ['', 'Complete typical current (+12/−12/+5 mA): ' + ' / '.join(maximum([report['complete_typical_mA'][r]]) for r in RAILS) + '. Guaranteed maximum current: ' + ' / '.join(maximum([report['guaranteed_maximum_mA'][r]]) for r in RAILS) + '.']
    family_table = [
        'Current worksheet subtotals, rounded to 0.001 mA. The shared octave reference is listed separately. Unknown maxima remain unknown; a planning subtotal never substitutes for them.', '',
        '| Family / sheet | Instances | Planning +12 / −12 / +5 mA | Guaranteed maximum +12 / −12 / +5 mA | Scope |',
        '| --- | --- | --- | --- | --- |',
    ]
    for family, items in sorted(families.items()):
        totals = [f'{sum(number(row["planning_upper_subtotal_mA"][rail]) for row in items):,.3f}' for rail in RAILS]
        maxima = [maximum([row['guaranteed_maximum_mA'][rail] for row in items]) for rail in RAILS]
        scope = '**Partial known subtotal; omitted loads remain unbounded**' if any(row['partial'] for row in items) else 'Planning worksheet only'
        family_table.append('| `' + family + '` | ' + ', '.join(row['instance'] for row in items) + ' | ' + ' / '.join(totals) + ' | ' + ' / '.join(maxima) + ' | ' + scope + ' |')
    bleeders = report['synth_inlet']['worst_voltage_and_resistance_bleeder_current_mA']
    family_table += ['| POWER | POWER | ' + ' / '.join(display(bleeders[r]) for r in RAILS) + ' | NOT ESTABLISHED on every rail | Bleeder allowance only; leakage/startup/fault loads unbounded |']
    return {'schematic-rail-current': '\n'.join(rail_table), 'schematic-family-current': '\n'.join(family_table)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    old = PAGE.read_text()
    new = old
    for name, body in sections(json.loads(REPORT.read_text())).items():
        new = render(new, name, body, True)
    if args.check and old != new:
        raise SystemExit('Schematic-status current documentation drift')
    if not args.check:
        PAGE.write_text(new)
    print('PASS: schematic-status current sections match master budget; hardware unvalidated')


if __name__ == '__main__':
    main()
