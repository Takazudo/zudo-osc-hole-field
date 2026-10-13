"""Source-only qualification boundary tests; no Docker/systemd/native runs."""
import argparse
import importlib.util
import json
import os
import signal
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import native_resource_guard as guard
import qualify_resource_guard as qualification
import run_resource_fixture as fixture

IMAGE = 'sha256:' + 'a' * 64


class QualificationBoundaries(unittest.TestCase):
    def test_cleanup_exception_still_restores_signal_handlers(self):
        previous = signal.getsignal(signal.SIGTERM)
        def failed(args):
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            raise OSError('receipt write failed')
        with patch.object(qualification, '_qualify', side_effect=failed), self.assertRaises(OSError):
            qualification.qualify(None)
        self.assertEqual(signal.getsignal(signal.SIGTERM), previous)

    def test_active_phase_termination_retains_failure_and_owned_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'fresh'
            args = argparse.Namespace(admission_id='parent', sha='1' * 40,
                hook_sha256=qualification.hashlib.sha256((HERE / 'run.sh').read_bytes()).hexdigest(),
                evidence_directory=str(evidence))
            commands = []
            def command(argv, **kwargs):
                commands.append(argv)
                if argv[:2] == ['git', 'rev-parse']: return args.sha
                if argv[:2] == ['git', 'status']: return ''
                if argv[0] == 'cc' and '-o' in argv:
                    Path(argv[argv.index('-o') + 1]).write_bytes(b'mocked binary')
                if argv[:3] == ['docker', 'image', 'import']: return IMAGE
                if argv[:2] == ['cc', '--version']: return 'mock compiler'
                if argv[:2] == ['systemctl', 'show']: return 'inactive'
                return ''
            child = Mock(); child.poll.return_value = None
            def wait(timeout):
                if timeout == 75:
                    signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
                return 0
            child.wait.side_effect = wait
            previous = signal.getsignal(signal.SIGTERM)
            def cleanup(worker):
                self.assertEqual(signal.getsignal(signal.SIGTERM), signal.SIG_IGN)
                return []
            with patch.object(guard, 'run', side_effect=command), \
                    patch.object(qualification, 'capability_probe', return_value={}), \
                    patch.object(qualification.subprocess, 'Popen', return_value=child), \
                    patch.object(qualification, 'cleanup_started_worker', side_effect=cleanup) as cleaned, \
                    patch.object(qualification, 'wait_for'), patch.object(qualification, 'quiet', return_value=True), \
                    patch.object(qualification, 'observe_owned_worker', return_value={'workload_absent': True}), \
                    patch.object(Path, 'glob', return_value=[]):
                self.assertEqual(qualification.qualify(args), 1)
            child.terminate.assert_called_once(); cleaned.assert_called_once()
            self.assertEqual(signal.getsignal(signal.SIGTERM), previous)
            self.assertIn(['docker', 'image', 'rm', IMAGE], commands)
            report = json.loads((evidence / 'qualification.json').read_text())
            self.assertEqual(report['status'], 'FAIL')
            self.assertIn('interrupted by signal', report['reason'])
            self.assertTrue(report['owned_image_removed'])
            self.assertTrue(report['owned_workloads_absent'])

    def test_harmless_mode_requires_exact_fixture_not_arbitrary_native_command(self):
        command = [sys.executable, str(HERE / 'run_resource_fixture.py'), '--image', IMAGE, '--mode', 'aggregate']
        metadata = [{'Id': IMAGE, 'Config': {'Entrypoint': ['/fixture']}}]
        with patch.object(guard, 'run', return_value=json.dumps(metadata)) as call:
            guard.require_harmless_fixture(IMAGE, command)
            call.assert_called_once_with(['docker', 'image', 'inspect', IMAGE])
        with patch.object(guard, 'run') as call:
            for bad in ([sys.executable, 'scripts/native.py'], command + ['extra'], command[:-1] + ['route']):
                with self.assertRaisesRegex(ValueError, 'only the reviewed fixture'):
                    guard.require_harmless_fixture(IMAGE, bad)
            call.assert_not_called()

    def test_harmless_image_identity_and_entrypoint_refused(self):
        command = [sys.executable, str(HERE / 'run_resource_fixture.py'), '--image', IMAGE, '--mode', 'hold']
        for metadata in ({'Id': 'sha256:' + 'b' * 64, 'Config': {'Entrypoint': ['/fixture']}},
                         {'Id': IMAGE, 'Config': {'Entrypoint': ['/bin/sh']}}):
            with patch.object(guard, 'run', return_value=json.dumps([metadata])):
                with self.assertRaisesRegex(ValueError, 'identity/entrypoint'):
                    guard.require_harmless_fixture(IMAGE, command)

    def test_fixture_command_keeps_shared_slice_caps_no_pull_no_network(self):
        worker = 'q-test-parent-death'
        env = {'EPIC242_NATIVE_WORKER': worker,
               'EPIC242_NATIVE_SLICE': 'epic242-w' + worker.encode().hex() + '.slice',
               'EPIC242_NATIVE_DEADLINE': str(int(time.time()) + 30)}
        command = fixture.fixture_command(IMAGE, 'hold', env)
        for expected in ('--memory=6442450944', '--memory-swap=6442450944', '--pull=never',
                         '--network=none', '--cgroup-parent=' + env['EPIC242_NATIVE_SLICE']):
            self.assertIn(expected, command)
        self.assertEqual(command[-2:], [IMAGE, 'hold'])
        for mutation in ({'EPIC242_NATIVE_SLICE': 'epic242-q-test-parent-death.slice'},
                         {'EPIC242_NATIVE_DEADLINE': '1'}, {'DOCKER_HOST': 'tcp://remote'}):
            with self.assertRaises(ValueError):
                fixture.fixture_command(IMAGE, 'hold', {**env, **mutation})

    def test_capability_probe_refuses_before_control_mutation(self):
        with patch.object(Path, 'read_text', return_value='tail\n'), \
                patch.object(guard, 'run') as commands, patch.object(guard, 'local_docker') as docker:
            with self.assertRaisesRegex(ValueError, 'no reconfiguration'):
                qualification.capability_probe()
            commands.assert_not_called()
            docker.assert_not_called()

    def test_readiness_needs_guard_owned_membership_before_fault(self):
        worker = 'q-tested'
        record = {'worker': worker, 'sha': '1' * 40, 'image_id': IMAGE,
                  'slice_path': '/epic242.slice/epic242-w' + worker.encode().hex() + '.slice',
                  'container_id': 'owned'}
        with patch.object(Path, 'glob', return_value=[]), patch.object(guard, 'run', return_value='active'):
            self.assertFalse(qualification.ready(worker, '1' * 40, IMAGE))
        with tempfile.TemporaryDirectory() as tmp:
            receipt = Path(tmp) / 'membership.json'
            receipt.write_text(json.dumps(record))
            with patch.object(Path, 'glob', return_value=[receipt]), \
                    patch.object(guard, 'run', side_effect=['active', json.dumps([{'State': {'Running': True}}])]):
                self.assertTrue(qualification.ready(worker, '1' * 40, IMAGE))
            receipt.write_text(json.dumps({**record, 'sha': '2' * 40}))
            with patch.object(Path, 'glob', return_value=[receipt]):
                with self.assertRaisesRegex(ValueError, 'handshake differs'):
                    qualification.membership(worker, '1' * 40, IMAGE)

    def test_phase_inputs_are_exact_bounded_and_non_native(self):
        args = argparse.Namespace(admission_id='parent-approved', sha='1' * 40, hook_sha256='2' * 64)
        for phase, seconds in [('smoke', 20), ('timeout', 5), ('parent-death', 30), ('watchdog-death', 30)]:
            command = qualification.guard_command(args, 'q-worker', phase, IMAGE, Path('/tmp/evidence'))
            self.assertEqual(command[command.index('--seconds') + 1], str(seconds))
            self.assertIn('--harmless-fixture-image', command)
            self.assertEqual(command[-1], 'aggregate' if phase == 'smoke' else 'hold')
            self.assertNotIn('kicad-cli', command)

    def test_empty_or_unrelated_fault_receipt_cannot_pass(self):
        with self.assertRaises(ValueError):
            qualification.phase_result('timeout', 1, {}, [], True)
        receipt = {'status': 'FAIL', 'observed_containers': ['owned'], 'reason': 'wrong image'}
        with self.assertRaisesRegex(ValueError, 'unrelated'):
            qualification.phase_result('timeout', 1, receipt, [], True)
        receipt['reason'] = 'whole-command deadline'
        qualification.phase_result('timeout', 1, receipt, [], True)
        with self.assertRaisesRegex(ValueError, 'supervisor'):
            qualification.phase_result('watchdog-death', 1, receipt, [], True)
        receipt['reason'] = 'independent watchdog not active'
        qualification.phase_result('watchdog-death', 1, receipt, [], True)
        for phase in ('smoke', 'timeout', 'parent-death', 'watchdog-death'):
            with self.assertRaisesRegex(ValueError, 'survivors'):
                qualification.phase_result(phase, 1, receipt, [], False)

    def test_parent_death_needs_independent_watchdog_clean_receipt(self):
        with self.assertRaises(ValueError):
            qualification.phase_result('parent-death', -9, {}, [], True)
        with self.assertRaises(ValueError):
            qualification.phase_result('parent-death', -9, {}, [{'cleanup_failures': ['survivor']}], True)
        fault = {'pid': 123, 'proc_start': '456', 'injected_at': 10}
        good = {'reason': 'parent guard identity missing', 'cleanup_failures': [], 'parent_pid': 123, 'parent_start': '456', 'finished_at': 11}
        qualification.phase_result('parent-death', -9, {}, [good], True, fault)
        for bad in ({**good, 'reason': 'whole-command deadline'}, {**good, 'parent_pid': 124}, {**good, 'finished_at': 9}):
            with self.assertRaises(ValueError):
                qualification.phase_result('parent-death', -9, {}, [bad], True, fault)

    def test_watchdog_cleanup_error_cannot_be_hidden_by_quiet_state(self):
        receipt = {'status': 'FAIL', 'observed_containers': ['owned'], 'reason': 'whole-command deadline'}
        for embedded, external in (({'cleanup_failures': ['removal failed']}, []), ({}, [{'cleanup_failures': ['survivor']}])):
            with self.assertRaisesRegex(ValueError, 'cleanup failure'):
                qualification.phase_result('timeout', 1, {**receipt, 'watchdog': embedded}, external, True)

    def test_final_owned_observation_requires_every_unit_and_no_container(self):
        with patch.object(guard, 'worker_containers', return_value=[]), patch.object(guard, 'run', side_effect=['inactive', 'failed', 'inactive']):
            state = qualification.observe_owned_worker('q-test')
            self.assertTrue(state['workload_absent'])
            self.assertEqual(len(state['unit_states']), 3)
        with patch.object(guard, 'worker_containers', return_value=['owned']), patch.object(guard, 'run', return_value='inactive'):
            self.assertFalse(qualification.observe_owned_worker('q-test')['workload_absent'])
        with patch.object(guard, 'worker_containers', return_value=[]), patch.object(guard, 'run', side_effect=['inactive', 'active', 'inactive']):
            self.assertFalse(qualification.observe_owned_worker('q-test')['workload_absent'])
        with patch.object(guard, 'worker_containers', side_effect=ValueError('daemon unavailable')):
            with self.assertRaisesRegex(ValueError, 'daemon unavailable'):
                qualification.observe_owned_worker('q-test')

    def test_qualifier_final_cleanup_uses_same_guard_lease(self):
        from contextlib import contextmanager
        entered = []
        @contextmanager
        def lease(*args):
            entered.append(True)
            yield
            entered.pop()
        def cleanup(*args):
            self.assertTrue(entered)
            return []
        with patch.object(Path, 'glob', return_value=[Path('/tmp/owned/cleanup.lock')]), patch.object(guard, 'cleanup_lease', side_effect=lease), patch.object(guard, 'cleanup', side_effect=cleanup):
            self.assertEqual(qualification.cleanup_started_worker('q-test'), [])
        with patch.object(Path, 'glob', return_value=[]), patch.object(qualification, 'observe_owned_worker', return_value={'workload_absent': False}), patch.object(guard, 'cleanup') as mutation:
            with self.assertRaisesRegex(ValueError, 'lease unavailable'):
                qualification.cleanup_started_worker('q-test')
            mutation.assert_not_called()

    def test_preflight_failure_retains_receipt_without_image_or_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            evidence = Path(tmp) / 'fresh'
            args = argparse.Namespace(admission_id='parent', sha='1' * 40,
                                      hook_sha256='2' * 64, evidence_directory=str(evidence))
            with patch.object(guard, 'run', side_effect=['1' * 40, '']), \
                    patch.object(qualification.hashlib, 'sha256') as digest, \
                    patch.object(qualification, 'capability_probe', side_effect=ValueError('unsupported runner')), \
                    patch.object(qualification.subprocess, 'Popen') as child:
                digest.return_value.hexdigest.return_value = '2' * 64
                self.assertEqual(qualification.qualify(args), 1)
                child.assert_not_called()
            report = json.loads((evidence / 'qualification.json').read_text())
            self.assertEqual(report['reason'], 'unsupported runner')
            self.assertFalse(report['native_execution'])
            self.assertEqual(report['phases'], {})
            self.assertEqual(report['raw_phase_evidence'], {})
            with self.assertRaisesRegex(ValueError, 'fresh evidence'):
                qualification.qualify(args)

    def test_workflow_is_only_manual_one_job_no_native_step(self):
        import yaml
        path = HERE.parents[1] / '.github/workflows/routing-benchmark.yml'
        workflow = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        self.assertIn('workflow_dispatch', workflow['on'])
        job = workflow['jobs']['qualify']
        self.assertIn('inputs.resource_qualification', job['if'])
        for name, existing in workflow['jobs'].items():
            if name not in ('qualify', 'lifecycle-qualification'):
                self.assertIn('!inputs.resource_qualification', existing['if'])
        self.assertEqual(len(workflow['jobs']), 9)
        self.assertEqual(job['runs-on'], 'ubuntu-24.04')
        self.assertEqual(job['timeout-minutes'], '10')
        commands = '\n'.join(step.get('run', '') for step in job['steps'])
        self.assertIn('qualify_resource_guard.py', commands)
        for forbidden in ('kicad-cli', 'routing-benchmark', 'route_shards', 'gh workflow run', 'docker pull'):
            self.assertNotIn(forbidden, commands)
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        self.assertEqual(workflow['concurrency']['cancel-in-progress'], 'false')


if __name__ == '__main__':
    unittest.main()
