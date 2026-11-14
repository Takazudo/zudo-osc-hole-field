"""Tests for the ST-03 stack-mechanics calculator. No network, no KiCad."""
from pathlib import Path
import hashlib
import json
import math
import re
import unittest

import stack_mechanics as sm
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

    def test_prose_numbers_follow_from_the_json(self):
        c = self.c
        claims = {
            '0.295': c.aperture_stack_first('jack')[2] - c.aperture_clearance(c.d['apertures']['jack'])[0],
            '0.128': c.aperture_stack_first('selector')[2] - c.aperture_clearance(c.d['apertures']['selector'])[0],
            '0.241': c.aperture_stack_first('el_passage_pot')[2] - c.aperture_clearance(c.d['apertures']['el_passage_pot'])[0],
            '593': c.dv('strain_design_limit') * 1e6,
            '1185': c.dv('strain_test_level') * 1e6,
            '0.028': c.delta_allow(c.dv('strain_design_limit'), 15.0),
            '0.045': c.delta_allow(c.dv('strain_design_limit'), 19.0),
            '0.03': c.v('toggle_nut_thickness') - c.toggle_gap(),
            '0.90': c.combine(c.p_mismatch_terms())[0],
            '0.960': c.z_gap('O_from_carrier')['wc'],
            '0.11': c.dv('m25_pitch') / 4,
            '70': 423 * 1.0 / 6,
        }
        for text, value in claims.items():
            decimals = len(text.split('.')[1]) if '.' in text else 0
            self.assertEqual(f'{value:.{decimals}f}', text, text)
            self.assertIn(text, self.readme)

    def test_headline_ranges(self):
        c = self.c
        best = [c.xy(u, c.best_scheme(u))['wc'] for u in sm.FRONT_UNITS]
        self.assertEqual(f'{min(best):.2f}', '0.89')
        self.assertEqual(f'{max(best):.2f}', '1.03')
        d_req = [c.d_required(c.g['units'][u]['longest_side_mm']) for u in ('JL', 'JR', 'P')] + [c.d_required(c.g['K']['longest_side_mm'])]
        self.assertEqual(f'{min(d_req):.1f}', '15.5')
        self.assertEqual(round(max(d_req)), 23)
        rss = c.z_gap('JL')['rss']
        self.assertEqual(f"{2 * (0.1 + rss):.2f}", '0.43')
        self.assertEqual(f"{2 * (0.3 + rss):.2f}", '0.83')


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

    def test_parameters_are_the_brief_sets(self):
        p = self.data['parameters']
        self.assertEqual(p['a_mm'], [0.1, 0.2, 0.3, 0.5])
        self.assertEqual(p['f_N'], [0.3, 0.5, 1.0])
        self.assertEqual(p['t_mm'], [0.1, 0.2, 0.3])

    def test_no_assumed_term_is_labelled_sourced_in_readme(self):
        for name, t in self.data['terms'].items():
            row = [ln for ln in self.readme.splitlines() if ln.startswith(f'| `{name}` |')]
            self.assertEqual(len(row), 1, name)
            self.assertIn(f"| {t['status']} |", row[0])


class TestGeometry(Base):
    def test_geometry_block_is_current(self):
        fresh = geo.derive()
        fresh['el_passage_diameters_mm'] = [list(x) for x in fresh['el_passage_diameters_mm']]
        self.assertEqual(json.loads(json.dumps(fresh)), self.data['geometry'])

    def test_plan_counts_are_reproduced(self):
        g = self.data['geometry']
        self.assertEqual(g['K']['pairs'], 197)
        self.assertEqual(g['K']['positions'], 777)
        self.assertEqual(g['units']['P']['pairs'], 135)
        self.assertEqual(g['units']['P']['positions'], 423)
        self.assertEqual(g['units']['EL']['positions'], 36)
        self.assertEqual(g['j_to_p_post_row_spacing_mm'], [15.0, 19.0])
        hw = sum(sum(v.values()) for k, v in g['hardware_class_counts'].items() if not k.startswith('el_passage'))
        self.assertEqual(hw, 438)


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

    def test_worst_case_not_below_rss(self):
        for u in sm.FRONT_UNITS:
            r = self.c.xy(u, self.c.best_scheme(u))
            self.assertGreaterEqual(r['wc'], r['rss'])

    def test_min_a(self):
        self.assertEqual(self.c.min_a(0.35), 0.5)
        self.assertEqual(self.c.min_a(0.3), 0.3)
        self.assertIsNone(self.c.min_a(0.51))


if __name__ == '__main__':
    unittest.main()
