"""Git-backed regression coverage for explicit frozen/current execution."""
import io
from pathlib import Path
import subprocess
import tempfile
import unittest

import architecture_history as history


class HistoricalContext(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.git('config', 'user.name', 'Fixture')
        self.module = self.root / history.DIRECTORY / 'test_history.py'
        self.module.parent.mkdir(parents=True)
        self.module.write_text(
            'from pathlib import Path\nimport unittest\n'
            'class Original(unittest.TestCase):\n'
            ' def test_original(self):\n'
            '  self.assertEqual((Path(__file__).resolve().parents[3]/"evidence.txt").read_text(), "retained")\n'
            '  self.assertEqual((Path(__file__).resolve().parents[3]/"current.txt").read_text(), "old context")\n')
        for name, value in [('evidence.txt', 'retained'), ('current.txt', 'old context'),
                            ('adapter.txt', 'entrypoint')]:
            (self.root / name).write_text(value)
        self.checkpoint = self.commit()
        (self.root / 'current.txt').write_text('new context')
        self.base = self.commit()

    def git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.root, text=True).strip()

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        return self.git('rev-parse', 'HEAD')

    def verify(self, commit=None, modules=('test_history.py',)):
        history.verify_binding(self.root, commit or self.checkpoint, modules,
                               self.base, ('current.txt',), ('adapter.txt',))

    def assert_clean_worktrees(self):
        self.assertEqual(self.git('worktree', 'list', '--porcelain').count('worktree '), 1)

    def test_original_assertions_execute_in_original_context(self):
        self.verify()
        self.assertEqual(history.replay(self.root, self.checkpoint, ('test_history.py',)), 1)
        self.assertEqual((self.root / 'current.txt').read_text(), 'new context')
        self.assert_clean_worktrees()

    def test_dirty_evidence_rejected(self):
        (self.root / 'evidence.txt').write_text('altered')
        with self.assertRaisesRegex(ValueError, 'checkpoint bytes changed'):
            self.verify()

    def test_missing_evidence_rejected(self):
        (self.root / 'evidence.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'checkpoint bytes changed'):
            self.verify()

    def test_renamed_evidence_rejected(self):
        self.git('mv', 'evidence.txt', 'renamed.txt')
        with self.assertRaisesRegex(ValueError, 'checkpoint bytes changed'):
            self.verify()

    def test_redirected_evidence_rejected(self):
        path = self.root / 'evidence.txt'
        path.unlink()
        path.symlink_to('current.txt')
        with self.assertRaisesRegex(ValueError, 'checkpoint bytes changed'):
            self.verify()

    def test_current_context_exception_is_pinned(self):
        (self.root / 'current.txt').write_text('unreviewed change')
        with self.assertRaisesRegex(ValueError, 'Current-context binding changed'):
            self.verify()

    def test_changed_historical_assertion_rejected(self):
        self.module.write_text('')
        with self.assertRaisesRegex(ValueError, 'checkpoint bytes changed'):
            self.verify()

    def test_missing_mapped_module_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Missing or redirected'):
            self.verify(modules=('test_missing.py',))

    def test_missing_commit_rejected(self):
        with self.assertRaises(subprocess.CalledProcessError):
            self.verify(commit='a' * 40)

    def test_frozen_assertion_failure_propagates_and_cleans_up(self):
        self.module.write_text('import unittest\nclass Broken(unittest.TestCase):\n'
                               ' def test_failure(self): self.fail("retained failure")\n')
        checkpoint = self.commit()
        with self.assertRaises(subprocess.CalledProcessError):
            history.replay(self.root, checkpoint, ('test_history.py',))
        self.assert_clean_worktrees()

    def test_empty_checkpoint_suite_is_not_a_pass(self):
        self.module.write_text('# No executed assertions\n')
        checkpoint = self.commit()
        with self.assertRaises((ValueError, subprocess.CalledProcessError)) as caught:
            history.replay(self.root, checkpoint, ('test_history.py',))
        if isinstance(caught.exception, subprocess.CalledProcessError):
            self.assertEqual(caught.exception.returncode, 5)  # unittest's empty-suite exit
        else:
            self.assertIn('executed test count', str(caught.exception))
        self.assert_clean_worktrees()

    def test_new_tests_run_in_current_context_and_fail_normally(self):
        live = self.module.parent / 'test_new_current.py'
        live.write_text('import unittest\nclass Live(unittest.TestCase):\n'
                        ' def test_current_failure(self): self.fail("current failure")\n')
        self.verify()  # New files are not historical evidence.
        suite = history.CurrentLoader({'test_history.py'}).discover(str(self.module.parent))
        result = unittest.TextTestRunner(stream=io.StringIO()).run(suite)
        self.assertEqual(result.testsRun, 1)
        self.assertEqual(len(result.failures), 1)
        self.assertIn('current failure', result.failures[0][1])


if __name__ == '__main__':
    unittest.main()
