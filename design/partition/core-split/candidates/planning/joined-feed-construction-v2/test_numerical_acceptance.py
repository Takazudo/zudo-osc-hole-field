"""Source-only accuracy-gate regressions; no production solve or native launch."""
import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from numerical_acceptance import assess

CONFIG = {'numerical_tolerances': {'kcl_relative': 1e-9, 'energy_relative': 1e-9,
           'reciprocity_relative': 1e-9},
          'return_states': {'single': [[4], [5], [6]], 'double': [[4, 5], [4, 6], [5, 6]]}}


class NumericalAcceptance(unittest.TestCase):
    def test_observed_production_failures_do_not_pass_on_exit_zero(self):
        for residual in (1.4499316030378085e-9, 1.227478631500586e-9):
            result = assess('reduce', {'checks': {'reciprocity_relative': 1e-14,
                'interface_solve_residual_relative': 5e-11,
                'load_solve_residual_relative': residual}}, CONFIG)
            self.assertEqual(result['status'], 'FAIL')
            self.assertEqual(len(result['failures']), 1)
            self.assertIn('load_solve_residual_relative', result['failures'][0])

    def test_boundary_and_missing_nonfinite_metrics_and_limits(self):
        self.assertFalse(assess('dpoint', {'solve_residual_relative': 1e-9}, CONFIG)['failures'])
        for value in (None, True, float('nan'), float('inf'), -1, 1.000001e-9):
            self.assertTrue(assess('dpoint', {'solve_residual_relative': value}, CONFIG)['failures'])
        for limit in (None, True, float('nan'), float('inf'), 0, -1):
            config = copy.deepcopy(CONFIG); config['numerical_tolerances']['kcl_relative'] = limit
            self.assertTrue(assess('dpoint', {'solve_residual_relative': 0}, config)['failures'])
        self.assertEqual(len(assess('reduce', {'checks': None}, CONFIG)['failures']), 3)

    def test_every_configured_coupled_state_is_required(self):
        checks = {'global_kcl_relative': 0, 'max_free_node_kcl_relative': 0,
                  'driving_point_solve_residual': 0, 'energy_minus_load_work_relative': 0,
                  'nonnegative_energy': True}
        states = {'all-present': checks}
        for group in ('single', 'double'):
            for removed in CONFIG['return_states'][group]:
                states['remove-' + '-'.join('W' + str(w) for w in removed)] = dict(checks)
        result = {'net': 'AGND', 'states': 7, 'checks': states}
        self.assertFalse(assess('couple', result, CONFIG)['failures'])
        missing = copy.deepcopy(result); missing['checks'].pop('remove-W4'); missing['states'] = 6
        self.assertTrue(assess('couple', missing, CONFIG)['failures'])
        for metric in checks:
            bad = copy.deepcopy(result); bad['checks']['remove-W4-W5'].pop(metric)
            self.assertTrue(assess('couple', bad, CONFIG)['failures'])
        bad = copy.deepcopy(result); bad['checks']['all-present']['nonnegative_energy'] = 1
        self.assertTrue(assess('couple', bad, CONFIG)['failures'])

    def test_cli_preserves_failed_payload_and_bound_verdict_then_exits(self):
        import finite_solve as solver
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); config = p/'config.json'; config.write_text(json.dumps(CONFIG)); output = p/'result.pkl.gz'
            def fixture(args):
                output.write_bytes(b'preserved failed unit payload')
                return {'solve_residual_relative': 1.5e-9}
            argv = ['dpoint', '--config', str(config), '--output', str(output), '--start', '0', '--stop', '1']
            for key in ('operator', 'coverage', 'cases', 'case', 'depth', 'board', 'net'):
                argv += ['--' + key, 'fixture']
            with patch.object(solver, 'dpoint', side_effect=fixture), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
                solver.main(argv)
            self.assertEqual(output.read_bytes(), b'preserved failed unit payload')
            verdict = json.loads(Path(str(output) + '.numerical.json').read_text())
            self.assertEqual(verdict['status'], 'FAIL')
            self.assertEqual(verdict['output_sha256'], solver.sha(output))
            self.assertEqual(verdict['config_sha256'], solver.sha(config))

    def test_driver_stops_before_any_driving_points_after_failed_reduction(self):
        import run_coupled_e16 as driver
        class FailedLedger:
            def __init__(self, *args): self.log = []
            def run(self, name, command, inputs, methods, outputs):
                calls.append(name)
                if 'reduce' in name: raise SystemExit('retained numerical failure')
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); config = p/'config.json'; config.write_text(json.dumps(CONFIG | {
                'scenario': {'id': 'fixture', 'ledger': 'fixture-ledger'}, 'default_depth_case': 'fixture'}))
            cases = p/'cases.json'; cases.write_text('{"cases": {"fixture": {}}}')
            argv = ['driver', '--python', sys.executable, '--finite', str(p/'finite'), '--output', str(p/'out'),
                    '--config', str(config), '--cases', str(cases), '--net=+12V']
            with patch.object(driver.rs, 'Ledger', FailedLedger), patch.object(sys, 'argv', argv), self.assertRaises(SystemExit):
                driver.main()
        self.assertEqual(len(calls), 2)
        self.assertIn('KA-reduce', calls[-1])

    def test_second_board_reduction_failure_precedes_all_driving_points(self):
        import run_coupled_e16 as driver
        calls = []
        class FailedKB:
            def __init__(self, out, *args):
                self.out = out; self.log = []; (out/'steps').mkdir()
            def run(self, name, command, inputs, methods, outputs):
                calls.append(name)
                if name.startswith('KB-reduce'): raise SystemExit('KB numerical failure')
                if name.startswith('KA-reduce'):
                    (self.out/'steps'/ (name + '.json')).write_text(json.dumps({'stdout_tail': '{"pads": 200}'}))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); config = p/'config.json'; config.write_text(json.dumps(CONFIG | {
                'scenario': {'id': 'fixture', 'ledger': 'fixture-ledger'}, 'default_depth_case': 'fixture'}))
            cases = p/'cases.json'; cases.write_text('{"cases": {"fixture": {}}}')
            argv = ['driver', '--python', sys.executable, '--finite', str(p/'finite'), '--output', str(p/'out'),
                    '--config', str(config), '--cases', str(cases), '--net=+12V']
            with patch.object(driver.rs, 'Ledger', FailedKB), patch.object(sys, 'argv', argv), self.assertRaises(SystemExit):
                driver.main()
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[-1].startswith('KB-reduce'))

    def test_reductions_only_never_dispatches_driving_or_coupled_work(self):
        import run_coupled_e16 as driver
        calls = []
        class Reduced:
            def __init__(self, out, *args):
                self.out = out; self.log = []; (out/'steps').mkdir()
            def run(self, name, command, inputs, methods, outputs):
                calls.append(name)
                if 'reduce' in name:
                    (self.out/'steps'/ (name + '.json')).write_text(json.dumps({'stdout_tail': '{"pads": 200}'}))
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp); config = p/'config.json'; config.write_text(json.dumps(CONFIG | {
                'scenario': {'id': 'fixture', 'ledger': 'fixture-ledger'}, 'default_depth_case': 'fixture'}))
            cases = p/'cases.json'; cases.write_text('{"cases": {"fixture": {}}}')
            argv = ['driver', '--python', sys.executable, '--finite', str(p/'finite'), '--output', str(p/'out'),
                    '--config', str(config), '--cases', str(cases), '--net=+12V', '--reductions-only']
            with patch.object(driver.rs, 'Ledger', Reduced), patch.object(sys, 'argv', argv):
                driver.main()
            log = json.loads((p/'out/coupled-log.json').read_text())
            self.assertTrue(log['invocations'][0]['reductions_only'])
        self.assertEqual(len(calls), 3)
        self.assertTrue(calls[1].startswith('KA-reduce'))
        self.assertTrue(calls[2].startswith('KB-reduce'))


if __name__ == '__main__':
    unittest.main()
