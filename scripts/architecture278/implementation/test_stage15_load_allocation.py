import copy
import json
import unittest
import stage15_load_allocation as s

class LoadAllocation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=[json.loads(p.read_text()) for p in [s.OUT/'load-input.json',s.inherited.OUT.parent/'stage10/inventory-report.json',s.ROOT/'design/standard/electrical-standard.json']]
        cls.report=s.analyze(*cls.args)

    def test_exact_output_KCL_with_bias(self):
        u,A,ro,RL,vos,ib=5,1234,76,10000,80e-6,17e-9
        v=s.output_dc(u,A,ro,RL,vos,ib)
        vf=v-100*ib;drive=v+998*(v/RL+ib);internal=drive+ro*(v/RL+ib)
        self.assertAlmostEqual(internal,A*(u+vos-vf),places=10)

    def test_cap_leak_KCL(self):
        u,A,ro,RL,ib,ic=-3,4321,87,10000,15e-9,2e-9
        v=s.output_with_cap_leak(u,A,ro,RL,ib=ib,icap=ic)
        vf=v-100*(ib-ic);drive=v+998*(v/RL+ib-ic);internal=drive+ro*(v/RL+ib)
        self.assertAlmostEqual(internal,A*(u-vf),places=10)

    def test_delta_equals_closed_loop_impedance(self):
        for u in (-5,0,5):
            A,ro=1000,100;vo=s.output_dc(u,A,ro,None);z=(998+ro)/(A+1)
            self.assertAlmostEqual(s.load_delta(u,A,ro),-vo*z/(10000+z),places=13)

    def test_series_drop_is_not_residual(self):
        self.assertAlmostEqual(s.load_delta(5,100000,0),-4.989895221463314e-6,places=13)
        self.assertAlmostEqual(5*998/10000,.499)

    def test_load_criterion_inverse(self):
        z=s.allowable_z(5,.001);self.assertAlmostEqual(z,2.000400080016003)
        self.assertAlmostEqual(5*z/(10000+z),.001)
        self.assertIsNone(s.allowable_z(0,.001))

    def test_paired_offset_changes_not_cancelled(self):
        delta=s.output_dc(5,10000,100,10000,vos=.001)-s.output_dc(5,10000,100,None,vos=0)
        self.assertGreater(delta,.0009)

    def test_input_signed_KCL(self):
        vin,S,Rp,Rlim,Id,I=5,123,100000,10000,1e-9,20e-9
        sense=vin+s.input_error(vin,S,Rp,Rlim,Id,I);protected=sense+Rlim*I
        self.assertAlmostEqual((vin-protected)/S,protected/Rp+Id+I,places=14)
        self.assertAlmostEqual(s.input_error(-5,10),-s.input_error(5,10))

    def test_input_allowance_inverse(self):
        a=s.input_allowances(.00025,5,1);limit=a['series_resistance_limit_if_no_other_input_errors_ohm']
        self.assertAlmostEqual(abs(s.input_error(5,limit)),.00025)
        self.assertLess(a['remaining_after_declared_divider_V'],0)

    def test_input_source_binding_mutation(self):
        args=copy.deepcopy(self.args);args[1]['packages']['U7102']['pins']['2']='/A01/IN_TIP'
        with self.assertRaises(ValueError):s.analyze(*args)
        args=copy.deepcopy(self.args);args[1]['packages']['R7108']['unit_records'][0]['value']='1000 Ω'
        with self.assertRaises(ValueError):s.analyze(*args)

    def test_same_temperature_bias_not_conflated(self):
        args=copy.deepcopy(self.args);args[0]['common_condition']['OPA_bias_25C_max_A']=15e-9
        with self.assertRaises(ValueError):s.analyze(*args)

    def test_internal_bias_numeric_allocation(self):
        a=s.internal_bias_allowances(.00025,.5,.5)
        total=sum(a['known_absolute_coefficients_ohm'].values())
        self.assertAlmostEqual(a['common_independent_pin_current_ceiling_A']*total,.00025)
        self.assertAlmostEqual(a['conditional_known_bias_at15nA_fulltemp_V']/a['conditional_known_bias_at20pA25C_V'],750)
        self.assertEqual(s.internal_bias_allowances(0,.5,.5)['common_independent_pin_current_ceiling_A'],0)

    def test_all_states_and_conditional_status(self):
        self.assertEqual(len(self.report['per_state_allowances']),10)
        for case in self.report['engineering_scenarios']:
            self.assertEqual(len(case['rows']),13)
            self.assertTrue(all(r['hardware_load_criterion_met'] is None for r in case['rows']))
        self.assertIsNone(self.report['actual_complete_load_bound_V'])
        self.assertEqual(len(self.report['required_parameters']),7)

if __name__=='__main__':unittest.main()
