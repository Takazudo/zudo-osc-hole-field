"""Finite access regression: no drill, void, or private-court shortcuts."""
import unittest
import shapely
from shapely.geometry import Point,box
from scripts.pcbgen.ground_access import strip,annular_access
from scripts.pcbgen.ground_private import alternative_conductance
import numpy as np

class GroundAccessTests(unittest.TestCase):
    def test_shared_barrel_conductance_is_not_duplicated(self):
        impedance=np.eye(4)*.001+np.ones((4,4))*.002
        actual=alternative_conductance(impedance,.1)
        self.assertAlmostEqual(actual,4/(.101+4*.002))
        self.assertLess(actual,4/.103)
        self.assertAlmostEqual(alternative_conductance(impedance,.1,0),3/(.101+3*.002))
    def test_strip_rejects_gap(self):
        copper=shapely.union_all([box(0,0,1,1),box(1.1,0,2,1)])
        self.assertIsNone(strip(copper,(.5,.5),(1.5,.5),.001))
    def test_finite_strip_charges_length(self):
        proof=strip(box(0,0,2,1),(.3,.5),(1.7,.5),.001)
        self.assertGreater(proof['ohm'],0)
        self.assertAlmostEqual(proof['ohm'],.001*1.4/.25)
    def test_supported_ring_and_private_cut(self):
        hole=Point(0,0).buffer(.15,quad_segs=32)
        copper=shapely.difference(box(-1,-1,1,1),hole)
        bridge={'x_mm':0,'y_mm':0,'annular_width_mm':.2}
        proof=annular_access(copper,hole,bridge,(.7,0),.001)
        self.assertIsNotNone(proof)
        self.assertTrue(proof['complete_annular_band_contained'])
        self.assertGreater(proof['annular_ohm'],0)
        cut=shapely.difference(copper,box(-.8,-.02,.8,.02))
        self.assertIsNone(annular_access(cut,hole,bridge,(.7,0),.001))
    def test_zero_or_tiny_annulus_rejected(self):
        hole=Point(0,0).buffer(.15)
        bridge={'x_mm':0,'y_mm':0,'annular_width_mm':.005}
        self.assertIsNone(annular_access(box(-1,-1,1,1),hole,bridge,(.7,0),.001))
    def test_common_strip_cannot_cross_private_court(self):
        common=shapely.difference(box(0,0,4,1),box(1,0,3,1))
        self.assertIsNone(strip(common,(.5,.5),(3.5,.5),.001))

if __name__=='__main__':unittest.main()
