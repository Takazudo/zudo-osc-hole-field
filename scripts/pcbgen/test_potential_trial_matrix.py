"""The bounded potential-only path preserves actual four-foil functionals."""
import unittest
import numpy as np
from shapely.geometry import box
from scripts.pcbgen.test_sheet_volume import assembly, RHO, THICKNESS
from scripts.pcbgen.potential_trial_matrix import potential_matrix


class PotentialTrialTests(unittest.TestCase):
    def test_shared_barrel_and_finite_source_witness(self):
        source=box(.4,.4,.65,.65);sink=box(-.7,-.5,-.45,-.25)
        conductor=assembly([(0,0)],(-1,-1,1,1),source,sink,1)
        profiles=[[(3,source,1.),(1,sink,-1.)],[(0,source,1.),(1,sink,-1.)]]
        direct=conductor.area_profile_matrices(profiles,RHO,THICKNESS)
        conductor.certificate_mode='potential'
        old=conductor.area_profile_matrix_batched(profiles,RHO,THICKNESS,batch_size=1)
        new=potential_matrix(conductor,profiles,batch_size=1)
        self.assertLess(new['maximum_equation_residual_A'],1e-8)
        self.assertGreaterEqual(np.linalg.eigvalsh(direct['upper']-new['energy']).min(),-1e-12)
        self.assertGreaterEqual(np.linalg.eigvalsh(direct['lower']-new['energy']).min(),-1e-12)
        self.assertLess(new['maximum_residual_work_allowance_ohm'],old['maximum_residual_work_allowance_ohm'])
        self.assertTrue(all(r['gauge_work_omitted_only_because_trial_coefficient_is_exact_zero'] for r in new['potential_residual_work']))


if __name__ == '__main__': unittest.main()
