"""Oracle selection must fail closed before executing any discovered case."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'source_only_selector', Path(__file__).with_name('run-source-only-python.py'))
selector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(selector)


class SourceOnlySelectionTests(unittest.TestCase):
    def select(self, root, identities):
        executed = []

        class Case(unittest.TestCase):
            def __init__(self, identity):
                super().__init__('runTest')
                self.identity = identity

            def id(self):
                return self.identity

            def runTest(self):
                executed.append(self.identity)
                self.assertNotIn(selector.ORACLE, self.identity)
                self.assertNotEqual(self.identity, 'source.failure')

        suite = unittest.TestSuite([unittest.TestSuite([Case(i) for i in identities])])
        with patch.object(sys, 'argv', ['selector', root]), \
                patch.object(selector.unittest, 'TestLoader') as loader, \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            loader.return_value.discover.return_value = suite
            code = selector.main()
        return code, executed

    def test_both_exact_discovery_identities_exclude_only_oracle(self):
        for root, prefix in [('design/spec', 'cells.'), ('design/spec/cells', '')]:
            with self.subTest(root=root):
                self.assertEqual(self.select(root, [prefix + selector.ORACLE, 'source.safe']),
                                 (0, ['source.safe']))

    def test_missing_oracle_refuses_all_execution(self):
        self.assertEqual(self.select('design/spec', ['source.safe']), (2, []))

    def test_duplicate_oracle_refuses_all_execution(self):
        self.assertEqual(self.select('design/spec/cells',
                         ['source.safe', selector.ORACLE, selector.ORACLE]), (2, []))

    def test_unexpected_prefix_refuses_all_execution(self):
        self.assertEqual(self.select('design/spec', ['source.safe', 'other.' + selector.ORACLE]),
                         (2, []))

    def test_oracle_in_unexpected_root_refuses_all_execution(self):
        self.assertEqual(self.select('scripts/checks', ['source.safe', selector.ORACLE]), (2, []))

    def test_unrelated_root_runs_nested_source_cases(self):
        self.assertEqual(self.select('scripts/checks', ['source.safe']), (0, ['source.safe']))

    def test_selected_failure_is_not_hidden(self):
        self.assertEqual(self.select('scripts/checks', ['source.failure']), (1, ['source.failure']))

    def test_neighbor_runs_without_vendor_model_setup(self):
        from design.spec.cells import test_sweep_precision_vendor as vendor
        case = vendor.PrecisionVendorSweepGate('test_unrounded_thresholds_are_strict')
        with patch.object(vendor, 'model', side_effect=AssertionError('native model forbidden')) as model:
            result = unittest.TestResult()
            unittest.TestSuite([case]).run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertTrue(result.wasSuccessful(), result.errors + result.failures)
        model.assert_not_called()
