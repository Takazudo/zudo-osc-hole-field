import copy
from fractions import Fraction as F
import itertools
import json
from pathlib import Path
import tempfile
import unittest

from scripts.checks import negative_inverter_candidate as m


class InverterStudyTests(unittest.TestCase):
    def setUp(self):
        self.frozen=m.snapshot()
        self.data={k:json.loads(self.frozen[p]) for k,p in m.INPUTS.items()}

    def test_normal_strict_budget_and_equality_witness(self):
        r=m.calculate(self.data);b=F(r['normal']['exact_budget_fraction'])
        low,high=m.factors(.001,25e-6,25,[-40,125])
        g=F(4990,151000)*low/high
        threshold=F('.4')*F('.93')*F('1.016')*F('1.017')
        self.assertEqual(F('11.74')*g-b,threshold)
        self.assertLess(F('11.74')*g-b-F(1,10**12),threshold)
        self.assertLessEqual(F(r['normal']['strict_total_additive_output_error_budget_V']),b)
        self.assertIsNone(r['normal']['actual_joint_error_max_V'])
        self.assertGreater(r['normal']['source_10k_to_midsupply_load_sink_current_at_candidate_output_A'][0],
                           r['normal']['ideal_feedback_output_source_current_upper_A'])

    def test_forced_output_countermodel_and_independent_kcl(self):
        r=m.calculate(self.data)
        self.assertTrue(r['passive_ports']['forced_sum_inside_cold_differential_0p2V'])
        self.assertFalse(r['rejected_RG_1k_countermodel']['forced_sum_inside_cold_differential_0p2V'])
        vs=m.node(F('12.48'),F('5.2'),F(151000),F(4990),F(150),F('0.00001'))
        self.assertEqual((vs-F('12.48'))/151000+(vs-F('5.2'))/4990+vs/150,F('.00001'))
        self.assertGreater(r['passive_ports']['forced_branch_current_A']['RF'][1],.001)

    def test_power_bounds_cover_interior_resistance_points(self):
        low,high=m.factors(.001,25e-6,25,[-40,125]);box=m.passive_screen(low,high,150,F('.00001'))
        for fs in itertools.product((low,F(1),high),repeat=4):
            r1,r2,rf,rg=[n*f for n,f in zip((150000,1000,4990,150),fs)]
            vn,vo,inj=F('12.48'),F('5.2'),F('.00001');vs=m.node(vn,vo,r1+r2,rf,rg,inj)
            currents=((vn-vs)/(r1+r2),(vn-vs)/(r1+r2),(vo-vs)/rf,vs/rg)
            for name,res,i in zip(('RN1','RN2','RF','RG'),(r1,r2,rf,rg),currents):
                self.assertLessEqual(i*i*res,F(box['forced_branch_power_upper_W'][name]))

    def test_cold_current_sensitivity_is_not_a_source_limit(self):
        original=m.calculate(self.data)['passive_ports']['cold_highZ_output_V']
        self.data['spec']['conditions']['cold_current_sensitivity_each_A']=0
        zero=m.calculate(self.data)['passive_ports']['cold_highZ_output_V']
        self.assertLess(zero[1],original[1]);self.assertLess(original[0],zero[0])
        for bad in (-1e-9,float('nan'),float('inf'),True,.01):
            self.data['spec']['conditions']['cold_current_sensitivity_each_A']=bad
            with self.assertRaises(ValueError):m.calculate(self.data)

    def test_static_fault_does_not_promote_timing(self):
        r=m.calculate(self.data);f=r['negative_fault_witness']
        self.assertTrue(f['conditional_below_every_UV_trip'])
        self.assertFalse(f['at_least_10percent_UV_overdrive_all_corners'])
        self.assertLess(f['minimum_UV_overdrive_fraction'],.007)
        self.assertIsNone(f['maximum_total_detection_s'])
        self.assertTrue(r['outside_normal_band_no_trip_countermodel']['inside_nominal_trip_window'])
        self.assertIsNone(r['source_observations']['opa']['maximum_startup_or_settling_s'])

    def test_source_condition_and_closure_mutations(self):
        mutations=[
            lambda d:d['sources']['observations']['opa'].update(maximum_startup_or_settling_s=2e-6),
            lambda d:d['sources']['observations']['opa'].update(iq_conditions='Any supply and load'),
            lambda d:d['sources']['observations']['tps']['timing_conditions'].update(overdrive_fraction=.005),
            lambda d:d['sources']['sources'].pop(),
            lambda d:d['sources']['sources'].append(copy.deepcopy(d['sources']['sources'][0])),
            lambda d:d['sources']['sources'][0].update(sha256='0'*64),
            lambda d:d['sources']['sources'][0].update(mpn='TPS37044OTHER'),
        ]
        for change in mutations:
            d=copy.deepcopy(self.data);change(d)
            with self.assertRaises(ValueError):m.calculate(d)

    def test_topology_scenarios_and_flags_are_locked(self):
        mutations=[
            lambda d:d['spec']['resistors'][3].update(ohm=1000),
            lambda d:d['spec']['resistors'][0].update(dnp=True),
            lambda d:d['spec']['amplifier_pins'].update({'2':'+5V'}),
            lambda d:d['spec']['hypothetical_interface'].update(SENSE2_pin='2'),
            lambda d:d['spec']['conditions'].update(forced_VN_V=[-10,10]),
            lambda d:d['spec']['conditions'].update(resistor_temperature_C=[0,25]),
            lambda d:d['supply']['source_requirement']['required_load_voltage_magnitude_V'].update({'-12V':[11.9,12.1]}),
            lambda d:d['spec'].update(selected=True),
            lambda d:d['spec'].update(qualification_accepted=True),
            lambda d:d['spec'].update(canonical_protection_implemented=True),
        ]
        for change in mutations:
            d=copy.deepcopy(self.data);change(d)
            with self.assertRaises(ValueError):m.calculate(d)

    def test_cold_highz_both_polarities_and_two_current_sources(self):
        r=m.calculate(self.data)['passive_ports']
        self.assertLess(r['cold_highZ_output_V'][0],0)
        self.assertGreater(r['cold_highZ_output_V'][1],0)
        self.assertLess(r['cold_highZ_output_V'][1],.066)
        vn,rn,rg,rf,ii,io=map(F,('-12.48','151000','150','4990','.00001','-.00001'))
        vi=(vn/rn+ii+io)/(1/rn+1/rg);vo=vi+io*rf
        self.assertEqual((vo-vi)/rf,io)
        self.assertEqual((vi-vn)/rn+vi/rg+(vi-vo)/rf,ii)

    def test_current_comparison_charges_reference_once_and_stays_conditional(self):
        r=m.calculate(self.data)['hypothetical_current_comparison'];old=self.data['current']
        removed=old['reference_output_total_A']+old['active_device_source_rows']['U102']['package_table_sum_A']+old['active_device_source_rows']['U103']['package_table_sum_A']
        self.assertAlmostEqual(r['removed_reference_and_comparator_5V_A'],removed,places=15)
        self.assertAlmostEqual(r['new_conditional_5V_A'],.00467182695338154,places=14)
        self.assertFalse(r['application_qualified']);self.assertIsNone(r['dynamic_current_max_A'])
        self.assertEqual(r['original_auxiliary_allowance_mA'],{'+5V':20,'+12V':20,'-12V':20})

    def test_current_comparison_rejects_negative_and_nonfinite_operands(self):
        for bad in (-1,float('nan'),float('inf')):
            d=copy.deepcopy(self.data);d['current']['reference_output_total_A']=bad
            with self.assertRaises(ValueError):m.calculate(d)
        d=copy.deepcopy(self.data)
        d['current']['active_device_source_rows']['U102']['package_table_sum_A']=35e-6
        with self.assertRaises(ValueError):m.calculate(d)

    def test_frozen_input_provenance_and_mutation_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for p,b in self.frozen.items():
                path=root/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
            frozen=m.snapshot(root);result=m.build(frozen)
            path=root/m.INPUTS['spec'];d=json.loads(path.read_bytes());d['conditions']['cold_current_sensitivity_each_A']=0;path.write_text(json.dumps(d))
            self.assertEqual(result['sensitivity_current_each_A'],1e-5)
            self.assertEqual(m.build(frozen),result)
            with self.assertRaises(ValueError):m.verify_unchanged(frozen,root)

    def test_current_report_dependency_cannot_be_rebound(self):
        frozen=dict(self.frozen)
        path='scripts/checks/monitor_permit_current.py'
        frozen[path]+=b'\n# changed producer\n'
        with self.assertRaises(ValueError):m.build(frozen)

    def test_outward_rounding_and_factor_domains(self):
        x=F(1,3)
        self.assertLessEqual(F(m.display(x)),x);self.assertGreaterEqual(F(m.display(x,True)),x)
        for t,k in ((-.001,25e-6),(.001,-25e-6),(1,0),(.001,.1),(float('nan'),0)):
            with self.assertRaises(ValueError):m.factors(t,k,25,[-40,125])


if __name__=='__main__':unittest.main()
