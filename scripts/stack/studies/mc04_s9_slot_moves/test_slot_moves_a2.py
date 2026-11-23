"""MC04-S9-A2: the joint re-run under the DS-146 rules (result-a2.json pinned; the rebuild is slot_moves_a2.py --check)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slot_moves as sm  # noqa: E402
import slot_moves_a2 as a2  # noqa: E402

DOC = json.loads(a2.OUT.read_text())
A = json.loads(sm.OUT.read_text())
TABLE = {r['ic']: r for r in DOC['decision_table']}
OUTCOMES = {'U5209': 'R1 clean (joint)', 'U5110': 'R1 not clean', 'U8409': 'R1 not clean', 'U5210': 'R1 clean (joint)'}


class Scene:
    s = a1 = None

    @classmethod
    def get(cls):
        if cls.s is None:
            cls.s = a2.S9A2()
            cls.s.setup9()
            cls.a1 = a2.Arm1A2(cls.s, 0.0)
        return cls.s, cls.a1


class Pinned(unittest.TestCase):
    def test_outcomes(self):
        self.assertEqual({ic: r['outcome'] for ic, r in TABLE.items()}, OUTCOMES)
        self.assertTrue(DOC['joint_scene']['clean'])
        self.assertEqual(sorted(DOC['joint_scene']['restored']), ['U5209', 'U5210'])
        self.assertTrue(all(r['legal_at_recorded_position'] for r in DOC['joint_scene']['restored'].values()))
        self.assertEqual(DOC['caps_reached'], [])
        self.assertTrue(DOC['prior_study']['unchanged'])
        self.assertEqual(DOC['runs']['U5209']['variant_A']['clean'], [])
        self.assertTrue(DOC['runs']['U5209']['variant_B']['clean_pairs'])

    def test_inputs_have_not_drifted(self):
        pins, base = sm.input_pins()
        pins[a2.TRIMMER_PLAN] = a2.hashlib.sha256(sm.blob(a2.TRIMMER_PLAN)).hexdigest()
        self.assertEqual(pins, DOC['inputs'])

    def test_every_clean_move_keeps_its_limits(self):
        scene = DOC['joint_scene']
        for p in scene['parts_re_placed']:
            self.assertIsNotNone(p['face'], p['ref'])
            self.assertLessEqual(p['moved_mm'], sm.LIMIT)
            if p.get('trimmer'):
                self.assertEqual(p['face'], p['face_before'], p['ref'])
            c = p.get('condition') or {}
            if c.get('kind') in ('decoupler', 'R_ISO'):
                self.assertLessEqual(p['distance_to_ic_after_mm'], c['limit_mm'] + 0.01, p['ref'])
        for k in ('U5110', 'U8409', 'U5210'):
            for c in DOC['runs'][k]['clean']:
                f = c['figures']
                self.assertGreaterEqual(f['moved']['loop_mm'], 0.0)
                self.assertTrue(f['compliance_within_limit'])
                for x in f['members'] + f['riders']:
                    self.assertLessEqual(x['moved_mm'], x['limit_mm'] + 1e-9)

    def test_not_run_checks(self):
        self.assertTrue(all(v.startswith('NOT RUN') for v in DOC['oracle_checks'].values()))


class Rules(unittest.TestCase):
    def test_a_candidate_covering_u8409_is_rejected(self):
        s, a1 = Scene.get()
        lid = 'P-K-P-L13.01.01.01'
        held = next(r for r in A['arm1']['targets'] if r['ic'] == 'U5210')['moves'][lid]['geometry']  # the S9-A move
        self.assertIsNone(sm.Arm1(s, 0.0).accept_for(lid, ('U5210',))(held))   # accepted under the S9-A rules
        self.assertEqual(a1.accept_for(lid, ('U5210',))(held), 'covers the recorded courtyard of U8409')

    def test_a_trimmer_keeps_its_face(self):
        s, a1 = Scene.get()
        faces, check, cond = a1.conditions(('K', 'RV8407'), ())
        self.assertEqual(faces, [s.fps[('K', 'RV8407')]['side']])
        faces, check, cond = a1.conditions(('K', 'R8356'), ())
        self.assertEqual(len(faces), 2)   # a plain surface-mount passive on K may take the other face

    def test_r_fb_stops_and_r_iso_moves_within_its_condition(self):
        s, a1 = Scene.get()
        self.assertEqual(a2.buffer_kind(s, ('K', 'R8340'))[0], 'stop')        # R_FB on /M4A/..._FB
        self.assertEqual(a2.buffer_kind(s, ('K', 'U8411'))[0], 'stop')        # the buffer IC
        self.assertEqual(a2.buffer_kind(s, ('K', 'C8438'))[0], 'decoupler')
        self.assertEqual(a2.buffer_kind(s, ('K', 'R8339'))[0], 'r_iso')       # DRIVE and REMOTE only
        faces, check, cond = a1.conditions(('K', 'R8339'), ())
        here = s.current_origin(('K', 'R8339'))
        self.assertIsNone(check(here))                                         # where it is: within the condition
        amp = s.current_origin(('K', cond['op_amp']))
        far = [2 * here[0] - amp[0], 2 * here[1] - amp[1]]
        self.assertIn('farther', check(far))                                   # farther from its op-amp: rejected

    def test_mutation_fails(self):
        s, a1 = Scene.get()
        lid = 'P-K-P-L13.01.01.01'
        best = DOC['runs']['U5210']['clean'][0]
        self.assertIsNone(a1.accept_for(lid, ('U5210',))(best['geometry']))
        bad = json.loads(json.dumps(best['geometry']))
        bad['slot'] = [bad['slot'][0], bad['slot'][1] - 0.5, bad['slot'][2], bad['slot'][3] - 0.5]  # 0.5 mm onto U8409
        self.assertIsNotNone(a1.accept_for(lid, ('U5210',))(bad))


if __name__ == '__main__':
    unittest.main()
