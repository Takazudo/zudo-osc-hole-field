"""Harmless guard boundary tests; these do not qualify a kernel cgroup runner."""
import importlib.util
import argparse
from contextlib import redirect_stdout
import json
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('guard', Path(__file__).with_name('native_resource_guard.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class GuardTests(unittest.TestCase):
    def test_identity_and_stop_conditions(self):
        for value in ('../x', 'x;sudo', 'x y', '', 'UPPER', 'a' * 62):
            with self.subTest(value=value), self.assertRaises(ValueError):
                guard.identity(value)
        self.assertEqual(guard.identity('run-251-a1'), 'run-251-a1')
        self.assertIsNone(guard.stop_reason(guard.CAP + guard.FLOOR, {'oom': 2}, {'oom': 2}, 0, 300))
        self.assertIn('free-memory', guard.stop_reason(guard.ABORT_FREE, {}, {}, 0, 300))
        self.assertIn('OOM', guard.stop_reason(9 * guard.GIB, {'oom_kill': 2}, {'oom_kill': 1}, 0, 300))
        self.assertEqual(guard.stop_reason(9 * guard.GIB, {}, {}, 300, 300), 'whole-command deadline')

    def test_aggregate_cgroup_limits_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            cg = Path(directory)
            (cg / 'memory.max').write_text(str(guard.CAP))
            (cg / 'memory.swap.max').write_text('0')
            for name in ('memory.current', 'memory.peak', 'memory.events'):
                (cg / name).write_text('0')
            original_read = Path.read_text

            def read(path, *args, **kwargs):
                if str(path) == '/sys/fs/cgroup/cgroup.controllers':
                    return 'cpu memory pids'
                return original_read(path, *args, **kwargs)

            with patch.object(Path, 'read_text', read):
                guard.cgroup_limits(cg)
                (cg / 'memory.max').write_text(str(guard.AGGREGATE_CAP))
                guard.cgroup_limits(cg, guard.AGGREGATE_CAP)
                with self.assertRaisesRegex(ValueError, 'shared slice cap'):
                    guard.cgroup_limits(cg)
                (cg / 'memory.max').write_text('max')
                with self.assertRaisesRegex(ValueError, 'shared slice cap'):
                    guard.cgroup_limits(cg)
                (cg / 'memory.max').write_text(str(guard.CAP))
                (cg / 'memory.swap.max').write_text('max')
                with self.assertRaisesRegex(ValueError, 'zero swap'):
                    guard.cgroup_limits(cg)

    def test_crashed_worker_populations_count_against_two_slots(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            for name, populated in [('epic242-dead.slice', 1), ('epic242-live.slice', 1),
                                    ('epic242-empty.slice', 0)]:
                child = parent / name
                child.mkdir()
                (child / 'memory.current').write_text('0')
                (child / 'cgroup.events').write_text('populated ' + str(populated) + '\n')
            self.assertEqual(set(guard.populated_workers(parent)),
                             {'epic242-dead.slice', 'epic242-live.slice'})
            with self.assertRaisesRegex(ValueError, 'including stale runs'):
                guard.require_capacity(parent)
            (parent / 'epic242-dead.slice' / 'cgroup.events').write_text('populated 0\n')
            guard.require_capacity(parent)
            with self.assertRaisesRegex(ValueError, 'headroom'):
                guard.require_capacity(parent, 10 * guard.GIB)
            guard.require_capacity(parent, 14 * guard.GIB)
            (parent / 'epic242-live.slice' / 'memory.current').write_text(str(guard.CAP))
            guard.require_capacity(parent, 8 * guard.GIB)
            # Missing evidence is not interpreted as an empty slot.
            (parent / 'epic242-live.slice' / 'cgroup.events').unlink()
            with self.assertRaises(FileNotFoundError):
                guard.require_capacity(parent)

    def test_container_cap_and_membership(self):
        item = {'HostConfig': {'Memory': guard.CAP, 'MemorySwap': guard.CAP,
                               'CgroupParent': 'epic242-a.slice'}}
        guard.docker_membership(item, '0::/epic242.slice/epic242-a.slice/docker-abc.scope',
                                '/epic242.slice/epic242-a.slice')
        with self.assertRaisesRegex(ValueError, 'outside'):
            guard.docker_membership(item, '0::/other.slice/docker-abc.scope',
                                    '/epic242.slice/epic242-a.slice')
        item['HostConfig']['MemorySwap'] = 0
        with self.assertRaisesRegex(ValueError, 'caps'):
            guard.docker_membership(item, '0::/epic242.slice/epic242-a.slice/docker-abc.scope',
                                    '/epic242.slice/epic242-a.slice')

    def test_cleanup_orders_producer_container_anchor_and_checks_survivors(self):
        calls = []
        stopped = set()

        def command(args, **_):
            calls.append(args)
            if args[:2] == ['systemctl', 'show']:
                return 'loaded' if '--property=LoadState' in args else ('inactive' if args[2] in stopped else 'active')
            if args[:3] == ['sudo', '-n', 'systemctl']:
                stopped.add(args[-1])
            return ''

        with patch.object(guard, 'worker_containers', side_effect=[['owned123'], []]), \
                patch.object(guard, 'run', side_effect=command):
            self.assertEqual(guard.cleanup('a', ['checks.service'], 'anchor.service'), [])
        self.assertLess(calls.index(['sudo', '-n', 'systemctl', 'stop', 'checks.service']),
                        calls.index(['docker', 'rm', '-f', 'owned123']))
        self.assertLess(calls.index(['docker', 'rm', '-f', 'owned123']),
                        calls.index(['sudo', '-n', 'systemctl', 'stop', 'anchor.service']))

    def test_cleanup_lease_serializes_guard_and_watchdog(self):
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory) / 'cleanup.lock'
            lock.touch(mode=0o600)
            entered = threading.Event()
            finished = threading.Event()

            def contender():
                with guard.cleanup_lease(str(lock), os.getuid(), time.monotonic() + 2):
                    entered.set()
                finished.set()

            with guard.cleanup_lease(str(lock), os.getuid(), time.monotonic() + 2):
                thread = threading.Thread(target=contender)
                thread.start()
                self.assertFalse(entered.wait(0.15))
            self.assertTrue(finished.wait(1))
            thread.join()

    def test_cleanup_tolerates_transient_removal_and_disappeared_anchor(self):
        calls = []
        listed = iter([['owned123'], ['owned123'], []])

        def command(args, **_):
            calls.append(args)
            if args[:3] == ['systemctl', 'show', 'anchor.service']:
                return 'not-found' if '--property=LoadState' in args else 'inactive'
            if args[:2] == ['docker', 'rm']:
                raise subprocess.CalledProcessError(1, args, stderr='removal of container owned123 is already in progress')
            return ''

        with patch.object(guard, 'worker_containers', side_effect=lambda *a, **k: next(listed)), \
                patch.object(guard, 'run', side_effect=command):
            self.assertEqual(guard.cleanup('a', [], 'anchor.service'), [])
        self.assertFalse(any(args[:3] == ['sudo', '-n', 'systemctl'] for args in calls))

    def test_unit_stop_success_must_prove_final_inactive_state(self):
        def command(args, **_):
            if args[:2] == ['systemctl', 'show']:
                return 'loaded' if '--property=LoadState' in args else 'active'
            return ''  # systemctl stop reports success, unit remains active.
        with patch.object(guard, 'run', side_effect=command):
            failure = guard.stop_unit_if_present('anchor.service', lambda: 3)
        self.assertIn("final unit state=('loaded', 'active')", failure)

    def test_unit_stop_error_preserves_stderr_when_still_active(self):
        def command(args, **_):
            if args[:2] == ['systemctl', 'show']:
                return 'loaded' if '--property=LoadState' in args else 'active'
            raise subprocess.CalledProcessError(5, args, stderr='permission denied')
        with patch.object(guard, 'run', side_effect=command):
            failure = guard.stop_unit_if_present('anchor.service', lambda: 3)
        self.assertIn('permission denied', failure)
        self.assertIn("('loaded', 'active')", failure)
        self.assertFalse(guard.unit_settled('not-found', 'active'))

    def test_cleanup_preserves_real_survivor_and_stderr(self):
        clock = [0.0]
        def tick():
            return clock[0]
        def sleep(_):
            clock[0] += 20
        def command(args, **_):
            if args[:2] == ['docker', 'rm']:
                raise subprocess.CalledProcessError(1, args, stderr='permission denied')
            return ''

        with patch.object(guard, 'worker_containers', return_value=['owned123']), \
                patch.object(guard, 'run', side_effect=command), \
                patch.object(guard.time, 'monotonic', side_effect=tick), \
                patch.object(guard.time, 'sleep', side_effect=sleep):
            failures = guard.cleanup('a', [])
        self.assertTrue(any('owned123' in item and 'permission denied' in item for item in failures))

    def test_pinned_image_must_be_local_no_pull(self):
        image = 'kicad/kicad@sha256:' + '1' * 64
        with patch.object(Path, 'read_text', return_value="KICAD_IMAGE='" + image + "'\n"), \
                patch.object(guard, 'run', return_value=json.dumps([{'RepoDigests': [image]}])) as command:
            self.assertEqual(guard.require_local_image(), image)
            command.assert_called_once_with(['docker', 'image', 'inspect', image])
        with patch.object(Path, 'read_text', return_value="KICAD_IMAGE='" + image + "'\n"), \
                patch.object(guard, 'run', return_value=json.dumps([{'RepoDigests': []}])):
            with self.assertRaisesRegex(ValueError, 'never pull'):
                guard.require_local_image()

    def test_remote_or_unsupported_daemon_refused(self):
        with patch.dict(guard.os.environ, {'DOCKER_HOST': 'tcp://remote'}), \
                patch.object(guard, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'custom Docker'):
                guard.local_docker()
            command.assert_not_called()

    def test_startup_refuses_without_systemd_pid_one_before_side_effects(self):
        args = argparse.Namespace(worker='test-a', admission_id='admitted', command=['/bin/true'],
                                  seconds=30, sha='0' * 40, evidence='/tmp/unused-guard-evidence',
                                  plan=False, hook_sha256='0' * 64)
        original_read = Path.read_text

        def read(path, *a, **kw):
            if str(path) == '/proc/1/comm':
                return 'python\n'
            return original_read(path, *a, **kw)

        with patch.object(Path, 'read_text', read), patch.object(guard, 'run') as command:
            with redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, 'PID 1 must be systemd'):
                    guard.execute(args)
            command.assert_not_called()

    def test_hook_passes_caps_to_every_docker_run(self):
        with tempfile.TemporaryDirectory() as directory:
            binpath = Path(directory) / 'docker'
            output = Path(directory) / 'calls.jsonl'
            binpath.write_text('#!' + sys.executable + '\n'
                               'import json, os, sys\n'
                               'with open(os.environ["FAKE_DOCKER_CALLS"], "a") as out:\n'
                               '    out.write(json.dumps(sys.argv[1:]) + "\\n")\n'
                               'print("10.0.6")\n')
            binpath.chmod(0o755)
            root = Path(__file__).resolve().parents[2]
            env = os.environ.copy()
            env.update(PATH=directory + os.pathsep + env['PATH'], FAKE_DOCKER_CALLS=str(output),
                       EPIC242_NATIVE_SLICE='epic242-w61.slice', EPIC242_NATIVE_WORKER='a',
                       EPIC242_NATIVE_DEADLINE=str(int(time.time()) + 60))
            result = subprocess.run(['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version'],
                                    cwd=root, env=env, capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 0, result.stderr)
            calls = [json.loads(line) for line in output.read_text().splitlines()]
            self.assertEqual(len(calls), 2)  # Version probe and requested command.
            for call in calls:
                self.assertIn('--pull=never', call)
                self.assertIn('--memory=6442450944', call)
                self.assertIn('--memory-swap=6442450944', call)
                self.assertIn('--cgroup-parent=epic242-w61.slice', call)
                self.assertIn('--label', call)
                self.assertIn('epic242.native.worker=a', call)
                self.assertIn('timeout', call)

            binpath.write_text(binpath.read_text().replace('10.0.6', '10.0.5'))
            result = subprocess.run(['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version'],
                                    cwd=root, env=env, capture_output=True, text=True, timeout=5)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('requires KiCad 10.0.6', result.stderr)

    def test_hook_refuses_native_fallback(self):
        root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env.update(EPIC242_NATIVE_SLICE='epic242-w61.slice', EPIC242_NATIVE_WORKER='a',
                   EPIC242_NATIVE_DEADLINE=str(int(time.time()) + 60), KICAD_CLI_BIN='/bin/true')
        result = subprocess.run(['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version'],
                                cwd=root, env=env, capture_output=True, text=True, timeout=5)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('requires the local Docker oracle', result.stderr)


if __name__ == '__main__':
    unittest.main()
