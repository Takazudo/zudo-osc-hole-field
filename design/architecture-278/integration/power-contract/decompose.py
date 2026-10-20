"""OSC power-budget decomposition (owner request, zudo-pd #218 comment 6284861864).

Splits the canonical planning budget into fixed, operation/patch-dependent,
reserve, allowance and margin parts, row by row from design/power/rail-ledger.json,
and derives demand levels from those parts. Arithmetic only: nothing here is
measured, and no level below the canonical one changes a requirement. A lower
level is at most a candidate re-basing for the owner (PWR-D5).
Writes decomposition.json; --check compares it with the committed file.
"""
from pathlib import Path
import hashlib, json, math, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RAILS = ('+12V', '-12V', '+5V')
INPUTS = {
    'rail_ledger': 'design/power/rail-ledger.json',
    'supply_architecture': 'design/power/supply-architecture.json',
    'supply_architecture_input': 'design/power/supply-architecture-input.json',
    'stage54_accounting': 'design/architecture-278/implementation/stage54/power-cleanup/accounting.json',
    'combined_ledger': 'design/architecture-278/integration/power-contract/ledger.json',
}

# Category of every worksheet row, by its label. An unknown label fails the build.
Q_IC = 'fixed_ic_quiescent'
Q_LOGIC = 'fixed_logic_quiescent_and_rate'
S_STATIC = 'fixed_static_resistive_reference'
R_RESERVE = 'coarse_reserve'
P_SIGNAL = 'patch_signal_dependent'
P_INTERNAL = 'internal_signal_path'
P_OPER = 'operation_state_dependent'
CATEGORY = {
    'OPA4197IPWR': Q_IC, 'OPA4196IDR': Q_IC, 'OPA4196IDR whole quad package': Q_IC,
    'ADG5412FBRUZ': Q_IC, 'LM13700M_NOPB': Q_IC, 'LM393BIDR': Q_IC, 'AS3340D core': Q_IC,
    'LF398M_NOPB': Q_IC, 'NOISE2 filtered digital supply': Q_IC,
    'SN74HC00DR': Q_LOGIC, 'SN74HC74DR': Q_LOGIC, 'SN74HC14DR': Q_LOGIC, 'CD74HC221M96': Q_LOGIC,
    'REF5050 local generator and rail ladder': S_STATIC, 'REF5050 allocation': S_STATIC,
    'Offset trim track': S_STATIC, 'Manual control tracks': S_STATIC, 'one manual offset pot': S_STATIC,
    'Offset/input low-side divider loads': S_STATIC, '10 MΩ selector-common bias load': S_STATIC,
    'Input-isolator enable feeds': S_STATIC, 'Input-isolator enable feed': S_STATIC,
    'Input isolation enables': S_STATIC, 'fault-switch enable feeds': S_STATIC,
    'ATTEN fault-switch enable feed': S_STATIC, 'two input-switch enable feeds': S_STATIC,
    'Internal resistive/reference/shaper load reserve': R_RESERVE,
    'Reference, rates, clamp and control reserve': R_RESERVE,
    'Reference/control/expo/feedback reserve': R_RESERVE,
    'reference, signal pots, summer feedback, servo and trims': R_RESERVE,
    'Shared reference and distribution reserve': R_RESERVE,
    '5 V conditioning reserve': R_RESERVE,
    'magnitude_leds': P_SIGNAL, 'Three magnitude LEDs': P_SIGNAL, 'three magnitude LEDs': P_SIGNAL,
    'magnitude indicators': P_SIGNAL, 'Four magnitude indicators': P_SIGNAL,
    'Magnitude indicator envelope': P_SIGNAL, 'one clip LED': P_SIGNAL, 'pre-level clip LED': P_SIGNAL,
    'output_loads': P_SIGNAL, 'Four 10 kohm jack loads': P_SIGNAL, 'Four external output loads': P_SIGNAL,
    'External output loads': P_SIGNAL, 'External output load': P_SIGNAL, 'one external output load': P_SIGNAL,
    'SUM external load': P_SIGNAL,
    # Internal clamp, feedback and summing networks: signal-dependent, but no
    # patching or brightness notice can bound them.
    'Four diode clamp feeds': P_INTERNAL, 'Four fold feedback paths': P_INTERNAL,
    'Command clamp resistor': P_INTERNAL, 'internal command and feedback load': P_INTERNAL,
    'Other local signal/control resistor paths': P_INTERNAL,
    'FOLD depth track/harness drive': P_OPER, 'LEVEL track/harness drive': P_OPER,
    'PNP bias/command branch': P_OPER, 'Two stage LEDs': P_OPER, 'Comparator pullups': P_OPER,
    'Five control-contact pulls': P_OPER,
}
# Jack loads and magnitude LEDs return to ground: at any instant each draws from
# one analog rail only, so the +12 V and -12 V envelopes cannot both peak. This
# lowers total power, never a single rail's current. Feedback, summing, clamp and
# differential drive paths and clip LEDs (+12 V to -12 V) load both rails at once.
ONE_RAIL_AT_A_TIME = {
    'magnitude_leds', 'Three magnitude LEDs', 'three magnitude LEDs', 'magnitude indicators',
    'Four magnitude indicators', 'Magnitude indicator envelope', 'output_loads', 'Four 10 kohm jack loads',
    'Four external output loads', 'External output loads', 'External output load', 'one external output load',
    'SUM external load',
}
NOMINAL_V = {'+12V': 12, '-12V': 12, '+5V': 5}
# Fitted downstream capacitance reported by the OSC owner from source at e1969027
# (answer to Q6, relayed by the coordinator; all MLCC, +5 V includes NOISE_VDD 4.7 uF).
FITTED_UF = {'+12V': 49.9, '-12V': 42.2, '+5V': 24.5}


def require(ok, msg):
    if not ok:
        raise SystemExit('FAIL ' + msg)


def read(rel):
    return json.loads((ROOT / rel).read_text())


def sha(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def r6(x):
    return round(x, 6)


def zero():
    return {r: 0.0 for r in RAILS}


def add(*terms):
    return {r: r6(sum(t[r] for t in terms)) for r in RAILS}


def sub(a, b):
    return {r: r6(a[r] - b[r]) for r in RAILS}


def watts(mA, volts):
    return r6(sum(mA[r] / 1000 * volts[r] for r in RAILS))


def continuous_rule(mA, reserve, step):
    return {r: int(math.ceil(round(mA[r] * (1 + reserve), 9) / step) * step) for r in RAILS}


def build():
    led = read(INPUTS['rail_ledger'])
    sel = read(INPUTS['supply_architecture'])['selected_requirement']
    arch_in = read(INPUTS['supply_architecture_input'])
    s54 = read(INPUTS['stage54_accounting'])
    pw = read(INPUTS['combined_ledger'])['power']
    env, src = arch_in['load_envelope'], arch_in['source_requirement']
    v_hi = {r: src['voltage_magnitude_at_source_V'][r][1] for r in RAILS}

    cats = {c: {'planning_mA': zero(), 'typical_mA': zero(), 'rows': 0, 'labels': set()}
            for c in (Q_IC, Q_LOGIC, S_STATIC, R_RESERVE, P_INTERNAL, P_SIGNAL, P_OPER)}
    one_rail_overlap = zero()   # min(+12, -12) per row, removable from power only
    per_rail_overcount = zero()  # charges the row's own basis says cannot occur
    overcount_rows = []
    for row in led['worksheet_loads']:
        label = row['label']
        require(label in CATEGORY, 'uncategorised worksheet label: ' + label)
        c = cats[CATEGORY[label]]
        plan, typ = row['planning_allowance_mA'], row['reported_assumed_typical_mA']
        c['rows'] += 1
        c['labels'].add(label)
        for r in RAILS:
            c['planning_mA'][r] += plan[r]
            c['typical_mA'][r] += typ[r]
        if label in ONE_RAIL_AT_A_TIME:
            m = min(plan['+12V'], plan['-12V'])
            one_rail_overlap['+12V'] += m
        basis = row.get('basis') or ''
        if label == 'Two stage LEDs' and 'one-hot' in basis:
            d = plan['+5V'] / 2
            per_rail_overcount['+5V'] += d
            overcount_rows.append({'id': row['id'], 'rail': '+5V', 'mA': r6(d), 'basis': basis})
    for c in cats.values():
        c['planning_mA'] = {r: r6(v) for r, v in c['planning_mA'].items()}
        c['typical_mA'] = {r: r6(v) for r, v in c['typical_mA'].items()}
        c['labels'] = sorted(c['labels'])
    one_rail_overlap = {r: r6(v) for r, v in one_rail_overlap.items()}
    per_rail_overcount = {r: r6(v) for r, v in per_rail_overcount.items()}

    worksheet_plan = add(*(c['planning_mA'] for c in cats.values()))
    for r in RAILS:
        require(abs(worksheet_plan[r] - sel['worksheet_mA'][r]) < 1e-5, 'categories reproduce worksheet ' + r)
    reserves = cats[R_RESERVE]['planning_mA']
    require(reserves['+12V'] == reserves['-12V'] == s54['coarse_reserve_mA_per_analog_rail'], 'coarse analog reserve')

    allow_plan = {r: r6(sum(a['mA'] for a in sel['allowances'][r])) for r in RAILS}
    canonical = add(worksheet_plan, allow_plan)
    for r in RAILS:
        require(abs(canonical[r] - sel['normal_with_allowances_mA'][r]) < 1e-5, 'canonical reproduced ' + r)
    # Typical allowances: bleeder, leakage and protection as planned; H1/H2 reference
    # and logic at their pre-sensitivity draft values; NOISE2 sensitivity extra at 0.
    allow_typ = zero()
    for r in RAILS:
        for a in sel['allowances'][r]:
            if a['id'].startswith(('H1:', 'H2:')):
                allow_typ[r] += a['mA'] / led['draft_allowances'][a['id']]['sensitivity_multiplier']
            elif a['id'] != 'NOISE2-extra-sensitivity':
                allow_typ[r] += a['mA']
    allow_typ = {r: r6(v) for r, v in allow_typ.items()}

    fixed_plan = add(cats[Q_IC]['planning_mA'], cats[Q_LOGIC]['planning_mA'], cats[S_STATIC]['planning_mA'], reserves, allow_plan)
    fixed_typ = add(cats[Q_IC]['typical_mA'], cats[Q_LOGIC]['typical_mA'], cats[S_STATIC]['typical_mA'],
                    cats[R_RESERVE]['typical_mA'], allow_typ)
    var_plan = add(cats[P_INTERNAL]['planning_mA'], cats[P_SIGNAL]['planning_mA'], cats[P_OPER]['planning_mA'])
    var_typ = add(cats[P_INTERNAL]['typical_mA'], cats[P_SIGNAL]['typical_mA'], cats[P_OPER]['typical_mA'])
    user_typ = add(cats[P_SIGNAL]['typical_mA'], cats[P_OPER]['typical_mA'])
    # Stage54 confirms the A0x/M4x/M5x clip comparators sit on -12 V; it corrects
    # their typical -12 V current up (planning already charges it).
    clip = s54['clip_comparator_accounting']
    require(clip['planning_correction_mA'] == 0, 'clip comparator planning correction')
    clip_typ = {'+12V': 0.0, '-12V': clip['negative_typical_correction_mA'], '+5V': 0.0}
    iq_spread = sub(add(cats[Q_IC]['planning_mA'], cats[Q_LOGIC]['planning_mA']),
                    add(cats[Q_IC]['typical_mA'], cats[Q_LOGIC]['typical_mA']))

    step, reserve = env['current_rounding_mA'], env['reserve_fraction']
    ramp = sel['full_capacitance_ramp_increment_mA']
    fault = env['fault_increment_mA']
    stage54_iq = s54['removed_Iq_mA']['planning_Iq']

    def level(cls, mA, basis, rule=True):
        out = {'classification': cls, 'mA': mA,
               'rail_output_W_nominal': watts(mA, NOMINAL_V),
               'rail_output_W_source_band_max': watts(mA, v_hi),
               'basis': basis}
        if rule:
            out['continuous_rule_result_mA'] = continuous_rule(mA, reserve, step)
        return out

    normal_typ = add(fixed_typ, var_typ, clip_typ)
    # Ramp term = C x (1 + tolerance) x upper load-band voltage / minimum soft start.
    tol, t_ms = src['capacitance_tolerance_fraction'], src['soft_start_min_ms']
    v_load = {r: src['required_load_voltage_magnitude_V'][r][1] for r in RAILS}
    def ramp_mA(uF):
        return {r: r6(uF[r] * (1 + tol) * v_load[r] / t_ms) for r in RAILS}
    for r, v in ramp_mA(src['nominal_capacitance_ceiling_uF']).items():
        require(abs(v - ramp[r]) < 1e-6, 'ceiling ramp reproduced ' + r)
    ramp_fitted = ramp_mA(FITTED_UF)
    heavy = sub(canonical, per_rail_overcount)
    overlap_W = r6(one_rail_overlap['+12V'] / 1000 * 12)
    usage = add(fixed_plan, cats[P_INTERNAL]['planning_mA'], user_typ)
    levels = {
        'normal_typical': level(
            'CALCULATED from reported/assumed typical rows; UNVERIFIED',
            normal_typ, 'Every row at its reported/assumed typical, plus the Stage54 clip-comparator -12 V typical correction; allowances at pre-sensitivity draft values (protection/supervision and reference/logic included, unlike the ledger reported typical subtotal).'),
        'heavy_realistic_patch': level(
            'CALCULATED planning upper with documented impossible combinations removed; UNVERIFIED',
            heavy, 'Canonical planning (full-temperature maximum Iq, every output into 10 kohm at 5 V, every indicator at planning brightness, all reserves) minus only the per-rail charges whose own worksheet basis says cannot occur. Every output may hold a positive DC CV at once, so per-rail signal loads are not halved.'),
        'canonical_planning_all_upper_terms': level(
            'PLANNING ALLOCATION (canonical; governs the current requirement)',
            canonical, 'supply-architecture.json selected_requirement.normal_with_allowances_mA, reproduced row by row.'),
        'explicit_usage_limit_candidate': level(
            'CANDIDATE operating range (PWR-D5); CALCULATED, UNVERIFIED; not a requirement',
            usage, 'Fixed parts and internal signal paths at planning; external patch/indicator and operation rows held to their typical values by a stated usage limit (for example: indicators near typical brightness, outputs into typical 100 kohm loads). Shows the most any patch-based usage limit can remove; enforcement is by user instruction only.'),
        'startup_worst_envelope': level(
            'CONSERVATIVE ENVELOPE (calculated); UNVERIFIED',
            add(canonical, ramp), 'Canonical planning plus the full-capacitance ramp at the 10 ms minimum soft start (capacitance ceiling +20 %). Loads draw less at reduced voltage, so this overstates a real ramp; the 20 ms transient requirement covers it with the one-fault increment.', rule=False),
        'startup_envelope_fitted_capacitance': level(
            'CALCULATED from OSC-owner-reported fitted capacitance; UNVERIFIED; not a contract value',
            add(canonical, ramp_fitted), 'Canonical planning plus the ramp of the fitted 49.9 / 42.2 / 24.5 uF (+20 %) at the 10 ms minimum soft start. The contract keeps the 150 / 150 / 100 uF ceiling and the transient requirement unchanged; a later capacitance addition up to the ceiling stays allowed.', rule=False),
        'transient_requirement_20ms': level(
            'CONTRACT REQUIREMENT (unchanged)', sel['minimum_transient_mA'],
            'canonical + ramp + one external-forcing fault, rounded; supply-architecture.json', rule=False),
        'continuous_requirement': level(
            'CONTRACT REQUIREMENT (unchanged)', sel['minimum_continuous_mA'],
            'canonical x 1.1, rounded up to 100 mA', rule=False),
    }
    levels['heavy_realistic_patch']['rail_output_W_nominal_one_rail_at_a_time'] = r6(levels['heavy_realistic_patch']['rail_output_W_nominal'] - overlap_W)
    # Reproduce the requirement rule on the canonical level.
    require(levels['canonical_planning_all_upper_terms']['continuous_rule_result_mA'] == sel['minimum_continuous_mA'], 'continuous rule')
    for r in RAILS:
        require(sel['minimum_transient_mA'][r] >= canonical[r] + ramp[r] + fault[r] - 1e-6, 'transient covers startup and fault ' + r)

    budget_steps = {
        'fixed_quiescent_and_static_planning_mA': fixed_plan,
        'of_which_coarse_reserve_mA': reserves,
        'of_which_inlet_protection_reference_logic_allowances_mA': allow_plan,
        'patch_signal_and_operation_planning_mA': var_plan,
        'canonical_planning_mA': canonical,
        'reserve_x1_1_and_100mA_rounding_mA': sub(sel['minimum_continuous_mA'], canonical),
        'continuous_requirement_mA': sel['minimum_continuous_mA'],
        'startup_ramp_and_fault_to_transient_mA': sub(sel['minimum_transient_mA'], sel['minimum_continuous_mA']),
        'transient_requirement_mA': sel['minimum_transient_mA'],
    }
    share = {r: r6(fixed_plan[r] / canonical[r]) for r in RAILS}

    sixty = {}
    for name in ('normal_typical', 'heavy_realistic_patch', 'canonical_planning_all_upper_terms',
                 'explicit_usage_limit_candidate', 'continuous_requirement', 'transient_requirement_20ms'):
        w = levels[name]['rail_output_W_source_band_max']
        sixty[name] = {'rail_output_W_source_band_max': w,
                       'end_to_end_efficiency_needed_60W': r6(w / 60),
                       'end_to_end_efficiency_needed_57W_source_minus_5pct': r6(w / 57)}

    # Current PD chain: LDO post-regulators draw output current from pre-rails no lower
    # than the PD-screened minima, so converter input power is at least this / efficiency.
    chain60 = {}
    for name in ('normal_planning', 'continuous_requirement', 'startup_envelope_10ms', 'transient_requirement_20ms'):
        pre = pw[name]['current_pd_chain_pre_rail_W_lower_bound']['screened_minimum_setpoints']
        chain60[name] = {'pre_rail_W_lower_bound': pre,
                         'converter_efficiency_needed_60W': r6(pre / 60),
                         'converter_efficiency_needed_57W_source_minus_5pct': r6(pre / 57)}

    return {
        'schema_version': 1,
        'status': 'UNVALIDATED DRAFT decomposition; arithmetic on committed worksheet rows; nothing measured; no requirement changed',
        'request': 'https://github.com/Takazudo/zudo-pd/issues/218#issuecomment-6284861864',
        'inputs_sha256': {k: {'path': p, 'sha256': sha(p)} for k, p in INPUTS.items()},
        'classification_legend': {
            'CALCULATED': 'arithmetic on committed rows; inherits each row\'s own status (typical, planning, assumption)',
            'MEASURED': 'none; no whole-instrument or module current has been measured',
            'UNVERIFIED': 'every calculated level until bench measurement',
            'CONTRACT': 'existing requirement, unchanged',
            'CANDIDATE': 'possible new operating range for an owner decision (PWR-D5); never booked'},
        'categories': cats,
        'budget_steps': budget_steps,
        'fixed_share_of_canonical': share,
        'double_counting_and_margins': {
            'per_rail_overcount_documented_mA': per_rail_overcount,
            'per_rail_overcount_rows': overcount_rows,
            'one_rail_at_a_time_overlap_mA': {
                'mA_on_each_analog_rail': one_rail_overlap['+12V'],
                'power_W_removable_at_nominal': overlap_W,
                'note': 'Jack loads and magnitude LEDs return to ground and draw from one analog rail at a time; this lowers total power only. Per-rail current is unchanged because all outputs may sit at one polarity together.'},
            'iq_spread_planning_minus_typical_mA': iq_spread,
            'iq_spread_note': 'Planning mixes guaranteed full-temperature maxima (TI OPA419x) with unverified planning allowances (ADG5412 extrapolated to +/-12 V, HC logic, NOISE2, LM13700) that could be exceeded. The sum of ~260 packages is unlikely to sit at every maximum, but no distribution is retained, so no statistical credit is taken without measurement.',
            'lm393_minus12': 'Stage54 clip_comparator_accounting confirms pin 4 on -12V for every LM393 row that charges -12 V (A01-A06, M4A/B, M5A/B), despite a row basis saying no -12 V current; planning stays, typical gains 10 mA. H/O/E LM393 rows book 0 mA on -12 V (possible under-booking, open).',
            'trim_current_inside_reserves_mA_per_analog_rail': s54['nominal_trim_current_contained_in_reserves_mA_per_analog_rail'],
            'ota_bias_overlap_with_reserves': 'OPEN: reserve rows state a conservative overlap with the inherited OTA bias allowance (26 IABC branches); size unknown, no credit taken.',
            'stage54_idle_quads_planning_Iq_mA': stage54_iq,
            'ramp_increment_ceiling_mA': ramp,
        'ramp_increment_fitted_mA': ramp_fitted,
        'stage54_note': 'Unadopted conditional removal of idle op-amp quads; listed separately, not applied to any level.',
        },
        'levels': levels,
        'sixty_watt_class_screen': {
            'status': 'Rail output power only. Charger input power = rail output / end-to-end efficiency (converters, LDO headroom, cable, PDO). No efficiency is booked here; the PD owner screens the supply side.',
            'levels': sixty,
            'current_ldo_chain_at_60W': chain60,
            'current_ldo_chain_note': 'From ledger.json: pre-rail power with the existing LDO post-regulation (PD-screened minimum pre-rail setpoints). Converter efficiency is not booked; PD screened about 0.85 at its own 1.2/0.8/0.5 A targets.'},
        'measured': {r: None for r in RAILS},
    }


def main():
    out = HERE / 'decomposition.json'
    text = json.dumps(build(), indent=2, ensure_ascii=False, default=sorted) + '\n'
    if '--check' in sys.argv:
        if out.read_text() != text:
            raise SystemExit('FAIL decomposition.json is stale; run decompose.py')
        print('PASS decomposition.json up to date')
        return
    out.write_text(text)
    print('wrote', out.relative_to(ROOT))


if __name__ == '__main__':
    main()
