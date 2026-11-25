"""MC04-S8 Revision 5: the link-era re-placement record and its status in the Gate A open list (no KiCad)."""
import json
import sys
import tempfile
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
        self.assertEqual((len(placed), len(opened)), (10, 3))
        self.assertEqual(opened, {'U1415', 'U5110', 'U8409'})
        self.assertEqual({r['ic'] for r in REC['not_displaced_after_s10']}, {'U5209', 'U5210'})
        self.assertEqual(REC['s10']['disposition'], 'STOP')
        withheld = {'U4222', 'U4227', 'U4537'}
        self.assertEqual(set(REC['s10']['withheld_overlay_ics']), withheld)
        self.assertFalse(withheld & placed)
        self.assertTrue(REC['s10']['stop'])
        ruled = REC['s10']['ruled_parts']
        self.assertFalse(ruled['R5257']['meets'])
        self.assertGreater(ruled['R5257']['distance_to_ic_mm'], ruled['R5257']['limit_mm'])
        self.assertEqual(ruled['R5259']['face'], 'B')
        self.assertTrue(all(ruled[t]['rear'] for t in ('RV4503', 'RV8407', 'RV2310')))
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
        far = {o['ic']: o.get('far_option_overlaps', []) for o in REC['open']}
        self.assertIn('U8409', far['U5110'])

    def test_u4433_is_its_own_exception(self):
        r = next(x for x in REC['placed'] if x['ic'] == 'U4433')
        self.assertIn('DS-144', r['ruling'])
        self.assertNotIn('U4417', r['class'])
        self.assertEqual((r['pose']['face'], r['pose']['turn_deg'], r['pose']['moved_mm']), ('F', 270, 25.5))
        self.assertTrue(r['ds144_checks']['pass'])
        self.assertTrue(r['ds144_checks']['member_faces']['all_clear'])
        self.assertEqual(r['ds144_checks']['board_conflicts']['other_conflicts'], [])
        self.assertEqual(len(r['conditions']), 3)
        self.assertTrue(any('fact-flipflop-input-transition45' in c for c in r['conditions']))
        self.assertTrue(any('DS-88' in c for c in r['conditions']))
        doc = json.loads(ga.OUT.read_text())
        self.assertIn('GA-LOC-U4433', {i['id'] for i in doc['items']})

    def test_stale_or_injected_candidate_placement_is_rejected(self):
        record = ler.build()
        record['placed'].append({'board': 'K', 'ic': 'U4222', 'class': 'S10 block-rule overlay'})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'link-era-replacements.json'
            path.write_text(json.dumps(record))
            with self.assertRaisesRegex(ValueError, 'unapproved placement'):
                ler.checked_record(path, json.loads(lg.LINK_GATE.read_text())['replacement']['footprints'])

    def test_missing_era_and_changed_gate_scene_fail_closed(self):
        rows = json.loads(lg.LINK_GATE.read_text())['replacement']['footprints']
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(FileNotFoundError):
            ler.checked_record(Path(tmp) / 'missing.json', rows)
        new_open = dict(rows[0], ref='U_NEW', new=None)
        with self.assertRaisesRegex(ValueError, 'Unaccounted open gate rows'):
            ler.checked_record(ler.OUT, rows + [new_open])

    def test_gate_record_carries_it(self):
        gate = json.loads(lg.LINK_GATE.read_text())
        self.assertEqual(gate['link_era_replacements'], REC)

    def test_gate_a_status(self):
        doc = json.loads(ga.OUT.read_text())
        disposition = next(x for x in doc['items'] if x['id'] == 'GA-S10-DISPOSITION')
        self.assertEqual(disposition['status'], 'STOP')
        self.assertEqual(disposition['reasons'], REC['s10']['stop'])
        self.assertFalse(any(x['kind'] == 'S10 overlay block' for x in doc['items']))
        rows = [i for i in doc['items'] if i['kind'] == 'open re-placement (re-route)']
        self.assertEqual(len(rows), 13)
        self.assertEqual(sum(doc['re_placement_status'].values()), 13)
        resolved = {i['ref'] for i in rows if i['status'].startswith('RESOLVED FOR THE LINK ERA')}
        self.assertEqual(resolved, {r['ic'] for r in REC['placed'] if r['class'] != 'S10 block-rule overlay'})
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
