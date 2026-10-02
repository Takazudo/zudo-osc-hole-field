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

    def test_clamped_reference_feed_bypasses_bottom_resistor(self):
        before=self.build()['reference_output_branch_bounds_A']['R109_to_R112_clamped']
        # A change of R113 value/MPN cannot lower the clamped feed bound.
        part=next(p for p in self.spec['components'] if p['ref']=='R113')
        part['mpn']='RT0603BRD0714KL';part['value']=14000
        after=self.build()['reference_output_branch_bounds_A']['R109_to_R112_clamped']
        self.assertEqual(before,after)
        self.assertGreater(before,3.31/7250)

    def test_report_current(self):
        model.run(check=True)

    def test_invalid_resistor_factors_cannot_cancel(self):
        part=next(p for p in self.catalog['parts'] if p['mpn']=='RT0603BRD074K99L')
        part['tolerance_fraction']=2
        part['tcr_abs_per_C']=0.02
        with self.assertRaisesRegex(ValueError,'independent resistor'): self.build()

    def test_both_buffers_and_bleeder_are_counted(self):
        report=self.build()
        self.assertEqual(set(self.current),{'U101','U102','U103','U104','U105','U106'})
        self.assertAlmostEqual(report['conditional_active_quiescent_sum_A']/1e-6,210)
        original=report['states']['permit_enabled']['conditional_dc_A']['+5V']
        # Change only R125 to the already cataloged 14k identity.
        part=next(p for p in self.spec['components'] if p['ref']=='R125')
        part.update(value=14000,mpn='RT0603BRD0714KL')
        changed=self.build()
        delta=changed['states']['permit_enabled']['conditional_dc_A']['+5V']-original
        self.assertAlmostEqual(delta,changed['timing_bleed_conditional_dc_A']-report['timing_bleed_conditional_dc_A'])
        self.assertGreater(delta,0)

    def test_both_high_inputs_miss_the_fixed_icc_test_point(self):
        report=self.build()['steady_high_icc_applicability']
        self.assertEqual(report['source_high_input_test_V'],5.5)
        self.assertEqual(report['buffers']['U104']['conditional_steady_high_input_V'],[4.81,5.2])
        low,high=report['buffers']['U106']['conditional_steady_high_input_V']
        self.assertAlmostEqual(low,4.356563565626415)
        self.assertAlmostEqual(high,4.744184382574166)
        for row in report['buffers'].values():
            self.assertFalse(row['icc_high_test_point_matches_entire_conditional_interval'])
            self.assertFalse(row['application_qualified'])
        self.assertIsNone(report['actual_extra_supply_current_A'])

    def test_divider_interval_uses_actual_resistor_corners(self):
        original=self.build()['steady_high_icc_applicability']
        part=next(p for p in self.spec['components'] if p['ref']=='R125')
        part.update(value=14000,mpn='RT0603BRD0714KL')
        changed=self.build()['steady_high_icc_applicability']
        self.assertLess(changed['U106_divider_gain_bounds'][1],
                        original['U106_divider_gain_bounds'][0])
        self.assertEqual(changed['buffers']['U104'],original['buffers']['U104'])

    def test_modeled_test_point_match_is_not_qualification(self):
        self.supply['source_requirement']['required_load_voltage_magnitude_V']['+5V']=[5.5,5.5]
        report=self.build()['steady_high_icc_applicability']
        self.assertTrue(report['buffers']['U104']['icc_high_test_point_matches_entire_conditional_interval'])
        self.assertFalse(report['buffers']['U104']['application_qualified'])
        self.assertFalse(report['buffers']['U106']['icc_high_test_point_matches_entire_conditional_interval'])

    def test_rail_level_reinterpretation_of_source_row_is_rejected(self):
        for ref in ('U104','U106'):
            with self.subTest(ref=ref):
                original=self.current[ref]['conditions']
                self.current[ref]['conditions']=original.replace('VI5.5V orGND','VI=VCC orGND')
                with self.assertRaisesRegex(ValueError,'ICC source condition'):
                    self.build()
                self.current[ref]['conditions']=original

    def test_nonphysical_supply_and_resistance_corners_are_rejected(self):
        original=copy.deepcopy(self.supply)
        for bounds in ([0,5.2],[5.2,4.81],[float('nan'),5.2],[4.81,float('inf')],[True,5.2]):
            with self.subTest(bounds=bounds):
                self.supply['source_requirement']['required_load_voltage_magnitude_V']['+5V']=bounds
                with self.assertRaisesRegex(ValueError,'supply bounds'): self.build()
        self.supply=original
        row=next(p for p in self.catalog['parts'] if p['mpn']=='RC0805FR-07100KL')
        for tolerance in (-.01,float('nan'),float('inf'),True):
            with self.subTest(tolerance=tolerance):
                row['tolerance_fraction']=tolerance
                with self.assertRaisesRegex(ValueError,'independent resistor'): self.build()
