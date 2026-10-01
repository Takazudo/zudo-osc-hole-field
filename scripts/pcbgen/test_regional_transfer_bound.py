from fractions import Fraction as F
import unittest
from scripts.pcbgen.test_cut_current_witness import solve_exact
from scripts.pcbgen.regional_transfer_bound import regional_bounds


class RegionalTransferTests(unittest.TestCase):
    def fixture(self, source_cycle=0, observation_cycle=0):
        edges=[{'id':'a','from':'J','to':'K','resistance_ohm':2},
               {'id':'b','from':'J','to':'P','resistance_ohm':3},
               {'id':'c','from':'P','to':'K','resistance_ohm':5}]
        _,source=solve_exact(edges,source={'J':1,'K':-1,'P':0})
        _,observation=solve_exact(edges,source={'J':0,'K':-1,'P':1})
        cycle={'a':1,'b':-1,'c':-1}
        s={k:source[k]+source_cycle*cycle[k] for k in cycle}
        b={k:observation[k]+observation_cycle*cycle[k] for k in cycle}
        rows=[{'id':e['id'],'source_energy_upper':e['resistance_ohm']*s[e['id']]**2,
               'observation_energy_upper':e['resistance_ohm']*b[e['id']]**2,
               'trial_cross_lower':e['resistance_ohm']*s[e['id']]*b[e['id']],
               'trial_cross_upper':e['resistance_ohm']*s[e['id']]*b[e['id']]} for e in edges]
        args=dict(region_ids=list(cycle),common_region_ids=['a','c'],regions=rows,
                  source_energy_upper=sum(r['source_energy_upper'] for r in rows),
                  observation_energy_upper=sum(r['observation_energy_upper'] for r in rows),
                  source_energy_lower=sum(e['resistance_ohm']*source[e['id']]**2 for e in edges),
                  observation_energy_lower=sum(e['resistance_ohm']*observation[e['id']]**2 for e in edges))
        exact={e['id']:e['resistance_ohm']*source[e['id']]*observation[e['id']] for e in edges}
        return args,exact

    def test_zero_gap_gives_actual_signed_regional_transfers(self):
        args,exact=self.fixture();result=regional_bounds(**args)
        self.assertLess(exact['b'],0)
        for key,value in exact.items():
            self.assertLessEqual(F(result['regions'][key]['transfer_lower']),value)
            self.assertGreaterEqual(F(result['regions'][key]['transfer_upper']),value)
            self.assertEqual(result['regions'][key]['error_radius_upper'],0)
        self.assertEqual(sum(exact.values()),1)

    def test_conserved_perturbed_trials_cover_exact_solution(self):
        for x in (F(-1),F(-1,4),F(0),F(3,4)):
            for y in (F(-2,3),F(0),F(1,2)):
                args,exact=self.fixture(x,y);result=regional_bounds(**args)
                for key,region in result['regions'].items():
                    self.assertLessEqual(F(region['transfer_lower']),exact[key])
                    self.assertGreaterEqual(F(region['transfer_upper']),exact[key])
                for name,keys in [('whole_domain',list(exact)),('common',['a','c'])]:
                    value=sum(exact[k] for k in keys)
                    self.assertLessEqual(F(result[name]['transfer_lower']),value)
                    self.assertGreaterEqual(F(result[name]['transfer_upper']),value)

    def test_independent_regional_uppers_can_exceed_tighter_complete_upper(self):
        # The exact same physical fields admit loose regional bounds and a
        # tight global bound simultaneously. No energy or gap is increased.
        for x,y in ((F(0),F(0)),(F(1,4),F(-2,3))):
            args,exact=self.fixture(x,y)
            original=regional_bounds(**args)
            for row in args['regions']:
                row['source_energy_upper']+=10
                row['observation_energy_upper']+=10
            result=regional_bounds(**args)
            self.assertEqual(result['source_gap_upper'],original['source_gap_upper'])
            self.assertEqual(result['observation_gap_upper'],original['observation_gap_upper'])
            self.assertEqual(result['whole_domain'],original['whole_domain'])
            for key,value in exact.items():
                self.assertLessEqual(F(result['regions'][key]['transfer_lower']),value)
                self.assertGreaterEqual(F(result['regions'][key]['transfer_upper']),value)

    def test_loose_regional_uppers_do_not_hide_global_cross_contradiction(self):
        args,_=self.fixture()
        for row in args['regions']:
            row.update(source_energy_upper=100,observation_energy_upper=100)
        args['regions'][0].update(trial_cross_lower=99,trial_cross_upper=100)
        with self.assertRaisesRegex(ValueError,'complete trial energies'):
            regional_bounds(**args)

    def test_opposite_regional_crosses_cannot_hide_joint_energy_contradiction(self):
        rows=[dict(id=name,source_energy_upper=10,observation_energy_upper=10,
                   trial_cross_lower=cross,trial_cross_upper=cross)
              for name,cross in [('positive',2),('negative',-2)]]
        # Every individual cross fits the global norm and their sum is zero,
        # but their absolute sum requires more complete energy than supplied.
        with self.assertRaisesRegex(ValueError,'complete trial energies'):
            regional_bounds(region_ids=['positive','negative'],common_region_ids=['positive'],
                            regions=rows,source_energy_upper=2,source_energy_lower=0,
                            observation_energy_upper=2,observation_energy_lower=0)

    def test_missing_overlap_identity_and_energy_inconsistency_rejected(self):
        for mutation in ('missing','duplicate','foreign_common','energy','cross','negative_gap'):
            args,_=self.fixture()
            if mutation=='missing':args['regions'].pop()
            elif mutation=='duplicate':args['regions'].append(args['regions'][0])
            elif mutation=='foreign_common':args['common_region_ids']=['unknown']
            elif mutation=='energy':args['source_energy_upper']=0
            elif mutation=='cross':args['regions'][0].update(trial_cross_lower=99,trial_cross_upper=100)
            else:args['source_energy_lower']=99
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):regional_bounds(**args)
