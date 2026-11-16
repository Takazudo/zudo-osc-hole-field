"""Unit tests for the ST-04 a2 flat-link calculator: no network, no KiCad."""
import copy
import json
import math
import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link_electrical as le  # noqa: E402


class Retained(unittest.TestCase):
    def test_retained_files_equal_a_fresh_run(self):
        rj, rm, hj, dj, lj = le.generate()
        self.assertEqual((le.OUT / 'results.json').read_text(), rj, 'run link_electrical.py')
        self.assertEqual((le.OUT / 'README.md').read_text(), rm, 'run link_electrical.py')
        self.assertEqual((le.OUT / 'harness-baseline.json').read_text(), hj, 'run link_electrical.py')
        self.assertEqual((le.OUT / 'ds62-table.json').read_text(), dj, 'run link_electrical.py')
        self.assertEqual((le.OUT / 'link-ratios.json').read_text(), lj, 'run link_electrical.py')

    def test_every_input_has_a_status(self):
        inp = le.load_inputs()
        for k, v in inp['cable'].items():
            self.assertIn('status', v, k)
        for k, v in list(inp['aggressors'].items()) + list(inp['victims'].items()):
            self.assertIn(v['status'], ('SOURCED', 'DERIVED', 'ASSUMED'), k)
        for pk in le.PITCHES:
            for r in inp['contact'][pk]['ratings_A']:
                self.assertIn(r['status'], ('SOURCED', 'DERIVED', 'ASSUMED'))

    def test_readme_has_no_stray_backslash_and_no_warning(self):
        import warnings
        self.assertNotIn('\\′', (le.OUT / 'README.md').read_text())
        with warnings.catch_warnings():
            warnings.simplefilter('error')
            compile((Path(le.__file__)).read_text(), le.__file__, 'exec')

    def test_changed_input_changes_text(self):
        inp = copy.deepcopy(le.load_inputs())
        inp['aggressors']['LOGIC']['load_F'] = 2.2e-11
        inp['cable']['eps_eff']['value'] = [1.0, 2.0, 3.0]
        r = le.results(inp)
        text = le.readme(inp, r)
        self.assertIn('load 22 pF', text)
        self.assertIn('ε_eff swept 1 / 2 / 3', text)
        self.assertNotIn('load 15 pF', text)

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
        self.assertEqual(len(sig), 490)
        joints = {}
        for s in sig:
            joints[s['family']] = joints.get(s['family'], 0) + 1
        self.assertEqual(joints, {'K/P': 246, 'JR/K': 106, 'JL/K': 100, 'P/K for EL': 18, 'JL/P pass-through': 16, 'SUB': 4})
        self.assertFalse(any(s['class'] == 'NC' for s in sig))

    def test_counts_equal_room_study(self):
        site = json.loads((le.ROOT / 'design/stack/geometry/links/link-candidate.json').read_text())['site_counts']
        sig = le.link_signals()
        self.assertEqual(len(sig), site['signals'])
        for fam, row in site['by_family'].items():
            self.assertEqual(sum(s['family'] == fam for s in sig), row['signals'], fam)
        r = json.loads((le.OUT / 'results.json').read_text())
        self.assertEqual(sum(r['branch_signals'].values()), site['signals'])
        for pk, opts in r['ground_counts'].items():
            for rows in opts.values():
                self.assertEqual(sum(x['signals'] for x in rows.values()), site['signals'])

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
    def test_capacities_equal_room_study(self):
        sys.path.insert(0, str(le.ROOT / 'scripts/stack/geometry'))
        import links
        for n in (20, 22, 30, 40):
            self.assertEqual(le.ds51_capacity(n, 'A'), links.capacity(n, 'G-PER-2S'))
            self.assertEqual(le.ds51_capacity(n, 'B_inner'), links.capacity(n, 'G-BETWEEN'))
        self.assertEqual([le.ds51_capacity(n, 'A') for n in (20, 22, 30, 40)], [13, 14, 20, 26])
        self.assertEqual([le.ds51_capacity(n, 'B_inner') for n in (20, 22, 30, 40)], [10, 11, 15, 20])

    def test_rule_counts_per_link(self):
        rj = json.loads((le.OUT / 'results.json').read_text())
        for pk, opts in rj['ground_counts'].items():
            for c, rows in opts.items():
                for j, x in rows.items():
                    for k in ('rule_A', 'rule_B_inner', 'rule_B_outer'):
                        y = x[k]
                        self.assertEqual(y['links'], math.ceil(x['signals'] / y['signals_per_link']))
                        self.assertLessEqual(x['signals'] + y['grounds'], y['links'] * int(c))
                    self.assertLessEqual(x['signals'] + x['grounds_rule'], x['links_rule'] * int(c))
        x = le.ds51_counts(40, 20)
        self.assertEqual((x['rule_A']['links'], x['rule_A']['grounds']), (4, 3 * 7 + 1))
        self.assertEqual((x['rule_B_inner']['links'], x['rule_B_inner']['grounds']), (4, 36))

    def test_grouping_tries_every_existing_cable(self):
        sep = 'not in the same flat cable (separate link or ground layer)'
        table = {('LOGIC', 'ANALOGUE'): sep, ('ANALOGUE', 'PRECISION'): sep, ('ANALOGUE', 'ANALOGUE'): 'side by side'}
        verdicts = [{'pitch': 'pitch_1_0', 'aggressor': a, 'victim': v, 'need': table.get((a, v), 'side by side')}
                    for a in le.AGGRESSORS for v in le.VICTIMS]
        sig = [{'family': 'JL/K', 'front_board': 'JL', 'class': c} for c in ('LOGIC', 'ANALOGUE', 'PRECISION')]
        out = le.ground_count(sig, verdicts, 'pitch_1_0', 20)['JL to K']
        self.assertEqual(out['cables'], ['LOGIC + PRECISION', 'ANALOGUE'])


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


class AttemptA4(unittest.TestCase):
    """a4 part 1: adapter class, signals_all and the DS-62 ratio table."""

    @classmethod
    def setUpClass(cls):
        import ds62_table
        cls.d = ds62_table
        cls.inp = le.load_inputs()
        cls.res = json.loads((le.OUT / 'results.json').read_text())
        cls.tab = json.loads((le.OUT / 'ds62-table.json').read_text())

    def test_class_rules_are_byte_identical_to_a3(self):
        import hashlib
        h = hashlib.sha256(json.dumps(self.inp['classes']['rules'], sort_keys=True).encode()).hexdigest()
        self.assertEqual(h, '9929223c963d93faf8b5a8948589ae19fbc87b72f85e9187c796b2788a799d76')

    def test_signals_all_extends_the_490_unchanged(self):
        self.assertEqual(len(self.res['signals']), 490)
        self.assertEqual(len(self.res['signals_all']), 511)
        self.assertEqual(self.res['signals_all'][:490], self.res['signals'])

    def test_adapter_signals_are_21_static_lines(self):
        extra = self.d.all_signals(self.inp)[490:]
        self.assertEqual(len(extra), 21)
        self.assertEqual({s['class'] for s in extra}, {'STATIC'})
        nets = {s['net'].split('/')[-1] for s in extra}
        self.assertEqual(nets, {'OCT_SELECTED'} | {f'OSC_OCT{i}' for i in range(6)})

    def test_static_adapter_orders_are_8_circuits_with_one_ground(self):
        o = self.d.ADAPTER_ORDERS
        self.assertEqual(o['ds79']['order'], [f'OSC_OCT{i}' for i in range(6)] + ['AGND', 'OCT_SELECTED'])
        self.assertEqual((len(o['ds79']['order']), o['ds79']['order'].count('AGND')), (8, 1))
        self.assertEqual(o['alternating_14']['order'].count('AGND'), 7)

    # review of 2026-11-14 23:18 UTC: each test fails on the code of part 1
    def test_finding_1_adapter_step_per_cable_in_use_and_at_one_length(self):
        ad = self.tab['adapter_link']
        got = {(c['name'], c['cable'], c['length_mm']) for c in ad['cases']}
        for cab in ('C81339', 'C29534'):
            for name in ('ds79', 'part_1'):
                self.assertTrue(any(g[:2] == (name, cab) for g in got), (name, cab))
        c8 = self.d.adapter_case(ad, 'part_1', 'C29534')
        c14 = self.d.adapter_case(ad, 'alternating_14', 'C68390')
        self.assertEqual(c8['length_mm'], c14['length_mm'])
        self.assertLess(c14['peak_V'], c8['peak_V'])

    def test_finding_2_static_victim_uses_precision_terms(self):
        par = {'Cm_F': 1e-13, 'Cv_total_F': 5e-12, 'M_eff_H': 1e-9}
        self.assertEqual(self.d.pair_level(par, 'ANALOGUE', 'STATIC', self.inp),
                         self.d.pair_level(par, 'ANALOGUE', 'PRECISION', self.inp))
        with self.assertRaises(self.d.NoVictimTerms):
            self.d.victim_terms('UNKNOWN')

    def test_finding_3_placements_take_both_directions(self):
        for how in (self.d.ONE, self.d.SIDE):
            pl = {(w, tuple(win), a, v) for w, win, a, v in self.d.placements(14, how, 40)}
            for w, win, a, v in pl:
                self.assertIn((w, win, v, a), pl)

    def test_finding_4_split_follows_the_list(self):
        orig = le.classified_signals
        try:
            le.classified_signals = lambda inp, root=le.ROOT: orig(inp, root)[10:]
            link, adapter = self.d.split_signals(self.inp)
        finally:
            le.classified_signals = orig
        self.assertEqual(len(link), 480)
        self.assertEqual(len(adapter), 21)
        self.assertEqual({x['class'] for x in adapter}, {'STATIC'})

    def test_logic_and_wiper_never_share_a_cable(self):
        base = {k: {'aggressor_class': k.split('>')[0], 'victim': k.split('>')[1]}
                for k in ['LOGIC>WIPER', 'LOGIC>LOGIC', 'ANALOGUE>ANALOGUE']}
        rows = self.d.pairs_allowed(base)
        self.assertEqual([r[0] for r in rows], ['ANALOGUE>ANALOGUE', 'LOGIC>LOGIC'])
        self.assertEqual(dict((r[0], r[3]) for r in rows)['LOGIC>LOGIC'], self.d.SIDE)

    def test_configured_window_is_the_whole_cable(self):
        self.assertGreaterEqual(self.inp['ds62']['window_half_width']['value'],
                                max(c['circuits'] for c in self.inp['ds62']['cables']))
        for n in (14, 26):
            full, part = self.d.full_vs_clipped(self.inp, n)
            self.assertEqual(full, part)

    def test_a_narrow_window_overstates_coupling(self):
        full, part = self.d.full_vs_clipped(self.inp, 26, half=4)
        self.assertGreater(part['Cm_F'], full['Cm_F'])
        self.assertGreater(part['M_eff_H'], full['M_eff_H'])

    def test_rows_above_one_are_reported_as_needs_design(self):
        above = self.tab['above_1']
        self.assertTrue(above)
        self.assertTrue(all(r['ratio'] > 1.0 for r in above))
        self.assertTrue(all(r['ratio'] <= 1.0 for r in self.tab['table'] if r not in above))
        readme = (le.OUT / 'README.md').read_text()
        self.assertIn('## DS-62 at the lengths in use (NEEDS_DESIGN)', readme)

    def test_largest_ratio_per_length_is_the_table_maximum(self):
        for L, r in self.tab['largest_ratio_per_length'].items():
            m = max(x['ratio'] for x in self.tab['table'] if x['length_mm'] == float(L))
            self.assertEqual(r['ratio'], m)


class AttemptA4Part2(unittest.TestCase):
    """a4 part 2: gate checks 3 and 4 on the record of the room study."""

    @classmethod
    def setUpClass(cls):
        import link_ratios
        cls.lr = link_ratios
        cls.inp = le.load_inputs()
        cls.links = link_ratios.load_record()
        cls.out = json.loads((le.OUT / 'link-ratios.json').read_text())
        cls.res = json.loads((le.OUT / 'results.json').read_text())

    def test_record_projection_is_the_one_read(self):
        self.assertEqual(self.lr.projection_sha256(self.links), self.inp['link_record']['projection_sha256'],
                         'the record changed: check the change and pin the new projection')

    def test_record_projection_goes_stale_when_a_position_changes(self):
        links = copy.deepcopy(self.links)
        p = links[0]['positions']
        p[0], p[-1] = dict(p[-1], pos=p[0]['pos']), dict(p[0], pos=p[-1]['pos'])
        self.assertNotEqual(self.lr.projection_sha256(links), self.inp['link_record']['projection_sha256'])

    def test_record_counts(self):
        kinds = [p['kind'] for l in self.links for p in l['positions']]
        self.assertEqual((len(self.links), kinds.count('signal'), kinds.count('ground'), kinds.count('unused')), (61, 511, 322, 339))
        self.assertEqual(len(self.out['links']), 61)
        self.assertEqual(sum(1 for r in self.out['links'] if r['host']), 20)
        self.assertEqual(sum(len(r['riders']) for r in self.out['links']), 42)

    def test_record_signals_equal_signals_all(self):
        rec = sorted((p['site'], p['net'], p['class']) for l in self.links for p in l['positions'] if p['kind'] == 'signal')
        mine = sorted((x['pair'], x['net'], x['class']) for x in self.res['signals_all'])
        self.assertEqual(len(mine), 511)
        self.assertEqual(rec, mine)

    def test_every_directed_pair_is_evaluated(self):
        self.assertEqual(self.out['missing_references'], [])
        for l, r in zip(self.links, self.out['links']):
            sig = [p for p in l['positions'] if p['kind'] == 'signal']
            n_agg = sum(1 for p in sig if p['class'] in ('LOGIC', 'ANALOGUE', 'PRECISION'))
            self.assertEqual(r['pairs_evaluated'], n_agg * (len(sig) - 1), l['id'])

    def test_the_rule_holds_on_the_record(self):
        self.assertEqual(self.out['rule_breaks'], {})
        logic = [r for r in self.out['rules'] if r['logic_runs'] or r['single_logic']]
        self.assertEqual(len(logic), 10)

    def test_fault_injection_breaks_the_rule(self):
        l = next(x for x in self.links if x['id'] == 'P-K-P-L13.01.01.01')
        bad = copy.deepcopy(l)
        p = bad['positions']
        p[1] = dict(p[2], pos=2)  # a logic line in place of the ground beside an analogue line at position 1
        self.assertTrue(self.lr.rule_check(bad)['breaks'])
        ad = copy.deepcopy(next(x for x in self.links if x['joint'] == 'O-K'))
        ad['positions'][0], ad['positions'][7] = dict(ad['positions'][7], pos=1), dict(ad['positions'][0], pos=8)
        self.assertTrue(any('DS-79' in b for b in self.lr.rule_check(ad)['breaks']))

    def test_part1_reference_for_analogue_pairs(self):
        r = next(x for x in self.out['links'] if x['largest_pair'] and x['largest_pair']['pair'] == 'ANALOGUE>ANALOGUE')
        self.assertAlmostEqual(r['largest_pair']['harness_min_V'] * 1000, 1.115, places=3)

    def test_needs_design_links_and_remedy(self):
        above = {r['id']: r for r in self.out['links'] if r['ratio'] and r['ratio'] > 1.0}
        self.assertEqual(set(above), set(self.out['links_above_1']))
        self.assertEqual(self.out['verdict'], 'NEEDS_DESIGN' if above else 'DONE')
        for r in above.values():
            x = r['remedy_ds77']
            if x['grounds_moved_in']:
                self.assertLessEqual(x['ratio_after'], 1.0)
                self.assertEqual(len(x['order_after']), r['circuits'])
            else:
                self.assertIsNone(x['ratio_after'])

    def test_remedy_keeps_size_and_rule(self):
        l = next(x for x in self.links if x['id'] == 'P-K-P-L07')
        t = self.lr.with_grounds_in_runs(l, 1)
        self.assertEqual(len(t['positions']), l['circuits'])
        self.assertEqual(self.lr.rule_check(t)['breaks'], [])
        self.assertEqual(sorted(p['net'] for p in t['positions'] if p['kind'] == 'signal'),
                         sorted(p['net'] for p in l['positions'] if p['kind'] == 'signal'))

    def test_more_contacts_less_current_and_a2_covers(self):
        d = le.pp.load()
        a = self.lr.worst_contact_at(self.inp, 'P', 1, 2, 50.0, d)
        b = self.lr.worst_contact_at(self.inp, 'P', 10, 2, 50.0, d)
        self.assertLess(b, a)
        gs = self.out['ground_share']
        for x in gs['branches']:
            self.assertLessEqual(x['one_contact_A']['one_post_open'], gs['a2_one_post_open_one_ground_A'] + 1e-12)
            self.assertTrue(x['within']['0.35'])
            self.assertGreaterEqual(x['fewest_on_a_link'], 1)

    def test_adapter_ground_has_no_dc(self):
        for x in self.out['adapter_return']:
            self.assertEqual((x['ground_contacts'], x['dc_A']), (1, 0.0))
            self.assertLess(x['step_into_ground_A'], x['step_all_lines_A'])


class KernelReviewRegressions(unittest.TestCase):
    """Four independently reviewed latent kernel failures on pinned main."""

    @classmethod
    def setUpClass(cls):
        import harness_baseline
        import link_ratios
        cls.hb, cls.lr = harness_baseline, link_ratios
        cls.inp = le.load_inputs()

    def test_same_class_harness_reference_includes_both_directions(self):
        pats = [{'id': 'asymmetric', 'classes': ['LOGIC', 'G', 'LOGIC'], 'cut_length_mm': 50}]
        with patch.object(self.hb, 'harness_pair_parameters', side_effect=lambda inp, classes, a, v, length, eps: {'a': a, 'Cm_F': 0.0, 'M_eff_H': 0.0}):
            with patch.object(self.hb, 'level', side_effect=lambda par, agg, vic, inp: (1.0 + par['a'], 1.0)):
                rows, _ = self.hb.baseline(self.inp, pats)
        self.assertEqual(rows['LOGIC>LOGIC']['triples'], 2)
        self.assertEqual(rows['LOGIC>LOGIC']['max_V'], 3.0)

    def test_mixed_length_share_bounds_each_possible_contact(self):
        d = le.pp.load()
        lengths = [40.0, 80.0]
        got = self.lr.worst_contact_mixed_at(self.inp, 'P', lengths, 2, d)
        rj = le.pp.joint_ohm(d, le.pp.branch_gap('P', d))
        expected = []
        for i, length in enumerate(lengths):
            rmin, _ = self.lr.ground_paths_at(self.inp, length)
            other = self.lr.ground_paths_at(self.inp, lengths[1-i])[1]
            alt = le.pp.v(d, 'return_plane_ohm') + 1 / (1 / other + 2 / rj)
            expected.append(le.pp.v(d, 'single_return_A') * alt / (rmin + alt))
        self.assertAlmostEqual(got, max(expected))
        self.assertNotAlmostEqual(got, self.lr.worst_contact_at(self.inp, 'P', 2, 2, 40.0, d))

    def test_missing_or_nonfinite_evidence_never_passes(self):
        good = {'links': [{'id': 'x', 'ratio': None, 'pairs_without_reference': []}], 'rules': [{'id': 'x', 'breaks': []}],
                'missing_references': []}
        self.assertEqual(self.lr.verdict(good)[0], 'DONE')  # intentional STATIC/WIPER-only null
        for change in ({'missing_references': ['LOGIC>UNKNOWN']},
                       {'links': [{'id': 'x', 'ratio': float('nan'), 'pairs_without_reference': []}]},
                       {'links': [{'id': 'x', 'ratio': float('inf'), 'pairs_without_reference': []}]}):
            bad = dict(good, **change)
            self.assertNotEqual(self.lr.verdict(bad)[0], 'DONE')

    def test_unknown_signal_class_is_not_silently_quiet(self):
        with self.assertRaises(ValueError):
            self.hb.aggressor_of('UNKNOWN')
        link = copy.deepcopy(next(x for x in self.lr.load_record() if x['joint'] == 'O-K'))
        link['positions'][0]['class'] = 'UNKNOWN'
        with self.assertRaises(ValueError):
            self.lr.link_pairs(self.inp, link, {})

    def test_projection_includes_branch_and_reported_totals(self):
        link = copy.deepcopy(self.lr.load_record()[0])
        initial = self.lr.projection_sha256([link])
        for field, value in (('joint', 'JL-P via K'), ('front_board', 'JR'), ('grounds', 99), ('unused', 99)):
            changed = dict(link, **{field: value})
            self.assertNotEqual(self.lr.projection_sha256([changed]), initial, field)


if __name__ == '__main__':
    unittest.main()
