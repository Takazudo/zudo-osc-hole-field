"""A dense gauge star must not inflate every ordinary contraction row."""
import unittest
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scripts.pcbgen.residual_work import ResidualWork


class ResidualWorkTests(unittest.TestCase):
    def test_gauge_star_and_represented_operator_residual_are_enclosed(self):
        n = 4097
        weights = np.geomspace(1e-5, 1e10, n-1)
        ids = np.arange(1,n)
        matrix = coo_matrix((np.r_[weights,-weights,-weights,weights.sum()],
            (np.r_[ids,ids,np.zeros(n-1,dtype=int),0],
             np.r_[ids,np.zeros(n-1,dtype=int),ids,0])),shape=(n,n)).tocsc()
        field = np.zeros((n,2)); field[1:,0] = np.linspace(.123,.456,n-1)
        field[1:,1] = np.sin(np.arange(n-1))
        rhs = matrix@field
        bound, report = ResidualWork(matrix).one_norm(field,rhs)
        reference = matrix.astype(np.longdouble)@field.astype(np.longdouble)-rhs.astype(np.longdouble)
        self.assertTrue(np.all(np.sum(abs(reference[1:]),axis=0)<=bound))
        self.assertEqual(report['maximum_nongauge_row_operation_count'],68)
        self.assertGreater(report['gauge_row_operation_count'],8000)
        old_gamma=(64+max(np.diff(matrix.indptr)))*np.finfo(float).eps
        old=old_gamma*np.sum(abs(matrix)@abs(field),axis=0)
        self.assertTrue(np.all(bound<old/20))
        field[0,0]=1.
        with self.assertRaisesRegex(ValueError,'exactly zero'):
            ResidualWork(matrix).one_norm(field,rhs)

    def test_source_error_and_underflow_are_not_dropped(self):
        matrix=csr_matrix([[1.,0.],[0.,1e-200]])
        field=np.array([[0.],[1e-200]]); rhs=np.array([[0.],[1e-300]])
        bound,report=ResidualWork(matrix).one_norm(field,rhs,.1)
        self.assertGreaterEqual(bound[0],1.1e-300)
        self.assertGreater(report['maximum_source_roundoff_L1_A'],0.)


if __name__ == '__main__': unittest.main()
