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
                         {'+12V': 1.7, '-12V': 1.6, '+5V': .3})
        self.assertEqual({r: v['maximum_delivered_A'] for r, v in report['loss_calculations'].items()},
                         {'+12V': 2.1, '-12V': 2.0, '+5V': .5})
        self.assertAlmostEqual(report['loss_calculations']['+12V']['legacy_ptc_drop_V'], .425)
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

    def test_candidate_sensitivity_does_not_book_reuse_or_close_gate(self):
        report = audit.build(self.contract)
        candidate = report['candidate_switch_sensitivity']
        self.assertEqual(candidate['existing_ADG_package_count'], 110)
        self.assertEqual(len(set(candidate['existing_ADG_package_refs'])), 110)
        self.assertEqual(candidate['new_module_and_receiver_local_quads'], 45)
        self.assertEqual(candidate['replace_existing_and_add_count'], 155)
        self.assertEqual(candidate['delta_to_existing_ADG_planning_mA'], {'+12V': -50.0, '-12V': .5})
        self.assertEqual(candidate['project_verdict'], 'UNSOURCED')
        self.assertIsNone(report['selected_topology'])
        self.assertTrue(report['open_gates'])
        self.assertGreater(report['prospective_each_499ohm_dissipation_W'], .30)

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
