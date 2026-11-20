import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit.py'))
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
EV = a.load_evidence()
INP = json.loads((a.ROOT / EV['model_bindings']['inputs']).read_text())


class Tests(unittest.TestCase):
    def test_full_contract_with_ratio_sweep(self):
        r = a.contract(EV, INP, store=None)
        self.assertTrue(all(v.startswith('NOT_RUN') for v in r['sources'].values()))
        self.assertFalse(r['ground_share']['legacy_applicable_to_150200075'])
        self.assertIsNone(r['ground_share']['source_min'])
        self.assertEqual(r['ground_share']['status'], 'OPEN')
        th = r['ground_share']['required_min_mohm_per_50mm']
        self.assertTrue(8.6 < th['0.35'] < 8.8 and 5.7 < th['0.5'] < 6.0)
        self.assertEqual(r['ground_share']['evaluated_at_length_mm'], 49.0)
        self.assertLess(th['0.35'], r['ground_share']['source_max_mohm_per_50mm'])
        sweep = r['capacitance']['pair_floating_calibration']['by_length_mm']
        self.assertEqual({k: v['links_above_1'] for k, v in sweep.items()}, {'49.0': 17, '51.0': 17, '53.0': 17})
        self.assertGreater(sweep['53.0']['max_ratio'], sweep['49.0']['max_ratio'])
        self.assertFalse(r['capacitance']['reading_contradicts_model_upper_bound']['one_interior_conductor_vs_all_others'])
        self.assertTrue(r['capacitance']['reading_contradicts_model_upper_bound']['adjacent_pair_others_floating'])
        self.assertEqual(r['capacitance']['status'], 'OPEN')
        fs = r['capacitance']['finite_thickness_summary']
        self.assertEqual(fs['equal_eps_all_pass_to_eps'], 4.7)
        self.assertTrue(fs['retained_harness_failing_cases'])
        self.assertTrue(all(c.startswith(('4.0:', '4.7:')) and 'retained' in c for c in fs['retained_harness_failing_cases']))
        self.assertNotIn('reinforcement_thickness_nominal_mm', EV['conflicts'])
        self.assertIn('odd', EV['facts']['conductor_width_mm'][2])
        self.assertFalse(r['product_qualified'])
        self.assertEqual(r['dimensional']['reinforcement_length_mm']['governing_envelope'], ['4.00', '8.00'])
        self.assertEqual(r['current']['binding_A'], 0.35)

    def test_invented_minimum_rejected(self):
        ev = copy.deepcopy(EV); ev['facts']['conductor_resistance_min'] = '500'
        with self.assertRaises(ValueError):
            a.contract(ev, INP, run_ratios=False)

    def test_revision_or_part_change_rejected(self):
        for path, value in [(('candidate', 'mpn'), '150200076'), (('sources', 'PS', 'revision'), 'E')]:
            ev = copy.deepcopy(EV); node = ev
            for k in path[:-1]:
                node = node[k]
            node[path[-1]] = value
            with self.assertRaises(ValueError):
                a.contract(ev, INP, run_ratios=False)

    def test_finite_thickness_drift_fails(self):
        for key in ('sha256',):
            ev = copy.deepcopy(EV); ev['finite_thickness_study'][key] = '0' * 64
            with self.assertRaises(ValueError):
                a.finite_thickness(ev)
        ev = copy.deepcopy(EV); k = next(iter(ev['finite_thickness_study']['inputs_sha256']))
        ev['finite_thickness_study']['inputs_sha256'][k] = '0' * 64
        with self.assertRaises(ValueError):
            a.finite_thickness(ev)

    def test_conflict_shape_guard(self):
        ev = copy.deepcopy(EV); ev['conflicts']['reinforcement_length_mm']['PS'] = ['6.00', '3.00']
        with self.assertRaises(ValueError):
            a.dimensional(ev)

    def test_missing_or_drifted_store_fails(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                a.check_sources(EV, d)
            for key in ('PS', 'SD'):
                p = Path(d) / EV['sources'][key]['store_path']; p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b'x' * EV['sources'][key]['bytes'])
            with self.assertRaises(ValueError):
                a.check_sources(EV, d)


if __name__ == '__main__':
    unittest.main()
