"""MC04-S7 Revision 14 item 8: the Gate A open list equals a fresh build from its sources (no KiCad, no network)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack'))

import gate_a_open_items as ga  # noqa: E402


class GateAOpenItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(ga.OUT.read_text())
        cls.ids = {i['id'] for i in cls.doc['items']}

    def test_committed_list_is_a_fresh_build(self):
        self.assertEqual(json.dumps(ga.build(), indent=1) + '\n', ga.OUT.read_text())

    def test_reach_exceptions_by_id(self):
        self.assertTrue({'GA-REACH-JL-K-26', 'GA-REACH-JL-K-27', 'GA-REACH-JR-K-28', 'GA-REACH-JR-K-29', 'GA-REACH-SLEEVES'} <= self.ids)

    def test_fifteen_open_replacements_with_u4647_and_u4129(self):
        rows = [i for i in self.doc['items'] if i['kind'] == 'open re-placement (re-route)']
        self.assertEqual(len(rows), 15)
        self.assertTrue({'GA-REPLACE-JR-U4647', 'GA-REPLACE-K-U4129'} <= self.ids)
        self.assertTrue(all(r['overlaps'] for r in rows))

    def test_protection_locality_interim_exceptions_and_slot_drift(self):
        self.assertTrue({'GA-PROT-D4101', 'GA-PROT-D4102', 'GA-LOC-R8381', 'GA-LOC-R8382', 'GA-LOC-U5113'} <= self.ids)
        self.assertTrue({'GA-SLOT-JR-K-JR-L01', 'GA-SLOT-JR-K-JR-L03'} <= self.ids)
        self.assertIn('GA-FIX-JL-P-4-P-SLV-L1', self.ids)


if __name__ == '__main__':
    unittest.main()
