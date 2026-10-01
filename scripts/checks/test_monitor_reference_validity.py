import copy
import json
import unittest
from scripts.checks import monitor_reference_validity as model


class ReferenceValidityTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(model.SPEC.read_text())
        self.catalog=json.loads(model.CATALOG.read_text())
        self.old=json.loads(model.rail.SPEC.read_text())
        self.negative=json.loads(model.negative.SPEC.read_text())
        self.facts,self.mpn=model.source_facts()

    def build(self):
        return model.calculate(self.spec,self.catalog,self.old,self.negative,self.facts,self.mpn)

    def test_coarse_good_does_not_prove_precision(self):
        result=self.build()
        self.assertFalse(result['narrow_reference_proved_by_coarse_enclosure'])
        for study in result['studies'].values():
            self.assertFalse(study['negative_normal_band_guaranteed'])
            self.assertLess(study['negative_normal_UV_margin_V'],0)
            self.assertLess(study['negative_normal_OV_margin_V'],0)
        counter=result['forced_nominal_counterexample']
        self.assertTrue(counter['coarse_monitor_ideal_released'])
        self.assertTrue(counter['negative_comparators_ideal_released'])
        self.assertFalse(counter['negative_rail_inside_required_band'])

    def test_narrow_legacy_study_is_not_mutated(self):
        before=copy.deepcopy(self.negative)
        self.build()
        self.assertEqual(self.negative,before)
        self.assertEqual(self.negative['reference']['normal_target_V'],[3.29,3.31])

    def test_recovery_is_stricter_than_retaining_good(self):
        study=self.build()['studies']['zero_sense_current']
        outer=study['possible_retained_good_reference_extent_V']
        inner=study['guaranteed_recovery_interval_V']
        self.assertLess(outer[0],inner[0])
        self.assertLess(inner[1],outer[1])

    def test_stale_network_or_wrong_divider_family_rejected(self):
        self.negative['resistors'][0]['ohm']+=1
        with self.assertRaisesRegex(ValueError,'captured resistor'):self.build()
        self.negative=json.loads(model.negative.SPEC.read_text())
        next(p for p in self.catalog['parts'] if p['mpn']=='RT0603BRD075K1L')['tolerance_fraction']=0.01
        with self.assertRaisesRegex(ValueError,'divider evidence'):self.build()

    def test_source_accuracy_changes_propagate(self):
        baseline=self.build()['studies']['zero_sense_current']['events_V']['UV_trip']
        self.facts['accuracy']['value']['at_0p4V_fraction']=0
        revised=self.build()['studies']['zero_sense_current']['events_V']['UV_trip']
        self.assertGreater(revised[0],baseline[0])
        self.assertLess(revised[1],baseline[1])

    def test_report_reproduces(self):
        model.run(check=True)
