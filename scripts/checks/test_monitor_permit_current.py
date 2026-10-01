import copy
import json
import unittest
from scripts.checks import monitor_permit_current as model


class MonitorCurrentTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(model.SPEC.read_text())
        self.catalog=json.loads(model.CATALOG.read_text())
        self.supply=json.loads(model.SUPPLY.read_text())
        self.current,_=model.load_current_facts()

    def build(self):
        return model.build(self.spec,self.catalog,self.supply,self.current)

    def test_reference_load_consumes_5v_allowance_once(self):
        initial=self.build()
        next(p for p in self.catalog['parts'] if p['mpn']=='RT0603BRD0714KL')['resistance_ohm']=28000
        for p in self.spec['components']:
            if p['mpn']=='RT0603BRD0714KL': p['value']=28000
        changed=self.build()
        delta_ref=changed['reference_output_total_A']-initial['reference_output_total_A']
        for key in initial['states']:
            delta_5v=(changed['states'][key]['conditional_dc_A']['+5V']
                      -initial['states'][key]['conditional_dc_A']['+5V'])
            self.assertAlmostEqual(delta_5v,delta_ref)
        self.assertLess(delta_ref,0)
        self.assertFalse(initial['qualification_accepted'])
        self.assertIsNone(initial['total_dynamic_current_A'])

    def test_dual_comparator_count_and_identity(self):
        self.assertEqual(self.current['U102']['units_per_package'],2)
        self.assertAlmostEqual(self.current['U102']['package_table_sum_A'],70e-6)
        self.current['U102']['mpn']='TLV9021DR'
        with self.assertRaisesRegex(ValueError,'MPN'): self.build()

    def test_allowance_changes_do_not_change_circuit_demand(self):
        initial=self.build()
        self.supply['load_envelope']['auxiliary_allowance_mA']['+5V']=1
        changed=self.build()
        key='both_paths_conservative_dc_screen'
        self.assertEqual(initial['states'][key]['conditional_dc_A'],changed['states'][key]['conditional_dc_A'])
        self.assertLess(changed['states'][key]['unallocated_auxiliary_A']['+5V'],0)

    def test_rewiring_and_resistor_identity_rejected(self):
        self.spec['components'][0]['pins']['1']='AGND'
        with self.assertRaisesRegex(ValueError,'topology'): self.build()
        self.spec=json.loads(model.SPEC.read_text())
        next(p for p in self.spec['components'] if p['ref']=='R124')['value']=1000
        with self.assertRaisesRegex(ValueError,'MPN'): self.build()

    def test_report_current(self):
        model.run(check=True)
