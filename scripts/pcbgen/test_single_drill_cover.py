"""Adversarial exact nominal cover geometry, independent of native execution."""
import copy
import unittest
from fractions import Fraction as Q
from scripts.pcbgen.single_drill_cover import (
    certify, native_outline, plane_nonempty, square_valid, inside_pad,
)


class SingleDrillCoverTest(unittest.TestCase):
    def fixture(self):
        p={'kind':'roundrect','centre_nm':[0,0],'half_size_nm':[600000,300000],
           'corner_radius_nm':100000,'quarter_turns':0}
        pad={'ref':'U1','pad':'1','uuid':'pad','net':'AGND',
             'analytic_primitives':{'F.Cu':p}}
        hole={'uuid':'via','net':'AGND','plated':True,'xy_mm':[.4,0],
              'size_mm':[.3,.3],'copper_layers':['F.Cu','B.Cu']}
        vp={'kind':'circle','centre_nm':[400000,0],'half_size_nm':[350000,350000],
            'corner_radius_nm':0,'quarter_turns':0}
        via={'uuid':'via','net':'AGND','copper':{'F.Cu':[], 'B.Cu':[]},
             'analytic_primitives':{'F.Cu':vp,'B.Cu':vp}}
        outline=[(-2000000,-2000000),(2000000,-2000000),(2000000,2000000),(-2000000,2000000)]
        return pad,hole,via,[hole],outline,'F.Cu'

    def test_exact_tree_and_every_overlap_corner(self):
        args=self.fixture();r=certify(*args);p=args[0]['analytic_primitives']['F.Cu']
        reached={0}
        for edge in r['overlap_tree']:
            self.assertIn(edge['parent'],reached);self.assertNotIn(edge['child'],reached)
            self.assertGreater(edge['area_nm2'],0)
            self.assertTrue(square_valid(edge['square_nm'],[r['domains'][edge[k]] for k in ('child','parent')],p,(400000,0),150000,350000))
            reached.add(edge['child'])
        self.assertEqual(reached,set(range(len(r['domains']))))
        # The implicit convex primitive retains its circular corners: no hull.
        self.assertFalse(inside_pad((600000,300000),p))
        # Exact supporting-plane tangency has zero area and is excluded.
        self.assertFalse(plane_nonempty(p,(1,0),600000))
        self.assertTrue(plane_nonempty(p,(1,0),599999))

    def test_wrong_net_foreign_drill_and_clipped_annulus_reject(self):
        args=list(self.fixture());args[2]=copy.deepcopy(args[2]);args[2]['net']='+5V'
        with self.assertRaisesRegex(ValueError,'same-net'):certify(*args)
        args=list(self.fixture());foreign=copy.deepcopy(args[1]);foreign.update(uuid='foreign',xy_mm=[.7,0],net='+12V');args[3]=args[3]+[foreign]
        with self.assertRaisesRegex(ValueError,'other native drill'):certify(*args)
        # Pad fits but its full via land is clipped by the actual board edge.
        args=list(self.fixture());args[4]=[(-2000000,-2000000),(725000,-2000000),(725000,2000000),(-2000000,2000000)]
        with self.assertRaisesRegex(ValueError,'native cut'):certify(*args)

    def test_vanishing_overlap_and_no_octagon_margin(self):
        args=list(self.fixture());p=args[0]['analytic_primitives']['F.Cu']
        annulus={'kind':'annulus'}
        self.assertFalse(square_valid([550000,0,551000,1000],[annulus],p,(400000,0),150000,350000))
        self.assertFalse(square_valid([600000,0,600000,1000],[annulus],p,(400000,0),150000,350000))
        args[2]=copy.deepcopy(args[2]);args[2]['analytic_primitives']['F.Cu']['half_size_nm']=[160000,160000]
        with self.assertRaisesRegex(ValueError,'missing octagon'):certify(*args)

    def test_complete_native_cut_authority_rejects_extra_cut(self):
        outline=[[0,0],[4,0],[4,4],[0,4]]
        lines=['(kicad_pcb']
        for a,b in zip(outline,outline[1:]+outline[:1]):
            lines.append('(gr_line\n (start %s %s) (end %s %s) (layer "Edge.Cuts"))'%(*a,*b))
        text='\n'.join(lines)+'\n)\n'
        self.assertEqual(native_outline(text,outline),[(0,0),(4000000,0),(4000000,4000000),(0,4000000)])
        extra='(gr_line\n (start 1 1) (end 2 1) (layer "Edge.Cuts"))\n'
        with self.assertRaisesRegex(ValueError,'complete exported'):native_outline(text[:-2]+extra+')\n',outline)


if __name__=='__main__':unittest.main()
