"""Deterministic admission/retention tests; no Docker, cgroups or KiCad run."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from scripts.kicad import native_resource_guard as guard
from scripts.kicad.test_native_resource_lifecycle import CID, OTHER, WORKER, SLICE, container, missing

SCRIPT = Path(__file__).with_name('native_start_gate.sh')
TOKEN = 'gate.abcdefgh1234'
IMAGE = 'pinned@sha256:' + '1' * 64


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.gate = self.root / 'gates' / TOKEN
        (self.root / 'gates').mkdir(mode=0o700)
        self.gate.mkdir(mode=0o700)
        (self.root / 'start-gate.sh').write_bytes(SCRIPT.read_bytes())
        self.deadline = int(time.time()) + 10
        self.request = dict(container_id=CID, token=TOKEN, worker=WORKER,
                            deadline=self.deadline, image=IMAGE, command=['/bin/true'])
        (self.gate / 'request.json').write_text(json.dumps(self.request))
        (self.gate / 'container-id').write_text(CID + '\n')
        self.item = container()
        self.item['Config'].update(Image=IMAGE, Entrypoint=['/bin/sh'],
            Cmd=['/epic242-start.sh', '/epic242-gate', str(self.deadline), TOKEN, '/bin/true'])
        self.item['Config']['Labels']['epic242.native.gate'] = TOKEN
        self.item['HostConfig']['AutoRemove'] = False
        self.item['Mounts'] = [dict(Type='bind', Source=str(source), Destination=dest, RW=False)
            for source, dest in [(self.gate, '/epic242-gate'), (self.root / 'start-gate.sh', '/epic242-start.sh')]]
        self.evidence = dict(container_lifecycle=[], container_memberships={}, container_admissions={},
                            container_states={}, gate_script_sha256=hashlib.sha256(SCRIPT.read_bytes()).hexdigest())

    def observe(self, final=False):
        guard.observe_gated_container(CID, WORKER, SLICE, self.root, self.deadline, IMAGE, self.evidence, final)

    def admit(self):
        original = Path.read_text
        def read(path, *args, **kw):
            if str(path) == '/proc/123/cgroup':
                return '0::' + SLICE + '/docker-' + CID + '.scope\n'
            return original(path, *args, **kw)
        with patch.object(guard, 'run', return_value=json.dumps([self.item])), \
             patch.object(guard, 'process_identity', return_value='start'), patch.object(Path, 'read_text', read):
            self.observe()

    def terminal(self, code=0):
        self.item['State'].update(Running=False, Status='exited', ExitCode=code, Pid=0)

    def test_short_command_cannot_run_before_ack_then_exit_status_retained(self):
        # Actual shell gate with a harmless marker command; synchronize on the wait loop.
        ready = self.root / 'sleep-observed'
        bindir = self.root / 'bin'; bindir.mkdir()
        sleeper = bindir / 'sleep'
        sleeper.write_text('#!/bin/sh\ntouch "$GATE_TEST_READY"\nexec /bin/sleep "$@"\n')
        sleeper.chmod(0o755)
        marker = self.root / 'native-command-ran'
        env = dict(os.environ, HOME=str(self.root / 'home'), XDG_RUNTIME_DIR=str(self.root / 'runtime'),
                   PATH=str(bindir) + os.pathsep + os.environ['PATH'], GATE_TEST_READY=str(ready))
        process = subprocess.Popen(['/bin/sh', str(SCRIPT), str(self.gate), str(self.deadline), TOKEN,
                                    '/bin/sh', '-c', 'touch "$1"', 'test', str(marker)], env=env)
        self.addCleanup(lambda: process.poll() is None and process.kill())
        limit = time.monotonic() + 3
        while not ready.exists() and time.monotonic() < limit:
            time.sleep(.01)
        self.assertTrue(ready.exists())
        self.assertFalse(marker.exists())
        self.admit()
        self.assertEqual(process.wait(timeout=3), 0)
        self.assertTrue(marker.exists())
        self.terminal()
        with patch.object(guard, 'run', return_value=json.dumps([self.item])):
            self.observe(final=True)
        self.assertEqual(self.evidence['container_states'][CID]['ExitCode'], 0)

    def test_missing_before_or_after_admission_never_accepted(self):
        for admitted in (False, True):
            if admitted: self.admit()
            with self.subTest(admitted=admitted), patch.object(guard, 'run', side_effect=missing()):
                with self.assertRaises(subprocess.CalledProcessError): self.observe()

    def test_exit_before_first_membership_even_zero_is_fatal(self):
        self.terminal()
        with patch.object(guard, 'run', return_value=json.dumps([self.item])):
            with self.assertRaisesRegex(ValueError, 'before verified admission'): self.observe()
        self.assertFalse((self.gate / 'ack').exists())

    def test_failed_exit_retains_terminal_record_and_fails(self):
        self.admit(); self.terminal(7)
        with patch.object(guard, 'run', return_value=json.dumps([self.item])):
            with self.assertRaisesRegex(ValueError, 'terminal state'): self.observe(final=True)
        self.assertEqual(self.evidence['container_lifecycle'][-1]['state']['ExitCode'], 7)
        self.assertEqual(self.evidence['container_states'][CID]['ExitCode'], 7)

    def test_wrong_identity_command_mount_retention_fail_without_ack(self):
        mutations = [lambda x: x['Config']['Labels'].pop('epic242.native.gate'),
            lambda x: x['Config']['Cmd'].append('extra'), lambda x: x['Config'].update(Image='other'),
            lambda x: x['HostConfig'].update(AutoRemove=True),
            lambda x: x['Mounts'][0].update(RW=True), lambda x: x['Mounts'][0].update(Source='/other'),
            lambda x: x['Mounts'].append(dict(Source=str(self.root), Destination='/alias', RW=True))]
        for change in mutations:
            item = copy.deepcopy(self.item); change(item)
            with self.subTest(item=item), patch.object(guard, 'run', return_value=json.dumps([item])):
                with self.assertRaises(ValueError): self.observe()
            self.assertFalse((self.gate / 'ack').exists())

    def test_stale_ack_swapped_request_and_changed_script_fail(self):
        (self.gate / 'ack').write_text(TOKEN + ':' + CID + '\n')
        with patch.object(guard, 'run', return_value=json.dumps([self.item])):
            with self.assertRaisesRegex(ValueError, 'stale'): self.observe()
        (self.gate / 'ack').unlink()
        self.request['container_id'] = OTHER
        (self.gate / 'request.json').write_text(json.dumps(self.request))
        with patch.object(guard, 'run', return_value=json.dumps([self.item])):
            with self.assertRaisesRegex(ValueError, 'identity differs'): self.observe()
        self.request['container_id'] = CID
        (self.gate / 'request.json').write_text(json.dumps(self.request))
        (self.root / 'start-gate.sh').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'snapshot changed'): self.admit()

    def test_inventory_covers_failed_create_start_missing_extra_and_changed_label(self):
        with patch.object(guard, 'worker_containers', return_value=[CID]):
            self.assertEqual(guard.gated_inventory(self.root, WORKER, self.evidence), {CID})
            with self.assertRaises(ValueError): guard.gated_inventory(self.root, WORKER, self.evidence, True)
        self.admit()
        for listed in ([], [CID, OTHER]):
            with patch.object(guard, 'worker_containers', return_value=listed), self.assertRaises(ValueError):
                guard.gated_inventory(self.root, WORKER, self.evidence, True)
        with patch.object(guard, 'worker_containers', return_value=[CID]):
            self.assertEqual(guard.gated_inventory(self.root, WORKER, self.evidence, True), {CID})
            (self.root / 'gates' / 'gate.failedcreate').mkdir(mode=0o700)
            with self.assertRaises(FileNotFoundError): guard.gated_inventory(self.root, WORKER, self.evidence, True)

    def test_gate_rejects_wrong_ack_expired_deadline_and_propagates_failed_command(self):
        env = dict(os.environ, HOME=str(self.root / 'home'), XDG_RUNTIME_DIR=str(self.root / 'runtime'))
        for ack, deadline, expected in [(TOKEN + ':' + OTHER, self.deadline, 125),
                (TOKEN + ':' + CID, int(time.time()) - 1, 124),
                (TOKEN + ':' + CID, self.deadline, 7)]:
            (self.gate / 'ack').write_text(ack + '\n')
            result = subprocess.run(['/bin/sh', str(SCRIPT), str(self.gate), str(deadline), TOKEN,
                                     '/bin/sh', '-c', 'exit 7'], env=env, timeout=3)
            self.assertEqual(result.returncode, expected)

    def test_live_membership_still_checked_after_ack(self):
        self.admit()
        original = Path.read_text
        def read(path, *args, **kw):
            if str(path) == '/proc/123/cgroup': return '0::/wrong.slice/docker.scope'
            return original(path, *args, **kw)
        with patch.object(guard, 'run', return_value=json.dumps([self.item])), \
             patch.object(guard, 'process_identity', return_value='start'), patch.object(Path, 'read_text', read):
            with self.assertRaisesRegex(ValueError, 'outside'): self.observe()

    def test_no_ack_expires_without_running_command(self):
        marker = self.root / 'should-not-exist'
        result = subprocess.run(['/bin/sh', str(SCRIPT), str(self.gate), str(int(time.time()) + 1), TOKEN,
                                 '/usr/bin/touch', str(marker)], timeout=3)
        self.assertEqual(result.returncode, 124)
        self.assertFalse(marker.exists())

    def test_symlink_gate_or_request_refused(self):
        request = self.gate / 'request.json'; request.rename(self.gate / 'real.json')
        request.symlink_to(self.gate / 'real.json')
        with patch.object(guard, 'run', return_value=json.dumps([self.item])), self.assertRaises(ValueError):
            self.observe()


if __name__ == '__main__':
    unittest.main()
