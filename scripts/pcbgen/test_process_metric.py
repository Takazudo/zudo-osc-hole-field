"""Positive mapped-stack current/potential energy envelopes."""
import unittest
import numpy as np
from scripts.pcbgen.process_metric import cylindrical_bounds,depth_scales


class ProcessMetricTests(unittest.TestCase):
    def test_nominal_map_and_all_interval_corners(self):
        r,t,p=.165,4.,2.06435e-5
        current,potential=cylindrical_bounds((r,r),(t,t),(1,1),(1,1),(p,p))
        np.testing.assert_allclose(current,p*np.array([r*t,1/(r*t),1/(r*t)]))
        np.testing.assert_allclose(potential,np.array([1/(r*t),r*t,r*t])/p)
        bounds=((.15,.19),(3.8,4.2),(.9,1.3),(.8,1.25),(1.95e-5,2.15e-5))
        upper_j,upper_v=cylindrical_bounds(*bounds)
        import itertools
        for r,t,q,s,p in itertools.product(*bounds):
            exact_j=p*np.array([r*t/(q*s),q/(r*t*s),s/(r*t*q)])
            exact_v=np.array([q*s/(r*t),r*t*s/q,r*t*q/s])/p
            self.assertTrue(np.all(exact_j<=upper_j));self.assertTrue(np.all(exact_v<=upper_v))

    def test_depth_partition_retains_positive_foil_and_dielectric_traces(self):
        reference=[0,.07,1.2,1.34,1.4,1.47,1.53,1.6]
        lengths=[(.07,.085),(1.10,1.16),(.14,.17),(.055,.065),(.07,.085),(.055,.065),(.07,.085)]
        scales=depth_scales(reference,lengths)
        self.assertEqual(len(scales),7)
        for (lo,hi),step,(a,b) in zip(scales,np.diff(reference),lengths):
            self.assertAlmostEqual(lo*step,a);self.assertAlmostEqual(hi*step,b)
        with self.assertRaises(ValueError):depth_scales([0,.1,.1],[(.1,.1),(.1,.1)])


if __name__=='__main__':unittest.main()
