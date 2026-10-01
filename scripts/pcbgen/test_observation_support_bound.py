from fractions import Fraction as F
import math
import unittest
from scripts.pcbgen.observation_support_bound import support_bound, sqrt_upper, upward


class ObservationSupportTests(unittest.TestCase):
    def fixture(self):
        return dict(observation_kind='voltage', energy_upper=3, energy_lower='2.915',
                    source_ids=['near', 'far'],
                    sources=[{'id':'near', 'trial_value':'.8', 'source_energy_upper_ohm':1},
                             {'id':'far', 'trial_value':'2.5', 'source_energy_upper_ohm':3}],
                    redistribution_ids=['shape'],
                    redistribution=[{'id':'shape', 'trace_oscillation_upper':'1.7',
                                     'shape_energy_upper_ohm':2}],
                    source_budget_A=1, redistribution_budget_A=1)

    def test_complete_resistor_chain_observation_bounds_every_signed_scenario(self):
        # Ground--1ohm--near--2ohm--far. b observes far, exact dual energy3.
        # Trial v=(0,.8,2.5): lower=2*2.5-(.8**2+1.7**2/2)=2.915.
        # Unit near/far source energies1/3; near-to-far redistribution energy2.
        result = support_bound(**self.fixture())
        self.assertGreaterEqual(result['observation_abs_upper'], 5)
        self.assertLess(result['observation_abs_upper'], 5.2)
        for x in range(-4,5):
            for y in range(-4,5):
                if abs(x)+abs(y)>4:continue
                for z in range(-4,5):
                    exact = abs(F(x,4)+3*F(y,4)-2*F(z,4))
                    self.assertGreaterEqual(F(result['observation_abs_upper']), exact)

    def test_zero_net_current_keeps_shape_contribution(self):
        values=self.fixture();values.update(source_budget_A=0,energy_upper=4,energy_lower=0,
            redistribution_budget_A=2,
            redistribution=[{'id':'shape','trace_oscillation_upper':0,'shape_energy_upper_ohm':9}])
        result=support_bound(**values)
        self.assertEqual(result['net_source_contribution_upper'],0)
        self.assertEqual(result['redistribution_contribution_upper'],12)

    def test_independent_global_budgets_not_repeated_per_contact(self):
        values=self.fixture();values.update(energy_upper=0,energy_lower=0,source_budget_A=2,
            redistribution_budget_A=3)
        for row in values['sources']:row['trial_value']=2
        values['redistribution']=[{'id':'shape','trace_oscillation_upper':1,'shape_energy_upper_ohm':2}]
        result=support_bound(**values)
        self.assertEqual(result['observation_abs_upper'],7)
        self.assertEqual(sum(result['maximizing_net_amplitudes_A_upper'].values()),2)

    def test_caps_need_evidence_and_obey_one_total_budget(self):
        values=self.fixture();values.update(energy_upper=0,energy_lower=0,source_budget_A=1,
                                          redistribution_budget_A=0)
        values['sources'][1].update(absolute_current_cap_A='.25')
        with self.assertRaisesRegex(ValueError,'evidence'):support_bound(**values)
        values['sources'][1]['cap_evidence']='synthetic fixture cap, not a physical component claim'
        result=support_bound(**values)
        self.assertEqual(result['maximizing_net_amplitudes_A_upper'],{'far':.25,'near':.75})
        self.assertGreaterEqual(F(result['observation_abs_upper']),F('1.225'))

    def test_missing_foreign_duplicate_and_unbounded_shape_refuse(self):
        for mutation in ('missing','foreign','duplicate','missing_energy'):
            values=self.fixture()
            if mutation=='missing':values['redistribution']=[]
            elif mutation=='foreign':values['redistribution'][0]['id']='unknown'
            elif mutation=='duplicate':values['sources'].append(values['sources'][0])
            else:del values['redistribution'][0]['shape_energy_upper_ohm']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):support_bound(**values)

    def test_negative_gap_nonfinite_and_boolean_refuse(self):
        for key,value in [('energy_lower',4),('energy_upper',math.inf),
                          ('source_budget_A',-1),('source_budget_A',True)]:
            values=self.fixture();values[key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):support_bound(**values)

    def test_outward_square_root_and_conversion(self):
        for value in (F(0),F(2),F(1,10**400),F(10**400),F(1,3)):
            root=sqrt_upper(value)
            self.assertGreaterEqual(root*root,value)
            if root:self.assertLess((root-F(1,1<<80))**2,value)
        for value in (F(1,10),F(1,10**400),F(10**300)):
            self.assertGreaterEqual(F(upward(value)),value)
        with self.assertRaisesRegex(ValueError,'representable'):upward(F(10**400))

    def test_current_observation_has_conductance_gap_and_ampere_output(self):
        values=self.fixture();values['observation_kind']='wire_current'
        result=support_bound(**values)
        self.assertEqual(result['witness_gap_unit'],'siemens')
        self.assertEqual(result['observation_unit'],'A')
