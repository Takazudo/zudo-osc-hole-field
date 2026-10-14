"""Tiny exact ordering oracles; no original artifacts or campaign execution."""
import hashlib
import unittest
from unittest.mock import patch
from fractions import Fraction as Q

import numpy as np
import scipy.sparse as sp

import attribution_uniqueness as U
import attribution_resolution as V
from test_attribution_interval_oracle import inverse, infnorm


class Ordering(unittest.TestCase):
    def certificate(self,a,b=None,d=None,work=None):
        return U.certify(a,{'fixture':'ordering'},{'fixture':'ordering'},work,
                         border=None if b is None else (b,d),reference=True,
                         frontier=True,ordering=U.REFERENCE_ORDER)

    def test_exact_schur_inverse_and_original_bytes_preserved(self):
        h=np.array([[4,-1,0,-1],[-1,4,-1,0],[0,-1,4,-1],[-1,0,-1,4]],dtype=float)
        a=h.copy();a[0,1]+=100;a[1,0]-=100;a=sp.csr_matrix(a)
        b=np.array([[-1,0],[0,-2],[-1,0],[0,-1]],dtype=float);d=np.diag([10.,10.])
        before=(U.matrix_hash(a),b.tobytes(),d.tobytes())
        cert=self.certificate(a,b,d)
        self.assertEqual(cert['matrix_sha256'],before[0])
        self.assertEqual(before,(U.matrix_hash(a),b.tobytes(),d.tobytes()))
        exact_inv=inverse(h)
        self.assertGreaterEqual(Q(cert['inverse_infinity_upper']),infnorm(exact_inv))
        for i in range(2):
            for j in range(2):
                value=Q(d[i,j])-sum(Q(b[p,i])*exact_inv[p][q]*Q(b[q,j]) for p in range(4) for q in range(4))
                lo,hi=cert['schur_intervals'][i][j]
                self.assertLessEqual(Q(lo),value);self.assertGreaterEqual(Q(hi),value)
        ordered,border,info=U._order_reference(a,(b,d),U.Work())
        same_order=U.certify(ordered,{'x':1},{'x':1},border=border,reference=True)
        for key in ('minimum_pivot_lower','inverse_infinity_upper','schur_intervals','arithmetic_updates'):
            self.assertEqual(cert[key],same_order[key])
        self.assertEqual(cert['analysis_ordering'],info)
        self.assertIs(border[1],d)
        # Known nonidentity ordering; stale unpermuted B fails exact Schur oracle.
        p=np.array([2,3,1,0],dtype=np.int64)
        self.assertEqual(info['permutation_sha256'],hashlib.sha256(memoryview(p).cast('B')).hexdigest())
        wrong_inv=inverse(h[p][:,p])
        wrong=Q(d[0,0])-sum(Q(b[i,0])*wrong_inv[i][j]*Q(b[j,0]) for i in range(4) for j in range(4))
        right=Q(d[0,0])-sum(Q(b[i,0])*exact_inv[i][j]*Q(b[j,0]) for i in range(4) for j in range(4))
        self.assertNotEqual(wrong,right)

    def test_invalid_bijections_rejected_before_indexing(self):
        a=sp.eye(3,format='csr',dtype=float)
        for bad in (np.array([0,0,2]),np.array([-1,1,2]),np.array([0,1,3]),
                    np.array([0,1]),np.array([0.,1.,2.]),np.array([[0,1,2]])):
            with patch.object(U,'reverse_cuthill_mckee',return_value=bad):
                with self.assertRaisesRegex(ValueError,'permutation'):
                    self.certificate(a)

    def test_structural_superset_and_exact_failure_identity(self):
        a=sp.csr_matrix([[2.,100.],[-100.,2.]])
        cert=self.certificate(a)
        self.assertEqual(cert['analysis_ordering']['graph_nnz'],4)  # H itself is diagonal.
        self.assertEqual(cert['analysis_ordering']['graph'],'symmetric-original-nonzero-structural-superset')
        a=sp.csr_matrix([[2.,-1.],[-1.,2.]])
        real=U.reverse_cuthill_mckee
        with patch.object(U,'reverse_cuthill_mckee',wraps=real) as order:
            with self.assertRaisesRegex(ValueError,'arithmetic cap.*permutation_sha256') as error:
                self.certificate(a,work=U.Work(max_updates=0))
            order.assert_called_once()
        self.assertIn(U.matrix_hash(a),str(error.exception))
        self.assertLess(len(str(error.exception)),2048)

    def test_floating_kb_coupling_and_removed_wire_rejection(self):
        ka=self.certificate(sp.csr_matrix([[2.,100.],[-100.,2.]]),np.array([[-1.],[-1.]]),np.array([[2.]]))
        kb=self.certificate(sp.csr_matrix([[1.]]),np.array([[-1.]]),np.array([[1.]]))
        ka['B_infinity_upper'],ka['BT_infinity_upper']=V.matrix_norms(np.array([[-1.],[-1.]]))
        kb['B_infinity_upper'],kb['BT_infinity_upper']=V.matrix_norms(np.array([[-1.]]))
        coupled=U.certify_coupled(ka['schur_intervals'],kb['schur_intervals'],1,[True],U.Work(),reference=True)
        self.assertGreaterEqual(Q(V.network_inverse_bound({'KA':ka,'KB':kb},coupled)),Q(22556,5001))
        with self.assertRaisesRegex(ValueError,'UNRESOLVED'):
            U.certify_coupled(ka['schur_intervals'],kb['schur_intervals'],1,[False],U.Work(),reference=True)

    def test_order_can_improve_or_worsen_work_without_automatic_fallback(self):
        def compare(a):
            a=sp.csr_matrix(a,dtype=float);b=np.zeros((a.shape[0],1));b[-1]=-1;d=np.array([[2.]])
            natural=U.certify(a,{'x':1},{'x':1},border=(b,d),reference=True,frontier=True)
            ordered=self.certificate(a,b,d)
            return natural['arithmetic_updates'],ordered['arithmetic_updates']
        n=25;edge=np.zeros((n,n));edge[0,1:]=edge[1:,0]=-1
        self.assertEqual(compare(edge+np.diag(1+np.abs(edge).sum(axis=1))),(2601,29))
        q=sp.diags([-np.ones(4),np.full(5,2.),-np.ones(4)],[-1,0,1],format='csr')
        self.assertEqual(compare(sp.kron(sp.eye(5),q)+sp.kron(q,sp.eye(5))),(295,345))
        # Disconnected structure is also a complete validated permutation.
        a=sp.block_diag([[[2.,-1.],[-1.,2.]],[[3.]]],format='csr')
        a.sort_indices();self.certificate(a)


if __name__=='__main__':unittest.main()
