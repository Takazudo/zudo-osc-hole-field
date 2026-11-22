"""MC04-S7 Revision 9 / Revision 11 addendum: a K service aperture displaces pinned packages on both faces of K."""
import unittest

import scripts.checks.partition35_floorplan as fp


def row(x, y, side, footprint='zudo-osc-hole-field:R0603'):
    return {'courtyard_mm': [x - 1, y - 0.5, x + 1, y + 0.5], 'side': side, 'footprint': footprint}


APERTURE = {'box_mm': [166.6, 120.9, 168.8, 123.1]}  # JL-K-27-K's 2.2 mm NPTH at (167.7, 122)


class Apertures(unittest.TestCase):
    def rows(self):
        return {'K': {'RF': row(167.7, 122.0, 'F.Cu'), 'RB': row(167.7, 122.0, 'B.Cu'),
                      'ROUT': row(175.0, 122.0, 'B.Cu')},
                'JL': {'RJ': row(167.7, 122.0, 'B.Cu')}}

    def test_aperture_displaces_both_faces_of_k(self):
        self.assertEqual(fp.header_conflicts('K', self.rows(), [], apertures=[APERTURE]), {'RF', 'RB'})

    def test_without_the_aperture_nothing_is_displaced(self):
        self.assertEqual(fp.header_conflicts('K', self.rows(), []), set())

    def test_apertures_apply_to_k_only(self):
        self.assertEqual(fp.header_conflicts('JL', self.rows(), [], apertures=[APERTURE]), set())

    def test_a_covered_bypass_capacitor_takes_its_ic(self):
        rows = self.rows()
        rows['K']['U1'] = row(190.0, 122.0, 'B.Cu', 'zudo-osc-hole-field:SOIC-8_3.9x4.9mm_P1.27mm')
        parts = [{'ref': 'RB', 'decouples_ref': 'U1'}]
        self.assertEqual(fp.header_conflicts('K', rows, [], parts=parts, apertures=[APERTURE]), {'RF', 'RB', 'U1'})


if __name__ == '__main__':
    unittest.main()
