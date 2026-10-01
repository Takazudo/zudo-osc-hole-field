import math
import unittest
from dataclasses import replace

from scripts.pcbgen.pth_wall_to_b_cut import (
    Geometry, resistance_upper, shell_field, sleeve_field,
)


class PthWallToBCutTest(unittest.TestCase):
    def setUp(self):
        # Conditional PROJECT numbers: no manufactured wall is asserted.
        self.geometry = Geometry(.61, .635, .915, 1.6, .035, .0175)

    def test_pointwise_boundary_and_interface_traces(self):
        g = self.geometry
        ri, ro, radius, length, _, depth = g.checked()
        current = -1.3
        q = current/(2*math.pi*ri*length)
        for z in (.1, .8, length-depth-.001, length-depth+.001, length-.001):
            self.assertAlmostEqual(shell_field(g, ri, z, current)[0], q, places=12)
            expected = current/(2*math.pi*ro*depth) if z > length-depth else 0.0
            self.assertAlmostEqual(shell_field(g, ro, z, current)[0], expected, places=12)
            if z > length-depth:
                self.assertAlmostEqual(shell_field(g, ro, z, current)[0],
                                       sleeve_field(g, ro, z, current)[0], places=12)
        for r in (ri, (ri+ro)/2, ro):
            self.assertAlmostEqual(shell_field(g, r, 0, current)[2], 0, places=12)
            self.assertAlmostEqual(shell_field(g, r, length, current)[2], 0, places=12)
        for r in (ro, (ro+radius)/2, radius):
            self.assertAlmostEqual(sleeve_field(g, r, length, current)[2], 0, places=12)
            self.assertAlmostEqual(sleeve_field(g, r, length-depth, current)[2],
                                   -current/(math.pi*(radius*radius-ro*ro)), places=12)
        self.assertAlmostEqual(sleeve_field(g, radius, length-depth/2, current)[0], 0, places=12)
        # The integral of the wall, radial interface, and internal cut traces.
        self.assertAlmostEqual(-q*(2*math.pi*ri*length), -current)
        self.assertAlmostEqual(current/(2*math.pi*ro*depth)*(2*math.pi*ro*depth), current)
        self.assertAlmostEqual(-sleeve_field(g, (ro+radius)/2, length-depth, current)[2]
                               *math.pi*(radius*radius-ro*ro), current)
        # Perturbing either radial profile destroys pointwise gluing.
        self.assertGreater(abs(shell_field(g, ro, length-depth/2, current)[0]
                               -1.01*sleeve_field(g, ro, length-depth/2, current)[0]), 1e-3)

    def test_divergence_and_energy_quadrature(self):
        g = self.geometry
        ri, ro, radius, length, _, depth = g.checked()
        current = .7
        eps = 1e-6
        for r, z, field in ((.622, .7, shell_field),
                            (.622, length-depth/2, shell_field),
                            (.78, length-depth/2, sleeve_field)):
            jr = lambda x, y: field(g, x, y, current)[0]
            jz = lambda x, y: field(g, x, y, current)[2]
            divergence = ((r+eps)*jr(r+eps, z)-(r-eps)*jr(r-eps, z))/(2*eps*r)
            divergence += (jz(r, z+eps)-jz(r, z-eps))/(2*eps)
            self.assertLess(abs(divergence), 1e-6)
        # Midpoint integration is diagnostic; the analytic bound is independently
        # derived from pointwise inequalities and rounded outward by the helper.
        rho = 2.3e-5
        energy = 0.0
        for low, high, zlow, zhigh, field in (
            (ri, ro, 0, length, shell_field),
            (ro, radius, length-depth, length, sleeve_field),
        ):
            nr = nz = 48
            dr = (high-low)/nr; dz = (zhigh-zlow)/nz
            for ir in range(nr):
                r = low+(ir+.5)*dr
                for iz in range(nz):
                    z = zlow+(iz+.5)*dz
                    jr, jtheta, jz = field(g, r, z, current)
                    energy += rho*(jr*jr+jtheta*jtheta+jz*jz)*2*math.pi*r*dr*dz
        upper = resistance_upper(g, rho)
        self.assertGreater(energy, 0)
        self.assertLess(energy, current*current*upper['total_ohm_upper'])
        self.assertGreaterEqual(upper['total_ohm_upper'],
                                upper['shell_ohm_upper']+upper['sleeve_ohm_upper']-1e-15)

    def test_geometry_mutations_reject(self):
        g = self.geometry
        for mutated in (replace(g, shell_outer_radius_mm=g.inner_radius_mm),
                        replace(g, land_radius_mm=g.shell_outer_radius_mm),
                        replace(g, transfer_depth_mm=g.b_foil_thickness_mm),
                        replace(g, b_foil_thickness_mm=g.board_depth_mm)):
            with self.assertRaises(ValueError):
                resistance_upper(mutated, 2.3e-5)
        with self.assertRaises(ValueError):
            shell_field(g, .6, .8, 1.)
        with self.assertRaises(ValueError):
            sleeve_field(g, .8, 1.0, 1.)
        with self.assertRaises(ValueError):
            resistance_upper(g, float('nan'))


if __name__ == '__main__':
    unittest.main()
