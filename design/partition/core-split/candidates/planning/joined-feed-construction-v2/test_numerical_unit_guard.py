"""Lightweight guard scheduling tests; no shared slot or production solver launched."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import numerical_unit_guard as guard
import replay_steps as rs

PASS = 'heavy-guard: verdict=PASS exit=0 secs=1 min_mem_mb=4096 reason=-\n'


class Guard(unittest.TestCase):
    def test_verdict_requires_unique_measured_matching_success(self):
        self.assertTrue(guard.UnitGuard.verdict(PASS, 0)['passed'])
        for stderr, code in [('', 0), (PASS+PASS, 0), (PASS, 1),
                             (PASS.replace('4096', '?'), 0),
                             (PASS.replace('PASS', 'FAIL'), 0),
                             (PASS.replace('exit=0', 'exit=2'), 0)]:
            self.assertFalse(guard.UnitGuard.verdict(stderr, code)['passed'])

    def test_overrides_and_inherited_markers_refuse_before_dispatch(self):
        g = guard.UnitGuard('a'*64)
        for key in ('HEAVY_GUARD_HELD', 'HEAVY_GUARD_DIR', 'HEAVY_GUARD_MAX_RUN', 'E16_SOLVE_SCOPE'):
            with patch.dict(os.environ, {key: '1'}), self.assertRaises(SystemExit):
                g.check()
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(SystemExit):
            g.check()

    def test_wrong_guard_hash_and_missing_tools_refuse(self):
        g = guard.UnitGuard('a'*64)
        clean = {k:v for k,v in os.environ.items() if not k.startswith('HEAVY_GUARD_') and k!='E16_SOLVE_SCOPE'}
        with patch.dict(os.environ, clean, clear=True), patch.object(guard, 'sha', return_value='b'*64), self.assertRaises(SystemExit):
            g.check()
        with patch.dict(os.environ, clean, clear=True), patch.object(guard, 'sha', return_value='a'*64), patch.object(guard.shutil, 'which', return_value=None), self.assertRaises(SystemExit):
            g.check()

    def test_queue_wraps_timeout_without_overrides(self):
        g = guard.UnitGuard('a'*64)
        with patch.object(g, 'check'):
            argv = g.command(sys.executable, ['timeout', '180s', 'python', 'solver'])
        self.assertEqual(argv[:3], ['bash', str(g.path), '--'])
        self.assertEqual(argv[-4:], ['timeout', '180s', 'python', 'solver'])
        self.assertNotIn('--max-run', argv)

    def test_marker_without_guard_owner_cannot_execute_workload(self):
        g = guard.UnitGuard('a'*64)
        with patch.object(g, 'check'), patch.object(Path, 'read_text', return_value='pid=999999999 started=0 '), patch.object(guard.os, 'getppid', return_value=1), self.assertRaisesRegex(SystemExit, 'not an ancestor'):
            g.prove_owner()
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)/'never-created'
            env = {k:v for k,v in os.environ.items() if not k.startswith('HEAVY_GUARD_')}
            run = subprocess.run([sys.executable, str(HERE/'numerical_unit_guard.py'), '--inside', 'a'*64, '--', sys.executable, '-c', 'from pathlib import Path;Path('+repr(str(target))+').touch()'], env=env, capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse(target.exists())

    def test_actual_ancestor_descriptor_and_lock_required(self):
        g = guard.UnitGuard('a'*64)
        with patch.object(g, 'check'), patch.object(guard.os, 'getppid', return_value=2345), patch.object(Path, 'read_text', return_value='pid=2345 started=0 '), patch.object(Path, 'read_bytes', return_value=b'bash\0'+str(g.path).encode()+b'\0'), patch.object(guard.os.path, 'samefile', return_value=True), tempfile.TemporaryDirectory() as tmp:
            g.directory = Path(tmp); (g.directory/'slot-0.lock').touch()
            with self.assertRaisesRegex(SystemExit, 'not locked'):
                g.prove_owner()
            with patch.object(guard.fcntl, 'flock', side_effect=BlockingIOError):
                g.prove_owner()
            with patch.object(guard.os.path, 'samefile', return_value=False), self.assertRaisesRegex(SystemExit, 'descriptor'):
                g.prove_owner()

    def test_driver_passes_guard_to_every_serial_unit(self):
        import run_coupled_e16 as driver
        calls=[]
        class RecordingLedger:
            def __init__(self,out,resume,python,unit_guard):
                self.out=out;self.log=[];(out/'steps').mkdir()
                self.guard=unit_guard
            def run(self,name,*args):
                calls.append((name,self.guard.expected))
                if 'reduce' in name:
                    (self.out/'steps'/(name+'.json')).write_text(json.dumps({'stdout_tail':'{"pads": 97}'}))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);config=p/'config.json';config.write_text(json.dumps({'scenario':{'id':'fixture','ledger':'unused'},'default_depth_case':'fixture'}))
            cases=p/'cases.json';cases.write_text('{"cases":{"fixture":{}}}')
            argv=['driver','--python',sys.executable,'--finite',str(p/'finite'),'--output',str(p/'out'),'--config',str(config),'--cases',str(cases),'--net=+12V','--unit-heavy-guard-sha256','a'*64]
            with patch.object(driver.rs,'Ledger',RecordingLedger), patch.object(guard.UnitGuard,'check'), patch.object(sys,'argv',argv):driver.main()
        self.assertEqual(len(calls),8)  # service, two reductions, four chunks, coupling
        self.assertTrue(all(h=='a'*64 for _,h in calls))
        self.assertTrue(calls[2][0].startswith('KB-reduce'))
        self.assertTrue(calls[-1][0].startswith('couple'))


class FixtureGuard:
    """Only for lightweight ledger tests: never invokes the real heavy guard."""
    def binding(self): return {'test_only': True}
    def command(self, python, command): return command
    verdict = staticmethod(guard.UnitGuard.verdict)


class Ledger(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.out = Path(self.tmp.name)/'out';self.out.mkdir()
        self.script = Path(self.tmp.name)/'unit.py'; self.result = self.out/'result.txt'
        self.script.write_text('import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text("preserved")\nprint('+repr(PASS)+',file=sys.stderr,end="")\n')

    def run_unit(self, resume=False):
        ledger=rs.Ledger(self.out,resume,sys.executable,unit_guard=FixtureGuard())
        with contextlib.redirect_stdout(io.StringIO()):
            ledger.run('fixture',[self.script,self.result],[],[self.script],[self.result])
        return ledger

    def test_missing_verdict_is_failure_and_retains_raw_outputs(self):
        self.script.write_text('import sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text("preserved")\n')
        with self.assertRaises(SystemExit): self.run_unit()
        rec=json.loads((self.out/'steps/fixture.json').read_text())
        self.assertEqual(rec['process_exit_code'],0);self.assertEqual(rec['exit_code'],1)
        self.assertEqual(self.result.read_text(),'preserved')
        self.assertEqual(len(rec['stream_files']),2)

    def test_orphan_streams_are_refused_or_preserved_before_retry(self):
        (self.out/'steps').mkdir()
        stream=self.out/'steps/fixture.stderr.txt';stream.write_text('original interrupted failure')
        with self.assertRaises(SystemExit):self.run_unit()
        self.assertEqual(stream.read_text(),'original interrupted failure')
        ledger=self.run_unit(True)
        self.assertIn('partial',ledger.log[0]['rejected'])
        retained=list((self.out/'rejected').rglob('fixture.stderr.txt'))
        self.assertEqual(len(retained),1)
        self.assertEqual(retained[0].read_text(),'original interrupted failure')

    def test_resume_verifies_streams_and_preserves_rejected_evidence(self):
        self.run_unit(); self.assertTrue(self.run_unit(True).log[0]['reused'])
        (self.out/'steps/fixture.stderr.txt').write_text('tampered')
        ledger=self.run_unit(True)
        self.assertIn('guard receipt',ledger.log[0]['rejected'])
        retained=list((self.out/'rejected').rglob('fixture.stderr.txt'))
        self.assertEqual(len(retained),1);self.assertEqual(retained[0].read_text(),'tampered')


if __name__ == '__main__':unittest.main()
