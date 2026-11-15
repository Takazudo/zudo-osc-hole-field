"""Portable discovery must not replay an archived host workspace."""
import ast
import os
import re
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'scripts/checks/run-python-tests.sh'
ARCHIVE = Path('design/architecture-278/implementation/stage17-native-x0x-001')
PORTABLE = Path('scripts/architecture278/implementation')
PARITY_TEST = PORTABLE / 'test_stage17_native_parity.py'


FROZEN = Path('scripts/checks/frozen_studies.py')
# Pre-split runner, used to prove that no argument still behaves exactly as before.
PRE_SPLIT = '8020a3cbdbd1ffe4114b274d46bbb9fdd835e946'
TEST = 'import unittest\nclass Check(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n'
# Stands in for the registry script: replay reports a fixed count, discover runs the folder.
FAKE_FROZEN = '''import subprocess, sys
if sys.argv[1:] == ["replay"]:
    print("REPLAYED pinned studies")
    print("Ran %s tests in frozen study worktrees" % REPLAY_COUNT)
    sys.exit(0)
if sys.argv[1:2] == ["discover"] and len(sys.argv) == 3:
    sys.exit(subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", sys.argv[2],
                              "-p", "test_*.py"]))
sys.exit("unexpected arguments")
'''


def normalized(result):
    # Unittest timings and the per-run temporary root are the only variable text.
    def clean(text):
        text = re.sub(r'/[^\s"\']*/osc-runner-fixture-[^/\s"\']+', '<root>', text)
        return re.sub(r' in \d+\.\d+s', ' in <time>', text)
    return result.returncode, clean(result.stdout), clean(result.stderr)


def fake_frozen(count=2):
    return 'REPLAY_COUNT = %d\n' % count + FAKE_FROZEN


class DiscoveryBoundary(unittest.TestCase):
    def run_fixture(self, files, *args, runner=None):
        with tempfile.TemporaryDirectory(prefix='osc-runner-fixture-') as directory:
            root = Path(directory)
            # This fixture tests shell routing; real checkpoint bindings have
            # separate Git-backed tests in test_architecture_history.py.
            files = {Path('scripts/checks/architecture_history.py'):
                     'import subprocess,sys\n'
                     'sys.exit(subprocess.call([sys.executable,"-m","unittest","discover",'
                     '"-s","scripts/architecture278/implementation"]))\n', **files}
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            env = dict(os.environ)
            env.pop('PYTHONPATH', None)
            if runner is not None:
                (root / 'pre-split-runner.sh').write_text(runner)
            script = str(root / 'pre-split-runner.sh') if runner is not None else str(RUNNER)
            return subprocess.run(['bash', script, *args], cwd=root, env=env,
                                  text=True, capture_output=True, timeout=30)

    def test_archive_is_not_imported_but_other_design_tests_run(self):
        test = 'import unittest\nclass Check(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n'
        result = self.run_fixture({
            ARCHIVE / 'test_native_parity.py': 'raise RuntimeError("archived host snapshot imported")\n',
            PARITY_TEST: test,
            Path('design/other/test_other.py'): test,
        })
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('NOT RUN: frozen host harness', result.stdout)
        self.assertIn('Discovering tests under design/other/', result.stdout)
        self.assertIn('Python unit tests: 2 tests ran.', result.stdout)

    def test_missing_portable_replacement_fails(self):
        result = self.run_fixture({ARCHIVE / 'test_native_parity.py': ''})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing portable replacement', result.stderr)

    def test_import_errors_outside_archive_still_fail(self):
        result = self.run_fixture({Path('design/other/test_broken.py'):
                                   'import deliberately_missing_discovery_dependency\n'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ModuleNotFoundError', result.stderr)

    def test_assertion_failures_still_fail(self):
        result = self.run_fixture({Path('scripts/tests/test_bad.py'):
            'import unittest\nclass Check(unittest.TestCase):\n def test_bad(self): self.fail("kept failure")\n'})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('kept failure', result.stderr)

    def test_empty_roots_still_report_zero(self):
        result = self.run_fixture({Path('scripts/placeholder.txt'): ''})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('0 tests ran', result.stdout)

    def split_fixture(self, count=2):
        return {
            FROZEN: fake_frozen(count),
            ARCHIVE / 'test_native_parity.py': 'raise RuntimeError("archived host snapshot imported")\n',
            PARITY_TEST: TEST,
            Path('design/other/test_other.py'): TEST,
            Path('scripts/tests/test_more.py'): TEST,
        }

    def test_current_discovers_without_replay(self):
        result = self.run_fixture(self.split_fixture(), 'current')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('REPLAYED', result.stdout)
        self.assertNotIn('Replaying superseded studies', result.stdout)
        self.assertIn('NOT RUN: frozen host harness', result.stdout)
        self.assertIn('Discovering tests under design/other/', result.stdout)
        self.assertIn('Current-tree Python unit tests: 3 tests ran.', result.stdout)
        self.assertIn('NOT RUN: retained-artifact integration', result.stdout)

    def test_frozen_replays_and_discovers_nothing(self):
        result = self.run_fixture(self.split_fixture(), 'frozen')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('Replaying superseded studies at their pinned commits', result.stdout)
        self.assertIn('REPLAYED', result.stdout)
        self.assertNotIn('Discovering tests', result.stdout)
        self.assertNotIn('NOT RUN', result.stdout)
        self.assertIn('Superseded study replay: 2 tests ran.', result.stdout)

    def test_split_counts_add_up_to_all(self):
        def total(*args):
            result = self.run_fixture(self.split_fixture(), *args)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            return int(re.search(r'^[^:\n]+: (\d+) tests ran\.$', result.stdout, re.M).group(1))
        self.assertEqual(total('all'), 5)
        self.assertEqual(total('current') + total('frozen'), total('all'))
        self.assertEqual(total(), total('all'))

    def test_unknown_or_extra_arguments_fail(self):
        for args in (('bogus',), ('current', 'frozen'), ('',)):
            with self.subTest(args=args):
                result = self.run_fixture(self.split_fixture(), *args)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn('Usage: bash scripts/checks/run-python-tests.sh', result.stderr)
                self.assertNotIn('tests ran', result.stdout)

    def test_frozen_without_registry_fails(self):
        files = self.split_fixture()
        del files[FROZEN]
        result = self.run_fixture(files, 'frozen')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing superseded study registry script', result.stderr)
        self.assertNotIn('tests ran', result.stdout)

    def test_frozen_with_zero_replayed_tests_fails(self):
        result = self.run_fixture(self.split_fixture(count=0), 'frozen')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('no executed tests', result.stderr)

    def test_no_argument_behaves_as_before(self):
        runner = subprocess.check_output(
            ['git', 'show', PRE_SPLIT + ':scripts/checks/run-python-tests.sh'], cwd=ROOT, text=True)
        fixtures = (self.split_fixture(), {Path('scripts/placeholder.txt'): ''},
                    {Path('design/other/test_broken.py'): 'import missing_discovery_dependency\n'},
                    {k: v for k, v in self.split_fixture().items() if k != FROZEN})
        for files in fixtures:
            with self.subTest(files=sorted(map(str, files))):
                before = self.run_fixture(files, runner=runner)
                for args in ((), ('all',)):
                    after = self.run_fixture(files, *args)
                    self.assertEqual(normalized(after), normalized(before))

    def test_portable_parity_preserves_archived_comparator(self):
        self.assertEqual((ROOT / ARCHIVE / 'native_parity.py').read_bytes(),
                         (ROOT / PORTABLE / 'stage17_native_parity.py').read_bytes())

    def test_all_archived_mutation_assertions_are_preserved(self):
        archived = ast.parse((ROOT / ARCHIVE / 'test_native_parity.py').read_text())
        portable = ast.parse((ROOT / PARITY_TEST).read_text())
        # Only the import name and repository locator differ from the snapshot.
        for node in archived.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'native_parity':
                        alias.name = 'stage17_native_parity'
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == 'REPO' for target in node.targets
            ):
                node.value = ast.parse('Path(__file__).resolve().parents[3]', mode='eval').body
        self.assertEqual(ast.dump(archived), ast.dump(portable))
        cases = [node for node in ast.walk(portable)
                 if isinstance(node, ast.FunctionDef) and node.name.startswith('test_')]
        self.assertEqual(len(cases), 12)


if __name__ == '__main__':
    unittest.main()
