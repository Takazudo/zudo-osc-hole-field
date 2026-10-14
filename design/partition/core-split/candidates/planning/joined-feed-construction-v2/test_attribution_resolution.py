"""Analytic enclosures for the selected-field robustness gate, source only."""
import unittest
from fractions import Fraction

import numpy as np
import scipy.sparse as sp

import attribution_resolution as V
import attribution_uniqueness as U
from attribution_transport import Budget


class Resolution(unittest.TestCase):
    def test_inverse_norm_bound_for_known_integer_matrix(self):
        matrix=sp.csr_matrix([[2.,1.],[1.,2.]])
        cert=U.certify(matrix,{'fixture':True},{'fixture':True})
        # Exact inverse [[2,-1],[-1,2]]/3 has infinity norm 1.
        self.assertGreaterEqual(cert['inverse_infinity_upper'],1.)

    def test_residual_outward_encloses_exact_fraction(self):
        a=sp.csr_matrix([[3.,-1.],[-1.,2.]])
        x=np.array([np.longdouble('0.40000000000000001'),np.longdouble('.2')])
        b=np.zeros((2,1));d=np.ones((1,1));t=np.array([0.]);f=np.array([1.,0.])
        bound=V.residual_bound(a,b,d,x,t,f,[U.ZERO],Budget())
        exact=[Fraction.from_float(float(f[i]))-sum(Fraction.from_float(float(a[i,j]))*Fraction(str(x[j])) for j in range(2)) for i in range(2)]
        self.assertGreaterEqual(bound,float(max(map(abs,exact))))

    def test_field_energy_interval_contains_analytic_extremes(self):
        m=sp.csr_matrix([[1.,-1.],[-1.,1.]])
        field=np.array([0.,1.]);nodes=np.array([0,1]);fixed=np.array([True,False])
        lo,hi=V.energy_interval(m,nodes,field,.01,fixed,Budget())
        self.assertLessEqual(lo,.99**2)
        self.assertGreaterEqual(hi,1.01**2)

    def test_held_reaction_interval_contains_analytic_extremes(self):
        m=sp.csr_matrix([[1.,-1.],[-1.,1.]])
        lo,hi=V.reaction_interval(m,np.array([0]),np.array([0.,1.]),.01,np.array([True,False]),[],np.array([]),1.,Budget())
        self.assertLessEqual(lo,-1.01)
        self.assertGreaterEqual(hi,-.99)

    def test_screen_supported_rejected_and_overlap(self):
        self.assertEqual(V.screen((.2,.21),(1.,1.01),(-1.,-.9))['status'],'SUPPORTED')
        self.assertEqual(V.screen((.01,.02),(1.,1.01),(-1.,-.9))['status'],'REJECTED')
        self.assertEqual(V.screen((.09,.11),(1.,1.01),(-1.,-.9))['status'],'INCONCLUSIVE')
        self.assertEqual(V.screen((.2,.21),(1.,1.01),(-.1,.1))['status'],'INCONCLUSIVE')
        self.assertEqual(V.screen((.2,.21),(-1.,1.),(-1.,-.9))['status'],'INCONCLUSIVE')

    def test_nonfinite_resolution_refused(self):
        with self.assertRaises(ValueError):V.pair(np.inf)
        with self.assertRaises(ValueError):U.upper_mul(1e300,1e300)


if __name__=='__main__':unittest.main()
