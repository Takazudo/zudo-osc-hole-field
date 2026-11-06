"""Reject supply-cleanup receipts that escape the reviewed exact occurrence set."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('full_b1_retirement', ROOT / 'design/architecture-278/implementation/stage42/full-b1/retirement_guard.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class FullB1Retirement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / 'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_text()
        cls.proof = json.loads(m.PROOF.read_text())
        cls.receipt = {'retired_private_copper': [],
                       'retired_stage42_supply_copper': cls.proof['screened_retirements'],
                       'supply_contact_proof_sha256': m.digest(m.PROOF.read_text())}

    def test_exact_reviewed_rows(self):
        self.assertEqual(len(m.bound_retirements(self.receipt, self.raw)), 21)
        self.assertTrue(all(not b['current_pad_contacts'] for b in self.proof['branches']))

    def test_missing_extra_or_edited_row(self):
        for change in ('missing', 'extra', 'edited'):
            receipt = copy.deepcopy(self.receipt)
            rows = receipt['retired_stage42_supply_copper']
            if change == 'missing': rows.pop()
            elif change == 'extra': rows.append(copy.deepcopy(rows[0]))
            else: rows[0]['net'] = 'AGND'
            with self.assertRaises(ValueError): m.bound_retirements(receipt, self.raw)

    def test_wrong_proof_or_baseline(self):
        receipt = copy.deepcopy(self.receipt); receipt['supply_contact_proof_sha256'] = '0' * 64
        with self.assertRaises(ValueError): m.bound_retirements(receipt, self.raw)
        with self.assertRaises(ValueError): m.bound_retirements(self.receipt, self.raw + '\n')

    def test_stage41_retirement_cannot_double_count(self):
        receipt = copy.deepcopy(self.receipt); receipt['retired_local_supply_copper'] = [receipt['retired_stage42_supply_copper'][0]]
        with self.assertRaises(ValueError): m.bound_retirements(receipt, self.raw)

    def test_private_retirement_duplicate_rejected(self):
        receipt = copy.deepcopy(self.receipt); receipt['retired_private_copper'] = [receipt['retired_stage42_supply_copper'][0]]
        with self.assertRaises(ValueError): m.bound_retirements(receipt, self.raw)
