"""Source-only route boundary tests; no Docker/native execution."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from scripts.kicad import settle_only_pilot as pilot


class PilotTests(unittest.TestCase):
    def test_all_other_jobs_exclude_settle(self):
        text=(pilot.ROOT/'.github/workflows/routing-benchmark.yml').read_text()
        for job in ('benchmark','adopt','local-pilot','hole-audit','mask-audit','zone-audit','qualify'):
            section=text.split('  '+job+':\n',1)[1].split('\n  ',1)[0]
            self.assertIn('!inputs.settle_only',section)
        self.assertIn('if: ${{ always() }}',text.split('  settle-only:\n',1)[1])
        self.assertIn('retention-days: 7',text.split('  settle-only:\n',1)[1])
        self.assertIn('SETTLE_PILOT: ${{ inputs.settle_pilot }}',text.split('  settle-only:\n',1)[1])
        self.assertIn('SETTLE_SECONDS: ${{ inputs.settle_seconds }}',text.split('  settle-only:\n',1)[1])
        self.assertIn('timeout-minutes: 25',text.split('  settle-only:\n',1)[1])

    def test_request_sha_hook_and_modes(self):
        env={'REVIEWED_COMMIT':'a'*40,'GITHUB_SHA':'a'*40,'REVIEWED_HOOK_SHA256':'b'*64,
             'PARENT_ADMISSION_ID':'admitted-one','REQUEST_BOARD':'osc-core','CONFLICTING_MODES':'false',
             'SETTLE_PILOT':'three-A','SETTLE_SECONDS':'300','GITHUB_RUN_ID':'38130450410','GITHUB_RUN_ATTEMPT':'1'}
        with patch.object(pilot.guard,'run',side_effect=lambda cmd: 'a'*40 if cmd[1]=='rev-parse' else ''),patch.object(pilot,'sha',return_value='b'*64):
            self.assertEqual(pilot.validate(env),('a'*40,'b'*64))
            for changes in ({'GITHUB_SHA':'c'*40},{'GITHUB_SHA':''},{'REVIEWED_COMMIT':''},{'REVIEWED_HOOK_SHA256':'c'*64},{'REQUEST_BOARD':'osc-jack-left'},{'CONFLICTING_MODES':'true'},{'PARENT_ADMISSION_ID':''},{'SETTLE_PILOT':'other'},{'GITHUB_RUN_ID':'bad/run'},{'GITHUB_RUN_ATTEMPT':'bad/run'},{'SETTLE_SECONDS':''},{'SETTLE_SECONDS':'301'},{'SETTLE_SECONDS':'601'},{'SETTLE_SECONDS':'0600'},{'SETTLE_SECONDS':'600'}):
                with self.subTest(changes=changes),self.assertRaises(ValueError):
                    pilot.validate(env|changes)
            self.assertEqual(pilot.validate(env|{'SETTLE_PILOT':'two-A','SETTLE_SECONDS':'600'}),('a'*40,'b'*64))

    def test_budget_is_exact_and_two_a_only(self):
        for name in pilot.PILOTS:
            self.assertEqual(pilot.settle_budget({'SETTLE_PILOT':name,'SETTLE_SECONDS':'300'}),300)
        self.assertEqual(pilot.settle_budget({'SETTLE_PILOT':'two-A','SETTLE_SECONDS':'600'}),600)
        for bad in ('0','1','299','301','599','601','1800','600.0',' 600','600 ',''):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                pilot.settle_budget({'SETTLE_PILOT':'two-A','SETTLE_SECONDS':bad})
        for name in pilot.PILOTS[1:]:
            with self.subTest(name=name),self.assertRaises(ValueError):
                pilot.settle_budget({'SETTLE_PILOT':name,'SETTLE_SECONDS':'600'})

    def test_all_reviewed_ids_have_seals_and_distinct_outputs(self):
        seals=json.loads((pilot.ROOT/'design/partition/core-split/candidates/pilots/source-fixture-seals.json').read_text())
        self.assertEqual(set(pilot.PILOTS),set(seals))
        paths=[pilot.output_path({'SETTLE_PILOT':name,'GITHUB_RUN_ID':'42','GITHUB_RUN_ATTEMPT':'2'}) for name in pilot.PILOTS]
        self.assertEqual(len(set(paths)),5)
        self.assertTrue(all(len(seals[name]['files_sha256'])==291 for name in pilot.PILOTS))

    def test_tree_detects_changed_missing_extra_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);file=root/'input';file.write_text('original');files={'input':pilot.sha(file)}
            pilot.verify_tree(root,files)
            file.write_text('changed')
            with self.assertRaises(ValueError):pilot.verify_tree(root,files)
            file.unlink();file.symlink_to('/etc/hosts')
            with self.assertRaises(ValueError):pilot.verify_tree(root,files)
            file.unlink()
            with self.assertRaises(ValueError):pilot.verify_tree(root,files)

    def test_probe_deadline_cannot_pass_after_budget(self):
        with patch.object(pilot.time,'monotonic',return_value=301),self.assertRaises(TimeoutError):
            pilot.remaining(300)
        with patch.object(pilot.time,'monotonic',return_value=299):
            self.assertEqual(pilot.remaining(300),1)

    def test_preparation_ceiling_floor_and_deadline(self):
        self.assertIsNone(pilot.preparation_stop(10*pilot.guard.GIB,100,1))
        for values in ((pilot.guard.FLOOR,100,1),(10*pilot.guard.GIB,pilot.guard.CAP,1),(10*pilot.guard.GIB,100,300)):
            self.assertIsNotNone(pilot.preparation_stop(*values))

    def test_backend_groups_include_containerd_and_reject_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); docker=base/'docker'; docker.mkdir()
            for name in ('memory.current','memory.events','memory.max'):(docker/name).write_text('0')
            fake=base/'process';fake.mkdir();(fake/'comm').write_text('containerd');(fake/'cgroup').write_text('0::/outside')
            with patch.object(pilot,'daemon_cgroup',return_value=(2,docker)),patch.object(pilot.guard,'run',return_value='not-found'),patch.object(Path,'iterdir',return_value=iter([fake])):
                # Non-numeric process paths are ignored; use a numeric PID fixture.
                fake.rename(base/'123');fake=base/'123'
                with patch.object(Path,'iterdir',return_value=iter([fake])),self.assertRaisesRegex(ValueError,'unaccounted'):
                    pilot.accounting_groups()

    def test_preparation_failure_retained_and_no_materialization(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(pilot,'validate',return_value=('a'*40,'b'*64)),patch.object(pilot,'prepare_image',side_effect=ValueError('daemon proof missing')),patch.object(pilot,'output_path',return_value=Path(tmp)/'absent'),patch.object(pilot.subprocess,'run') as run:
            self.assertEqual(pilot.execute({'RUNNER_TEMP':tmp,'PARENT_ADMISSION_ID':'slot-one','SETTLE_PILOT':'two-A','SETTLE_SECONDS':'600'}),1)
            receipt=json.loads((Path(tmp)/'epic242-candidate-settle-only/pilot.json').read_text())
            self.assertEqual(receipt['status'],'BLOCKED')
            self.assertEqual(receipt['pilot'],'two-A')
            self.assertEqual(receipt['native_seconds_limit'],600)
            self.assertEqual(run.call_count,1)
            self.assertIn('pip',run.call_args.args[0])

    def test_reviewed_six_hundred_seconds_reaches_guard_only_for_two_a(self):
        private=pilot.ROOT/'design/partition/core-split/candidates/pilots/generated/source-test-600-never-created'
        with tempfile.TemporaryDirectory() as tmp,patch.object(pilot,'validate',return_value=('a'*40,'b'*64)),patch.object(pilot,'prepare_image'),patch.object(pilot,'output_path',return_value=private),patch.object(pilot,'snapshot',return_value={}),patch.object(pilot,'verify_tree'),patch.object(pilot.subprocess,'run',side_effect=lambda command,**kw: subprocess.CompletedProcess(command,0)):
            env={'RUNNER_TEMP':tmp,'PARENT_ADMISSION_ID':'slot-one','SETTLE_PILOT':'two-A',
                 'SETTLE_SECONDS':'600','GITHUB_RUN_ID':'42','GITHUB_RUN_ATTEMPT':'1'}
            self.assertEqual(pilot.execute(env),0)
            receipt=json.loads((Path(tmp)/'epic242-candidate-settle-only/pilot.json').read_text())
            command=receipt['command']
            self.assertEqual(command[command.index('--seconds')+1],'600')
            self.assertEqual(receipt['native_seconds_limit'],600)
            self.assertEqual(command[command.index('--worker')+1],'settle-two-a-42-1')

if __name__=='__main__':unittest.main()
