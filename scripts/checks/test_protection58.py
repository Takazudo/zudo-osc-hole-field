"""Regression checks for audit omissions and false promotion of the open gate."""
import copy
from dataclasses import replace
import json
import subprocess
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
