from copy import deepcopy
from fractions import Fraction as F
import unittest

from scripts.pcbgen.harness_collar_bound import assembled_harness_bound, collar_certificate


class HarnessCollarTests(unittest.TestCase):
    def collar(self, identity="left"):
        return dict(collar_id=identity, reference_length_lower_mm=".6",
                    reference_diameter_upper_mm=".18", metric_ratio_upper=1,
                    trace_kind="uniform_reference_section", full_physical_section=True,
                    insulated_lateral_boundary=True, source_free_collar=True,
                    no_unmodeled_internal_interface_energy=True,
                    premise_reference="Synthetic complete-prism fixture, not actual JST metal")

    def fixture(self):
        return dict(test_domain_id="synthetic_complete_harness",
                    test_boundary_reference="Two isolated external excitation terminals; all input power retained",
                    test_resistance_upper_ohm=".08",
                    test_bound_kind="total_passive_input_power_over_current_squared",
                    linear_passive_dc=True, other_power_sources_absent=True,
                    all_excitation_current_crosses_both_collars=True,
                    other_electrical_ports_absent=True,
                    fixture_energy_subtracted=False, collars_disjoint=True,
                    collars=[self.collar(),self.collar("right")],
                    adapters=[dict(region_id="left_solder", matching_collar_id="left",
                                   matching_trace_reference="Synthetic complete uniform face",
                                   outside_tested_domain_and_collars=True, energy_upper_ohm=".001"),
                              dict(region_id="right_solder", matching_collar_id="right",
                                   matching_trace_reference="Synthetic complete uniform face",
                                   outside_tested_domain_and_collars=True, energy_upper_ohm=".001")],
                    allowance_ohm=".1")

    def test_exact_multiplier_and_two_disjoint_collars_charged_once(self):
        proof=assembled_harness_bound(**self.fixture())
        self.assertEqual(F(proof["maximum_collar_multiplier_exact"]),F(121,100))
        self.assertEqual(F(proof["total_upper_exact_ohm"]),F(".0988"))
        self.assertGreaterEqual(F(proof["total_upper_ohm"]),F(".0988"))
        self.assertEqual(proof["conditional_local_allowance_screen"],"PASS")
        self.assertIn("NOT ADMITTED",proof["status"])

    def test_unequal_collar_gains_use_max_not_product_or_sum(self):
        inputs=self.fixture();inputs["collars"][1]["reference_length_lower_mm"]=".3"
        proof=assembled_harness_bound(**inputs)
        self.assertEqual(F(proof["maximum_collar_multiplier_exact"]),F(36,25))
        self.assertEqual(F(proof["total_upper_exact_ohm"]),F(".1172"))
        self.assertEqual(proof["conditional_local_allowance_screen"],"FAIL")

    def test_polynomial_current_field_trace_and_divergence_are_exact(self):
        # D=[0,1]^2, L=1. Original J=(-a(x^2-x),0,I+a*z*(2x-1)).
        # chi=z and psi_x=a*z*(x^2-x) give
        # K=(a(2z-1)(x^2-x),0,I+a*z*(1-z)*(2x-1)).
        for I in (F(0),F(1),F(-3,2)):
            for a in (F(-4),F(0),F(7,3)):
                for x in (F(0),F(1,3),F(1)):
                    for z in (F(0),F(2,5),F(1)):
                        jx=-a*(x*x-x);jz=I+a*z*(2*x-1)
                        kx=a*(2*z-1)*(x*x-x);kz=I+a*z*(1-z)*(2*x-1)
                        self.assertEqual(-a*(2*x-1)+a*(2*x-1),0)
                        self.assertEqual(a*(2*z-1)*(2*x-1)+a*(1-2*z)*(2*x-1),0)
                        if x in (0,1):self.assertEqual((jx,kx),(0,0))
                        if z==0:self.assertEqual(kz,jz)
                        if z==1:self.assertEqual(kz,I)
                original_energy=I*I+F(13,90)*a*a
                corrected_energy=I*I+a*a/F(45)
                # d=sqrt(2)<3/2 gives a wholly rational sufficient bound.
                certificate=self.collar();certificate.update(reference_length_lower_mm=1,
                                                              reference_diameter_upper_mm="1.5")
                gamma=collar_certificate(**certificate)["multiplier_exact"]
                self.assertLessEqual(corrected_energy,gamma*original_energy)

    def test_exact_volume_quadrature_matches_polynomial_energy(self):
        # Boole quadrature is exact through degree five on [0,1].
        nodes=[F(0),F(1,4),F(1,2),F(3,4),F(1)]
        weights=[F(x,90) for x in (7,32,12,32,7)]
        I,a=F(1),F(3,2);old=new=F(0)
        for x,wx in zip(nodes,weights):
            for z,wz in zip(nodes,weights):
                jx=-a*(x*x-x);jz=I+a*z*(2*x-1)
                kx=a*(2*z-1)*(x*x-x);kz=I+a*z*(1-z)*(2*x-1)
                old+=wx*wz*(jx*jx+jz*jz)
                new+=wx*wz*(kx*kx+kz*kz)
        self.assertEqual(old,I*I+F(13,90)*a*a)
        self.assertEqual(new,I*I+a*a/F(45))

    def test_weighted_profile_and_axial_metric_allowance_are_explicit(self):
        c=self.collar();c.update(trace_kind="conductivity_weighted_reference_section",
                               reference_sigma_ratio_upper=4,
                               conductivity_profile_reference="Synthetic two-layer sigma_0 field",
                               metric_ratio_upper="1.1")
        proof=collar_certificate(**c)
        self.assertEqual(proof["multiplier_exact"],F("1.584"))
        self.assertIn("sigma_0",proof["target_trace"])
        c["conductivity_profile_reference"]=None
        with self.assertRaisesRegex(ValueError,"conductivity profile"):
            collar_certificate(**c)
        c=self.collar();c["no_unmodeled_internal_interface_energy"]=False
        with self.assertRaisesRegex(ValueError,"interface charge"):
            collar_certificate(**c)

    def test_full_section_and_power_measurement_premises_fail_closed(self):
        for key in ("full_physical_section","insulated_lateral_boundary","source_free_collar"):
            c=self.collar();c[key]=False
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,"Full physical"):
                collar_certificate(**c)
        for key,value in [("test_bound_kind","point_kelvin_voltage_over_current"),
                          ("fixture_energy_subtracted",True),("other_power_sources_absent",False),
                          ("all_excitation_current_crosses_both_collars",False),
                          ("other_electrical_ports_absent",False),
                          ("collars_disjoint",False),("linear_passive_dc",False)]:
            f=self.fixture();f[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):assembled_harness_bound(**f)

    def test_invalid_metrics_and_duplicate_or_unmatched_regions_refuse(self):
        for key,value in [("reference_length_lower_mm",0),("reference_diameter_upper_mm",0),
                          ("metric_ratio_upper",".9"),("reference_sigma_ratio_upper",2)]:
            c=self.collar();c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):collar_certificate(**c)
        f=self.fixture();f["adapters"][1]["region_id"]="left_solder"
        with self.assertRaisesRegex(ValueError,"once-only"):assembled_harness_bound(**f)
        f=self.fixture();f["adapters"][1]["matching_collar_id"]="missing"
        with self.assertRaisesRegex(ValueError,"named collar"):assembled_harness_bound(**f)
        f=self.fixture();f["adapters"][1]["outside_tested_domain_and_collars"]=False
        with self.assertRaisesRegex(ValueError,"outside"):assembled_harness_bound(**f)

    def test_scalar_end_contact_resistance_does_not_bound_strand_profiles(self):
        # Header-to-seven-strand star: one 0.03-ohm branch, six M-ohm branches.
        # An equipotential electrode shorts all strand ends, so R_scalar<0.03
        # for every M. The prescribed equal strand profile costs (0.03+6M)/49.
        for M in (F(1),F(100),F(10000)):
            scalar=1/(1/F(".03")+6/M)
            equal_profile_energy=(F(".03")+6*M)/49
            self.assertLess(scalar,F(".03"))
            self.assertGreater(equal_profile_energy,F(".05"))

    def test_parallel_fixture_bypass_invalidates_total_current_normalization(self):
        harness,shunt=F(100),F(".001")
        measured_parallel=1/(1/harness+1/shunt)
        self.assertLess(measured_parallel,F(".001"))
        self.assertGreater(harness,10000*measured_parallel)
        inputs=self.fixture()
        inputs["test_resistance_upper_ohm"]=measured_parallel
        inputs["all_excitation_current_crosses_both_collars"]=False
        with self.assertRaisesRegex(ValueError,"no bypass"):
            assembled_harness_bound(**inputs)


if __name__ == "__main__":
    unittest.main()
