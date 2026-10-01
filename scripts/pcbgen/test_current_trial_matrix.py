"""Current-specific refined-field, +PSD work and physical KCL checks."""
import unittest
import numpy as np
from shapely.geometry import box
from scripts.pcbgen.test_sheet_volume import assembly,RHO,THICKNESS
from scripts.pcbgen.current_trial_matrix import current_matrix


class CurrentTrialTests(unittest.TestCase):
    def test_refined_current_preserves_sources_and_encloses_direct_trial_gram(self):
        source=box(.4,.4,.65,.65);sink=box(-.7,-.5,-.45,-.25)
        conductor=assembly([(0,0)],(-1,-1,1,1),source,sink,1)
        profiles=[[(3,source,1.),(1,sink,-1.)],[(0,source,1.),(1,sink,-1.)]]
        direct=conductor.area_profile_matrices(profiles,RHO,THICKNESS)
        conductor.certificate_mode='current'
        class PerturbedFirstSolve:
            def __init__(self,factor):self.factor=factor;self.first=True
            def solve(self,rhs):
                result=self.factor.solve(rhs)
                if self.first:
                    result[5,0]+=1e-8;self.first=False
                return result
        conductor.hybrid_factor=PerturbedFirstSolve(conductor.hybrid_factor)
        result=current_matrix(conductor,profiles,RHO,THICKNESS,batch_size=1)
        self.assertGreater(result['current_refinement'][0]['initial_float64_residual_A'],1e-8)
        self.assertGreater(result['current_refinement'][0]['corrections'],0)
        self.assertLess(result['maximum_equation_residual_A'],1e-8)
        for row in result['physical_gate_components']:
            for key in ('operator_residual_A','sheet_source_balance_A','barrel_balance_A','shared_face_continuity_A'):
                self.assertLess(row[key],1e-8)
        self.assertGreaterEqual(np.linalg.eigvalsh(result['energy']-direct['upper']).min(),-1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(result['energy']-direct['lower']).min(),0)
        self.assertTrue(all(r['gauge_work_omitted_only_because_trial_coefficient_is_exact_zero'] for r in result['current_residual_work']))
        self.assertGreater(result['maximum_residual_work_allowance_ohm'],0)
        self.assertTrue(result['conservation_correction'])
        self.assertTrue(result['numerical_current_allowance'])


if __name__=='__main__':unittest.main()
