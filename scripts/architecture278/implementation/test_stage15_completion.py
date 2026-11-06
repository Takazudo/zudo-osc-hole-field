"""Independent analysis-only checks using direct node equations and emitted witnesses."""
import itertools
import json
import math
from pathlib import Path
import unittest
from unittest.mock import patch
import stage15_completion as gate
import stage15_allocation as a
import stage15_load_allocation as load


def independent_output(vin,cv,atten,manual,p,removed=(),reference_fraction=0):
    ka=1 if 'attenuverter_ratio' in removed else p['ka']
    kn=1 if 'reference_inverter_ratio' in removed else p['kn']
    hi=5*(1+reference_fraction);lo=-kn*hi
    w_atten=atten*vin
    w_manual=(1-manual)*lo+manual*hi
    if 'atten_loading' not in removed:
        w_atten /= 1+(1000+10000*atten*(1-atten))/1e7
    if 'manual_loading' not in removed:
        w_manual /= 1+(1000+100000*manual*(1-manual))/1e7
    va=w_atten+(w_atten-vin)*ka
    summer=-(p['ga']*va+p['gm']*w_manual+p['gcv']*cv)
    return -p['gr']*summer


class IndependentCompletion(unittest.TestCase):
    def test_direct_nodes_match_all_counterfactual_witnesses(self):
        report=json.loads((a.OUT/'allocation-report.json').read_text())
        for scenario in report['scenarios']:
            for row in scenario['state_rows']:
                v,c,at,x=(row[k] for k in ('vin_V','CV_V','atten_fraction','manual_fraction'))
                for key in ('resistor_only_worst_witness','with_reference_initial_worst_witness'):
                    w=row[key]
                    out=independent_output(v,c,at,x,w['params'],scenario['removed_nonidealities'],w['reference_fraction'])
                    self.assertAlmostEqual(w['out_V'],out,places=12)
                    self.assertAlmostEqual(sum(w['signed_terms_V'].values()),out-((2*at-1)*v+c+5*(2*x-1)),places=12)
                w=row['with_reference_initial_worst_witness']
                before=independent_output(v,c,at,x,w['params'],(),w['reference_fraction'])
                self.assertAlmostEqual(row['same_corner_counterfactual_delta_V'],w['out_V']-before,places=12)

    def test_conditioned_load_cases_from_same_physical_corner(self):
        report=json.loads((a.OUT/'allocation-report.json').read_text())
        corners=list(a.prior.all_cases(.0001,.001))
        for scenario in report['scenarios']:
            for row in scenario['state_rows']:
                vin,cv,at,x=(row[k] for k in ('vin_V','CV_V','atten_fraction','manual_fraction'))
                ideal=(2*at-1)*vin+cv+5*(2*x-1)
                for case in row['conditioned_output_load_cases']:
                    A=case['parameters']['A0'];ro=case['parameters']['ro_DC_ohm']
                    actual=[]
                    for w in case['endpoint_witnesses']:
                        p=corners[w['corner_index']][0]
                        u=independent_output(vin,cv,at,x,p,scenario['removed_nonidealities'],w['reference_fraction'])
                        opened=A*u/(A+1)
                        loaded=A*u/(A+1+(998+ro)/10000)
                        self.assertAlmostEqual(w['open_fixed_residual_V'],opened-ideal,places=12)
                        self.assertAlmostEqual(w['loaded_fixed_residual_V'],loaded-ideal,places=12)
                        self.assertAlmostEqual(w['load_change_V'],loaded-opened,places=12)
                        self.assertAlmostEqual(sum(w['loaded_signed_terms_V'].values()),loaded-ideal,places=12)
                        actual.append(loaded-ideal)
                    self.assertLessEqual(actual[0],actual[1])
                    for actual_value,reported in zip(actual,case['loaded_signed_interval_V']):
                        self.assertAlmostEqual(actual_value,reported,places=12)

    def test_paired_gain_and_intercept_with_nonzero_other_stimulus(self):
        p={'ka':1.002,'kn':.998,'gr':1.0001,'ga':.9999,'gm':1.0001,'gcv':1.0001}
        at,x=.75,.25
        cvp=independent_output(2,5,at,x,p);cvm=independent_output(2,-5,at,x,p)
        inp=independent_output(5,2,at,x,p);inm=independent_output(-5,2,at,x,p)
        row=a.affine(2,2,at,x,p)
        self.assertAlmostEqual((cvp-cvm)/10,row['CV_gain'])
        self.assertAlmostEqual((inp-inm)/10,row['IN_gain'])
        self.assertAlmostEqual((cvp+cvm)/2,2*row['IN_gain']+row['zero_input_intercept_V'])
        self.assertNotAlmostEqual(row['fixed_setting_residual_V'],2*(row['CV_gain']-1),places=5)

    def test_counterfactual_interaction_is_not_additive(self):
        p={'ka':1.002,'kn':1.002,'gr':1,'ga':1,'gm':1,'gcv':1}
        f=lambda removed:independent_output(0,0,.5,.25,p,removed)
        base=f(())
        separate=(f(('reference_inverter_ratio',))-base)+(f(('manual_loading',))-base)
        joint=f(('reference_inverter_ratio','manual_loading'))-base
        self.assertGreater(abs(joint-separate),1e-6)

    def test_missing_implementation_never_hidden_as_zero(self):
        r=json.loads((a.OUT/'allocation-report.json').read_text())
        self.assertFalse(r['hardware_acceptance']);self.assertFalse(r['component_geometry_changed'])
        self.assertFalse(r['necessary_next_conditions']['single_correction_suffices'])
        self.assertFalse(r['necessary_next_conditions']['joint_four_corrections_suffice'])
        for s in r['scenarios']:
            for row in s['state_rows']:
                v=row['with_reference_initial_worst_witness']['fixed_setting_residual_V']
                b=row['remaining_at_same_worst_witness']
                self.assertAlmostEqual(b['remaining_absolute_budget_V'],.002-abs(v))
                self.assertEqual(b['additional_error_allowance_V'],max(0,.002-abs(v)))

    def test_output_exact_kcl_including_signed_leak_and_internal_resistance(self):
        for u,A,ro,rl,ib,ic in itertools.product((-5,0,5),(1000,1e5),(0,70),(None,10000),(-1e-9,1e-9),(-2e-9,2e-9)):
            vos=30e-6
            jack=load.output_with_cap_leak(u,A,ro,rl,vos,ib,ic)
            ileakback=ib-ic
            fb=jack-load.RF*ileakback
            i_load=0 if rl is None else jack/rl
            drive=jack+load.RS*(i_load+ileakback)
            internal=A*(u+vos-fb)
            self.assertAlmostEqual(internal-drive,ro*(i_load+ib),places=9)

    def test_inverted_load_limit_is_tight(self):
        z=load.allowable_z(5,.001)
        self.assertAlmostEqual(5*z/(10000+z),.001)
        self.assertGreater(5*(z+1e-3)/(10000+z+1e-3),.001)
        self.assertAlmostEqual(load.load_delta(5,1e5,50),-load.output_dc(5,1e5,50,None)*(1048/100001)/(10000+1048/100001))

    def test_guard_rejects_load_acceptance_promotion(self):
        original=Path.read_text
        def changed(path,*args,**kwargs):
            raw=original(path,*args,**kwargs)
            if path==gate.OUT/'load-report.json':
                r=json.loads(raw);r['hardware_acceptance']=True
                return json.dumps(r)
            return raw
        with patch.object(gate,'preserve',return_value=360),patch.object(Path,'read_text',changed):
            with self.assertRaisesRegex(ValueError,'acceptance'):gate.build()

    def test_guard_rejects_incomplete_review_coverage(self):
        import hashlib
        original=Path.read_text
        name='scripts/architecture278/implementation/stage15_load_allocation.py'
        def changed(path,*args,**kwargs):
            if path==gate.OUT/'review-root.json':
                return json.dumps({'independent_review':True,'authorship_exclusion':'test fixture',
                    'source_sha256':{name:hashlib.sha256((gate.ROOT/name).read_bytes()).hexdigest()}})
            return original(path,*args,**kwargs)
        with patch.object(Path,'read_text',changed):
            with self.assertRaisesRegex(ValueError,'review coverage'):gate.reviews()

    def test_input_node_kcl_signed_currents(self):
        for vin,S,Id,Is in itertools.product((-5,0,5),(0,10,1000),(-1e-9,1e-9),(-2e-9,2e-9)):
            e=load.input_error(vin,S,drain_leak_A=Id,sense_current_A=Is)
            sense=vin+e;protected=sense+10000*Is
            if S:self.assertAlmostEqual((vin-protected)/S,protected/100000+Id+Is,places=12)
            else:self.assertAlmostEqual(protected,vin)


if __name__=='__main__':unittest.main()
