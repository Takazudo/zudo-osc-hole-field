"""MC04-S7 Revision 12: near-slot eviction treats every active sleeve keep-out as occupied."""
import json
import math
import tempfile
import unittest
from pathlib import Path

import scripts.checks.partition35_floorplan as fp
from scripts.checks.connector_packing35 import source
from scripts.checks.jack_locality import masks_for, nearest

R0603 = [-1.48, -0.73, 1.48, 0.73]  # an 0603 courtyard about its origin
SLV = (244.0, 24.0)
RADIUS = 3.75


def box_dist(b, c):
    return math.hypot(max(b[0] - c[0], 0, c[0] - b[2]), max(b[1] - c[1], 0, c[1] - b[3]))


class SleeveEviction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outline = source()['boards']['JR']['outline']

    def grid(self):
        return fp.Grid('JR', 'F.Cu', self.outline)

    def place_nearest(self, grid, slot):
        envelope, masks = masks_for([R0603], grid.scale, 0, fp.oriented_box)
        d, x, y = nearest(grid, masks, (round((slot[0] + envelope[0]) * grid.scale), round((slot[1] + envelope[1]) * grid.scale)))
        ox, oy = x / grid.scale - envelope[0], y / grid.scale - envelope[1]
        return ox, oy, [R0603[0] + ox, R0603[1] + oy, R0603[2] + ox, R0603[3] + oy]

    def test_nearest_free_pose_inside_a_keepout_is_skipped(self):
        slot = (243.0, 25.0)  # an evicted 0603 whose nearest free pose is its own slot, inside SLV-U2's keep-out
        free = self.grid()
        _, _, b = self.place_nearest(free, slot)
        self.assertLess(box_dist(b, SLV), RADIUS)  # without the rule it lands in the keep-out
        g = self.grid()
        fp.occupy_keepout(g, SLV, RADIUS)
        ox, oy, b = self.place_nearest(g, slot)
        self.assertGreaterEqual(box_dist(b, SLV), RADIUS - 1e-9)  # the next free pose, clear of the keep-out
        self.assertLess(math.hypot(ox - slot[0], oy - slot[1]), RADIUS + 3.0)  # and still near its slot

    def test_every_cell_a_box_needs_inside_the_disk_is_occupied(self):
        g = self.grid()
        fp.occupy_keepout(g, SLV, RADIUS)
        for k in range(36):
            a = math.radians(10 * k)
            for d in (0.0, 1.0, 2.0, RADIUS - 0.05):
                x, y = SLV[0] + d * math.cos(a), SLV[1] + d * math.sin(a)
                self.assertFalse(fp.grid_free(g, [x - 0.05, y - 0.05, x + 0.05, y + 0.05], 0), (x, y))
        self.assertTrue(fp.grid_free(g, [SLV[0] + RADIUS + 0.3, 23.0, SLV[0] + RADIUS + 1.0, 25.0], 0))

    def test_keepouts_come_from_active_sleeves_on_their_boards(self):
        doc = {'fixings': [
            {'id': 'SLV-U2', 'kind': 'sleeve added', 'active': True, 'xy': [244.0, 24.0], 'keepout_radius_mm': {'K': 4.05, 'JR': 3.75}},
            {'id': 'SLV-X', 'kind': 'sleeve added', 'active': False, 'xy': [10.0, 10.0], 'keepout_radius_mm': {'JR': 3.75}},
            {'id': 'POWER-JR-AGND1', 'kind': 'post', 'active': True, 'xy': [50.0, 50.0], 'keepout_radius_mm': {'JR': 3.75}}]}
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'f.json'
            path.write_text(json.dumps(doc))
            self.assertEqual(fp.sleeve_keepouts('JR', path), [((244.0, 24.0), 3.75)])
            self.assertEqual(fp.sleeve_keepouts('K', path), [((244.0, 24.0), 4.05)])
            self.assertEqual(fp.sleeve_keepouts('JL', path), [])

    def test_committed_list_has_the_ruled_sleeves(self):
        self.assertIn(((244.0, 24.0), 3.75), [(tuple(map(float, c)), r) for c, r in fp.sleeve_keepouts('JR')])


if __name__ == '__main__':
    unittest.main()
