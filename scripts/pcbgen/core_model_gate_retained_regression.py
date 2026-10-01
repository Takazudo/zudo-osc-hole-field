"""A populated failed native export cannot become a K electrical input."""
import unittest
import tempfile
import hashlib
from pathlib import Path
from scripts.pcbgen.core_model_gate import require_native_prerequisite,path_in_worktree,verify_native_companions,ROOT


class CoreModelGateTests(unittest.TestCase):
    def test_actual_failed_v2_is_rejected_before_modeling(self):
        cache=Path('.circuit-cache/issue38-recovery/core-feasibility-v2')
        with self.assertRaisesRegex(ValueError,'successful native rule/parity'):
            require_native_prerequisite(cache/'ground-feasibility-geometry.json',
                cache/'ground-feasibility-native-receipt.json',Path('design/partition/core-ground-feasibility/osc-core.receipt.json'))


if __name__ == '__main__':
    unittest.main()
