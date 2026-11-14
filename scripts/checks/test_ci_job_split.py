"""Preserve the pre-split checks and exercise the required gate's shell command."""
import itertools
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BASE = '0755535b46939c82d70703277b347bc4ebb7252a'
BUILD_STEP = '      - name: Build documentation site\n'
WIND_AUDIT_STEP = (
    '      - name: Audit zudo-wind utility candidates\n'
    '        run: pnpm --dir doc exec zfb wind audit --project-root . --fail-on error\n\n')
UNIT_STEP = '      - name: Run Python unit tests\n'
UNIT_COMMAND = '        run: bash scripts/checks/run-python-tests.sh\n'
CURRENT_COMMAND = '        run: bash scripts/checks/run-python-tests.sh current\n'
REPLAY_STEP = (
    '      - name: Replay superseded studies at their pinned commits\n'
    '        run: bash scripts/checks/run-python-tests.sh frozen\n\n')
# Records every python3 invocation instead of running tests, so the runner's
# routing can be compared on the real tree in seconds.
STAND_IN = '''#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$STAND_IN_LOG"
if [[ "${2:-}" == replay ]]; then
  echo 'Ran 3 tests in frozen study worktrees'
else
  echo 'Ran 1 test in 0.000s'
fi
'''


def jobs(source):
    return {m.group(1): m.group(2) for m in re.finditer(
        r'^  ([a-z-]+):\n(.*?)(?=^  [a-z-]+:\n|\Z)',
        source.split('\njobs:\n', 1)[1], re.M | re.S)}


def header(name):
    return f'    name: {name}\n    runs-on: ubuntu-latest\n    timeout-minutes: 30\n\n'


def run_command(step):
    return shlex.split(step.split('        run: ', 1)[1])


class JobSplitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = subprocess.check_output(
            ['git', 'show', BASE + ':.github/workflows/check.yml'],
            cwd=ROOT, text=True)
        cls.after = (ROOT / '.github/workflows/check.yml').read_text()
        cls.old = jobs(cls.before)
        cls.new = jobs(cls.after)
        old = cls.old['python-tests']
        cls.setup = old[old.index('    steps:'):old.index(UNIT_STEP)]
        cls.checks = old[old.index(UNIT_STEP):old.index(
            '      - name: Check aggregate source regeneration')]
        cls.aggregate = old[old.index('      - name: Check aggregate source regeneration'):]

    def test_trigger_permissions_and_unrelated_jobs_unchanged(self):
        self.assertEqual(self.before.split('\njobs:\n')[0],
                         self.after.split('\njobs:\n')[0])
        # The documentation job is the pre-split job plus exactly one reviewed
        # addition: the zudo-wind candidate audit introduced with the
        # zudo-circuit-doc 0.3.0 / zfb 5.2.2 host migration (#154). Any other
        # change to that job still fails here.
        self.assertIn(BUILD_STEP, self.old['documentation'])
        expected = self.old['documentation'].replace(BUILD_STEP, WIND_AUDIT_STEP + BUILD_STEP, 1)
        self.assertEqual(expected, self.new['documentation'].split(
            '  # Preserve the required check name;')[0])
        self.assertEqual(self.old['board-drc'], self.new['board-drc'])
        self.assertEqual(set(self.new), {'documentation', 'python-tests', 'python-checks',
                                         'frozen-replay', 'aggregate-regeneration', 'board-drc'})

    def test_all_workers_keep_exact_setup_and_all_checks(self):
        # The pre-split unit-test command appears exactly once and is the only
        # line of the checks that the split replaces.
        self.assertEqual(self.checks.count(UNIT_COMMAND), 1)
        self.assertEqual(self.checks.index(UNIT_COMMAND), len(UNIT_STEP))
        current_checks = self.checks.replace(UNIT_COMMAND, CURRENT_COMMAND, 1)
        for key, name, body in (
            ('python-checks', 'Python and native checks', current_checks),
            ('frozen-replay', 'Superseded study replay', REPLAY_STEP),
            ('aggregate-regeneration', 'Aggregate source regeneration', self.aggregate),
        ):
            with self.subTest(job=key):
                self.assertEqual(self.new[key], header(name) + self.setup + body)

    def test_two_unit_commands_cover_the_pre_split_command(self):
        self.assertNotIn(UNIT_COMMAND, self.after)
        self.assertEqual(self.after.count(CURRENT_COMMAND), 1)
        self.assertEqual(self.after.count(REPLAY_STEP), 1)
        commands = {mode: run_command(step) for mode, step in (
            ('all', UNIT_COMMAND), ('current', CURRENT_COMMAND), ('frozen', REPLAY_STEP))}
        with tempfile.TemporaryDirectory() as directory:
            stand_in = Path(directory) / 'python3'
            stand_in.write_text(STAND_IN)
            stand_in.chmod(0o755)
            calls, outputs = {}, {}
            for mode, command in commands.items():
                log = Path(directory) / (mode + '.log')
                log.write_text('')
                env = {**os.environ, 'PATH': f'{directory}:{os.environ["PATH"]}',
                       'STAND_IN_LOG': str(log)}
                env.pop('PYTHONPATH', None)
                result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                        capture_output=True, timeout=300)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                calls[mode] = log.read_text().splitlines()
                outputs[mode] = result.stdout.splitlines()
        replay = 'scripts/checks/frozen_studies.py replay'
        self.assertEqual(calls['frozen'], [replay])
        self.assertNotIn(replay, calls['current'])
        self.assertEqual(calls['all'].count(replay), 1)
        visited = [call for call in calls['all'] if call != replay]
        self.assertGreater(len(visited), 0)
        self.assertEqual(calls['current'], visited)
        self.assertEqual(sorted(calls['current'] + calls['frozen']), sorted(calls['all']))
        discovered = len(visited)
        self.assertIn(f'Python unit tests: {discovered + 3} tests ran.', outputs['all'])
        self.assertIn(f'Current-tree Python unit tests: {discovered} tests ran.',
                      outputs['current'])
        self.assertIn('Superseded study replay: 3 tests ran.', outputs['frozen'])
        # Every line of the pre-split output except its total appears in exactly
        # one of the two split outputs.
        def body(lines):
            return [line for line in lines if not re.search(r': \d+ tests ran\.$', line)]
        self.assertEqual(sorted(body(outputs['current']) + body(outputs['frozen'])),
                         sorted(body(outputs['all'])))

    def test_required_gate_is_unconditional_and_checks_all_three_results(self):
        gate = self.new['python-tests']
        self.assertEqual(gate, '''    name: Python unit tests
    runs-on: ubuntu-latest
    timeout-minutes: 30
    needs: [python-checks, frozen-replay, aggregate-regeneration]
    if: ${{ always() }}
    steps:
      - name: Require all three verification jobs to succeed
        env:
          TEST_RESULT: ${{ needs.python-checks.result }}
          FROZEN_RESULT: ${{ needs.frozen-replay.result }}
          REGEN_RESULT: ${{ needs.aggregate-regeneration.result }}
        run: |
          test "$TEST_RESULT" = success && test "$FROZEN_RESULT" = success && test "$REGEN_RESULT" = success

''')

    def test_gate_rejects_failure_cancelled_skipped_and_missing_results(self):
        command = self.new['python-tests'].split('        run: |\n', 1)[1]
        command = '\n'.join(line[10:] for line in command.splitlines())
        states = ('success', 'failure', 'cancelled', 'skipped', '')
        triples = list(itertools.product(states, repeat=3))
        self.assertEqual(len(triples), 125)
        for tests, frozen, regen in triples:
            with self.subTest(tests=tests, frozen=frozen, regeneration=regen):
                result = subprocess.run(['bash', '-e', '-c', command],
                    env={**os.environ, 'TEST_RESULT': tests, 'FROZEN_RESULT': frozen,
                         'REGEN_RESULT': regen})
                self.assertEqual(result.returncode == 0,
                                 tests == frozen == regen == 'success')


if __name__ == '__main__':
    unittest.main()
