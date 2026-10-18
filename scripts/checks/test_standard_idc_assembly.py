"""Source-only IDC candidate regressions; not physical qualification."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT/'design/architecture-278/implementation/stage36/standard-idc-assembly'
spec = importlib.util.spec_from_file_location('standard_idc_assembly', HERE/'generate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class StandardIDCAssembly(unittest.TestCase):
    def setUp(self):
        self.p = m.build()
        self.by_ref = {c['ref']: c for c in self.p['connectors']}

    def test_determinism_and_bound_sources(self):
        self.assertEqual(self.p, json.loads((HERE/'candidate.json').read_text()))
        for path, digest in self.p['source_sha256'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), digest)

    def test_numbered_nets_and_face_reflection(self):
        old = json.loads(m.PRIOR.read_text())
        for link, mapping in self.p['pin_maps'].items():
            self.assertEqual(mapping['pins'], old['pin_maps'][link]['pins'])
            for ref in mapping['refs']:
                c = self.by_ref[ref]
                self.assertEqual(c['coordinates'], next(x for x in old['connector_coordinates'] if x['ref'] == ref))
                for pin in c['coordinates']['pins']:
                    self.assertEqual(mapping['pins'][str(pin['pin'])], pin['net'])
                    self.assertEqual(pin['socket_face_xy'], [pin['header_face_xy'][0], -pin['header_face_xy'][1]])
        self.assertEqual(self.p['pin_maps']['J-PWR']['pins']['3'], '+5V')
        self.assertIsNone(self.p['pin_maps']['J-PWR']['pins']['5'])

    def test_drawing_constraints_not_metric_rounding(self):
        d = self.p['maker_constraints']
        self.assertEqual(d['socket_closed_height_inch_conversion_mm'], 10.414)
        self.assertEqual(d['socket_closed_height_metric_annotation_mm'], 10.5)
        self.assertEqual(d['minimum_exposure_surplus_mm'], .2032)
        self.assertEqual(d['header_floor_above_seated_pcb_interval_mm'], [3.2258, 3.7338])
        self.assertEqual(d['header_tail_from_standoff_seat_interval_mm'], [2.5654, 3.1242])
        self.assertEqual(d['minimum_body_cavity_total_width_gap_mm'], .0508)
        self.assertIsNone(d['socket_closed_height_max_mm'])
        self.assertIsNone(d['socket_maximum_pin_insertion_mm'])

    def test_service_failures_retained(self):
        c = self.by_ref['J17902']['screens']
        self.assertEqual(c['installed']['necessary_max_height_above_board_mm'], 23)
        self.assertEqual(c['withdrawal15']['necessary_max_height_above_board_mm'], 8)
        self.assertEqual(c['withdrawal15']['limiting_obstacles'], ['A01-core'])
        self.assertLess(self.by_ref['J17901']['screens']['grip_withdrawal15']['necessary_max_height_above_board_mm'], 0)

    def test_unknowns_do_not_become_clearance_passes(self):
        self.assertFalse(self.p['adopted'])
        for c in self.p['connectors']:
            for key in ['mated_max_height_mm', 'cable_exit_z_mm', 'cable_cut_length_mm', 'minimum_bend_radius_mm']:
                self.assertIsNone(c[key])
            self.assertTrue(all(s['status'].startswith('UNKNOWN') for s in c['screens'].values()))
        self.assertIn('RV1408', self.by_ref['J17901']['unknown_neighbor_projection_refs'])
        self.assertIn('RV1608', self.by_ref['J17902']['unknown_neighbor_projection_refs'])

    def test_obstacle_and_boundary_sensitivity(self):
        xy = [0, 0, 10, 10]
        obstacle = {'id': 'injected', 'xy': [10, 0, 20, 10], 'z': [20, 30]}
        self.assertEqual(m.height_limit(xy, 5, [obstacle], 15, 1)[0]['height_mm'], -1)
        obstacle['xy'][0] = 10.001
        self.assertEqual(m.height_limit(xy, 5, [obstacle], 15, 1)[0]['id'], 'existing_cover_inner_z105')

    def test_rotated_four_corner_bounds(self):
        self.assertEqual(m.footprint([208,108], 20, 10, 90), [203,98,213,118])
        for c in self.p['connectors']:
            self.assertEqual(c['known_tail_hits'], [])
            self.assertAlmostEqual(c['tail_below_nominal_pcb_mm'][1], 1.5242)


if __name__ == '__main__':
    unittest.main()
