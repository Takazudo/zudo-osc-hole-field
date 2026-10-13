"""Small analytic cancellation regression; not a production geometry reproduction."""
import ast
from pathlib import Path
import unittest
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# Load only the numerical helpers: this regression requires no geometry, native
# tools, mesh construction, large board operators, or production solver command.
source=Path(__file__).with_name('finite_solve.py')
tree=ast.parse(source.read_text())
helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_extended_residual','refined_solve','reconstruct_potential')]
def need(condition,message):
 if not condition:raise ValueError(message)
ns={'np':np,'REFINE_STEPS':3,'need':need}
exec(compile(ast.Module(body=helpers,type_ignores=[]),str(source),'exec'),ns)

class Refinement(unittest.TestCase):
 def test_load_accumulator_retains_corrections_below_float64_spacing(self):
  A,_,lu=self.fixture();b=np.array([0.,2.3e-6])
  old,res=ns['refined_solve'](lu,A,b)
  self.assertGreater(res,1e-9)
  x,res=ns['refined_solve'](lu,A,b,extended_solution=True)
  self.assertEqual(x.dtype,np.dtype(np.longdouble));self.assertLess(res,1e-9)
  current=np.longdouble(1e8)*(x[1]-x[0])
  independent=np.array([x[0]-current,current-np.longdouble(b[1])])
  self.assertLess(float(np.max(abs(independent))/b[1]),1e-9)
  red={'N':3,'free':np.array([0,1]),'u0':x,'Y':np.zeros((2,1))}
  rebuilt=ns['reconstruct_potential'](red,np.zeros(1))
  self.assertEqual(rebuilt.dtype,x.dtype);np.testing.assert_array_equal(rebuilt[:2],x)
  self.assertEqual(rebuilt[2],0)
  current=np.longdouble(1e8)*(rebuilt[1]-rebuilt[0])
  self.assertLess(float(max(abs(rebuilt[0]-current),abs(current-b[1]))/b[1]),1e-9)
  with self.assertRaises(ValueError):ns['refined_solve'](lu,A,np.column_stack([b,b]),extended_solution=True)

 def fixture(self):
  # 1 S to ground at node 0, 1e8 S between nodes 0 and 1;
  # inject 10 uA at node 1. Exact voltages are I and I*(1+1e-8).
  A=sp.csc_matrix([[100000001.,-100000000.],[-100000000.,100000000.]])
  b=np.array([0.,1e-5]);return A,b,spla.splu(A)
 def test_analytic_cancellation_without_relaxing_threshold(self):
  A,b,lu=self.fixture();old=lu.solve(b)
  for _ in range(3):old+=lu.solve(b-A@old)
  self.assertGreater(np.max(abs(b-A@old))/np.max(abs(b)),1e-9)
  x,res=ns['refined_solve'](lu,A,b)
  self.assertLess(res,1e-9)
  # Independent two-node branch equations, no sparse matvec or helper reuse.
  z=x.astype(np.longdouble);g=np.longdouble(100000000)
  current=g*(z[1]-z[0]);r=np.array([z[0]-current,current-np.longdouble(b[1])])
  self.assertLess(float(np.max(abs(r))/abs(b[1])),1e-9)
  np.testing.assert_allclose(x,[1e-5,1e-5*(1+1e-8)],rtol=1e-9,atol=0.)
 def test_multi_rhs_and_csr_use_same_equations(self):
  A,b,lu=self.fixture();B=np.column_stack([b,-b,2*b])
  x,res=ns['refined_solve'](lu,A,B)
  self.assertLess(res,1e-9)
  np.testing.assert_allclose(x[:,1],-x[:,0],rtol=1e-12,atol=0.)
  np.testing.assert_allclose(x[:,2],2*x[:,0],rtol=1e-12,atol=0.)
  np.testing.assert_allclose(ns['_extended_residual'](A,x,B),ns['_extended_residual'](A.tocsr(),x,B),rtol=0.,atol=1e-15)
 def test_zero_rhs_remains_zero(self):
  A,b,lu=self.fixture();x,res=ns['refined_solve'](lu,A,b*0)
  np.testing.assert_array_equal(x,np.zeros(2));self.assertEqual(res,0.)

if __name__=='__main__':unittest.main()
