"""Keep declared JR replay choices executable through the strict dispatch allowlist."""
import os
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[2]


class RoutingWorkflowDispatchTests(unittest.TestCase):
    def setUp(self):
        source = (ROOT / '.github/workflows/routing-benchmark.yml').read_text()
        choices = re.search(r'jr_replay:\s*\n(?:(?!      \w).+\n)*?        options: \[([^\]]+)\]', source)
        self.assertIsNotNone(choices)
        self.choices = [choice.strip() for choice in choices[1].split(',')]
        allowlist = re.search(r'case "\$JR_REPLAY" in\n.*?\besac', source, re.DOTALL)
        self.assertIsNotNone(allowlist)
        self.allowlist = allowlist[0]

    def dispatch(self, choice):
        return subprocess.run(['bash', '-c', self.allowlist], env={**os.environ, 'JR_REPLAY': choice}, capture_output=True).returncode

    def test_every_declared_jr_replay_passes_dispatch(self):
        for choice in self.choices:
            with self.subTest(choice=choice):
                self.assertEqual(self.dispatch(choice), 0)

    def test_unknown_jr_replay_is_rejected(self):
        self.assertNotEqual(self.dispatch('unknown-replay'), 0)


if __name__ == '__main__':
    unittest.main()
