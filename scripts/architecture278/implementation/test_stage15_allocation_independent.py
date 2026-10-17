"""Load-author independent review tests for root's signed allocation composition."""
import json
import unittest
import stage15_allocation as m

class IndependentAllocation(unittest.TestCase):
    def test_direct_stage_KCL_for_all_factor_masks(self):
        p={'kn':1.002002002,'ka':.998001998,'ga':1.0001,'gm':1/1.0001,'gcv':1,'gr':1.0001}
        for mask in range(16):
            removed=[key for bit,key in enumerate(m.FACTORS) if mask&(1<<bit)]
            for _,vin,cv,a,x in m.prior.STATES:
                kn=1 if 'reference_inverter_ratio' in removed else p['kn']
                ka=1 if 'attenuverter_ratio' in removed else p['ka']
                beta=a if 'atten_loading' in removed else a*1e7/(1e7+1000+10000*a*(1-a))
                manual_damp=1 if 'manual_loading' in removed else 1e7/(1e7+1000+100000*x*(1-x))
                vref=5.005;vneg=-kn*vref
                vmanual=(x*vref+(1-x)*vneg)*manual_damp
                vatten=(1+ka)*beta*vin-ka*vin
                vsummer=-(p['ga']*vatten+p['gm']*vmanual+p['gcv']*cv)
                self.assertAlmostEqual(m.affine(vin,cv,a,x,p,removed,.001)['out_V'],-p['gr']*vsummer,places=12)

    def test_analytic_coefficients_from_voltage_perturbation(self):
        p={'kn':1.002,'ka':.998,'ga':1.0001,'gm':.9999,'gcv':1,'gr':1.0001}
        for _,_,_,a,x in m.prior.STATES:
            ours=m.coefficients(a,x,p)
            base=m.prior.previous.transfer(0,0,a,x,**p)['out_V']
            for key,value in ours.items():
                changed=m.prior.previous.transfer(0,0,a,x,errors={key:.001},**p)['out_V']
                self.assertAlmostEqual(changed-base,.001*value,places=12)

    def test_persisted_loaded_signed_terms_close(self):
        r=json.loads((m.OUT/'allocation-report.json').read_text())
        for scenario in r['scenarios']:
            for state in scenario['state_rows']:
                for case in state['conditioned_output_load_cases']:
                    for w in case['endpoint_witnesses']:
                        self.assertAlmostEqual(sum(w['loaded_signed_terms_V'].values()),w['loaded_fixed_residual_V'],places=11)
                        self.assertAlmostEqual(w['loaded_fixed_residual_V']-w['open_fixed_residual_V'],w['load_change_V'],places=12)

    def test_reference_ceiling_is_inverse_not_component_claim(self):
        r=json.loads((m.OUT/'allocation-report.json').read_text())['necessary_next_conditions']
        gain=1.0001**2
        self.assertAlmostEqual(5*(gain*(1+r['perfect_four_corrections_manual_endpoint_reference_fraction_ceiling'])-1)+r['analysis_only_other_error_reserve_V'],.002,places=12)
        self.assertFalse(r['single_correction_suffices']);self.assertFalse(r['joint_four_corrections_suffice'])

if __name__=='__main__':unittest.main()
