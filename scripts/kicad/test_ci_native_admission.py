"""Admission boundary tests; no Docker, systemd or native command is invoked."""
import argparse
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('admission', Path(__file__).with_name('ci_native_admission.py'))
admission = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admission)

SHA = 'a' * 40
DIGEST = 'b' * 64


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.env = {'GITHUB_RUN_ID': '123', 'GITHUB_RUN_ATTEMPT': '2', 'GITHUB_SHA': SHA,
                    'EPIC242_PARENT_ADMISSION_RUN_ID': '123', 'EPIC242_PARENT_ADMISSION_SHA': SHA,
                    'EPIC242_REVIEWED_HOOK_SHA256': DIGEST}
        self.args = argparse.Namespace(phase='python', board=None, seconds=1680,
                                       evidence='/tmp/native-evidence.json', command=['bash', 'check.sh'])

    def test_exact_admission_builds_guard_command(self):
        command = admission.admitted_command(self.env, SHA, self.args)
        self.assertIn('ci-123-2-python', command)
        self.assertIn('--hook-sha256', command)
        self.assertEqual(command[-2:], ['bash', 'check.sh'])

    def test_missing_and_stale_run_id_refused(self):
        for admitted_id in ('', '122'):
            with self.subTest(admitted_id=admitted_id), self.assertRaisesRegex(ValueError, 'run ID'):
                admission.admitted_command(self.env | {'EPIC242_PARENT_ADMISSION_RUN_ID': admitted_id}, SHA, self.args)

    def test_missing_and_wrong_sha_or_hook_refused(self):
        for env, head in ((self.env | {'EPIC242_PARENT_ADMISSION_SHA': ''}, SHA),
                          (self.env | {'EPIC242_PARENT_ADMISSION_SHA': 'c' * 40}, SHA),
                          (self.env, 'd' * 40)):
            with self.subTest(env=env, head=head), self.assertRaisesRegex(ValueError, 'SHA'):
                admission.admitted_command(env, head, self.args)
        with self.assertRaisesRegex(ValueError, 'hook'):
            admission.admitted_command(self.env | {'EPIC242_REVIEWED_HOOK_SHA256': ''}, SHA, self.args)

    def test_board_identity_and_exact_deadline(self):
        board = argparse.Namespace(phase='board', board='osc-core', seconds=2580,
                                   evidence='/tmp/native-evidence.json', command=['bash', 'board.sh'])
        self.assertIn('ci-123-2-osc-core', admission.admitted_command(self.env, SHA, board))
        board.seconds = 2700
        with self.assertRaisesRegex(ValueError, '43 minutes'):
            admission.admitted_command(self.env, SHA, board)


if __name__ == '__main__':
    unittest.main()
