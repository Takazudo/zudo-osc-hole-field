"""Verify local fixtures restore the caller's exact environment, including failures."""
import os
import unittest
from unittest.mock import patch

import test_native_validation as fixtures


class LocalFixtureEnvironmentTests(unittest.TestCase):
    def run_local_suite(self, contaminated):
        local = fixtures.nv.local_admission()
        keys = (*local.CI_KEYS, *local.AUTHORITY_KEYS)
        env = {k: v for k, v in os.environ.items() if k not in keys}
        if contaminated:
            env.update({key: 'inherited-parent-' + key for key in keys})
            env['EPIC242_LOCAL_REQUEST'] = ''  # Distinguish empty from absent.
        with patch.dict(os.environ, env, clear=True):
            before = dict(os.environ)
            suite = unittest.defaultTestLoader.loadTestsFromTestCase(fixtures.LocalStagingTests)
            expected = suite.countTestCases()
            result = unittest.TestResult()
            suite.run(result)
            self.assertEqual(dict(os.environ), before)
            self.assertEqual(result.testsRun, expected)
            self.assertTrue(result.wasSuccessful(), result.errors + result.failures)

    def test_clean_parent_environment_is_restored(self):
        self.run_local_suite(False)

    def test_ci_contaminated_parent_environment_is_restored(self):
        self.run_local_suite(True)

    def test_later_setup_failure_restores_authority(self):
        case = fixtures.LocalStagingTests('test_local_preparation_all_targets_without_approval_or_github_identity')
        with patch.dict(os.environ, {'GITHUB_RUN_ID': 'parent-run', 'EPIC242_LOCAL_REQUEST': ''}), \
                patch.object(fixtures.nv, 'prepare', side_effect=RuntimeError('injected setup failure')):
            before = dict(os.environ)
            result = unittest.TestResult()
            try:
                case.run(result)
                self.assertEqual(dict(os.environ), before)
                self.assertEqual(len(result.errors), 1)
                self.assertIn('injected setup failure', result.errors[0][1])
            finally:
                if hasattr(case, 'tmp'):
                    case.tmp.cleanup()
