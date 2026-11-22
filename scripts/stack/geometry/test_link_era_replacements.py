"""MC04-S8 Revision 5: the link-era re-placement record and its status in the Gate A open list (no KiCad)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / 'scripts/stack'))

import link_era_replacements as ler  # noqa: E402
import links_gate as lg  # noqa: E402
import gate_a_open_items as ga  # noqa: E402

REC = json.loads(ler.OUT.read_text())


class LinkEraRecord(unittest.TestCase):
    def test_record_is_a_fresh_build(self):
        self.assertEqual(json.dumps(ler.build(), indent=1) + '\n', ler.OUT.read_text())

    def test_record_states_its_model_and_sources(self):
        self.assertIn('GH headers dropped', REC['model'])
        self.assertIn('not checked against the interim boards', REC['model'])
        self.assertIn('board_conflicts.py', REC['evidence_interim_boards'])
        self.assertEqual(len(REC['sources']), len(ler.SOURCES))

    def test_placed_and_open(self):
        placed = {r['ic'] for r in REC['placed']}
        opened = {r['ic'] for r in REC['open']}
        self.assertEqual(len(placed) + len(opened), 15)
        self.assertFalse(placed & opened)
        self.assertIn('U8409', opened)
        for r in REC['placed']:
            self.assertLessEqual(r['pose']['moved_mm'], 50.0 if r['ic'] in ('U1318', 'U4417', 'U4433', 'U4526') else 24.0, r['ic'])
            self.assertTrue(r['member_face_check']['all_clear'], r['ic'])
            for b in r['blocks_moved']:
                self.assertLessEqual(b['moved_mm'], 24.0)
        for o in REC['open']:
            self.assertTrue(o['status'].startswith('OPEN (link era)'))
            if o['ic'] in ('U1415', 'U5110', 'U5209', 'U5210', 'U8409'):
                self.assertEqual(o['status'], 'OPEN (link era): NEEDS_DESIGN for Gate A-paper')
                self.assertFalse(o['gate_a_paper']['evaluated'])
            self.assertIn('0.5 mm', json.dumps(o['proof']))
            self.assertIn('cheapest_option', o)
            if o['ic'] != 'U8409':
                self.assertIn('withdrawn_pose', o)

    def test_gate_record_carries_it(self):
        gate = json.loads(lg.LINK_GATE.read_text())
        self.assertEqual(gate['link_era_replacements'], REC)

    def test_gate_a_status(self):
        doc = json.loads(ga.OUT.read_text())
        rows = [i for i in doc['items'] if i['kind'] == 'open re-placement (re-route)']
        self.assertEqual(len(rows), 15)
        self.assertEqual(sum(doc['re_placement_status'].values()), 15)
        resolved = {i['ref'] for i in rows if i['status'].startswith('RESOLVED FOR THE LINK ERA')}
        self.assertEqual(resolved, {r['ic'] for r in REC['placed']})
        opened = {i['ref'] for i in rows if i['status'].startswith('OPEN (link era)')}
        self.assertEqual(opened, {r['ic'] for r in REC['open']})
        self.assertTrue(all(i['model'] == REC['model'] for i in rows))
        for i in doc['items']:
            self.assertNotIn('distance_from_slot_mm', i)
            if i['id'] in ('GA-LOC-U4417', 'GA-LED-U4647'):
                self.assertIn('link-era model', i['model'])
        for i in rows:
            if i['status'].startswith('OPEN (link era)'):
                self.assertIn('cheapest_option', i)

if __name__ == '__main__':
    unittest.main()
