"""The live bridge must reject real obligation/input drift, not hide it in history."""
import copy
import hashlib
import json
import unittest
import subprocess
import os
import sys
import tempfile
from unittest.mock import patch
from scripts.checks import protection_study_applicability as bridge


class ProtectionStudyApplicability(unittest.TestCase):
    def test_direct_script_runs_without_pythonpath_from_another_directory(self):
        environment = dict(os.environ)
        environment.pop('PYTHONPATH', None)
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(bridge.ROOT / 'scripts/checks/protection_study_applicability.py')],
                cwd=directory, env=environment, text=True, capture_output=True, check=True)
        self.assertEqual(json.loads(result.stdout)['hardware_protection'],
                         'OPEN; physical qualification NOT RUN')

    def test_live_inputs_and_all_arithmetic_match_the_retained_study_scope(self):
        self.assertIn('historical ADG savings are not current', bridge.verify()['status'])

    def test_same_count_but_different_output_identity_is_rejected(self):
        before = json.loads(bridge.historical(bridge.AUDIT))
        after = copy.deepcopy(before)
        after['outputs'][0]['uid'] = 'unreviewed-output'
        with self.assertRaisesRegex(ValueError, 'obligation changed: outputs'):
            bridge.projection_matches(before, after)

    def test_changed_reference_connection_is_rejected(self):
        before = json.loads(bridge.historical(bridge.AUDIT))
        after = copy.deepcopy(before)
        after['reference_receivers'][0]['net'] = 'unreviewed-net'
        with self.assertRaisesRegex(ValueError, 'obligation changed: reference_receivers'):
            bridge.projection_matches(before, after)

    def test_changed_non_audit_input_is_not_exempted(self):
        raw = b'original'
        report = {'input_sha256': {'scripts/checks/precision_output_cell.py': hashlib.sha256(raw).hexdigest()}}
        with self.assertRaisesRegex(ValueError, 'Current study input changed'):
            bridge.verify_bound_inputs(report, lambda _: b'changed', lambda _: raw)
        with self.assertRaisesRegex(ValueError, 'Historical input binding mismatch'):
            bridge.verify_bound_inputs(report, lambda _: raw, lambda _: b'changed')

    def test_unavailable_history_fails_without_current_tree_fallback(self):
        with patch.object(bridge.subprocess, 'check_output',
                          side_effect=subprocess.CalledProcessError(128, ['git', 'show'])):
            with self.assertRaises(subprocess.CalledProcessError):
                bridge.historical('missing-study-input')


if __name__ == '__main__':
    unittest.main()
