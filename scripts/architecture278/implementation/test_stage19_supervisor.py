"""Synthetic supervisor tests. No Docker, KiCad, or native capability probes."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import stage19_container as container
import stage19_host as host
import stage19_protocol as p
import stage19_retention as retention

XML = b'<export version="E"><design><tool>Eeschema 10.0.6</tool></design></export>'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name); self.control = self.root / 'control'; self.control.mkdir()
        self.out = self.root / 'out'; self.out.mkdir()
        self.proposal = {'run_id': p.RUN, 'nonce': 'a' * 64, 'source_commit': p.SOURCE, 'verification_commit': 'b' * 40, 'request_sha256': 'c' * 64, 'run_path': str(self.root / p.RUN)}

    def save(self, name, value, root=None):
        (root or self.control).joinpath(name).write_bytes(p.json_bytes(value))

    def authorize(self):
        for name in p.RUNTIME:
            (self.control / name).write_text('synthetic runtime\n')
        for name in p.REVIEWED - set(p.RUNTIME):
            self.save(name, {})
        owner = {**self.proposal, 'approved': True, 'native_export_opportunities': 1, 'approved_by': 'owner', 'approval_reference': 'fresh owner instruction', 'issued_at_unix': 900, 'expires_at_unix': 1100}
        self.save('owner-approval.json', owner)
        review = {**self.proposal, 'approved': True, 'reviewer': 'independent reviewer', 'independent_of_implementation': True, 'issued_at_unix': 900, 'expires_at_unix': 1100, 'capability_sha256': p.digest(self.control / 'capability.json'), 'docker_inspect_sha256': p.digest(self.control / 'docker-inspect.json')}
        self.save('live-review.json', review)
        self.admit = {**self.proposal, 'approved': True, 'issued_at_unix': 900, 'expires_at_unix': 1100, 'reviewed_sha256': {name: p.digest(self.control / name) for name in p.REVIEWED}}
        self.save('admit.json', self.admit)

    def proof(self):
        return {**self.proposal, 'limits': {'cpu.max': '200000 100000', 'memory.max': '4294967296', 'memory.swap.max': '0', 'pids.max': '128'}, 'output_capacity_bytes': p.LIMIT, 'interfaces': ['lo'], 'uid': 1000, 'gid': 1000, 'groups': [1000], 'readonly': {k: True for k in ('/', '/inputs/stage17/generated', '/inputs/stage18/generated', '/control', '/dev/shm')}, 'other_path_writable': {k: False for k in ('/dev', '/dev/mqueue', '/etc/hosts', '/etc/hostname', '/etc/resolv.conf')}}

    def inspection(self, repo, run):
        mounts = [{'Type': 'bind', 'Source': str(run), 'Destination': '/control', 'RW': False}, {'Type': 'bind', 'Source': str(run / 'empty'), 'Destination': '/dev/mqueue', 'RW': False}]
        for stage in ('stage17', 'stage18'):
            mounts.append({'Type': 'bind', 'Source': str(repo / 'design/architecture-278/implementation' / stage / 'generated'), 'Destination': f'/inputs/{stage}/generated', 'RW': False})
        return [{'Id': 'd' * 64, 'Config': {'Image': p.IMAGE, 'Labels': {'osc.run_nonce': self.proposal['nonce']}, 'Entrypoint': ['/usr/bin/timeout'], 'Cmd': ['-s', 'KILL', '600', 'python3', '-B', '/control/stage19_container.py']}, 'HostConfig': {'NetworkMode': 'none', 'ReadonlyRootfs': True, 'NanoCpus': 2000000000, 'Memory': 4294967296, 'MemorySwap': 4294967296, 'PidsLimit': 128, 'Privileged': False, 'CapDrop': ['ALL'], 'CapAdd': None, 'SecurityOpt': ['no-new-privileges'], 'IpcMode': 'none', 'LogConfig': {'Type': 'none'}, 'Tmpfs': {'/output': 'rw,noexec,nosuid,nodev,size=262144000,mode=1777'}}, 'Mounts': mounts}]


class AdmissionTests(Fixture):
    def test_fresh_and_exact(self):
        self.authorize(); p.admission(self.control, self.proposal, 1000)

    def test_reject_stale_or_copied_admission(self):
        self.authorize()
        for key, bad in [('approved', False), ('nonce', 'old'), ('source_commit', 'old'), ('verification_commit', 'old'), ('run_id', 'run002'), ('request_sha256', 'old'), ('expires_at_unix', 999), ('issued_at_unix', 1001)]:
            with self.subTest(key=key):
                altered = copy.deepcopy(self.admit); altered[key] = bad; self.save('admit.json', altered)
                with self.assertRaises(ValueError): p.admission(self.control, self.proposal, 1000)

    def test_reject_hash_missing_extra_or_substituted(self):
        self.authorize()
        for mode in ('missing', 'extra', 'wrong'):
            altered = copy.deepcopy(self.admit)
            if mode == 'missing': del altered['reviewed_sha256']['request.json']
            if mode == 'extra': altered['reviewed_sha256']['legacy-admit.json'] = 'a' * 64
            if mode == 'wrong': altered['reviewed_sha256']['capability.json'] = 'a' * 64
            self.save('admit.json', altered)
            with self.subTest(mode=mode), self.assertRaises(ValueError): p.admission(self.control, self.proposal, 1000)

    def test_owner_and_review_required(self):
        for name, key, value in [('owner-approval.json', 'approved', False), ('owner-approval.json', 'run_path', '/old'), ('owner-approval.json', 'expires_at_unix', 999), ('live-review.json', 'independent_of_implementation', False), ('live-review.json', 'capability_sha256', 'wrong')]:
            self.authorize(); data = p.load(self.control / name); data[key] = value; self.save(name, data)
            self.admit['reviewed_sha256'][name] = p.digest(self.control / name); self.save('admit.json', self.admit)
            with self.subTest(name=name, key=key), self.assertRaises(ValueError): p.admission(self.control, self.proposal, 1000)

    def test_json_duplicates_and_size(self):
        (self.control / 'bad').write_bytes(b'{"approved":true,"approved":false}')
        with self.assertRaises(ValueError): p.load(self.control / 'bad')
        (self.control / 'bad').write_bytes(b'x' * 10)
        with self.assertRaises(ValueError): p.load(self.control / 'bad', 9)

    def test_nonfinite_times(self):
        for bad in (float('nan'), float('inf'), True):
            with self.assertRaises(ValueError): p.fresh({'issued_at_unix': bad, 'expires_at_unix': 1100}, 1000, 300)

    def test_capability_failures(self):
        p.capability(self.proof(), self.proposal)
        for key, value in [('nonce', 'old'), ('limits', {}), ('uid', 0), ('groups', [0]), ('interfaces', ['lo', 'eth0']), ('output_capacity_bytes', p.LIMIT + 1), ('readonly', {}), ('other_path_writable', {})]:
            proof = self.proof(); proof[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): p.capability(proof, self.proposal)

    def test_mount_and_inspection_failures(self):
        repo = self.root / 'repo'; run = self.root / p.RUN
        rows = self.inspection(repo, run); p.inspect_container(rows, repo, run)
        for mutation in ('network', 'rw', 'extra', 'image', 'timeout'):
            bad = copy.deepcopy(rows)
            if mutation == 'network': bad[0]['HostConfig']['NetworkMode'] = 'host'
            if mutation == 'rw': bad[0]['Mounts'][0]['RW'] = True
            if mutation == 'extra': bad[0]['Mounts'].append({'Type': 'volume', 'Destination': '/extra', 'RW': True})
            if mutation == 'image': bad[0]['Config']['Image'] = 'latest'
            if mutation == 'timeout': bad[0]['Config']['Cmd'][2] = '6000'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): p.inspect_container(bad, repo, run)

    def test_input_inventory_omission_extra_symlink(self):
        root = self.root / 'inputs'; root.mkdir(); (root / 'a').write_text('input')
        original = p.inventory(root)
        (root / 'a').write_text('substitution'); self.assertNotEqual(p.inventory(root), original)
        (root / 'extra').write_text('extra'); self.assertNotEqual(p.inventory(root), original)
        (root / 'link').symlink_to(root / 'a')
        with self.assertRaises(ValueError): p.inventory(root)


class ExecutionTests(Fixture):
    def run_once(self, version=b'10.0.6\n', exit_code=0, timeout=False):
        calls = []
        def runner(argv, stdout, stderr, timeout):
            calls.append(argv)
            if len(calls) == 1: stdout.write(version)
            else: (self.out / 'netlist.xml').write_bytes(XML)
            return subprocess.CompletedProcess(argv, exit_code)
        records = []
        result = container.execute_once(self.control, self.out, self.proposal, 0, records, runner=runner, clock=lambda: 1, wall=lambda: 1000)
        return result, calls, records

    def test_exact_two_commands_and_single_consumption(self):
        self.authorize(); result, calls, records = self.run_once()
        self.assertEqual(result, 'NATIVE_SUCCESS'); self.assertEqual(calls, p.COMMANDS)
        with self.assertRaises(FileExistsError): self.run_once()

    def test_bad_version_never_exports(self):
        self.authorize(); result, calls, records = self.run_once(version=b'10.0.5\n')
        self.assertEqual(result, 'VERSION_MISMATCH'); self.assertEqual(len(calls), 1)

    def test_oversized_version_never_exports(self):
        self.authorize(); result, calls, records = self.run_once(version=b'10.0.6' + b' ' * 100)
        self.assertEqual(result, 'VERSION_MISMATCH'); self.assertEqual(len(calls), 1)

    def test_nonzero_never_retries(self):
        self.authorize(); result, calls, records = self.run_once(exit_code=7)
        self.assertEqual(result, 'NATIVE_FAILURE'); self.assertEqual(len(calls), 1)

    def test_timeout_consumes_opportunity(self):
        self.authorize(); calls = []
        def runner(argv, **kwargs):
            calls.append(argv); raise subprocess.TimeoutExpired(argv, 1)
        records = []
        with self.assertRaises(subprocess.TimeoutExpired): container.execute_once(self.control, self.out, self.proposal, 0, records, runner=runner, clock=lambda: 1, wall=lambda: 1000)
        self.assertEqual(len(calls), 1); self.assertIsNone(records[0]['exit']); self.assertTrue((self.out / 'consumed.json').exists())

    def test_invalid_admission_never_calls_runner(self):
        self.authorize(); self.admit['nonce'] = 'old'; self.save('admit.json', self.admit)
        with patch.object(subprocess, 'run') as runner:
            with self.assertRaises(ValueError): container.execute_once(self.control, self.out, self.proposal, 0, [], runner=runner, clock=lambda: 1, wall=lambda: 1000)
            runner.assert_not_called()


class RetentionTests(Fixture):
    def success(self):
        self.save('done.json', {'status': 'NATIVE_SUCCESS', 'native_success': True, 'commands_attempted': 2, 'quiescent': True}, self.out)
        self.save('commands.json', [{'argv': argv, 'exit': 0, 'started_elapsed_seconds': 1, 'elapsed_seconds': 1} for argv in p.COMMANDS], self.out)
        self.save('resource.json', {'elapsed_seconds': 3, 'rusage_children': [0] * 16, 'cgroup': {'memory.peak': '100', 'memory.events': 'oom 0', 'cpu.stat': 'usage_usec 1'}}, self.out)
        for name in ('supervisor.stdout', 'supervisor.stderr', 'command-0.stderr', 'command-1.stdout', 'command-1.stderr'):
            (self.out / name).write_bytes(b'')
        (self.out / 'command-0.stdout').write_bytes(b'10.0.6\n'); (self.out / 'netlist.xml').write_bytes(XML)
        self.save('consumed.json', {**self.proposal, 'automatic_retry': False, 'admission_sha256': 'a' * 64, 'capability_sha256': 'b' * 64}, self.out)

    def receipt(self):
        rows = [{'path': str(path.relative_to(self.out)), 'size': path.stat().st_size, 'sha256': p.digest(path)} for path in sorted(self.out.rglob('*')) if path.is_file()]
        return {'status': 'VERIFIED_HASHED_COPY', 'bytes': sum(r['size'] for r in rows), 'files': rows, 'cleanup_permitted': True}

    def test_success_separates_parity(self):
        self.success(); result = retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)
        self.assertTrue(result['cleanup_permitted']); self.assertEqual(result['logical_parity'], 'NOT RUN')

    def test_omitted_evidence(self):
        for name in ('resource.json', 'done.json', 'commands.json', 'command-1.stderr', 'consumed.json', 'netlist.xml'):
            self.success(); (self.out / name).unlink()
            with self.subTest(name=name), self.assertRaises((ValueError, FileNotFoundError)): retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)

    def test_sexpr_only_not_success(self):
        self.success(); (self.out / 'netlist.xml').rename(self.out / 'netlist.net')
        with self.assertRaises(ValueError): retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)

    def test_bad_xml(self):
        for xml in (b'', b'(export)', b'<export version="D"/>', b'<export version="E"><tool>Eeschema 10.0.5</tool></export>'):
            self.success(); (self.out / 'netlist.xml').write_bytes(xml)
            with self.subTest(xml=xml), self.assertRaises((ValueError, p.ET.ParseError)): retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)

    def test_xml_structural_bounds_and_declarations(self):
        for xml in (b'<!DOCTYPE export [<!ENTITY x "Eeschema 10.0.6">]><export version="E"><design><tool>&x;</tool></design></export>', b'<export version="E">' + b'<n>' * 65 + b'</n>' * 65 + b'</export>', b'<export version="E">' + b'<n/>' * 100001 + b'</export>', b'<export version="E"><tool>Eeschema 10.0.6</tool></export>'):
            self.success(); (self.out / 'netlist.xml').write_bytes(xml)
            with self.assertRaises(ValueError): retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)

    def test_done_substitution(self):
        for key, value in [('status', 'PASS'), ('native_success', False), ('commands_attempted', 1), ('quiescent', False)]:
            self.success(); done = p.load(self.out / 'done.json'); done[key] = value; self.save('done.json', done, self.out)
            with self.subTest(key=key), self.assertRaises(ValueError): retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)

    def test_commands_substitution(self):
        for mode in ('argv', 'extra', 'null', 'nonzero', 'bad_version'):
            self.success(); commands = p.load(self.out / 'commands.json')
            if mode == 'argv': commands[1]['argv'][-1] = '/inputs/old.kicad_sch'
            if mode == 'extra': commands.append(commands[-1])
            if mode == 'null': commands[-1]['exit'] = None
            if mode == 'nonzero': commands[-1]['exit'] = 1
            if mode == 'bad_version': (self.out / 'command-0.stdout').write_bytes(b'10.0.5')
            self.save('commands.json', commands, self.out)
            with self.subTest(mode=mode), self.assertRaises(ValueError): retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)

    def test_durable_hash_size_membership(self):
        self.success(); receipt = self.receipt(); (self.out / 'netlist.xml').write_bytes(XML + b' ')
        with self.assertRaises(ValueError): retention.verify(self.out, receipt, self.proposal, 'a' * 64, 'b' * 64)
        self.success(); receipt = self.receipt(); receipt['bytes'] += 1
        with self.assertRaises(ValueError): retention.verify(self.out, receipt, self.proposal, 'a' * 64, 'b' * 64)

    def test_complete_failure_retained_without_success(self):
        self.success(); commands = p.load(self.out / 'commands.json'); commands[-1]['exit'] = 2
        self.save('commands.json', commands, self.out); (self.out / 'netlist.xml').unlink()
        self.save('done.json', {'status': 'NATIVE_FAILURE', 'native_success': False, 'commands_attempted': 2, 'quiescent': True}, self.out)
        result = retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64); self.assertTrue(result['cleanup_permitted']); self.assertFalse(result['native']['native_success'])

    def test_foreign_consumption(self):
        self.success(); data = p.load(self.out / 'consumed.json'); data['nonce'] = 'old'; self.save('consumed.json', data, self.out)
        with self.assertRaises(ValueError): retention.verify(self.out, self.receipt(), self.proposal, 'a' * 64, 'b' * 64)

    def test_isolated_scanner(self):
        with patch.object(retention.raw, 'stream', return_value=0) as stream:
            retention.isolated_stream(['docker', 'exec', 'synthetic', 'python3', '-c', 'print(1)'], 1, 1, lambda b: None)
            self.assertEqual(stream.call_args.args[0][3:6], ['python3', '-I', '-c'])

    def test_metadata_cap(self):
        (self.control / 'big').write_bytes(b'1234567890')
        with patch.object(p, 'META_LIMIT', 9), self.assertRaises(ValueError): host.metadata_bytes(self.control)

    def test_docker_builder_only_two_input_mounts(self):
        argv = p.docker_argv('/repo', '/run/' + p.RUN)
        self.assertIn('--pull=never', argv); self.assertEqual(argv.count('--mount'), 4)
        self.assertEqual(argv[-4:], ['600', 'python3', '-B', '/control/stage19_container.py'])


class HostLifecycleTests(Fixture):
    def setup_launch(self):
        self.repo = self.root / 'repo'; scripts = self.repo / 'scripts/architecture278/implementation'; scripts.mkdir(parents=True)
        for name in p.RUNTIME: (scripts / name).write_text('synthetic runtime')
        self.run = self.root / p.RUN
        self.request_path = self.root / 'request.json'; self.request_path.write_bytes(p.json_bytes({'verification_commit': 'b' * 40, 'input_files_sha256': {}}))
        self.proposal.update(request_sha256=p.digest(self.request_path), run_path=str(self.run))
        self.owner_path = self.root / 'owner.json'
        self.owner_path.write_bytes(p.json_bytes({**self.proposal, 'approved': True, 'native_export_opportunities': 1, 'approved_by': 'owner', 'approval_reference': 'fresh', 'issued_at_unix': 900, 'expires_at_unix': 1100}))
        self.calls = []; self.elapsed = 0

    def simulate(self, mode):
        self.setup_launch()
        def command(argv, **kwargs):
            self.calls.append(argv)
            if argv[1] == 'ps': return b'existing' if mode == 'collision' else b''
            if argv[1] == 'run':
                if mode.startswith('lost'):
                    self.elapsed = 600; raise TimeoutError('lost launch response')
                return ('d' * 64).encode()
            if argv[1] == 'inspect':
                rows = self.inspection(self.repo, self.run)
                if mode == 'lost-foreign': rows[0]['Config']['Labels'] = {}
                return p.json_bytes(rows)
            if argv[1] == 'rm': return b'removed'
            raise AssertionError(argv)
        def run(argv, **kwargs):
            self.calls.append(argv)
            return subprocess.CompletedProcess(argv, 1 if argv[-1] == '/output/ready' else 0)
        def retain(*args, **kwargs):
            if mode == 'bad-retention':
                self.elapsed = 600; raise ValueError('partial retention')
            return {'status': 'VERIFIED_HASHED_COPY_AND_RECEIPTS', 'native': {'native_success': True}, 'cleanup_permitted': True}
        with patch.object(host, 'host_preflight'), patch.object(host, 'checkout'), patch.object(host, 'command', side_effect=command), patch.object(host.subprocess, 'run', side_effect=run), patch.object(host.retention, 'retain', side_effect=retain), patch.object(host.secrets, 'token_hex', return_value='a' * 64), patch.object(host.time, 'time', return_value=1000), patch.object(host.time, 'monotonic', side_effect=lambda: self.elapsed):
            if mode == 'success': self.assertEqual(host.orchestrate(self.repo, self.run, self.request_path, self.owner_path), 0)
            else:
                with self.assertRaises((ValueError, TimeoutError)): host.orchestrate(self.repo, self.run, self.request_path, self.owner_path)

    def test_checkout_rejects_incomplete_or_substituted_manifest(self):
        repo = Path(host.__file__).resolve().parents[3]
        canonical = {'verification_commit': 'b' * 40, 'source_commit': p.SOURCE, 'native_argv': p.COMMANDS, 'image': p.IMAGE, 'verification_files_sha256': {'source': 'a' * 64}, 'runtime_sha256': {name: 'c' * 64 for name in p.RUNTIME}, 'input_files_sha256': {'stage18/generated/a01.kicad_sch': 'd' * 64}}
        for field in ('verification_files_sha256', 'input_files_sha256'):
            bad = copy.deepcopy(canonical); bad[field] = {}
            with patch.object(host, 'command', return_value=('b' * 40).encode()), patch.object(host.requests, 'request', return_value=canonical), self.assertRaises(ValueError):
                host.checkout(repo, bad)

    def test_name_collision_never_touches_container(self):
        self.simulate('collision'); self.assertEqual([c[1] for c in self.calls], ['ps']); self.assertFalse(self.run.exists())

    def test_lost_response_foreign_container_never_killed(self):
        self.simulate('lost-foreign'); self.assertNotIn('kill', [c[1] for c in self.calls]); self.assertNotIn('rm', [c[1] for c in self.calls])

    def test_lost_response_owned_container_stopped_not_removed(self):
        self.simulate('lost-owned'); self.assertIn(['docker', 'kill', 'd' * 64], self.calls); self.assertNotIn('rm', [c[1] for c in self.calls])

    def test_failed_retention_no_removal(self):
        self.simulate('bad-retention'); self.assertNotIn('rm', [c[1] for c in self.calls]); self.assertTrue((self.run / 'host-failure.json').is_file())

    def test_verified_retention_removes_only_owned_id(self):
        self.simulate('success'); self.assertIn(['docker', 'rm', 'd' * 64], self.calls)


if __name__ == '__main__':
    unittest.main()
