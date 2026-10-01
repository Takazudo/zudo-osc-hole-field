import copy
import json
import unittest
from scripts.checks import monitor_permit_behavior as model


class MonitorPermitBehaviorTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(model.SPEC.read_text())
        self.report=model.build(self.spec)

    def test_short_fault_clears_but_does_not_rearm(self):
        case=self.report['cases']['short_good_fast_low']
        self.assertTrue(case[1]['q'])
        self.assertFalse(case[2]['q'])
        self.assertTrue(case[2]['clock'])
        self.assertFalse(case[3]['q'])

    def test_long_fault_rearms(self):
        case=self.report['cases']['long_good_fast_low']
        self.assertFalse(case[2]['clock'])
        self.assertTrue(case[3]['q'])

    def test_power_loss_never_assumes_low_or_recovery(self):
        case=self.report['cases']['control_power_loss']
        self.assertIsNone(case[2]['q'])
        self.assertIsNone(case[3]['q'])
        self.assertIsNone(self.report['physical_release_bound_s'])

    def test_rc_change_changes_clock_delay(self):
        changed=copy.deepcopy(self.spec)
        next(p for p in changed['components'] if p['ref']=='C109')['value'] *= 2
        other=model.build(changed)
        self.assertAlmostEqual(other['ideal_charge_to_clock_s'],2*self.report['ideal_charge_to_clock_s'])

    def test_reference_load_includes_coarse_divider(self):
        changed=copy.deepcopy(self.spec)
        for p in changed['components']:
            if p['ref'] in ['R109','R110','R111','R112','R113']:
                p['value'] *= 2
        delta=(self.report['nominal_partial_current_ledger']['reference_output_A']
               -model.build(changed)['nominal_partial_current_ledger']['reference_output_A'])
        self.assertAlmostEqual(delta,0.0002)
        self.assertIsNone(self.report['nominal_partial_current_ledger']['total_supply_current_A'])

    def test_no_qualification_promotion(self):
        self.spec['qualification_accepted']=True
        with self.assertRaises(ValueError):
            model.build(self.spec)

    def test_committed_report_current(self):
        model.run(check=True)

    def test_rewiring_and_duplicate_reference_rejected(self):
        altered=copy.deepcopy(self.spec)
        next(p for p in altered['components'] if p['ref']=='R120')['pins']['1']='AGND'
        with self.assertRaisesRegex(ValueError,'topology'): model.build(altered)
        altered=copy.deepcopy(self.spec)
        altered['components'].append(altered['components'][0])
        with self.assertRaisesRegex(ValueError,'topology'): model.build(altered)

    def test_order_states_and_evaluated_hash(self):
        a=self.report['cases']['arrival:+12V,VN,+5V']
        b=self.report['cases']['arrival:+5V,VN,+12V']
        self.assertNotEqual(a['rail_states'],b['rail_states'])
        self.assertEqual(sum(a['rail_states'][1].values()),1)
        changed=copy.deepcopy(self.spec)
        next(p for p in changed['components'] if p['ref']=='C109')['value'] *= 2
        self.assertNotEqual(self.report['evaluated_input_sha256'],model.build(changed)['evaluated_input_sha256'])
