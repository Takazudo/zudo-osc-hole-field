"""Unit tests for the ST-05 thermal paper screen: no network, no KiCad."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_inputs as ex
import thermal as T
import thermal_readme as R

STATUSES = {'SOURCED', 'DERIVED', 'ASSUMED', 'UNSOURCED'}


class Screen(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()
        cls.normal = T.power_map(cls.d, 'normal')
        cls.contract = T.power_map(cls.d, 'contract')

    def test_inputs_and_pins_match_the_repository(self):
        self.assertEqual(ex.check(self.d), [])

    def test_readme_is_the_rendering(self):
        self.assertEqual(R.README.read_text(), R.render())

    def test_every_term_has_value_unit_status_and_source(self):
        for name, t in self.d['terms'].items():
            self.assertEqual(set(t) - {'range', 'alternatives'}, {'value', 'unit', 'status', 'source'}, name)
            self.assertIn(t['status'], STATUSES, name)
            self.assertTrue(t['source'], name)
            if t['status'] == 'UNSOURCED':
                self.assertIsNone(t['value'], name)

    def test_every_cited_pin_exists(self):
        ids = {p['id'] for p in self.d['provenance']['pins']}
        for name, t in self.d['terms'].items():
            for pin in re.findall(r'pins? ([a-z0-9][A-Za-z0-9_\-+.]*(?:, [a-z0-9][A-Za-z0-9_\-+.]*)*)', t['source']):
                for one in pin.split(', '):
                    if one.startswith(('ledger-', 'partition-', 'plan-', 'gates-', 'stack-', 'fixings-', 'fact-',
                                       'decision-', 'led-', 'posts-', 'osc-', 'floorplan-', 'board-')):
                        self.assertIn(one, ids, name)

    def test_no_whole_campaign_file_is_pinned(self):
        for p in self.d['provenance']['pins']:
            if p['path'].startswith('circuit/orchestration/campaigns/'):
                self.assertIn('row', p)
            self.assertTrue({'object', 'row', 'line_prefix', 'fact_id'} & set(p), p['id'])


class PowerMap(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()
        cls.normal = T.power_map(cls.d, 'normal')
        cls.contract = T.power_map(cls.d, 'contract')

    def test_board_totals_sum_to_the_instrument(self):
        for m in (self.normal, self.contract):
            self.assertAlmostEqual(sum(m['boards'].values()) + m['external_W'], m['input_W'], places=9)
            self.assertLess(abs(m['residual_W']), 1e-9)

    def test_normal_load_is_34_83_W_and_not_35_4(self):
        self.assertAlmostEqual(self.normal['input_W'], 12 * 1.431825194 + 12 * 1.392592182 + 5 * 0.187873956, places=9)
        self.assertAlmostEqual(round(self.normal['input_W'], 2), 34.83)
        cases = T.ledger_case_W(self.d)
        self.assertAlmostEqual(cases['conditional_SH_short_resistor_case_mA'], 35.4, delta=0.01)
        self.assertGreater(abs(cases['two_feed_total_mA'] - 35.4), 0.5)

    def test_contract_is_41_1_W(self):
        self.assertAlmostEqual(self.contract['input_W'], 41.1, places=9)

    def test_bleeder_residual_is_two_inlets(self):
        bleed = T.all_rows(self.d)[-1]['mA']
        per = T.term(self.d, 'bleeder_per_inlet_mA')
        for got, one in zip(bleed, per):
            self.assertAlmostEqual(got, 2 * one, places=5)

    def test_every_row_is_classified_and_located(self):
        pk = T.packages_by(self.d)
        for row in T.all_rows(self.d):
            rule, frac, ext = T.classify(self.d, row, pk)
            self.assertAlmostEqual(sum(frac.values()), 1.0, places=9, msg=row['id'])
            self.assertGreaterEqual(ext, 0.0)
        self.assertEqual(len(T.all_rows(self.d)), 362 + 10 + 1)

    def test_external_loads_are_5V_into_10k(self):
        self.assertAlmostEqual(self.normal['external_W'], T.output_count(self.d) * 25 / 10000, places=12)

    def test_k_carries_most(self):
        self.assertGreater(self.normal['boards']['K'], 0.6 * self.normal['internal_W'])

    def test_package_power_conserves_ic_rows(self):
        pk = T.packages_by(self.d)
        ic = sum(T.row_power_W(self.d, r['mA']) for r in T.all_rows(self.d)
                 if T.classify(self.d, r, pk)[0] in ('IC', 'NOISE2', 'REF', 'LOGIC'))
        self.assertAlmostEqual(sum(T.package_powers(self.d).values()), ic, places=9)


class Enclosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()

    def test_area_drop_reproduces_the_plan(self):
        drop = 1 - T.outer_area_m2(self.d, 34) / T.outer_area_m2(self.d, 120)
        self.assertAlmostEqual(drop, T.term(self.d, 'plan_area_drop'), delta=0.005)

    def test_plan_method_reproduces_the_rise_ranges(self):
        lo34, hi34 = T.plan_method(self.d, 34, 35.4)[0], T.plan_method(self.d, 34, 41.1)[1]
        lo120, hi120 = T.plan_method(self.d, 120, 35.4)[0], T.plan_method(self.d, 120, 41.1)[1]
        self.assertEqual((round(lo34), round(hi34)), (17, 22))
        self.assertEqual((round(lo120), round(hi120)), (12, 15))

    def test_shell_balance_matches_the_network(self):
        for depth in (40, 120):
            for o in ('V', 'H'):
                for lv in ('low', 'high'):
                    net = T.network(self.d, depth, o, lv, 'contract')
                    q = T.power_map(self.d, 'contract')['internal_W']
                    self.assertAlmostEqual(net['rise']['shell'], T.surface_rise(self.d, depth, o, lv, q), places=4)

    def test_low_coefficients_are_hotter(self):
        for depth in (40, 120):
            for o in ('V', 'H'):
                hi = T.network(self.d, depth, o, 'high', 'normal')
                lo = T.network(self.d, depth, o, 'low', 'normal')
                for n in hi['rise']:
                    self.assertGreater(lo['rise'][n], hi['rise'][n] - 1e-9, (depth, o, n))

    def test_resting_rear_wall_makes_lying_worse(self):
        q = T.power_map(self.d, 'contract')['internal_W']
        for depth in (40, 34, 120):
            self.assertGreater(T.surface_rise(self.d, depth, 'H', 'low', q), T.surface_rise(self.d, depth, 'V', 'low', q))

    def test_thirty_four_mm_does_not_fit(self):
        cases = self.d['inputs']['stack']['enclosure_depth_cases']
        self.assertAlmostEqual(cases[1]['rear_part_clearance_mm'], -3.2)
        self.assertAlmostEqual(self.d['inputs']['stack']['K_rear_parts_z_mm'], -37.2)

    def test_vent_and_supply_rows_move_the_right_way(self):
        base = T.network(self.d, 40, 'V', 'low', 'contract')['rise']['K']
        self.assertLess(T.network(self.d, 40, 'V', 'low', 'contract', vent_cm2=20.0)['rise']['K'], base)
        self.assertGreater(T.network(self.d, 40, 'V', 'low', 'contract', supply='inside', eta=0.75)['rise']['K'], base)

    def test_wall_changes_the_readme(self):
        d = copy.deepcopy(self.d)
        d['terms']['wall_mm']['value'] = 3.0
        self.assertGreater(T.outer_area_m2(d, 40), T.outer_area_m2(self.d, 40))


class Interior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()

    def test_gaps_follow_the_planes(self):
        pairs = {(p['upper'], p['lower']): p for p in T.facing_pairs(self.d, 40)}
        self.assertAlmostEqual(pairs[('JL', 'K')]['gap_mm'], 19.0)
        self.assertAlmostEqual(pairs[('JR', 'K')]['gap_mm'], 19.0)
        self.assertAlmostEqual(pairs[('P', 'K')]['gap_mm'], 17.0)
        self.assertAlmostEqual(pairs[('O1', 'K')]['gap_mm'], 13.0)
        self.assertAlmostEqual(pairs[('EL', 'P')]['gap_mm'], 7.2)
        self.assertAlmostEqual(pairs[('K', 'shell')]['gap_mm'], 7.8)
        k_area = T.polygon_area(self.d['inputs']['planes_40']['K']['outline'])
        self.assertAlmostEqual(pairs[('K', 'shell')]['area_mm2'], k_area, places=6)

    def test_column_areas_cover_the_box(self):
        x0, y0, x1, y1 = T.term(self.d, 'enclosure_internal_xy_mm')
        for depth in (40, 120):
            planes = T.planes_for(self.d, depth)
            covered = sum((r[2] - r[0]) * (r[3] - r[1]) for r, m in T.compressed_cells(self.d, planes))
            self.assertAlmostEqual(covered, (x1 - x0) * (y1 - y0), places=6)

    def test_nusselt_floor_and_conduction_case(self):
        for o in ('V', 'H'):
            for lv in ('low', 'high'):
                for g in T.network(self.d, 40, o, lv, 'contract')['gaps']:
                    self.assertGreaterEqual(g['Nu'], 1.0)
                    if lv == 'low':
                        self.assertEqual(g['Nu'], 1.0)

    def test_solver(self):
        self.assertEqual([round(x, 9) for x in T.solve_linear([[2.0, 1.0], [1.0, 3.0]], [3.0, 5.0])], [0.8, 1.4])

    def test_radiation_coefficient(self):
        h = T.h_rad(self.d, 300.0, 300.0, 1.0, 1.0)
        self.assertAlmostEqual(h, 4 * T.term(self.d, 'sigma') * 300.0 ** 3, places=9)


class HotParts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()

    def test_ten_classes_with_as3340_first_and_bleeder_densest(self):
        top = T.top_ten(self.d, 'normal')
        self.assertEqual(len(top), 10)
        self.assertEqual(top[0]['symbol'], 'AS3340D')
        densest = max(top, key=lambda c: c['density_mW_mm2'])
        self.assertTrue(densest['symbol'].startswith('RC0603FR-072K2L'))

    def test_no_ic_bundle_holds_a_thermal_resistance(self):
        survey = self.d['inputs']['bundle_thermal_survey']
        for sym, (_, need) in R.LIMIT_FACTS.items():
            for bundle, ids in survey.items():
                self.assertFalse(any(re.search(r'rth|theta|junction', i) for i in ids), bundle)

    def test_bleeder_figures_come_from_its_bundle(self):
        fact = self.d['inputs']['bundle_facts']['fact-power-bleeder-application']
        text = json.dumps(ex.bundle_facts()[1]['fact-power-bleeder-application'][1])
        self.assertEqual(fact['bundle'], 'component-yageo-rc0603fr-072k2l')
        for figure in ('400K/W', '71.942', '110C'):
            self.assertIn(figure, text)
        curve = self.d['inputs']['bundle_facts']['fact-power-bleeder-derating']['value']
        self.assertEqual(curve, {'full_power_temperature_C': 70, 'zero_power_temperature_C': 155})
        self.assertEqual(T.term(self.d, 'resistor_power_curve')['T_zero_C'], curve['zero_power_temperature_C'])

    def test_hc_limit_from_bundles(self):
        for fid in ('fact-schmitt-temperature', 'fact-flipflop-temperature'):
            self.assertEqual(self.d['inputs']['bundle_facts'][fid]['value']['maximum'],
                             T.term(self.d, 'hc_logic_ambient_max_C'))

    def test_as3340_split(self):
        s = T.as3340_split_W(self.d)
        self.assertAlmostEqual(s['core_W'] + s['vee_driver_W'], 12 * 0.0065 + 12 * 0.010, places=9)
        self.assertAlmostEqual(s['row_W'], 0.198, places=9)

    def test_needs_design_verdict(self):
        k_lo = 40 + T.network(self.d, 40, 'H', 'low', 'contract')['rise']['K']
        self.assertGreater(k_lo, T.term(self.d, 'hc_logic_ambient_max_C'))
        self.assertIn('NEEDS_DESIGN', R.README.read_text().splitlines()[0])


class Regions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()

    def test_sensitive_sites(self):
        rows = T.sensitive_table(self.d)
        self.assertEqual(sum(1 for r in rows if r['function'].endswith('core')), 5)
        self.assertEqual(sum(1 for r in rows if r['function'].endswith('REF5050')), 24)
        for r in rows:
            self.assertGreater(r['distance_mm'], 0.0)

    def test_k_cells_conserve_power(self):
        cells, meta = T.k_cells(self.d, 'contract')
        self.assertAlmostEqual(sum(c['W'] for c in cells.values()), T.power_map(self.d, 'contract')['boards']['K'], places=6)
        self.assertAlmostEqual(sum(c['area_mm2'] for c in cells.values()), meta['K_area_mm2'], places=6)
        self.assertAlmostEqual(sum(c['rise_bound_K'] * c['area_mm2'] for c in cells.values()), 0.0, places=3)

    def test_post_conductance_is_positive_and_not_credited(self):
        g, area = T.post_conductance(self.d)
        self.assertTrue(0 < g[0] < g[1])
        self.assertEqual(sum(1 for f in self.d['inputs']['fixings_active'] if f['kind'] == 'post'), 18)
        self.assertEqual(len(self.d['inputs']['fixings_active']), 22)


if __name__ == '__main__':
    unittest.main()
