"""Correction-energy envelope including asymmetric rounding and cancellation."""
import unittest
import numpy as np
from scripts.pcbgen.positive_energy_bound import row_envelope,diagonal_energy,positive_quadratic_energy


class PositiveEnergyTests(unittest.TestCase):
    def test_optimized_contraction_cannot_underflow_bounds_before_large_mass(self):
        matrix=np.array([[np.longdouble('1e300')]])
        bounds=np.array([[np.longdouble('1e-200')]])
        upper=positive_quadratic_energy(matrix,bounds)
        exact=matrix[0,0]*bounds[0,0]**2
        self.assertGreaterEqual(np.longdouble(upper[0]),exact)
        self.assertLess(np.longdouble(upper[0])/exact,1+1e-12)

    def test_first_stage_underflow_is_charged_after_large_later_multiplier(self):
        matrix=np.array([[0,np.longdouble('1e-300')],[np.longdouble('1e-300'),0]])
        bounds=np.array([[np.longdouble('1e200')],[np.longdouble('1e-200')]])
        upper=positive_quadratic_energy(matrix,bounds)
        exact=2*matrix[0,1]*bounds[0,0]*bounds[1,0]
        self.assertGreaterEqual(np.longdouble(upper[0]),exact)

    def test_fast_positive_quadratic_encloses_extended_precision(self):
        rng=np.random.default_rng(381)
        for shape in ((32,32),(71,3,3)):
            matrix=rng.normal(size=shape).astype(np.longdouble)
            matrix*=np.longdouble(1)+np.finfo(np.longdouble).eps*7
            bounds=(10**rng.uniform(-15,-5,size=shape[:-1]+(8,))).astype(np.longdouble)
            upper=positive_quadratic_energy(matrix,bounds)
            m=matrix.reshape(-1,shape[-1],shape[-1]);b=bounds.reshape(-1,shape[-1],8)
            exact=np.einsum('tib,tij,tjb->b',b,abs(m),b)
            self.assertTrue(np.all(upper>=exact))
            self.assertLess(np.max(upper/exact),1+1e-10)

    def test_fast_positive_quadratic_covers_underflow(self):
        matrix=np.array([[1e-300]],dtype=np.longdouble)
        bounds=np.array([[1e-30]],dtype=np.longdouble)
        upper=positive_quadratic_energy(matrix,bounds)
        self.assertGreaterEqual(np.longdouble(upper[0]),matrix[0,0]*bounds[0,0]**2)

    def test_nonuniform_intervals_enclose_full_quadratic(self):
        rng=np.random.default_rng(38)
        matrices=rng.normal(size=(37,7,7))
        # Deliberately asymmetric: the helper must not rely on stored symmetry.
        bounds=10**rng.uniform(-15,-4,size=(37,7,11))
        field=bounds*rng.uniform(-1,1,size=bounds.shape)
        exact=np.einsum('tib,tij,tjb->b',field.astype(np.longdouble),matrices.astype(np.longdouble),field.astype(np.longdouble))
        original_absolute=np.einsum('tib,tij,tjb->b',bounds.astype(np.longdouble),abs(matrices).astype(np.longdouble),bounds.astype(np.longdouble))
        upper=diagonal_energy(row_envelope(matrices),bounds)
        self.assertTrue(np.all(upper>=exact));self.assertTrue(np.all(upper>=original_absolute))

    def test_bound_does_not_lose_opposite_sign_cancellation(self):
        matrix=np.array([[1.,-1.],[-1.,1.]])
        bounds=np.ones((2,2));field=np.array([[1.,1.],[1.,-1.]])
        upper=diagonal_energy(row_envelope(matrix),bounds)
        exact=np.diag(field.T@matrix@field)
        self.assertEqual(exact[0],0);self.assertEqual(exact[1],4)
        self.assertTrue(np.all(upper>=exact));self.assertTrue(np.all(upper>=4))


if __name__=='__main__':unittest.main()
