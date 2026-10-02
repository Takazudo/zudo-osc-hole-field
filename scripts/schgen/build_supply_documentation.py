#!/usr/bin/env python3
"""Render current power allocation sections from the checked supply report."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAILS = ('+12V', '-12V', '+5V')


def triple(values, factor=1, digits=3):
    return ' / '.join(f'{values[r] * factor:.{digits}f}' for r in RAILS)


def sections(report):
    selected = report['selected_requirement']
    contract = report['contract']
    requirement = contract['source_requirement']
    harness = contract['inlet']['harness']
    counts = report['allocation_counts']
    caps = report['implementation']['actual_fitted_capacitor_inventory']
    fitted = {r: caps[r]['captured_fitted_nominal_uF'] for r in RAILS}
    remaining = {r: caps[r]['remaining_nominal_uF_before_unplaced_board_bulk'] for r in RAILS}
    rows = [
        ('Normal planning load including allowances', selected['normal_with_allowances_mA'], 'mA', 3),
        ('Minimum continuous delivery', selected['minimum_continuous_mA'], 'mA', 0),
        (f"Minimum transient delivery for at least {requirement['transient_requirement_duration_ms']} ms", selected['minimum_transient_mA'], 'mA', 0),
        ('Maximum delivered current, including limiter tolerance', requirement['maximum_delivered_current_mA'], 'mA', 0),
        ('Full capacitance ramp increment', selected['full_capacitance_ramp_increment_mA'], 'mA', 2),
    ]
    table = ['| Requirement | +12 V | −12 V (magnitude) | +5 V |', '| --- | --- | --- | --- |']
    for title, values, unit, digits in rows:
        table.append('| ' + title + ' | ' + ' | '.join(f'{values[r]:,.{digits}f} {unit}' for r in RAILS) + ' |')
    for title, key in [('Source magnitude band, including ripple', 'voltage_magnitude_at_source_V'), ('Required voltage magnitude at load', 'required_load_voltage_magnitude_V')]:
        table.append('| ' + title + ' | ' + ' | '.join(f'{requirement[key][r][0]:.2f}…{requirement[key][r][1]:.2f} V' for r in RAILS) + ' |')
    summary = (f"All {counts['signal_modules']} signal modules, the shared reference, {counts['worksheet_loads']} worksheet loads and {counts['physical_IC_packages']} fitted IC packages belong to `EXT`. These counts describe the captured master; the separate protection candidate is not a fitted implementation.\n\n" + '\n'.join(table) + '\n\nThese are conditional planning requirements, not measured source capacity or guaranteed whole-instrument maxima. Source, inlet and mate remain **NOT SELECTED**; protection remains open in #59 and physical qualification **NOT RUN** in #57.')
    cap_summary = (f"The captured master rail-attributed capacitor inventory is **{triple(fitted, digits=1)} µF** on +12/−12/+5 V, leaving **{triple(remaining, digits=1)} µF** nominal against the source-contract ceilings before unplaced board bulk. Local VEE5 and filtered NOISE_VDD capacitors count against their upstream rails. This is the master inventory, not a census of completed board copper or the unfitted protection candidate. Reconcile every board reservoir and selected protection capacitor; per-pin proximity and effective ceramic capacitance remain open.")
    ret = (f"The checker allows the full **{selected['worst_single_return_contact_A']:.1f} A** maximum delivered-current sum in any one AGND conductor. At **{selected['max_conductor_path_ohm']:.3f} Ω** per complete conductor, the worst return shift is **{selected['worst_return_shift_V']*1000:.0f} mV**. Source maxima plus this shift are **{triple(selected['source_maximum_plus_return_shift_V'])} V**. The separate current allocations are **{harness['max_protection_drop_V']*1000:.0f} mV** for protection and **{harness['max_distribution_drop_V']*1000:.0f} mV** for board distribution. Including these allocations, worst total rail-plus-return losses are **{triple(selected['worst_rail_plus_return_loss_V'], 1000, 0)} mV**.\n\nMinimum continuous delivery evaluated at source-band maxima requires **{selected['required_continuous_output_power_W']:.2f} W**; this is not an upper delivered-power or fault-power ceiling. Protection dissipation allocations are **{triple(selected['protection_dissipation_allocation_W_per_rail'], 1000, 0)} mW**, and the conservative single return path dissipates **{selected['worst_return_path_transient_dissipation_W']:.4f} W**. These calculations depend on the declared wire/contact/current bounds; installed temperature rise, source losses and limiter dynamics are unqualified. Ground is not fused, switched or disconnected to cure a loop.")
    comparison = ['Current-load recalculation against the historical pinned-source ceilings; these are rejected architecture comparisons, not selected hardware.', '', '| Domain | Normal +12 / −12 / +5 mA | Conditional ramp/fault +12 / −12 / +5 mA | −12 V margin | Status |', '| --- | --- | --- | --- | --- |']
    for domain, row in report['three_source_evaluation'].items():
        comparison.append(f"| {domain} | {triple(row['normal_with_allowances_mA'])} | {triple(row['conditional_10ms_start_and_one_fault_mA'])} | {row['margin_to_pinned_ceiling_mA']['-12V']:.3f} mA | {row['status']} |")
    comparison.extend(['', f"The current single-source comparison is **{triple(report['original_single_source']['planning_mA'])} mA**. The two-source −12 V excess is **{report['rejected_two_source_excess_mA']['-12V']:.3f} mA**. Three is only the aggregate arithmetic candidate count; the declared domain allocation still fails where the table reports a negative margin."])
    return {'power-current': summary, 'power-capacitance': cap_summary, 'power-return': ret, 'power-comparison': '\n'.join(comparison)}


TARGETS = {
    'doc/src/content/docs/architecture/osc-power.mdx': ('power-current', 'power-capacitance'),
    'doc/src/content/docs/decisions/osc-supply-architecture.mdx': ('power-current', 'power-return', 'power-comparison'),
    'design/power/downstream-handoff-52.md': ('power-capacitance',),
}


def render(text, name, body, mdx):
    start = '{/* ' + name + ':start */}' if mdx else '<!-- ' + name + ':start -->'
    end = '{/* ' + name + ':end */}' if mdx else '<!-- ' + name + ':end -->'
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f'{name}: expected exactly one generated section')
    result, count = re.subn(re.escape(start) + r'.*?' + re.escape(end), lambda _: start + '\n\n' + body + '\n\n' + end, text, flags=re.S)
    if count != 1:
        raise ValueError(f'{name}: invalid section order')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    bodies = sections(json.loads((ROOT / 'design/power/supply-architecture.json').read_text()))
    for relative, names in TARGETS.items():
        path = ROOT / relative
        old = path.read_text()
        new = old
        for name in names:
            new = render(new, name, bodies[name], path.suffix == '.mdx')
        if args.check and old != new:
            raise SystemExit(f'Power documentation drift: {relative}')
        if not args.check:
            path.write_text(new)
    print('PASS: current power documentation matches supply report; physical qualification NOT RUN')


if __name__ == '__main__':
    main()
