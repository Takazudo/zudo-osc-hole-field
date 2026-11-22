"""MC04-S7 Revision 5: minimal-reflow pins and the displaced-pin rule of the floorplan."""
import json
import unittest

from scripts.partition import reflow_pins as rp
from scripts.checks import partition35_floorplan as fp


class ReflowPins(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(rp.OUT.read_text())
        cls.floor = json.loads(fp.OUT.read_text())

    def test_committed_pins_are_fresh(self):
        self.assertEqual(rp.build(), self.doc)

    def test_undisturbed_reflow_pins_keep_their_pre_move_pose(self):
        placed = {p['ref']: p for p in self.floor['placements']}
        boards = self.floor['adopted_placement_pins']['boards']
        moved = {r for b in boards.values() for k in ('evicted', 'displaced_by_gh_headers', 'displaced_by_k_block_pins')
                 for r in b.get(k, [])}
        kept = [r for r in self.doc['pins'] if r.get('reflow_pin') and r['ref'] not in moved]
        self.assertTrue(kept)
        for r in kept:
            p = placed[r['ref']]
            self.assertEqual((p['board'], p['x_mm'], p['y_mm'], p['side']), (r['board'], r['x_mm'], r['y_mm'], r['side']), r['ref'])


class BeyondLocality(unittest.TestCase):
    """Revision 6 item 4: every same-board move beyond 24 mm since 6093081c is a recorded exception or a decoupler
    within the 3 mm bypass limit of its IC supply pin."""

    def test_far_moves_are_recorded(self):
        import math
        import subprocess
        base = json.loads(subprocess.run(['git', '-C', str(rp.ROOT), 'show', '6093081c:design/partition/floorplan-candidate.json'],
                                         capture_output=True, text=True, check=True).stdout)
        old = {p['ref']: p for p in base['placements']}
        floor = json.loads(fp.OUT.read_text())
        acc = json.loads(fp.ACCEPTANCES.read_text())['acceptances']
        listed = {a['ref'] for a in acc} | {c for a in acc for c in a.get('moves_with', [])}
        far = [p['ref'] for p in floor['placements'] if p['ref'] in old and old[p['ref']]['board'] == p['board']
               and math.hypot(p['x_mm'] - old[p['ref']]['x_mm'], p['y_mm'] - old[p['ref']]['y_mm']) > 24.0]
        self.assertTrue(far)
        bypass = {x['capacitor']: x['supply_pad_centre_distance_mm'] for x in floor['bypass_proximity']['pairs']}
        for ref in far:
            if ref.startswith('C') and ref in bypass:
                # a decoupler is judged by its supply pin, not its slot (Revision 6 item 4)
                self.assertLessEqual(bypass[ref], 3.0, ref)
            else:
                self.assertIn(ref, listed, ref)


class Displaced(unittest.TestCase):
    ROWS = {'K': {
        'U1': {'footprint': 'zudo-osc-hole-field:C0603', 'side': 'F.Cu', 'courtyard_mm': [0, 0, 4, 4]},
        'C1': {'footprint': 'zudo-osc-hole-field:C0603', 'side': 'F.Cu', 'courtyard_mm': [20, 20, 22, 21]},
        'R1': {'footprint': 'zudo-osc-hole-field:C0603', 'side': 'B.Cu', 'courtyard_mm': [0, 0, 2, 1]},
        'R2': {'footprint': 'zudo-osc-hole-field:C0603', 'side': 'F.Cu', 'courtyard_mm': [50, 50, 52, 51]},
        'B1': {'footprint': 'zudo-osc-hole-field:C0603', 'side': 'F.Cu', 'courtyard_mm': [49, 49, 53, 53], 'k_block_move': True}}}
    HEADERS = [{'board': 'K', 'side': 'F.Cu', 'land_courtyard_mm': [1, 1, 3, 3]}]
    PARTS = [{'ref': 'C1', 'decouples_ref': 'U1'}]

    def test_overlap_same_face_and_bypass_closure(self):
        out = fp.header_conflicts('K', self.ROWS, self.HEADERS, self.PARTS)
        self.assertIn('U1', out)       # under the header land, same face
        self.assertIn('C1', out)       # its bypass capacitor follows
        self.assertNotIn('R1', out)    # other face
        self.assertIn('R2', out)       # under a K block pin
        self.assertNotIn('B1', out)    # a block pin itself is never displaced

    def test_header_only_view(self):
        out = fp.header_conflicts('K', self.ROWS, self.HEADERS, self.PARTS, blocks=False)
        self.assertEqual(out, {'U1', 'C1'})


if __name__ == '__main__':
    unittest.main()
