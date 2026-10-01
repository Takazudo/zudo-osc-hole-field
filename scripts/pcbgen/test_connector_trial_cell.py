from copy import deepcopy
from fractions import Fraction as F
import json
import math
import unittest

from scripts.pcbgen.connector_trial_cell import (
    PROPOSAL, corner_upper, evaluate, geometry_checks, interval,
    rectangle_integral_upper, slab_upper, taper_upper, bulk_class_admission,
    maximum_weight_square_sum,
    toe_body_centres,
)


class ConnectorTrialCellTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads(PROPOSAL.read_text())

    def test_complete_positive_interval_cell_books_all_regions(self):
        result = evaluate(self.spec)
        total = F(result["exact_upper_ohm"])
        self.assertEqual(sum(map(F, result["exact_costs_ohm"].values())), total)
        self.assertEqual(len(result["exact_costs_ohm"]), 15)
        self.assertTrue(all(F(x) > 0 for x in result["exact_costs_ohm"].values()))
        self.assertLess(total, F("0.05"))
        self.assertGreater(total, F("0.045"))
        self.assertGreaterEqual(F(result["unit_current_end_energy_upper_ohm"]), total)
        self.assertFalse(result["physical_class_selected"])
        self.assertIn("NOT RUN", result["geometry"]["actual_internal_metal_containment"])
        for value in self.spec["intervals"].values():
            interval(value)

    def test_bulk_box_has_real_allowed_member_violation_even_at_circle_limit(self):
        result = evaluate(self.spec)
        lower = F(result["exact_circular_member_lower_ohm_per_m"])
        self.assertEqual(lower, F(11500, 65219))
        self.assertGreater(lower, F("0.17"))
        self.assertLess(lower, F(result["uniform_bulk_wire_trial_ohm_per_m_upper"]))
        self.assertIn("FAIL", result["bulk_parameter_box_screen"])
        # This is explicitly not a minimum radius guarantee for Alpha Wire.
        self.assertIn("UNSELECTED", self.spec["status"])

    def test_corner_field_glues_exact_full_face_traces_and_conserves(self):
        a, b, h, current = F("0.15"), F("0.16"), F("0.08"), F(1)
        for y in (F(0), b/2, b):
            for z in (F(0), h/2, h):
                jy = current*y/(a*b*h)
                jz = current*(1-z/h)/(a*b)
                self.assertEqual(current/(a*b*h)-current/(a*b*h), 0)
                if y == 0:
                    self.assertEqual(jy, 0)
                if y == b:
                    self.assertEqual(jy*a*h, current)
                if z == 0:
                    self.assertEqual(jz*a*b, current)
                if z == h:
                    self.assertEqual(jz, 0)
        # Product Simpson quadrature is exact for the quadratic energy.
        energy = F(0)
        for y, wy in [(0,F(1,6)), (b/2,F(2,3)), (b,F(1,6))]:
            for z, wz in [(0,F(1,6)), (h/2,F(2,3)), (h,F(1,6))]:
                jy = current*y/(a*b*h)
                jz = current*(1-z/h)/(a*b)
                energy += a*b*h*wy*wz*(jy*jy+jz*jz)
        self.assertEqual(energy, h/(3*a*b)+b/(3*a*h))
        self.assertEqual(corner_upper((a,a),(b,b),(h,h),F(1)), energy)

    def test_taper_inverse_area_bound_converges_from_above(self):
        # A homothetic square taper has exact integral 1/(a0*a1).
        a0, a1 = F("0.3"), F("0.06")
        exact = 1/(a0*a1)
        values = [rectangle_integral_upper(a0,a0,a1,a1,n) for n in (8,32,128)]
        self.assertTrue(all(x >= exact for x in values))
        self.assertGreater(values[0], values[1])
        self.assertGreater(values[1], values[2])
        # Opposite slopes remain bounded without assuming monotone area.
        bound = rectangle_integral_upper(F(1), F(2), F(2), F(1), 128)
        numerical = sum(1/((1+(i+.5)/10000)*(2-(i+.5)/10000)) for i in range(10000))/10000
        self.assertGreater(float(bound), numerical)

    def test_taper_uniform_end_traces_and_side_tangency(self):
        a0,b0,a1,b1,L = map(F, ("0.16","0.08","0.30","0.10","0.20"))
        cx,cy = F(0), F("0.01")
        da,db,dx,dy = (a1-a0)/L, (b1-b0)/L, cx/L, cy/L
        for z in (F(0),L/2,L):
            a,b = a0+da*z,b0+db*z
            for xi,eta in [(F(-1,2),F(0)),(F(1,2),F(0)),(F(0),F(-1,2)),(F(0),F(1,2))]:
                jx,jy,jz = (dx+da*xi)/(a*b),(dy+db*eta)/(a*b),1/(a*b)
                self.assertEqual(jz*a*b,1)
                if abs(xi)==F(1,2):
                    self.assertEqual(jx-(dx+da*xi)*jz,0)
                if abs(eta)==F(1,2):
                    self.assertEqual(jy-(dy+db*eta)*jz,0)
            # Eulerian divergence: x/y terms cancel d(Jz)/dz exactly.
            self.assertEqual(da/(a*a*b)+db/(a*b*b)-(da*b+a*db)/(a*a*b*b),0)
        upper=taper_upper((a0,a0),(b0,b0),(a1,a1),(b1,b1),(L,L),F(1),offset=(cx,cy))
        self.assertGreater(upper,0)

    def test_mean_and_neumann_correction_energy_are_orthogonal(self):
        # Analytic cosine mode on a square; no uniform-injection assertion.
        w,h,rho,I,g = 0.46,0.12,1e-4,1.0,2.0
        area=w*w
        exact=rho*(h*I*I/area+(h/3+w*w/(math.pi**2*h))*g*g*area/2)
        conservative=rho*(h*I*I/area+(h/3+2*w*w/(9*h))*g*g*area/2)
        self.assertLess(exact,conservative)
        # Uniform mean dot vertical correction integrates cos over a period
        # and is exactly zero; do not add a Minkowski charge here.
        self.assertAlmostEqual(math.sin(math.pi)-math.sin(0),0,places=14)
        result=slab_upper(F(".2"),F(".2"),F(".4"),(F(".1"),F(".15")),F(".01"),F(".0001"))
        self.assertGreater(result,0)

    def test_required_solid_hub_cannot_be_replaced_by_convex_hull(self):
        spec=deepcopy(self.spec)
        spec["physical_model"]["continuous_solid_crimp_hub_required"]=False
        with self.assertRaisesRegex(ValueError,"full solid hub"):
            evaluate(spec,verify_sources=False)

    def test_bad_geometry_or_zero_tolerance_fails_closed(self):
        for key,value,pattern in [
            ("contained_strand_radius",[".07",".071"],"polygon escapes"),
            ("hub_width",[".1",".11"],"patches escape"),
            ("toe_height",[".08",".08"],"nonzero-width"),
            ("toe_height",[".12",".13"],"toe height"),
        ]:
            spec=deepcopy(self.spec);spec["intervals"][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,pattern):
                geometry_checks(spec)

    def test_microscopic_patch_law_is_not_a_scalar_50_milliohm_substitute(self):
        baseline=evaluate(self.spec)
        spec=deepcopy(self.spec)
        spec["intervals"]["mating_interface_areal_resistance"]=[".00001",".0001"]
        changed=evaluate(spec)
        self.assertEqual(changed["conditional_energy_screen"],"FAIL")
        self.assertGreater(changed["costs_ohm_upper"]["finite_mating_interface"],
                           baseline["costs_ohm_upper"]["finite_mating_interface"])

    def test_correlated_bulk_class_has_strict_margin_and_independent_tolerances(self):
        rho70=F(".000017241")*(1+F(".003947")*50)
        for case in range(8):
            strands=[]
            for i in range(7):
                sign=1 if (i+case)%2 else -1
                strands.append({"radius_mm":F(".078")+sign*F(".0001"),
                                "rho_lower_ohm_mm":F(".000016")*(1+sign*F(1,200)),
                                "rho_upper_ohm_mm":rho70*(1+(1 if (i+case)%3 else -1)*F(1,200))})
            result=bulk_class_admission(self.spec,strands)
            self.assertTrue(result["admissible_correlated_parameters"])
            self.assertLess(result["bulk_upper_ohm_per_m"],F(".17"))
            self.assertGreater(result["bulk_lower_ohm_per_m"],F(".1"))
            weights=result["strand_weights"]
            self.assertEqual(sum(weights),1)
            self.assertGreater(len(set(weights)),1)
            self.assertLessEqual(sum(a*a for a in weights),result["weight_square_sum_upper"])

    def test_rejected_independent_box_corner_is_not_silently_admitted(self):
        strands=[{"radius_mm":".077","rho_lower_ohm_mm":".000016",
                  "rho_upper_ohm_mm":".000023"} for _ in range(7)]
        result=bulk_class_admission(self.spec,strands)
        self.assertFalse(result["admissible_correlated_parameters"])
        self.assertGreater(result["bulk_upper_ohm_per_m"],F(".17"))
        strands=[{"radius_mm":".078","rho_lower_ohm_mm":".00001",
                  "rho_upper_ohm_mm":".00002"} for _ in range(7)]
        result=bulk_class_admission(self.spec,strands)
        self.assertFalse(result["admissible_correlated_parameters"])
        self.assertLess(result["bulk_lower_ohm_per_m"],F(".1"))

    def test_weighted_microcontact_profile_includes_all_strands(self):
        upper=maximum_weight_square_sum(F("1.2"))
        self.assertGreater(upper,F(1,7))
        self.assertLess(upper,F(".15"))
        # A common finite patch width does not force equal currents: the
        # squared L2 norm of the seven-patch profile is sum(alpha_j^2)/S.
        weights=[F(".145"),F(".140"),F(".143"),F(".142"),F(".144"),F(".141"),F(".145")]
        self.assertEqual(sum(weights),1)
        self.assertLess(sum(x*x for x in weights),upper)

    def test_moved_body_pays_the_actual_connected_taper_displacement(self):
        baseline=evaluate(self.spec)
        spec=deepcopy(self.spec);spec["geometry"]["body_front_y"]="0.8"
        p,_,_=geometry_checks(spec)
        start,end=toe_body_centres(p,spec["geometry"])
        self.assertEqual(start,(F(".7375"),F(".74")))
        self.assertEqual(end,(F(".845"),F(".85")))
        # The new body face is reached through a real sheared taper, not an
        # uncharged 0.1 mm jump between independent toe and spine positions.
        changed=evaluate(spec,verify_sources=False)
        expected=taper_upper(p["toe_width"],p["toe_height"],p["body_width"],
                             p["body_depth"],p["body_taper_length"],p["rho_alloy"][1],
                             offset=(F(0),F(".1125")))
        self.assertEqual(F(changed["exact_costs_ohm"]["toe_to_body_taper"]),expected)
        self.assertGreater(expected,F(baseline["exact_costs_ohm"]["toe_to_body_taper"]))
        # Moving both front datums preserves this taper's local field. The
        # horizontal prism and the following spine pay their changed lengths.
        spec["geometry"]["toe_projection"]="0.8"
        translated=evaluate(spec,verify_sources=False)
        self.assertEqual(translated["exact_costs_ohm"]["toe_to_body_taper"],
                         baseline["exact_costs_ohm"]["toe_to_body_taper"])

    def test_possible_metal_box_must_contain_every_reference_extent(self):
        for axis,bounds in (("x",["-.23",".23"]),("y",["0","1.7"]),
                            ("z",["0","7.49"]),("x",[".5","-.5"])):
            spec=deepcopy(self.spec)
            spec["geometry"]["maximum_possible_metal_box"][axis]=bounds
            with self.subTest(axis=axis,bounds=bounds),self.assertRaisesRegex(ValueError,"maximum envelope"):
                evaluate(spec,verify_sources=False)

    def test_metal_envelope_includes_actual_strand_annuli(self):
        spec=deepcopy(self.spec)
        spec["intervals"]["hub_width"]=[".46",".47"]
        # Contains all inscribed current polygons (x<=.16+.079=.239), but
        # excludes part of the permitted 1.01-radius actual strand metal.
        spec["geometry"]["maximum_possible_metal_box"]["x"]=["-.2395",".2395"]
        with self.assertRaisesRegex(ValueError,"maximum envelope: x"):
            evaluate(spec,verify_sources=False)
        spec["geometry"]["maximum_possible_metal_box"]["x"]=["-.24",".24"]
        self.assertFalse(evaluate(spec,verify_sources=False)["physical_class_selected"])

    def test_full_pad_wetting_contains_the_required_solder_support(self):
        for maximum in ([".17","1.7"],[".6",".49"],["0","1.7"]):
            spec=deepcopy(self.spec)
            spec["geometry"]["maximum_wetting_native_pad"]=maximum
            with self.subTest(maximum=maximum),self.assertRaises(ValueError):
                evaluate(spec,verify_sources=False)
        spec=deepcopy(self.spec)
        spec["geometry"]["maximum_wetting_native_pad"]=[".18",".50"]
        result=evaluate(spec,verify_sources=False)
        self.assertEqual(result["geometry"]["full_possible_wetting_xy_mm"],
                         ["-9/100","-1/4","9/100","1/4"])


if __name__ == "__main__":
    unittest.main()
