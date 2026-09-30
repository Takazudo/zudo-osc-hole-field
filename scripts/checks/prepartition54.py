#!/usr/bin/env python3
"""Check the issue #54 conditional pre-partition confirmation snapshot."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
REPORT = ROOT / 'design/reports/pre-partition-confirm.json'
CAPTURE_COMMIT = 'a594b96c81e9b7c2919dc761b68533af9f5d4c56'
SOURCE_COMMIT = '4cc30612c4d9cd0597caae2eccd1967b8870c6b9'
PREREQUISITES = {
    '#52': '1a2f33cf6e61cf89c7422a1a42122806f68e3033',
    '#47': '95d44b47d4a8b17f7980ebb8073679a4212d44b4',
    '#53': 'b27bc800219fe3b75ce6559fb763e38378ff1f9a',
    '#56': '4dd813760d00a1f2a7513713bda835975c93fcb6',
}
SNAPSHOT_FILES = (
    'design/spec/instrument.py',
    'design/spec/modules/power.py',
    'design/grid/placements.lock.json',
    'schematic/zudo-osc-hole-field.kicad_sch',
    'design/reports/master-audit.json',
    'design/reports/netlist-stats.json',
    'design/reports/master-erc-warning-baseline.json',
    'design/reports/power-boundary.json',
    'design/power/supply-architecture-input.json',
    'design/power/supply-architecture.json',
    'design/power/rail-budget.json',
    'design/power/rail-ledger.json',
    'design/power/protection58-draft-contract.json',
    'design/power/protection58-audit.json',
    'design/power/protection58-output-model.json',
    'design/mechanical/selector-assembly.json',
    'design/mechanical/selector-assembly-check.json',
    'scripts/pcbgen/netlist.py',
    'design/boards/fixture-route-dense.json',
    'scripts/pcbgen/fixtures/dense-evidence/copper.json',
    'scripts/pcbgen/fixtures/dense-evidence/stitching.json',
    'scripts/pcbgen/fixtures/dense-evidence/preservation.json',
    'scripts/pcbgen/fixtures/dense-evidence/final-drc.json',
    'scripts/pcbgen/fixtures/dense-evidence/verification.json',
    'design/reports/spice/cells.json',
    'design/reports/spice/envelope.json',
    'design/reports/spice/filter.json',
    'design/reports/spice/mixers.json',
    'design/reports/spice/noise.json',
    'design/reports/spice/offset.json',
    'design/reports/spice/oscillator.json',
    'design/reports/spice/sample_hold.json',
    'design/reports/spice/wavefolder.json',
    'design/reports/spice/precision-output-sweep.json',
    'design/reports/spice/precision-output-vendor.json',
    'scripts/checks/prepartition54.py',
    'scripts/checks/regen-all.sh',
    'scripts/schgen/audit_master.py',
    'scripts/schgen/check_erc_warnings.py',
    'scripts/schgen/smoke.sh',
    'scripts/schgen/regen-master-reports.sh',
    'scripts/schgen/README.md',
    'design/power/downstream-handoff-52.md',
    'design/power/downstream-amendments-48.md',
    'design/power/downstream-amendments-58.md',
    'doc/src/content/docs/verification/osc-precision-output-model.mdx',
    'doc/src/content/docs/decisions/osc-selector-assembly.mdx',
    'doc/src/content/docs/decisions/osc-supply-architecture.mdx',
    'design/spec/modules/run_envelope_spice.py',
    'design/spec/modules/run_filter_spice.py',
    'design/spec/modules/run_mixer_spice.py',
    'design/spec/modules/run_noise_spice.py',
    'design/spec/modules/run_offset_spice.py',
    'design/spec/modules/run_oscillator_spice.py',
    'design/spec/modules/run_sample_hold_spice.py',
    'design/spec/modules/run_wavefolder_spice.py',
    'design/spec/cells/sweep_precision.py',
    'design/spec/cells/sweep_precision_vendor.py',
    'design/spec/cells/run_spice.py',
    'scripts/checks/protection58.py',
    'scripts/checks/protection58_model.py',
    '.claude/skills/component-alps-alpine-srbv160803/manifest.json',
    '.claude/skills/component-alps-alpine-srbv160803/sources.json',
    '.claude/skills/component-alps-alpine-srbv160803/facts.json',
    '.claude/skills/component-alps-alpine-srbv160803/coverage.json',
    '.claude/skills/component-alps-alpine-srbv160803/interactions.json',
    '.claude/skills/component-alps-alpine-srbv160803/pin-map.json',
    '.claude/skills/component-dealon-dw254p-2x8-l0/manifest.json',
    '.claude/skills/component-dealon-dw254p-2x8-l0/sources.json',
    '.claude/skills/component-dealon-dw254p-2x8-l0/facts.json',
    '.claude/skills/component-dealon-dw254p-2x8-l0/coverage.json',
    '.claude/skills/component-dealon-dw254p-2x8-l0/interactions.json',
    '.claude/skills/component-dealon-dw254p-2x8-l0/pin-map.json',
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text())


def sha256(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def canonical_netlist_sha256(path: Path) -> str:
    text = path.read_text()
    text, count = re.subn(
        r'(?m)^(\t\t\(date ")[^"]+("\))$',
        r'\1<NORMALIZED_KICAD_EXPORT_DATE>\2', text, count=1,
    )
    require(count == 1, 'native KiCad netlist export timestamp field was not uniquely found')
    return hashlib.sha256(text.encode()).hexdigest()


def check_commit_ancestry() -> None:
    for commit in (SOURCE_COMMIT, *PREREQUISITES.values()):
        exists = subprocess.run(
            ['git', 'cat-file', '-e', f'{commit}^{{commit}}'], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        require(exists.returncode == 0, f'missing provenance commit: {commit}')
    for issue, commit in PREREQUISITES.items():
        result = subprocess.run(
            ['git', 'merge-base', '--is-ancestor', commit, SOURCE_COMMIT], cwd=ROOT,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        require(result.returncode == 0, f'{issue} prerequisite is not in source commit {SOURCE_COMMIT}')


def export_native_netlist() -> Path:
    out = ROOT / '.circuit-cache/prepartition54/master.net'
    out.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'sch', 'export', 'netlist',
         '--format', 'kicadsexpr', '-o', out.relative_to(ROOT).as_posix(),
         'schematic/zudo-osc-hole-field.kicad_sch'],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    require(result.returncode == 0, 'pinned KiCad native netlist export failed: ' + result.stderr[-1200:])
    return out


def check_precision_islands(families, instances, module_names: set[str]) -> int:
    family_by_name = {family.name: family for family in families}
    output_count = 0
    for instance in instances:
        if instance.name not in module_names:
            continue
        family = family_by_name[instance.family]
        parts = [p for p in family.parts if p.attributes.get('Role', '').startswith('precision_output:')]
        feedback_parts = [p for p in parts if p.attributes.get('Role', '').endswith(':R_FB')]
        compensation_parts = [p for p in parts if p.attributes.get('Role', '').endswith(':C_FAST')]
        require(len(feedback_parts) == len(compensation_parts), f'{instance.name}: precision feedback/compensation count differs')
        for feedback in feedback_parts:
            compensation = next((p for p in compensation_parts if p.pins.get('2') == feedback.pins.get('2')), None)
            require(compensation is not None, f'{instance.name}: missing local compensation for {feedback.key}')
            require(feedback.attributes.get('Island') == compensation.attributes.get('Island') != '',
                    f'{instance.name}: jack feedback and compensation do not share a named island')
            require(feedback.pins.get('1') not in family.global_nets and feedback.pins.get('2') not in family.global_nets,
                    f'{instance.name}: precision feedback net became global')
            require(compensation.pins.get('1') not in family.global_nets and compensation.pins.get('2') not in family.global_nets,
                    f'{instance.name}: precision compensation net became global')
            output_count += 1
    require(output_count == 16, f'precision feedback/compensation boundaries changed: {output_count} != 16')
    return output_count


def check_report(capture_check: bool = False) -> None:
    report = read_json('design/reports/pre-partition-confirm.json')
    require(report.get('schema_version') == 1, 'unsupported report schema')
    require(report.get('report_date') == '2026-09-28', 'report date changed; rerun the authored verification')
    require(report.get('status') == 'CONDITIONAL PARTITION INPUTS CONFIRMED; UNVALIDATED DRAFT',
            'report must preserve conditional draft status')
    provenance = report.get('provenance', {})
    require(provenance.get('source_commit') == SOURCE_COMMIT, 'source commit drift')
    require(provenance.get('base_branch') == 'base/osc-hole-field', 'base branch drift')
    require(provenance.get('prerequisite_commits') == PREREQUISITES, 'prerequisite SHA drift')
    check_commit_ancestry()

    snapshot = report.get('snapshot', {})
    snapshot_hashes = snapshot.get('tracked_input_sha256', {})
    require(set(snapshot_hashes) == set(SNAPSHOT_FILES) and
            all(re.fullmatch(r'[0-9a-f]{64}', value) for value in snapshot_hashes.values()),
            'report must contain a complete SHA-256 inventory of the captured pre-partition inputs')
    require(re.fullmatch(r'[0-9a-f]{64}', snapshot.get('native_netlist_sha256', '')) is not None and
            snapshot.get('kicad_version') == '10.0.6',
            'report must pin a canonical native netlist hash and KiCad 10.0.6')
    require(snapshot.get('superseded_by') == [
                'issue #35 partition-specific source/placement reconciliation',
                'issue #37 panel regeneration and board-level checks',
            ], 'report must identify the downstream checks that supersede its live snapshot')
    # This mode is intentionally an entry-phase gate. Once #35/#37 mutate
    # placements, source partition, or generated board artifacts, a historical
    # pre-partition report must not fail simply because those authorized inputs
    # changed. The default mode verifies the durable report/provenance; this
    # explicit mode compares the captured hashes and re-runs live CAD/source
    # checks while the project is still at the pre-partition boundary.
    if not capture_check:
        # Validate the committed #54 capture, not a later legitimate live ERC
        # inventory. The recorded snapshot hash authenticates these bytes.
        baseline_path = 'design/reports/master-erc-warning-baseline.json'
        captured = subprocess.check_output(['git', 'show', f'{CAPTURE_COMMIT}:{baseline_path}'], cwd=ROOT)
        require(hashlib.sha256(captured).hexdigest() == snapshot_hashes[baseline_path],
                'historical ERC baseline does not match the #54 snapshot')
        erc_baseline = json.loads(captured)
        erc_inventory_digest = hashlib.sha256(json.dumps(
            erc_baseline['warnings'], sort_keys=True, separators=(',', ':')
        ).encode()).hexdigest()
        require(erc_baseline['warning_count'] == 228 and
                erc_baseline['kicad_version'] == '10.0.6' and
                sum(erc_baseline['warnings_by_sheet'].values()) == 228 and
                all(item['severity'] == 'warning' and item['type'] == 'pin_to_pin'
                    for item in erc_baseline['warnings']) and
                erc_baseline['warning_inventory_sha256'] == erc_inventory_digest,
                'durable ERC warning identity baseline is invalid')
        require(report['captured_master']['erc_warning_inventory_sha256'] == erc_baseline['warning_inventory_sha256'] and
                report['captured_master']['erc_warnings_by_sheet'] == erc_baseline['warnings_by_sheet'],
                'report ERC warning identities differ from the pinned baseline')
        required_command_ids = {
            'pre_edit_circuit_check', 'baseline_regeneration', 'pnpm_check',
            'post_edit_circuit_check', 'master_erc_netlist', 'regen_twice',
            'selector_fixture', 'dense_fixture', 'focused_tests',
            'abstract_filter_tests', 'protection_draft_gate', 'protection_closed_gate',
            'prepartition54_capture_check',
        }
        command_results = {item['id']: item for item in report.get('command_results', [])}
        require(required_command_ids <= command_results.keys(), 'report is missing required command results')
        for command_id in required_command_ids - {'protection_closed_gate'}:
            require(command_results[command_id]['status'] == 'PASS' and
                    command_results[command_id]['exit_code'] == 0,
                    f'recorded report gate is not passing: {command_id}')
        require(command_results['protection_closed_gate']['status'] == 'OPEN (EXPECTED)' and
                command_results['protection_closed_gate']['exit_code'] == 1,
                '#59 implementation gate must remain explicitly OPEN')
        print('PASS: #54 pre-partition confirmation record and provenance are internally consistent')
        print('Historical scope: later #35 partition reconciliation and #37 panel regeneration supersede live-input hashes')
        return

    from design.spec.instrument import specification
    from scripts.schgen.audit_master import EXPECTED_MODULES

    require(snapshot_hashes == {path: sha256(path) for path in SNAPSHOT_FILES},
            'pre-partition live inputs changed; use the later #35/#37 regeneration and board gates')
    native_path = export_native_netlist()
    native_sha = canonical_netlist_sha256(native_path)
    require(snapshot.get('native_netlist_sha256') == native_sha, 'native master netlist changed; rerun all master integration gates')
    require(snapshot.get('kicad_version') == '10.0.6', 'native oracle version must be KiCad 10.0.6')

    families, instances = specification()
    module_names = {i.name for i in instances} & EXPECTED_MODULES
    require(len(EXPECTED_MODULES) == 33 and module_names == EXPECTED_MODULES,
            'selected source topology must retain the exact 33 signal modules')
    require(len([i for i in instances if i.name in EXPECTED_MODULES]) == 33,
            'signal-module count changed independently of power hierarchy')
    family_by_name = {family.name: family for family in families}
    power_families = {
        family.name for family in families
        if any(p.attributes.get('Role', '').startswith('power:') for p in family.parts)
    }
    power_names = sorted(i.name for i in instances if i.family in power_families)
    other_names = sorted(i.name for i in instances if i.name not in EXPECTED_MODULES and i.family not in power_families)
    master = read_json('design/reports/master-audit.json')
    stats = read_json('design/reports/netlist-stats.json')
    require(master['instance_count'] == len(instances), 'master hierarchy count is not source-derived')
    require(master['module_count'] == 33 and master['module_instances'] == sorted(EXPECTED_MODULES),
            'master report does not retain the independent 33-module invariant')
    require(master['power_instances'] == power_names and master['power_instance_count'] == len(power_names),
            'master report power-sheet count differs from selected source topology')
    require(master['other_instance_count'] == len(other_names), 'master report non-module hierarchy count drift')
    require(master['panel_uid_count'] == 438, 'master panel UID count drift')
    require(stats['instance_count'] == len(instances) and stats['module_instance_count'] == 33,
            'netlist statistics hierarchy/module count drift')
    require(stats['power_instance_count'] == len(power_names) and stats['other_instance_count'] == len(other_names),
            'netlist statistics source-defined power hierarchy drift')
    require(stats['panel_part_count'] == 438 and stats['component_count'] == 5752,
            'master component or fixed panel package count drift')
    require(master['designator_count'] == 5758 and stats['multi_unit_package_count'] > 0,
            'unique designator/package-unit accounting drift')
    erc_baseline = read_json('design/reports/master-erc-warning-baseline.json')
    require(erc_baseline['warning_count'] == 228 and erc_baseline['kicad_version'] == '10.0.6',
            'documented native ERC warning baseline changed')
    erc_inventory_digest = hashlib.sha256(json.dumps(
        erc_baseline['warnings'], sort_keys=True, separators=(',', ':')
    ).encode()).hexdigest()
    require(erc_baseline['warning_inventory_sha256'] == erc_inventory_digest,
            'ERC warning baseline inventory checksum is invalid')
    require(sum(erc_baseline['warnings_by_sheet'].values()) == 228 and
            all(item['severity'] == 'warning' and item['type'] == 'pin_to_pin'
                for item in erc_baseline['warnings']),
            'ERC baseline warning identity inventory is incomplete or contains another class')
    require(report['captured_master']['erc_warning_inventory_sha256'] == erc_baseline['warning_inventory_sha256'] and
            report['captured_master']['erc_warnings_by_sheet'] == erc_baseline['warnings_by_sheet'],
            'report ERC warning identities differ from the pinned baseline')

    lock = read_json('design/grid/placements.lock.json')
    placements = lock['placements']
    require(len(placements) == 438 and report['fixed_hardware']['uid_xy_sha256'] ==
            read_json('design/power/supply-architecture-input.json')['fixed_uid_xy_sha256'],
            'fixed UID/x/y lock drift')
    jack_parts = [
        (instance.name, part)
        for instance in instances if instance.name in EXPECTED_MODULES
        for part in family_by_name[instance.family].parts
        if part.prefix == 'J' and part.attributes.get('PanelUid')
    ]
    require(len(jack_parts) == 180 and all(part.pins.get('S') == 'AGND' for _, part in jack_parts),
            'all 180 panel jack sleeves must remain on common AGND')
    precision_outputs = check_precision_islands(families, instances, EXPECTED_MODULES)

    sensitive_violations = []
    for net in master['sensitive_nets']:
        members = net['members']
        require(bool(members), f"sensitive net has no members: {net['net']}")
        require(all(member['island'] for member in members), f"sensitive member lacks an island: {net['net']}")
        if len(net['islands']) > 1 and any(member['panel_uid'] for member in members):
            sensitive_violations.append(net['net'])
    require(not sensitive_violations, 'panel-connected sensitive net crosses islands: ' + ', '.join(sensitive_violations))
    require(report['captured_master']['sensitive_island_audit']['precision_feedback_and_compensation_outputs'] == precision_outputs,
            'precision output island count drift')

    source = read_json('design/power/supply-architecture-input.json')
    source_domain = report['selected_source']
    domain = source['domains']
    require(source['decision'] == 'EXTERNAL_REGULATED_SOURCE_REQUIREMENT' and set(domain) == {'EXT'},
            'selected topology must remain one EXT requirement-only source domain')
    require(source_domain['domain'] == 'EXT' and source_domain['signal_modules'] == 33,
            'report domain/module scope drift')
    require(source_domain['domain_instances'] == domain['EXT']['module_instances'], 'EXT module/reference roster drift')
    require(source['physical_source']['status'] == 'NOT SELECTED', 'physical source must remain unselected')
    require(source_domain['physical_source_status'] == 'NOT SELECTED', 'report must not select physical source')
    require(source_domain['measured_source_capacity_mA'] == {rail: None for rail in ('+12V', '-12V', '+5V')},
            'unknown source capacity must remain null')
    req = source['source_requirement']
    require(source_domain['continuous_required_mA'] == { '+12V': 1600, '-12V': 1500, '+5V': 300 },
            'continuous source requirement changed')
    require(source_domain['transient_required_mA'] == { '+12V': 1900, '-12V': 1800, '+5V': 400 },
            'transient source requirement changed')
    require(source_domain['maximum_delivered_current_mA'] == req['maximum_delivered_current_mA'],
            'maximum delivered current contract drift')
    require(source_domain['worst_single_return_contact_A'] == 4.4 and
            source_domain['max_conductor_path_ohm'] == 0.02,
            'return contract drift')
    require(source_domain['return_sharing'] == 'NOT ASSUMED; any one AGND contact may carry the full summed rail transient',
            'report must not assume equal return sharing')
    inlet = source['inlet']
    require(source_domain['inlet_reservation']['reservation_xyz_mm'] == inlet['reservation_xyz_mm'],
            'requirement-only inlet reservation drift')
    require(source_domain['inlet_reservation']['harness_max_length_mm'] == inlet['harness']['max_length_mm'] == 300,
            'external harness requirement drift')
    require(source['returns']['topology'].startswith('Single EXT source common return bonded to instrument AGND star'),
            'return topology drift')
    require(source_domain['rejected_internal_source_pockets'] == 'Three P+B candidate pockets are not part of selected EXT topology',
            'report must keep rejected P+B pockets outside selected topology')

    supply = read_json('design/power/supply-architecture.json')
    implementation = supply['implementation']
    require(supply['status'].startswith('PASS: conditional requirement arithmetic/allocation ONLY'),
            'supply architecture is not a conditional requirement-only pass')
    require(implementation['patch_sleeves_on_agnd'] == 180 and implementation['abstract_parts_have_no_footprint_or_bom'],
            'supply implementation boundary/count drift')
    ledger = read_json('design/power/rail-ledger.json')
    selected = ledger['selected_domain']
    require(selected['id'] == 'EXT' and selected['module_count'] == 33 and selected['shared_reference_count'] == 1,
            'rail ledger selected EXT topology/count drift')
    require(selected['worksheet_load_count'] == 347 and selected['physical_ic_package_count'] == 634,
            'rail ledger whole-package/load count drift')
    require(ledger['measured_source_capacity_mA'] == {rail: None for rail in ('+12V', '-12V', '+5V')},
            'rail ledger must retain unknown measured source capacity')
    bulk = implementation['actual_fitted_capacitor_inventory']
    expected_bulk = {'+12V': 48.3, '-12V': 41.1, '+5V': 24.5}
    require({rail: bulk[rail]['captured_fitted_nominal_uF'] for rail in expected_bulk} == expected_bulk,
            'captured fitted capacitance inventory drift')
    require(all(bulk[rail]['initial_bulk_uF_per_powered_board'] == 4.7 and
                'OPEN' in bulk[rail]['board_bulk_status'] for rail in expected_bulk),
            '4.7 uF per-board/rail reservation must remain OPEN pending board-count reconciliation')
    cap_report = report['rail_and_capacitance_contract']
    require(cap_report['initial_bulk_uF_per_powered_board_per_rail'] == 4.7 and
            cap_report['fitted_nominal_uF_by_rail'] == expected_bulk,
            'report bulk reservation/capacitance arithmetic drift')
    require(cap_report['powered_board_count'] is None and cap_report['aggregate_board_bulk_status'] == 'OPEN',
            'unknown board count must not become an arithmetic margin pass')

    boundary = read_json('design/reports/power-boundary.json')
    require(boundary['status'].endswith('requirement-only boundary remains UNIMPLEMENTED'),
            'power-boundary status must keep implementation explicitly open')
    require(boundary['protection_implemented'] is False and boundary['energization_authorized'] is False,
            'abstract boundary was promoted to protection or energization')
    require(boundary['orderable_footprint'] is None and boundary['bom_entry'] is False,
            'CN301/XB301 must remain non-orderable and excluded from BOM')
    require(set(boundary['raw_net_nodes']) == {'+12V_IN', '-12V_IN', '+5V_IN'} and
            set(boundary['load_rail_boundary_nodes']) == {'+12V', '-12V', '+5V'},
            'raw/load rail boundaries drift')
    require(report['protection_boundary']['captured_implementation']['status'] ==
            'PASS - abstract native pins and raw/load separation only',
            'captured power-boundary gate status drift')
    require(report['protection_boundary']['circuit_evidence']['status'] == 'OPEN' and
            report['protection_boundary']['circuit_evidence']['follow_up'].endswith('/issues/59'),
            'exact protection circuit evidence must remain OPEN under #59')
    require(report['protection_boundary']['physical_qualification']['status'] == 'NOT RUN' and
            report['protection_boundary']['physical_qualification']['follow_up'].endswith('/issues/57'),
            'physical power qualification must remain NOT RUN under #57')
    protection = read_json('design/power/protection58-audit.json')
    require(protection['output_count'] == 82 and protection['precision_count'] == 16 and
            len(protection['reference_receivers']) == 30, 'protection obligation path counts drift')
    candidate = report['protection_boundary']['open_partition_reservation']
    require(candidate['output_paths'] == 82 and candidate['precision_sense_paths'] == 16 and
            candidate['octave_reference_receivers'] == 30 and
            candidate['candidate_switch_channels'] == 98,
            'protection boundary/reservation path counts drift')
    require(candidate['candidate_local_quad_packages'] == 35 and
            candidate['candidate_positive_Iq_sensitivity_mA'] == 45.5 and
            candidate['positive_auxiliary_allocation_mA'] == 20,
            'candidate package/current sensitivity drift')
    require(candidate['candidate_local_feedback_capacitance_nF'] == 10 and
            candidate['switch_capacitance_sensitivity_pF'] == 24 and
            candidate['allocation_status'] == 'OPEN PARTITION RESERVATION; no fitted zero-area device or proved clearance',
            'candidate capacitance/geometry reservation was promoted')
    require(report['protection_boundary']['overall_protection_status'] ==
            'OPEN - circuit evidence #59; physical qualification #57 NOT RUN',
            'do not collapse protection contract, implementation, and physical status')

    selector = read_json('design/mechanical/selector-assembly.json')
    selector_check = read_json('design/mechanical/selector-assembly-check.json')
    selector_report = report['selected_selector']
    require(selector_report['manufacturer'] == 'Alps Alpine' and selector_report['mpn'] == 'SRBV160803',
            'selector identity drift')
    require(selector_check['status'] == 'CONDITIONAL UNVALIDATED DRAFT' and selector_check['fixed_features'] == 438 and
            selector_check['fixed_modules'] == 33, 'selector fixed-scope report drift')
    require(selector_check['inter_selector_keepout_intersections'] == [] and
            selector_check['drc']['front'] == {} and selector_check['drc']['rear'] == {} and
            selector_check['drc']['panel'] == {}, 'selector known deterministic geometry/DRC conflict')
    require(selector['physical_qualification_issue'].endswith('/issues/55') and
            selector_report['physical_qualification']['status'] == 'NOT RUN',
            'selector physical coupon must remain NOT RUN under #55')
    require(len(selector['instances']) == 5 and selector_report['front_adapter_count'] == 3 and
            selector_report['rear_adapter_count'] == 2, 'selector five-up reservation drift')

    command_results = report.get('command_results', [])
    ids = {item['id']: item for item in command_results}
    for required_id in ('pre_edit_circuit_check', 'baseline_regeneration', 'pnpm_check',
                        'post_edit_circuit_check', 'master_erc_netlist', 'regen_twice',
                        'selector_fixture', 'dense_fixture', 'focused_tests',
                        'abstract_filter_tests', 'protection_draft_gate', 'protection_closed_gate'):
        require(required_id in ids, f'missing required command evidence: {required_id}')
    for command_id in ('pre_edit_circuit_check', 'baseline_regeneration', 'pnpm_check',
                       'post_edit_circuit_check', 'master_erc_netlist', 'regen_twice',
                       'selector_fixture', 'dense_fixture', 'focused_tests',
                       'abstract_filter_tests', 'protection_draft_gate'):
        require(ids[command_id]['status'] == 'PASS' and ids[command_id]['exit_code'] == 0,
                f'required gate is not passing: {command_id}')
    require(ids['protection_closed_gate']['status'] == 'OPEN (EXPECTED)' and
            ids['protection_closed_gate']['exit_code'] == 1,
            'the #59 implementation gate must remain explicitly OPEN')
    require(ids['master_erc_netlist']['documented_warning_count'] == 228 and
            ids['dense_fixture']['rule_errors'] == ids['dense_fixture']['unconnected_items'] ==
            ids['dense_fixture']['parity_issues'] == 0 and ids['dense_fixture']['rule_warnings'] == 159,
            'native ERC/dense warning and error breakdown changed')
    require(report['selected_source']['physical_qualification']['status'] == 'NOT RUN' and
            report['selected_source']['physical_qualification']['follow_up'].endswith('/issues/57'),
            'source/cable physical checks must remain NOT RUN under #57')
    require(report['selected_selector']['physical_qualification']['follow_up'].endswith('/issues/55'),
            'selector fit follow-up must remain #55')
    require(report['visual_review']['status'] == 'RENDERED AND INSPECTED; NOT DIMENSIONAL OR PHYSICAL PROOF',
            'visual status must retain its limits')

    verifier = subprocess.run(
        ['python3', 'scripts/schgen/verify_netlist.py', native_path.relative_to(ROOT).as_posix()],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    require(verifier.returncode == 0, 'native source/netlist parity rerun failed: ' + verifier.stdout + verifier.stderr)
    master_audit = subprocess.run(
        ['python3', 'scripts/schgen/audit_master.py', native_path.relative_to(ROOT).as_posix(), '--check'],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    require(master_audit.returncode == 0, 'source-defined master audit rerun failed: ' + master_audit.stdout + master_audit.stderr)
    print('PASS: #54 pre-partition report matches the current source, native netlist, fixed hardware, EXT/rail contract, selector reservation, and open protection boundary')
    print('Scope: 33 signal modules; source-defined hierarchy; 438 locked centres; 180 AGND sleeves; 634 fitted IC packages; 347 worksheet loads')
    print('Status boundary: #59 circuit OPEN; #55/#57 physical qualification NOT RUN; dense fixture 0 errors / 159 silk warnings')


if __name__ == '__main__':
    try:
        if len(sys.argv) > 2 or (len(sys.argv) == 2 and sys.argv[1] != '--capture-check'):
            raise ValueError('usage: python3 scripts/checks/prepartition54.py [--capture-check]')
        check_report(capture_check=len(sys.argv) == 2)
    except (KeyError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        raise SystemExit(1)
