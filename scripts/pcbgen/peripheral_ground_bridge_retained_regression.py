"""Exact source bridge text ownership; native DRC remains a separate gate."""
import unittest
from pathlib import Path

from scripts.pcbgen.peripheral_ground_bridge import insert


ROOT = Path(__file__).resolve().parents[2]
BRIDGE = {
    'source_xy_mm': [218, 166], 'native_xy_mm': [318, 216],
    'net': 'AGND', 'layers': ['F.Cu', 'B.Cu'],
    'diameter_mm': 0.7, 'drill_mm': 0.3,
}


class PeripheralGroundBridgeTest(unittest.TestCase):
    def test_actual_optical_board_exact_single_bridge(self):
        original = (ROOT/'boards/osc-stage-optical/osc-stage-optical-ground-prerequisite-v1.kicad_pcb').read_text()
        updated, receipt = insert(original, 'osc-stage-optical', BRIDGE)
        self.assertEqual(updated.replace(updated[updated.rfind('\t(via\n'):updated.rfind('\n)\n')+1], ''), original)
        self.assertEqual(receipt['source_bridge'], BRIDGE)
        with self.assertRaises(ValueError):
            insert(updated, 'osc-stage-optical', BRIDGE)
        bad = dict(BRIDGE, native_xy_mm=[318, 217])
        with self.assertRaises(ValueError):
            insert(original, 'osc-stage-optical', bad)


if __name__ == '__main__':
    unittest.main()
