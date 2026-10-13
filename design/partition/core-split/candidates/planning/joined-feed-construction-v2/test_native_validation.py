"""Source-only request tests. No pcbnew import, Docker, admission or native work."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

spec = importlib.util.spec_from_file_location('native_validation', Path(__file__).with_name('native_validation.py'))
nv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nv)
REPO = Path(os.environ.get('E16_TEST_REPO', str(nv.ROOT)))
F = Path('design/partition/core-split/candidates/planning/joined-feed-construction-v2')


def worker_env(target='KA-t2'):
    worker = 'ci-123-1-e16-' + target.lower()
    return {'EPIC242_NATIVE_WORKER': worker, 'EPIC242_NATIVE_SLICE': 'epic242-w' + worker.encode().hex() + '.slice',
            'EPIC242_NATIVE_DEADLINE': str(int(time.time()) + 2580), **{key: 'fixture-value' for key in nv.AUTHORITY_KEYS}}


def ports(board):
    result = []
    for index, net in enumerate(('+12V', '-12V', '+5V', 'AGND', 'AGND', 'AGND', '+5V')):
        terminal = index < 6
        source_id = f'CS247-{board}-W{index}' if terminal else str(uuid.uuid5(uuid.NAMESPACE_DNS, board + '-pad'))
        result.append({'id': source_id, 'ref': None if terminal else 'U1', 'pad': None if terminal else '3',
             'net': net, 'component_ids': [net + '-component'], 'all_port_fragments_connected_to_feed': True,
             'any_fragment_connected': True})
    return result


def graph_fixture(board):
    source_ports = ports(board)
    mapping = [{'source_id': p['id'], 'native_pad_uuid': str(uuid.uuid5(uuid.NAMESPACE_DNS, p['id'])) if index < 6 else p['id'],
          'ref': 'CS' + str(index) if index < 6 else p['ref'], 'pad': '1' if index < 6 else p['pad'], 'net': p['net']}
          for index, p in enumerate(source_ports)]
    return {'board': board, 'physical_ports': source_ports,
            'graph': {'AGND': {'all_three_returns_one_board_component': True}}}, mapping


class RequestTests(unittest.TestCase):
    def test_worker_refuses_absence_slice_mismatch_expiry_and_excess_budget(self):
        self.assertTrue(nv.verify_worker(worker_env()).endswith('e16-ka-t2'))
        for env in ({}, worker_env() | {'EPIC242_NATIVE_SLICE': 'other.slice'},
                    worker_env() | {'EPIC242_NATIVE_DEADLINE': str(int(time.time()) - 1)},
                    worker_env() | {'EPIC242_NATIVE_DEADLINE': str(int(time.time()) + 2581)}):
            with self.subTest(env=env), self.assertRaises(ValueError):
                nv.verify_worker(env)

    def test_worker_must_name_exact_parent_run_attempt_target(self):
        env = worker_env() | {'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1'}
        nv.verify_worker_authority(env, 'KA-t2')
        for changed in (env | {'GITHUB_RUN_ID': '124'}, env | {'GITHUB_RUN_ATTEMPT': '2'}):
            with self.assertRaisesRegex(ValueError, 'exact parent-approved'):
                nv.verify_worker_authority(changed, 'KA-t2')

    def test_native_import_is_after_refusal(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, 'worker'):
            nv.native_fill(Path('/does/not/exist'), 'KA-t2')
        with patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, 'worker'):
            nv.native_connectivity(Path('/does/not/exist'), 'KA-t2')
        self.assertNotIn('pcbnew', __import__('sys').modules)

    def test_command_boundaries_full_severity_and_no_reset(self):
        commands = nv.phase_commands(str(F / 'native_validation.py'), '.circuit-cache/request', 'KA-t2', worker_env())
        self.assertEqual([p for p, _ in commands], ['fill', 'drc', 'connectivity'])
        fill, drc, census = [c for _, c in commands]
        self.assertIn('native-fill', fill)
        self.assertIn('native-connectivity', census)
        self.assertIn('--severity-all', drc)
        self.assertNotIn('--refill-zones', drc)
        self.assertEqual(drc[-1], '.circuit-cache/request/KA-t2/filled/KA-t2.kicad_pcb')
        for command in (fill, census):
            self.assertIn('env', command)
            self.assertTrue(any(c.startswith('EPIC242_NATIVE_SLICE=') for c in command))
        admission = nv.admission_command(REPO, str(F / 'native_validation.py'), '.circuit-cache/request', 'KB-p1')
        self.assertIn('e16-kb-p1', admission)
        self.assertEqual(admission[admission.index('--seconds') + 1], '2580')
        self.assertEqual(admission[-1], 'KB-p1')

    def test_receipt_chain_binds_commands_and_exact_output_to_next_input(self):
        chain = nv.append_chain([], 'fill', {'pcb': 'source'}, {'pcb': 'filled'}, ['fill'], 0)
        chain = nv.append_chain(chain, 'drc', {'pcb': 'filled'}, {'pcb': 'filled', 'drc': 'report'}, ['drc', '--severity-all'], 0)
        nv.verify_chain(chain)
        self.assertEqual(chain[0]['output_sha256']['pcb'], chain[1]['input_sha256']['pcb'])
        bad = copy.deepcopy(chain)
        bad[1]['command'].append('--refill-zones')
        with self.assertRaisesRegex(ValueError, 'hash chain'):
            nv.verify_chain(bad)
        bad = copy.deepcopy(chain)
        bad[1]['previous_record_sha256'] = None
        with self.assertRaises(ValueError):
            nv.verify_chain(bad)

    def test_every_pad_and_original_uuid_required_including_cs_terminals(self):
        graph, mapping = graph_fixture('KA')
        self.assertEqual(len(nv.validate_mapping(graph, mapping)), 7)
        for bad in (mapping[:-1], mapping + mapping[:1], [dict(r, native_pad_uuid=mapping[0]['native_pad_uuid']) for r in mapping]):
            with self.assertRaises(ValueError):
                nv.validate_mapping(graph, bad)
        bad = copy.deepcopy(mapping)
        bad[-1]['native_pad_uuid'] = str(uuid.uuid4())
        with self.assertRaisesRegex(ValueError, 'original UUID'):
            nv.validate_mapping(graph, bad)

    def test_reconciliation_retains_pad_differences_and_complete_peer_groups(self):
        graph, mapping = graph_fixture('KA')
        native_pads = [{'uuid': r['native_pad_uuid'], 'ref': r['ref'], 'pad': r['pad'], 'net': r['net']} for r in mapping]
        clusters = {p['uuid']: p['net'] + '-native' for p in native_pads}
        result = nv.reconcile(graph, mapping, native_pads, clusters)
        self.assertEqual(result['pad_count'], 7)
        self.assertEqual(result['differences'], [])
        clusters[mapping[-1]['native_pad_uuid']] = 'isolated-pad'
        result = nv.reconcile(graph, mapping, native_pads, clusters)
        difference = next(r for r in result['differences'] if r['source_id'] == mapping[-1]['source_id'])
        self.assertFalse(difference['native_pad_to_feed'])
        self.assertFalse(difference['peer_agreement'])
        self.assertEqual(len(result['native_cluster_pad_groups']['isolated-pad']), 1)
        with self.assertRaisesRegex(ValueError, 'census'):
            nv.reconcile(graph, mapping, native_pads[:-1], clusters)
        native_pads[-1]['net'] = 'AGND'
        with self.assertRaisesRegex(ValueError, 'identity/net'):
            nv.reconcile(graph, mapping, native_pads, clusters)


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.root = self.base / 'repo'
        self.here = self.root / F
        self.here.mkdir(parents=True)
        self.out = self.base / 'materialized'
        self.out.mkdir()
        self.graphs = {}
        for name in ('native_validation.py', 'staged_caps.py'):
            source = Path(__file__).with_name(name)
            if not source.exists():
                source = REPO / F / name
            shutil.copyfile(source, self.here / name)
        for name in ('run.sh', 'pin.env', 'native_resource_guard.py', 'ci_native_admission.py'):
            destination = self.root / 'scripts/kicad' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO / 'scripts/kicad' / name, destination)
        for target in nv.TARGETS:
            board, round_id = target.split('-')
            graph, mapping = graph_fixture(board)
            source = {'board': board, 'objects': [{'id': p['id'], 'kind': 'pad', 'net': p['net']} for p in graph['physical_ports']],
                      'loads': [], 'coordinate_offset_mm': [100., 50.]}
            source_path = self.out / (target + '-source.json')
            source_path.write_bytes(nv.canonical(source))
            with patch.object(nv, 'HERE', self.here):
                spec = importlib.util.spec_from_file_location('capsfixture', self.here / 'staged_caps.py')
                caps = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(caps)
                normalized = caps.materialize(source)
            normal_path = self.out / (target + '-caps.json')
            normal_path.write_bytes(nv.canonical(normalized))
            graph['input_sha256'] = {str(normal_path): nv.sha(normal_path)}
            graph_path = self.out / (target + '-graph.json')
            graph_path.write_bytes(nv.canonical(graph))
            self.graphs[target] = graph_path
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
                (self.out / (target + suffix)).write_text('SOURCE ' + target + suffix)
            outputs = {target + suffix: nv.sha(self.out / (target + suffix)) for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru', '-source.json')}
            material = {'schema': 'e16-source-materialization-v1', 'board': board, 'round': round_id,
                  'native_calls': 0, 'accepted': False, 'rail_physical_pad_map': mapping, 'output_sha256': outputs,
                  'input_sha256': {str(source_path): nv.sha(source_path)},
                  'materialized_source_objects_content_sha256': hashlib.sha256(json.dumps(source['objects'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()}
            (self.out / (target + '-materialization.json')).write_bytes(nv.canonical(material))
        self.stage = self.root / '.circuit-cache/request'

    def tearDown(self):
        self.tmp.cleanup()

    def git_read(self, command, **kwargs):
        if command[:2] == ['git', 'check-ignore']:
            return subprocess.CompletedProcess(command, 0, b'', b'')
        if command == ['git', 'rev-parse', 'HEAD']:
            return subprocess.CompletedProcess(command, 0, 'a' * 40 + '\n', '')
        raise AssertionError('unexpected process ' + repr(command))

    def prepare(self):
        with patch.object(nv, 'HERE', self.here), patch.object(nv, 'ROOT', self.root), patch.object(nv.subprocess, 'run', self.git_read):
            return nv.prepare([self.out], self.graphs, self.stage, root=self.root)

    def test_prepare_stages_all_exact_hashes_sidecars_and_executable_requests(self):
        packet = self.prepare()
        self.assertEqual(packet['native_calls'], 0)
        self.assertEqual(set(packet['requests']), set(nv.TARGETS))
        for name, digest in packet['staged_input_sha256'].items():
            self.assertEqual(nv.sha(self.stage / 'materialized' / name), digest)
        for target in nv.TARGETS:
            for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_dru'):
                self.assertEqual(nv.sha(self.stage / target / 'filled' / (target + suffix)), nv.sha(self.out / (target + suffix)))
        with self.assertRaisesRegex(ValueError, 'fresh stage'):
            self.prepare()

    def test_source_graph_epoch_mismatch_and_sidecar_tampering_refused(self):
        graph_path = self.graphs['KB-p1']
        graph = nv.read_json(graph_path)
        normalized_path = Path(next(iter(graph['input_sha256'])))
        normalized = nv.read_json(normalized_path)
        normalized['objects'].append({'id': 'unreviewed-addition', 'kind': 'segment'})
        normalized_path.write_bytes(nv.canonical(normalized))
        graph['input_sha256'][str(normalized_path)] = nv.sha(normalized_path)
        graph_path.write_bytes(nv.canonical(graph))
        with patch.object(nv, 'HERE', self.here), self.assertRaisesRegex(ValueError, 'recipe'):
            nv.collect_materialized([self.out], self.graphs)
        graph['input_sha256'][str(normalized_path)] = '0' * 64
        graph_path.write_bytes(nv.canonical(graph))
        with patch.object(nv, 'HERE', self.here), self.assertRaisesRegex(ValueError, 'graph input'):
            nv.collect_materialized([self.out], self.graphs)

    def test_execution_refuses_absent_parent_admission_before_any_command(self):
        self.prepare()
        with patch.object(nv, 'HERE', self.here), patch.object(nv, 'ROOT', self.root), \
                patch.object(nv.subprocess, 'run', self.git_read), patch.dict(os.environ, {}, clear=True), \
                self.assertRaisesRegex(ValueError, 'parent admission'):
            nv.execute(self.stage, 'KA-t2')

    def test_parent_digest_cannot_be_issued_by_prepare_or_resealed_inputs(self):
        request = self.prepare()
        env = {"GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1", "GITHUB_SHA": "a" * 40,
               "EPIC242_PARENT_ADMISSION_RUN_ID": "123", "EPIC242_PARENT_ADMISSION_SHA": "a" * 40,
               "EPIC242_REVIEWED_HOOK_SHA256": request['oracle_sha256']['scripts/kicad/run.sh']}
        with self.assertRaisesRegex(ValueError, 'parent-approved request'):
            nv.verify_authority(request, self.stage / 'request.json', env, 'a' * 40)
        env['EPIC242_PARENT_REQUEST_SHA256'] = nv.sha(self.stage / 'request.json')
        forwarded = nv.verify_authority(request, self.stage / 'request.json', env, 'a' * 40)
        self.assertEqual(forwarded[0], 'env')
        self.assertIn('GITHUB_RUN_ATTEMPT=1', forwarded)
        changed = dict(request, status='RESEALED')
        (self.stage / 'request.json').write_bytes(nv.canonical(changed))
        with self.assertRaisesRegex(ValueError, 'parent-approved request'):
            nv.verify_authority(changed, self.stage / 'request.json', env, 'a' * 40)

    def test_original_materializer_input_hashes_are_required(self):
        path = self.out / 'KA-t2-materialization.json'
        material = nv.read_json(path)
        material['input_sha256'][str(self.out / 'KA-t2-source.json')] = '0' * 64
        path.write_bytes(nv.canonical(material))
        with patch.object(nv, 'HERE', self.here), self.assertRaisesRegex(ValueError, 'materializer source input'):
            nv.collect_materialized([self.out], self.graphs)

    def test_actual_guard_provenance_rejects_caller_set_environment(self):
        env = worker_env()
        proc = self.base / 'cgroup-proc'
        cgroup = self.base / 'cgroups'
        proc.write_text('0::/unadmitted-process')
        with self.assertRaisesRegex(ValueError, 'actual admitted'):
            nv.host_guard_provenance(env, proc, cgroup)
        worker = env['EPIC242_NATIVE_WORKER']
        membership = '/epic242.slice/' + env['EPIC242_NATIVE_SLICE'] + '/epic242-' + worker + '-checks.service'
        proc.write_text('0::' + membership)
        for location, cap in ((cgroup / 'epic242.slice', 12884901888), (cgroup / 'epic242.slice' / env['EPIC242_NATIVE_SLICE'], 6442450944)):
            location.mkdir(parents=True, exist_ok=True)
            (location / 'memory.max').write_text(str(cap))
            (location / 'memory.swap.max').write_text('0')
        nv.host_guard_provenance(env, proc, cgroup)
        (cgroup / 'epic242.slice/memory.max').write_text('max')
        with self.assertRaisesRegex(ValueError, 'cap mismatch'):
            nv.host_guard_provenance(env, proc, cgroup)

    def test_native_requires_readonly_guard_gate_exact_command_and_ack(self):
        self.prepare()
        gate = self.base / 'gate'
        gate.mkdir()
        mountinfo = self.base / 'mountinfo'
        mountinfo.write_text('1 0 0:1 / /epic242-gate ro - bind none ro\n2 0 0:1 / /epic242-start.sh ro - bind none ro\n')
        cgroup = self.base / 'container-cgroup'
        cgroup.mkdir()
        (cgroup / 'memory.max').write_text('6442450944')
        (cgroup / 'memory.swap.max').write_text('0')
        env = worker_env()
        cid, token = 'f' * 64, 'gate.abcdefghijkl'
        (gate / 'container-id').write_text(cid + '\n')
        (gate / 'ack').write_text(token + ':' + cid + '\n')
        command = ['env'] + [key + '=' + env[key] for key in (*nv.GUARD_KEYS, *nv.AUTHORITY_KEYS)] + ['python3', str(F / 'native_validation.py'), 'native-fill', '--stage', '.circuit-cache/request', '--target', 'KA-t2']
        image = __import__('re').search(r"^KICAD_IMAGE='([^']+)'$", (self.root / 'scripts/kicad/pin.env').read_text(), __import__('re').M).group(1)
        request = dict(container_id=cid, token=token, worker=env['EPIC242_NATIVE_WORKER'], deadline=int(env['EPIC242_NATIVE_DEADLINE']), image=image, command=command)
        (gate / 'request.json').write_bytes(nv.canonical(request))
        with patch.object(nv, 'ROOT', self.root), patch.object(nv, 'HERE', self.here):
            nv.native_guard_provenance(env, self.stage, 'KA-t2', 'native-fill', gate, mountinfo, cgroup)
            (gate / 'ack').write_text('unsolicited')
            with self.assertRaisesRegex(ValueError, 'acknowledgement'):
                nv.native_guard_provenance(env, self.stage, 'KA-t2', 'native-fill', gate, mountinfo, cgroup)
            (gate / 'ack').write_text(token + ':' + cid + '\n')
            request['command'][-1] = 'KB-p1'
            (gate / 'request.json').write_bytes(nv.canonical(request))
            with self.assertRaisesRegex(ValueError, 'exact native command'):
                nv.native_guard_provenance(env, self.stage, 'KA-t2', 'native-fill', gate, mountinfo, cgroup)

    def test_rerun_cannot_reuse_request_attempt(self):
        self.prepare()
        env = {"GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "2", "GITHUB_SHA": "a" * 40,
               "EPIC242_PARENT_ADMISSION_RUN_ID": "123", "EPIC242_PARENT_ADMISSION_SHA": "a" * 40,
               "EPIC242_REVIEWED_HOOK_SHA256": "b" * 64}
        with patch.object(nv, 'HERE', self.here), patch.object(nv, 'ROOT', self.root), \
                patch.object(nv.subprocess, 'run', self.git_read), patch.dict(os.environ, env, clear=True), \
                self.assertRaisesRegex(ValueError, 'attempt'):
            nv.execute(self.stage, 'KA-t2')

    def test_tampered_staged_inputs_are_rejected(self):
        self.prepare()
        (self.stage / 'materialized/KA-t2/KA-t2.kicad_dru').write_text('CHANGED')
        with patch.object(nv, 'HERE', self.here), self.assertRaisesRegex(ValueError, 'staged input changed'):
            nv.load_stage(self.stage, 'KA-t2', root=self.root)


class LocalStagingTests(unittest.TestCase):
    """Real source preparation/authority functions against disposable tiny fixtures."""
    tearDown = StagingTests.tearDown
    git_read = StagingTests.git_read

    def setUp(self):
        StagingTests.setUp(self)
        for name in ('local_native_admission.py', 'native_start_gate.sh', 'operator_terminal.py'):
            shutil.copyfile(REPO / 'scripts/kicad' / name, self.root / 'scripts/kicad' / name)
        with patch.object(nv, 'ROOT', self.root):
            self.local = nv.local_admission()
        # Local fixture requests must not inherit a CI job's authority. Restore
        # every original value after this test, including when setup fails.
        clean_authority = patch.dict(os.environ, {
            key: '' for key in (*self.local.CI_KEYS, *self.local.AUTHORITY_KEYS)
        })
        clean_authority.start()
        self.addCleanup(clean_authority.stop)
        self.heavy = self.base / 'heavy.sh'
        self.heavy.write_text('fixture')
        self.patches = [patch.object(nv, 'ROOT', self.root), patch.object(nv, 'HERE', self.here),
                        patch.object(nv, 'local_admission', return_value=self.local),
                        patch.object(self.local, 'clean_head', return_value='a' * 40)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)
        original = self.local.prepare
        def prepare(*args, **kwargs):
            return original(*args, **kwargs, heavy_guard=self.heavy)
        with patch.object(nv.subprocess, 'run', self.git_read), patch.object(self.local, 'prepare', prepare):
            self.packet = nv.prepare([self.out], self.graphs, self.stage, root=self.root,
                                     local_run_id='b' * 32, run_attempt=2)
        self.target = 'KA-t2'
        self.path = self.stage / self.target / 'local-request.json'
        self.approval = self.path.with_name('operator-approval.json')

    def approved_fixture(self):
        self.local.approve(self.root, self.path, nv.sha(self.path), str(self.approval.relative_to(self.root)),
                           'test fixture', 'fixture reservation', 'fixture qualification')
        worker = self.local.read(self.path)['worker']
        return {'EPIC242_ADMISSION_MODE': 'local', 'EPIC242_LOCAL_REQUEST': str(self.path.relative_to(self.root)),
                'EPIC242_PARENT_LOCAL_REQUEST_SHA256': nv.sha(self.path),
                'EPIC242_LOCAL_APPROVAL': str(self.approval.relative_to(self.root)),
                'EPIC242_LOCAL_APPROVAL_SHA256': nv.sha(self.approval),
                'EPIC242_NATIVE_WORKER': worker, 'EPIC242_NATIVE_SLICE': 'epic242-w' + worker.encode().hex() + '.slice',
                'EPIC242_NATIVE_DEADLINE': str(int(time.time()) + 2580)}

    def test_local_preparation_all_targets_without_approval_or_github_identity(self):
        self.assertEqual(self.packet['admission_mode'], 'local')
        self.assertNotIn('github_run_attempt', self.packet)
        for target in nv.TARGETS:
            request = self.local.validate_request(self.root, self.stage / target / 'local-request.json')
            self.assertEqual(request['target'], target)
            self.assertEqual(request['seconds'], 2580)
            self.assertFalse((self.stage / target / 'operator-approval.json').exists())
        with patch.object(nv.subprocess, 'run') as launch, self.assertRaises(FileNotFoundError):
            nv.execute(self.stage, self.target)
        launch.assert_not_called()

    def test_local_authority_transport_and_target_is_exact(self):
        env = self.approved_fixture()
        nv.verify_authority(self.packet, self.stage / 'request.json', env, 'a' * 40)
        nv.verify_worker_authority(env, self.target)
        phases = nv.phase_commands(str(F / 'native_validation.py'), '.circuit-cache/request', self.target, env)
        for key in self.local.AUTHORITY_KEYS:
            self.assertIn(key + '=' + env[key], phases[0][1])
            self.assertIn(key + '=' + env[key], phases[2][1])
        self.assertFalse(any('GITHUB_' in part for part in phases[0][1]))
        with self.assertRaises(ValueError):
            nv.verify_worker_authority(env, 'KB-t2')
        for changed in (env | {'GITHUB_RUN_ID': '123'}, env | {'EPIC242_ADMISSION_MODE': 'unknown'},
                        env | {'EPIC242_NATIVE_WORKER': 'ci-1-2-e16-ka-t2'}):
            with self.assertRaises(ValueError):
                nv.verify_worker(changed)

    def test_mixed_ci_and_local_authority_is_still_rejected(self):
        with self.assertRaisesRegex(ValueError, 'mixed CI/local authority refused'):
            self.local.no_mixed_authority(self.approved_fixture() | {'GITHUB_RUN_ID': '123'})

    def test_changed_local_request_and_filled_copy_rejected_before_execution(self):
        self.approved_fixture()
        filled = self.stage / self.target / 'filled' / (self.target + '.kicad_pcb')
        filled.write_text('changed before fill')
        with patch.object(nv.subprocess, 'run') as launch, self.assertRaisesRegex(ValueError, 'sealed input'):
            nv.execute(self.stage, self.target)
        launch.assert_not_called()

    def test_native_local_context_needs_real_gate_before_trusting_host_sha(self):
        env = self.approved_fixture()
        # A worktree .git pointer is outside /work. No git command is needed in
        # the container, but real read-only gate proof is required first.
        with patch.dict(os.environ, env, clear=True), patch.object(nv.subprocess, 'run') as process, \
             patch.object(nv, 'native_guard_provenance', side_effect=ValueError('no actual gate')):
            with self.assertRaisesRegex(ValueError, 'actual gate'):
                nv.native_context(self.stage, self.target, 'native-fill')
            process.assert_not_called()
        with patch.dict(os.environ, env, clear=True), patch.object(nv.subprocess, 'run') as process, \
             patch.object(nv, 'native_guard_provenance') as proof:
            self.assertEqual(nv.native_context(self.stage, self.target, 'native-fill')[1], self.packet)
            self.assertTrue(proof.called)
            process.assert_not_called()

    def test_local_native_gate_binds_full_authority_and_readonly_ack(self):
        env = self.approved_fixture()
        gate = self.base / 'local-gate'; gate.mkdir()
        mounts = self.base / 'local-mounts'
        mounts.write_text('1 0 0:1 / /epic242-gate ro - bind none ro\n2 0 0:1 / /epic242-start.sh ro - bind none ro\n')
        cg = self.base / 'local-container'; cg.mkdir()
        (cg / 'memory.max').write_text('6442450944'); (cg / 'memory.swap.max').write_text('0')
        cid, token = 'f' * 64, 'gate.abcdefghijkl'
        (gate / 'container-id').write_text(cid); (gate / 'ack').write_text(token + ':' + cid + '\n')
        command = nv.phase_commands(str(F / 'native_validation.py'), '.circuit-cache/request', self.target, env)[0][1][2:]
        image = __import__('re').search(r"^KICAD_IMAGE='([^']+)'$", (self.root / 'scripts/kicad/pin.env').read_text(), __import__('re').M).group(1)
        entry = dict(container_id=cid, token=token, worker=env['EPIC242_NATIVE_WORKER'],
                     deadline=int(env['EPIC242_NATIVE_DEADLINE']), image=image, command=command)
        (gate / 'request.json').write_bytes(nv.canonical(entry))
        nv.native_guard_provenance(env, self.stage, self.target, 'native-fill', gate, mounts, cg)
        entry['command'] = [x for x in command if not x.startswith('EPIC242_LOCAL_APPROVAL_SHA256=')]
        (gate / 'request.json').write_bytes(nv.canonical(entry))
        with self.assertRaisesRegex(ValueError, 'exact native command'):
            nv.native_guard_provenance(env, self.stage, self.target, 'native-fill', gate, mounts, cg)

    def test_inner_authority_preserves_filled_chain_but_rejects_method_tamper(self):
        env = self.approved_fixture()
        filled = self.stage / self.target / 'filled' / (self.target + '.kicad_pcb')
        filled.write_text('filled bytes; exact chain checked by native worker')
        nv.verify_authority(self.packet, self.stage / 'request.json', env, 'a' * 40)
        (self.root / 'scripts/kicad/native_start_gate.sh').write_text('changed method')
        with self.assertRaisesRegex(ValueError, 'sealed input'):
            nv.verify_authority(self.packet, self.stage / 'request.json', env, 'a' * 40)


if __name__ == '__main__':
    unittest.main()
