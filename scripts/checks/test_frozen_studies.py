"""Frozen-study pins are immutable, parent-bound and replay real assertions."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.checks import frozen_studies as fs

PASS = 'import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n'


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


class FrozenStudies(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        git(self.root, 'init', '-q')
        git(self.root, 'config', 'user.email', 'fixture@example.invalid')
        git(self.root, 'config', 'user.name', 'fixture')
        (self.root / 'study').mkdir()
        (self.root / 'study/test_study.py').write_text(PASS)
        (self.root / 'source.txt').write_text('studied\n')
        git(self.root, 'add', '.')
        git(self.root, 'commit', '-qm', 'study')
        self.pin = git(self.root, 'rev-parse', 'HEAD')
        (self.root / 'source.txt').write_text('adopted change\n')
        git(self.root, 'commit', '-qam', 'adopt')
        self.later = git(self.root, 'rev-parse', 'HEAD')

    def tearDown(self):
        self.temp.cleanup()

    def entry(self, **change):
        return {'path': 'study/test_study.py', 'commit': self.pin, 'superseded_by': self.later,
                'reason': 'fixture', **change}

    def test_replay_runs_the_pinned_module(self):
        self.assertEqual(fs.replay([self.entry()], self.root), 1)

    def test_edited_test_bytes_are_rejected(self):
        (self.root / 'study/test_study.py').write_text(PASS + '# edited\n')
        with self.assertRaisesRegex(ValueError, 'differ from their frozen commit'):
            fs.verify(self.entry(), self.root)

    def test_pin_must_be_first_parent_of_superseding_commit(self):
        (self.root / 'source.txt').write_text('another\n')
        git(self.root, 'commit', '-qam', 'later')
        newest = git(self.root, 'rev-parse', 'HEAD')
        with self.assertRaisesRegex(ValueError, 'first parent'):
            fs.verify(self.entry(superseded_by=newest), self.root)

    def test_abbreviated_commit_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'full commit'):
            fs.verify(self.entry(commit=self.pin[:12]), self.root)

    def test_failing_pinned_assertion_still_fails(self):
        (self.root / 'study/test_study.py').write_text(PASS.replace('assertTrue(True)', 'fail("kept")'))
        git(self.root, 'commit', '-qam', 'failing study')
        pin = git(self.root, 'rev-parse', 'HEAD')
        (self.root / 'source.txt').write_text('adopted again\n')
        git(self.root, 'commit', '-qam', 'adopt again')
        entry = self.entry(commit=pin, superseded_by=git(self.root, 'rev-parse', 'HEAD'))
        with self.assertRaises(subprocess.CalledProcessError):
            fs.replay([entry], self.root)

    def test_registry_requires_reason_and_unique_paths(self):
        path = self.root / 'registry.json'
        path.write_text(json.dumps({'studies': [self.entry(reason='')]}))
        with self.assertRaisesRegex(ValueError, 'reason'):
            fs.load(path)
        path.write_text(json.dumps({'studies': [self.entry(), self.entry()]}))
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            fs.load(path)

    def test_current_discovery_excludes_only_pinned_modules(self):
        (self.root / 'study/test_current.py').write_text(PASS)
        loader = fs.CurrentLoader({(self.root / 'study/test_study.py').resolve()})
        suite = loader.discover(str(self.root / 'study'), top_level_dir=str(self.root / 'study'))
        self.assertEqual(suite.countTestCases(), 1)

    def test_repository_registry_is_bound(self):
        for entry in fs.load():
            fs.verify(entry)


if __name__ == '__main__':
    unittest.main()
