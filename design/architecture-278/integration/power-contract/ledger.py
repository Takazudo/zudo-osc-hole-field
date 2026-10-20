"""Combined OSC demand / zudo-pd supply ledger.

Reads committed OSC power reports, the unadopted Stage54 accounting and the
provisional PD supply context; writes ledger.json. Unknowns stay null, no
efficiency or rating is invented, and conditional savings stay in their own row.
"""
from pathlib import Path
import hashlib, json, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAILS = ('+12V', '-12V', '+5V')
INPUTS = {
    'rail_budget': 'design/power/rail-budget.json',
    'supply_architecture': 'design/power/supply-architecture.json',
    'supply_architecture_input': 'design/power/supply-architecture-input.json',
    'stage54_accounting': 'design/architecture-278/implementation/stage54/power-cleanup/accounting.json',
    'pd_supply_input': 'design/architecture-278/integration/power-contract/supply-input.json',
}


def require(ok, msg):
    if not ok:
        raise SystemExit('FAIL ' + msg)


def read(rel):
    return json.loads((ROOT / rel).read_text())


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def r6(x):
    return round(x, 6)


def watts(currents_mA, volts):
    return r6(sum(currents_mA[r] / 1000 * volts[r] for r in RAILS))


def build():
    budget = read(INPUTS['rail_budget'])
    arch = read(INPUTS['supply_architecture'])
    arch_in = read(INPUTS['supply_architecture_input'])
    s54 = read(INPUTS['stage54_accounting'])
    pd = read(INPUTS['pd_supply_input'])
    sel = arch['selected_requirement']
    src = arch_in['source_requirement']
    env = arch_in['load_envelope']

    # Cross-check the brief's figures against current evidence before use.
    require(sel['minimum_continuous_mA'] == {'+12V': 1700, '-12V': 1600, '+5V': 300}, 'continuous requirement')
    require(sel['minimum_transient_mA'] == {'+12V': 2000, '-12V': 1900, '+5V': 400}, 'transient requirement')
    require(s54['EXT_normal_with_allowances_after_Iq_mA'] == {'+12V': 1492.819166, '-12V': 1393.56866, '+5V': 224.286445}, 'Stage54 conditional planning')
    require(s54['removed_Iq_mA'] == {'planning_Iq': {'+12V': 42.0, '-12V': 42.0, '+5V': 0.0}, 'typical': {'+12V': 27.36, '-12V': 27.36, '+5V': 0.0}}, 'Stage54 Iq')
    require(s54['EXT_normal_with_allowances_before_mA'] == sel['normal_with_allowances_mA'], 'Stage54 baseline equals canonical requirement')
    require(all(v is None for v in budget['guaranteed_maximum_mA'].values()), 'guaranteed maxima must stay unknown')
    for r in RAILS:
        require(abs(sum(i['planning_upper_subtotal_mA'][r] for i in budget['instances']) + budget['synth_inlet']['worst_voltage_and_resistance_bleeder_current_mA'][r] - budget['reported_planning_upper_subtotal_mA'][r]) < 1e-5, 'planning subtotal ' + r)

    # Demand grouped by module family, from the committed per-instance worksheet.
    families = {}
    for inst in budget['instances']:
        f = families.setdefault(inst['family'], {'instances': [], 'partial': False,
                                                  'reported_typical_mA': {r: 0 for r in RAILS},
                                                  'planning_upper_mA': {r: 0 for r in RAILS}})
        f['instances'].append(inst['instance'])
        f['partial'] = f['partial'] or inst['partial']
        for r in RAILS:
            f['reported_typical_mA'][r] += inst['reported_typical_subtotal_mA'][r]
            f['planning_upper_mA'][r] += inst['planning_upper_subtotal_mA'][r]
    for f in families.values():
        for k in ('reported_typical_mA', 'planning_upper_mA'):
            f[k] = {r: r6(v) for r, v in f[k].items()}

    normal = sel['normal_with_allowances_mA']
    states = {
        'reported_typical_subtotal': {
            'classification': 'REPORTED/ASSUMED TYPICAL, PARTIAL (complete typical unknown)',
            'mA': budget['reported_assumed_typical_subtotal_mA'],
            'basis': 'design/power/rail-budget.json; excludes items listed in incomplete_sources'},
        'normal_planning': {
            'classification': 'PLANNING ALLOCATION (canonical, not a maximum or measurement)',
            'mA': normal,
            'basis': 'supply-architecture.json selected_requirement.normal_with_allowances_mA'},
        'normal_planning_stage54_conditional': {
            'classification': 'UNADOPTED CONDITIONAL (Stage54 idle-quad removal, max-Iq allowance)',
            'mA': s54['EXT_normal_with_allowances_after_Iq_mA'],
            'basis': 'Stage54 accounting.json; not booked against any requirement'},
        'startup_envelope_10ms': {
            'classification': 'CONSERVATIVE ENVELOPE (normal planning plus full-capacitance ramp; not a simultaneous operating point)',
            'mA': {r: r6(normal[r] + sel['full_capacitance_ramp_increment_mA'][r]) for r in RAILS},
            'basis': 'ramp increment at %s ms soft start and capacitance ceiling +20 %%; load current during the ramp is lower than at full voltage' % src['soft_start_min_ms']},
        'normal_plus_one_fault': {
            'classification': 'PLANNING ALLOCATION plus one bounded external-forcing fault',
            'mA': {r: r6(normal[r] + env['fault_increment_mA'][r]) for r in RAILS},
            'basis': env['fault_basis']},
        'continuous_requirement': {
            'classification': 'CONTRACT REQUIREMENT (minimum source delivery)',
            'mA': sel['minimum_continuous_mA'],
            'basis': 'normal planning x (1 + %s reserve), rounded up to %s mA' % (env['reserve_fraction'], env['current_rounding_mA'])},
        'transient_requirement_20ms': {
            'classification': 'CONTRACT REQUIREMENT (minimum source delivery for %s ms)' % src['transient_requirement_duration_ms'],
            'mA': sel['minimum_transient_mA'],
            'basis': 'supply-architecture.json selected_requirement.minimum_transient_mA'},
        'interface_maximum': {
            'classification': 'CONTRACT INTERFACE LIMIT (source current limit must stay at or below)',
            'mA': src['maximum_delivered_current_mA'],
            'basis': src['current_limit_contract']},
    }
    # Reserve check reproduces the continuous requirement rule without changing it.
    for r in RAILS:
        step = env['current_rounding_mA']
        req = -(-normal[r] * (1 + env['reserve_fraction']) // step) * step
        require(req == sel['minimum_continuous_mA'][r], 'continuous rule ' + r)
        cond = -(-s54['EXT_normal_with_allowances_after_Iq_mA'][r] * (1 + env['reserve_fraction']) // step) * step
        states['normal_planning_stage54_conditional'].setdefault('continuous_rule_result_mA', {})[r] = int(cond)

    v_lo = {r: src['voltage_magnitude_at_source_V'][r][0] for r in RAILS}
    v_hi = {r: src['voltage_magnitude_at_source_V'][r][1] for r in RAILS}
    chain = pd['chain']
    pre_nom = {r: chain[r]['pre_rail_nominal_V'] for r in RAILS}
    # Valid only while each pre-regulator regulates: an LDO draws at least its
    # output current from a pre-rail no lower than the PD-screened minimum.
    pre_min = {r: chain[r]['pre_rail_min_V'] for r in RAILS}
    for r in RAILS:
        require(pre_min[r] > v_hi[r], 'pre-rail floor above output ' + r)
    budgets = pd['input_boundary_W']

    power = {}
    for name, st in states.items():
        if name == 'interface_maximum':
            continue  # an upper limit, not a demand
        mA = st['mA']
        out_lo, out_hi = watts(mA, v_lo), watts(mA, v_hi)
        pre_l = watts(mA, pre_min)
        power[name] = {
            'osc_inlet_W_at_source_band': [out_lo, out_hi],
            'current_pd_chain_pre_rail_W_lower_bound': {'nominal_setpoints': watts(mA, pre_nom), 'screened_minimum_setpoints': pre_l},
            'efficiency_needed': {k: {'any_architecture_end_to_end': r6(out_lo / w), 'current_pd_chain_converters': r6(pre_l / w)}
                                  for k, w in budgets.items() if k != 'note' and k != 'classification'},
        }
        # PD's own U4 conduction-only model is an optimistic ceiling (losses omitted).
        u4 = max(pd['pd_screen_at_design_targets']['u4_modeled_conduction_efficiency'])
        neg_in = mA['-12V'] / 1000 * pre_min['-12V'] / u4
        pos = r6(mA['+12V'] / 1000 * pre_min['+12V'] + mA['+5V'] / 1000 * pre_min['+5V'])
        power[name]['positive_converter_efficiency_needed_with_pd_u4_model'] = {
            k: (r6(pos / (w - neg_in)) if w > neg_in else None)
            for k, w in budgets.items() if k not in ('note', 'classification')}
        power[name]['infeasible_at_100_percent'] = {
            k: {'any_architecture': out_lo > w, 'current_pd_chain': pre_l > w}
            for k, w in budgets.items() if k not in ('note', 'classification')}

    targets = pd['output_design_target_mA']
    per_rail = {name: {r: {'demand_mA': st['mA'][r], 'pd_design_target_mA': targets[r],
                           'excess_over_target_mA': r6(st['mA'][r] - targets[r])} for r in RAILS}
                for name, st in states.items() if name != 'interface_maximum'}

    ratings = {}
    for r in RAILS:
        ptc = chain[r]['ptc']
        cont, trans, imax = (states[k]['mA'][r] / 1000 for k in ('continuous_requirement', 'transient_requirement_20ms', 'interface_maximum'))
        ratings[r] = {
            'ptc': ptc['ref'] + ' ' + ptc['mpn'],
            'continuous_requirement_A': cont,
            'ptc_ihold_25C_A': ptc['ihold_A_25C'],
            'ptc_ihold_85C_A': ptc['ihold_A_85C'],
            'continuous_exceeds_ptc_hold_25C': cont > ptc['ihold_A_25C'],
            'ptc_itrip_25C_A': ptc['itrip_A_25C'],
            'ptc_enforces_interface_maximum': ptc['itrip_A_25C'] <= imax,
            'ptc_drop_at_continuous_V_r1max': None if ptc['r1max_ohm'] is None else r6(cont * ptc['r1max_ohm']),
            'ldo_table_rows_end_A': chain[r]['ldo_table_rows_end_A'],
            'continuous_beyond_ldo_table_rows': cont > chain[r]['ldo_table_rows_end_A'],
            'transient_beyond_ldo_table_rows': trans > chain[r]['ldo_table_rows_end_A'],
            'sources': [ptc['source'], chain[r]['ldo_source']]}

    bands = {}
    for r in RAILS:
        pd_iv = chain[r]['output_conditional_V']
        osc = src['voltage_magnitude_at_source_V'][r]
        load = src['required_load_voltage_magnitude_V'][r]
        bands[r] = {'osc_source_band_V': osc, 'osc_required_load_band_V': load,
                    'pd_conditional_output_V': pd_iv,
                    'within_osc_source_band': 'not demonstrated' if not (osc[0] <= pd_iv[0] and pd_iv[1] <= osc[1]) else 'screen inside band',
                    'screen_outside_osc_load_band_before_ptc_and_cable_drop': pd_iv[0] < load[0] or pd_iv[1] > load[1],
                    'source': chain[r]['output_source']}

    return {
        'schema_version': 1,
        'status': 'UNVALIDATED DRAFT combined power-contract ledger; arithmetic only; no measured, guaranteed or simulated capacity',
        'classification_legend': {
            'GUARANTEED': 'manufacturer limit under its stated conditions; none booked for whole-instrument demand',
            'TYPICAL': 'reported/assumed typical; partial',
            'PLANNING': 'project allocation, not a maximum',
            'CONTRACT': 'requirement the source must meet',
            'CONDITIONAL': 'unadopted proposal; never booked against a requirement',
            'SIMULATION': 'none in this ledger',
            'MEASURED': 'none; every measured field is null'},
        'inputs_sha256': {k: {'path': p, 'sha256': sha(p)} for k, p in INPUTS.items()},
        'pd_commit': pd['commit'],
        'demand_by_family': families,
        'inlet_allowances_mA': sel['allowances'],
        'states': states,
        'power': power,
        'per_rail_vs_pd_design_target': per_rail,
        'voltage_bands': bands,
        'ratings_screen': ratings,
        'pd_screen_at_design_targets': pd['pd_screen_at_design_targets'],
        'pd_open_qualification_quoted': pd['open_qualification_quoted'],
        'supply_capability_mA': pd['capability_mA'],
        'converter_efficiency_booked': None,
        'guaranteed_whole_instrument_maximum_mA': {r: None for r in RAILS},
        'measured_whole_instrument_mA': {r: None for r in RAILS},
        'measured_source_capacity_mA': {r: None for r in RAILS},
        'unknown_reasons_preserved': s54['unknown_reasons_preserved'],
        'source_not_proven_preserved': arch['not_proven'],
        'unresolved_ota_mirror_allocation': {
            'status': 'OPEN; no rebate booked',
            'branches': len(s54['OTA_bias_overlap_branches']),
            'coarse_reserve_mA_per_analog_rail': s54['coarse_reserve_mA_per_analog_rail']},
    }


if __name__ == '__main__':
    data = build()
    out = HERE / 'ledger.json'
    text = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
    if '--check' in sys.argv:
        require(out.read_text() == text, 'ledger.json drift')
    else:
        out.write_text(text)
    p = data['power']
    print('PASS ledger; continuous OSC inlet %.2f-%.2f W; current PD chain pre-rail lower bound %.2f W'
          % (*p['continuous_requirement']['osc_inlet_W_at_source_band'],
             p['continuous_requirement']['current_pd_chain_pre_rail_W_lower_bound']['screened_minimum_setpoints']))
