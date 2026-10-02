import unittest
from fractions import Fraction as F
from scripts.pcbgen.foil_edge_bubble_probe import edge_bubble,check_patch,p1_work,gram_update,psd,sqrt_up

A=(0,0);B=(1,1);C=(1,0);D=(0,1)
TRI=((A,C,B),(A,B,D));EDGE=(A,B)
BUBBLE=tuple(edge_bubble(t,EDGE) for t in TRI)
Q=(((F(1),F(1)),)*3,((F(0),F(0)),)*3)

def work(a,b):return sum((p1_work(t,u,v) for t,u,v in zip(TRI,a,b)),F())
def scaled(a,s):return tuple(tuple(tuple(s*x for x in v) for v in tri) for tri in a)
def add(a,b):return tuple(tuple(tuple(x+y for x,y in zip(u,v)) for u,v in zip(ta,tb)) for ta,tb in zip(a,b))
def points(m):return [[(x,x) for x in row] for row in m]

class ProofFixtures(unittest.TestCase):
    def test_exact_reduction_full_traces_and_divergence(self):
        check_patch(TRI,BUBBLE,EDGE)
        self.assertEqual(work(Q,Q),1)
        self.assertEqual(work(Q,BUBBLE),F(1,3))
        self.assertEqual(work(BUBBLE,BUBBLE),F(1,3))
        improved=add(Q,scaled(BUBBLE,-1))
        self.assertEqual(work(improved,improved),F(2,3))
        for t,q in zip(TRI,improved):
            self.assertEqual(q,tuple((F(x),1-F(y)) for x,y in t))
    def test_exact_two_column_gram_and_naive_diagonal_failure(self):
        U=[[F(1),F(2)],[F(2),F(4)]]
        L=[[F(2,3),F(4,3)],[F(4,3),F(8,3)]]
        H=[[F(1,3),F(2,3)],[F(2,3),F(4,3)]]
        G=[[-x for x in row] for row in H]
        self.assertEqual(gram_update(U,L,points(G),H,[0,0]),L)
        self.assertFalse(psd([[F(2,3),2],[2,F(8,3)]]))
    def test_nonzero_raw_to_conserved_correction_units(self):
        U=[[1,0],[0,0]];L=[[F(2,3),0],[0,0]];H=[[F(1,3),0],[0,0]]
        out=gram_update(U,L,points([[F(-11,30),0],[0,0]]),H,[F(1,300),0])
        self.assertGreaterEqual(out[0][0],F(2,3))
        self.assertLess(out[0][0]-F(2,3),F(1,10**20))
    def test_no_improvement_for_global_gradient(self):
        q=tuple(tuple((F(x),F(y)) for x,y in t) for t in TRI)
        self.assertEqual(work(q,BUBBLE),0)
        zero=[[0,0],[0,0]];U=[[1,0],[0,1]]
        self.assertEqual(gram_update(U,zero,points(zero),zero,[0,0]),U)
    def test_source_divergence_does_not_change_under_curl(self):
        radial=tuple(tuple((F(x),F(y)) for x,y in t) for t in TRI)
        q=add(Q,radial)
        self.assertEqual(work(q,BUBBLE),F(1,3))
        check_patch(TRI,BUBBLE,EDGE)
    def test_changed_outer_trace_rejected(self):
        bad=list(BUBBLE);t=list(bad[0]);t[0]=(t[0][0]+1,t[0][1]);bad[0]=tuple(t)
        with self.assertRaises(ValueError):check_patch(TRI,bad,EDGE)
    def test_internal_normal_trace_rejected_even_when_each_divergence_is_zero(self):
        doubled=tuple(tuple(2*x for x in v) for v in BUBBLE[1])
        with self.assertRaisesRegex(ValueError,"shared normal trace"):
            check_patch(TRI,(BUBBLE[0],doubled),EDGE)
    def test_updated_upper_contradiction_rejected(self):
        U=[[1,0],[0,0]]
        with self.assertRaisesRegex(ValueError,"contradicts lower"):
            gram_update(U,U,points([[F(-1,3),0],[0,0]]),[[F(1,3),0],[0,0]],[0,0])
    def test_wrong_or_overlapping_patch_rejected(self):
        with self.assertRaises(ValueError):check_patch((TRI[0],TRI[0]),(BUBBLE[0],BUBBLE[0]),EDGE)
        with self.assertRaises(ValueError):edge_bubble(TRI[0],(A,D))
    def test_impossible_cross_or_negative_correction_rejected(self):
        U=[[1,0],[0,1]];zero=[[0,0],[0,0]]
        with self.assertRaises(ValueError):gram_update(U,zero,points([[1,0],[0,0]]),zero,[0,0])
        with self.assertRaises(ValueError):gram_update(U,zero,points(zero),zero,[-1,0])
    def test_sqrt_enclosure(self):
        for x in (F(),F(1,9),F(2),F(1,10**40),F(10**40)):
            u=sqrt_up(x);self.assertGreaterEqual(u*u,x)
            if u:self.assertLess((u-F(1,2**80))**2,x)


class IntegratedArithmeticFixtures(unittest.TestCase):
    def test_reconstruct_saved_flux_and_compose_two_columns(self):
        from scripts.pcbgen.foil_edge_bubble_probe import patch_work,combine_patches,rt0_values
        flux=(((1,2),(0,0),(-1,-2)),((0,0),(0,0),(0,0)))
        self.assertEqual(rt0_values(TRI[0],[1,0,-1]),Q[0])
        g,h=patch_work(TRI,flux,EDGE,F(1))
        self.assertEqual((g,h),([F(1,3),F(2,3)],F(1,3)))
        G,H,beta=combine_patches([{'raw_work_exact':g,'bubble_energy_exact':h}])
        self.assertEqual(beta,[[-1.,-2.]])
        self.assertEqual(G,[[-x for x in row] for row in H])
        self.assertEqual(H,[[F(1,3),F(2,3)],[F(2,3),F(4,3)]])
    def test_material_and_flux_scaling(self):
        from scripts.pcbgen.foil_edge_bubble_probe import patch_work
        flux=(((3,6),(0,0),(-3,-6)),((0,0),(0,0),(0,0)))
        g,h=patch_work(TRI,flux,EDGE,F(7,10))
        self.assertEqual(g,[F(7,10),F(7,5)]);self.assertEqual(h,F(7,30))
    def test_psd_float_serialization_covers_all_entries(self):
        from scripts.pcbgen.foil_edge_bubble_probe import upper_float_matrix,transfer_interval
        m=[[F(2,3),F(4,3)],[F(4,3),F(8,3)]];u=upper_float_matrix(m)
        self.assertTrue(psd([[F(u[i][j])-m[i][j] for j in range(2)] for i in range(2)]))
        lo,hi=transfer_interval(u,m)
        self.assertLessEqual(lo,F(4,3));self.assertGreaterEqual(hi,F(4,3))
    def test_rounding_coefficient_remains_explicit_not_claimed_optimal(self):
        from scripts.pcbgen.foil_edge_bubble_probe import combine_patches
        G,H,beta=combine_patches([{'raw_work_exact':[1,2],'bubble_energy_exact':3}])
        b=F(beta[0][0]);self.assertEqual(G[0][0],b);self.assertEqual(H[0][0],3*b*b)

if __name__=='__main__':unittest.main()
