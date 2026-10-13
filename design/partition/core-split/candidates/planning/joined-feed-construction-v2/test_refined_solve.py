"""Small analytic cancellation regression; not a production geometry reproduction."""
import ast
import pickle
from pathlib import Path
import unittest
import weakref
from unittest.mock import patch
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.sparse import _sparsetools

# Load only the numerical helpers: this regression requires no geometry, native
# tools, mesh construction, large board operators, or production solver command.
source=Path(__file__).with_name('finite_solve.py')
tree=ast.parse(source.read_text())
helpers=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_extended_residual','_refined_accumulator','refined_solve','refined_projection','refined_interface_solve','reconstruct_potential')]
def need(condition,message):
 if not condition:raise ValueError(message)
ns={'np':np,'REFINE_STEPS':3,'need':need}
exec(compile(ast.Module(body=helpers,type_ignores=[]),str(source),'exec'),ns)

class Refinement(unittest.TestCase):
 def test_invalid_interface_residual_cannot_be_hidden_by_maximum(self):
  A,b,lu=self.fixture()
  for invalid in (float('nan'),float('inf'),-1.):
   with self.subTest(invalid=invalid),patch.dict(ns,{'refined_solve':lambda *args,**kw:(np.zeros(2),invalid)}):
    with self.assertRaisesRegex(ValueError,'invalid interface residual'):
     ns['refined_interface_solve'](lu,A,b[:,None])

 def test_interface_basis_preserves_load_relative_coupled_kcl(self):
  # A source shunt and a terminal shunt, joined by a highly conductive edge.
  # Long-double u0 alone cannot preserve the float64 terminal response.
  A=sp.csc_matrix([[100000001.,-100000000.],[-100000000.,100000001.]])
  lu=spla.splu(A);B=np.array([[0.],[-1.]]);load=np.array([2.3e-6,0.]);vt=np.array([1.7e-5])
  u0,_=ns['refined_solve'](lu,A,load,extended_solution=True)
  old,_=ns['refined_solve'](lu,A,B)
  Y,res=ns['refined_interface_solve'](lu,A,B)
  self.assertEqual(Y.dtype,np.dtype(np.longdouble));self.assertLess(res,1e-9)
  # Use independently written branch-current equations, not the residual helper.
  def branch_residual(basis):
   red={'N':3,'free':np.array([0,1]),'u0':u0,'Y':basis}
   vm=ns['reconstruct_potential'](red,vt);self.assertEqual(vm[2],0)
   link=np.longdouble(1e8)*(vm[0]-vm[1])
   residual=[vm[0]+link-np.longdouble(load[0]),vm[1]-link-np.longdouble(vt[0])]
   return float(max(abs(x) for x in residual)/max(abs(load)))
  self.assertGreater(branch_residual(old),1e-9)
  self.assertLess(branch_residual(Y),1e-9)
  restored=pickle.loads(pickle.dumps(Y))
  self.assertEqual(restored.dtype,Y.dtype);np.testing.assert_array_equal(restored,Y)
  self.assertLess(branch_residual(restored),1e-9)

 def test_interface_columns_use_original_global_residual_normalization(self):
  A,b,lu=self.fixture();B=np.column_stack([b,-3*b,b*0])
  Y,reported=ns['refined_interface_solve'](lu,A,B)
  self.assertEqual(Y.dtype,np.dtype(np.longdouble))
  # Compare each column against the analytic shunt/edge solution at the declared
  # numerical tolerance; separately rounded RHS columns need not scale bitwise.
  expected=np.vstack([B[1],B[1]*(1+1e-8)])
  np.testing.assert_allclose(Y,expected,rtol=1e-9,atol=0.)
  np.testing.assert_array_equal(Y[:,2],np.zeros(2))
  measured=float(np.max(abs(ns['_extended_residual'](A,Y,B))))/float(np.max(abs(B)))
  self.assertAlmostEqual(reported,measured,delta=1e-24)
  empty,res=ns['refined_interface_solve'](lu,A,np.empty((2,0)))
  self.assertEqual(empty.shape,(2,0));self.assertEqual(res,0.)

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
  self.assertEqual(x.dtype,np.dtype(np.float64),'ordinary multi-RHS solves must remain float64')
  self.assertLess(res,1e-9)
  np.testing.assert_allclose(x[:,1],-x[:,0],rtol=1e-12,atol=0.)
  np.testing.assert_allclose(x[:,2],2*x[:,0],rtol=1e-12,atol=0.)
  np.testing.assert_allclose(ns['_extended_residual'](A,x,B),ns['_extended_residual'](A.tocsr(),x,B),rtol=0.,atol=1e-15)
 def test_zero_rhs_remains_zero(self):
  A,b,lu=self.fixture();x,res=ns['refined_solve'](lu,A,b*0)
  np.testing.assert_array_equal(x,np.zeros(2));self.assertEqual(res,0.)

class ExtendedResidualKernel(unittest.TestCase):
 @staticmethod
 def original_scatter(A,x,b):
  # Retained pre-optimization arithmetic, independent of the compiled kernel.
  xx=np.asarray(x);bb=np.asarray(b);vector=bb.ndim==1
  if vector:xx=xx[:,None];bb=bb[:,None]
  result=np.empty(bb.shape,dtype=np.float64)
  for j in range(bb.shape[1]):
   rr=bb[:,j].astype(np.longdouble)
   for lo in range(0,len(A.data),65536):
    hi=min(lo+65536,len(A.data))
    major=np.searchsorted(A.indptr,np.arange(lo,hi),side='right')-1
    row,col=(A.indices[lo:hi],major) if A.format=='csc' else (major,A.indices[lo:hi])
    product=A.data[lo:hi].astype(np.longdouble)*xx[col,j].astype(np.longdouble)
    np.add.at(rr,row,-product)
   result[:,j]=rr
  return result[:,0] if vector else result

 def assert_equivalent(self,A,x,b):
  before=[v.copy() for v in (A.data,A.indices,A.indptr,x,b)]
  with np.errstate(invalid='ignore',over='ignore'):
   expected=self.original_scatter(A,x,b);actual=ns['_extended_residual'](A,x,b)
  self.assertEqual(actual.dtype,np.dtype(np.float64))
  np.testing.assert_array_equal(actual,expected)
  finite=np.isfinite(expected)
  self.assertEqual(actual[finite].tobytes(),expected[finite].tobytes(),'finite/signed-zero bytes differ')
  for old,current in zip(before,(A.data,A.indices,A.indptr,x,b)):
   np.testing.assert_array_equal(old,current)

 def test_cancellation_and_stored_duplicate_order(self):
  A=sp.csc_matrix([[100000001.,-100000000.],[-100000000.,100000000.]])
  x=np.array([[1,1],[1+np.longdouble(1)/1e8,1+np.longdouble(3)/1e8]],dtype=np.longdouble)
  self.assert_equivalent(A,x,np.array([[0.,-2.],[1.,3.]]))
  # Grouping all products first would give -2 instead of the original -3.
  A=sp.csc_matrix((np.array([1e20,-1e20,3.]),np.array([0,0,0]),np.array([0,3])),shape=(1,1))
  self.assert_equivalent(A,np.ones(1,dtype=np.longdouble),np.ones(1))
  self.assertEqual(ns['_extended_residual'](A,np.ones(1),np.ones(1))[0],-3.)

 def test_unsorted_rows_vector_and_matrix_inputs(self):
  A=sp.csc_matrix((np.array([3.,1.,2.,-4.]),np.array([1,0,1,0]),np.array([0,3,4])),shape=(2,2))
  for dtype in (np.float64,np.longdouble):
   for width in (1,3,8):
    with self.subTest(dtype=dtype,width=width):
     x=np.arange(2*width,dtype=dtype).reshape(2,width)/7;b=np.ones((2,width))*1e-8
     self.assert_equivalent(A,x,b)
     self.assert_equivalent(A,x[:,0],b[:,0])

 def test_signed_zeros_and_nonfinite_propagation(self):
  for zero in (0.,-0.):
   A=sp.csc_matrix((np.array([zero,-zero,3.,-2.]),np.array([1,0,1,0]),np.array([0,2,4])),shape=(2,2))
   self.assert_equivalent(A,np.array([zero,-zero],dtype=np.longdouble),np.array([-zero,zero]))
  for value,x in ((np.inf,0.),(np.nan,0.),(1.,np.nan),(1.,np.inf),(0.,np.inf)):
   with self.subTest(value=value,x=x):
    A=sp.csc_matrix(([value],([0],[0])),shape=(1,1))
    self.assert_equivalent(A,np.array([x],dtype=np.longdouble),np.ones(1))

 def test_split_column_and_empty_column_spans_are_bounded(self):
  matrices=[sp.csc_matrix((np.ones(70001),(np.arange(70001),np.zeros(70001,dtype=int))),shape=(70001,1)),
            sp.csc_matrix(([2.,-3.],([0,2],[0,70000])),shape=(3,70002))]
  for A in matrices:
   calls=[];kernel=_sparsetools.csc_matvec
   def checked(rows,cols,ptr,indices,data,values,rr):
    self.assertLessEqual(len(data),65536);self.assertLessEqual(cols,65536);self.assertLessEqual(len(ptr),65537)
    self.assertTrue(np.shares_memory(indices,A.indices))
    for array in (data,values,rr):self.assertEqual(array.dtype,np.dtype(np.longdouble))
    calls.append(rr.ctypes.data)
    return kernel(rows,cols,ptr,indices,data,values,rr)
   with patch.object(_sparsetools,'csc_matvec',checked):
    self.assert_equivalent(A,np.ones(A.shape[1],dtype=np.longdouble)*np.longdouble('.123456789123456789'),np.ones(A.shape[0]))
   self.assertEqual(len(calls),2);self.assertEqual(len(set(calls)),1,'multiple extended output vectors allocated')

 def test_csr_keeps_original_path_and_empty_matrix_is_supported(self):
  A=sp.csr_matrix([[3.,-2.,0.],[0.,7.,1.]])
  with patch.object(_sparsetools,'csc_matvec',side_effect=AssertionError('CSR must not use CSC kernel')):
   self.assert_equivalent(A,np.arange(6,dtype=np.longdouble).reshape(3,2),np.ones((2,2)))
  self.assert_equivalent(sp.csc_matrix((4,5)),np.zeros((5,2)),np.zeros((4,2)))

 def test_csc_boundary_queries_preserve_index_dtype(self):
  # A scalar int64 query makes NumPy copy the entire int32 index array on
  # every search. Require matching query types without timing-dependent tests.
  for index_type in (np.int32,np.int64):
   with self.subTest(index_type=index_type):
    A=sp.csc_matrix([[3.,-2.],[0.,7.]])
    A.indices=A.indices.astype(index_type);A.indptr=A.indptr.astype(index_type)
    x=np.array([.2,.3],dtype=np.longdouble);b=np.array([.1,.2])
    expected=self.original_scatter(A,x,b);search=np.searchsorted;calls=[]
    def checked(array,value,*args,**kwargs):
     self.assertIs(array,A.indptr)
     self.assertEqual(np.asarray(value).ndim,0)
     self.assertEqual(np.asarray(value).dtype,array.dtype)
     calls.append(int(value));return search(array,value,*args,**kwargs)
    with patch.object(np,'searchsorted',checked):actual=ns['_extended_residual'](A,x,b)
    self.assertEqual(calls,[0,A.nnz-1]);np.testing.assert_array_equal(actual,expected)

class DrivingPointProjection(unittest.TestCase):
 def fixture(self):
  A=sp.csc_matrix([[100000001.,-100000000.],[-100000000.,100000000.]])
  W=np.array([[j/16 for j in range(16)],[1-j/16 for j in range(16)]])
  B=np.array([[-1.],[0.]])
  lu=spla.splu(A,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0.,options=dict(SymmetricMode=True))
  return A,W,B,lu

 def test_rounding_node_vectors_fails_but_extended_projection_matches_analytic(self):
  A,W,B,lu=self.fixture();_,old=ns['refined_solve'](lu,A,W)
  self.assertGreater(old,1e-9)
  measured=[];original=ns['_refined_accumulator']
  def checked(*args,**kwargs):
   U,res=original(*args,**kwargs);rhs=args[2]
   flow=np.longdouble(1e8)*(U[0]-U[1])
   residual=np.vstack([rhs[0]-U[0]-flow,rhs[1]+flow])
   measured.append(float(np.max(abs(residual))))
   return U,res
  with patch.dict(ns,{'_refined_accumulator':checked}):e,q,res=ns['refined_projection'](lu,A,W,B)
  self.assertLess(res,1e-9);self.assertLess(max(measured)/np.max(abs(W)),1e-9)
  self.assertEqual(e.dtype,np.dtype(np.float64));self.assertEqual(q.dtype,np.dtype(np.float64))
  np.testing.assert_allclose(e,1+W[1]**2/1e8,rtol=1e-9,atol=0.)
  np.testing.assert_allclose(q,-np.ones((1,16)),rtol=1e-9,atol=0.)

 def test_eight_column_bound_release_and_three_corrections(self):
  A,W,B,lu=self.fixture();original=ns['_refined_accumulator'];previous=[];widths=[]
  class CountLU:
   calls=0
   def solve(self,b):
    self.calls+=1;return lu.solve(b)
  counted=CountLU()
  def checked(*args,**kwargs):
   if previous:self.assertIsNone(previous[-1]())
   U,res=original(*args,**kwargs);previous.append(weakref.ref(U));widths.append(U.shape[1])
   self.assertLessEqual(U.shape[1]*U.dtype.itemsize,16*np.dtype(np.float64).itemsize)
   return U,res
  with patch.dict(ns,{'_refined_accumulator':checked}):ns['refined_projection'](counted,A,W[:,:11],B)
  self.assertEqual(widths,[8,3]);self.assertEqual(counted.calls,2*(1+ns['REFINE_STEPS']))

 def test_original_batch_normalization_not_maximum_subblock_ratio(self):
  A,W,B,lu=self.fixture();W[:,8:]*=1e-3
  def controlled(lu,A,rhs,**kw):return np.zeros(rhs.shape,dtype=np.longdouble),1e-10 if np.max(abs(rhs))>.01 else 1e-6
  with patch.dict(ns,{'_refined_accumulator':controlled}):_,_,res=ns['refined_projection'](lu,A,W,B)
  expected=max(1e-10*np.max(abs(W[:,:8])),1e-6*np.max(abs(W[:,8:])))/np.max(abs(W))
  self.assertEqual(res,expected)

 def test_invalid_residual_is_rejected(self):
  A,W,B,lu=self.fixture()
  for value in (float('nan'),float('inf'),-1.):
   with self.subTest(value=value),patch.dict(ns,{'_refined_accumulator':lambda *args,**kw:(np.zeros((2,8)),value)}):
    with self.assertRaisesRegex(ValueError,'invalid driving-point residual'):ns['refined_projection'](lu,A,W,B)

 def test_width_refusal_precedes_lu(self):
  A,W,B,lu=self.fixture()
  class NoLU:
   def solve(self,b):raise AssertionError('must refuse before solve')
  with self.assertRaisesRegex(ValueError,'eight RHS'):ns['_refined_accumulator'](NoLU(),A,np.zeros((2,9)),extended_solution=True)
  with self.assertRaisesRegex(ValueError,'sixteen RHS'):ns['refined_projection'](NoLU(),A,np.zeros((2,17)),B)

 def test_zero_and_empty_projections(self):
  A,W,B,lu=self.fixture()
  for width in (0,8,16):
   e,q,res=ns['refined_projection'](lu,A,np.zeros((2,width)),B)
   np.testing.assert_array_equal(e,np.zeros(width));np.testing.assert_array_equal(q,np.zeros((1,width)));self.assertEqual(res,0.)

if __name__=='__main__':unittest.main()
