"""Portable discovery must not replay an archived host workspace."""
import ast
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / 'scripts/checks/run-python-tests.sh'
ARCHIVE = Path('design/architecture-278/implementation/stage17-native-x0x-001')
PORTABLE = Path('scripts/architecture278/implementation')
PARITY_TEST = PORTABLE / 'test_stage17_native_parity.py'


class DiscoveryBoundary(unittest.TestCase):
    def run_fixture(self, files):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            env = dict(os.environ)
            env.pop('PYTHONPATH', None)
            return subprocess.run(['bash', str(RUNNER)], cwd=root, env=env,
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
