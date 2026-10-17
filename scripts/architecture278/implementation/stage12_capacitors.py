"""One source-only reference capacitor overlay; no simulator or hardware calls."""
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/architecture-278/implementation/stage12'
MPN = 'CC0603KRX5R8BB475'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze(spec, inventory, predecessor):
    packages = inventory['packages']
    need(len(packages) == 90 and sum(len(p['units']) for p in packages.values()) == 118,
         'complete source package/unit inventory')
    need(spec['candidate_only'] is True and set(spec['overlay']) == {'C7101', 'C7102'},
         'one bounded two-value overlay')
    part = spec['part']
    need(part['MPN'] == MPN and part['nominal_F'] == 4.7e-6 and
         part['tolerance_fraction'] == .1 and part['rated_voltage_V'] == 25 and
         part['temperature_range_C'] == [-55, 85] and part['dielectric'] == 'X5R',
         'exact reviewed capacitor specification')
    need(part['dimensions_mm'] == [1.6, .8, .8] and
         part['dimension_tolerances_mm'] == [.15, .15, .15], 'package dimensions')
    for key in ('guaranteed_bias_retention', 'guaranteed_aging_rate', 'guaranteed_ESR_ohm'):
        need(part[key] is None, 'typical data cannot become guarantee')
    ev = spec['evidence']['capacitor']
    need(ev['url'].endswith('/specsheet/' + MPN) and
         ev['sha256'] == '2b7228d96d8ef926d5ed25553740890bb34ebc08db6b8529b180db87b30be7de',
         'exact primary document binding')
    need(ev['physical_pdf_page_index'] == 0 and ev['printed_page_label'] == 'unlabelled' and
         [r['physical_pdf_page_index'] for r in ev['additional_locators']] == [1, 2, 3],
         'specification and typical disclaimer locators')
    need(spec['evidence']['reference'] == predecessor['sources']['REF50-app'] and
         spec['application'] == predecessor['REF5050_application'], 'REF5050AI application binding')
    app = spec['application']
    need(app['output_cap_range_F'] == [1e-6, 50e-6] and
         app['recommended_input_bypass_F'] == [1e-6, 1e-5] and
         app['stability_ESR_max_ohm'] == 1.5 and app['noise_recommended_ESR_ohm'] == [1, 1.5],
         'stability and noise criteria remain separate')
    need(spec['unchanged_local_bypass'] == 'C7107' and
         packages['C7107']['unit_records'][0]['value'] == '100 nF' and
         packages['C7107']['pins'] == {'1': '+12V', '2': 'AGND'} and
         packages['C7107']['source_package']['decouples_ref'] == 'U7101',
         'retained local bypass association')
    need(spec['operating_assumptions']['input_proposed_rail_envelope_V'] == 13.2,
         'retained proposed rail envelope')
    rows = {}
    for ref, choice in spec['overlay'].items():
        p = packages[ref]
        need(choice['pins'] == p['pins'] and choice['units'] == p['units'] and
             choice['footprint'] == p['footprint'] == 'zudo-osc-hole-field:C0603',
             'whole-package topology preserved')
        need(choice['captured_value'] == p['unit_records'][0]['value'] and
             choice['captured_MPN'] == p['attributes']['MPN'], 'captured identity preserved')
        expected = {'1': '+12V' if ref == 'C7101' else '/A01/C534b2a_RAW_5V', '2': 'AGND'}
        need(p['pins'] == expected and choice['candidate_MPN'] == MPN and
             choice['candidate_value_F'] == part['nominal_F'], 'exact overlay net/value')
        bias = spec['operating_assumptions'][ref + '_bias_V']
        need(bias == (12 if ref == 'C7101' else 5), 'nominal bias assumption')
        reading = spec['typical_visual_readings'][str(bias) + 'V_retained_fraction_interval']
        need(len(reading) == 2 and all(math.isfinite(v) and 0 < v <= 1 for v in reading)
             and reading[0] <= reading[1], 'finite typical reading interval')
        initial_min = part['nominal_F'] * (1 - part['tolerance_fraction'])
        rows[ref] = {**choice, 'nominal_bias_V': bias,
            'initial_tolerance_interval_F': [initial_min, part['nominal_F'] * 1.1],
            'required_combined_retention_after_initial_min_for_1uF': 1e-6 / initial_min,
            'typical_plot_nominal_C_interval_F': [part['nominal_F'] * v for v in reading],
            'typical_plot_scope': spec['typical_visual_readings']['scope'],
            'effective_C_at_bias_temperature_age_F': None, 'guaranteed_ESR_ohm': None,
            'application_minimum_proven': False,
            'local_initial_value_gap_removed': initial_min >= 1e-6,
            'status': 'EVALUATED CANDIDATE ONLY; APPLICATION PROOF INCOMPLETE'}
    corner = spec['typical_visual_readings']['13.2V_retained_fraction_interval']
    need(len(corner) == 2 and all(math.isfinite(v) and 0 < v <= 1 for v in corner)
         and corner[0] <= corner[1], 'finite proposed-rail reading')
    rows['C7101']['proposed_13p2V_envelope_diagnostic'] = {
        'typical_plot_nominal_C_interval_F': [part['nominal_F'] * v for v in corner],
        'guaranteed_effective_C_F': None,
        'scope': 'Retained interface13.2V proposal. Typical nominal interval crosses1uF before tolerance/temperature/aging; not a proven failure bound or qualification.'}
    topology = {r: {k: p[k] for k in ('pins', 'units', 'footprint', 'owner')}
                for r, p in packages.items()}
    return {'status': 'ONE CAPACITOR CORRECTION OVERLAY; NOT QUALIFIED',
        'overlay_id': spec['overlay_id'], 'overlay': rows, 'part': part,
        'conservation': {'packages': 90, 'units': 118, 'all_source_refs': sorted(packages),
            'changed_value_refs': ['C7101', 'C7102'], 'unchanged_refs': sorted(set(packages) - set(rows)),
            'added_packages': [], 'removed_packages': [], 'topology_changed': False,
            'source_topology_sha256': hashlib.sha256(json.dumps(topology, sort_keys=True).encode()).hexdigest()},
        'input_bypass': {'captured_nominal_total_F': 2e-7, 'candidate_nominal_total_F': 4.8e-6,
            'C7107_retained_F': 1e-7, 'effective_combined_C_F': None,
            'scope': 'C7101 evaluated alone against1uF; no unproven effective contribution from C7107 credited.'},
        'reference_application': app,
        'ESR_assessment': {'stability_limit_ohm': 1.5, 'noise_recommendation_ohm': [1, 1.5],
            'guaranteed_actual_ESR_ohm': None, 'stability_proven': False, 'noise_recommendation_proven': False,
            'scope': 'Typical frequency curves are not bounds at all relevant conditions. DF alone without specified test frequency cannot establish application ESR. No series resistor added; that would change topology and require separate scope.'},
        'condition_assessment': {'bias': '5V output and12V input nominal; retained interface proposal extends to13.2V. Hardware rail overshoot/startup bound remains unknown',
            'temperature': 'Exact candidate rated-55..85C; no assumption of prior X7R125C capability. Joint bias/temperature bounds unavailable.',
            'tolerance': '4.23..5.17uF initial tolerance only; not biased/aged guarantee',
            'aging': 'Exact guaranteed aging rate, de-aging reference/time and required service lifetime unknown; no family-rate borrowing.',
            'required_temperature_range_C': spec['operating_assumptions']['required_operating_temperature_C'],
            'required_service_lifetime_hours': spec['operating_assumptions']['service_lifetime_hours']},
        'next_constraint': 'Need guaranteed combined bias/temperature/age effectiveC and applicable ESR for this exact part, plus defined operating envelope; current overlay cannot be accepted as a closed correction. No additional topology authorized here.',
        'evidence': spec['evidence'], 'canonical_values_changed': False,
        'candidate_values_changed': True, 'hardware_acceptance': False,
        'native': 'NOT RUN', 'simulation': 'NOT RUN', 'physical': 'NOT RUN'}


def build():
    paths = [OUT / 'capacitor-input.json', OUT.parent / 'stage10/inventory-report.json',
             OUT.parent / 'stage11/identity-input.json']
    data = [json.loads(p.read_text()) for p in paths]
    result = analyze(*data)
    paths += [Path(__file__), Path(__file__).with_name('test_stage12_capacitors.py'),
              ROOT / 'scripts/checks/partition35.py']
    result['source_sha256'] = {str(p.relative_to(ROOT)): digest(p) for p in paths}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    body = json.dumps(build(), indent=2, sort_keys=True, allow_nan=False) + '\n'
    dest = OUT / 'capacitor-report.json'
    if args.check:
        need(dest.read_text() == body, 'stale capacitor overlay report')
    else:
        dest.write_text(body)
    print('One2-capacitor overlay/90packages preserved; effectiveC/ESR acceptance OPEN')


if __name__ == '__main__':
    main()
