"""Verifier-owned row/forest proof; no original data or externally supplied edges."""
import test_virtual as V
from test_virtual import C,W,T,P,np,csr,CONTEXT
import unittest
import json
from pathlib import Path
import weakref

RESULTS={}


def run(a):
    m=P.Meter();r=W.measured(lambda:P.certify_forest(a,CONTEXT,m),m)
    r['proposed_scalar_contributions']=getattr(m,'proposed_scalar_contributions',0)
    r['integer_units']=getattr(m,'integer_operations',0)
    r['integer_bit_work_envelope']=getattr(m,'integer_bit_work_envelope',0)
    r['integer_phase_operations']=getattr(m,'integer_phases',{})
    r['proposed_contribution_phases']=getattr(m,'proposed_contribution_phases',{})
    r['proposed_width_histogram']=getattr(m,'proposed_width_histogram',{})
    r['index_visits']=getattr(m,'index_visits',{})
    r['index_phase_visits']=getattr(m,'index_phase_visits',{})
    r['tree_structure_order']=getattr(m,'forest_order',0)
    r['selected_edges_before_exit']=getattr(m,'forest_selected_edges',0)
    r['producer_outcome']='CONSTRUCTED_AND_CERTIFIED' if r['status']=='CERTIFIED' else 'REFUSED_DURING_VERIFIER_CONSTRUCTION'
    r['screen']='NOT RUN: board-only fixture' 
    return r


class ForestTests(unittest.TestCase):
    def test_retained_grids_and_recurrence_count(self):
        for side in [4,8,9]:
            a=T.grid(side);r=run(a);RESULTS[f'grid{side}']=r
            self.assertEqual(r['status'],'CERTIFIED')
            self.assertEqual(r['proposed_contribution_phases']['forest_exact_rows'],a.nnz-a.shape[0])
            self.assertEqual(r['proposed_contribution_phases']['forest_selection'],a.shape[0]-1)
            self.assertEqual(r['proposed_contribution_phases']['forest_paths'],a.shape[0])
            self.assertLessEqual(r['inverse_infinity_upper'],side*side*(1+2*(side-1))*1.000001)
            self.assertEqual(r['proposed_scalar_contributions'],sum(r['proposed_contribution_phases'].values()))
            self.assertEqual(r['index_visit_total'],sum(r['index_phase_visits'].values()))

    def test_nonroot_heterogeneous_unions(self):
        a=np.zeros((5,5))
        for i,j,c in [(0,4,2.),(1,2,.5),(1,3,4.),(2,4,1.25)]:
            a[i,i]+=c;a[j,j]+=c;a[i,j]-=c;a[j,i]-=c
        a[3,3]+=2.;r=run(csr(a));RESULTS['heterogeneous_nonroot']=r
        self.assertEqual(r['status'],'CERTIFIED')
        self.assertEqual(r['root'],3)
        self.assertGreaterEqual(T.F(r['tree_max_inverse_diagonal_upper']),T.F(81,20))
        self.assertLess(r['inverse_infinity_upper'],20.250000001)
        self.assertGreaterEqual(T.F(r['inverse_infinity_upper']),max(sum(map(abs,row)) for row in T.exact_inverse(csr(a))))

    def test_virtual_coupled_and_rejections(self):
        for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
            blocks,d,ref,m,view=V.view_case(kwargs)
            r=W.measured(lambda:P.coercivity_interval_certificate(view,view.interval_entries(),CONTEXT,m,
                bound_mode='path-only',exact_kernel='compact',forest=True),m)
            self.assertEqual(r['status'],'CERTIFIED');r.update(W.physical_result(r,blocks,ref))
            r['view_access']=dict(view.access);RESULTS[name]=r
        for name,a in [('disconnected',csr([[1.,0.],[0.,1.]])),
                       ('singular',csr([[1.,-1.],[-1.,1.]])),
                       ('one_sided',csr([[2.,-1.],[0.,2.]]))]:
            r=run(a);RESULTS[name]=r;self.assertEqual(r['status'],'REFUSED')
            self.assertGreater(r['integer_units'],0)

    def test_scope_failure_width_and_lifetime(self):
        m=P.Meter();m.phase='failed_scope'
        with self.assertRaises(ValueError):
            with P.ProposedContribution(m):
                P.compact_add((1,2048),(1,-1075),m)
        self.assertGreater(m.proposed_scalar_contributions,0)
        self.assertFalse(m.contribution_active)
        m=P.Meter();m.phase='wide_cancellation'
        with P.ProposedContribution(m):
            r=P.compact_add(((1<<100)+1,0),(-1,100),m)
        self.assertEqual(r,(1,0))
        self.assertEqual(m.proposed_scalar_contributions,2)
        m=P.Meter();f=P._VerifiedForest(5,m);d=weakref.ref(f.dsu);s=weakref.ref(f.size)
        f.release_selection();self.assertIsNone(d());self.assertIsNone(s())
        limited=P.Meter(P.I.Work(max_updates=1,max_entries=100000))
        with self.assertRaises(ValueError):P.certify_forest(T.grid(4),CONTEXT,limited)
        self.assertGreater(limited.proposed_scalar_contributions,1)

if __name__=='__main__':
    import sys
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ForestTests))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(RESULTS,indent=2,sort_keys=True)+'\n')
    raise SystemExit(not r.wasSuccessful())
