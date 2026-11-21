"""MC04-S6 revision 4: the c6 rebind changed only the geometry and output pins (no KiCad, no network)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links_gate as lg  # noqa: E402
import links_gate_c6 as c6  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s6-c6-rebind-check-20261122.json'


class C6Rebind(unittest.TestCase):
    def test_signal_and_positions_pins_are_the_retained_ones(self):
        self.assertEqual(c6.SOURCE_SIGNAL_SHA256, 'baa834876861bea8245c223950e3405ec7d9223f327f99f38fc3c5a59da128c4')
        self.assertEqual(c6.SOURCE_POSITIONS_SHA256, 'c95a3dfbd397cfe3785e6e8f90037105a86ee01a9460fd98d7fab0b932f57ebd')
        rec = json.loads(RECORD.read_text())
        self.assertEqual(rec['old_source_pins']['signal'], c6.SOURCE_SIGNAL_SHA256)
        self.assertEqual(rec['old_source_pins']['positions'], c6.SOURCE_POSITIONS_SHA256)
        self.assertEqual(rec['new_source_pins']['signal'], c6.SOURCE_SIGNAL_SHA256)
        self.assertEqual(rec['new_source_pins']['positions'], c6.SOURCE_POSITIONS_SHA256)

    def test_rebound_pins_are_the_recorded_rebind(self):
        rec = json.loads(RECORD.read_text())
        self.assertEqual(c6.SOURCE_GEOMETRY_SHA256, rec['new_source_pins']['geometry'])
        self.assertEqual(c6.OUTPUT_LINKS_SHA256, rec['new_output_links_sha256'])
        self.assertTrue(rec['riders_identical'])

    def test_committed_gate_record_is_the_c6_output(self):
        doc = json.loads(lg.LINK_GATE.read_text())
        self.assertTrue(c6.valid_record(doc))
        self.assertEqual(doc['c6']['signal_sha256'], c6.SOURCE_SIGNAL_SHA256)
        self.assertEqual(c6.digest([x['positions'] for x in doc['links']]) != '', True)


if __name__ == '__main__':
    unittest.main()
