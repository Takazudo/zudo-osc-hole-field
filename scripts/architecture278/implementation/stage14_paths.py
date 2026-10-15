"""Rebind the frozen Stage13 capacitor overlay to complete source allocations.

This is graph accounting, not copper routing, circuit simulation or acceptance.
"""
import argparse
import copy
import json
from pathlib import Path

import stage10_interfaces as interface
import stage11_electrical as electrical
import stage11_assessment as common
import stage12_budget as budget

ROOT = common.ROOT
OUT = ROOT / 'design/architecture-278/implementation/stage14'
need = common.need


def read(relative):
    return json.loads((OUT.parent / relative).read_text())


def delta_rows(before, after, key, metric):
    old = {key(row): row for row in before}
    need(len(old) == len(before) == len(after), 'path count changed')
    need(set(old) == {key(row) for row in after}, 'path identity changed')
    result = []
    for row in after:
        prev = old[key(row)]
        need(row['edge_indices'] == prev['edge_indices'], 'path topology changed')
        if row[metric] != prev[metric]:
            result.append({'net': row['net'], 'to': row['to'],
                           'before_allocated_mm': prev[metric],
                           'after_allocated_mm': row[metric],
                           'delta_allocated_mm': row[metric] - prev[metric],
                           'edge_indices': row['edge_indices'], 'routed_mm': None})
    return result


def analyze(overlay, old_graph, old_paths, mech, inv, spec, support, old_electrical):
    # Regenerate from every actual pad, retaining the original graph construction.
    candidate = copy.deepcopy(mech)
    candidate['placements'] = overlay['placements']
    graph, paths = interface.analyze(spec, candidate, inv)
    changed_nodes = {key for key in graph['nodes'] if graph['nodes'][key] != old_graph['nodes'][key]}
    expected_nodes = {f'{ref}:{pin}' for ref in ('C7101', 'C7102') for pin in ('1', '2')}
    need(changed_nodes == expected_nodes, 'exact four changed pads required')
    need(set(graph['nodes']) == set(old_graph['nodes']), 'graph nodes changed')
    for key in expected_nodes:
        a, b = graph['nodes'][key], old_graph['nodes'][key]
        need({k:v for k,v in a.items() if k != 'pad_xyz_mm'} ==
             {k:v for k,v in b.items() if k != 'pad_xyz_mm'}, 'pad net or identity changed')
        ref, pin = key.split(':')
        need(a['pad_xyz_mm'] == overlay['placements'][ref]['pads_xyz_mm'][pin][0], 'overlay pad binding')
    need(len(graph['edges']) == len(old_graph['edges']), 'edge inventory changed')
    incident = {i for i,e in enumerate(old_graph['edges']) if changed_nodes.intersection((e['from'],e['to']))}
    declared = {i for row in overlay['endpoint_delta_and_invalidation']['changed_source_pads']
                for i in row['invalidated_incident_graph_edges']}
    need(incident == declared and len(incident) == 5, 'all invalidated edges required')
    edge_changes = []
    for i,(old,new) in enumerate(zip(old_graph['edges'],graph['edges'])):
        need({k:v for k,v in old.items() if k != 'allocated_developed_mm'} ==
             {k:v for k,v in new.items() if k != 'allocated_developed_mm'}, 'edge topology changed')
        if i in incident:
            expected = interface.trace_length(graph['nodes'][new['from']]['pad_xyz_mm'],
                                              graph['nodes'][new['to']]['pad_xyz_mm'])
            need(new['allocated_developed_mm'] == expected, 'stale incident length')
            edge_changes.append({'edge_index': i, 'from':new['from'], 'to':new['to'], 'net':new['net'],
                'before_allocated_mm':old['allocated_developed_mm'],
                'after_allocated_mm':new['allocated_developed_mm'],
                'delta_allocated_mm':new['allocated_developed_mm']-old['allocated_developed_mm'],
                'routed_mm':None})
        else:
            need(old == new, 'unaffected edge changed')
    mapping = budget.mapping(graph, paths, inv)
    alternative = electrical.feed_alternative(copy.deepcopy(old_electrical), support, graph, paths)
    old_straps = {r['to']:r for r in old_electrical['lowR_complete_endpoint_paths']}
    strap_deltas = []
    for row in alternative['lowR_complete_endpoint_paths']:
        previous = old_straps[row['to']]
        need(row['new_segments'] == previous['new_segments'] and
             row['retained_suffix_edge_indices'] == previous['retained_suffix_edge_indices'], 'strap geometry changed')
        if row['complete_boundary_to_pad_allocation_mm'] != previous['complete_boundary_to_pad_allocation_mm']:
            strap_deltas.append({'to':row['to'],'net':row['net'],
                'before_allocated_mm':previous['complete_boundary_to_pad_allocation_mm'],
                'after_allocated_mm':row['complete_boundary_to_pad_allocation_mm'], 'routed_mm':None})
    groups = [ ('signal_net_paths','complete_net_pad_path_allocation_mm'),
               ('local_endpoint_paths','complete_net_pad_path_allocation_mm'),
               ('power_and_return_endpoint_paths','allocated_developed_mm') ]
    deltas = {name:delta_rows(old_paths[name],paths[name],lambda r:(r['net'],r['to']),metric)
              for name,metric in groups}
    need(len(mapping) == 106 and len(alternative['lowR_complete_endpoint_paths']) == 26 and
         len(alternative['lowR_unmodified_front_endpoint_targets']) == 80, '106 endpoint coverage')
    # Domain wording/limits are carried byte-for-byte at the individual endpoint.
    prior_mapping = {r['to']:r for r in read('stage12/budget-report.json')['resistance_endpoint_mapping']}
    for row in mapping:
        for field in ('original_plane_requirement','expanded_architecture_comparison','upstream_source_feed'):
            need(row[field] == prior_mapping[row['to']][field], 'resistance requirement changed')
    summary = {'changed_pad_nodes':sorted(changed_nodes), 'incident_edge_deltas':edge_changes,
               'path_deltas':deltas, 'unselected_strap_path_deltas':strap_deltas,
               'counts':{'nodes':len(graph['nodes']), 'edges':len(graph['edges']),
                         'crossing_signal_paths':len(paths['signal_net_paths']),
                         'local_endpoint_paths':len(paths['local_endpoint_paths']),
                         'power_return_endpoints':len(mapping), 'strap_core_endpoints':26,'retained_front_endpoints':80},
               'historical_crossing_max_mm':max(r['complete_net_pad_path_allocation_mm'] for r in old_paths['signal_net_paths']),
               'overlay_crossing_max_mm':max(r['complete_net_pad_path_allocation_mm'] for r in paths['signal_net_paths']),
               'resistance_endpoint_mapping':mapping,
               'unselected_strap_endpoint_paths':alternative['lowR_complete_endpoint_paths'],
               'unselected_strap_unchanged_front_targets':alternative['lowR_unmodified_front_endpoint_targets'],
               'resistance_accounting':read('stage12/budget-report.json')['resistance_accounting'],
               'capacitance_scope':'Physical harness wire lengths unchanged; wire-only sensitivity unchanged. New package/PCB/loop parasitics and complete effective capacitance UNKNOWN.',
               'load_scope':'Recomputed geometry is not resistance or current. Actual copper widths, paths, necks, vias, upstream source and shared return currents remain UNKNOWN; no equal sharing.',
               'calibration':'Stage13 result frozen; no new knob fitting or error acceptance.'}
    for result in (graph,paths,summary):
        result.update(status='STAGE14 GEOMETRY-BOUND ALLOCATION; NOT ELECTRICAL ACCEPTANCE',
                      hardware_acceptance=False, native='NOT RUN', simulation='NOT RUN', physical='NOT RUN',
                      actual_copper_routing='NOT RUN')
    return graph,paths,summary


def build():
    names = ['stage13/package-report.json','stage10/interfaces-report.json','stage10/electrical-report.json',
             'stage10/mechanical-report.json','stage10/inventory-report.json','stage10/interface-input.json',
             'stage11/support-report.json','stage11/electrical-report.json']
    reports = [read(name) for name in names]
    for report in reports:
        if 'source_sha256' in report: common.bindings(report)
    results = analyze(*reports)
    sources = [OUT.parent/name for name in names] + [OUT.parent/'stage12/budget-report.json',
               Path(__file__),Path(__file__).with_name('test_stage14_paths.py'),
               Path(interface.__file__),Path(electrical.__file__),Path(budget.__file__)]
    for result in results:
        result['source_sha256'] = {str(p.relative_to(ROOT)):common.digest(p) for p in sources}
    return results


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name,result in zip(('interfaces','paths','rebudget'),build()):
        text=json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n';target=OUT/(name+'-report.json')
        if args.check: need(target.read_text()==text,'stale Stage14 '+name)
        else: target.write_text(text)
    print('PASS Stage14 four pads/five edges and all106 endpoint allocations; electrical acceptance OPEN')

if __name__=='__main__':main()
