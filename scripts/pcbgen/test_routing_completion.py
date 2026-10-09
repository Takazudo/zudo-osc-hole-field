"""Completion gate regressions, using synthetic data rather than a native run."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import check_routing_completion as completion
from scripts.pcbgen.check_routing_completion import zero_gate


class CompletionGateTests(unittest.TestCase):
    def setUp(self):
        self.dump = {'open_edges': 0, 'islands': {'AGND': [['a', 'b']]}}
        self.drc = {'violations': [], 'schematic_parity': [], 'unconnected_items': []}

    def gate(self, fresh=None, drc=None):
        return zero_gate(self.dump, fresh or self.dump, self.drc, drc or self.drc)

    def test_zero_with_identical_membership(self):
        self.assertTrue(self.gate()['passed'])

    def test_empty_cli_sample_cannot_hide_native_edges(self):
        self.dump.update(open_edges=1, islands={'AGND': [['a'], ['b']]})
        self.assertFalse(self.gate()['passed'])

    def test_false_zero_cannot_hide_separate_native_islands(self):
        self.dump['islands'] = {'AGND': [['a'], ['b']]}
        self.assertFalse(self.gate()['passed'])

    def test_equal_zero_counts_cannot_hide_membership_change(self):
        fresh = copy.deepcopy(self.dump)
        fresh['islands'] = {'AGND': [['a', 'c']]}
        self.assertFalse(self.gate(fresh=fresh)['passed'])

    def test_native_errors_and_parity_fail(self):
        for field, value in [('violations', [{'severity': 'error'}]), ('schematic_parity', [{}])]:
            drc = copy.deepcopy(self.drc)
            drc[field] = value
            self.assertFalse(self.gate(drc=drc)['passed'])

    def test_native_failure_invalidates_prior_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / '.circuit-cache/routing-completion.json'
            out.parent.mkdir()
            out.write_text('{"passed": true}')
            with patch.object(completion, 'ROOT', root), patch.object(completion, 'digest', side_effect=RuntimeError('native unavailable')):
                with self.assertRaisesRegex(RuntimeError, 'native unavailable'):
                    completion.main()
            receipt = json.loads(out.read_text())
            self.assertFalse(receipt['passed'])
            self.assertEqual(receipt['status'], 'NATIVE CHECK FAILED; NOT PASSED')


if __name__ == '__main__':
    unittest.main()
