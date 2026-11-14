"""Unit tests for the ST-04 a2 flat-link calculator: no network, no KiCad."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link_electrical as le  # noqa: E402


class Retained(unittest.TestCase):
    def test_retained_files_equal_a_fresh_run(self):
        rj, rm, hj = le.generate()
        self.assertEqual((le.OUT / 'results.json').read_text(), rj, 'run link_electrical.py')
        self.assertEqual((le.OUT / 'README.md').read_text(), rm, 'run link_electrical.py')
        self.assertEqual((le.OUT / 'harness-baseline.json').read_text(), hj, 'run link_electrical.py')

    def test_every_input_has_a_status(self):
        inp = le.load_inputs()
        for k, v in inp['cable'].items():
            self.assertIn('status', v, k)
        for k, v in list(inp['aggressors'].items()) + list(inp['victims'].items()):
            self.assertIn(v['status'], ('SOURCED', 'DERIVED', 'ASSUMED'), k)
        for pk in le.PITCHES:
            for r in inp['contact'][pk]['ratings_A']:
                self.assertIn(r['status'], ('SOURCED', 'DERIVED', 'ASSUMED'))

    def test_wave_sources_are_the_sourced_0_5mm_ratings(self):
        inp = le.load_inputs()
        vals = {r['value']: r['status'] for r in inp['contact']['pitch_0_5']['ratings_A']}
        self.assertEqual(vals[0.5], 'SOURCED')
        self.assertEqual(vals[0.35], 'DERIVED')
        self.assertAlmostEqual(0.7 * 0.5, 0.35)


class Signals(unittest.TestCase):
    def test_counts_match_da03(self):
        inp = le.load_inputs()
        sig = le.classified_signals(inp)
        self.assertEqual(len(sig), 492)
        joints = {}
        for s in sig:
            joints[s['family']] = joints.get(s['family'], 0) + 1
        self.assertEqual(joints, {'K/P': 246, 'JR/K': 108, 'JL/K': 100, 'P/K for EL': 18, 'JL/P pass-through': 16, 'SUB': 4})
        self.assertEqual(sum(s['class'] == 'NC' for s in sig), 2)

    def test_classification_examples(self):
        inp = le.load_inputs()
        kinds = le.partition_kinds()
        rules = inp['classes']['rules']
        self.assertEqual(le.classify('/E1/TRIG_ACTIVE', kinds, rules), 'LOGIC')
        self.assertEqual(le.classify('/O1/LOCAL_REF5', kinds, rules), 'PRECISION')
        self.assertEqual(le.classify('/A01/C38cac0_W', kinds, rules), 'WIPER')
        self.assertEqual(le.classify('/F1/BP_CORE', kinds, rules), 'ANALOGUE')


class Physics(unittest.TestCase):
    def test_mom_matches_conformal_map(self):
        for w, s in ((0.65e-3, 0.35e-3), (0.3e-3, 0.2e-3)):
            c = le.capacitance_matrix([0.0, w + s], w, 2.0)
            ref = le.coplanar_pair_c(w, s, 2.0)
            self.assertLess(abs(-c[0, 1] - ref) / ref, 0.01)

    def test_capacitance_columns_sum_to_zero_and_ground_screens(self):
        cen = [i * 1e-3 for i in range(5)]
        c = le.capacitance_matrix(cen, 0.65e-3, 1.0)
        for j in range(5):
            self.assertAlmostEqual(c[:, j].sum() / c[j, j], 0.0, places=9)
        self.assertLess(-c[0, 2], -c[0, 1] / 3)

    def test_grover_mutual_limit(self):
        l, d = 0.06, 1e-3
        approx = le.MU0 * l / (2 * math.pi) * (math.log(2 * l / d) - 1)
        self.assertLess(abs(le.lp_mutual(l, d) - approx) / approx, 0.02)

    def test_ground_between_reduces_coupling(self):
        inp = le.load_inputs()
        for pk in le.PITCHES:
            adj = le.pair_parameters(inp, pk, 50, 3.2, 'A', 'adjacent')
            gnd = le.pair_parameters(inp, pk, 50, 3.2, 'A', 'across_ground')
            self.assertLess(gnd['Cm_F'], adj['Cm_F'])
            self.assertLess(abs(gnd['M_eff_H']), abs(adj['M_eff_H']))
            self.assertAlmostEqual(sum(adj['return_split'].values()), -1.0, places=9)

    def test_longer_cable_couples_more(self):
        inp = le.load_inputs()
        a = le.pair_parameters(inp, 'pitch_1_0', 50, 2.1, 'A', 'adjacent')
        b = le.pair_parameters(inp, 'pitch_1_0', 80, 2.1, 'A', 'adjacent')
        self.assertAlmostEqual(b['Cm_F'] / a['Cm_F'], 90 / 60, places=6)
        self.assertGreater(b['M_eff_H'], a['M_eff_H'])


class GroundCurrent(unittest.TestCase):
    def test_one_ground_meets_every_rating_with_a_post_in_place(self):
        inp = le.load_inputs()
        for pk in le.PITCHES:
            for b in ('JL', 'JR', 'P'):
                for posts in (3, 2):
                    i = le.worst_ground_contact(inp, pk, b, 1, posts)
                    self.assertLess(i, min(r['value'] for r in inp['contact'][pk]['ratings_A']))

    def test_bound_formula_by_hand(self):
        inp = le.load_inputs()
        d = le.pp.load()
        rj = le.pp.joint_ohm(d, 19.0)
        alt = 0.0005 + 1 / (3 / rj)
        self.assertAlmostEqual(le.worst_ground_contact(inp, 'pitch_1_0', 'JL', 1, 3), 4.6 * alt / (0.0332 + alt), places=12)

    def test_all_posts_open_needs_many_grounds(self):
        inp = le.load_inputs()
        n = le.min_grounds(inp, 'pitch_1_0', 'JL', 0, 0.4)
        self.assertGreater(n, 30)
        self.assertLessEqual(le.worst_ground_contact(inp, 'pitch_1_0', 'JL', n, 0), 0.4)
        self.assertGreater(le.worst_ground_contact(inp, 'pitch_1_0', 'JL', n - 1, 0), 0.4)

    def test_fault_injection_low_resistance_link_exceeds(self):
        inp = copy.deepcopy(le.load_inputs())
        inp['conductor_resistance_mohm']['pitch_1_0']['min'] = 0.1
        self.assertGreater(le.worst_ground_contact(inp, 'pitch_1_0', 'JL', 1, 3), 0.5)


class Counts(unittest.TestCase):
    def test_rule_counts(self):
        rj = json.loads((le.OUT / 'results.json').read_text())
        for pk, opts in rj['ground_counts'].items():
            for c, rows in opts.items():
                for j, x in rows.items():
                    self.assertEqual(x['rule_A']['grounds'], math.ceil(x['signals'] / 2))
                    self.assertLessEqual(x['signals'] + x['rule_B']['grounds'], x['rule_B']['links'] * int(c))
                    self.assertLessEqual(x['signals'] + x['grounds_rule'], x['links_rule'] * int(c))


class HarnessBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import harness_baseline as hb
        cls.hb = hb
        cls.inp = le.load_inputs()
        cls.pats = hb.harness_patterns(cls.inp)
        cls.counts = hb.pattern_counts(cls.pats)

    def test_pattern_sizes_and_ground_between(self):
        self.assertEqual(self.counts['sizes'], {3: 127, 7: 10, 8: 58})
        self.assertEqual(self.counts['adjacent_signals'], [])
        self.assertEqual(len(self.counts['signal_beside_rail']), 6)
        self.assertEqual(sum(p['classes'][0] == 'G' for p in self.pats), 0)
        self.assertEqual(sum(c.count('G') for c in (p['classes'] for p in self.pats)), 380)

    def test_manager_count_reproduced(self):
        tri = {k: len(v) for k, v in self.counts['triples'].items()}
        hs = self.counts['harness_count']
        expected = {'ANALOGUE/PRECISION': (39, 34), 'ANALOGUE/WIPER': (14, 14), 'LOGIC/LOGIC': (17, 17),
                    'LOGIC/PRECISION': (11, 11), 'ANALOGUE/LOGIC': (2, 2), 'PRECISION/PRECISION': (18, 18),
                    'PRECISION/WIPER': (5, 5), 'WIPER/WIPER': (40, 40)}
        for k, (t, h) in expected.items():
            self.assertEqual((tri[k], hs[k]), (t, h), k)
        self.assertEqual((tri['ANALOGUE/ANALOGUE'], hs['ANALOGUE/ANALOGUE']), (172, 80))
        ko = [t for t in self.counts['triples']['ANALOGUE/ANALOGUE'] if t['harness'].startswith('K-O')]
        self.assertEqual(len(ko), 25)
        self.assertEqual(len({t['harness'] for t in ko}), 10)
        self.assertEqual((172 - 25, 80 - 10), (147, 70))

    def test_round_wire_capacitance_matches_formula(self):
        for d in (1.25e-3, 2.5e-3):
            c = self.hb.wire_capacitance_matrix([0.0, d], 0.2413e-3, 2.0)
            ref = self.hb.two_wire_c(d, 0.2413e-3, 2.0)
            self.assertLess(abs(-c[0, 1] - ref) / ref, 0.005)

    def test_loom_wire_and_length(self):
        self.assertTrue(all(p['wire_mpn'] == 'Alpha Wire 6821 BK005' for p in self.pats))
        self.assertEqual(max(p['cut_length_mm'] for p in self.pats), 204)

    def test_rule_keeps_flat_at_or_below_harness(self):
        b = json.loads((le.OUT / 'harness-baseline.json').read_text())
        names = {0: 'flat side by side', 1: 'flat one ground between (rule A)', 2: 'flat two grounds between'}
        for pk, rule in b['rules'].items():
            for r in b['comparison']:
                if r['pitch'] != pk:
                    continue
                a, v = r['pair'].split('>')
                need = rule[a + '/' + v]
                self.assertIsNotNone(need)
                self.assertLessEqual(r['ratio_to_min'][names[need]], 1.0)
            self.assertIsNone(rule['LOGIC/WIPER'])

    def test_fault_injection_longer_flat_exceeds(self):
        fl = self.hb.flat_levels(self.inp, 'pitch_1_0', 400, 'ANALOGUE', 'ANALOGUE')
        base, _ = self.hb.baseline(self.inp, self.pats)
        self.assertGreater(fl['flat one ground between (rule A)'], base['ANALOGUE>ANALOGUE']['min_V'])


if __name__ == '__main__':
    unittest.main()
