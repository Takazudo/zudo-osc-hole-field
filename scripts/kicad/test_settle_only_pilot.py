"""Source-only route boundary tests; no Docker/native execution."""
import json
from pathlib import Path
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

    def test_request_sha_hook_and_modes(self):
        env={'REVIEWED_COMMIT':'a'*40,'GITHUB_SHA':'a'*40,'REVIEWED_HOOK_SHA256':'b'*64,
             'PARENT_ADMISSION_ID':'admitted-one','REQUEST_BOARD':'osc-core','CONFLICTING_MODES':'false'}
        with patch.object(pilot.guard,'run',side_effect=lambda cmd: 'a'*40 if cmd[1]=='rev-parse' else ''),patch.object(pilot,'sha',return_value='b'*64):
            self.assertEqual(pilot.validate(env),('a'*40,'b'*64))
            for changes in ({'GITHUB_SHA':'c'*40},{'REVIEWED_COMMIT':''},{'REVIEWED_HOOK_SHA256':'c'*64},{'REQUEST_BOARD':'osc-jack-left'},{'CONFLICTING_MODES':'true'},{'PARENT_ADMISSION_ID':''}):
                with self.subTest(changes=changes),self.assertRaises(ValueError):
                    pilot.validate(env|changes)

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
        with tempfile.TemporaryDirectory() as tmp,patch.object(pilot,'validate',return_value=('a'*40,'b'*64)),patch.object(pilot,'prepare_image',side_effect=ValueError('daemon proof missing')),patch.object(pilot,'OUTPUT',Path(tmp)/'absent'),patch.object(pilot.subprocess,'run') as run:
            self.assertEqual(pilot.execute({'RUNNER_TEMP':tmp,'PARENT_ADMISSION_ID':'slot-one'}),1)
            receipt=json.loads((Path(tmp)/'epic242-three-a-settle-only/pilot.json').read_text())
            self.assertEqual(receipt['status'],'BLOCKED')
            self.assertEqual(run.call_count,1)
            self.assertIn('pip',run.call_args.args[0])

if __name__=='__main__':unittest.main()
