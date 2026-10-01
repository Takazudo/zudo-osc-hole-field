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

    def test_formal_signed_trace_divergence_and_face_reversal(self):
        for face, sign in (('F.Cu', 1), ('B.Cu', -1)):
            for current, q, b in ((F(2), F(-3), F(1, 4)), (F(0), F(5), F(1, 4))):
                cut = face_field_coefficients(current=current, source_value=q,
                    return_value=b, depth=0, height=F(1, 10), face=face,
                    global_outward_sign=sign)
                top = face_field_coefficients(current=current, source_value=q,
                    return_value=b, depth=F(1, 10), height=F(1, 10),
                    face=face, global_outward_sign=sign)
                self.assertEqual(cut['cut_outward'], current*b)
                self.assertEqual(top['exterior_outward'], -q)
                self.assertEqual(top['divergence_jxy']+top['divergence_jz'], 0)
                self.assertEqual(top['drill_wall_outward'], 0)
                self.assertEqual(top['lateral_outward'], 0)
                self.assertEqual(top['jz_global'], sign*top['jz_local'])
        with self.assertRaisesRegex(ValueError, 'orientation'):
            face_field_coefficients(current=1, source_value=1, return_value=1,
                depth=0, height=1, face='B.Cu', global_outward_sign=1)

    def test_exact_tree_and_cross_term_energy(self):
        c = finite_cover_coefficient(local_poincare_mm2=[1, 2, 3],
            full_f_support_area_upper_mm2=4, parents=[-1, 0, 1],
            overlap_area_lower_mm2=[None, F(1, 100), F(1, 50)],
            exact_partition_masses=[F(2), F(-3), F(1)])
        self.assertGreater(c, 0)
        with self.assertRaises(ValueError):
            finite_cover_coefficient(local_poincare_mm2=[1, 2, 3],
                full_f_support_area_upper_mm2=4, parents=[-1, 0, 1],
                overlap_area_lower_mm2=[None, 0, F(1, 50)],
                exact_partition_masses=[F(2), F(-3), F(1)])
        for current, norm in ((F(1), F(3)), (F(0), F(3))):
            result = conditional_energy_upper(current_a=current,
                source_l2_a_per_mm=norm, return_patch_area_mm2=F(1, 4),
                source_slab_mm=F(1, 10), rho_max_ohm_mm=F(1, 100),
                cover_poincare_mm2=F.from_float(c))
            self.assertGreater(result['energy_w_upper'], 0)
            self.assertIn('CONDITIONAL SYMBOLIC', result['status'])
        self.assertGreaterEqual(sqrt_upper(F(2))**2, 2)


if __name__ == '__main__':
    unittest.main()
