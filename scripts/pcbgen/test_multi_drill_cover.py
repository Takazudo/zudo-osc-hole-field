"""Exact multiple-hole coverage and adversarial annulus/overlap geometry."""
import copy
from fractions import Fraction as Q
import unittest
from scripts.pcbgen.multi_drill_cover import (
    certify,convex_branches,pad_intersection_positive,clip,square_inside,
)


class MultiDrillCoverTest(unittest.TestCase):
    def fixture(self):
        p={'kind':'roundrect','centre_nm':[0,0],'half_size_nm':[800000,200000],
           'corner_radius_nm':100000,'quarter_turns':0}
        pad={'ref':'C1','pad':'2','uuid':'source','net':'AGND','copper':{'B.Cu':[]},'analytic_primitives':{'B.Cu':p}}
        holes=[];items={}
        for i,x in enumerate([-.4,.4]):
            uid='via'+str(i);h={'uuid':uid,'net':'AGND','plated':True,'xy_mm':[x,0],
                'size_mm':[.3,.3],'copper_layers':['F.Cu','B.Cu']};holes.append(h)
            primitive={'kind':'circle','centre_nm':[int(x*1000000),0],'half_size_nm':[350000,350000],
                       'corner_radius_nm':0,'quarter_turns':0}
            items[uid]={'uuid':uid,'net':'AGND','copper':{'B.Cu':[]},'analytic_primitives':{'B.Cu':primitive}}
        outline=[(-2000000,-2000000),(2000000,-2000000),(2000000,2000000),(-2000000,2000000)]
        return pad,holes,items,holes,outline,'B.Cu'

    def test_two_holes_complete_choices_and_exact_connected_tree(self):
        args=self.fixture();r=certify(*args);annuli=[d for d in r['domains'] if d['kind']=='annulus']
        self.assertEqual(len(annuli),2)
        self.assertEqual(r['complete_halfplane_choices'],64)
        self.assertEqual(r['positive_convex_leaves']+sum(8**(2-len(e['choice_prefix'])) for e in r['pruned_choice_prefixes']),64)
        self.assertTrue(all(len(d['planes'])==2 for d in r['domains'] if d['kind']=='convex_piece'))
        seen={0}
        for edge in r['overlap_tree']:
            self.assertIn(edge['parent'],seen);self.assertNotIn(edge['child'],seen)
            for k in ('parent','child'):
                self.assertTrue(square_inside(edge['square_nm'],r['domains'][edge[k]],r['source_primitive']))
            seen.add(edge['child'])
        self.assertEqual(seen,set(range(len(r['domains']))))

    def test_annulus_clipped_by_another_target_foreign_drill_or_edge(self):
        args=list(self.fixture());args=copy.deepcopy(args)
        args[1][1]['xy_mm']=[0,0];args[2]['via1']['analytic_primitives']['B.Cu']['centre_nm']=[0,0]
        with self.assertRaisesRegex(ValueError,'other drill clips full annulus'):certify(*args)
        args=list(self.fixture());foreign=copy.deepcopy(args[1][0]);foreign.update(uuid='foreign',net='+5V',xy_mm=[0,0]);args[3]=args[3]+[foreign]
        with self.assertRaisesRegex(ValueError,'foreign drill'):certify(*args)
        args=list(self.fixture());args[4]=[(-2000000,-2000000),(2000000,-2000000),(2000000,300000),(-2000000,300000)]
        with self.assertRaisesRegex(ValueError,'native cut clips full annulus'):certify(*args)
        args=list(self.fixture());args[2]=copy.deepcopy(args[2]);args[2]['via0']['net']='foreign'
        with self.assertRaisesRegex(ValueError,'same-net'):certify(*args)

    def test_exact_rounded_corner_empty_and_tangent_overlap(self):
        p={'kind':'roundrect','centre_nm':[0,0],'half_size_nm':[10,10],
           'corner_radius_nm':5,'quarter_turns':0}
        # Actual corner is circular, not its bounding box/hull.
        self.assertFalse(pad_intersection_positive([(Q(9),Q(9)),(Q(10),Q(9)),(Q(10),Q(10)),(Q(9),Q(10))],p)[0])
        self.assertTrue(pad_intersection_positive([(Q(5),Q(5)),(Q(9),Q(5)),(Q(9),Q(9)),(Q(5),Q(9))],p)[0])
        domain={'kind':'annulus','centre_nm':[0,0],'inner_radius_nm':5,'outer_radius_nm':10}
        self.assertFalse(square_inside([5,0,6,1],domain,p))
        self.assertFalse(square_inside([6,0,6,1],domain,p))
        self.assertTrue(square_inside([6,0,7,1],domain,p))

    def test_clipping_and_zero_area_branch(self):
        poly=[(Q(0),Q(0)),(Q(4),Q(0)),(Q(4),Q(4)),(Q(0),Q(4))]
        result=clip(poly,(1,1),Q(15,2))
        self.assertEqual(set(result),{(Q(7,2),Q(4)),(Q(4),Q(7,2)),(Q(4),Q(4))})
        p={'kind':'rectangle','centre_nm':[2,2],'half_size_nm':[2,2],'corner_radius_nm':0,'quarter_turns':0}
        self.assertFalse(pad_intersection_positive(clip(poly,(1,1),8),p)[0])


if __name__=='__main__':unittest.main()
