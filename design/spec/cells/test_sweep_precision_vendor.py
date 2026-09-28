"""The previous failing network must make the actual model check fail."""
import subprocess
import unittest

from ._builder import ROOT
from .sweep_precision_vendor import model, verdict


class PrecisionVendorSweepGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        model()

    def test_original_network_returns_nonzero_for_supported_failure(self):
        result = subprocess.run(
            ["python3", "-m", "design.spec.cells.sweep_precision_vendor", "--fixture-original", "--offline"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("0/1 pass; 1 fail", result.stdout)

    def test_unrounded_thresholds_are_strict(self):
        case = {"overshoot_percent": 10.00001, "positive_error_mV": 0,
                "negative_error_mV": 0, "positive_late_ripple_mV": 0,
                "negative_late_ripple_mV": 0}
        self.assertEqual(verdict(case), ["overshoot > 10%"])


if __name__ == "__main__":
    unittest.main()
