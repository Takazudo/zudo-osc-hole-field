#!/usr/bin/env python3
"""Bounded arithmetic only. No CAD, solver, native campaign or energized test."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / 'design/architecture-278'
LIMITS = {'branch_K_ground_mohm': .5, 'rail_transfer_mohm': 1, 'hot_distribution_mV': 20, 'full_path_V': .20, 'GH_contact_A': .5}
RAILS = ['+12V', '-12V', '+5V']

def nonnegative_number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('Expected finite nonnegative number')
    return value

def evaluate(data):
    if data['limits'] != LIMITS:
        raise ValueError('Existing limits must not be reset')
    ref = data['reference']
    for key in ['branches', 'aggregate_limit_pF', 'remote_length_mm', 'remote_limit_mm', 'adjacent_step_target_uV']:
        nonnegative_number(ref[key])
    if ref['remote_limit_mm'] != 300 or ref['adjacent_step_target_uV'] != 2000:
        raise ValueError('Inherited remote envelope/adjacent step target changed')
    if ref['branches'] != 5 or ref['aggregate_limit_pF'] != 1000:
        raise ValueError('Five-receiver aggregate octave constraint changed')
    numbers = [*ref['branch'].values(), ref['shared_trace_pF'], ref['shared_test_pF'], *ref['error_terms_uV'].values()]
    for number in numbers:
        nonnegative_number(number)
    if ref['actual_capacitance_pF'] is not None:
        nonnegative_number(ref['actual_capacitance_pF'])
    if ref['actual_errors_uV'] is not None:
        for number in ref['actual_errors_uV'].values():
            nonnegative_number(number)
    cap = ref['shared_trace_pF'] + ref['shared_test_pF'] + ref['branches'] * sum(ref['branch'].values())
    if cap > 1000 or ref['remote_length_mm'] > 300:
        raise ValueError('Remote/reference envelope exceeded')
    if sum(ref['error_terms_uV'].values()) * 2 > ref['adjacent_step_target_uV']:
        raise ValueError('Adjacent receiver error allocation exceeds target')
    if ref['actual_capacitance_pF'] is not None and not 0 <= ref['actual_capacitance_pF'] <= 1000:
        raise ValueError('Actual reference capacitance exceeds envelope')
    segments = data['resistance_segments']
    if len({x['id'] for x in segments}) != len(segments):
        raise ValueError('Duplicate path segment')
    expected = {'source-output', 'source-middle-hot', 'middle-zone-hot', 'middle-interface-hot', 'interface-load-hot', 'load-interface-return', 'interface-middle-return', 'middle-zone-return', 'middle-source-return'}
    if {x['id'] for x in segments} != expected:
        raise ValueError('Missing or unexpected whole-path segment')
    for segment in segments:
        expected_group = 'source' if segment['id'] == 'source-output' else 'rail' if segment['id'].endswith('-hot') else 'ground'
        if segment['group'] != expected_group:
            raise ValueError('Path segment group cannot be reassigned')
        for field in ['allocation_mohm', 'actual_mohm']:
            if segment[field] is not None:
                nonnegative_number(segment[field])
        if expected_group != 'source' and segment['allocation_mohm'] is None:
            raise ValueError('Required segment allocation missing')
    for group, limit in [('rail', 1), ('ground', .5)]:
        if sum(x['actual_mohm'] or 0 for x in segments if x['group'] == group) > limit:
            raise ValueError('Known partial resistance already violates unchanged limit')
    totals = {g: sum(x['allocation_mohm'] or 0 for x in segments if x['group'] == g) for g in ['rail', 'ground']}
    if totals['rail'] > 1 or totals['ground'] > .5:
        raise ValueError('Combined path allocation exceeds inherited limit')
    if any(x['actual_mohm'] is not None and x['actual_mohm'] < 0 for x in segments):
        raise ValueError('Negative physical resistance')
    return {'allocated_rail_mohm': totals['rail'], 'allocated_return_mohm': totals['ground'], 'aggregate_octave_pF': cap, 'octave_remaining_pF': 1000-cap, 'reference_error_allocation_uV': sum(ref['error_terms_uV'].values()), 'physical_acceptance': 'OPEN: actual paths, source impedance, load maxima and reference errors unqualified'}

def build(root=ROOT):
    paths = ['design/architecture-278/electrical-input.json', 'design/architecture-278/source-ledger.json', 'design/architecture-278/interface-contract.json', 'design/power/rail-ledger.json', 'design/power/rail-budget.json', 'design/reports/current/oscillator.json', 'design/reports/oscillator-reference-fanout.json', 'design/partition/rail-access-current-mechanisms.md', 'design/connectors/jst-gh.json']
    read = lambda p: json.loads((root/p).read_text())
    data, ledger, contract, power, budget, osc, fanout = [read(p) for p in paths[:7]]
    result = evaluate(data)
    physical = {(p['instance'], p['ref']): p for p in power['physical_ic_packages']}
    owners = {p['ref']: p['owner'] for p in contract['packages']}
    worksheet = power['worksheet_loads']
    devices = []
    for p in ledger['packages']:
        ic = physical.get((p['instance'], p['ref']))
        matches = [w for w in worksheet if w['instance'] == p['instance'] and w['label'] == p.get('symbol', p['mpn'])]
        status = 'DNP' if p['dnp'] else 'partial' if matches else 'unmapped'
        if ic and not ic['rails']:
            status = 'unserved'
        devices.append({'ref':p['ref'], 'instance':p['instance'], 'mpn':p['mpn'], 'units':p['units'], 'current_board':p['current_board'], 'candidate_owner':owners.get(p['ref'], 'other-function boundary; unchanged'), 'rails':ic['rails'] if ic else [], 'supply_pins':ic['supply_pins'] if ic else {}, 'classification':status, 'worksheet_ids':[w['id'] for w in matches], 'decouples_ref':p['decouples_ref'], 'state_bounds_mA':{s:None for s in data['states']}, 'reason':'DNP excludes fitted load only' if p['dnp'] else 'Worksheet package allowance only; dynamics/fault/temperature maxima OPEN' if matches else 'No exact per-device worksheet allocation; passive/signal-dependent/leakage demand not assumed zero'})
    rows = []
    for w in worksheet:
        rows.append({**w, 'classification':'partial', 'allocation_status':'existing worksheet once only; do not sum again with per-device coverage', 'candidate_board_allocation':'OPEN where lumped load spans front/rear'})
    cases=[]
    for n in (1,2,5):
        currents={r:round(n*osc['sheets'][0]['planning_upper_mA_per_instance'][r]+osc['sheets'][1]['planning_upper_mA_per_instance'][r],6) for r in RAILS}
        cases.append({'oscillators':n, 'shared_reference_count':1, 'planning_mA':currents, 'rail_drop_at_allocated_1mohm_mV':{r:round(i*.001,6) for r,i in currents.items()}, 'return_upper_sum_mA':round(sum(currents.values()),6), 'return_drop_at_allocated_half_mohm_mV':round(sum(currents.values())*.0005,6), 'GH_worst_one_contact_A':{r:i/1000 for r,i in currents.items()}, 'physical_acceptance':'NOT ESTABLISHED: planning currents not complete maxima; actual resistance/contact multiplicity OPEN'})
    return {'schema_version':1,'status':'UNVALIDATED DESIGN ALLOCATION; no qualification', 'source_sha256':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in paths}, 'allocation':result, 'device_coverage':devices, 'classification_counts':dict(Counter(p['classification'] for p in devices)), 'worksheet_loads':rows, 'load_cases':cases, 'whole_instrument_instances':budget['instances'], 'source_capacity_limits':budget['rails'], 'preserved_reference_conditioned_outputs':fanout['local_outputs_per_oscillator'], 'limits':data['limits'], 'resistance_segments':data['resistance_segments'], 'topology_comparison':data['topology_comparison'], 'fault_owners':data['fault_owners'], 'not_run':['native/numerical campaign prohibited','energized fault and physical verification not authorized']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    output=json.dumps(build(),indent=2,sort_keys=True)+'\n';path=DIR/'electrical-report.json'
    if args.check:
        if not path.exists() or path.read_text()!=output: raise SystemExit('electrical report drift')
        print('PASS: deterministic electrical report; physical electrical acceptance OPEN')
    else:path.write_text(output)
if __name__=='__main__':main()
