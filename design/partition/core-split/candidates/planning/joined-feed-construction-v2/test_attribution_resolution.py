"""Analytic enclosures for the selected-field robustness gate, source only."""
import unittest
import math
import sys
from unittest.mock import patch
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


class ReferenceCoercivity(unittest.TestCase):
    def certify(self,a,b=None,d=None,work=None):
        a=sp.csr_matrix(a,dtype=float);before=U.matrix_hash(a)
        cert=U.certify(a,{'fixture':'reference'},{'fixture':'reference'},work,
                       border=None if b is None else (np.array(b,dtype=float),np.array(d,dtype=float)),reference=True)
        self.assertEqual(U.matrix_hash(a),before)
        self.assertEqual(cert['status'],'SYMMETRIC_PART_REFERENCE_SPD')
        self.assertTrue(cert['analysis_reference_only'])
        return cert

    def test_half_sum_outward_extremes_and_subnormals(self):
        tiny=math.ulp(0.);big=sys.float_info.max
        values=[0.,tiny,-tiny,2*tiny,-2*tiny,1.,-1.,big,-big,math.nextafter(big,0),100.,-100.]
        for a in values:
            for b in values:
                lo,hi=U.average_enclosure(a,b)
                exact=(Fraction.from_float(a)+Fraction.from_float(b))/2
                self.assertTrue(math.isfinite(lo) and math.isfinite(hi))
                self.assertLessEqual(Fraction.from_float(lo),exact);self.assertGreaterEqual(Fraction.from_float(hi),exact)
        for x in (math.inf,math.nan):
            with self.assertRaises(ValueError):U.average_enclosure(x,0.)

    def test_large_skew_coercivity_uses_exact_average_not_sampled_smallness(self):
        cert=self.certify([[2,100],[-100,2]],work=U.Work(max_entries=2))
        self.assertGreaterEqual(cert['inverse_infinity_upper'],.5)
        self.certify([[2,1],[0,2]])  # Missing transpose entry means an exact zero.
        for bad in ([[1,2],[-2,-1]],[[0,1],[-1,0]]):
            with self.assertRaisesRegex(ValueError,'UNRESOLVED'):self.certify(bad)

    def test_reference_preflight_refuses_before_midpoint_rows_or_elimination(self):
        with patch.object(U,'average_enclosure') as average,patch.object(U,'_eliminate') as eliminate:
            with self.assertRaisesRegex(ValueError,'sparse fill cap'):
                self.certify([[2,1],[0,2]],work=U.Work(max_entries=1))
        average.assert_not_called();eliminate.assert_not_called()
        with self.assertRaisesRegex(ValueError,'sparse fill cap'):
            self.certify([[2]],b=[[-1]],d=[[1]],work=U.Work(max_entries=1))

    def test_full_joined_reference_counts_all_variables_once_and_rejects_disconnect(self):
        work=U.Work()
        ka=self.certify([[2,100],[-100,2]],b=[[-1],[-1]],d=[[2]],work=work)
        kb=self.certify([[1]],b=[[-1]],d=[[1]],work=work)
        ka['B_infinity_upper'],ka['BT_infinity_upper']=V.matrix_norms(np.array([[-1.],[-1.]]))
        kb['B_infinity_upper'],kb['BT_infinity_upper']=V.matrix_norms(np.array([[-1.]]))
        coupled=U.certify_coupled(ka['schur_intervals'],kb['schur_intervals'],1,[True],work,reference=True)
        bound=V.network_inverse_bound({'KA':ka,'KB':kb},coupled)
        # Independent Fraction oracle: original M inverse infinity =22556/5001;
        # reference H inverse infinity=7, block formula=12, global ceil(sqrt5)=3.
        self.assertGreaterEqual(Fraction.from_float(bound),Fraction(22556,5001))
        originals={k:dict(v,analysis_reference_only=False) for k,v in {'KA':ka,'KB':kb}.items()}
        original_coupled=dict(coupled,analysis_reference_only=False)
        reference_block=V.network_inverse_bound(originals,original_coupled)
        self.assertGreaterEqual(bound,reference_block*3)
        self.assertLess(bound,reference_block*3.000001)
        with self.assertRaisesRegex(ValueError,'mixed'):
            V.network_inverse_bound(originals,coupled)
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'):
            U.certify_coupled(ka['schur_intervals'],kb['schur_intervals'],1,[False],U.Work(),reference=True)


if __name__=='__main__':unittest.main()
