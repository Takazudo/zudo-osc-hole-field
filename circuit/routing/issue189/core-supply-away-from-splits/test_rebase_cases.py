"""Whole-case exclusion and unknown/partial accepted-copper regression checks."""
import copy
import importlib.util
import json
import unittest
from pathlib import Path
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('supply_rebase', HERE / 'rebase_proposal.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class RebaseCasesTests(unittest.TestCase):
    def setUp(self):
        self.proposal = json.loads((HERE / 'proposal-original.json').read_text())
        self.selection = json.loads((HERE / 'selection.json').read_text())['selected']
        self.ground = json.loads((HERE.parent / 'core-finer-ground-batch/proposal.json').read_text())['copper']

    def test_unchanged_core_keeps_all_cases(self):
        rows, kept, excluded = module.select_whole_cases(self.proposal, self.selection, [])
        self.assertEqual((len(rows), len(kept), len(excluded)), (120, 94, 0))
        self.assertEqual(module.retained_known_additions([], [self.ground]), [])

    def test_ground_conflict_excludes_whole_u4439_case(self):
        rows, kept, excluded = module.select_whole_cases(self.proposal, self.selection, self.ground)
        self.assertEqual((len(rows), len(kept), len(excluded)), (118, 93, 1))
        self.assertEqual(excluded[0]['pads'], ['U4439.4'])
        self.assertEqual(len(excluded[0]['uuids']), 2)
        self.assertFalse(set(excluded[0]['uuids']) & {r['uuid'] for r in rows})

    def test_partial_accepted_ground_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'partial known'):
            module.retained_known_additions([{'uuid': self.ground[0]['uuid']}], [self.ground])

    def test_unknown_accepted_copper_is_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'unknown accepted'):
            module.retained_known_additions([{'uuid': 'unknown'}], [self.ground])

    def test_missing_case_membership_is_rejected(self):
        with self.assertRaises(AssertionError):
            module.select_whole_cases(self.proposal, self.selection[1:], [])

if __name__ == '__main__':
    unittest.main()
