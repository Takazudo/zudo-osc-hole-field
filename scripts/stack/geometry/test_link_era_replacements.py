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

    def test_fourteen_placed_and_one_open(self):
        placed = {r['ic'] for r in REC['placed']}
        self.assertEqual(len(placed), 14)
        self.assertEqual([r['ic'] for r in REC['open']], ['U8409'])
        self.assertFalse(placed & {r['ic'] for r in REC['open']})
        for r in REC['placed']:
            self.assertLessEqual(r['pose']['moved_mm'], 50.0 if r['ic'] in ('U1318', 'U4417') else 24.0, r['ic'])
            for b in r['blocks_moved']:
                self.assertLessEqual(b['moved_mm'], 24.0)
        o = REC['open'][0]
        self.assertFalse(o['proof']['found'])
        self.assertIn('0.5 mm', o['proof']['grid_caveat'])
        opt = o['cheapest_option']
        self.assertTrue(opt['neighbours_beyond_24mm'])
        self.assertIn('first one found', opt['first_found'])
        self.assertIn('U5210', opt['supersedes'])
        self.assertTrue(opt['neighbour_electrical'])
        c = [m for r in REC['placed'] for m in r['passives_moved'] if m['ref'] == 'C5210']
        self.assertTrue(c and 'via' in c[0]['note'])

    def test_gate_record_carries_it(self):
        gate = json.loads(lg.LINK_GATE.read_text())
        self.assertEqual(gate['link_era_replacements'], REC)

    def test_gate_a_status(self):
        doc = json.loads(ga.OUT.read_text())
        rows = [i for i in doc['items'] if i['kind'] == 'open re-placement (re-route)']
        self.assertEqual(len(rows), 15)
        resolved = [i for i in rows if i['status'].startswith('RESOLVED FOR THE LINK ERA')]
        research = [i for i in rows if i['status'].startswith('NEEDS RE-SEARCH')]
        clear = {r['ic'] for r in REC['placed'] if r['member_face_check']['all_clear']}
        self.assertEqual({i['ref'] for i in resolved}, clear)
        self.assertEqual(len(resolved) + len(research), 14)
        for i in research:
            self.assertTrue(i['member_face_check']['blocked'])
        self.assertTrue(all(i['model'] == REC['model'] for i in rows))
        self.assertEqual(sum(doc['re_placement_status'].values()), 15)
        for i in doc['items']:
            self.assertNotIn('distance_from_slot_mm', i)
            if i['id'] in ('GA-LOC-U4417', 'GA-LED-U4647'):
                self.assertIn('link-era model', i['model'])
        u = next(i for i in rows if i['ref'] == 'U8409')
        self.assertEqual(u['status'], 'OPEN (link era)')
        self.assertIn('cheapest_option', u)


if __name__ == '__main__':
    unittest.main()
