"""MC04-S7 Revisions 12 and 13: near-slot eviction treats every active sleeve keep-out as occupied, and the parts a
keep-out displaces are placed after every other evicted part."""
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


class KeepoutLast(unittest.TestCase):
    """Revision 13: a keep-out-displaced part never takes a position another evicted part would have taken."""

    @classmethod
    def setUpClass(cls):
        cls.outline = source()['boards']['JR']['outline']

    def place_all(self, order, slots, keepout=True):
        g = fp.Grid('JR', 'F.Cu', self.outline)
        if keepout:
            fp.occupy_keepout(g, SLV, RADIUS)
        out = {}
        for ref in order:
            envelope, masks = masks_for([R0603], g.scale, 0, fp.oriented_box)
            slot = slots[ref]
            _, x, y = nearest(g, masks, (round((slot[0] + envelope[0]) * g.scale), round((slot[1] + envelope[1]) * g.scale)))
            ox, oy = x / g.scale - envelope[0], y / g.scale - envelope[1]
            b = [R0603[0] + ox, R0603[1] + oy, R0603[2] + ox, R0603[3] + oy]
            g.fill([b[0], b[1], b[2] + .35, b[3] + .35], 0)
            out[ref] = (ox, oy)
        return out

    def test_order_puts_keepout_parts_last(self):
        self.assertEqual(fp.evicted_order({'R9', 'D1', 'C5', 'R2'}, ['D1', 'R2']), ['C5', 'R9', 'D1', 'R2'])
        self.assertEqual(fp.evicted_order({'R9', 'D1'}, []), ['D1', 'R9'])

    def test_a_keepout_part_does_not_take_another_parts_pose(self):
        # D1 sat in the keep-out; R9's slot is D1's next free pose outside it
        d1 = (243.0, 24.0)
        slots = {'D1': d1, 'R9': self.place_all(['D1'], {'D1': d1})['D1']}
        alone = self.place_all(['R9'], slots)
        first = self.place_all(['D1', 'R9'], slots)  # reference order: D1 first takes R9's place
        self.assertNotEqual(first['R9'], alone['R9'])
        last = self.place_all(fp.evicted_order(set(slots), ['D1']), slots)
        self.assertEqual(last['R9'], alone['R9'])
        x, y = last['D1']
        self.assertGreaterEqual(box_dist([R0603[0] + x, R0603[1] + y, R0603[2] + x, R0603[3] + y], SLV), RADIUS - 1e-9)

    def test_committed_floorplan_keeps_evicted_parts_out_of_sleeve_keepouts(self):
        rep = json.loads(fp.OUT.read_text())
        self.assertEqual(rep['adopted_placement_pins']['boards']['JR'].get('placed_after_sleeve_keepouts'),
                         ['D4101', 'D4102', 'R8425', 'R8426'])
        for p in rep['placements']:
            if p.get('evicted_near_slot'):
                for c, r in fp.sleeve_keepouts(p['board']):
                    self.assertFalse(fp.keepout_entered(p['courtyard_mm'], c, r), p['ref'])


class GeneratorOrder(unittest.TestCase):
    """Revision 14 item 3: the order rule at generator level. A fresh floorplan build equals the committed one, and the
    same build in plain reference order (the rule removed) moves parts outside the four keep-out-displaced ones."""

    def test_fresh_build_equals_the_committed_floorplan(self):
        self.assertEqual(fp.dumps(fp.build()) + chr(10), fp.OUT.read_text())

    def test_reference_order_moves_other_evicted_parts(self):
        committed = {p['ref']: p for p in json.loads(fp.OUT.read_text())['placements']}
        saved = fp.evicted_order
        fp.evicted_order = lambda evicted, keepout_last: sorted(evicted)
        try:
            rebuilt = {p['ref']: p for p in fp.build()['placements']}
        finally:
            fp.evicted_order = saved
        moved = sorted(r for r, p in rebuilt.items() if (p['x_mm'], p['y_mm'], p['side']) != (committed[r]['x_mm'], committed[r]['y_mm'], committed[r]['side']))
        self.assertTrue(set(moved) - {'D4101', 'D4102', 'R8425', 'R8426'}, moved)


if __name__ == '__main__':
    unittest.main()
