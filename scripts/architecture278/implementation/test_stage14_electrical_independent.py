"""Independent review checks against inspected primary conditions and charge units."""
import json
from decimal import Decimal as D
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/architecture-278/implementation/stage14'

class IndependentElectrical(unittest.TestCase):
    def test_primary_conditions(self):
        inp=json.loads((OUT/'electrical-input.json').read_text())
        ref=inp['reference_conditions']; buf=inp['buffer_conditions']
        self.assertEqual(ref['IQ_max_full_temperature_A'],.0012)
        self.assertEqual(ref['VIN_abs_V'],[-.3,18])
        self.assertEqual(ref['VOUT_abs_V'],[-.3,5.5])
        self.assertEqual(buf['PW_bias_max_full_temperature_A'],15e-9)
        self.assertEqual(buf['input_abs_current_A'],.01)
        self.assertEqual(buf['input_abs_commonmode_beyond_rails_V'],.5)

    def test_charge_energy_with_independent_decimal_units(self):
        report=json.loads((OUT/'electrical-report.json').read_text(),parse_float=D)
        for row,cap_uF,volts in zip(report['capacitor_accounting'],('4.7','22'),('13.2','5')):
            for ix,tol in enumerate(('.9','1.1')):
                charge=D(cap_uF)*D(tol)*D(volts)/D(1000000)
                self.assertLess(abs(row['initial_charge_interval_C'][ix]-charge),D('1e-17'))
                self.assertLess(abs(row['initial_energy_interval_J'][ix]-charge*D(volts)/2),D('1e-17'))

    def test_no_offstate_or_lifetime_acceptance(self):
        report=json.loads((OUT/'electrical-report.json').read_text())
        self.assertIsNone(report['discharge_time_upper_bound_s'])
        self.assertIsNone(report['startup_time_upper_bound_s'])
        self.assertIsNone(report['reference_conditions']['guaranteed_VOUT_to_VIN_reverse_current_A'])
        self.assertFalse(report['hardware_acceptance'])
        self.assertTrue(all(not r['complete_or_joint_condition_bound'] for r in report['raw_reference_conditioned_load_subtotals']))
        self.assertTrue(all(c['status']=='NOT RUN' for c in report['validation_cases']))

    def test_raw_dc_fanout_independently_from_inventory_graph(self):
        graph=json.loads((OUT/'interfaces-report.json').read_text())
        endpoints=set()
        for edge in graph['edges']:
            if edge['net']=='/A01/C534b2a_RAW_5V': endpoints.update((edge['from'],edge['to']))
        self.assertEqual(endpoints,{'C7102:1','U7101:6','U7104:3'})

if __name__=='__main__': unittest.main()
