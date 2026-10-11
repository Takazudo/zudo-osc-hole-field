"""Source-only tests for the exclusive lifecycle CI path."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.kicad import qualify_startup_handshake as lifecycle

SHA = 'a' * 40
HOOK = 'b' * 64
CID1 = '1' * 64
CID2 = '2' * 64


def receipt(failing=False):
    ids = (CID1, CID2)
    commands = (['kicad-cli', 'version'], ['/bin/false'] if failing else ['kicad-cli', 'version'])
    worker = 'life-123-1-' + ('fail' if failing else 'ok')
    command = ['bash', 'scripts/kicad/run.sh', '/bin/false' if failing else 'kicad-cli',
               *([] if failing else ['version'])]
    return {
        'status': 'FAIL / NOT ACCEPTED' if failing else
                  'COMMAND PASS ONLY; native acceptance requires exact complete evidence',
        'plan': {'worker': worker, 'sha': SHA, 'hook_sha256': HOOK,
                 'admission_id': 'gate-one', 'seconds': 60, 'command': command,
                 'memory_max': lifecycle.guard.CAP,
                 'aggregate_memory_max': lifecycle.guard.AGGREGATE_CAP},
        'container_admissions': {cid: {'request': {'container_id': cid, 'worker': worker,
               'token': 'gate', 'command': command}, 'ack': 'gate:' + cid}
               for cid, command in zip(ids, commands)},
        'container_memberships': {cid: {'container_id': cid, 'worker': worker,
            'cgroup': '0::/epic242.slice/epic242-w' + worker.encode().hex() + '.slice/docker.scope',
            'host_config': {'Memory': lifecycle.guard.CAP,
                            'MemorySwap': lifecycle.guard.CAP,
                            'CgroupParent': 'epic242-w' + worker.encode().hex() + '.slice'}}
            for cid in ids},
        'container_states': {cid: {'Running': False, 'Status': 'exited',
            'ExitCode': 1 if failing and cid == CID2 else 0, 'OOMKilled': False, 'Error': ''}
            for cid in ids},
        'observed_containers': list(ids), 'final_owned_state': {'workload_absent': True},
        'cleanup_failures': [], 'memory_before_cleanup': {'status': 'OBSERVED'},
        'reason': 'Docker container failed or indeterminate terminal state' if failing else None,
        'exit_code': None if failing else 0,
    }


class LifecycleQualificationTests(unittest.TestCase):
    def test_preflight_binds_exact_sha_hook_mode_and_run(self):
        env = {'REVIEWED_COMMIT': SHA, 'REVIEWED_HOOK_SHA256': HOOK,
               'GITHUB_SHA': SHA, 'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '1',
               'PARENT_ADMISSION_ID': 'gate-one', 'REQUEST_BOARD': 'osc-core',
               'CONFLICTING_MODES': 'false'}
        with patch.object(lifecycle.guard, 'run', side_effect=[SHA, '']), \
             patch.object(lifecycle.hashlib, 'sha256') as digest:
            digest.return_value.hexdigest.return_value = HOOK
            self.assertEqual(lifecycle.validate(env), (SHA, HOOK, 'gate-one', 'life-123-1'))
        for changed in ({'GITHUB_SHA': 'c' * 40}, {'REQUEST_BOARD': 'osc-jack-left'},
                        {'CONFLICTING_MODES': 'true'}, {'PARENT_ADMISSION_ID': ''},
                        {'GITHUB_RUN_ID': ''}, {'REVIEWED_HOOK_SHA256': 'c' * 64}):
            with self.subTest(changed=changed), patch.object(lifecycle.guard, 'run',
                    side_effect=[SHA, '']), patch.object(lifecycle.hashlib, 'sha256') as digest:
                digest.return_value.hexdigest.return_value = HOOK
                with self.assertRaises(ValueError): lifecycle.validate(env | changed)

    def test_commands_are_sequential_bounded_oracle_only(self):
        for failing in (False, True):
            command = lifecycle.guard_command(SHA, HOOK, 'gate-one', 'life-123-1-ok',
                                               Path('/tmp/fresh.json'), failing)
            self.assertEqual(command[command.index('--seconds') + 1], '60')
            self.assertNotIn('--harmless-fixture-image', command)
            self.assertEqual(command[-3:] if not failing else command[-2:],
                             ['scripts/kicad/run.sh', 'kicad-cli', 'version'] if not failing else
                             ['scripts/kicad/run.sh', '/bin/false'])

    def test_exact_success_and_expected_failure(self):
        self.assertEqual(lifecycle.verify_phase('success', 0, receipt(), SHA, HOOK, 'gate-one', 'life-123-1-ok')['retained_exit_codes'], [0, 0])
        self.assertEqual(lifecycle.verify_phase('intentional-failure', 1, receipt(True), SHA, HOOK, 'gate-one', 'life-123-1-fail')['retained_exit_codes'], [0, 1])

    def test_unexpected_failure_cannot_be_reclassified(self):
        for change in (
            lambda r: r.update(status='FAIL / CLEANUP BLOCKER'),
            lambda r: r.update(reason='Docker daemon unavailable'),
            lambda r: r['container_admissions'].pop(CID2),
            lambda r: r['container_memberships'].pop(CID2),
            lambda r: r['container_states'][CID2].update(ExitCode=0),
            lambda r: r['container_states'][CID1].update(ExitCode=1),
            lambda r: r['plan'].update(sha='c' * 40),
            lambda r: r['plan'].update(admission_id='wrong'),
            lambda r: r['plan'].update(seconds=300),
            lambda r: r.update(pre_cleanup_state_errors=['missing']),
            lambda r: r['container_states'][CID2].update(OOMKilled=True),
            lambda r: r['container_admissions'][CID2]['request'].update(command=['wrong']),
            lambda r: r['final_owned_state'].update(workload_absent=None),
            lambda r: r['memory_before_cleanup'].update(status='UNAVAILABLE'),
            lambda r: r.update(cleanup_failures=['survivor']),
            lambda r: r.update(watchdog={'reason': 'died'}),
        ):
            item = receipt(True)
            change(item)
            with self.subTest(item=item), self.assertRaises(ValueError):
                lifecycle.verify_phase('intentional-failure', 1, item, SHA, HOOK, 'gate-one', 'life-123-1-fail')
        with self.assertRaises(ValueError): lifecycle.verify_phase('intentional-failure', 0, receipt(True), SHA, HOOK, 'gate-one', 'life-123-1-fail')
        with self.assertRaises(ValueError): lifecycle.verify_phase('success', 1, receipt(), SHA, HOOK, 'gate-one', 'life-123-1-ok')

    def test_pre_cleanup_snapshot_records_both_terminals_without_changing_cause(self):
        worker = 'life-123-1-fail'
        slice_unit = 'epic242-w' + worker.encode().hex() + '.slice'
        evidence = {'reason': 'original failed exit', 'container_lifecycle': [],
                    'container_states': {}, 'container_admissions': {CID1: {}, CID2: {}}}

        def inspect(args, **kwargs):
            cid = args[-1]
            item = {'Id': cid, 'Config': {'Labels': {'epic242.native.worker': worker}},
                    'HostConfig': {'Memory': lifecycle.guard.CAP,
                                   'MemorySwap': lifecycle.guard.CAP, 'CgroupParent': slice_unit},
                    'State': {'Running': False, 'Status': 'exited',
                              'ExitCode': 1 if cid == CID2 else 0,
                              'OOMKilled': False, 'Error': ''}}
            return json.dumps([item])

        with patch.object(lifecycle.guard, 'gated_inventory', return_value={CID1, CID2}), \
             patch.object(lifecycle.guard, 'run', side_effect=inspect):
            errors = lifecycle.guard.snapshot_failed_containers(
                worker, '/epic242.slice/' + slice_unit, Path('/tmp/owned'), evidence)
        self.assertEqual(errors, [])
        self.assertEqual(evidence['container_states'][CID1]['ExitCode'], 0)
        self.assertEqual(evidence['container_states'][CID2]['ExitCode'], 1)
        self.assertEqual(evidence['reason'], 'original failed exit')
        with patch.object(lifecycle.guard, 'gated_inventory', return_value={CID1, CID2}), \
             patch.object(lifecycle.guard, 'run', side_effect=ValueError('daemon unavailable')):
            errors = lifecycle.guard.snapshot_failed_containers(
                worker, '/epic242.slice/' + slice_unit, Path('/tmp/owned'), evidence)
        self.assertTrue(errors)

    def test_preparation_failure_retains_negative_receipt_and_stops(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(lifecycle, 'validate',
                return_value=(SHA, HOOK, 'gate-one', 'life-123-1')), \
             patch.object(lifecycle, 'prepare_image', side_effect=ValueError('unaccounted backend')), \
             patch.object(lifecycle.subprocess, 'run') as command:
            self.assertEqual(lifecycle.execute({'RUNNER_TEMP': tmp, 'REVIEWED_COMMIT': SHA}), 1)
            command.assert_not_called()
            result = json.loads((Path(tmp) / 'epic242-startup-lifecycle/lifecycle.json').read_text())
            self.assertEqual(result['status'], 'BLOCKED / NOT QUALIFIED')
            self.assertIn('unaccounted backend', result['reason'])
            self.assertEqual(result['phases'], {})

    def test_workflow_is_exclusive_and_retains_every_result(self):
        import yaml
        workflow = yaml.load((lifecycle.ROOT / '.github/workflows/routing-benchmark.yml').read_text(),
                             Loader=yaml.BaseLoader)
        self.assertIn('lifecycle_qualification', workflow['on']['workflow_dispatch']['inputs'])
        job = workflow['jobs']['lifecycle-qualification']
        self.assertEqual(job['if'], '${{ inputs.lifecycle_qualification }}')
        for name, other in workflow['jobs'].items():
            if name != 'lifecycle-qualification':
                self.assertIn('!inputs.lifecycle_qualification', other['if'], name)
        self.assertEqual(job['runs-on'], 'ubuntu-24.04')
        self.assertIn('issue189-core-audit-task-pilot', job['concurrency']['group'])
        self.assertEqual(workflow['permissions']['contents'], 'read')
        commands = '\n'.join(step.get('run', '') for step in job['steps'])
        self.assertIn('qualify_startup_handshake.py run', commands)
        self.assertNotIn('route_shards', commands)
        self.assertNotIn('settle_only_pilot.py run', commands)
        upload = job['steps'][-1]
        self.assertEqual(upload['if'], '${{ always() }}')
        self.assertEqual(upload['with']['if-no-files-found'], 'error')
        self.assertEqual(upload['with']['retention-days'], '7')


if __name__ == '__main__':
    unittest.main()
