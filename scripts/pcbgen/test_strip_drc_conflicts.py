"""Pure tests of the DRC conflict selection (no KiCad)."""
import unittest

from scripts.pcbgen.strip_drc_conflicts import conflicts


def v(kind, *descs, uuids=None):
    uuids = uuids or [f'u{i}' for i in range(len(descs))]
    return {'type': kind, 'items': [{'description': d, 'uuid': u} for d, u in zip(descs, uuids)]}


class ConflictSelection(unittest.TestCase):
    def test_track_against_a_moved_pad_is_selected(self):
        got = conflicts([v('shorting_items', 'Track [N1] on B.Cu, length 0.15 mm', 'Pad 1 [N2] of RB1504 on B.Cu')], ['RB1504'])
        self.assertEqual([(u, k, r, t) for u, k, r, t, _ in got], [('u0', 'Track', 'RB1504', 'shorting_items')])

    def test_via_against_a_moved_pad_is_selected(self):
        got = conflicts([v('hole_clearance', 'Via [N1] on F.Cu - B.Cu', 'Pad 3 [N2] of U8417 on B.Cu')], ['U8417'])
        self.assertEqual([(u, k) for u, k, *_ in got], [('u0', 'Via')])

    def test_conflicts_without_a_moved_part_are_ignored(self):
        got = conflicts([v('clearance', 'Track [N1] on B.Cu, length 1 mm', 'Pad 1 [N2] of R9999 on B.Cu')], ['RB1504'])
        self.assertEqual(got, [])

    def test_other_violation_types_and_non_copper_items_are_ignored(self):
        got = conflicts([v('courtyards_overlap', 'Footprint RB1504', 'Footprint R1'),
                         v('silk_overlap', 'Track [N] on F.Cu, length 1 mm', 'Pad 1 [N] of RB1504 on F.Cu'),
                         v('clearance', 'Zone [AGND] on B.Cu', 'Pad 1 [N] of RB1504 on B.Cu')], ['RB1504'])
        self.assertEqual(got, [])


if __name__ == '__main__':
    unittest.main()
