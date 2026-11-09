"""Regression checks for audit omissions and false promotion of the open gate."""
import copy
from dataclasses import replace
import json
import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from scripts.checks import protection58 as audit


class ProtectionAuditTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((audit.ROOT / 'design/power/supply-architecture-input.json').read_text())

    def test_extra_source_domain_rejected(self):
        self.contract['domains']['SECOND'] = copy.deepcopy(self.contract['domains']['EXT'])
        with self.assertRaisesRegex(ValueError, 'one EXT'):
            audit.build(self.contract)

    def test_loss_budget_follows_declared_continuous_contract(self):
        report = audit.build(self.contract)
        self.assertEqual({r: v['continuous_A'] for r, v in report['loss_calculations'].items()},
                         {'+12V': 1.6, '-12V': 1.6, '+5V': .3})
        self.assertEqual({r: v['maximum_delivered_A'] for r, v in report['loss_calculations'].items()},
                         {'+12V': 2.1, '-12V': 2.0, '+5V': .5})
        self.assertAlmostEqual(report['loss_calculations']['+12V']['legacy_ptc_drop_V'], .4)
        # A future declared requirement must reach the audit instead of another
        # hardcoded map. The supply generator separately rejects ledger mismatch.
        self.contract['source_requirement']['minimum_continuous_current_mA']['+12V'] = 1800
        changed = audit.build(self.contract)['loss_calculations']['+12V']
        self.assertEqual(changed['continuous_A'], 1.8)
        self.assertAlmostEqual(changed['resistance_budget_ohm_at_continuous'], .04 / 1.8)

    def test_missing_continuous_requirement_and_weakened_drop_rejected(self):
        del self.contract['source_requirement']['minimum_continuous_current_mA']
        with self.assertRaisesRegex(ValueError, 'declared continuous'):
            audit.build(self.contract)
        self.contract = json.loads((audit.ROOT / 'design/power/supply-architecture-input.json').read_text())
        self.contract['inlet']['harness']['max_protection_drop_V'] = .05
        with self.assertRaisesRegex(ValueError, '40 mV'):
            audit.build(self.contract)

    def test_current_population_separates_adopted_identities_and_historical_screen(self):
        report = audit.build(self.contract)
        population = report['current_switch_population']
        groups = {g['mpn']: g for g in population['groups']}
        self.assertEqual({mpn: g['count'] for mpn, g in groups.items()},
                         {'TMUX7412FRRPR': 98, 'TMUX6112PWR': 12})
        self.assertEqual(population['package_count'], 110)
        bindings = population['input_sha256']
        for path in ('design/standard/parts-shortlist.json', 'design/grid/placements.lock.json',
                     'scripts/schgen/core.py', 'scripts/libgen/build_symbol_lib.py',
                     'symbols/src/TMUX7412FRRPR.kicad_sym', 'symbols/src/TMUX6112PWR.kicad_sym'):
            self.assertEqual(bindings[path], hashlib.sha256((audit.ROOT / path).read_bytes()).hexdigest())
        self.assertEqual(len({r for g in groups.values() for r in g['refs']}), 110)
        self.assertEqual(groups['TMUX7412FRRPR']['current_evidence']['conditioned_125C_table_population_mA'],
                         {'+12V': 58.8, '-12V': 49.0})
        self.assertEqual(groups['TMUX6112PWR']['current_evidence']['conditioned_125C_table_population_mA'],
                         {'+12V': .276, '-12V': .144})
        self.assertIsNone(population['guaranteed_project_total_mA'])
        self.assertTrue(all(g['guaranteed_project_current_mA'] is None for g in groups.values()))
        candidate = report['historical_candidate_switch_sensitivity']
        self.assertEqual(candidate['assumed_pre_S2b_ADG_package_count'], 110)
        self.assertEqual(candidate['current_ADG_package_count'], 0)
        self.assertEqual(candidate['new_module_and_receiver_local_quads'], 45)
        self.assertEqual(candidate['replace_existing_and_add_count'], 155)
        self.assertEqual(candidate['delta_to_existing_ADG_planning_mA'], {'+12V': -50.0, '-12V': .5})
        self.assertIn('HISTORICAL', candidate['status'])
        self.assertEqual(candidate['project_verdict'], 'UNSOURCED')
        self.assertIsNone(report['selected_topology'])
        self.assertTrue(report['open_gates'])
        self.assertGreater(report['prospective_each_499ohm_dissipation_W'], .30)

    def test_current_screen_rejects_unsupported_values_and_units(self):
        fact = {'unit': 'uA per package', 'value': {'IDD_max_125C': 23, 'ISS_max_125C': 12}}
        self.assertEqual(audit.conditioned_current(fact, 3), {'+12V': .069, '-12V': .036})
        for value in (None, True, -1, float('nan'), float('inf'), '23'):
            changed = copy.deepcopy(fact)
            changed['value']['IDD_max_125C'] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Unsupported switch current value'):
                audit.conditioned_current(changed, 3)
        fact['unit'] = 'A'
        with self.assertRaisesRegex(ValueError, 'Unsupported switch current unit'):
            audit.conditioned_current(fact, 3)

    def test_package_unit_identity_mismatch_rejected(self):
        families, instances = audit.specification()
        family_map = {f.name: f for f in families}
        name = next(n for n, f in family_map.items()
                    if any(p.attributes.get('MPN') == 'TMUX7412FRRPR' for p in f.parts))
        family = family_map[name]
        index = next(i for i, p in enumerate(family.parts) if p.attributes.get('MPN') == 'TMUX7412FRRPR')
        parts = list(family.parts)
        parts[index] = replace(parts[index], attributes={**parts[index].attributes, 'MPN': 'ADG5412FBRUZ'})
        family_map[name] = replace(family, parts=tuple(parts))
        with self.assertRaisesRegex(ValueError, 'symbol/MPN mismatch'):
            audit.switch_population(family_map, instances)

    def test_dnp_units_do_not_create_fitted_packages(self):
        families, instances = audit.specification()
        changed = {f.name: replace(f, parts=tuple(replace(p, dnp=True)
                   if p.attributes.get('MPN') == 'TMUX6112PWR' else p for p in f.parts))
                   for f in families}
        population = audit.switch_population(changed, instances)
        self.assertEqual(population['package_count'], 98)
        self.assertEqual([g['mpn'] for g in population['groups']], ['TMUX7412FRRPR'])
        self.assertIsNone(population['guaranteed_project_total_mA'])

    def test_candidate_selection_and_broken_source_receipt_rejected(self):
        original = json.loads((audit.ROOT / 'design/power/protection59-sources.json').read_text())
        mutations = [
            (lambda r: r.update(protection_implemented=True), 'implemented protection'),
            (lambda r: r['sources'][0].update(selection='SELECTED'), 'select or install'),
            (lambda r: r['sources'][0].update(sha256='0' * 64), 'Invalid candidate source hash'),
            (lambda r: r['sources'][-1].update(sha256='a' * 64), 'cannot claim retained bytes'),
            (lambda r: r['sources'][0]['normal_iq_screen'].update(project_verdict='PASS'), 'current screen'),
            (lambda r: r['sources'][0]['normal_iq_screen'].update(positive_mA=-.6), 'current screen'),
        ]
        for mutate, message in mutations:
            with self.subTest(message=message):
                changed = copy.deepcopy(original)
                mutate(changed)
                with self.assertRaisesRegex(ValueError, message):
                    audit.check_candidate_research(changed)

    def test_optional_cache_absence_is_reported_but_present_corruption_rejected(self):
        research = json.loads((audit.ROOT / 'design/power/protection59-sources.json').read_text())
        research['sources'] = [research['sources'][0]]
        source = research['sources'][0]
        source['file'] = 'candidate.pdf'
        original = b'%PDF-1.7\nTest-only hash fixture, not manufacturer evidence.\n'
        source['sha256'] = hashlib.sha256(original).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.assertEqual(audit.check_candidate_research(research, root), ['TMUX7412FRRPR'])
            (root / source['file']).write_bytes(original)
            self.assertEqual(audit.check_candidate_research(research, root), [])
            (root / source['file']).write_bytes(original + b'changed')
            with self.assertRaisesRegex(ValueError, 'Source bytes changed'):
                audit.check_candidate_research(research, root)

    def test_regulated_net_rebinding_rejected(self):
        self.contract['domains']['EXT']['regulated_nets']['-12V'] = '+12V'
        with self.assertRaisesRegex(ValueError, 'net separation'):
            audit.build(self.contract)

    def test_output_omission_rejected(self):
        families, instances = audit.specification()
        mutated = tuple(replace(f, parts=tuple(p for p in f.parts if p.attributes.get('Role') != 'precision_output:R_ISO_B')) if f.name == 'mult' else f for f in families)
        with patch.object(audit, 'specification', return_value=(mutated, instances)):
            with self.assertRaisesRegex(ValueError, 'every locked output'):
                audit.build(self.contract)

    def test_requirement_gate_fails_despite_consistent_report(self):
        result = subprocess.run(['python3', 'scripts/checks/protection58.py', '--check', '--require-closed'], cwd=audit.ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('BLOCKED: exact protection implementation gate', result.stdout)

    def test_draft_cannot_be_promoted_to_orderable_or_energizable(self):
        draft = json.loads((audit.ROOT / 'design/power/protection58-draft-contract.json').read_text())
        for field in ('orderable', 'energization_authorized', 'protection_implemented'):
            changed = copy.deepcopy(draft)
            changed[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, 'False hardware promotion'):
                audit.draft_contract_check(changed)

    def test_conditional_draft_can_pass_while_implementation_stays_open(self):
        result = subprocess.run(['python3', 'scripts/checks/protection58.py', '--check', '--require-draft'], cwd=audit.ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('NON-ORDERABLE / NOT-ENERGIZABLE', result.stdout)
        self.assertIn('BLOCKED: exact protection implementation gate', result.stdout)


if __name__ == '__main__':
    unittest.main()
