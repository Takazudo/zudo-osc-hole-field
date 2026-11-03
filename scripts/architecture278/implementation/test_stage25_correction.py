"""Regression tests for candidate identity, allocation honesty and manufacturing limits."""
import copy
import math
import unittest
import stage25_correction as s


class CorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = s.read(s.OUT/'candidate.json')
        cls.p = s.read(s.ROOT/s.REL/'stage16/inputs-report.json')['packages']['RV1308']
        cls.m = s.read(s.ROOT/s.REL/'stage18/compatibility-report.json')['unit_metadata']['RV1308.0']

    def validate(self, c):
        s.validate_candidate(c, self.p, self.m)

    def test_candidate_is_valid(self):
        self.validate(self.c)

    def test_reject_changed_pin_net(self):
        c=copy.deepcopy(self.c);c['changes']['RV1308']['pins']['2']='AGND'
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_nc_short(self):
        c=copy.deepcopy(self.c);c['changes']['RV1308']['pins']['4']='AGND'
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_missing_pin(self):
        c=copy.deepcopy(self.c);del c['changes']['RV1308']['pins']['5']
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_moved_hardware(self):
        c=copy.deepcopy(self.c);c['changes']['RV1308']['retained_placement']['origin_mm'][0]+=1
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_lost_unit_metadata(self):
        c=copy.deepcopy(self.c);c['changes']['RV1308']['retained_source_unit_metadata']={}
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_wrong_detent(self):
        c=copy.deepcopy(self.c);c['changes']['RV1308']['after_mpn']='PTV09A-4220F-B103'
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_loosened_criterion(self):
        c=copy.deepcopy(self.c);c['static_target_V']=.005
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_unapproved_native_or_adoption(self):
        for key,val in [('hardware_qualification',True),('native_execution','RUN'),('factory_protocol_approved',True)]:
            c=copy.deepcopy(self.c);c[key]=val
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(c)

    def test_reject_reference_rewire(self):
        c=copy.deepcopy(self.c);c['retained']['negative_reference_resistors_ohm']=[100000,100000]
        with self.assertRaises(ValueError):self.validate(c)

    def test_reject_removed_return_or_changed_filter(self):
        for key in ('return_ohm','cap_F'):
            c=copy.deepcopy(self.c);c['retained'][key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):self.validate(c)

    def test_reject_precision_knob_law(self):
        c=copy.deepcopy(self.c);c['prescribed_voltage_at_knob_positions']=True
        with self.assertRaises(ValueError):self.validate(c)

    def test_nominal_loading_independent_dense_grid(self):
        for rp in (1e4,1e5):
            actual=s.pot_screen(rp)['maximum_abs_ideal_loading_error_V']
            grid=max(abs(5*(2*x/10000-1)*(1000+rp*x/10000*(1-x/10000))/(1e7+1000+rp*x/10000*(1-x/10000))) for x in range(10001))
            self.assertAlmostEqual(actual,grid,delta=1e-9)

    def test_nominal_recommendation_numbers(self):
        old,new=s.pot_screen(1e5),s.pot_screen(1e4)
        self.assertAlmostEqual(old['maximum_abs_ideal_loading_error_V'],.005093968,places=9)
        self.assertAlmostEqual(new['maximum_abs_ideal_loading_error_V'],.000796799,places=9)
        self.assertAlmostEqual(new['center_1percent_settling_s'],.000161125,places=9)
        self.assertEqual(new['reference_to_reference_current_A'],.001)
        self.assertEqual(new['total_track_power_W'],.01)
        self.assertEqual(old['open_wiper_V_per_nA'],new['open_wiper_V_per_nA'])

    def test_invalid_component_domains(self):
        for x in (0,-1,float('nan'),float('inf'),True):
            with self.subTest(x=x),self.assertRaises(ValueError):s.pot_screen(x)

    def test_no_mathematical_baseline_cancellation(self):
        self.assertAlmostEqual(s.baseline_residual(5,0,.0003,1.0002),.0013)
        self.assertNotAlmostEqual(s.baseline_residual(5,0,.0003,1.0002),.001)

    def test_changed_reference_not_removed_by_initial_setup(self):
        self.assertAlmostEqual(s.baseline_residual(0,0,.0002,1,.0007),.0009)

    def test_unknown_terms_cannot_produce_pass(self):
        r=s.static_allocation(.0001,dict.fromkeys(s.TERMS))
        self.assertIsNone(r['complete_bound_V'])
        self.assertIsNone(r['mathematical_allocation_within_target'])
        self.assertAlmostEqual(r['one_shared_remainder_V'],.00099995)
        self.assertFalse(r['hardware_acceptance'])

    def test_missing_term_rejected(self):
        terms=dict.fromkeys(s.TERMS);terms.pop(s.TERMS[-1])
        with self.assertRaises(ValueError):s.static_allocation(.0001,terms)

    def test_duplicate_or_invented_term_rejected(self):
        terms=dict.fromkeys(s.TERMS);terms['reference_initial_added_again']=.005
        with self.assertRaises(ValueError):s.static_allocation(.0001,terms)

    def test_remainder_is_shared(self):
        terms={k:.0002 for k in s.TERMS};r=s.static_allocation(.0001,terms)
        self.assertFalse(r['mathematical_allocation_within_target'])
        self.assertGreater(r['complete_bound_V'],.002)

    def test_zero_algebra_is_not_hardware_acceptance(self):
        r=s.static_allocation(.0001,dict.fromkeys(s.TERMS,0))
        self.assertTrue(r['mathematical_allocation_within_target'])
        self.assertFalse(r['hardware_acceptance'])

    def test_bad_allocation_bound_rejected(self):
        for x in (-1,float('nan'),float('inf'),True):
            terms=dict.fromkeys(s.TERMS);terms[s.TERMS[0]]=x
            with self.subTest(x=x),self.assertRaises(ValueError):s.static_allocation(.0001,terms)

    def test_full_temperature_network_uses_one_envelope(self):
        r=s.static_allocation(.000125,dict.fromkeys(s.TERMS))
        self.assertAlmostEqual(r['network_ratio_bound_V'],.001250078125)

    def test_default_hole_cannot_guarantee(self):
        self.assertFalse(s.hole_route(4,'ENIG')['diameter_contains_only_drawing_allowed_values'])

    def test_tighter_diameter_does_not_fix_other_gates(self):
        r=s.hole_route(4,'ENIG',tighter=True)
        self.assertTrue(r['diameter_contains_only_drawing_allowed_values'])
        for k in ('position_guaranteed','fixing_holes_guaranteed','finished_hole_interpretation_confirmed','complete_route_qualified'):
            self.assertFalse(r[k])

    def test_tighter_option_not_for_two_layer_or_hasl(self):
        for layers,finish in ((2,'ENIG'),(4,'HASL')):
            with self.assertRaises(ValueError):s.hole_route(layers,finish,tighter=True)

    def test_tighter_option_not_for_fixing_holes(self):
        with self.assertRaises(ValueError):s.hole_route(4,'ENIG',2.8,tighter=True)

    def test_supplier_observation_missing_rejected(self):
        with self.assertRaises(ValueError):s.supplier_observation('<html>no stock</html>','C5848782')

    def test_receipt_redirect_rejected(self):
        r=s.read(s.OUT/'sources.json')['ptv09'];r['final_url']='https://example.com/error'
        with self.assertRaises(ValueError):s.validate_receipt(r)

    def test_receipt_missing_timezone_rejected(self):
        r=s.read(s.OUT/'sources.json')['ptv09'];r['retrieved_UTC']='2026-10-17T00:00:00'
        with self.assertRaises(ValueError):s.validate_receipt(r)

    def test_receipt_unavailable_hash_rejected(self):
        r=s.read(s.OUT/'sources.json')['ptv09'];r['sha256']='0'*64
        with self.assertRaises(ValueError):s.validate_receipt(r)

    def test_deterministic_build(self):
        self.assertEqual(s.build(),s.build())

    def test_reference_delta_not_absolute(self):
        r=s.build()['reference_alternatives']
        self.assertAlmostEqual(r['spare_between_two_arbitrary_full_temperature_points_sensitivity_V'],.003225)
        self.assertEqual(r['spare_between_two_arbitrary_full_temperature_points_sensitivity_V'],2*r['spare_bias_PW_full_temperature_absolute_sensitivity_V'])
        self.assertIsNone(r['local_temperature_delta_bound_V'])
        self.assertAlmostEqual(r['retained_reference_full_spec_box_span_V'],.0066)
        self.assertIsNone(r['post_setup_reference_error_bound_V'])


if __name__ == '__main__':unittest.main()
