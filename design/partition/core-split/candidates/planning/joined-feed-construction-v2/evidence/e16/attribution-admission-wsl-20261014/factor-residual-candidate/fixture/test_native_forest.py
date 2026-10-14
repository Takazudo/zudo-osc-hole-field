"""Native forest regressions on retained bounded fixtures; no original IO."""
import os
os.environ.update(OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
import tempfile
import unittest
import json
import sys
from pathlib import Path
import native_forest as N
import test_forest as F
import test_virtual as V
from test_virtual import T,P,W,np,csr,CONTEXT
RESULTS={}

class NativeForestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='e16-native-forest-')
        path,identity=N.build(cls.temp.name);cls.kernel=N.Kernel(path);RESULTS['build']=identity
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def measured(self,a):
        r=W.measured(lambda:self.kernel.certify(a,CONTEXT),P.Meter())
        r['unused_legacy_meter']=r.pop('accounting')
        r['measurement_scope']='tracemalloc excludes native stack; RSS is process high water; native fixed buffers reported separately'
        return r
    def test_retained_and_held_out(self):
        for side in (4,8,9):
            a=T.grid(side);r=self.measured(a);RESULTS[f'grid{side}']=r
            self.assertEqual(r['status'],'CERTIFIED',r)
            old=F.run(a)
            self.assertAlmostEqual(r['inverse_infinity_upper']/old['inverse_infinity_upper'],1.,places=12)
            self.assertEqual(r['row_visits'],a.shape[0])
            self.assertEqual(r['selected_edges'],a.shape[0]-1)
            self.assertEqual(r['phase_work']['exact_rows']['proposed_contributions'],a.nnz-a.shape[0])
    def test_heterogeneous_and_refusals(self):
        a=np.zeros((5,5))
        for i,j,c in [(0,4,2.),(1,2,.5),(1,3,4.),(2,4,1.25)]:
            a[i,i]+=c;a[j,j]+=c;a[i,j]-=c;a[j,i]-=c
        a[3,3]+=2.;a=csr(a);r=self.measured(a);RESULTS['heterogeneous']=r
        self.assertEqual(r['status'],'CERTIFIED');self.assertEqual(r['root'],3)
        self.assertGreaterEqual(T.F(r['inverse_infinity_upper']),max(sum(map(abs,row)) for row in T.exact_inverse(a)))
        for name,a in [('disconnected',csr([[1.,0.],[0.,1.]])),('singular',csr([[1.,-1.],[-1.,1.]])),
                       ('one_sided',csr([[2.,-1.],[0.,2.]])),('deficit',csr([[.1,-1.],[-1.,2.]]))]:
            r=self.measured(a);RESULTS[name]=r;self.assertEqual(r['status'],'REFUSED')
            self.assertGreater(r['native_kernel_units'],0)
    def test_coupled_actual_screen(self):
        for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
            blocks,d,ref,m,view=V.view_case(kwargs);r=self.measured(view)
            self.assertEqual(r['status'],'CERTIFIED',r)
            r.update(W.physical_result(r,blocks,ref))
            r['midpoint_assembly']=W.snapshot(m)
            r['midpoint_proposed_contributions']=getattr(m,'proposed_scalar_contributions',0)
            r['complete_proposed_contributions']=r['proposed_scalar_contributions']+r['midpoint_proposed_contributions']
            RESULTS[name]=r
            old=P.coercivity_interval_certificate(view,view.interval_entries(),CONTEXT,P.Meter(),bound_mode='path-only',exact_kernel='compact',forest=True)
            self.assertAlmostEqual(r['inverse_infinity_upper']/old['inverse_infinity_upper'],1.,places=12)
    def test_bindings_and_bad_input(self):
        a=T.grid(4);first=self.kernel.certify(a,CONTEXT)
        a.data[0]+=1.;second=self.kernel.certify(a,CONTEXT)
        self.assertNotEqual(first['matrix_sha256'],second['matrix_sha256'])
        self.assertNotEqual(first['witness_sha256'],second['witness_sha256'])
        a.data[0]=np.nan
        self.assertEqual(self.kernel.certify(a,CONTEXT)['status'],'REFUSED')
        with self.assertRaises(ValueError):self.kernel.certify(T.grid(12),CONTEXT)
        a=T.grid(4);a.indptr=a.indptr[:-1]
        with self.assertRaisesRegex(ValueError,'metadata'):self.kernel.certify(a,CONTEXT)
        a=T.grid(4);a.indices=a.indices[:-1]
        with self.assertRaisesRegex(ValueError,'metadata'):self.kernel.certify(a,CONTEXT)
        a=T.grid(4);a.indices[0]=-1
        self.assertEqual(self.kernel.certify(a,CONTEXT)['status'],'REFUSED')

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeForestTests))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(RESULTS,sort_keys=True,indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
