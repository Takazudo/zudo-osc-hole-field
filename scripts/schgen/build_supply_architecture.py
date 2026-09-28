#!/usr/bin/env python3
"""Check the #48 conditional source requirement; never claim installed capacity."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.schgen.build_rail_ledger import build as ledger_build, no_duplicate_keys, RAIL_ALIASES
from design.spec.instrument import specification
from design.spec.modules.power import family as power_family
from scripts.checks.protection58 import build as protection_audit_build
RAILS = ('+12V', '-12V', '+5V')
INPUT = ROOT / 'design/power/supply-architecture-input.json'
OUTPUT = ROOT / 'design/power/supply-architecture.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads((ROOT / path).read_text(), object_pairs_hook=no_duplicate_keys)


def overlaps(a, b):
    return all(max(a[i], b[i]) < min(a[i+3], b[i+3]) for i in range(3))


def build(config=None):
    c = read(INPUT) if config is None else config
    def finite_values(value, path='contract'):
        if isinstance(value, dict):
            for key, child in value.items(): finite_values(child, path+'.'+key)
        elif isinstance(value, list):
            for child in value: finite_values(child, path)
        elif isinstance(value, (int, float)):
            require(math.isfinite(value), 'nonfinite value: '+path)
    finite_values(c)
    ledger = ledger_build()
    loads = ledger['worksheet_loads']
    expected = set(ledger['module_feed_assignment'])
    require(c['decision'] == 'EXTERNAL_REGULATED_SOURCE_REQUIREMENT', 'unsupported decision')
    require(set(c['domains']) == {'EXT'}, 'selected topology requires exactly one EXT domain')
    domain = c['domains']['EXT']
    require(len(domain['module_instances']) == len(set(domain['module_instances'])) and set(domain['module_instances']) == expected, 'missing/duplicate/extra module allocation')
    require(domain['regulated_nets'] == {r:r for r in RAILS} and domain['return_net'] == 'AGND', 'unexpected rail merging or return disconnection')
    require(domain['source_id'] == 'external-unselected', 'regulated source changed; no paralleling permitted')
    require(set(c['load_allocation']) == {r['id'] for r in loads}, 'missing/extra worksheet load')
    for load in loads:
        require(c['load_allocation'][load['id']] == {'domain':'EXT', 'rails':load['active_rails']}, 'wrong load domain/rail: '+load['id'])
    require(c['physical_source']['status'] == 'NOT SELECTED' and c['physical_source']['mpn'] is None and set(c['physical_source']['measured_capacity_mA']) == set(RAILS) and all(v is None for v in c['physical_source']['measured_capacity_mA'].values()), 'invented source capacity/identity')
    placements = read('design/grid/placements.lock.json')['placements']
    # Use the same stable UID/XY digest convention as the selector checker.
    fixed_digest = hashlib.sha256(json.dumps(sorted((p['uid'], p['x_mm'], p['y_mm']) for p in placements), separators=(',', ':')).encode()).hexdigest()
    require(len(placements) == c['fixed_feature_count'] == 438 and fixed_digest == c['fixed_uid_xy_sha256'], 'fixed panel geometry changed')
    require(len(expected - {'OCTAVE_REF'}) == c['fixed_module_count'] == 33, 'module scope changed')
    candidate = c['independent_candidate']
    require(candidate['source_count'] == 3 and set(candidate['domains']) == set('ABC'), 'three independent candidate sources required')
    assigned = [m for group in candidate['domains'].values() for m in group]
    require(len(assigned) == len(set(assigned)) and set(assigned) == expected, 'candidate missing/duplicate module')
    require({'OCTAVE_REF', 'O1','O2','O3','O4','O5'} <= set(candidate['domains']['A']), 'shared octave reference crosses candidate domains')
    require(candidate['planning_ceiling_mA'] == ledger['original_single_source_ceiling_mA'], 'pinned planning ceilings changed')
    bleeders = read('design/power/rail-budget-input.json')['synth_inlet']['worst_voltage_and_resistance_bleeder_current_mA']
    total = {r:sum(x['planning_allowance_mA'][r] for x in loads) for r in RAILS}
    env = c['load_envelope']; req = c['source_requirement']; inlet = c['inlet']; harness = inlet['harness']
    require(env['reserve_fraction'] >= .1 and env['current_rounding_mA'] == 100, 'reserve/rounding weakened')
    require(req['nominal_capacitance_ceiling_uF'] == {'+12V':150,'-12V':150,'+5V':100} and req['capacitance_tolerance_fraction'] == .2, 'OSC-ES-1 capacitance changed')
    require(req['soft_start_min_ms'] >= 10 and req['transient_requirement_duration_ms'] >= req['soft_start_min_ms'], 'startup duration incomplete')
    allowances = {r:[] for r in RAILS}
    for rail in RAILS:
        require(env['auxiliary_allowance_mA'][rail] >= 20 and env['leakage_allowance_mA'][rail] >= 1, 'required auxiliary/leakage allowance missing')
        allowances[rail] += [{'id':'one-inlet-bleeder','mA':bleeders[rail]}, {'id':'one-inlet-leakage','mA':env['leakage_allowance_mA'][rail]}, {'id':'protection-supervision-discharge','mA':env['auxiliary_allowance_mA'][rail]}]
    for key, value in ledger['draft_allowances'].items():
        if not key.startswith('inlet:'):
            allowances[value['rail']].append({'id':key, 'mA':value['planning_mA'] * value['sensitivity_multiplier']})
    allowances['+5V'].append({'id':'NOISE2-extra-sensitivity','mA':10})
    normal = {r:total[r] + sum(v['mA'] for v in allowances[r]) for r in RAILS}
    continuous = {r:math.ceil(normal[r]*(1+env['reserve_fraction']) / 100)*100 for r in RAILS}
    charge = {r:req['nominal_capacitance_ceiling_uF'][r]*(1+req['capacitance_tolerance_fraction'])*req['required_load_voltage_magnitude_V'][r][1] / req['soft_start_min_ms'] for r in RAILS}
    transient = {r:math.ceil((continuous[r]+charge[r]+env['fault_increment_mA'][r])/100)*100 for r in RAILS}
    require(env['fault_increment_mA']['+12V'] >= 24/998*1000 and env['fault_increment_mA']['-12V'] >= 24/998*1000, 'conditional output fault allowance missing')
    maximum = req['maximum_delivered_current_mA']
    require(all(maximum[r] >= transient[r] for r in RAILS), 'limiter cannot deliver required transient')
    return_A = sum(maximum.values())/1000
    rating = inlet['min_required_simultaneous_contact_rating_A']
    require(rating >= return_A and harness['ampacity_min_A_per_conductor'] >= return_A and inlet['max_each_return_conductor_current_A'] >= return_A, 'return contact/cable overload (no equal sharing assumption)')
    require(inlet['pin_map'] == {'1':'+12V_IN','2':'-12V_IN','3':'+5V_IN','4':'NC','5':'AGND','6':'AGND','7':'AGND','8':'AGND'}, 'wrong inlet pin map')
    require(inlet['min_required_contact_voltage_V'] >= 30 and 'NOT SELECTED' in inlet['status'], 'unproven inlet selection/rating')
    require(all(harness[k] >= 0 for k in ('max_length_mm','max_wire_ohm_per_m_at_hot_condition','max_contact_and_crimp_path_ohm','max_protection_drop_V','max_distribution_drop_V')), 'negative cable/protection allowance')
    conductor_R = harness['max_length_mm']/1000*harness['max_wire_ohm_per_m_at_hot_condition']+harness['max_contact_and_crimp_path_ohm']
    losses = {}
    for r in RAILS:
        amps = maximum[r]/1000
        require(amps <= min(rating, harness['ampacity_min_A_per_conductor'], inlet['max_each_rail_conductor_current_A']), 'rail conductor/contact overload')
        loss = (amps+return_A)*conductor_R+harness['max_protection_drop_V']+harness['max_distribution_drop_V']
        losses[r] = round(loss,6)
        require(loss <= req['max_total_rail_and_return_loss_V'], 'harness/protection/distribution voltage loss exceeded')
        source_low, source_high = req['voltage_magnitude_at_source_V'][r]
        load_low, load_high = req['required_load_voltage_magnitude_V'][r]
        require(0 < source_low <= source_high and 0 < load_low <= load_high, 'invalid voltage interval')
        require(source_low-req['max_total_rail_and_return_loss_V'] >= load_low and source_high+return_A*conductor_R <= load_high, 'source/load voltage band incompatible')
    require(len(c['fault_cases']) >= 5 and {x['case'] for x in c['fault_cases']} >= {'EXT off, external patch on','Any one rail absent or late','Reference receiver board unplugged','Return open, shifted/reversed plug or external fault','Three-source candidate one domain off'}, 'domain-off/fault analysis missing')
    candidate_rows = {}
    for g, modules in candidate['domains'].items():
        values = {r:sum(x['planning_allowance_mA'][r] for x in loads if x['instance'] in modules)+bleeders[r]+env['leakage_allowance_mA'][r]+env['auxiliary_allowance_mA'][r] for r in RAILS}
        for key, value in ledger['draft_allowances'].items():
            if key.split(':')[0] in modules:
                values[value['rail']] += value['planning_mA']*value['sensitivity_multiplier']
        if 'N1' in modules:values['+5V']+=10
        # Add full allocated board capacitance rather than the old inlet-only 1 ms calculation.
        startup = {r:values[r]+candidate['capacitor_share_uF'][g][r]*1.2*req['required_load_voltage_magnitude_V'][r][1]/10+env['fault_increment_mA'][r] for r in RAILS}
        require(all(startup[r] <= candidate['planning_ceiling_mA'][r] for r in RAILS), 'candidate per-domain current envelope fails')
        candidate_rows[g] = {'normal_with_allowances_mA':{r:round(values[r],6) for r in RAILS}, 'conditional_10ms_start_and_one_fault_mA':{r:round(startup[r],6) for r in RAILS}, 'margin_to_pinned_ceiling_mA':{r:round(candidate['planning_ceiling_mA'][r]-startup[r],6) for r in RAILS}}
    for r in RAILS:
        require(math.isclose(sum(v[r] for v in candidate['capacitor_share_uF'].values()), req['nominal_capacitance_ceiling_uF'][r]), 'candidate capacitance share missing')
    width,height,depth = candidate['enclosure_inside_xyz_mm']; reservations=[]
    require(len(candidate['pockets']) == 3, 'missing independent source pocket')
    for pocket in candidate['pockets']:
        body, support, cable = (pocket[k] for k in ('body_xyz_mm','support_xyz_mm','cable_exit_xyz_mm'))
        require([body[i+3]-body[i] for i in range(3)] == [116,91,25], 'pinned assembly envelope changed')
        require(all(support[i] <= body[i] and body[i+3] <= support[i+3] for i in range(3)), 'source outside separate support')
        for box in (support,cable):
            require(all(box[i] < box[i+3] for i in range(3)) and 0 <= box[0] < box[3] <= width and 0 <= box[1] < box[4] <= height and -depth <= box[2] < box[5] <= -45, 'source/support/cable outside rear chamber')
            require(not any(overlaps(box, other) for other in reservations), 'source/support/cable collision')
            reservations.append(box)
    require(all(x['pcb_z_mm']-4-.5 > -45 for x in read('design/mechanical/selector-assembly.json')['instances']), 'selector reservation overlaps rear chamber')
    minimum = max(math.ceil(total[r]/candidate['planning_ceiling_mA'][r]) for r in RAILS)
    require(minimum == 3, 'minimum independent arithmetic candidate changed')
    # Inspect the captured sheet instead of treating the contract as installed hardware.
    power_parts = {part.key: part for part in power_family().parts}
    legacy = read('design/power/protection-source-lock.json')['historical_ptc_limits']
    actual_inlet = power_parts['INLET']
    boundary = power_parts['BOUNDARY']
    require(actual_inlet.symbol.endswith(':OSC_EXT_INLET_R1') and boundary.symbol.endswith(':OSC_EXT_BOUNDARY_R1'), 'selected abstract power sheet missing')
    require(actual_inlet.pins == {'1':'+12V_IN','2':'-12V_IN','3':'+5V_IN','4':None,'5':'AGND','6':'AGND','7':'AGND','8':'AGND'}, 'logical inlet pin map drift')
    require(boundary.pins == {'1':'+12V_IN','2':'-12V_IN','3':'+5V_IN','4':'+12V','5':'-12V','6':'+5V','7':'AGND'}, 'raw/load boundary net drift')
    require(all(part.abstract and not part.footprint and not part.in_bom and part.on_board and
                part.attributes.get('Implementation') == 'REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE'
                for part in (actual_inlet, boundary)), 'abstract netlist-only boundary became orderable or disappeared from native netlist')
    require(not any(part.key.startswith(('PTC_', 'TVS_', 'FLAG_')) for part in power_parts.values()), 'legacy protection or ERC power flag reused')
    historical_path = {}
    for key, rail in (('P12','+12V'), ('N12','-12V'), ('P5','+5V')):
        historical_path[rail] = {
                'historical_part': legacy['part'],
                'hold_A_at_25C': legacy['hold_A_at_25C'],
                'required_continuous_A': continuous[rail]/1000,
                'r1max_ohm': legacy['r1max_ohm'],
                'drop_at_required_continuous_V_using_r1max': round(continuous[rail]/1000*legacy['r1max_ohm'],6),
                'passes_required_current_and_protection_loss':
                    legacy['hold_A_at_25C'] >= continuous[rail]/1000 and
                    continuous[rail]/1000*legacy['r1max_ohm'] <= harness['max_protection_drop_V'],
            }
    # These are fitted capacitor values visible in the master specification;
    # board-level 4.7 uF reservoirs remain an explicit, unplaced reservation.
    cap_values_uF = {'100 nF':.1, '1e-07 F':.1, '1 uF':1, '4.7 µF':4.7}
    families, instances = specification()
    by_family = {f.name:f for f in families}
    jack_sleeves = [(instance.name,part.key) for instance in instances
                    for part in by_family[instance.family].parts if part.prefix=='J' and part.pins.get('S')=='AGND']
    require(len(jack_sleeves)==180, 'patch sleeve AGND coverage changed')
    fitted_caps = {rail:[] for rail in RAILS}
    for instance in instances:
        for part in by_family[instance.family].parts:
            if part.prefix != 'C' or part.dnp:
                continue
            # Charge filtered NOISE_VDD and locally buffered VEE5 capacitance
            # to their upstream +5 and -12 planning domains conservatively.
            cap_rails = [rail for rail in RAILS if any(RAIL_ALIASES.get(net,net)==rail
                         for net in part.pins.values() if net is not None)]
            for rail in cap_rails:
                require(part.value in cap_values_uF, 'unparsed rail capacitor value: '+part.value)
                fitted_caps[rail].append({'instance':instance.name,'key':part.key,'value':part.value,'nominal_uF':cap_values_uF[part.value]})
    cap_inventory = {}
    supply_pin_counts = {rail:0 for rail in RAILS}
    for package in ledger['physical_ic_packages']:
        for net in package['supply_pins'].values():
            rail = RAIL_ALIASES.get(net,net)
            if rail in supply_pin_counts:
                supply_pin_counts[rail] += 1
    for rail in RAILS:
        nominal = round(sum(row['nominal_uF'] for row in fitted_caps[rail]),6)
        remaining = round(req['nominal_capacitance_ceiling_uF'][rail]-nominal,6)
        require(remaining >= 0, 'fitted rail capacitance exceeds ceiling')
        hundred_nf = sum(row['value'] in ('100 nF','1e-07 F') for row in fitted_caps[rail])
        require(hundred_nf >= supply_pin_counts[rail], '100 nF rail capacitor count below actual IC supply pin count: '+rail)
        cap_inventory[rail] = {'captured_fitted_count':len(fitted_caps[rail]),'captured_fitted_nominal_uF':nominal,
            'mapped_ic_supply_pin_count':supply_pin_counts[rail],
            'fitted_100nF_attributed_to_rail_count':hundred_nf,
            'per_pin_proximity_and_effective_C_status':'OPEN: count coverage only; package proximity, local VEE5 and effective ceramic capacitance require board audit',
            'remaining_nominal_uF_before_unplaced_board_bulk':remaining,
            'initial_bulk_uF_per_powered_board':4.7,
            'maximum_additional_full_board_allocations_at_4p7uF':math.floor((remaining+1e-9)/4.7),
            'board_bulk_status':'OPEN: board count and per-board/rail reservoir placement not established; no zero-capacitance assumption',
            'full_ceiling_with_plus20percent_uF':round(req['nominal_capacitance_ceiling_uF'][rail]*1.2,6)}
    protection = protection_audit_build()
    require(protection['output_count'] == 82 and protection['precision_count'] == 16 and len(protection['reference_receivers']) == 30, 'unresolved injection inventory changed')
    implementation = {
        'status': 'PASS: requirement-only specification separation; native netlist audited separately; OPEN: protection circuit #59; NOT RUN: physical #57',
        'captured_inlet_symbol': actual_inlet.symbol,
        'captured_inlet_footprint': actual_inlet.footprint,
        'captured_boundary_symbol': boundary.symbol,
        'captured_boundary_footprint': boundary.footprint,
        'abstract_parts_have_no_footprint_or_bom': True,
        'native_netlist_inclusion_note':'KiCad instance on_board=yes retains abstract pin nodes in native netlist; blank footprint and in_bom=no mean no orderable PCB placement or BOM line.',
        'raw_inlet_nets': ['+12V_IN','-12V_IN','+5V_IN'],
        'conditional_load_nets': list(RAILS),
        'agnd_common': True,
        'patch_sleeves_on_agnd':len(jack_sleeves),
        'selected_inlet_status': inlet['status'],
        'historical_ptc_comparison': historical_path,
        'actual_fitted_capacitor_inventory':cap_inventory,
        'open_injection_obligations':{'outputs':82,'precision_feedback':16,'octave_receivers':30,
            'status':'OPEN: no output/sense/reference isolation circuit selected'},
        'unbooked_local_quad_sensitivity_mA':protection['normal_positive_Iq_mA_sensitivity_local'],
        'auxiliary_allocation_plus12_mA':env['auxiliary_allowance_mA']['+12V'],
        'prospective_plus12_mA_excess_over_auxiliary_allocation':round(max(0,protection['normal_positive_Iq_mA_sensitivity_local']-env['auxiliary_allowance_mA']['+12V']),6),
        'missing_circuit_proofs': [
            'Load-side three-rail monitors and fail-safe inhibited enables',
            'Low-drop reverse-current blocking and coordinated shutdown/discharge on all rails',
            'Any-order/missing-rail and powered-off patch output/sense/reference injection bounds',
            'Open inlet AGND detection when a patch sleeve still provides a return path',
            'Per-board bulk, selected protection auxiliary-current and capacitance demand, source/inlet limiter let-through and fault energy',
            'Exact selected inlet drawing, rating, mating-face map and footprint',
        ],
    }
    return {'schema_version':1,'status':'PASS: conditional requirement arithmetic/allocation ONLY; hardware NOT SELECTED; unvalidated draft',
        'value_classification':'Computed report values DERIVED from authored PROPOSAL inputs and source-backed ledger; no measured/guaranteed capacity.',
        'input':'design/power/supply-architecture-input.json','contract':c,
        'implementation': implementation,
        'allocation_counts':{'signal_modules':33,'shared_references':1,'worksheet_loads':len(loads),'physical_IC_packages':ledger['physical_package_count'],'fixed_panel_centres':438},
        'physical_IC_allocation':[{**p,'domain':'EXT','mapped_supply_nets':p['supply_pins']} for p in ledger['physical_ic_packages']],
        'original_single_source':{'planning_mA':ledger['original_single_inlet_planning_mA'],'ceilings_mA':ledger['original_single_source_ceiling_mA'],'excess_mA':ledger['original_single_source_excess_mA']},
        'rejected_two_source_excess_mA':ledger['two_feed_total_excess_over_two_source_ceilings_mA'],
        'minimum_arithmetic_independent_sources':minimum,'three_source_evaluation':candidate_rows,
        'selected_requirement':{'worksheet_mA':{r:round(total[r],6) for r in RAILS},'allowances':allowances,'normal_with_allowances_mA':{r:round(normal[r],6) for r in RAILS},'minimum_continuous_mA':continuous,'full_capacitance_ramp_increment_mA':{r:round(charge[r],6) for r in RAILS},'minimum_transient_mA':transient,'worst_single_return_contact_A':return_A,'worst_return_shift_V':round(return_A*conductor_R,6),'max_conductor_path_ohm':conductor_R,'worst_rail_plus_return_loss_V':losses,
            'source_maximum_plus_return_shift_V':{r:round(req['voltage_magnitude_at_source_V'][r][1]+return_A*conductor_R,6) for r in RAILS},
            'required_continuous_output_power_W':round(sum(continuous[r]/1000*req['voltage_magnitude_at_source_V'][r][1] for r in RAILS),6),
            'protection_dissipation_allocation_W_per_rail':{r:round(continuous[r]/1000*harness['max_protection_drop_V'],6) for r in RAILS},
            'worst_return_path_transient_dissipation_W':round(return_A**2*conductor_R,6)},
        'guaranteed_whole_instrument_maximum_mA':{r:None for r in RAILS},'measured_source_capacity_mA':{r:None for r in RAILS},
        'not_proven':['Exact orderable connector/mate drawing, simultaneous-contact derating and footprint are not selected or qualified.', 'The requirement-only boundary separates raw and load nets but contains no protection circuit; #59 owns exact electrical realization.', 'Source realization, rail sequencing/backfeed/thermal/ripple, all-output faults, full-temperature maxima and physical fit remain NOT RUN in #57.']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');args=p.parse_args()
    report=build();body=json.dumps(report,indent=2)+'\n'
    if args.check:require(OUTPUT.exists() and OUTPUT.read_text()==body,'supply-architecture.json drift')
    else:OUTPUT.write_text(body)
    print(report['status'])
    selected=report['selected_requirement']
    print('Required continuous mA:', selected['minimum_continuous_mA'])
    print('Required transient mA:', selected['minimum_transient_mA'])
    print('Worst single return A:', selected['worst_single_return_contact_A'])

if __name__ == '__main__':main()
