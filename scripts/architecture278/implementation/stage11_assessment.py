"""Compose the bounded A01 refinement; never invoke native tools or simulation."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/architecture-278/implementation/stage11'
BASE = '4b1eb440c7cc270b5e9fcadaa8bab0d9539e1fd5'
PREFIXES = ('design/architecture-278/implementation/', 'scripts/architecture278/implementation/')
MUTABLE = {PREFIXES[0] + 'README.md', PREFIXES[0] + 'WORK.md', PREFIXES[1] + 'check_source.py'}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preserve(scope):
    need(scope['baseline_commit'] == BASE, 'wrong Stage10 baseline')
    paths = set(subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', BASE, *PREFIXES], cwd=ROOT,
        text=True).splitlines()) - MUTABLE
    claimed = scope['preserved_prior_source_sha256']
    need(set(claimed) == paths and len(paths) == 241, 'incomplete predecessor inventory')
    for path, sha in claimed.items():
        original = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
        need(sha == hashlib.sha256(original).hexdigest(), 'unbound predecessor digest ' + path)
        need(digest(ROOT / path) == sha, 'prior candidate changed ' + path)
    need(scope['instrument_invariants'] == {'OSC': 5, 'functions': 33, 'fixed_panel_centres': 438},
         'instrument scope changed')
    return len(paths)


def bindings(report):
    need(bool(report.get('source_sha256')), 'missing source bindings')
    for path, sha in report['source_sha256'].items():
        need(digest(ROOT / path) == sha, 'stale source binding ' + path)


def acceptance(report):
    keys = [key for key in ('hardware_acceptance', 'physical_acceptance') if key in report]
    need(bool(keys) and all(report[key] is False for key in keys), 'unreviewed domain acceptance')
    for key in ('native', 'simulation', 'physical'):
        if key in report:
            need(report[key] == 'NOT RUN', 'unreviewed execution claim')


def review_receipts():
    for role in ('root', 'code', 'electrical', 'mechanical'):
        path = OUT / ('review-' + role + '.json')
        need(path.exists(), 'missing independent review ' + role)
        review = json.loads(path.read_text())
        need(bool(review.get('authorship_exclusion')), 'review authorship boundary missing ' + role)
        bindings(review)


def finite(value):
    if isinstance(value, float):
        need(math.isfinite(value), 'nonfinite engineering result')
    elif isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)


def identities(report, inventory):
    rows = report['candidate_assignments']
    need(set(rows) == set(inventory['unselected_MPN_refs']) and len(rows) == 20,
         'candidate identity coverage')
    need(sum(ref.startswith('R') for ref in rows) == 17 and
         sum(ref.startswith('C') for ref in rows) == 3, 'resistor/capacitor inventory')
    for ref, row in rows.items():
        source = inventory['packages'][ref]
        need(row['ref'] == ref and row['pins'] == source['pins'] and
             row['footprint'] == source['footprint'] and
             row['role'] == source['attributes']['Role'] and
             row['captured_value'] == source['unit_records'][0]['value'],
             'identity detached from captured circuit ' + ref)
        rating = row['candidate_ratings']
        value = float(row['captured_value'].split()[0])
        need(math.isclose(value, rating['value_SI'], rel_tol=1e-12), 'candidate value changed ' + ref)
        tolerance = rating['tolerance_fraction']
        need(0 <= tolerance < 1, 'invalid component tolerance')
        expected = [value * (1 - tolerance), value * (1 + tolerance)]
        need(row['component_nominal_tolerance_interval_SI'] == expected,
             'candidate tolerance interval ' + ref)
        need(row['source_id'] in report['sources'], 'missing exact component evidence')
    cap = report['reference_capacitor_application']
    need(cap['tolerance_only_min_F'] < cap['application_output_min_F'] and
         cap['tolerance_only_establishes_application_min'] is False,
         'reference capacitor application gap hidden')
    need(report['canonical_BOM_changed'] is False and report['source_values_changed'] is False,
         'canonical identity/value mutation')
    return {'candidate_assignments': 20, 'resistors': 17, 'capacitors': 3,
            'reference_output_capacitor_qualified': False}


def endpoints(report, old, graph):
    rows = report['power_endpoint_comparison']
    original = {row['to']: row for row in old['power_and_return_endpoint_paths']}
    need(len(rows) == len(original) == 106 and {r['to'] for r in rows} == set(original),
         'power/return endpoint coverage')
    for row in rows:
        previous = original[row['to']]
        need(all(row[key] == previous[key] for key in ('net', 'source_boundary', 'edge_indices')),
             'power endpoint detached from source walk')
        here = row['source_boundary']
        gh = din = 0
        for index in row['edge_indices']:
            edge = graph['edges'][index]
            need(edge['net'] == row['net'] and here in (edge['from'], edge['to']), 'broken source walk')
            here = edge['to'] if here == edge['from'] else edge['from']
            gh += edge['mated_GH_contacts']
            din += edge['kind'] == 'DIN_mated_pair'
        need(here == row['to'] and gh == row['GH_contacts'] and din == row['DIN_contacts'],
             'power endpoint contact/path accounting')
        need(row['actual_complete_resistance_ohm'] is None and bool(row['unknown_terms']),
             'unknown complete resistance promoted')
    need(report['lowR_comparison']['selected_hardware'] is False,
         'unreviewed power hardware selection')
    return {'power_return_source_endpoints': 106, 'complete_resistance_qualified': False}


def feed_composition(electrical, support, graph, inventory):
    straps = support['low_R_feed_option']['straps']
    need(len(straps) == 3 and {s['net'] for s in straps} == {'+12V', '-12V', 'AGND'},
         'feed net inventory')
    by_net = {s['net']: s for s in straps}
    material = electrical['lowR_comparison']['strap']
    for strap in straps:
        need(strap['width_mm'] == material['width_mm'] and
             strap['thickness_mm'] == material['thickness_mm'] and
             strap['maximum_budget_mm'] == material['length_mm'] and
             0 < strap['developed_centerline_mm'] <= material['length_mm'],
             'mechanical/electrical feed dimensions detached')
    original = {r['to']: r for r in electrical['power_endpoint_comparison']}
    expected = {target for target in original if inventory['packages'][target.split(':')[0]]['owner'] == 'rear-core'}
    rows = electrical['lowR_complete_endpoint_paths']
    unchanged = electrical['lowR_unmodified_front_endpoint_targets']
    need(len(rows) == len(expected) and {r['to'] for r in rows} == expected and
         len(unchanged) == len(set(unchanged)) and set(unchanged) == set(original) - expected,
         'alternative/front endpoint partition')
    for row in rows:
        previous = original[row['to']]
        need(row['net'] == previous['net'] and row['source_boundary'] == previous['source_boundary'],
             'alternative endpoint source identity')
        strap = by_net[row['net']]
        anchor = 'A01:K-PWR:local:' + {'+12V': '1', '-12V': '2', 'AGND': '3'}[row['net']]
        coordinates = [graph['nodes'][row['source_boundary']]['pad_xyz_mm'], strap['middle_stud_xyz_mm'],
                       strap['rear_stud_xyz_mm'], graph['nodes'][anchor]['pad_xyz_mm']]
        segments = row['new_segments']
        need(len(segments) == 3, 'feed transfer segment omitted')
        total = 0
        for i, segment in enumerate(segments):
            start, end = coordinates[i:i+2]
            need(segment['from_xyz_mm'] == start and segment['to_xyz_mm'] == end,
                 'feed segment detached from stud or actual pad')
            if i == 1:
                length = strap['developed_centerline_mm']
                need(segment['joints'] == 2 and segment['maximum_material_budget_mm'] == material['length_mm'],
                     'feed joint/material allocation')
            else:
                dx, dy = sorted((abs(end[0]-start[0]), abs(end[1]-start[1])))
                length = 1.15 * (dy + (math.sqrt(2)-1) * dx) + 7 + abs(end[2]-start[2])
            need(math.isclose(segment['allocation_mm'], length, abs_tol=1e-9), 'feed transfer length')
            need(segment['resistance_ohm'] is None, 'unqualified feed resistance promoted')
            total += length
        current = anchor
        for index in row['retained_suffix_edge_indices']:
            edge = graph['edges'][index]
            need(edge['net'] == row['net'] and current in (edge['from'], edge['to']), 'broken feed suffix')
            current = edge['to'] if current == edge['from'] else edge['from']
            total += edge['allocated_developed_mm']
        need(current == row['to'] and math.isclose(total, row['complete_boundary_to_pad_allocation_mm'], abs_tol=1e-9),
             'complete alternative pad path')
        need(row['upstream_source_to_boundary_resistance_ohm'] is None and
             row['complete_source_to_pad_resistance_ohm'] is None, 'upstream or complete resistance promoted')
    return {'affected_rear_endpoints': len(rows), 'unchanged_front_endpoints': len(unchanged),
            'feed_selected': False}


def build():
    paths = {name: OUT / (name + '.json') for name in
             ('scope', 'identity-report', 'electrical-report', 'support-report')}
    reports = {name: json.loads(path.read_text()) for name, path in paths.items()}
    count = preserve(reports['scope'])
    for name in ('identity-report', 'electrical-report', 'support-report'):
        bindings(reports[name])
        finite(reports[name])
        acceptance(reports[name])
    prior = OUT.parent / 'stage10'
    prior_paths = {name: prior / (name + '.json') for name in
                   ('inventory-report', 'interfaces-report', 'electrical-report')}
    previous = {name: json.loads(path.read_text()) for name, path in prior_paths.items()}
    identity_counts = identities(reports['identity-report'], previous['inventory-report'])
    transport_counts = endpoints(reports['electrical-report'], previous['electrical-report'], previous['interfaces-report'])
    feed_counts = feed_composition(reports['electrical-report'], reports['support-report'],
                                   previous['interfaces-report'], previous['inventory-report'])
    result = {
        'status': 'BOUNDED A01 SOURCE REFINEMENT; ACCEPTANCE OPEN',
        'baseline_commit': BASE,
        'preserved_predecessor_files': count,
        'instrument_invariants': reports['scope']['instrument_invariants'],
        'source_instance': 'A01',
        'identity_crosscheck': identity_counts,
        'transport_crosscheck': transport_counts,
        'feed_crosscheck': feed_counts,
        'architecture_adopted': False,
        'hardware_acceptance': False,
        'native': 'NOT RUN', 'ERC': 'NOT RUN', 'DRC': 'NOT RUN',
        'simulation': 'NOT RUN', 'physical': 'NOT RUN',
        'source_sha256': {str(path.relative_to(ROOT)): digest(path) for path in
                          [*paths.values(), *prior_paths.values(), Path(__file__), Path(__file__).with_name('test_stage11_assessment.py')]},
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    body = json.dumps(build(), sort_keys=True, indent=2, allow_nan=False) + '\n'
    path = OUT / 'assessment-report.json'
    if args.check:
        need(path.read_text() == body, 'stale Stage11 composition')
        review_receipts()
    else:
        path.write_text(body)
    print('PASS bounded Stage11 source composition; acceptance remains OPEN')


if __name__ == '__main__':
    main()
