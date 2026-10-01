"""Reproduce protection blockers and inventory from authored circuit sources.

Default success means the blocked assessment is internally consistent. Use
--require-closed as an implementation gate; it deliberately fails while open.
No truth table or resistance calculation here is a hardware simulation.
"""
from pathlib import Path
from collections import Counter
import argparse
import hashlib
import itertools
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification
from design.spec.cells._builder import CELLS
from scripts.schgen.core import designator


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def draft_contract_check(draft):
    demand(draft['kind'] == 'REQUIREMENT ONLY' and draft['status'] == 'NON-ORDERABLE / NOT-ENERGIZABLE', 'Draft boundary status cannot imply implemented hardware')
    for field in ('protection_implemented', 'orderable', 'energization_authorized', 'physical_source_selected', 'parallel_regulated_outputs_permitted'):
        demand(draft[field] is False, f'False hardware promotion: {field}')
    demand(draft['selected_protection_mpn'] is None, 'No exact protection MPN is selected')
    demand(draft['domain'] == 'EXT' and draft['regulated_source_count'] == 1, 'Draft domain must remain EXT only')
    demand(draft['fixed_module_count'] == 33 and draft['fixed_feature_count'] == 438, 'Draft scope reduction is not permitted')
    demand(draft['ordinary_powered_off_patching_permitted'] is True, 'Power-off patching cannot be removed from scope')
    demand(draft['circuit_evidence_issue'].endswith('/issues/59') and draft['physical_qualification_issue'].endswith('/issues/57'), 'Circuit and physical follow-ups must remain distinct')
    return 'PASS: conditional draft contract ONLY; protection unimplemented; NON-ORDERABLE / NOT-ENERGIZABLE'


def check_candidate_research(research, root=ROOT):
    """Check research receipts and optional cached bytes; never promote hardware."""
    missing_cache = []
    demand(research['status'] == 'RESEARCH ONLY; no candidate selected or installed'
           and research['protection_implemented'] is False,
           'Candidate research cannot claim implemented protection')
    for source in research['sources']:
        demand(source['selection'] == 'NOT SELECTED' and source['installed'] is False,
               'Candidate research cannot select or install a part')
        demand(source['project_performance_verdict'] == 'UNSOURCED',
               'Candidate project-condition performance remains unresolved')
        if 'normal_iq_screen' in source:
            screen = source['normal_iq_screen']
            demand(screen['project_verdict'] == 'UNSOURCED'
                   and all(type(screen[k]) in (int, float) and math.isfinite(screen[k]) and screen[k] > 0
                           for k in ('positive_mA', 'negative_mA')),
                   'Candidate current screen must retain positive conditioned values and unresolved project limits')
        demand(source['availability'] in ('AVAILABLE', 'SOURCE UNAVAILABLE'),
               'Unknown candidate source availability')
        if source['availability'] == 'AVAILABLE':
            digest = source['sha256']
            demand(len(digest) == 64 and digest != '0' * 64
                   and all(c in '0123456789abcdef' for c in digest),
                   f"Invalid candidate source hash: {source['candidate']}")
            demand(source['retention']['mode'] == 'LOCAL CACHE ONLY',
                   'Candidate source retention must respect inspected reproduction terms')
            path = root / source['file']
            if path.exists():
                raw = path.read_bytes()
                demand(raw.startswith(b'%PDF-') and hashlib.sha256(raw).hexdigest() == digest,
                       f"Source bytes changed: {source['candidate']}")
            else:
                missing_cache.append(source['candidate'])
        else:
            demand(source['file'] is None and source['sha256'] == '0' * 64,
                   'Unavailable candidate source cannot claim retained bytes')
    return missing_cache


def build(contract=None):
    contract = contract or json.loads((ROOT / 'design/power/supply-architecture-input.json').read_text())
    demand(set(contract['domains']) == {'EXT'}, 'Only one EXT source domain is permitted')
    demand(contract['domains']['EXT']['regulated_nets'] == {r: r for r in ('+12V', '-12V', '+5V')}, 'Source-domain net separation changed')
    demand(contract['physical_source']['status'] == 'NOT SELECTED', 'Reassess protection against selected physical source')
    draft = json.loads((ROOT / 'design/power/protection58-draft-contract.json').read_text())
    draft_status = draft_contract_check(draft)
    for name in ('precision_output', 'general_output'):
        parts = {p['ref']: p for p in CELLS[name]['parts']}
        demand(parts['R_ISO_A']['value'] == parts['R_ISO_B']['value'] == 499, 'Output resistance changed; reassess fault current')
        if name == 'precision_output':
            demand(parts['R_FB']['value'] == 100 and parts['R_FB']['terminals'] == {'1': 'JACK', '2': 'FB'}, 'Precision sense path changed; reassess exposure')
    for source in json.loads((ROOT / 'design/power/protection58-sources.json').read_text())['sources']:
        if source['availability'] == 'AVAILABLE':
            raw = (ROOT / source['file']).read_bytes()
            demand(raw.startswith(b'%PDF-') and hashlib.sha256(raw).hexdigest() == source['sha256'], f"Source bytes changed: {source['candidate']}")
        else:
            demand(source['sha256'] == '0' * 64 and source['selection'] == 'NOT SELECTED', 'Unavailable evidence cannot select a candidate')
    research_path = ROOT / 'design/power/protection59-sources.json'
    research = json.loads(research_path.read_text())
    check_candidate_research(research)
    placements = json.loads((ROOT / 'design/grid/placements.lock.json').read_text())['placements']
    locked = {p['uid']: p for p in placements}
    families, instances = specification()
    families = {f.name: f for f in families}
    outputs = []
    packages = 0
    references = []
    existing_switch_packages = set()
    for instance in instances:
        if instance.name == 'POWER':
            continue
        family = families[instance.family]
        existing_switch_packages.update(designator(p, instance) for p in family.parts
                                        if p.symbol.endswith('ADG5412FBRUZ') and not p.dnp)
        jacks = {p.pins['T']: p for p in family.parts if p.prefix == 'J' and 'T' in p.pins}
        channels = 0
        for part in family.parts:
            role = part.attributes.get('Role', '')
            if role not in ('general_output:R_ISO_B', 'precision_output:R_ISO_B'):
                continue
            jack = jacks[part.pins['2']]
            uid = jack.attributes['PanelUid'].replace('${SHEETNAME}', instance.name)
            demand(uid in locked and locked[uid].get('direction') == 'out', f'Unbound output: {uid}')
            precision = role.startswith('precision')
            outputs.append({'uid': uid, 'instance': instance.name, 'tip_net': part.pins['2'], 'kind': 'precision' if precision else 'general', 'existing_series_ohm': 998, 'existing_sense_ohm': 100 if precision else None, 'isolation_channels_required': 2 if precision else 1, 'status': 'UNPROTECTED OUTPUT/SENSE; candidate not captured'})
            channels += 2 if precision else 1
        packages += math.ceil(channels / 4)
        if instance.family == 'oscillator':
            refs = sorted(n for n in family.global_nets if n.startswith('OSC_OCT'))
            demand(len(refs) == 6, 'Octave reference boundary changed')
            for net in refs:
                pins = [{'ref': designator(p, instance), 'pin': pin, 'role': p.attributes.get('Role')} for p in family.parts for pin, n in p.pins.items() if n == net]
                demand(pins, f'Declared reference has no actual receiver pin: {instance.name}/{net}')
                references.append({'instance': instance.name, 'net': net, 'receiver_pins': pins, 'status': 'Receiver input and source buffer require partial-connector analysis; no isolation captured'})
    expected = {p['uid'] for p in placements if p.get('direction') == 'out'}
    demand({o['uid'] for o in outputs} == expected and len(outputs) == len(expected), 'Not every locked output is audited exactly once')
    demand(len(outputs) == 82 and sum(o['kind'] == 'precision' for o in outputs) == 16, 'Output inventory changed; reassess')
    demand(len(placements) == 438 and len(contract['domains']['EXT']['module_instances']) == 34, 'Fixed scope changed (33 modules plus reference island)')
    channels = sum(o['isolation_channels_required'] for o in outputs)
    rails = ('+12V', '-12V', '+5V')
    declared_continuous = contract['source_requirement'].get('minimum_continuous_current_mA', {})
    demand(set(declared_continuous) == set(rails)
           and all(type(v) in (int, float) and math.isfinite(v) and v > 0
                   for v in declared_continuous.values()),
           'Missing or invalid declared continuous-current contract')
    continuous = {r: declared_continuous[r] / 1000 for r in rails}
    maximum = {r: v / 1000 for r, v in contract['source_requirement']['maximum_delivered_current_mA'].items()}
    demand(all(maximum[r] >= continuous[r] for r in rails), 'Continuous requirement exceeds maximum delivered current')
    protection_drop = contract['inlet']['harness']['max_protection_drop_V']
    demand(protection_drop == .04, 'Original 40 mV protection-drop budget changed')
    loss = {r: {'continuous_A': i, 'maximum_delivered_A': maximum[r], 'protection_drop_budget_V': protection_drop, 'resistance_budget_ohm_at_continuous': protection_drop / i, 'resistance_budget_ohm_at_maximum': protection_drop / maximum[r], 'legacy_ptc_drop_V': i * .25, 'legacy_ptc_dissipation_W': i * i * .25, 'two_fet_hot_drop_V_at_maximum': maximum[r] * 2 * .00245, 'two_fet_hot_dissipation_W_at_maximum': maximum[r] ** 2 * 2 * .00245} for r, i in continuous.items()}
    reference_packages = sum(math.ceil(count / 4) for count in Counter(r['instance'] for r in references).values())
    candidate = next(s for s in research['sources'] if s['candidate'] == 'TMUX7412FRRPR')
    iq = candidate['normal_iq_screen']
    replacement_count = len(existing_switch_packages) + packages + reference_packages
    candidate_current = {'+12V': replacement_count * iq['positive_mA'], '-12V': replacement_count * iq['negative_mA']}
    old_current = {'+12V': len(existing_switch_packages) * 1.3, '-12V': len(existing_switch_packages) * .7}
    truth_table = [{'valid_rails': dict(zip(continuous, state)), 'required_signal_enable': all(state), 'implemented': False} for state in itertools.product((False, True), repeat=3)]
    return {
        'schema_version': 1,
        'status': 'BLOCKED: no complete source-backed protection architecture selected',
        'selected_topology': None,
        'conditional_draft_gate': draft_status,
        'circuit_evidence_issue': draft['circuit_evidence_issue'],
        'draft_gate_does_not_check': 'Current schematic implementation, orderable part selection, routing, fit, thermal, physical source or energization',
        'physical_checks': 'NOT RUN: no populated hardware or selected source',
        'source_domain': 'EXT only; current limit is an external-source/inlet requirement, not a synth-side sense resistor requirement',
        'continuous_current_source': 'design/power/supply-architecture-input.json: source_requirement.minimum_continuous_current_mA; independently checked against ledger by build_supply_architecture.py',
        'loss_calculations': loss,
        'fet_conditions': 'PSMN1R0-40YLD Table 7: 2.45 mOhm at VGS=4.5 V, Tj=150 C, ID=25 A; resistance-only feasibility screen, no selected driver, SOA, reverse cutoff or thermal proof',
        'output_count': len(outputs), 'precision_count': 16, 'output_switch_channels': channels,
        'global_quad_minimum': math.ceil(channels / 4), 'module_local_quad_minimum': packages,
        'normal_positive_Iq_mA_sensitivity_global': math.ceil(channels / 4) * 1.3,
        'normal_positive_Iq_mA_sensitivity_local': packages * 1.3,
        'existing_aux_allowance_mA': contract['load_envelope']['auxiliary_allowance_mA']['+12V'],
        'candidate_switch_sensitivity': {
            'status': 'CONDITIONED PLANNING ONLY; no substitution, reuse or current saving booked',
            'candidate': candidate['candidate'],
            'evidence_file': str(research_path.relative_to(ROOT)),
            'evidence_sha256': hashlib.sha256(research_path.read_bytes()).hexdigest(),
            'evidence_scope': 'Actual TI bytes inspected; metadata/extracts committed; development-only PDF cache is optional and never a hardware-validation gate',
            'conditions': iq['conditions'],
            'project_verdict': iq['project_verdict'],
            'existing_ADG_package_refs': sorted(existing_switch_packages),
            'existing_ADG_package_count': len(existing_switch_packages),
            'receiver_local_quad_minimum': reference_packages,
            'new_module_and_receiver_local_quads': packages + reference_packages,
            'replace_existing_and_add_count': replacement_count,
            'existing_ADG_planning_mA': old_current,
            'replacement_and_addition_sensitivity_mA': candidate_current,
            'delta_to_existing_ADG_planning_mA': {r: round(candidate_current[r] - old_current[r], 6) for r in old_current},
        },
        'prospective_current_mA': {'original_sense_12V_100ohm': 12 / 100 * 1000, 'revised_sense_24_48V_2740ohm_minus1percent': 24.48 / (2740 * .99) * 1000, 'main_24_48V_998ohm_minus1percent': 24.48 / (998 * .99) * 1000},
        'prospective_each_499ohm_dissipation_W': (24.48 / (998 * .99)) ** 2 * (499 * .99),
        'outputs': sorted(outputs, key=lambda o: o['uid']),
        'reference_receivers': references,
        'required_state_table': truth_table,
        'arrival_orders': [list(p) for p in itertools.permutations(continuous)],
        'return_counterexample': {'healthy_inlet_return_ohm': .020, 'failed_inlet_return_ohm': None, 'replacement_patch_return_ohm': .020, 'test_net_return_A': 1, 'observed_AGND_shift_V_healthy': .020, 'observed_AGND_shift_V_failed': .020, 'conclusion': 'Identical rail-voltage observations; rail-only monitoring cannot distinguish these states. This is not impossibility of a separately instrumented return path.'},
        'open_gates': ['Exact three-rail gate drive/reverse cutoff and hot SOA', 'Guaranteed sensing windows, control supply, all six arrival/failure orders, hiccup/discharge timing and let-through', 'Output/sense switch bounds at project supplies and during floating/partial power', 'Package/island/reference allocation within actual rail/capacitance budgets', 'Observable inlet-return failure independent of patch sleeves; mechanical pilot alone does not detect broken wires', 'Local device-GND loss is outside grounded analog-switch guarantees', 'Enabled output contention: resistor derating, amplifier/package dissipation and actual switch fault transients'],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--require-closed', action='store_true')
    parser.add_argument('--require-draft', action='store_true')
    args = parser.parse_args()
    report = build()
    path = ROOT / 'design/power/protection58-audit.json'
    content = json.dumps(report, indent=2) + '\n'
    if args.check:
        demand(path.read_text() == content, 'Protection audit drift; regenerate')
    else:
        path.write_text(content)
    print('PASS: protection audit consistency ONLY; 82 outputs / 16 sense paths / 30 reference receivers')
    print('BLOCKED: exact protection implementation gate; no topology selected; physical checks NOT RUN')
    research = json.loads((ROOT / 'design/power/protection59-sources.json').read_text())
    for candidate in check_candidate_research(research):
        print(f'NOT RUN: optional candidate cache byte/hash check for {candidate}; cached PDF absent, acquisition receipt/extracts retained')
    if args.require_draft:
        print(report['conditional_draft_gate'])
    if args.require_closed:
        return 1 if report['open_gates'] else 0
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
