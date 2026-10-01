"""Spatial material variation preserves matrix bounds, not entrywise ordering."""
import unittest
from fractions import Fraction
import numpy as np
from scripts.pcbgen.conductivity_envelope import fixed_geometry_bracket


class ConductivityEnvelopeTests(unittest.TestCase):
    def test_float32_scalar_ratios_enclose_exact_represented_inputs(self):
        reference,minimum,maximum=map(np.float32,(.9,.7,1.3))
        original=np.array([[1.1]],dtype=np.float32)
        lower,upper=fixed_geometry_bracket(original,original,reference,minimum,maximum)
        exact=lambda value:Fraction(float(value))
        self.assertLessEqual(exact(lower[0,0]),exact(original[0,0])*exact(minimum)/exact(reference))
        self.assertGreaterEqual(exact(upper[0,0]),exact(original[0,0])*exact(maximum)/exact(reference))

    def test_float32_input_is_widened_before_outward_scaling(self):
        original=np.array([[1.1]],dtype=np.float32)
        lower,upper=fixed_geometry_bracket(original,original,1.,.7,1.3)
        exact=np.longdouble(original[0,0])
        self.assertEqual(lower.dtype,np.float64)
        self.assertEqual(upper.dtype,np.float64)
        self.assertLessEqual(np.longdouble(lower[0,0]),np.longdouble(.7)*exact)
        self.assertGreaterEqual(np.longdouble(upper[0,0]),np.longdouble(1.3)*exact)

    def test_nonuniform_edge_materials_inside_same_geometry_bracket(self):
        rng=np.random.default_rng(38);n=9
        edges=[(i,i+1) for i in range(n-1)]+[(0,4),(2,7),(1,6)]
        D=np.zeros((n,len(edges)))
        for j,(a,b) in enumerate(edges):D[a,j]=1;D[b,j]=-1
        D=D[1:];B=rng.normal(size=(n-1,4));base=10**rng.uniform(-1,1,len(edges))
        K=(D/base)@D.T;R=B.T@np.linalg.solve(K,B)
        lower,upper=fixed_geometry_bracket(R,R,1.,.5,1.7)
        for _ in range(20):
            rho=rng.uniform(.5,1.7,len(edges));actual=(D/(base*rho))@D.T
            Z=B.T@np.linalg.solve(actual,B)
            self.assertGreater(np.linalg.eigvalsh(Z-lower).min(),-1e-11)
            self.assertGreater(np.linalg.eigvalsh(upper-Z).min(),-1e-11)


if __name__=='__main__':unittest.main()
