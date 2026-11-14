"""Tests for the ST-03 stack-mechanics calculator (attempt a2). No network, no KiCad."""
from pathlib import Path
import hashlib
import json
import math
import unittest

import stack_mechanics as sm
import stack_mechanics_a3 as a3mod
import stack_mechanics_geometry as geo

ROOT = Path(__file__).resolve().parents[3]


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


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
                self.assertEqual(sha(s['path']), s['sha256'], sid)
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
        a = self.a
        counts = a.g['fixing_counts']
        self.assertEqual(sum(v for k, v in counts.items() if k.startswith('post')), 18)
        self.assertEqual(sum(v for k, v in counts.items() if k.startswith('kept support')), 12)
        _, _, per_n_fix, per_n_load = a.point_case(1.0)
        self.assertTrue(math.isclose(per_n_fix * 1e6, 9.1, abs_tol=0.1))
        self.assertTrue(math.isclose(per_n_load * 1e6, 36, abs_tol=1))
        self.assertGreater(a.point_case(20.0)[3], self.c.dv('strain_design_limit'))
        self.assertLess(a.point_case(5.0)[3], self.c.dv('strain_design_limit'))

    def test_sleeve_chain_and_rule(self):
        a = self.a
        lo, hi = a.sleeve_clearance(False)
        self.assertAlmostEqual(lo, -0.15)
        self.assertAlmostEqual(hi, 0.55)
        lo, hi = a.sleeve_clearance(True)
        self.assertAlmostEqual(lo, 0.03)
        self.assertAlmostEqual(hi, 0.32)
        shortest = min(s['d_fixing_mm'] for s in a.g['sleeves'])
        self.assertEqual(shortest, 22.0)
        self.assertGreater(a.strain_pull(a.turn_travel(1 / 8), shortest), self.c.dv('strain_design_limit'))
        self.assertIn('stop', self.readme)

    def test_pins_are_current(self):
        for sid in ('S-GEOM', 'S-PLAN', 'S-SPACER', 'S-DS', 'S-DA03'):
            s = self.data['sources'][sid]
            self.assertEqual(sha(s['path']), s['sha256'], sid)

    def test_a3_parameters_have_a_basis(self):
        for name, t in self.data['parameters']['a3'].items():
            self.assertIn(t['status'], self.data['status_vocabulary'], name)
            if t['status'] == 'SOURCED':
                self.assertTrue(t.get('source') and t.get('locator'), name)
            elif t['status'] == 'DERIVED':
                self.assertTrue(t.get('formula'), name)
            else:
                self.assertTrue(t.get('reason') and t.get('to_source'), name)


if __name__ == '__main__':
    unittest.main()
