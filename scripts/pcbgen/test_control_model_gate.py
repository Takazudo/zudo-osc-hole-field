import json
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.control_model_gate import require_native_prerequisite, resolve, ROOT


class ControlModelGateTests(unittest.TestCase):
    def test_zero_error_bare_and_failed_full_receipts_cannot_enter(self):
        (ROOT/'.circuit-cache').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache') as directory:
            directory = Path(directory)
            receipt = directory/'native-receipt.json'
            for content in (
                {'stage': 'bare_source_planning', 'board_id': 'osc-control',
                 'rule_error_count': 0, 'schematic_parity_count': 0, 'model_entry_allowed': False},
                {'board_id': 'osc-control', 'native_model_prerequisite_passed': False,
                 'rule_error_count': 1, 'schematic_parity_count': 0},
            ):
                receipt.write_text(json.dumps(content))
                with self.subTest(content=content), self.assertRaisesRegex(ValueError, 'successful full native'):
                    require_native_prerequisite(directory/'absent-geometry.json', receipt, directory/'absent-manifest.json')

    def test_native_container_paths_are_confined_to_actual_worktree(self):
        self.assertEqual(resolve('/work/design/boards/osc-control.json'), ROOT/'design/boards/osc-control.json')
        with self.assertRaisesRegex(ValueError, 'outside'):
            resolve('/work/../other/receipt.json')
        with self.assertRaisesRegex(ValueError, 'outside'):
            resolve('/tmp/unrelated/receipt.json')


if __name__ == '__main__':
    unittest.main()
