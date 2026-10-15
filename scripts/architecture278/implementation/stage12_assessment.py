"""Independent Stage12 composition; immutable history and no execution admission."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import stage11_assessment as previous

ROOT = previous.ROOT
OUT = ROOT / 'design/architecture-278/implementation/stage12'
BASE = '32317689d7e4b41b6c46c9f628d8b1156a3bf418'
need = previous.need
digest = previous.digest


def preserve(scope):
    need(scope['baseline_commit'] == BASE, 'wrong Stage11 baseline')
    paths = set(subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', BASE, *previous.PREFIXES],
        cwd=ROOT, text=True).splitlines()) - previous.MUTABLE
    hashes = scope['preserved_prior_source_sha256']
    need(set(hashes) == paths and len(paths) == 267, 'incomplete frozen predecessor inventory')
    for path, sha in hashes.items():
        original = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
        need(hashlib.sha256(original).hexdigest() == sha and digest(ROOT / path) == sha,
             'frozen predecessor changed ' + path)
    need(scope['instrument_invariants'] == {'OSC': 5, 'functions': 33, 'fixed_panel_centres': 438},
         'instrument scope changed')
    return len(paths)


def history(report):
    need(report['baseline_commit'] == BASE and len(report['records']) == 10,
         'criteria history coverage')
    need(len({row['id'] for row in report['records']}) == 10, 'duplicate criteria history')
    for row in report['records']:
        need(row['commit'] == BASE, 'criteria history checkpoint')
        spec = row['commit'] + ':' + row['path']
        raw = subprocess.check_output(['git', 'show', spec], cwd=ROOT)
        blob = subprocess.check_output(['git', 'rev-parse', spec], cwd=ROOT, text=True).strip()
        need(blob == row['git_blob'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
             'criteria historical bytes')
        lines = raw.decode().splitlines()
        need('\n'.join(lines[row['line_start']-1:row['line_end']]) == row['excerpt'],
             'criteria excerpt mismatch')
        url = 'https://github.com/Takazudo/zudo-osc-hole-field/blob/' + BASE + '/' + row['path'] + '#L' + str(row['line_start'])
        need(row['immutable_url'] == url and bool(row['classification']), 'criteria attribution')
    return 10


def reviews():
    for role in ('root', 'code', 'electrical', 'mechanical'):
        path = OUT / ('review-' + role + '.json')
        need(path.exists(), 'missing independent review ' + role)
        report = json.loads(path.read_text())
        need(bool(report.get('authorship_exclusion')), 'review authorship boundary')
        previous.bindings(report)


def resistance_mapping(report, graph, inventory, old_electrical):
    expected = {ref + ':' + pin: net for ref, package in inventory['packages'].items()
                for pin, net in package['pins'].items() if net in ('+12V', '-12V', '+5V', 'AGND')}
    rows = report['resistance_endpoint_mapping']
    need(len(rows) == len(expected) == 106 and {r['to']: r['net'] for r in rows} == expected,
         'resistance endpoint coverage')
    old = {r['to']: r for r in old_electrical['power_and_return_endpoint_paths']}
    usage = {}
    for row in old.values():
        for index in row['edge_indices']:
            usage[index] = usage.get(index, 0) + 1
    copper_kinds = {'local_source_copper', 'local_return_join', 'local_transport_branch',
                    'middle_copper', 'middle_power_copper', 'middle_AGND_copper', 'LED_local_copper'}
    other_domains = {
        'GH_harness': {'wire', 'crimp_termination', 'GH_mated_contact', 'GH_header_pin_termination'},
        'DIN_mated_pair': {'DIN_mated_contact', 'DIN_pin_termination'},
        'permanent_terminal_wire': {'wire', 'permanent_termination'},
    }
    for row in rows:
        old_row = old[row['to']]
        need(row['source_boundary'] == old_row['source_boundary'] and
             row['source_pad_xyz_mm'] == graph['nodes'][row['to']]['pad_xyz_mm'],
             'resistance actual source pad/boundary')
        terms = row['edge_terms']
        need([t['edge_index'] for t in terms] == old_row['edge_indices'], 'resistance edge walk omitted')
        for term in terms:
            edge = graph['edges'][term['edge_index']]
            kind = edge['kind']
            domains = {'PCB_spreading_necks_vias'} if kind in copper_kinds else other_domains.get(kind)
            need(domains is not None and set(term['domains']) == domains and len(term['domains']) == len(domains),
                 'resistance domain misclassification')
            need(term['kind'] == kind and term['from'] == edge['from'] and term['to'] == edge['to'] and
                 term['allocated_mm'] == edge['allocated_developed_mm'] and
                 term['wire_max_mm'] == edge['wire_cut_max_mm'] and
                 term['GH_contacts'] == edge['mated_GH_contacts'] and
                 term['DIN_contacts'] == int(kind == 'DIN_mated_pair'), 'resistance term detached')
            need(term['endpoint_walk_use_count'] == usage[term['edge_index']], 'shared edge usage mismatch')
            need(term['resistance_ohm'] is None and term['shared_current_A'] is None, 'unqualified conductor promoted')
        limit = .0005 if row['net'] == 'AGND' else .001
        need(row['original_plane_requirement']['limit_ohm'] == limit and
             row['expanded_architecture_comparison']['limit_ohm'] == limit and
             row['expanded_architecture_comparison']['accepted_redefinition'] is False,
             'historical limit relaxed or redefined')
        need(row['upstream_source_feed']['resistance_ohm'] is None and
             row['upstream_source_feed']['regulation_error_V'] is None and
             row['complete_transfer_error_V'] is None, 'unknown complete transfer promoted')
    need(report['resistance_accounting']['original_checks_preserved'] is True and
         report['resistance_accounting']['equal_sharing_credit'] is False, 'historical/shared-return boundary')
    return {'endpoints': 106, 'unique_physical_edges': len(usage), 'complete_transfer_qualified': False}


def criteria_boundaries(report, standard):
    criteria = report['criteria']
    cal = standard['calibration']
    need(criteria['static']['target_V'] == cal['static_precision_error_V'] and
         criteria['output_load_change']['target_V'] == cal['precision_output_load_error_V'] and
         criteria['pitch']['cents'] == cal['pitch_tracking_target_cents'] and
         criteria['pitch']['warmup_minutes'] == cal['warmup_minutes'], 'criteria numerical conflation')
    need(criteria['ideal_AO_runner']['executed'] is False and
         criteria['timing']['A01_settling_target_s'] is None, 'unadmitted execution or invented timing')
    need(bool(criteria['new_proposals']) and all(row['status'] == 'PROPOSED/UNAPPROVED'
                                              for row in criteria['new_proposals']), 'new criteria promoted')
    need(criteria['recommended_domain_mapping']['status'] == 'PROPOSED/UNAPPROVED; no existing check changed', 'domain reinterpretation promoted')
    need(report['complete_error_bound_V'] is None, 'unqualified complete DC budget promoted')


def capacitor_overlay(report, inventory):
    rows = report['overlay']
    packages = inventory['packages']
    need(set(rows) == {'C7101', 'C7102'}, 'capacitor overlay scope')
    part = report['part']
    need(part['MPN'] == 'CC0603KRX5R8BB475' and part['nominal_F'] == 4.7e-6 and
         part['tolerance_fraction'] == .1 and part['rated_voltage_V'] == 25 and
         part['temperature_range_C'] == [-55, 85], 'exact evaluated capacitor')
    for ref, row in rows.items():
        source = packages[ref]
        need(row['pins'] == source['pins'] and row['units'] == source['units'] and
             row['footprint'] == source['footprint'] and
             row['captured_MPN'] == source['attributes']['MPN'] and
             row['captured_value'] == source['unit_records'][0]['value'], 'capacitor detached from source')
        need(row['candidate_MPN'] == part['MPN'] and row['candidate_value_F'] == part['nominal_F'],
             'inconsistent capacitor candidate')
        minimum = part['nominal_F'] * (1 - part['tolerance_fraction'])
        maximum = part['nominal_F'] * (1 + part['tolerance_fraction'])
        need(row['initial_tolerance_interval_F'] == [minimum, maximum] and
             math.isclose(row['required_combined_retention_after_initial_min_for_1uF'], 1e-6 / minimum),
             'capacitor initial/retention arithmetic')
        need(row['application_minimum_proven'] is False and
             row['effective_C_at_bias_temperature_age_F'] is None and row['guaranteed_ESR_ohm'] is None,
             'typical capacitor response promoted')
    conservation = report['conservation']
    need(conservation['packages'] == len(packages) == 90 and conservation['units'] == 118 and
         conservation['all_source_refs'] == sorted(packages) and
         conservation['changed_value_refs'] == sorted(rows) and
         conservation['unchanged_refs'] == sorted(set(packages) - set(rows)) and
         not conservation['added_packages'] and not conservation['removed_packages'] and
         conservation['topology_changed'] is False, 'capacitor population conservation')
    topology = {ref: {key: package[key] for key in ('pins', 'units', 'footprint', 'owner')}
                for ref, package in packages.items()}
    sha = hashlib.sha256(json.dumps(topology, sort_keys=True).encode()).hexdigest()
    need(conservation['source_topology_sha256'] == sha, 'capacitor topology binding')
    need(report['input_bypass']['C7107_retained_F'] == 1e-7 and
         report['input_bypass']['effective_combined_C_F'] is None and
         report['canonical_values_changed'] is False and report['candidate_values_changed'] is True,
         'candidate/canonical capacitor boundary')
    need(report['ESR_assessment']['stability_proven'] is False and
         report['ESR_assessment']['noise_recommendation_proven'] is False,
         'ESR guarantee invented')
    return {'changed_candidate_values': sorted(rows), 'packages_preserved': 90,
            'correction_qualified': False}


def build():
    paths = {name: OUT / (name + '.json') for name in
             ('scope', 'criteria-history', 'capacitor-report', 'budget-report')}
    reports = {name: json.loads(path.read_text()) for name, path in paths.items()}
    count = preserve(reports['scope'])
    history_count = history(reports['criteria-history'])
    for name in ('capacitor-report', 'budget-report'):
        previous.bindings(reports[name])
        previous.finite(reports[name])
        previous.acceptance(reports[name])
    prior_paths = [OUT.parent / 'stage10' / (name + '.json') for name in
                   ('inventory-report', 'interfaces-report', 'electrical-report')]
    inventory, graph, old_electrical = [json.loads(p.read_text()) for p in prior_paths]
    standard_path = ROOT / 'design/standard/electrical-standard.json'
    mapped = resistance_mapping(reports['budget-report'], graph, inventory, old_electrical)
    criteria_boundaries(reports['budget-report'], json.loads(standard_path.read_text()))
    cap_counts = capacitor_overlay(reports['capacitor-report'], inventory)
    sources = [*paths.values(), Path(__file__), Path(previous.__file__),
               *prior_paths, standard_path, Path(__file__).with_name('test_stage12_assessment.py')]
    return {
        'status': 'BOUNDED A01 SOURCE STUDY; ACCEPTANCE OPEN',
        'baseline_commit': BASE,
        'preserved_predecessor_files': count,
        'immutable_criteria_excerpts': history_count,
        'resistance_mapping_crosscheck': mapped,
        'capacitor_overlay_crosscheck': cap_counts,
        'instrument_invariants': reports['scope']['instrument_invariants'],
        'mechanical_geometry_changed': False,
        'canonical_source_changed': False,
        'architecture_adopted': False, 'hardware_acceptance': False,
        'native': 'NOT RUN', 'ERC': 'NOT RUN', 'DRC': 'NOT RUN',
        'simulation': 'NOT RUN', 'physical': 'NOT RUN',
        'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sources},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = json.dumps(build(), sort_keys=True, indent=2, allow_nan=False) + '\n'
    path = OUT / 'assessment-report.json'
    if args.check:
        need(path.read_text() == text, 'stale Stage12 assessment')
        reviews()
    else:
        path.write_text(text)
    print('PASS Stage12 source composition; geometry frozen; acceptance OPEN')


if __name__ == '__main__':
    main()
