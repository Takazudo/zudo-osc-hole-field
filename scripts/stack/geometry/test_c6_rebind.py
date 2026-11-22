"""MC04-S6 revision 4 and MC04-S7 revision 2: each c6 rebind changed only the geometry and output pins. MC04-S7
revision 11: a fresh c6 attempt on the stage 7 gate re-pins the signal and positions too, and c6's own eight links keep
their output and riders (no KiCad, no network)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links_gate as lg  # noqa: E402
import links_gate_c6 as c6  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
RECORD = ROOT / 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-c6-rebind-check-20261122.json'
R11 = ROOT / 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-r11-c6-check-20261122.json'
R13 = ROOT / 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s7-r13-c6-rebind-check-20261122.json'


class C6Rebind(unittest.TestCase):
    def test_revision_2_rebind_kept_the_signal_and_positions_pins(self):
        rec = json.loads(RECORD.read_text())
        self.assertEqual(rec['old_source_pins']['signal'], rec['new_source_pins']['signal'])
        self.assertEqual(rec['old_source_pins']['positions'], rec['new_source_pins']['positions'])
        self.assertTrue(rec['riders_identical'])

    def test_revision_11_attempt_follows_revision_2(self):
        r2, r11 = json.loads(RECORD.read_text()), json.loads(R11.read_text())
        self.assertEqual(r11['old_source_pins'], r2['new_source_pins'])
        self.assertEqual(r11['old_output_links_sha256'], r2['new_output_links_sha256'])

    def test_pins_are_the_revision_13_rebind(self):
        r11, r13 = json.loads(R11.read_text()), json.loads(R13.read_text())
        # Revision 13 (JR step 7 redo) rebinds the geometry and output pins only
        self.assertEqual(r13['old_source_pins'], r11['new_source_pins'])
        self.assertEqual(r13['old_output_links_sha256'], r11['new_output_links_sha256'])
        self.assertEqual(r13['new_source_pins']['signal'], r11['new_source_pins']['signal'])
        self.assertEqual(r13['new_source_pins']['positions'], r11['new_source_pins']['positions'])
        self.assertEqual(r13['new_source_pins'], {'geometry': c6.SOURCE_GEOMETRY_SHA256,
                                                  'signal': c6.SOURCE_SIGNAL_SHA256,
                                                  'positions': c6.SOURCE_POSITIONS_SHA256})
        self.assertEqual(c6.OUTPUT_LINKS_SHA256, r13['new_output_links_sha256'])
        for rec in (r11, r13):
            self.assertEqual(rec['historical_source'], {'source_sha256': c6.SOURCE_SHA256,
                                                        'source_object_sha256': c6.SOURCE_OBJECT_SHA256})
        for name, row in r13['c6_links'].items():
            self.assertTrue(all(row.values()), name)
        self.assertEqual(r13['hold_errors'], [])

    def test_revision_11_c6_links_keep_their_output_and_riders(self):
        rec = json.loads(R11.read_text())
        self.assertEqual(len(rec['c6_links']), 8)
        for name, row in rec['c6_links'].items():
            self.assertEqual(row, {'pre_c6_positions_equal_retained_source': True,
                                   'output_positions_equal_previous': True, 'riders_equal_previous': True}, name)
        self.assertTrue(rec['riders_identical'])
        self.assertEqual(rec['hold_errors'], [])

    def test_committed_gate_record_is_the_c6_output(self):
        doc = json.loads(lg.LINK_GATE.read_text())
        self.assertTrue(c6.valid_record(doc))
        self.assertEqual(doc['c6']['signal_sha256'], c6.SOURCE_SIGNAL_SHA256)
        self.assertEqual(c6.digest(doc['links']), c6.OUTPUT_LINKS_SHA256)


if __name__ == '__main__':
    unittest.main()
