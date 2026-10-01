import json
from fractions import Fraction as F
from pathlib import Path
import unittest

from scripts.pcbgen.drilled_face_lift_trial import (
    conditional_energy_upper, face_field_coefficients,
    finite_cover_coefficient, sqrt_upper,
)
from scripts.pcbgen.multi_drill_cover import square_inside
from scripts.pcbgen.finite_cover_flux import annulus_poincare_upper


class DrilledFaceLiftTrialTest(unittest.TestCase):
    def test_two_drill_historical_overlap_fixture_is_exact(self):
        path = Path('.circuit-cache/issue38-recovery/multi-drill-cover-certificate-v2.json')
        cert = next(c for c in json.loads(path.read_text())['certificates']
                    if c['board_id'] == 'osc-jack-right' and c['ref'] == 'U8304')
        self.assertEqual(sum(d['kind'] == 'annulus' for d in cert['domains']), 2)
        self.assertGreater(sum(d['kind'] == 'convex_piece' for d in cert['domains']), 0)
        self.assertEqual(len(cert['overlap_tree']), len(cert['domains']) - 1)
        for edge in cert['overlap_tree']:
            square = edge['square_nm']
            self.assertEqual((square[2]-square[0])*(square[3]-square[1]), edge['area_nm2'])
            for index in (edge['parent'], edge['child']):
                self.assertTrue(square_inside(square, cert['domains'][index], cert['source_primitive']))
        edge = cert['overlap_tree'][0]
        bad = list(edge['square_nm']); bad[2] = bad[0]
        self.assertFalse(square_inside(bad, cert['domains'][edge['parent']], cert['source_primitive']))
        bad_annulus = dict(cert['domains'][0]); bad_annulus['inner_radius_nm'] = bad_annulus['outer_radius_nm']
        self.assertFalse(square_inside(edge['square_nm'], bad_annulus, cert['source_primitive']))
        # Historical fixture only: a convex subset of the pad box has
        # Poincare constant < box diameter squared / 9. Annuli use the
        # existing complete-annulus theorem. Both radii are exact native nm.
        half_x, half_y = cert['source_primitive']['half_size_nm']
        local = []
        for domain_id in cert['ordered_domain_ids']:
            domain = cert['domains'][domain_id]
            if domain['kind'] == 'annulus':
                local.append(annulus_poincare_upper(
                    F(domain['inner_radius_nm'], 10**6),
                    F(domain['outer_radius_nm'], 10**6)))
            else:
                local.append(F((2*half_x)**2+(2*half_y)**2, 9*10**12))
        parents = cert['ordered_parents']
        overlap = [None]+[F(e['area_nm2'], 10**12) for e in cert['overlap_tree']]
        # π < 22/7 and a union's area is no larger than the sum of boxes.
        area_upper = F(4*half_x*half_y, 10**12) + sum(
            F(22*d['outer_radius_nm']**2, 7*10**12)
            for d in cert['domains'] if d['kind'] == 'annulus')
        c = finite_cover_coefficient(local_poincare_mm2=local,
            full_f_support_area_upper_mm2=area_upper, parents=parents,
            overlap_area_lower_mm2=overlap,
            exact_partition_masses=[F(0)]*len(parents))
        self.assertGreater(c, 0)


if __name__ == '__main__':
    unittest.main()
