"""Preserve the pre-split checks and exercise the required gate's shell command."""
import itertools
import os
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASE = '0755535b46939c82d70703277b347bc4ebb7252a'


def jobs(source):
    return {m.group(1): m.group(2) for m in re.finditer(
        r'^  ([a-z-]+):\n(.*?)(?=^  [a-z-]+:\n|\Z)',
        source.split('\njobs:\n', 1)[1], re.M | re.S)}


class JobSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = subprocess.check_output(
            ['git', 'show', BASE + ':.github/workflows/check.yml'],
            cwd=ROOT, text=True)
        cls.after = (ROOT / '.github/workflows/check.yml').read_text()
        cls.old = jobs(cls.before)
        cls.new = jobs(cls.after)

    def test_trigger_permissions_and_unrelated_jobs_unchanged(self):
        self.assertEqual(self.before.split('\njobs:\n')[0],
                         self.after.split('\njobs:\n')[0])
        self.assertEqual(self.old['documentation'], self.new['documentation'].split(
            '  # Preserve the required check name;')[0])
        self.assertEqual(self.old['board-drc'], self.new['board-drc'])
        self.assertEqual(set(self.new), {'documentation', 'python-tests',
                                        'python-checks', 'aggregate-regeneration', 'board-drc'})

    def test_both_workers_keep_exact_setup_and_all_checks(self):
        old = self.old['python-tests']
        setup = old[old.index('    steps:'):old.index('      - name: Run Python unit tests')]
        checks = old[old.index('      - name: Run Python unit tests'):old.index(
            '      - name: Check aggregate source regeneration')]
        aggregate = old[old.index('      - name: Check aggregate source regeneration'):]
        for key, name, body in (
            ('python-checks', 'Python and native checks', checks),
            ('aggregate-regeneration', 'Aggregate source regeneration', aggregate),
        ):
            self.assertEqual(self.new[key],
                f'    name: {name}\n    runs-on: ubuntu-latest\n'
                '    timeout-minutes: 30\n\n' + setup + body)

    def test_required_gate_is_unconditional_and_checks_both_results(self):
        gate = self.new['python-tests']
        self.assertEqual(gate, '''    name: Python unit tests
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: [python-checks, aggregate-regeneration]
    if: ${{ always() }}
    steps:
      - name: Require both verification jobs to succeed
        env:
          TEST_RESULT: ${{ needs.python-checks.result }}
          REGEN_RESULT: ${{ needs.aggregate-regeneration.result }}
        run: |
          test "$TEST_RESULT" = success && test "$REGEN_RESULT" = success

''')

    def test_gate_rejects_failure_cancelled_skipped_and_missing_results(self):
        command = self.new['python-tests'].split('        run: |\n', 1)[1]
        command = '\n'.join(line[10:] for line in command.splitlines())
        states = ('success', 'failure', 'cancelled', 'skipped', '')
        for tests, regen in itertools.product(states, repeat=2):
            with self.subTest(tests=tests, regeneration=regen):
                result = subprocess.run(['bash', '-e', '-c', command],
                    env={**os.environ, 'TEST_RESULT': tests, 'REGEN_RESULT': regen})
                self.assertEqual(result.returncode == 0, tests == regen == 'success')


if __name__ == '__main__':
    unittest.main()
