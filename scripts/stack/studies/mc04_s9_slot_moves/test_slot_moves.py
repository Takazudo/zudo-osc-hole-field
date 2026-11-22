"""MC04-S9-A: the slot-move and package-room study (result.json pinned; the full rebuild is slot_moves.py --check)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slot_moves as sm  # noqa: E402

DOC = json.loads(sm.OUT.read_text())
ROWS = {r['ic']: r for r in DOC['arm1']['targets']}
TABLE = {r['ic']: r for r in DOC['decision_table']}
OUTCOMES = {'U5209': 'none', 'U5110': 'none', 'U8409': 'none', 'U5210': 'R1 clean', 'U1415': 'R2 room only by displacing input-buffer parts'}


class Scene:
    s = a1 = None

    @classmethod
    def get(cls):
        if cls.s is None:
            cls.s = sm.S9()
            cls.s.setup9()
            cls.a1 = sm.Arm1(cls.s, 0.0)
        return cls.s, cls.a1


class Pinned(unittest.TestCase):
    def test_inputs_have_not_drifted(self):
        pins, base = sm.input_pins()
        self.assertEqual(pins, DOC['inputs'])
        self.assertEqual(base, DOC['base'])
        self.assertTrue(base['links_and_replacement_unchanged'])
        self.assertEqual(base['link_era_rows_changed'], ['U4433'])

    def test_arm0_premise_and_reproduction(self):
        a0 = DOC['arm0']
        self.assertTrue(a0['premise_holds'])
        self.assertEqual(a0['gone_keepouts_in_field'], [])
        self.assertIn('P-K-P-L03.02.02.01', a0['gone_links'])
        self.assertTrue(a0['result_r7_reproduced_byte_for_byte'])
        self.assertEqual(set(a0['five_open'].values()), {'OPEN (link era)'})

    def test_per_ic_outcome(self):
        self.assertEqual({ic: r['outcome'] for ic, r in TABLE.items()}, OUTCOMES)
        for ic, r in TABLE.items():
            if r['R1'] != 'R1 clean':
                self.assertTrue(r['R1_reason'], ic)

    def test_room_only_rows_are_labelled(self):
        for r in DOC['arm2'] + DOC['combined']:
            self.assertEqual(r['label'], 'ROOM ONLY, NO PART SELECTED')
        self.assertEqual({r['ic'] for r in DOC['combined']},
                         {ic for ic, r in TABLE.items() if r['R1'] != 'R1 clean' and r['R2_with_input_buffer_guard'] != 'R2 room'})

    def test_tssop_courtyard_is_placed_as_the_soic(self):
        for r in DOC['arm2']:
            self.assertEqual(r['courtyard_soic'], r['courtyard_soic_from_library'], r['ic'])
            c = r['courtyard_tssop']
            self.assertEqual(sorted([round(c[2] - c[0], 2), round(c[3] - c[1], 2)]), [5.99, 7.7], r['ic'])

    def test_clean_move_figures(self):
        for ic, row in ROWS.items():
            for lid, m in row.get('moves', {}).items():
                f = m['figures']
                self.assertGreaterEqual(f['moved']['loop_mm'], 0.0, lid)
                self.assertTrue(f['compliance_within_limit'], lid)
                for x in f['members'] + f['riders']:
                    self.assertLessEqual(x['moved_mm'], x['limit_mm'] + 1e-9, lid)
                self.assertTrue(m['restored'][ic]['legal_at_recorded_position'])
                for p in m['parts_re_placed']:
                    self.assertIsNotNone(p['face'], p['ref'])
                    self.assertLessEqual(p['moved_mm'], sm.LIMIT, p['ref'])
        self.assertTrue(DOC['arm1']['joint_verification']['clean'])

    def test_not_established_and_not_run(self):
        self.assertTrue(all(v.startswith('NOT RUN') for v in DOC['oracle_checks'].values()))
        for k in ('c6', 'coupling', 'current', 'latch access', 'threading', 'routing', 'DRC', 'electrical'):
            self.assertTrue(any(k in x for x in DOC['not_established']), k)


class Rules(unittest.TestCase):
    def test_a_candidate_that_breaks_a_rider_limit_is_rejected(self):
        s, a1 = Scene.get()
        ex = DOC['arm1']['rider_rejection_examples']
        self.assertTrue(ex)
        for lid, e in ex.items():
            targets = tuple(ic for ic, lids in sm.TARGETS if lid in lids)
            why = a1.accept_for(lid, targets)(e['geometry'])
            self.assertTrue(why and why.startswith('rider'), (lid, why))

    def test_mutation_back_to_the_recorded_slot_fails(self):
        s, a1 = Scene.get()
        lid = 'P-K-P-L13.01.01.01'
        rec = s.byid[lid]['geometry']
        self.assertEqual(a1.accept_for(lid, ('U5210',))(rec), 'still covers U5210')
        clean, det = a1.evaluate({lid: rec}, ['U5210'])
        self.assertFalse(clean)
        self.assertIn('target not legal', det['categories'])
        moved = ROWS['U5210']['moves'][lid]['geometry']
        self.assertIsNone(a1.accept_for(lid, ('U5210',))(moved))
        clean, det = a1.evaluate({lid: moved}, ['U5210'])
        self.assertTrue(clean)
        self.assertEqual(det['parts_re_placed'], ROWS['U5210']['moves'][lid]['parts_re_placed'])


if __name__ == '__main__':
    unittest.main()
