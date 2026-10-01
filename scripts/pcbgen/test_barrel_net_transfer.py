"""Finite wall-to-annulus base trial on an actual plated-shell geometry."""
import math
import unittest

from scripts.pcbgen.barrel_source_flux import (
    net_wall_to_annulus_mode,
    net_wall_to_annulus_resistance_upper,
)


class BarrelNetTransferTest(unittest.TestCase):
    def test_divergence_boundary_flux_and_energy(self):
        ri, ro, length, rho = .61, .635, 1.6, 2.3e-5
        kw = dict(inner_radius_mm=ri, outer_radius_mm=ro, length_mm=length, current=1.)
        radius, z, step = .622, .7, 1e-7
        field = lambda r, h: net_wall_to_annulus_mode(r, h, **kw)
        radial = ((radius+step)*field(radius+step,z)[0]
                  -(radius-step)*field(radius-step,z)[0])/(2*step*radius)
        axial = (field(radius,z+step)[2]-field(radius,z-step)[2])/(2*step)
        self.assertLess(abs(radial+axial), 1e-7)
        q = 1/(2*math.pi*ri*length)
        self.assertAlmostEqual(field(ri,z)[0], q)
        self.assertAlmostEqual(field(ro,z)[0], 0)
        self.assertAlmostEqual(field(radius,0)[2], 0)
        self.assertAlmostEqual(field(radius,length)[2], 1/(math.pi*(ro*ro-ri*ri)))
        # Cylindrical volume measure is 2*pi*r dr dz; the outward upper must
        # dominate an independently integrated full-shell trial energy.
        n = 200; dr = (ro-ri)/n; dz = length/n; energy = 0
        for i in range(n):
            r = ri+(i+.5)*dr
            for j in range(n):
                values = field(r,(j+.5)*dz)
                energy += rho*sum(x*x for x in values)*2*math.pi*r*dr*dz
        upper = net_wall_to_annulus_resistance_upper(inner_radius_mm=ri,
            outer_radius_mm=ro,length_mm=length,rho_max_ohm_mm=rho)
        self.assertGreaterEqual(upper,energy)

    def test_no_zero_thickness_or_implicit_annular_transfer(self):
        with self.assertRaises(ValueError):
            net_wall_to_annulus_resistance_upper(inner_radius_mm=.15,
                outer_radius_mm=.15,length_mm=1.6,rho_max_ohm_mm=2.3e-5)
        with self.assertRaises(ValueError):
            net_wall_to_annulus_mode(.18,.5,inner_radius_mm=.15,
                outer_radius_mm=.175,length_mm=1.6,current=1.)


if __name__ == '__main__':
    unittest.main()
