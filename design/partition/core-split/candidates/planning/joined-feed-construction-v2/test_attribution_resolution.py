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

    def test_noncanonical_transpose_refused_without_changing_input(self):
        matrix=sp.diags([-np.ones(3),np.full(4,2.),-np.ones(3)],[-1,0,1],format='csc')
        self.assertFalse(matrix.has_canonical_format)
        self.assertTrue(matrix.tocsr().has_canonical_format)
        before=U.matrix_hash(matrix)
        with self.assertRaisesRegex(ValueError,'canonical transpose'):
            U.certify(matrix,{'fixture':True},{'fixture':True},reference=True)
        self.assertEqual(U.matrix_hash(matrix),before)
        sorted_matrix=matrix.copy();sorted_matrix.sort_indices()
        self.assertEqual(U.certify(sorted_matrix,{'fixture':True},{'fixture':True},reference=True)['status'],
                         'SYMMETRIC_PART_REFERENCE_SPD')

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


class FrontierStorage(unittest.TestCase):
    def certificate(self,a,border=None,work=None,frontier=True):
        return U.certify(a,{'fixture':'frontier'},{'fixture':'frontier'},work,
                         border=border,reference=True,frontier=frontier)

    def compare(self,a,border=None,work=None):
        before=U.matrix_hash(a)
        eager=self.certificate(a,border,frontier=False)
        frontier=self.certificate(a,border,work)
        for key in ('minimum_pivot_lower','inverse_infinity_upper','schur_intervals','arithmetic_updates','matrix_sha256'):
            self.assertEqual(eager[key],frontier[key],key)
        self.assertEqual(U.matrix_hash(a),before)
        self.assertEqual(frontier['storage'],U.FRONTIER_STORAGE)
        return eager,frontier

    def test_bordered_skew_equivalence_and_unchanged_input(self):
        rng=np.random.default_rng(71054)
        for n in range(2,10):
            for trial in range(4):
                edges=np.triu(rng.integers(-3,4,(n,n)),1);sym=edges+edges.T
                skew=rng.integers(-5,6,(n,n));skew=skew-skew.T
                a=sp.csc_matrix(sym+np.diag(2+np.abs(sym).sum(axis=1))+skew,dtype=float)
                b=rng.integers(-2,3,(n,2)).astype(float);d=np.diag([100.,100.])
                self.compare(a,(b,d))

    def test_chain_total_exceeds_cap_while_counted_live_frontier_fits(self):
        n=40;a=sp.diags([-np.ones(n-1),np.full(n,2.),-np.ones(n-1)],[-1,0,1],format='csc')
        a.sort_indices();b=np.zeros((n,1));b[-1]=-1;d=np.ones((1,1))
        with self.assertRaisesRegex(ValueError,'sparse fill cap'):
            self.certificate(a,(b,d),U.Work(max_entries=48),frontier=False)
        eager,frontier=self.compare(a,(b,d),U.Work(max_entries=42))
        self.assertEqual(eager['peak_sparse_entries'],82)
        self.assertEqual(frontier['peak_sparse_entries'],42)
        with self.assertRaisesRegex(ValueError,'entries=42, maximum=41'):
            self.certificate(a,(b,d),U.Work(max_entries=41))

    def test_actual_live_rows_and_factors_include_disconnected_pivot_aliases(self):
        actual_peak=0
        def observe(frame,event,arg):
            nonlocal actual_peak
            if event=='line' and frame.f_code is U._eliminate_frontier.__code__ and 'count' in frame.f_locals:
                local=frame.f_locals;rows={}
                for key in ('row','target'):
                    value=local.get(key)
                    if isinstance(value,dict):rows[id(value)]=value
                for key in ('pending','terminals'):
                    for value in local.get(key,{}).values():rows[id(value)]=value
                actual=sum(map(len,rows.values()))+sum(map(len,local.get('factors',[])))
                self.assertLessEqual(actual,local['count'])
                self.assertLessEqual(actual,local['work'].max_entries)
                actual_peak=max(actual_peak,actual)
            return observe
        a=sp.block_diag([[[2.,-1.],[-1.,2.]],[[2.,-1.],[-1.,2.]],[[1.]]],format='csc')
        a.eliminate_zeros();a.sort_indices();work=U.Work(max_entries=5)
        previous=sys.gettrace();sys.settrace(observe)
        try:self.compare(a,work=work)
        finally:sys.settrace(previous)
        self.assertEqual(actual_peak,5);self.assertEqual(work.peak_entries,5)
        dense=sp.csc_matrix(np.full((12,12),-1.)+np.eye(12)*13)
        sys.settrace(observe)
        try:
            with self.assertRaisesRegex(ValueError,'entries=41, maximum=40'):
                self.certificate(dense,work=U.Work(max_entries=40))
        finally:sys.settrace(previous)
        self.assertLessEqual(actual_peak,40)

    def test_work_budget_stays_shared_across_board_calls(self):
        a=sp.csc_matrix([[2.,-1.],[-1.,2.]])
        work=U.Work(max_updates=3)
        for expected in range(1,4):
            self.certificate(a,work=work);self.assertEqual(work.updates,expected)
        with self.assertRaisesRegex(ValueError,'arithmetic cap'):
            self.certificate(a,work=work)
        self.assertEqual(work.updates,4)

    def test_frontier_requires_reference_and_canonical_transpose(self):
        a=sp.diags([-np.ones(3),np.full(4,2.),-np.ones(3)],[-1,0,1],format='csc')
        with self.assertRaisesRegex(ValueError,'canonical transpose'):
            self.certificate(a)
        with self.assertRaisesRegex(ValueError,'explicit reference'):
            U.certify(sp.eye(2,format='csr'),{'x':1},{'x':1},frontier=True)


if __name__=='__main__':unittest.main()
