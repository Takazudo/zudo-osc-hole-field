import copy
import json
import unittest
from fractions import Fraction as F
from scripts.checks import monitor_reference_compatibility as model


class ReferenceCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(model.negative.SPEC.read_text())
        self.bands=json.loads((model.ROOT/self.spec['normal_voltage_source']).read_text())['source_requirement']['required_load_voltage_magnitude_V']['-12V']
        self.report=model.calculate(self.spec,self.bands)

    def exact(self,record):
        return F(record['numerator'],record['denominator'])

    def test_limiting_witnesses_reach_exact_zero_margin(self):
        self.assertEqual(self.report['resistor_corner_count'],256)
        for label,event,index,sign in [('lower_OV','OV',1,-1),('upper_UV','UV',0,1)]:
            row=self.report['limiting_corner_witnesses'][label]
            boundary=self.exact(row['boundary_V']);slope=self.exact(row['trip_slope_V_per_V'])
            spread=self.exact(row['trip_error_spread_V'])
            self.assertEqual(slope*boundary+sign*spread,model.rail.number(self.bands[index]))

    def test_display_rounding_stays_strictly_inside(self):
        values=list(map(model.rail.number,self.report['inward_display_reference_interval_V']))
        boundaries=self.report['strict_reference_boundaries_exact']
        self.assertGreater(values[0],self.exact(boundaries['lower']))
        self.assertLess(values[1],self.exact(boundaries['upper']))
        # Exactly representable boundaries still require inward movement.
        self.assertGreater(model.rail.number(model.inward(F(3),True)),3)
        self.assertLess(model.rail.number(model.inward(F(4),False)),4)

    def test_forward_model_switches_acceptance_across_each_boundary(self):
        exact=self.report['strict_reference_boundaries_exact']
        for label,direction in [('lower',1),('upper',-1)]:
            boundary=float(self.exact(exact[label]))
            for sign,expected in [(direction,True),(-direction,False)]:
                changed=copy.deepcopy(self.spec);value=boundary+sign*1e-5
                changed['reference']['normal_target_V']=[value,value]
                self.assertEqual(model.negative.calculate(changed)['conditional_static_normal_band_accepted'],expected)

    def test_original_reference_is_preserved_and_fault_acceptance_stays_false(self):
        self.assertEqual(self.report['original_reference_assumption_V'],[3.29,3.31])
        self.assertTrue(self.report['original_assumption_strictly_inside'])
        for name in ('qualification_accepted','canonical_protection_implemented','reference_requirement_changed','fault_rejection_accepted'):
            self.assertFalse(self.report[name])
        case=self.report['forced_nominal_counterexample']
        self.assertTrue(case['reference_inside_compatibility_interval'])
        self.assertTrue(case['comparators_ideal_released'])
        self.assertFalse(case['negative_rail_inside_normal_band'])

    def test_empty_interval_and_unsupported_slope_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'empty strict'):model.calculate(self.spec,[10,15])
        changed=copy.deepcopy(self.spec)
        next(p for p in changed['resistors'] if p['ref']=='RR')['ohm']=1e9
        with self.assertRaisesRegex(ValueError,'nonpositive reference'):model.calculate(changed,self.bands)

    def test_changed_error_envelope_narrows_compatibility(self):
        changed=copy.deepcopy(self.spec);changed['conditions']['powered_comparator_error_V']*=1.1
        after=model.calculate(changed,self.bands)['inward_display_reference_interval_V']
        before=self.report['inward_display_reference_interval_V']
        self.assertGreater(after[0],before[0]);self.assertLess(after[1],before[1])
