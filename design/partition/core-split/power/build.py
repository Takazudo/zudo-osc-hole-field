#!/usr/bin/env python3
"""Rebuild #247 source-only comparison contracts; never writes production files."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification
from scripts.schgen.core import designator

RAILS = ('+12V', '-12V', '+5V')
ALIASES = {'NOISE_VDD': '+5V', 'VEE5': '-12V'}
POSE_KEYS = ('id', 'pcb_reference', 'board', 'center_mm', 'footprint_origin_mm',
             'rotation_deg', 'kicad_orientation_deg', 'side', 'pin_map')
BASE_INPUTS = (
    'design/reports/io-partition.json', 'design/partition/partition.json',
    'design/partition/partition-input.json', 'design/partition/floorplan-candidate.json',
    'design/partition/connector-packing-candidate.json', 'design/partition/loom-candidate.json',
    'design/power/rail-ledger.json', 'design/power/rail-allocation-input.json',
    'design/power/supply-architecture-input.json', 'design/power/supply-architecture.json',
    'design/grid/placements.lock.json', 'design/partition/ground-material-evidence.json',
    'design/connectors/jst-gh.json', 'design/connectors/sources/jst-gh.pdf',
    'design/partition/sources/alpha-5859.pdf', 'design/partition/sources/alpha-6821.pdf',
    'scripts/checks/partition35.py', 'scripts/partition/model.py',
    'scripts/schgen/build_rail_ledger.py', 'scripts/schgen/analyze_rail_options.py',
    'scripts/schgen/build_supply_architecture.py', 'scripts/pcbgen/power_load_ledger.py',
    'design/partition/core-model-scope.md',
    'design/boards/osc-core.json',
)


def read(path):
    return json.loads((ROOT / path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(',', ':'), allow_nan=False)


def rounded(values):
    return {k: round(v, 6) for k, v in values.items()}


def cap_rail(net):
    return ALIASES.get(net.rsplit('/', 1)[-1] if net else net, net)


def csv_text(rows, fields):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fields, lineterminator='\n')
    writer.writeheader()
    for row in rows:
        writer.writerow({k: canonical(row[k]) if isinstance(row[k], (dict, list)) else row[k]
                         for k in fields})
    return out.getvalue()


def source_hashes():
    paths = {ROOT / p for p in BASE_INPUTS}
    for pattern in ('design/spec/**/*.py', 'design/spec/**/*.json', 'design/reports/current/*.json',
                    'design/standard/**/*.json', 'scripts/schgen/core.py',
                    'symbols/**/*.kicad_sym', 'footprints/kicad/zudo-osc-hole-field.pretty/*.kicad_mod'):
        paths.update(ROOT.glob(pattern))
    for owner in ('component-ti-opa4196idr', 'component-ti-opa4197ipwr',
                  'component-jst-gh', 'component-passives-family'):
        paths.update((ROOT / '.claude/skills' / owner).rglob('*.json'))
    paths.add(ROOT / '.claude/skills/component-spec-audit/references/inventory.json')
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in sorted(paths)}


def changed_at_ref(expected, reference):
    require(len(reference) == 40 and all(c in '0123456789abcdef' for c in reference),
            'comparison requires full immutable SHA')
    return [p for p,h in expected.items() if digest(subprocess.check_output(
        ['git','show',f'{reference}:{p}'],cwd=ROOT)) != h]


def assemble(config=None):
    config = config or read(str(HERE.relative_to(ROOT) / 'input.json'))
    partition = read('design/partition/partition.json')
    circuit = read('design/reports/io-partition.json')
    ledger = read('design/power/rail-ledger.json')
    supply = read('design/power/supply-architecture.json')
    source = read('design/partition/partition-input.json')
    parts = {p['ref']: p for p in circuit['physical_packages']}
    assignment = {p['ref']: p['board'] for p in partition['assignment']['components']}
    require(len(parts) == len(circuit['physical_packages']) == len(assignment), 'duplicate or missing physical package')
    require(config['power_parts_owner'] == config['existing_main_lands_owner'] == 'KA', 'unreviewed hub relocation')
    require(config['new_feed']['net_order'] == source['load_distribution']['net_order'], 'new feed pin order changed')
    require(config['bulk']['nominal_uF_per_board_rail'] == 4.7 and config['bulk']['reserve_mm'] == [5,3,5], 'unreviewed bulk requirement')
    require(config['new_feed']['terminal_reserve_mm'] == [6,6] and
            config['new_feed']['terminal_copper_mm'] == [4,4] and
            config['new_feed']['terminal_courtyard_mm'] == [5,5] and
            config['new_feed']['terminal_row_pitch_mm'] == 17 and
            config['new_feed']['wire_service_corridor_depth_mm'] == 28 and
            config['new_feed']['wire_service_corridor_height_mm'] == 28 and
            config['new_feed']['satellite_monitor_reserve_mm'] == [20,20,5],
            'unreviewed mechanical envelope change')
    families, instances = specification()
    families = {f.name: f for f in families}
    values, abstract = {}, []
    for inst in instances:
        for part in families[inst.family].parts:
            ref = designator(part, inst)
            if part.abstract:
                abstract.append({'ref': ref, 'pins': part.pins, 'footprint': part.footprint,
                                 'in_bom': part.in_bom, 'owner': 'unimplemented external source/protection boundary'})
            else:
                values[ref] = part.value
    require({p['ref'] for p in abstract} == {'CN301', 'XB301'}, 'abstract boundary inventory changed')
    require(all(not p['footprint'] and not p['in_bom'] for p in abstract), 'abstract boundary acquired physical implementation')
    pins = defaultdict(dict)
    for unit in circuit['package_units']:
        for pin, net in unit['pins'].items():
            require(pin not in pins[unit['ref']] or pins[unit['ref']][pin] == net, 'conflicting package pin')
            pins[unit['ref']][pin] = net
    owners = {}
    core_instances = {p['instance'] for ref, p in parts.items() if assignment[ref] == 'K' and p['instance'] != 'POWER'}
    for option, groups in config['options'].items():
        flattened = [inst for group in groups.values() for inst in group]
        require(len(flattened) == len(set(flattened)) and set(flattened) == core_instances, 'missing/duplicate core module')
        mapping = {inst: board for board, group in groups.items() for inst in group}
        require(all(mapping[x] == 'KA' for x in ('O1','O2','O3','O4','O5','OCTAVE_REF')), 'split oscillator/Kelvin reference group')
        owners[option] = {ref: assignment[ref] if assignment[ref] != 'K' else
                          'KA' if p['instance'] == 'POWER' else mapping[p['instance']]
                          for ref, p in parts.items()}
        for ref, p in parts.items():
            if p['decouples_ref']:
                require(owners[option][ref] == owners[option][p['decouples_ref']], 'split bypass '+ref)
        for group in circuit['local_raw_sensitive_nets']:
            require(len({owners[option][ref] for ref in group['refs']}) == 1, 'split sensitive net '+group['net'])
        for group in circuit['islands']:
            require(len({owners[option][ref] for ref in group['refs']}) == 1, 'split island '+group['island_id'])
    package_rows = []
    for ref, p in sorted(parts.items()):
        package_rows.append({'ref': ref, 'instance': p['instance'], 'mpn': p['mpn'],
            'source_board': assignment[ref], 'two_owner': owners['two'][ref],
            'three_owner': owners['three'][ref], 'dnp': p['dnp'], 'decouples_ref': p['decouples_ref'] or '',
            'value': values[ref], 'pins': pins[ref],
            'courtyard_mm': [p['courtyard']['width_mm'],p['courtyard']['height_mm']],
            'courtyard_mm2': p['courtyard']['area_mm2']})
    cap_values = {'100 nF': .1, '1e-07 F': .1, '1 uF': 1, '4.7 µF': 4.7,
                  '4.7 µF bulk reservation': 4.7}
    caps = []
    for ref, p in sorted(parts.items()):
        if not ref.startswith('C'):
            continue
        rails = sorted({cap_rail(n) for n in pins[ref].values()} & set(RAILS))
        if not rails:
            continue
        require(values[ref] in cap_values, 'unparsed supply capacitance '+ref+' '+values[ref])
        caps.append({'ref': ref, 'instance': p['instance'], 'dnp': p['dnp'],
                     'nominal_uF': cap_values[values[ref]], 'rails': rails, 'pins': pins[ref],
                     'two_owner': owners['two'][ref], 'three_owner': owners['three'][ref],
                     'decouples_ref': p['decouples_ref']})
    total_caps = rounded({r: sum(c['nominal_uF'] for c in caps if not c['dnp'] and r in c['rails']) for r in RAILS})
    require(total_caps == {r: supply['implementation']['actual_fitted_capacitor_inventory'][r]['captured_fitted_nominal_uF'] for r in RAILS}, 'fitted capacitance drift')
    headers = {h['id']: h for h in partition['connectors']}
    crossings = {n['net']: n for n in circuit['allowed_crossings']}
    harnesses, count = [], Counter()
    for h in partition['harnesses']:
        if 'K' not in h['boards']:
            continue
        endpoints = [headers[x] for x in h['header_ids']]
        require(endpoints[0]['pin_map'] == endpoints[1]['pin_map'], 'endpoint pin order mismatch '+h['id'])
        nets = list(endpoints[0]['pin_map'].values())
        count.update(n if n in (*RAILS, 'AGND', 'NC') else 'signal' for n in nets)
        assignment_by_option = {}
        for option in owners:
            core_dest = set()
            for net in nets:
                if net in (*RAILS, 'AGND', 'NC'):
                    continue
                core_dest.update(owners[option][m['ref']] for m in crossings[net]['members'] if assignment.get(m['ref']) == 'K')
            require(len(core_dest) == 1, 'mixed/unknown harness destination '+h['id'])
            assignment_by_option[option] = next(iter(core_dest))
        harnesses.append({'id': h['id'], 'source_boards': h['boards'], 'core_owner': assignment_by_option,
            'endpoints': [{k: e[k] for k in POSE_KEYS} | {
                          'header_mpn': e['header_mpn'], 'housing_mpn': e['housing_mpn'],
                          'contact_mpn': e['contact_mpn'], 'pose_policy': 'frozen' if e['board'] != 'K' else 'old pose retained as evidence; candidate pose owned by #245/#246'} for e in endpoints]})
    require(len(harnesses) == 191 and count == Counter({'signal':505,'AGND':376,'+12V':6,'-12V':6,'+5V':6,'NC':4}), 'K harness conservation failed')
    power = [p for p in package_rows if p['instance'] == 'POWER']
    require(len(power) == 13, 'POWER physical roster changed')
    require(not any(n and n.endswith('_IN') for p in power for n in p['pins'].values()), 'physical POWER part crossed raw/load boundary')
    main_lands = [t | {'candidate_owner': 'KA' if t['board'] == 'K' else t['board']} for t in partition['load_side_terminals']]
    require(sum(t['board'] == 'K' for t in main_lands) == 18, 'main land inventory changed')
    summaries = {}
    sr = supply['selected_requirement']
    req = supply['contract']['source_requirement']
    distribution = source['load_distribution']
    for option, groups in config['options'].items():
        module_owner = {inst: b for b, group in groups.items() for inst in group}
        budget = {b: {r:0.0 for r in RAILS} for b in [*groups, 'NONCORE_ONLY']}
        worksheet_rows = []
        for row in ledger['worksheet_loads']:
            b = module_owner.get(row['instance'], 'NONCORE_ONLY')
            for r in RAILS:
                budget[b][r] += row['planning_allowance_mA'][r]
            worksheet_rows.append({'id':row['id'], 'responsibility':b,
                'source':row['source'], 'source_row':row['source_row'], 'planning_mA':row['planning_allowance_mA']})
        global_allowances = {r:0.0 for r in RAILS}
        for r, rows in sr['allowances'].items():
            for row in rows:
                inst = row['id'].split(':')[0]
                inst = 'N1' if inst == 'NOISE2-extra-sensitivity' else inst
                if inst in module_owner:
                    budget[module_owner[inst]][r] += row['mA']
                else:
                    global_allowances[r] += row['mA']
        require(all(abs(sum(b[r] for b in budget.values())+global_allowances[r]-sr['normal_with_allowances_mA'][r]) < 1e-5 for r in RAILS), 'load conservation failed')
        require(sum(config['auxiliary_reserve_mA_per_rail'][option].values()) == 20, 'duplicated or missing global auxiliary allowance')
        boards = {}
        for board in groups:
            selected = [p for p in package_rows if p[option+'_owner'] == board]
            ics = [p | {'feed_owner': board} for p in ledger['physical_ic_packages'] if owners[option][p['ref']] == board]
            board_caps = [c for c in caps if c[option+'_owner'] == board]
            opamp_iq = sum({'OPA4196IDR':1.0,'OPA4197IPWR':6.0}.get(p['symbol'],0) for p in ics)
            boards[board] = {'instances':groups[board], 'package_count':len(selected),
                'dnp_refs':[p['ref'] for p in selected if p['dnp']],
                'fitted_ic_count':len(ics), 'fitted_ic_supply_pins':ics,
                'ic_count_by_exact_symbol':dict(sorted(Counter(p['symbol'] for p in ics).items())),
                'opamp_quiescent_subset_mA_per_analog_rail':opamp_iq,
                'opamp_subset_scope':'Only OPA4196IDR/OPA4197IPWR, four channels, IO=0, full-temperature Iq; not total core current, not additive to worksheet. fact-op-audio-quiescent-current / fact-op-precision-quiescent-current, retained TI PDF index7/printed8.',
                'existing_harness_count':sum(h['core_owner'][option] == board for h in harnesses),
                'module_responsibility_planning_mA':rounded(budget[board]),
                'physical_feed_current_maximum_mA':{r:None for r in RAILS},
                'new_protection_auxiliary_share_mA_per_rail':config['auxiliary_reserve_mA_per_rail'][option][board],
                'fitted_rail_capacitance_uF':rounded({r:sum(c['nominal_uF'] for c in board_caps if not c['dnp'] and r in c['rails']) for r in RAILS}),
                'source_capacitors':board_caps,
                'fitted_return_contact_count':sum(n == 'AGND' for p in selected if not p['dnp'] for n in p['pins'].values()),
                'fitted_supply_pin_count':dict(Counter(cap_rail(n) for p in ics for n in p['supply_pins'].values() if cap_rail(n) in RAILS)),
                'bypass_owner_pairs':[[p['ref'],p['decouples_ref']] for p in selected if p['decouples_ref']],
                'return_path':'IC/passive local return and bypass -> continuous local AGND -> dedicated main wire -> KA hub; GH/sleeve paths remain coupled parallel returns',
                'dynamic_path':'Switching/LED/output current and capacitor charge need signed waveform allocation; no part-count apportionment',
                'native_connectivity':'NOT RUN'}
        extra = len(groups)-1
        feeds = []
        for board in groups:
            if board == 'KA':
                continue
            fid = f'CS247-KA-{board}'
            feeds.append({'id':fid, 'boards':['KA',board], 'domain':'EXT',
                'wires':[{'id':f'{fid}-W{i}', 'net':net,
                    'terminal_ids':[f'{fid}-SRC-{i}',f'{fid}-DST-{i}'],
                    'wire_mpn':distribution['wire'], 'maximum_cut_length_mm':distribution['max_wire_length_mm'],
                    'current_screen_A':distribution['rail_max_A'].get(net,distribution['single_return_max_A'])}
                    for i,net in enumerate(config['new_feed']['net_order'],1)],
                'terminal_identity':'custom 4x4 mm PCB solder land, 5x5 courtyard in 6x6 reserve; no orderable part',
                'endpoint_envelopes':[{'id':fid+'-'+end, 'board':b, 'side':'F.Cu',
                    'terminal_centres_local_mm':[[3+i*config['new_feed']['terminal_row_pitch_mm'],3] for i in range(6)],
                    'land_row_reserve_mm':[91,6], 'corridor_local_box_mm':[0,6,0,91,34,28],
                    'global_origin_mm':None, 'installed_fit':'NOT RUN'} for end,b in [('SRC','KA'),('DST',board)]],
                'strain_relief_gap':config['new_feed']['strain_relief_candidate_gap'],
                'supply_path':'load side of unimplemented XB301 only; no physical raw/load bridge; never route through a different satellite core'})
        bulk_reservations = [{'id':f'CS247-BULK-{b}-{i}', 'board':b, 'net':r,
            'nominal_uF':4.7, 'envelope_mm':config['bulk']['reserve_mm'], 'side':'B.Cu',
            'manufacturer':None,'mpn':None,'global_origin_mm':None,
            'status':'UNSELECTED; place near feed; local envelope only'} for b in groups for i,r in enumerate(RAILS,1)]
        powered = [*groups,'JL','JR','P','EL']
        full_caps = {r:total_caps[r]+len(powered)*4.7 for r in RAILS}
        ramp = {r:full_caps[r]*1.2*v/10 for r,v in zip(RAILS,(13.2,13.2,5.5))}
        remaining_caps = {r:req['nominal_capacitance_ceiling_uF'][r]-full_caps[r] for r in RAILS}
        require(min(remaining_caps.values()) >= 0, 'capacitance ceiling exceeded')
        require(all(sr['minimum_continuous_mA'][r]+ramp[r] <= sr['minimum_transient_mA'][r] for r in RAILS), 'conditional ramp exceeds transient contract')
        summaries[option] = {'status':config['status'], 'boards':boards,
            'worksheet_accounting_scope':'Whole-module responsibility across K/JL/JR/P/EL; NOT physical core current, not added to separately counted package Iq',
            'worksheet_rows':worksheet_rows,'noncore_only_modules':['B1','B2','X1','X2'],
            'noncore_only_planning_mA':rounded(budget['NONCORE_ONLY']),
            'global_allowances_charged_once_mA':rounded(global_allowances),
            'total_planning_mA':sr['normal_with_allowances_mA'],
            'continuous_requirement_reserve_mA':rounded({r:sr['minimum_continuous_mA'][r]-sr['normal_with_allowances_mA'][r] for r in RAILS}),
            'new_feeds':feeds,'bulk_reservations':bulk_reservations,
            'preserved_protection_reserve':{'board':'KA',**source['boards']['K']['reserves'][0]},
            'satellite_monitor_reservations':[{'id':'CS247-MON-'+b,'board':b,'side':'B.Cu','envelope_mm':[20,20,5],'global_origin_mm':None,'mpn':None,'status':'PROPOSAL capacity only; exact #59 circuit and fit unknown'} for b in groups if b != 'KA'],
            'mechanical_budget':{'new_main_wire_count':6*extra,'new_main_lands':12*extra,
                'new_total_wire_cut_max_mm':660*extra,'new_land_cell_area_mm2':432*extra,
                'new_land_row_area_mm2':1092*extra,'new_service_corridor_projection_mm2':5096*extra,
                'new_bulk_parts_over_one_core':3*extra,'new_bulk_face_area_mm2_over_one_core':45*extra,
                'new_satellite_monitor_face_area_mm2':400*extra,
                'note':'Cells are inside row envelopes; do not add them twice. Corridors are separate swept-space reservations, not populated PCB area. Global fit/strain relief unresolved.'},
            'capacitance':{'powered_boards':powered,'fitted_nominal_uF':total_caps,
                'including_all_reserved_bulk_uF':rounded(full_caps),'remaining_nominal_uF':rounded(remaining_caps),
                'plus20percent_10ms_ramp_mA':rounded(ramp),
                'continuous_plus_ramp_mA':rounded({r:sr['minimum_continuous_mA'][r]+ramp[r] for r in RAILS}),
                'effective_C_ESR_and_hot_behaviour':'UNSOURCED / NEEDS BENCH; nominal values are not guaranteed effective values'}}
    wire_r = distribution['hot_resistance_requirement_ohm_per_m']*distribution['max_wire_length_mm']/1000 + distribution['combined_termination_resistance_ohm']
    drops = {r:1000*(a*(wire_r+distribution['rail_plane_resistance_ceiling_ohm'])+distribution['single_return_max_A']*(wire_r+distribution['return_plane_resistance_ceiling_ohm'])) for r,a in distribution['rail_max_A'].items()}
    material = read('design/partition/ground-material-evidence.json')['retained_reference_values']
    rho = material['annealed_copper_volume_resistivity_20C_ohm_mm']*(1+material['volume_temperature_coefficient_per_C']*(70-20))
    sheet_r = rho / .07
    report = {'schema_version':1,'source_main_sha':config['source_main_sha'],
        'package_ownership_policy':'Every CSV row has a physical board owner in each option; all fitted loads use EXT load-side or existing derived rails, local AGND/paired-rail returns and dedicated main feeds. DNP rows retain geometry but zero fitted injection. No independent source or signal normal is added.',
        'status':'SOURCE CONTRACT READY FOR REVIEW; architecture NOT SELECTED; native/physical acceptance NOT RUN',
        'layer_contract':read('design/boards/osc-core.json')['stackup'],
        'return_and_fault_contract':{
            'source_return_topology':supply['contract']['returns'],
            'existing_EL_bounds':{k:v for k,v in partition['power'].items() if k.startswith('EL_')},
            'unimplemented_protection_obligations':source['protection_obligations'],
            'partial_power':'Any missing/late rail or unplugged satellite can be backfed by signal/reference pins; common EXT is not sequencing protection. Require load-side detection, bounded injection, all-rail shutdown/discharge and reverse blocking (#59).',
            'return_open':'GH returns and patch sleeves can become unintended supply returns after a main return opens. No live internal service, ground switching or equal-sharing assumption. Return integrity and fault energy remain OPEN.',
            'reference':'O1-O5/OCTAVE_REF stay KA; existing adjacent Kelvin AGND and <=300mm/<=1nF reference harness conditions remain. Local sense does not cancel remote drop.',
            'coupling':'All cores, front boards, dedicated feeds and GH returns form one coupled network; old K nominal/return proofs are epoch-specific and cannot qualify this comparison.'},
        'options':summaries, 'external_boundary':{'abstract_parts':abstract,'contract_sha256':digest((ROOT/'design/power/supply-architecture-input.json').read_bytes()),
            'raw_nets':['+12V_IN','-12V_IN','+5V_IN'],'load_nets':list(RAILS),'domain':'EXT',
            'maximum_delivered_mA':partition['power']['maximum_delivered_mA'],
            'measured_source_capacity_mA':{r:None for r in RAILS},'no_physical_bridge':True},
        'power_parts':power,'existing_main_lands':main_lands,'existing_main_wires':partition['load_side_wires'],
        'conductor_screen':{'scope':'Conditional normal whole-source concentration on one edge; excludes local stored-energy discharge, circulating currents and fault survival.',
            'source':'design/partition/partition-input.json:load_distribution','wire_plus_terminations_ohm':wire_r,
            'single_return_A':4.6,'one_edge_rail_plus_return_drop_mV':rounded(drops),
            'remaining_20mV_margin_mV':rounded({r:20-d for r,d in drops.items()}),
            'rejected_two_full_serial_allowances_mV':rounded({r:2*d for r,d in drops.items()}),
            'one_return_wire_and_ends_dissipation_mW':round(4.6**2*wire_r*1000,6),
            'nominal_copper_rho70_ohm_mm':rho,'nominal_70um_sheet_resistance_ohm_per_square':sheet_r,
            'rail_1mohm_total_squares':.001/sheet_r,'return_0p5mohm_total_squares':.0005/sheet_r,
            'copper_scope':'Ideal uniform rectangular-strip comparison R=rho*L/(w*t); no actual plane, neck, via, contact or common-transfer extraction; no parallel-layer credit.',
            'global_budget':'Shared KA hub, branch, satellite, every access/neck/via consume ONE total 1mohm rail / 0.5mohm common AGND and 20mV path allowance; never restart budgets at each board.',
            'native_or_hot_result':None},
        'deterministic_rejections':[
            {'id':'serial-budget-duplication','verdict':'BLOCKER - deterministic spec violation','condition':'Two full existing distribution allowances placed in series','result_mV':rounded({r:2*d for r,d in drops.items()}),'limit_mV':20},
            {'id':'protection-reserve-overrun','verdict':'BLOCKER - deterministic spec violation','condition':'If inherited local-quad protection sensitivity is adopted unchanged','demand_plus12_mA':45.5,'global_auxiliary_allocation_mA':20,'excess_mA':25.5,'adopted':False}],
        'readiness':{'architecture_input':'READY FOR REVIEW with explicit unresolved gates','production_adoption':'NOT READY','native':'NOT RUN','physical':'NOT RUN',
            'blockers':['#245/#246 place both-ended feeds, bulk, protection and service envelopes; confirm <=110mm wire routes and bends',
                        '#253 selects architecture; #254 implements exact registry/source interfaces',
                        '#59 exact protection/partial power/return integrity and auxiliary demand; no raw/load bridge',
                        '#57/#65 actual source, hot contacts/wires/copper, stored-energy/current class and mechanical qualification',
                        'Recompute complete split-network GH return bounds and Kelvin transfer; old all-mates bounds are ineligible',
                        'No manufacturer identity/effective-C evidence for added bulk or local monitor circuit']}}
    preservation = {'schema_version':1,'source_main_sha':config['source_main_sha'],
        'k_harness_count':len(harnesses),'positions_per_endpoint':dict(count),'harnesses':harnesses,
        'noncore_pose_policy':'Freeze both endpoint Refs and complete pins; all noncore poses remain byte-value identical',
        'noncore_endpoint_pose_sha256':digest(canonical([{k:e[k] for k in POSE_KEYS} for h in harnesses for e in h['endpoints'] if e['board'] != 'K']).encode()),
        'new_feed_namespace':config['new_feed']['namespace']}
    return report, preservation, package_rows


def outputs():
    report, harnesses, packages = assemble()
    hashes = source_hashes()
    require(not changed_at_ref(hashes, report['source_main_sha']),
            'consumed sources differ from declared immutable input; review a new baseline before rebuilding')
    result = {'contract.json':json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)+'\n',
              'harness-contract.json':json.dumps(harnesses, indent=2, ensure_ascii=False, allow_nan=False)+'\n',
              'package-ownership.csv':csv_text(packages,list(packages[0]))}
    manifest = {'source_main_sha':report['source_main_sha'],'source_sha256':hashes,
                'lane_code_sha256':{p.name:digest(p.read_bytes()) for p in (HERE/'build.py',HERE/'input.json')},
                'output_sha256':{k:digest(v.encode()) for k,v in result.items()},
                'canonical_board_sha256':{str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in sorted((ROOT/'boards').rglob('*.kicad_pcb'))},
                'native_evidence':'NOT RUN; these are published byte hashes, not refilled native hashes'}
    result['manifest.json'] = json.dumps(manifest,indent=2)+'\n'
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--compare-ref', help='Read-only compare source inputs against an immutable integration commit')
    args = parser.parse_args()
    if args.compare_ref:
        manifest = read(str(HERE.relative_to(ROOT)/'manifest.json'))
        expected = manifest['source_sha256'] | manifest['canonical_board_sha256']
        changed = changed_at_ref(expected,args.compare_ref)
        print(json.dumps({'comparison_sha':args.compare_ref,'changed_inputs':changed,'status':'RECHECK REQUIRED' if changed else 'INPUT BYTES MATCH; coordinator admission still required'},indent=2))
        return 1 if changed else 0
    for name, body in outputs().items():
        target = HERE/name
        if args.check:
            require(target.exists() and target.read_text() == body, 'generated contract drift: '+name)
        else:
            target.write_text(body)
    print('PASS: source ownership, 191 harnesses/903 positions, load/capacitance conservation and deterministic contracts; native/physical NOT RUN')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
