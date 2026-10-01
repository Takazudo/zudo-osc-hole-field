"""Conserved tree routing and its long-double summation enclosure."""
from fractions import Fraction
import unittest
import numpy as np
from scipy.sparse import coo_matrix
from scripts.pcbgen.conserved_flow import FlowForest


class ConservedFlowTests(unittest.TestCase):
    def test_forest_routes_components_with_opposite_shared_face_currents(self):
        edges=[(0,1),(1,2),(0,2),(3,4),(0,1)]
        D=coo_matrix(([v for e in edges for v in (1.,-1.)],
            ([n for e in edges for n in e],np.repeat(np.arange(len(edges)),2))),shape=(5,len(edges))).tocsc()
        tree=FlowForest(D)
        source=np.array([[1.,.2],[-.3,-.2],[-.7,0.],[.25,.125],[-.25,-.125]])
        current,error,imbalance=tree.route(source,input_absolute_error=1e-16)
        np.testing.assert_allclose(D@current,source,atol=2e-16)
        self.assertLess(float(abs(imbalance).max()),1e-15)
        with self.assertRaisesRegex(ValueError,'not balanced'):
            tree.route(source+np.array([[0.],[0.],[0.],[.1],[0.]]))

    def test_subtree_interval_contains_exact_binary_rational_sum(self):
        n=300
        D=coo_matrix((np.tile([1.,-1.],n-1),
            (np.column_stack((np.arange(n-1),np.arange(1,n))).ravel(),np.repeat(np.arange(n-1),2))),shape=(n,n-1)).tocsc()
        source=np.zeros(n);source[1::2]=1e-8;source[2::2]=-1e-8;source[0]=-float(source.sum())
        tree=FlowForest(D);flow,bound,_=tree.route(source,input_absolute_error=1e-18)
        for edge in (0,1,149,298):
            exact=-sum((Fraction(float(v)) for v in source[edge+1:]),Fraction())
            error=abs(Fraction(str(flow[edge,0]))-exact)
            self.assertLessEqual(float(error),float(bound[0]))


if __name__=='__main__':unittest.main()
