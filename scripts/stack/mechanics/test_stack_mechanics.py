"""Tests for the ST-03 stack-mechanics calculator (attempts a2 to a6). No network, no KiCad."""
from pathlib import Path
import hashlib
import json
import math
import re
import unittest

import numpy as np

import stack_mechanics as sm
import stack_mechanics_a3 as a3mod
import stack_mechanics_geometry as geo

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def sha_rows(path, rows):
    """Digest of the cited decision rows only: the decision log gains rows with every record."""
    text = (ROOT / path).read_text()
    picked = []
    for row in rows:
        found = re.findall(r'^\| %s \|.*$' % re.escape(row), text, re.M)
        assert len(found) == 1, (row, len(found))
        picked.append(found[0])
    return hashlib.sha256('\n'.join(picked).encode()).hexdigest()


def pin_is_current(source):
    if 'json_key' in source:
        array = json.loads((ROOT / source['path']).read_text())[source['json_key']]
        return geo.fixings_array_sha256(array) == source['key_sha256']
    if 'rows' in source:
        return sha_rows(source['path'], source['rows']) == source['rows_sha256']
    return sha(source['path']) == source['sha256']


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = sm.load()
        cls.c = sm.Calc(cls.data)
        cls.readme = sm.README.read_text()


class TestReadmeIsRecomputed(Base):
    def test_every_block_matches_calculator(self):
        blocks = sm.render_all(self.data)
        found = {m.group(2): m.group(3) for m in sm.BLOCK.finditer(self.readme)}
        self.assertEqual(set(found), set(blocks))
        for name, text in blocks.items():
            self.assertEqual(found[name], text, name)

    def test_rendering_is_deterministic(self):
        self.assertEqual(sm.render_all(self.data), sm.render_all(json.loads(json.dumps(self.data))))

    def test_prose_numbers(self):
        c = self.c
        cap = [c.xy_row(j, 'capture') for j in ('JL', 'JR', 'P')]
        fin = [c.xy_row(j, 'final') for j in ('JL', 'JR', 'P')]
        initial = c.p['misalignment_mm']['initial']
        final = c.p['misalignment_mm']['final']
        self.assertTrue(math.isclose(min(r['median'] for r in cap), 0.344, abs_tol=0.005))
        self.assertTrue(math.isclose(max(r['median'] for r in cap), 0.401, abs_tol=0.005))
        self.assertLess(cap[0]['median'], initial['along'])
        self.assertGreater(cap[2]['median'], initial['along'])
        self.assertTrue(all(r['p95'] > initial['along'] for r in cap))
        self.assertTrue(all(r['median'] > final['across_single'] for r in fin))
        _, _, rss = c.selector_chain()
        self.assertTrue(math.isclose(rss, 0.267, abs_tol=0.002))
        self.assertIn('0.267', self.readme)
        gaps = {k: c.aperture_clearance(c.d['apertures'][k])[0] - c.aperture_baseline(c.d['apertures'][k])[1]
                for k in ('jack', 'pot', 'toggle', 'button', 'selector')}
        for k, v in {'jack': -0.120, 'pot': -0.070, 'toggle': -0.033, 'button': -0.027, 'selector': -0.003}.items():
            self.assertTrue(math.isclose(gaps[k], v, abs_tol=0.002), k)
        base = sum(len(v) for v in c.coverage('base').values())
        plus = sum(len(v) for v in c.coverage('plus').values())
        self.assertIn(f'{base} pairs miss it, and {plus} with the five', self.readme)
        self.assertTrue(math.isclose(c.dv('strain_design_limit') * 1e6, 593, abs_tol=1))
        self.assertTrue(math.isclose(c.delta_allow(c.dv('strain_design_limit'), 15.0), 0.028, abs_tol=0.001))
        self.assertTrue(math.isclose(c.delta_allow(c.dv('strain_design_limit'), 19.0), 0.045, abs_tol=0.001))
        self.assertTrue(math.isclose(c.toggle_gap(), 1.16, abs_tol=0.005))
        k = c.k_positions()
        self.assertEqual(k, 777)
        self.assertIn(f"{k * min(c.p['mating_force_N']):.0f} to {k * max(c.p['mating_force_N']):,.0f} N", self.readme)


class TestReviewFindings(Base):
    def test_f1_toggle_case_adds_the_p_mismatch(self):
        c = self.c
        pm_wc, pm_rss = c.wc_rss(c.p_mismatch_terms())
        case = [x for x in c.strain_cases() if x[0].startswith('P pulled by toggle')][0]
        self.assertAlmostEqual(case[3], c.toggle_gap() + pm_rss)
        self.assertTrue(math.isclose(case[3], 1.533, abs_tol=0.002))
        self.assertAlmostEqual(case[2], c.toggle_gap() + pm_wc)

    def test_f2_candidate_hash_is_recorded_and_current(self):
        current = sha(self.data['sources']['S-GEOM']['path'])
        self.assertEqual(self.data['sources']['S-GEOM']['sha256'], current)
        self.assertEqual(self.data['geometry']['sources']['stack_candidate']['sha256'], current)

    def test_f2_heights_from_da01_not_the_candidate(self):
        p = self.data['parameters']['da01']
        self.assertEqual(p['K_face_z_mm']['value'], -30.4)
        self.assertEqual(p['gap_mm']['value'], {'O': 12.8, 'P': 17.0, 'JL': 18.8, 'JR': 18.8, 'EL': 7.2})
        self.assertIn('S-DA01', p['gap_mm']['source'])

    def test_m1_four_limits(self):
        m = self.data['parameters']['da01']['misalignment_mm']['value']
        self.assertEqual((m['initial']['along'], m['initial']['across_single']), (0.39, 0.57))
        self.assertEqual((m['final']['along'], m['final']['across_single']), (0.07, 0.16))
        self.assertEqual(self.data['parameters']['da01']['el_misalignment']['status'], 'UNSOURCED')

    def test_m9_forces(self):
        p = self.data['parameters']['da01']
        self.assertEqual(p['mating_force_N']['value'], [0.84, 0.97, 1.33])
        self.assertEqual(p['unmating_force_N']['value'], [0.47, 0.98])
        n = self.c.k_positions() + sum(self.c.positions(x) for x in self.c.pairs('EL'))
        self.assertEqual(n, p['positions_per_side_total']['value'])

    def test_provisional_sites_are_provisional(self):
        sites = self.data['fixings']['provisional_tie_sites']
        self.assertEqual([s['xy'] for s in sites], [[202, 255], [252, 241], [227, 80], [227, 38], [108, 80]])
        self.assertIn('PROVISIONAL', json.dumps(self.data['fixings']))

    def test_worst_case_not_below_p95(self):
        for j in ('JL', 'JR', 'P', 'O', 'EL'):
            for phase in ('capture', 'final'):
                r = self.c.xy_row(j, phase)
                self.assertGreaterEqual(r['wc'] + 1e-6, r['p95'], (j, phase))
                self.assertGreaterEqual(r['p95'], r['median'], (j, phase))


class TestTerms(Base):
    def test_status_and_basis(self):
        sources = self.data['sources']
        for name, t in self.data['terms'].items():
            self.assertIn(t['status'], self.data['status_vocabulary'], name)
            self.assertIn('unit', t, name)
            if t['status'] == 'SOURCED':
                self.assertIn(t['source'], sources, name)
                self.assertTrue(t.get('locator'), name)
            elif t['status'] == 'ASSUMED':
                self.assertTrue(t.get('reason') and t.get('to_source'), name)
            else:
                self.assertTrue(t.get('formula'), name)

    def test_da01_parameters_have_a_basis(self):
        for name, t in self.data['parameters']['da01'].items():
            self.assertIn(t['status'], self.data['status_vocabulary'], name)
            if t['status'] == 'SOURCED':
                self.assertTrue(t.get('source') and t.get('locator'), name)
            elif t['status'] == 'DERIVED':
                self.assertTrue(t.get('formula'), name)
            else:
                self.assertTrue(t.get('reason') and t.get('to_source'), name)

    def test_stacker_a_follows_the_d3_rule(self):
        p = self.data['parameters']['da01']
        rule = p['body_clearance_rule_mm']['value']
        socket = p['socket_height_mm']['value']['single']
        for joint in ('O', 'P', 'JL', 'JR'):
            a_in = math.floor((p['gap_mm']['value'][joint] - socket - rule) / 25.4 / 0.005 + 1e-9) * 0.005
            self.assertAlmostEqual(p['stacker_A_in']['value'][joint], round(a_in, 3), msg=joint)

    def test_derived_terms_recompute(self):
        for name, value in self.c.derived().items():
            stored = self.data['terms'][name]['value']
            self.assertTrue(math.isclose(stored, value, rel_tol=2e-3, abs_tol=5e-4), (name, stored, value))

    def test_repository_sources_unchanged(self):
        for sid, s in self.data['sources'].items():
            if 'path' in s:
                self.assertTrue(pin_is_current(s), sid)
            if 'bundle' in s:
                self.assertEqual(sha(s['bundle']), s['bundle_sha256'], sid)

    def test_term_table_shows_each_status(self):
        for name, t in self.data['terms'].items():
            row = [ln for ln in self.readme.splitlines() if ln.startswith(f'| `{name}` |')]
            self.assertEqual(len(row), 1, name)
            self.assertIn(f"| {t['status']} |", row[0])


class TestGeometry(Base):
    def test_geometry_block_is_current(self):
        fresh = geo.derive(self.data)
        self.assertEqual(json.loads(json.dumps(fresh)), self.data['geometry'])

    def test_counts(self):
        g = self.data['geometry']
        k_pairs = [p for p in g['pairs'] if p['joint'] != 'EL']
        self.assertEqual(len(k_pairs), 197)
        self.assertEqual(len([p for p in k_pairs if p['joint'] == 'P']), 135)
        self.assertEqual(len(g['fixings']['posts']), 18)
        self.assertEqual(len(g['fixings']['kept_supports']), 12)
        self.assertEqual(len(g['fixings']['provisional']), 5)


class TestSupports(Base):
    def test_all_87_supports_have_one_disposition(self):
        part = json.loads((ROOT / 'design/partition/partition.json').read_text())
        ids = [s['id'] for s in part['supports']]
        self.assertEqual(len(ids), 87)
        claimed = []
        for row in self.data['supports_disposition']:
            if not row['counts_toward_87']:
                continue
            if isinstance(row['ids'], list):
                mine = row['ids']
            else:
                mine = [i for i in ids if i.startswith(row['ids'].rstrip('*'))]
            self.assertEqual(row['count'], len(mine), row['items'])
            claimed += mine
        self.assertEqual(sorted(claimed), sorted(ids))


class TestPhysics(Base):
    def test_strain_formula(self):
        self.assertAlmostEqual(self.c.strain(0.1, 15.0), 3 * 1.6 * 0.1 / 225)
        self.assertAlmostEqual(self.c.delta_allow(self.c.strain(0.1, 15.0), 15.0), 0.1)

    def test_order_statistic_of_one_uniform(self):
        xs = self.c._xs
        cdf = sm.worst_of_n_cdf((sm.np.array([1.0]), 0), sm.convolve([0.2]), 1, xs)
        self.assertTrue(math.isclose(sm.quantile(xs, cdf, 0.5), 0.1, abs_tol=0.002))


class TestAttemptA3(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.a = a3mod.A3(cls.c)

    def test_heights_reproduce_ds33(self):
        a = self.a
        self.assertEqual(a.p['K_face_z_mm'], -30.6)
        self.assertEqual(a.p['gap_mm'], {'O': 13.0, 'P': 17.0, 'JL': 19.0, 'JR': 19.0, 'EL': 7.2})
        for joint, (opn, close) in {'JL': (0.72, 1.47), 'P': (0.74, 1.45), 'O': (1.23, 0.96)}.items():
            h = a.heights(joint, 'a3')
            self.assertAlmostEqual(h['open'], opn, places=2, msg=joint)
            self.assertAlmostEqual(h['close_window'], close, places=2, msg=joint)

    def test_a2_inputs_are_frozen(self):
        self.assertEqual(self.data['parameters']['da01']['gap_mm']['value']['JL'], 18.8)
        self.assertEqual(self.c.v('post_length_tol'), 0.05)

    def test_toggle_chain(self):
        a = self.a
        r = a.toggle_cases()
        self.assertAlmostEqual(r[0]['nominal'], 1.36, places=3)
        self.assertAlmostEqual(r[0]['wc'], 1.10, places=3)
        self.assertAlmostEqual(r[1]['wc'], r[0]['wc'])
        self.assertTrue(math.isclose(r[0]['rss'], 0.42, abs_tol=0.005))
        self.assertAlmostEqual(sum(self.c.p_mismatch_terms()), 0.90, places=3)
        lo, hi = a.p['toggle_window_mm']
        self.assertLess(r[0]['nominal'] - r[0]['wc'], lo)
        self.assertGreater(r[0]['nominal'] + r[0]['wc'], hi)
        self.assertGreater(r[0]['nominal'] - r[0]['rss'], lo)

    def test_adapters(self):
        a = self.a
        self.assertEqual(len(a.g['adapter_pairs']), 6)
        final = a.adapter_xy('final')
        self.assertLess(final['median'], 0.27)
        self.assertGreater(final['median'], self.c.p['misalignment_mm']['final']['along'])
        self.assertGreater(a.adapter_xy('capture')['median'], self.c.p['misalignment_mm']['initial']['along'])
        _, _, rss = a.selector_misfit()
        self.assertTrue(math.isclose(rss, 0.352, abs_tol=0.002))

    def test_k_on_thirty_fixings(self):
        counts = self.a.g['fixing_counts']
        self.assertEqual(sum(v for k, v in counts.items() if k.startswith('post')), 18)
        self.assertEqual(sum(v for k, v in counts.items() if k.startswith('kept support')), 12)

    def test_item1_regions_reach_no_point_outside_k(self):
        outline = geo.load_json(geo.SOURCES['stack_candidate'])['candidate']['planes']['K']['outline']
        for key in ('posts_only', 'posts_and_sleeves'):
            reg = self.a.g['k_regions'][key]
            bay = reg['interior_bay']
            self.assertTrue(geo.inside(bay['centre_xy'], outline))
            self.assertLessEqual(bay['radius_mm'], geo.boundary_dist(bay['centre_xy'], outline) + 1e-6, key)
            self.assertLess(reg['edge_region_low_y']['point_xy'][1], reg['post_rows_y_mm'][0])
            self.assertGreater(reg['edge_region_high_y']['point_xy'][1], reg['post_rows_y_mm'][-1])
        self.assertTrue(math.isclose(self.a.g['k_regions']['posts_only']['interior_bay']['radius_mm'], 79.6, abs_tol=0.1))
        self.assertTrue(math.isclose(self.a.g['k_regions']['posts_only']['edge_region_low_y']['span_mm'], 156.2, abs_tol=0.1))

    def test_item1_push_and_weight(self):
        a, lim = self.a, self.c.dv('strain_design_limit')
        region, _, _, per_n = a.k_governing('posts_only', ('push', 1.0))
        self.assertIn('free-edge', region)
        self.assertTrue(math.isclose(per_n * 1e6, 57.3, abs_tol=0.2))
        self.assertLess(a.k_governing('posts_only', ('push', 5.0))[3], lim)
        self.assertGreater(a.k_governing('posts_only', ('push', 20.0))[3], lim)
        self.assertLess(a.k_governing('posts_only', ('g', a.p['handling_g']))[3], lim)
        self.assertTrue(math.isclose(a.k_governing('posts_only', ('g', 1.0))[3] * 1e6, 81, abs_tol=1))
        self.assertIn('1,146 microstrain', self.readme)

    def test_item2_posts_only_bow_is_larger(self):
        a = self.a
        for p in a.g['adapter_pairs']:
            self.assertGreaterEqual(p['d_post_mm'], p['d_fixing_mm'])
        self.assertGreater(a.adapter_z('posts_only')[0][1], a.adapter_z('posts_and_sleeves')[0][1])
        o1 = [p for p in a.g['adapter_pairs'] if p['id'] == 'K-O1-1'][0]
        self.assertEqual(o1['nearest_fixing'], 'K-SUP-3')
        self.assertTrue(o1['nearest_post'].startswith('POWER-'))

    def test_item3_k_play_is_one_draw(self):
        a = self.a
        cap, fin = a.adapter_xy('capture'), a.adapter_xy('final')
        for r, med, p95 in ((cap, 0.577, 0.886), (fin, 0.176, 0.285)):
            self.assertTrue(math.isclose(r['median'], med, abs_tol=0.003))
            self.assertTrue(math.isclose(r['p95'], p95, abs_tol=0.003))
        limits, _ = a.adapter_board_limits('capture')
        self.assertNotIn('K against the panel on its post screws', [n for n, _ in limits])

    def test_item4_adapter_z_both_sides(self):
        import stack_mechanics_a3 as m
        v = m.adapter_z_verdict(self.a, 'posts_only')
        self.assertTrue(math.isclose(v['wc_miss']['open'], 0.322, abs_tol=0.002))
        self.assertTrue(math.isclose(v['wc_miss']['close'], 0.672, abs_tol=0.002))
        self.assertLess(v['rss_miss']['open'], 0)
        self.assertLess(v['rss_miss']['close'], 0)
        self.assertIn('misses the opening side by 0.322', self.readme)

    def test_item5_inside_is_orientation_free(self):
        square = [[0, 0], [10, 0], [10, 10], [0, 10]]
        for poly in (square, square[::-1]):
            for pt in ([0, 5], [10, 5], [5, 0], [5, 10], [5, 5], [0, 0], [10, 10]):
                self.assertTrue(geo.inside(pt, poly), (pt, poly))
            self.assertFalse(geo.inside([11, 5], poly))

    def test_sleeve_chain_and_rule(self):
        a, lim = self.a, self.c.dv('strain_design_limit')
        lo, hi = a.sleeve_clearance(False)
        self.assertAlmostEqual(lo, -0.15)
        self.assertAlmostEqual(hi, 0.55)
        lo, hi = a.sleeve_clearance(True)
        self.assertAlmostEqual(lo, 0.03)
        self.assertAlmostEqual(hi, 0.32)
        window = a.p['sleeve_sort_window_mm']
        self.assertIn(f'{window[0]:.2f} to {window[1]:.2f} mm shorter than the posts', self.readme)
        shortest = min(s['d_fixing_mm'] for s in a.g['sleeves'])
        self.assertEqual(shortest, 22.0)
        eighth = a.strain_pull(a.turn_travel(1 / 8), shortest)
        self.assertGreater(eighth, lim)
        self.assertTrue(math.isclose(eighth * 1e6, 620, abs_tol=1))
        self.assertTrue(math.isclose(a.strain_pull(0.15, shortest) * 1e6, 1488, abs_tol=1))
        self.assertTrue(math.isclose(a.strain_pull(0.55, shortest) * 1e6, 5455, abs_tol=1))
        self.assertLess(c_allow := self.c.delta_allow(lim, shortest), a.turn_travel(1 / 8))
        self.assertGreater(c_allow, 0)
        for text in ('620 microstrain', '1,488 microstrain', '5,455 microstrain', 'until the washer just touches K, then stop'):
            self.assertIn(text, self.readme)

    def test_pins_are_current(self):
        for sid in ('S-GEOM', 'S-PLAN', 'S-SPACER', 'S-DS', 'S-DA03', 'S-FIX'):
            self.assertTrue(pin_is_current(self.data['sources'][sid]), sid)

    def test_a3_parameters_have_a_basis(self):
        for name, t in self.data['parameters']['a3'].items():
            self.assertIn(t['status'], self.data['status_vocabulary'], name)
            if t['status'] == 'SOURCED':
                self.assertTrue(t.get('source') and t.get('locator'), name)
            elif t['status'] == 'DERIVED':
                self.assertTrue(t.get('formula'), name)
            else:
                self.assertTrue(t.get('reason') and t.get('to_source'), name)



class TestAttemptA5(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import stack_mechanics_a5 as a5mod
        cls.m = a5mod
        cls.a = a5mod.A5(cls.c)

    def test_list_is_the_recorded_a1_list(self):
        fix = json.loads((ROOT / 'design/stack/fixings/fixing-sites.json').read_text())['fixings']
        posts = [f['id'] for f in fix if f['kind'] == 'post']
        a1 = [f['id'] for f in self.data['parameters']['a5']['st08_a1_sleeves']['value']]
        self.assertEqual([f['id'] for f in self.a.g['fixings']], posts + a1)
        kinds = [f['kind'] for f in self.a.g['fixings']]
        self.assertEqual((kinds.count('post'), kinds.count('sleeve kept'), kinds.count('sleeve added')), (18, 2, 3))
        self.assertEqual([f['xy'] for f in self.a.g['fixings'] if f['id'] == 'SLV-U1'], [[159.0, 38.0]])

    def test_farthest_points_match_st08(self):
        reg = self.a.g['regions']
        self.assertAlmostEqual(reg['list']['farthest']['span_mm'], 93.61, places=2)
        self.assertEqual(reg['list']['farthest']['point_xy'], [4.0, 247.0])
        self.assertAlmostEqual(reg['posts_only']['farthest']['span_mm'], 156.2, places=1)
        corner = self.a.p['far_points_xy'][1]
        self.assertAlmostEqual(min(geo.dist(corner, f['xy']) for f in self.a.g['fixings']), 90.4, places=1)

    def test_grillage_reproduces_a_cantilever_strip(self):
        """A rectangle held along one short side by pinned nodes 2 mm apart behaves as the strip of attempt a4."""
        bending = self.a.flex * self.a.p['grillage_stiffness_factor']
        length, width, step, q = 100.0, 40.0, 2.0, 1e-4
        outline = [[0, 0], [width, 0], [width, length], [0, length]]
        held = [(x, 0.0) for x in np.arange(0, width + 0.1, step)] + [(x, step) for x in np.arange(0, width + 0.1, step)]
        gr = self.m.Grillage(outline, step, held, bending)
        u = gr.uniform(q)
        exact = q * (length - step) ** 4 / (8 * bending)
        self.assertTrue(math.isclose(abs(gr.w_at(u, (width / 2, length))), exact, rel_tol=0.08))

    def test_list_figures(self):
        a, hg = self.a, self.a.a3.p['handling_g']
        s = a.uniform_summary('list', hg)
        self.assertTrue(math.isclose(s['max']['w'], 0.641, abs_tol=0.005))
        self.assertLess(s['max']['w'], a.p['rear_clearance_mm'])
        self.assertTrue(math.isclose(s['points'][0], 0.378, abs_tol=0.005))
        self.assertGreater(a.uniform_summary('posts_only', hg)['max']['w'], a.p['rear_clearance_mm'])
        plus = a.uniform_summary('list_plus_one', hg)
        self.assertLess(plus['points'][0], s['points'][0])

    def test_sleeve_strains(self):
        lim = self.c.dv('strain_design_limit')
        worst = self.a.p['sleeve_error_mm']['worst_case']
        spans = [s['span_mm'] for s in self.a.g['sleeves']]
        self.assertAlmostEqual(min(spans), 70.0, places=1)
        self.assertAlmostEqual(max(spans), 141.5, places=1)
        self.assertTrue(math.isclose(self.c.strain(worst, min(spans)) * 1e6, 539, abs_tol=1))
        self.assertTrue(all(self.c.strain(worst, sp) <= lim for sp in spans))
        self.assertAlmostEqual(self.a.p['grillage_stiffness_factor'], 1 - self.c.v('poisson_fr4'))

    def test_push_bounds(self):
        a, lim = self.a, self.c.dv('strain_design_limit')
        lb, d, length, _ = a.cut_lower_bound('list', a.p['far_points_xy'][1])
        self.assertTrue(math.isclose(d / length, 0.5, abs_tol=0.01))
        self.assertTrue(math.isclose(lim / lb, 10.3, abs_tol=0.1))
        comp, _ = a.compliance('list', node_xy=a.p['far_points_xy'][1])
        self.assertTrue(math.isclose(comp, 2.333, abs_tol=0.01))

    def test_corner_sleeves(self):
        for sid in ('JL-SUP-1', 'JR-SUP-1'):
            for board, f in self.a.g['corner_sleeves'][sid].items():
                self.assertAlmostEqual(min(f['edge_distances_mm']), 2.5, places=3, msg=(sid, board))
        refs = [p['ref'] for p in self.a.g['corner_sleeves']['JR-SUP-1']['JR']['footprints_within_8_mm']]
        self.assertIn('R4615', refs)
        area = self.m.annulus_area(3.5, 1.7, (0.0, 0.0), [((-2.5, -10.0), (-2.5, 10.0)), ((-10.0, -2.5), (10.0, -2.5))])
        self.assertTrue(math.isclose(area, 22.7, abs_tol=0.2))



class TestAttemptA6(Base):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import stack_mechanics_a5 as a5mod
        import stack_mechanics_a6 as a6mod
        cls.m5, cls.m6 = a5mod, a6mod
        cls.a = a6mod.A6(cls.c)
        cls.ruled = cls.a.movement('ruled')
        cls.map = a6mod.load_map()

    def test_pins(self):
        fix = json.loads((ROOT / 'design/stack/fixings/fixing-sites.json').read_text())['fixings']
        self.assertEqual(geo.fixings_array_sha256(fix), self.data['sources']['S-FIX']['key_sha256'])
        self.assertEqual(self.a.g['fixings_array_sha256'], self.data['sources']['S-FIX']['key_sha256'])
        for row in ('DS-72', 'DS-73', 'DS-74', 'DS-75', 'DS-76', 'DS-81'):
            self.assertIn(row, self.data['sources']['S-DS']['rows'])
        self.assertTrue(pin_is_current(self.data['sources']['S-DS']))
        self.assertFalse([s['path'] for s in self.data['sources'].values() if 'gate' in s.get('path', '')])  # ST-02's gate file is not pinned

    def test_ruled_list_is_the_active_entries(self):
        fix = json.loads((ROOT / 'design/stack/fixings/fixing-sites.json').read_text())['fixings']
        self.assertEqual(self.a.fixing_ids('ruled'), [f['id'] for f in fix if f['active']])
        sleeves = {f['id']: f['xy'] for f in self.a.g['sets']['ruled']['fixings'] if f['kind'] != 'post'}
        self.assertEqual(sleeves, {'SLV-U1': [74.0, 28.0], 'SLV-U2': [244.0, 24.0], 'SLV-L1': [93.0, 276.0], 'SLV-L2': [244.0, 230.0]})
        self.assertEqual(len(self.a.fixing_ids('ruled')), 22)

    def test_criterion_of_ds72(self):
        m, auth = self.ruled, self.a.p['authority_figures']['movement_mm']
        self.assertLessEqual(m['max']['w'], self.a.p['movement_limit_mm'])
        self.assertEqual(m['max']['at'], [4.0, 292.0])
        self.assertTrue(math.isclose(m['max']['w'], auth['max'], abs_tol=0.01))
        self.assertTrue(math.isclose(m['points']['left_edge'], auth['left_edge'], abs_tol=0.01))
        self.assertTrue(math.isclose(m['above_rows_max']['w'], auth['above_post_rows_max'], abs_tol=0.01))
        self.assertLess(m['strain']['eps'], self.c.dv('strain_design_limit'))
        m4 = self.a.movement('ruled', step=4.0, cover=False)
        self.assertTrue(math.isclose(m4['strain']['eps'] * 1e6, self.a.p['authority_figures']['strain_microstrain_4mm_grid'], abs_tol=1))
        self.assertTrue(math.isclose(m4['points']['above_post_rows'], auth['above_post_rows'], abs_tol=0.01))
        self.assertTrue(math.isclose(m4['points']['upper_edge_middle'], auth['upper_edge_middle'], abs_tol=0.01))
        self.assertTrue(self.a.passes(m))
        self.assertIn('(DONE)', self.readme)

    def test_grid_of_record_covers_k(self):
        self.assertEqual(self.m6.outline_step(self.a.outline), self.a.p['grid_step_mm'])
        self.assertTrue(self.a.grillage('ruled').covers)
        self.assertTrue(self.ruled['covers'])

    def test_no_merged_fixings_and_snaps_reported(self):
        gr = self.a.grillage('ruled')
        self.assertEqual(len(set(gr.fixed_nodes)), 22)
        self.assertEqual(len(gr.snap_mm), 22)
        self.assertLessEqual(max(gr.snap_mm), gr.h / math.sqrt(2) + 1e-9)
        m1 = self.a.movement('ruled', step=self.a.p['snap_check_step_mm'])
        self.assertLessEqual(max(m1['snap_mm']), 0.5 + 1e-9)
        self.assertLess(abs(m1['max']['w'] - self.ruled['max']['w']), 0.05)

    def test_sleeve_strains(self):
        err = self.a.a5.p['sleeve_error_mm']['worst_case']
        auth = self.a.p['authority_figures']['sleeve_strain_microstrain_worst_case']
        for s in self.a.sleeve_rows('ruled'):
            self.assertTrue(math.isclose(self.c.strain(err, s['span_mm']) * 1e6, auth[s['id']], abs_tol=1.5), s['id'])
            self.assertLess(self.c.strain(err, s['span_mm']), self.c.dv('strain_design_limit'))

    def test_comparison_rows(self):
        alt = [s for s in self.a.sleeve_rows('ALT-L2-A') if s['id'] == 'ALT-L2-A'][0]
        self.assertTrue(math.isclose(self.c.strain(0.55, alt['span_mm']) * 1e6, 588, abs_tol=1))
        fx = self.a.g['sets']['ALT-L2-A']['fixings']
        site = [f['xy'] for f in fx if f['id'] == 'ALT-L2-A'][0]
        close = sorted(round(geo.dist(site, f['xy']), 2) for f in fx if f['id'] != 'ALT-L2-A' and geo.dist(site, f['xy']) < 70)
        self.assertEqual(close, [67.0, 69.0, 69.25])
        self.assertTrue(math.isclose(self.a.movement('a1')['max']['w'], 0.641, abs_tol=0.005))
        for key, _, _ in self.a.comparison_sets():
            self.assertTrue(self.a.passes(self.a.movement(key)), key)
        ruled, plus = self.ruled, self.a.movement('ruled_plus_SLV-R1')
        self.assertIn(f"from {ruled['above_rows_max']['w']:.2f} to {plus['above_rows_max']['w']:.2f} mm", self.readme)
        ratio = plus['points']['above_post_rows'] / ruled['points']['above_post_rows']
        self.assertTrue(0.28 < ratio < 0.4)

    def test_map_regenerates(self):
        mp = self.map
        self.assertEqual(mp['inputs'], self.a.map_inputs())
        self.assertLessEqual(mp['inputs']['map_pitch_mm'], 4.0)
        gr = self.a.grillage('ruled')
        sel = self.a.map_nodes(gr)
        self.assertEqual([n[:2] for n in mp['nodes']], [[round(float(v), 3) for v in gr.nodes[k]] for k in sel])
        sample = list(range(0, len(sel), 400))
        comp = gr.point_compliance([sel[i] for i in sample])
        for i, cval in zip(sample, comp):
            self.assertTrue(math.isclose(mp['nodes'][i][2], cval, abs_tol=1e-5), mp['nodes'][i])
        origin = (min(v[0] for v in mp['inputs']['k_outline']), min(v[1] for v in mp['inputs']['k_outline']))
        regions = self.m6.map_regions(mp['nodes'], mp['inputs']['map_pitch_mm'], origin, [(t['mm_per_N'], t['rule']) for t in mp['thresholds']])
        self.assertTrue(self.m6.map_is_current(self.a, mp))
        self.assertEqual([(k['name'], k['xy']) for k in mp['corners']], [(n, xy) for n, xy in self.a.map_corner_names()])
        self.assertEqual(json.loads(json.dumps(regions)), mp['thresholds'])
        names = {k['name']: k['mm_per_N'] for k in mp['corners']}
        self.assertIsNotNone(names['notch corner'])
        self.assertGreater(names['lower left corner'], 1.0)
        self.assertTrue(math.isclose(self.a.push_at('ruled', (15.5, 234)), 0.42, abs_tol=0.02))
        self.assertTrue(math.isclose(self.a.push_at('ruled', (31.5, 283)), 0.76, abs_tol=0.02))

    # review findings of 23:18 UTC, each fails on the a5 code
    def test_finding1_grid_must_cover_the_outline(self):
        with self.assertRaises(ValueError):
            self.m5.Grillage(self.a.g['k_outline'], 4.0, self.a.fixings_xy('ruled'), self.a.bending)

    def test_finding2_merged_fixings_fail(self):
        outline = [[0, 0], [40, 0], [40, 40], [0, 40]]
        with self.assertRaises(self.m5.MergedFixings):
            self.m5.Grillage(outline, 2.0, [(10.0, 10.0), (10.4, 10.3), (30.0, 30.0)], self.a.bending)

    def test_finding3_no_straight_cut_gives_none(self):
        lb, d, length, deg = self.a.a5.cut_lower_bound('list', (150.0, 170.0))
        self.assertIsNone(lb)
        self.assertEqual(self.m5.cut_cells(None, 593e-6)[1], 'n/a')

    def test_finding4_scan_cache_follows_the_model(self):
        data = json.loads(json.dumps(self.data))
        data['parameters']['a5']['grillage_stiffness_factor']['value'] = 0.425
        soft = self.m5.A5(sm.Calc(data)).compliance_scan('list')[0]
        stiff = self.m5.A5(self.c).compliance_scan('list')[0]
        self.assertTrue(math.isclose(soft, 2 * stiff, rel_tol=1e-6))

    def test_finding5_empty_region_is_none(self):
        self.assertIsNone(geo.farthest_in_region(self.a.g['k_outline'], [[100, 100]], 4.0, lambda p: False))

    def test_finding6_edges_at_any_angle(self):
        outer, inner, d = 3.5, 1.7, 2.5
        normals = [0.0, 60.0]
        edges = []
        for deg in normals:
            nx, ny = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            px, py = -d * nx, -d * ny
            edges.append(((px - 10 * ny, py + 10 * nx), (px + 10 * ny, py - 10 * nx)))
        area = self.m5.annulus_area(outer, inner, (0.0, 0.0), edges, n=800)
        rr = np.linspace(inner, outer, 401)
        rm, dr = (rr[1:] + rr[:-1]) / 2, rr[1] - rr[0]
        th = np.linspace(0, 2 * math.pi, 2881)[:-1]
        R, T = np.meshgrid(rm, th)
        keep = np.ones(R.shape, bool)
        for deg in normals:
            nx, ny = math.cos(math.radians(deg)), math.sin(math.radians(deg))
            keep &= R * (np.cos(T) * nx + np.sin(T) * ny) >= -d
        reference = float((R * keep).sum() * dr * (th[1] - th[0]))
        self.assertTrue(math.isclose(area, reference, abs_tol=0.1))
        square = self.m5.annulus_area(outer, inner, (0.0, 0.0), [((-d, -10.0), (-d, 10.0)), ((-10.0, -d), (10.0, -d))])
        self.assertGreater(area - square, 0.3)



class TestAttemptA7(Base):
    """Corrections after the independent code review of the a6 code (DS-89); each test fails on the a6 code."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        import stack_mechanics_a5 as a5mod
        import stack_mechanics_a6 as a6mod
        cls.m5, cls.m6 = a5mod, a6mod
        cls.a = a6mod.A6(cls.c)

    def variant(self, edit):
        data = json.loads(json.dumps(self.data))
        edit(data)
        return sm.Calc(data)

    def test_f1_corners_keyed_by_coordinates(self):
        labels = [n for n, _ in self.a.corners()]
        self.assertEqual(len(set(labels)), len(labels))
        xy = (314.0, 246.0)
        self.assertTrue(math.isclose(self.a.push_at('a1', xy), 1.113, abs_tol=0.001))
        self.assertIn('| notch corner on the right edge | (314, 246) | 1.118 | 1.113 |', self.m6.render_a6_compliance(self.c))

    def test_f2_grid_heading_and_labels_are_computed(self):
        tight = self.variant(lambda d: d['parameters']['a6']['movement_limit_mm'].update(value=0.7))
        self.assertIn('only the 2 mm grid within 0.7 mm', self.m6.render_a6_grids(tight))
        self.assertIn('both within 1.4 mm', self.m6.render_a6_grids(self.c))
        strips = self.m6.dropped_strips(self.a.outline, 4.0)
        self.assertEqual(strips, ['x = 312 to 314 for y = 8 to 246', 'y = 244 to 246 for x = 258 to 314', 'x = 256 to 258 for y = 246 to 292'])
        self.assertEqual(self.m6.dropped_strips(self.a.outline, 2.0), [])

    def test_f3_lattice_area_follows_the_grid_origin(self):
        nodes = [[1.0 + 4 * i, 1.0 + 4 * j, 2.0] for i in range(3) for j in range(3)]
        t = self.m6.map_regions(nodes, 4.0, (1.0, 1.0), [(1.0, 'test')])[0]
        self.assertEqual(t['area_mm2_approx'], 9 * 16.0)
        self.assertEqual(self.m6.map_regions(nodes, 4.0, (0.0, 0.0), [(1.0, 'test')])[0]['area_mm2_approx'], 0.0)

    def test_f4_comparison_sets_come_from_the_fixing_file(self):
        sets = self.a.comparison_sets()
        self.assertEqual([k for k, _, _ in sets], ['ruled'] + ['ruled_plus_' + r['id'] for r in self.a.g['reserve']]
                         + [alt['id'] for alt in self.a.g['alternatives']] + ['a1'])
        for _, label, _ in sets:
            self.assertIn(f'| {label} |', self.readme)

        def move(d):
            alts = d['geometry']['a6']['alternatives']
            alts[0]['xy'] = [99.0, 276.0]
            del alts[1]
            alts.append({'id': 'ALT-NEW', 'xy': [250.0, 230.0], 'replaces': 'SLV-L2', 'findings': [], 'decision': None})
        labels = {k: lab for k, lab, _ in self.m6.A6(self.variant(move)).comparison_sets()}
        self.assertEqual(labels['ALT-L1-A'], 'SLV-L1 at (99, 276) instead of (93, 276)')
        self.assertNotIn('ALT-L1-B', labels)
        self.assertEqual(labels['ALT-NEW'], 'SLV-L2 at (250, 230) instead of (244, 230)')

    def test_f5_stale_map_is_not_published(self):
        mp = self.m6.load_map()
        mp['inputs_sha256'] = '0' * 64
        original = self.m6.load_map
        try:
            self.m6.load_map = lambda: mp
            text = self.m6.render_a6_compliance(self.c)
            self.assertIn('The compliance map is stale', text)
            self.assertNotIn('mm/N', text)
            self.assertIn('stale', self.m6.render_a6_head(self.c))
        finally:
            self.m6.load_map = original
        self.assertTrue(self.m6.map_is_current(self.a, self.m6.load_map()))

    def test_f6_snap_bounded_for_every_set_and_outside_fails(self):
        for key, _, _ in self.a.comparison_sets():
            gr = self.a.grillage(key)
            self.assertLessEqual(max(gr.snap_mm), gr.snap_bound_mm + 1e-9, key)
        with self.assertRaises(ValueError):
            self.m5.Grillage([[0, 0], [40, 0], [40, 40], [0, 40]], 2.0, [(10.0, 10.0), (41.0, 20.0)], self.a.bending)

    def test_f7_push_load_and_reading_share_their_nodes(self):
        with self.assertRaises(ValueError):
            self.a.push_at('ruled', (262.0, 250.0))
        gr = self.a.grillage('ruled')
        xy = (15.0, 292.0)
        load = np.zeros(gr.size)
        for k, wt in gr.bilinear(xy):
            load[3 * k] += wt
        self.assertEqual(len(gr.bilinear(xy)), 2)
        reference = float(load @ gr.solve(load))
        self.assertTrue(math.isclose(self.a.push_at('ruled', xy), reference, rel_tol=1e-9))

    def test_f8_empty_region_and_rows_per_set(self):
        a = self.a
        points = tuple((n, tuple(xy)) for n, xy in a.p['check_points_xy'].items())
        m = self.m6.movement_for(a.outline, 2.0, a.fixings_xy('ruled'), a.bending, True, a.a3.weight_pressure(a.hg), a.a5.t, points, (0.0,))
        self.assertIsNone(m['above_rows_max'])
        self.assertEqual(self.m6.peak_cell(None), 'n/a (no node above the post rows)')
        self.assertEqual(a.post_rows('a1'), tuple(a.a5.g['regions']['list']['post_rows_y_mm']))
        self.assertEqual(a.post_rows('ALT-L2-A'), tuple(a.g['sets']['ALT-L2-A']['regions']['post_rows_y_mm']))

    def test_f9_map_pitch_is_a_whole_multiple_of_the_grid(self):
        gr = self.a.grillage('ruled')
        for pitch in (3.0, 1.0, 0.0, -2.0):
            bad = self.m6.A6(self.variant(lambda d: d['parameters']['a6']['map_pitch_mm'].update(value=pitch)))
            with self.assertRaises(ValueError, msg=pitch):
                bad.map_nodes(gr)

    def test_f10_one_model_per_key_and_a_bounded_cache(self):
        a = self.a
        g1 = self.m5.grillage_for(a.outline, 2.0, a.fixings_xy('ruled'), a.bending, True)
        g2 = self.m5.grillage_for(a.outline, 2.0, a.fixings_xy('ruled'), a.bending, False)
        self.assertIs(g1, g2)
        self.assertEqual(self.m5._grillage.cache_info().maxsize, self.m5.GRILLAGE_CACHE_SIZE)
        self.assertLessEqual(self.m5.GRILLAGE_CACHE_SIZE, 8)
        with self.assertRaises(ValueError):
            self.m5.grillage_for(a.outline, 4.0, a.fixings_xy('ruled'), a.bending, True)


if __name__ == '__main__':
    unittest.main()
