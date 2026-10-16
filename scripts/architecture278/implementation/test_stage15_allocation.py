import copy
import itertools
import json
import unittest
import stage15_allocation as m

class Allocation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.inp=json.loads((m.OUT/'allocation-input.json').read_text());cls.r=m.analyze(cls.inp)
    def test_matches_existing_transfer_no_correction(self):
        for p,_,_,_ in list(m.prior.all_cases(.0001,.001))[::17]:
            for _,v,c,a,x in m.prior.STATES:
                q=m.affine(v,c,a,x,p,reference_fraction=.001)
                self.assertAlmostEqual(q['out_V'],m.prior.previous.transfer(v,c,a,x,ref=5.005,**p)['out_V'])
                self.assertAlmostEqual(sum(q['signed_terms_V'].values()),q['fixed_setting_residual_V'])
    def test_paired_gain_cancels_intercept_not_absolute(self):
        p={'gr':1,'ga':1,'gm':1,'gcv':1,'ka':1,'kn':1.002}
        q=m.affine(0,5,.5,.5,p)
        self.assertAlmostEqual(q['CV_gain'],1)
        self.assertGreater(abs(q['fixed_setting_residual_V']),.004)
        pos=m.affine(0,5,.5,.5,p)['out_V'];neg=m.affine(0,-5,.5,.5,p)['out_V']
        self.assertAlmostEqual((pos-neg)/10,1)
    def test_every_scenario_exact_same_corner_delta(self):
        for scenario in self.r['scenarios']:
            self.assertEqual(len(scenario['state_rows']),10)
            for row in scenario['state_rows']:
                w=row['with_reference_initial_worst_witness'];v,c,a,x=(row[k] for k in ('vin_V','CV_V','atten_fraction','manual_fraction'))
                old=m.affine(v,c,a,x,w['params'],(),w['reference_fraction'])
                self.assertAlmostEqual(row['same_corner_counterfactual_delta_V'],w['out_V']-old['out_V'])
                self.assertAlmostEqual(sum(t['signed_V'] for t in row['ranked_signed_terms_at_same_witness']),w['fixed_setting_residual_V'])
    def test_all16_factor_combinations(self):
        self.assertEqual(len(self.r['scenarios']),16)
        self.assertEqual(len({tuple(r['removed_nonidealities']) for r in self.r['scenarios']}),16)
    def test_single_correction_cannot_suffice(self):
        for s in self.r['scenarios']:
            if len(s['removed_nonidealities'])<=1:self.assertGreater(s['maximum_abs_with_reference_initial_V'],.002)
        self.assertGreater(self.r['scenarios'][-1]['maximum_abs_with_reference_initial_V'],.005)
    def test_no_negative_allowance_or_budget_reset(self):
        for s in self.r['scenarios']:
            for row in s['state_rows']:
                a=row['remaining_at_same_worst_witness']
                self.assertEqual(a['additional_error_allowance_V'],max(0,a['remaining_absolute_budget_V']))
                if a['remaining_absolute_budget_V']<0:self.assertEqual(a['common_equal_Vos_ceiling_V'],0)
    def test_reference_necessary_ceiling_less_existing(self):
        r=self.r['necessary_next_conditions']
        self.assertGreater(r['perfect_four_corrections_manual_endpoint_reference_fraction_ceiling'],0)
        self.assertLess(r['perfect_four_corrections_manual_endpoint_reference_fraction_ceiling'],.0001)
        self.assertFalse(r['joint_four_corrections_suffice'])
    def test_refuse_temperature_corner_mix(self):
        q=copy.deepcopy(self.inp);q['network_matching_fraction']=.000125
        with self.assertRaises(ValueError):m.analyze(q)
    def test_no_geometry_change(self):
        q=copy.deepcopy(self.inp);q['component_geometry_changed']=True
        with self.assertRaises(ValueError):m.analyze(q)
if __name__=='__main__':unittest.main()
