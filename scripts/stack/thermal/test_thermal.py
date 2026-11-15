"""Unit tests for the ST-05 thermal paper screen: no network, no KiCad."""
import copy
import json
import re
import sys
import unittest
from pathlib import Path
from unittest import mock

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

    def test_plan_row_figures_are_reproduced(self):
        plan = T.term(self.d, 'plan_heat_W')
        self.assertEqual(plan, [34.83, 41.1])
        self.assertAlmostEqual(T.power_map(self.d, 'normal')['input_W'], plan[0], delta=0.005)
        self.assertAlmostEqual(T.power_map(self.d, 'contract')['input_W'], plan[1], places=9)

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
        self.assertNotEqual(R.render(d), R.render(self.d))


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

    def test_hot_set_is_every_k_package_of_100_mW(self):
        hot = T.hot_packages(self.d)
        self.assertEqual(len(hot), 91)
        self.assertAlmostEqual(sum(h['W'] for h in hot), 13.374, places=3)
        self.assertTrue(all(h['W'] >= 0.1 - 1e-12 for h in hot))

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

    def test_done_with_the_heading_of_ds95(self):
        head = R.README.read_text().splitlines()[0]
        self.assertEqual(self.d['status'], 'DONE')
        self.assertIn('is NOT SHOWN met in either case depth', head)
        self.assertIn('#64 measures it', head)
        self.assertNotIn('NEEDS_DESIGN', head)

    def test_readme_uses_no_pass_or_fail(self):
        self.assertIsNone(re.search(r'\b(pass|passes|passed|fail|fails|failed|failure)\b', R.README.read_text(), re.I))


class Regions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()

    def test_sensitive_sites(self):
        rows = T.sensitive_table(self.d)
        self.assertEqual(sum(1 for r in rows if r['function'].endswith('core')), 5)
        self.assertEqual(sum(1 for r in rows if r['function'].endswith('REF5050')), 24)
        self.assertEqual(sum(1 for r in rows if r['hot_near']), 34)
        self.assertNotIn('distance_mm', rows[0])

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


class Findings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()

    def copy(self):
        return copy.deepcopy(self.d)

    def test_finding_01_headings_follow_the_comparison(self):
        d = self.copy()
        for sym in ('SN74HC14DR', 'SN74HC74DR', 'CL10A105KB8NNNC'):
            for r in d['inputs']['operating_ranges'][sym]:
                r['maximum'] = 150
        head = R.render(d).splitlines()[0]
        self.assertIn('150 °C limit', head)
        self.assertIn('is MET ON PAPER in both case depths', head)
        fake = {'box_mm': (200.0, 0.0, 300.0, 50.0), 'cells': [(4, 0)], 'lateral_K': (1.0, 2.0), 'hottest': (4, 0)}
        with mock.patch.object(T, 'warm_region', lambda d, cells: fake, create=True):
            text = '\n'.join(R.item5(R.facts(self.d)))
        self.assertIn('x 200 to 300, y 0 to 50, 1.0 to 2.0 K', text.splitlines()[0])

    def test_finding_02_power_outside_the_network_is_an_error(self):
        d = self.copy()
        real = T.power_map

        def extra(dd, case='normal'):
            m = real(dd, case)
            return dict(m, boards=dict(m['boards'], X9=1.0))
        with mock.patch.object(T, 'power_map', extra):
            with self.assertRaises(ValueError):
                T._network(d, 40, 'V', 'low', 'normal', 'outside', None, 0.0, None, 0.0)

    def test_finding_03_cells_follow_k_and_the_cell_term(self):
        d = self.copy()
        d['terms']['cell_mm']['value'] = 40.0
        self.assertEqual(T.cell_name(d, (1, 2)), 'x 40 to 80, y 80 to 120')
        cells, meta = T.k_cells(d, 'normal')
        self.assertAlmostEqual(sum(c['area_mm2'] for c in cells.values()), meta['K_area_mm2'], places=6)
        self.assertAlmostEqual(sum(c['W'] for c in cells.values()), T.power_map(d, 'normal')['boards']['K'], places=6)
        real = T.k_power_points

        def outside(dd, case='normal'):
            pts, spread = real(dd, case)
            return pts + [([2000.0, 2000.0], 1.0)], spread
        with mock.patch.object(T, 'k_power_points', outside):
            with self.assertRaises(ValueError):
                T.k_cells(self.copy(), 'normal')

    def test_finding_04_iterations_must_converge(self):
        with mock.patch.object(T, 'NETWORK_ROUNDS', 1, create=True):
            with self.assertRaises(RuntimeError):
                T._network(self.copy(), 40, 'V', 'low', 'normal', 'outside', None, 0.0, None, 0.0)
        with mock.patch.object(T, 'SURFACE_ROUNDS', 1, create=True):
            with self.assertRaises(RuntimeError):
                T.surface_rise(self.copy(), 40, 'V', 'low', 30.0)

    def test_finding_05_both_ends_of_a_row_read_one_board(self):
        boards = {p['board'] for p in T.class_places(self.d, 'SN74HC14DR')}
        self.assertEqual(boards, {'K', 'P'})
        for sym in T.limit_classes(self.d) + T.no_limit_classes(self.d):
            for depth in T.DEPTHS:
                c = T.class_comparison(self.d, sym, depth)
                for o in T.ORIENTS:
                    self.assertEqual(c['orients'][o]['worst']['board'], c['orients'][o]['best']['board'], (sym, depth, o))
        best = T.board_at_part(self.d, T.class_places(self.d, 'SN74HC14DR'), 40, 'V', 'low', 'high', board='P')
        self.assertEqual(best['board'], 'P')

    def test_finding_06_bleeder_note_stands_on_its_own(self):
        text = '\n'.join(R.item4(R.facts(self.d)))
        self.assertIn('### Bleeder note for #57', text)
        note = T.bleeder_note(self.d, 40, 'H')
        self.assertEqual([x['ref'] for x in note], ['R301', 'R302', 'R303'])
        for x in note:
            self.assertAlmostEqual(x['body_C'], x['board_C'] + 0.071942 * 400.0, places=6)

    def test_finding_07_a_site_outside_the_cells_renders(self):
        real = T.sensitive_table

        def with_gap(d, *a, **k):
            rows = [dict(x) for x in real(d, *a, **k)]
            for x in rows:
                if x['function'].endswith('REF5050') and not x['function'].startswith(('OCTAVE', 'H1', 'H2', 'F')):
                    x.update(rise_40=None, rise_120=None, cell=None)
                    break
            return rows
        with mock.patch.object(T, 'sensitive_table', with_gap):
            text = '\n'.join(R.item5(R.facts(self.d)))
        self.assertIn('## 5.', text)

    def test_finding_08_ambient_is_the_term_everywhere(self):
        d = self.copy()
        d['terms']['ambient_C']['value'] = 30.0
        with mock.patch.object(T, 'load', lambda path=None: d):
            text = R.render()
        self.assertIsNone(re.search(r'\b40 (°C|degC)', text))
        self.assertIn('at 30 °C ambient', text.splitlines()[0])
        k_lo = T.term(self.d, 'ambient_C') + T.network(self.d, 40, 'H', 'low', 'contract')['rise']['K']
        self.assertGreater(k_lo, T.term(self.d, 'hc_logic_ambient_max_C'))

    def test_finding_09_check_reports_a_pin_no_longer_produced(self):
        screen = self.copy()
        screen['provenance']['pins'].append({'id': 'retired-pin', 'path': 'x', 'row': 'x', 'sha256': '0'})
        self.assertIn('stored pin no longer produced retired-pin', ex.check(screen))

    def test_finding_10_survey_width_decides_the_thermal_figures(self):
        survey = self.d['inputs']['bundle_thermal_survey']
        for ids in survey.values():
            for i in ids:
                self.assertTrue(ex.THERMAL_WORDS.search(i), i)
        for sym in T.no_limit_classes(self.d) + T.limit_classes(self.d):
            self.assertEqual(T.thermal_figures(self.d, sym), [], sym)
        d = self.copy()
        d['inputs']['bundle_thermal_survey']['component-ti-lm393bidr'] = ['fact-comparator-power-derating']
        self.assertEqual(T.thermal_figures(d, 'LM393BIDR'), ['fact-comparator-power-derating'])


class AttemptA2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()

    def test_low_heat_load_from_bundle_typicals(self):
        low = T.power_map(self.d, 'low')
        self.assertAlmostEqual(low['input_W'], 28.111, places=3)
        self.assertAlmostEqual(low['boards']['K'], 19.412, places=3)
        self.assertLess(abs(low['residual_W']), 1e-9)
        facts = {x['fact'] for x in T.low_heat_rows(self.d).values()}
        self.assertEqual(facts, {'fact-op-precision-d-quiescent-current', 'fact-op-precision-quiescent-current',
                                 'fact-op-audio-quiescent-current', 'fact-fault-switch-t-normal-supply-current'})
        self.assertEqual(T.all_rows(self.d)[-1]['mA'], T.case_rows(self.d, 'low')[-1]['mA'])

    def test_low_heat_rejects_a_row_off_its_basis(self):
        d = copy.deepcopy(self.d)
        row = next(r for r in d['inputs']['rows'] if r['label'] == 'OPA4196IDR')
        row['mA'][0] += 1.0
        with self.assertRaises(ValueError):
            T.low_heat_rows(d)

    def test_words(self):
        self.assertEqual(T.word(85.0, 85.0, 70.0), 'MET ON PAPER')
        self.assertEqual(T.word(85.0, 95.0, 85.1), 'EXCEEDED ON PAPER')
        self.assertEqual(T.word(85.0, 95.0, 80.0), 'NOT SHOWN')
        self.assertEqual(T.word(None, 50.0, 40.0), 'NOT SHOWN')

    def test_comparison_of_record(self):
        self.assertEqual(T.limit_classes(self.d), ['CL10A105KB8NNNC', 'SN74HC14DR', 'SN74HC74DR'])
        for sym in ('SN74HC00DR', 'CD74HC221M96'):
            self.assertIn(sym, T.no_limit_classes(self.d))
            self.assertIsNone(T.retained_limit(self.d, sym))
        for sym in T.limit_classes(self.d):
            for depth in T.DEPTHS:
                c = T.class_comparison(self.d, sym, depth)
                for o in T.ORIENTS:
                    w = c['orients'][o]['worst']
                    readings = [T.place_reading(self.d, p, depth, o, *T.ENDS['worst']) for p in T.class_places(self.d, sym)]
                    self.assertAlmostEqual(w['T_C'], max(x['T_C'] for x in readings), places=9)
                    if w['board'] == 'K':
                        self.assertAlmostEqual(w['T_C'], w['board_mean_C'] + w['lateral_K'], places=9)

    def test_capacitor_places_come_from_the_partition_report(self):
        places = T.class_places(self.d, 'CL10A105KB8NNNC')
        self.assertEqual([p['ref'] for p in places], ['C302', 'C304', 'C306'])
        self.assertTrue(all(p['board'] == 'K' for p in places))

    def test_plan_heat_figures_are_read_by_unit(self):
        line = '| Heat in a closed case | 12.5 W at one load and 40 W at another, 3 K and 2 mm | src | #64 NOT RUN |'
        self.assertEqual(ex.plan_heat_W(line), [12.5, 40.0])

    def test_final_places_floorplan_alone_without_the_key(self):
        placements = [{'ref': 'U1', 'x_mm': 1.0, 'y_mm': 2.0, 'side': 'F.Cu'},
                      {'ref': 'U2', 'x_mm': 3.0, 'y_mm': 4.0, 'side': 'B.Cu'}]
        places, source = ex.final_places({'links': []}, placements)
        self.assertEqual(source, {'read': 'floorplan', 'moved': 0, 'listed': 0, 'kept': 0})
        self.assertEqual(places['U1'], {'xy': [1.0, 2.0], 'side': 'F.Cu'})

    def test_final_places_from_the_displaced_rows(self):
        placements = [{'ref': 'U1', 'x_mm': 1.0, 'y_mm': 2.0, 'side': 'F.Cu'},
                      {'ref': 'U2', 'x_mm': 3.0, 'y_mm': 4.0, 'side': 'B.Cu'},
                      {'ref': 'U3', 'x_mm': 5.0, 'y_mm': 6.0, 'side': 'B.Cu'}]
        record = {'displaced_k_ic_packages': [
            {'ref': 'U1', 'symbol': 'X', 'old': {'xy': [1.0, 2.0], 'side': 'F.Cu'},
             'new': {'xy': [11.0, 12.0], 'side': 'B.Cu'}, 'moved_mm': 14.1, 'step': 'radius'},
            {'ref': 'U2', 'symbol': 'X', 'old': {'xy': [3.0, 4.0], 'side': 'B.Cu'}, 'new': None,
             'moved_mm': None, 'step': 'none'}]}
        places, source = ex.final_places(record, placements)
        self.assertEqual(source, {'read': 'gate record displaced_k_ic_packages', 'moved': 1, 'listed': 2, 'kept': 1})
        self.assertEqual(places['U1'], {'xy': [11.0, 12.0], 'side': 'B.Cu'})
        self.assertEqual(places['U2'], {'xy': [3.0, 4.0], 'side': 'B.Cu'})
        self.assertEqual(places['U3'], {'xy': [5.0, 6.0], 'side': 'B.Cu'})

    def test_link_figures_from_a_parsed_record(self):
        record = {'summary': {'links': 3, 'placed': 2, 'slots': 2}, 'links': [
            {'placed': True, 'direction': '+y', 'loop_mm': 10.0, 'cable_length_mm': 40.0,
             'geometry': {'slot': [0, 0, 8, 1.5], 'front_tail': [0, 0, 7.5, 5]}},
            {'placed': True, 'direction': '-x', 'loop_mm': 2.0, 'cable_length_mm': 30.0,
             'geometry': {'slot': [0, 0, 1.5, 4], 'front_tail': [0, 0, 5, 3.5]}},
            {'placed': False, 'direction': '+y', 'loop_mm': 99.0, 'cable_length_mm': 99.0,
             'geometry': {'slot': [0, 0, 99, 99], 'front_tail': [0, 0, 99, 99]}}]}
        self.assertEqual(ex.link_figures(record), {'links': 3, 'placed': 2, 'slots': 2, 'slot_area_mm2': 18.0,
                                                   'loop_plan_area_mm2': 82.0, 'cable_plan_area_mm2': 405.0})

    def test_place_source_is_printed(self):
        ps = self.d['inputs']['place_source']
        self.assertEqual(ps['moved'] + ps['kept'], ps['listed'])
        self.assertIn('Places: ' + R.place_source(self.d), R.README.read_text())

    def test_options_are_listed_and_none_selected(self):
        text = R.README.read_text()
        self.assertIn('| Case on feet, lying |', text)
        self.assertIn('none is selected', text)
        self.assertNotIn('selected option', text)


def reading(t_c, board='K'):
    return {'T_C': t_c, 'board': board, 'ref': 'U1', 'lateral_K': 0.0}


class AttemptA3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = T.load()
        cls.r = R.facts(cls.d)

    def changed(self, name, value):
        d = copy.deepcopy(self.d)
        d['terms'][name]['value'] = value
        return d, R.facts(d)

    def test_finding_01_class_word_is_the_worst_of_both_orientations(self):
        temps = {('V', 'low'): 90.0, ('V', 'high'): 60.0, ('H', 'low'): 89.0, ('H', 'high'): 86.0}
        fake = lambda d, places, depth, orient, case, level, board=None, h_resting=None: reading(temps[(orient, level)])
        with mock.patch.object(T, 'board_at_part', fake):
            c = T.class_comparison(self.d, 'SN74HC14DR', 40)
        self.assertEqual(c['worse'], 'V')
        self.assertEqual(c['orients']['V']['word'], 'NOT SHOWN')
        self.assertEqual(c['orients']['H']['word'], 'EXCEEDED ON PAPER')
        self.assertEqual(c['word'], 'EXCEEDED ON PAPER')

    def test_finding_02_classify_reads_whole_words_and_names_a_missing_led(self):
        pk = {}
        row = {'label': 'spotlight trim', 'instance': 'X', 'id': 'X:trim', 'count': 1}
        self.assertNotEqual(T.classify(self.d, row, pk)[0], 'POT')
        row = {'label': 'Indicator LEDs', 'instance': 'nowhere', 'id': 'nowhere:led', 'count': 1}
        with self.assertRaises(ValueError):
            T.classify(self.d, row, pk)
        row = {'label': 'misled rows', 'instance': 'nowhere', 'id': 'nowhere:x', 'count': 1}
        try:
            kind = T.classify(self.d, row, pk)[0]
        except ValueError:
            kind = 'raised'
        self.assertNotIn(kind, ('LED', 'raised'))

    def test_finding_03_the_figures_are_terms(self):
        cases = [('post_count', 20, R.item1, 'the 20 posts'),
                 ('post_joint_ohm', 0.0007, R.item1, '0.7 mOhm joint'),
                 ('link_ground_current_A', 0.061, R.item1, 'at most 0.061'),
                 ('h_conv_resting', 0.5, R.item2, 'on a table 0.5'),
                 ('eps_board', [0.7, 0.9], R.item3, 'board emissivity 0.70 to 0.90'),
                 ('solder_joint_limit_C', 120.0, R.item4, '120')]
        for name, value, item, text in cases:
            d, r = self.changed(name, value)
            self.assertIn(text, '\n'.join(item(r)), name)
        self.assertNotIn('110 °C', '\n'.join(R.item4(self.changed('solder_joint_limit_C', 120.0)[1])))
        d = copy.deepcopy(self.d)
        d['inputs']['planes_40']['K']['face_z_mm'] -= 1.0
        self.assertIn(f"K {d['inputs']['planes_40']['K']['face_z_mm']:g}/", R.plane_text(d))
        d = copy.deepcopy(self.d)
        d['inputs']['rails_V'] = [15.0] + list(d['inputs']['rails_V'][1:])
        self.assertNotAlmostEqual(T.as3340_split_W(d)['core_W'], T.as3340_split_W(self.d)['core_W'])
        self.assertIn(f"at most {R.f(1000 * R.max_limit_package_W(self.d), 0)} mW each", R.README.read_text())

    def test_finding_04_heading_is_computed(self):
        head = R.header(self.r)[0]
        self.assertNotIn('HC logic', head)
        for s in self.r['limit_classes']:
            self.assertIn(s, head)
        r = dict(self.r, cmp={k: dict(v, word='MET ON PAPER') for k, v in self.r['cmp'].items()})
        self.assertIn('is MET ON PAPER in both case depths', R.header(r)[0])
        self.assertEqual(R.depth_state({40: ['MET ON PAPER'], 120: ['EXCEEDED ON PAPER']}),
                         'reads MET ON PAPER at 40 mm and EXCEEDED ON PAPER at 120 mm')
        self.assertIn('the +50 °C operating range printed for the panel pots is EXCEEDED ON PAPER in both case depths', head)

    def test_finding_05_precision_is_not_taken_from_the_text(self):
        places = T.term(self.d, 'plan_compare_decimals')
        self.assertFalse(R.same('35', 35.4, places))
        self.assertFalse(R.same('35.0', 35.4, places))
        self.assertTrue(R.same('35.40', 35.4, places))

    def test_finding_06_largest_shift_reads_every_end_and_one_class(self):
        s = self.r['limit_classes'][0]
        best = R.largest_shift(self.r, [s])
        allx = [self.r['cmp'][(s, 40)]['orients'][o][e]['T_C'] - self.r['cmp'][(s, 120)]['orients'][o][e]['T_C']
                for o in T.ORIENTS for e in T.ENDS]
        self.assertAlmostEqual(abs(best['shift']), max(abs(x) for x in allx))
        d = copy.deepcopy(self.d)
        for sym in self.r['limit_classes'][1:]:
            d['inputs']['operating_ranges'][sym] = []
        self.assertEqual(T.limit_classes(d), [s])
        self.assertTrue(R.item4(R.facts(d))[0].startswith('## 4.'))

    def test_finding_08_a_wrong_argument_writes_nothing(self):
        for mod, attr in ((R, 'README'), (ex, 'SCREEN')):
            target = mock.MagicMock()
            with mock.patch.object(mod, attr, target):
                self.assertEqual(mod.main(['--chek']), 2)
                self.assertEqual(mod.main(['--check', 'x']), 2)
            target.write_text.assert_not_called()

    def test_finding_09_supply_inside_loss_is_on_the_input_power(self):
        pm = T.power_map(self.d, 'normal')
        out = T.network(self.d, 40, 'V', 'low', 'normal')['q_W']
        inside = T.network(self.d, 40, 'V', 'low', 'normal', supply='inside', eta=0.8)['q_W']
        self.assertAlmostEqual(inside - out, pm['input_W'] * (1 / 0.8 - 1), places=9)
        for eta in (None, 0.0, 1.5):
            with self.assertRaises(ValueError):
                T.network(self.d, 40, 'V', 'low', 'normal', supply='inside', eta=eta)

    def test_finding_10_no_dead_code_and_the_figures_are_rendered(self):
        self.assertFalse(hasattr(T, 'results'))
        self.assertFalse(hasattr(T, 'BOARDS_FRONT'))
        with mock.patch.object(T, 'thermal_figures', lambda d, s: ['fact-made-up']):
            self.assertIn('`fact-made-up`', '\n'.join(R.evidence_needs(self.r)))

    def test_a_range_not_of_record_makes_no_limit(self):
        d = copy.deepcopy(self.d)
        sym = 'SN74HC14DR'
        for x in d['inputs']['operating_ranges'][sym]:
            x['verdict'] = 'UNSOURCED'
        self.assertIsNone(T.retained_limit(d, sym))
        self.assertEqual(T.class_comparison(d, sym, 40)['word'], 'NOT SHOWN')
        for s in ('2MS1T1B1M2QES-5', '2MS3T1B1M2QES', 'SRBV160803', 'WQP518MA'):
            self.assertIsNone(T.retained_limit(self.d, s), s)
            self.assertIn('NO LIMIT RETAINED', R.limit_text(self.d, s), s)
        self.assertIn('absolute maximum', R.limit_text(self.d, 'APHHS1005QWF/D'))

    def test_every_panel_row_has_its_board_and_a_word(self):
        boards = {b for b in self.r['boards']}
        for row in self.r['panel']:
            self.assertIn(row['board'], boards)
            words = [row['depths'][dep]['word'] for dep in T.DEPTHS]
            self.assertTrue(any(words), row['symbol'])
            for w in words:
                self.assertIn(w, (None, *T.WORD_RANK))
        for s in T.panel_parts(self.d):
            ws = [row['depths'][40]['word'] for row in self.r['panel'] if row['symbol'] == s and row['depths'][40]['word']]
            if ws:
                self.assertEqual(T.panel_class_word(self.d, s, 40), T.worst_word(ws))

    def test_no_typed_word_in_a_heading(self):
        for line in R.render().splitlines():
            if line.startswith('#'):
                for w in T.WORD_RANK:
                    if w in line:
                        self.assertTrue(any(x in line for x in ('in both case depths', 'in either case depth', ' at 40 mm', ' at 120 mm',
                                                                'read EXCEEDED', 'from MET ON PAPER')), line)

    def test_ambient_at_the_limit_is_found_by_the_network(self):
        s = self.r['limit_classes'][0]
        limit = T.retained_limit(self.d, s)['limit_C']
        amb = T.ambient_at(self.d, s, 40, 'V', 'worst', limit)
        d = copy.deepcopy(self.d)
        d['terms']['ambient_C']['value'] = amb
        c = T.class_comparison(d, s, 40)
        self.assertAlmostEqual(c['orients']['V']['worst']['T_C'], limit, delta=0.05)

    def test_derating_curve_and_pot_power(self):
        fid = next(k for k, v in self.d['inputs']['panel_facts'].items() if 'derating' in k)
        self.assertEqual(T.derating_ratio(self.d, fid, 40.0), 1.0)
        self.assertAlmostEqual(T.derating_ratio(self.d, fid, 70.0), 0.33, places=6)
        self.assertIsNone(T.derating_ratio(self.d, fid, 70.1))
        d = copy.deepcopy(self.d)
        e = d['inputs']['pot_ends'][0]
        rail = next(iter(d['inputs']['rail_voltages_V']))
        e['pin1'], e['pin3'] = rail, 'AGND'
        res = d['inputs']['panel_facts'][f"fact-{e['value'].split('-')[-1].lower()}-resistance"]['value']
        w = T.pot_powers(d)[0]['W']
        self.assertAlmostEqual(w, d['inputs']['rail_voltages_V'][rail] ** 2 / (res * 0.8))
        self.assertTrue(all(x['W'] is None for x in T.pot_powers(self.d)))

    def test_proposal_names_a_pot_over_the_warm_region_a_switch_and_an_led(self):
        x = R.panel_sensors(self.d)
        self.assertTrue(T.in_box(x['region']['box_mm'], x['pot']['xy']))
        self.assertEqual(x['pot']['board'], 'P')
        self.assertTrue(x['switch']['symbol'].startswith('B3F'))
        self.assertEqual(x['led']['board'], 'JR')
        self.assertIn(x['pot']['ref'], R.README.read_text())


if __name__ == '__main__':
    unittest.main()
