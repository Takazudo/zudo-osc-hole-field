"""Analytic cylinder/radial annulus and fixed-arc convergence benchmarks."""
import math
import unittest
import numpy as np
from scripts.pcbgen.ground_annular import polar_network,two_terminal_resistance

class AnnularNetworkTests(unittest.TestCase):
    rho=1.7241e-5*(1+.003947*50)
    sheet=rho/.07
    def angles(self,n):return [2*math.pi*i/n for i in range(n)]
    def test_uniform_cylinder_and_radial_annulus(self):
        ri,ro,h,t=.15,.22,1.6,.025
        for n in (8,16,32):
            y,receipt=polar_network(ri,ro,self.sheet,self.rho,t,h,self.angles(n),[(0,0,0,2*math.pi),(1,0,0,2*math.pi)])
            expected=self.rho*h/(2*math.pi*ri*t)+2*self.sheet*math.log(ro/ri)/(2*math.pi)
            self.assertAlmostEqual(two_terminal_resistance(y),expected,places=9)
            self.assertEqual(receipt['single_physical_barrel_sector_columns'],n)
    def test_two_adjacent_full_thickness_upper_links(self):
        ri,ro,h,t=.15,.22,1.6,.025
        y,_=polar_network(ri,ro,self.sheet,self.rho,t,h,self.angles(16),[(0,0,0,2*math.pi),(1,0,0,2*math.pi),(2,0,0,2*math.pi)])
        middle=-y[1,0]/y[1,1];voltage=np.array([1,middle,0]);current=(y@voltage)[0]
        expected=2*self.rho*h/(2*math.pi*ri*t)+2*self.sheet*math.log(ro/ri)/(2*math.pi)
        self.assertAlmostEqual(1/current,expected,places=9)
    def test_duplicate_layer_ports_rejected(self):
        with self.assertRaisesRegex(ValueError,'one fixed outer-rim port'):
            polar_network(.15,.22,self.sheet,self.rho,.025,1.6,self.angles(16),[(0,0,.0002,.4),(0,1,.0002,.4)])
    def test_rotation_and_wrapped_seam(self):
        results=[]
        for rotation in (0,-.1,2*math.pi-.1):
            angles=[a+rotation for a in self.angles(32)]
            y,_=polar_network(.15,.22,self.sheet,self.rho,.025,1.6,angles,[(0,rotation,.0002,.4),(1,rotation+math.pi,.0002,.4)],8)
            results.append(two_terminal_resistance(y))
        self.assertTrue(np.allclose(results,results[0],rtol=1e-10,atol=1e-12))
    def test_fixed_arc_patch_refinement(self):
        values=[]
        for n,nr in ((16,4),(32,8),(64,16)):
            y,_=polar_network(.15,.22,self.sheet,self.rho,.025,1.6,self.angles(n),[(0,0,.0002,.4),(1,math.pi,.0002,.4)],nr)
            values.append(two_terminal_resistance(y))
        self.assertLess(abs(values[2]-values[1]),abs(values[1]-values[0]))
        self.assertLess(abs(values[2]-values[1])/values[2],.01)

if __name__=='__main__':unittest.main()
