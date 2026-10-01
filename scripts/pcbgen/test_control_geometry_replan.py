import copy
import json
import unittest
from pathlib import Path
from shapely.geometry import Point, Polygon
from scripts.pcbgen.control_geometry_replan import revise, neighbor_envelopes


class ControlGeometryRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(path):
            return json.loads(Path(path).read_text())
        cls.original = read('design/boards/osc-control.json')
        cls.proposal = read('design/partition/control-ground-feasibility/proposal.json')
        cls.partition = read('design/partition/partition.json')
        cls.input = read('design/partition/partition-input.json')
        cls.selector = read('design/mechanical/selector-assembly.json')
        cls.lock = read('design/grid/placements.lock.json')
        cls.lands = [row for row in cls.partition['load_side_terminals'] if row['board'] == 'P']

    def test_actual_mount_conflict_repaired_without_pad_or_unrelated_geometry_change(self):
        revised, receipt = revise(self.original, self.proposal, self.lands)
        # The actual 2.4 mm mounting annulus crosses the old notch. The new
        # polygon contains even its radius enlarged by the full 0.5 mm rule.
        copper = Point(94.2, 185).buffer(1.2, quad_segs=128)
        required = Point(94.2, 185).buffer(1.7, quad_segs=128)
        self.assertFalse(Polygon(self.original['outline']).covers(copper))
        self.assertTrue(Polygon(revised['outline']).covers(required))
        self.assertAlmostEqual(receipt['RV601_nominal_copper_edge_clearance_mm'], .65)
        self.assertEqual(revised['mounting_holes'], self.original['mounting_holes'])
        self.assertEqual(revised['placement_uids'], self.original['placement_uids'])
        original_reserves = {row['id']: row for row in self.original['keepouts'] if row['id'] != 'load-power'}
        new_reserves = {row['id']: row for row in revised['keepouts']}
        self.assertTrue(all(new_reserves[key] == value for key, value in original_reserves.items()))
        self.assertEqual(len(new_reserves)-len(original_reserves), 4)
        self.assertTrue(all(row['layers'] == ['B.Cu'] for row in receipt['added_keepouts']))

    def test_tab_must_satisfy_both_retained_edge_and_neighbor_allocations(self):
        narrow = copy.deepcopy(self.proposal)
        narrow['geometry_replan']['RV601_tab']['left_x_mm'] = 92.6
        with self.assertRaisesRegex(ValueError, 'copper-edge'):
            revise(self.original, narrow, self.lands)
        with self.assertRaisesRegex(ValueError, 'body/support'):
            neighbor_envelopes(self.selector, self.input, self.lock, 92.0)
        good = neighbor_envelopes(self.selector, self.input, self.lock, 92.35)
        self.assertAlmostEqual(good['allocated_body_support_XY_gap_mm'], .55)
        self.assertAlmostEqual(good['remaining_board_copper_solder_z_gap_mm'], 1.85)

    def test_wrong_owner_land_or_changed_original_reserve_rejected(self):
        changed = copy.deepcopy(self.lands)
        changed[0]['side'] = 'F.Cu'
        with self.assertRaisesRegex(ValueError, 'source land'):
            revise(self.original, self.proposal, changed)
        original = copy.deepcopy(self.original)
        original['keepouts'][0]['polygon'][0][0] += .1
        with self.assertRaisesRegex(ValueError, 'broad terminal reservation'):
            revise(original, self.proposal, self.lands)


if __name__ == '__main__':
    unittest.main()
