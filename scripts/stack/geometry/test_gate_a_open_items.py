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

    def test_thirteen_open_replacements_with_u4647_and_u4129(self):
        rows = [i for i in self.doc['items'] if i['kind'] == 'open re-placement (re-route)']
        self.assertEqual(len(rows), 13)  # MC04-S10: U5209 and U5210 are no longer displaced
        self.assertFalse({'GA-REPLACE-K-U5209', 'GA-REPLACE-K-U5210'} & self.ids)
        self.assertTrue({'GA-REPLACE-JR-U4647', 'GA-REPLACE-K-U4129'} <= self.ids)
        self.assertTrue(all(r['overlaps'] for r in rows))

    def test_protection_locality_interim_exceptions_and_slot_drift(self):
        self.assertTrue({'GA-PROT-D4101', 'GA-PROT-D4102', 'GA-LOC-R8381', 'GA-LOC-R8382', 'GA-LOC-U5113'} <= self.ids)
        self.assertTrue({'GA-SLOT-JR-K-JR-L01', 'GA-SLOT-JR-K-JR-L03'} <= self.ids)
        self.assertIn('GA-FIX-JL-P-4-P-SLV-L1', self.ids)


    def test_dissolved_links_are_not_cited(self):
        gone = {l['id'] for l in json.loads((ROOT / ga.GATE).read_text())['links'] if l.get('gone')}
        self.assertIn('P-K-P-L03.02.02.01', gone)
        for i in self.doc['items']:
            for o in i.get('overlaps', []):
                self.assertNotIn(o['link'], gone, i['id'])
        u8409 = next(i for i in self.doc['items'] if i['id'] == 'GA-REPLACE-K-U8409')
        self.assertEqual({o['link'] for o in u8409['overlaps']}, {'P-K-P-L03.01'})

    def test_overlaps_skips_a_gone_link(self):
        rec = {'board': 'K', 'courtyard': [0.0, 0.0, 2.0, 2.0]}
        geo = {'K_connector': [1.0, 1.0, 3.0, 3.0]}
        live = {'id': 'A', 'front_board': 'P', 'geometry': geo}
        self.assertEqual([o['link'] for o in ga.overlaps(rec, [live, dict(live, id='B', gone=True)])], ['A'])

    def test_s10_items(self):
        kinds = {}
        for i in self.doc['items']:
            kinds.setdefault(i['kind'], []).append(i)
        self.assertEqual({i['ref'] for i in kinds['S10 overlay block']}, {'U4222', 'U4227', 'U4537'})
        u4537 = next(i for i in kinds['S10 overlay block'] if i['ref'] == 'U4537')
        self.assertIn('/E5/CLOCK', u4537['timing_nodes'])
        self.assertTrue(all(g['added_run_estimate_mm'] is not None for g in u4537['grown_nets']))
        self.assertTrue(kinds['S10 face change'])
        self.assertTrue(all(i['nets'] and i['from'] != i['to'] for i in kinds['S10 face change']))


if __name__ == '__main__':
    unittest.main()
