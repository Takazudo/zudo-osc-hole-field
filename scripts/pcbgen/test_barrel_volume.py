"""Physical single-barrel current conservation and fixed-profile refinement."""
import unittest
import numpy as np
from scripts.pcbgen.barrel_volume import BarrelVolume

RHO = 1.7241e-5*(1+.003947*50)
BANDS = [(0, .07), (1.2, 1.34), (1.4, 1.47), (1.53, 1.6)]


class BarrelVolumeTests(unittest.TestCase):
    def test_asymmetric_four_foil_contacts_share_one_refining_barrel(self):
        results = []
        for refinement in (1, 2, 4):
            barrel = BarrelVolume(.15, .025, .275, 1.6, BANDS, RHO,
                polygon_sides=8, angular_subdivisions=refinement,
                radial_steps=refinement, band_steps=refinement, gap_steps=2*refinement)
            n = barrel.angular_count
            first = np.zeros(barrel.port_count)
            first[:n//2] = 2/n
            first[3*n+3*n//4:] = -4/n
            second = np.zeros(barrel.port_count)
            second[n+n//4:n+n//2] = 4/n
            second[2*n:3*n] = -1/n
            a, fa, va = barrel.bounds(first)
            b, fb, vb = barrel.bounds(second)
            both, _, _ = barrel.bounds(first+second)
            self.assertLess(a['maximum_cell_divergence_A'], 1e-10)
            self.assertEqual(a['physical_barrel_count'], 1)
            self.assertGreater(a['upper_ohm'], a['lower_ohm'])
            mutual_ab = fa@(barrel.rt_matrix@fb)
            mutual_ba = fb@(barrel.rt_matrix@fa)
            self.assertAlmostEqual(mutual_ab, mutual_ba, places=12)
            self.assertAlmostEqual(both['upper_ohm'], a['upper_ohm']+b['upper_ohm']+2*mutual_ab, places=12)
            results.append(a)
        self.assertTrue(all(a['lower_ohm'] < b['lower_ohm'] for a, b in zip(results, results[1:])))
        self.assertTrue(all(a['upper_ohm'] > b['upper_ohm'] for a, b in zip(results, results[1:])))
        self.assertLess(results[-1]['upper_ohm']-results[-1]['lower_ohm'],
                        .5*(results[0]['upper_ohm']-results[0]['lower_ohm']))

    def test_uniform_annular_transfer_brackets_finite_axial_gap(self):
        barrel = BarrelVolume(.15, .025, .275, 1.6, [(0, .07), (1.53, 1.6)], RHO,
                              polygon_sides=16, radial_steps=2, band_steps=2, gap_steps=4)
        n = barrel.angular_count
        receipt, _, _ = barrel.bounds(np.r_[np.ones(n)/n, -np.ones(n)/n])
        gap = RHO*(1.53-.07)/(np.pi*(.175**2-.15**2))
        self.assertGreater(receipt['upper_ohm'], gap)
        self.assertGreater(receipt['lower_ohm'], .85*gap)
        with self.assertRaisesRegex(ValueError, 'balance'):
            barrel.bounds(np.ones(barrel.port_count))
        with self.assertRaisesRegex(ValueError, 'strictly positive'):
            BarrelVolume(.15, .025, .275, .14, [(0, .07), (.07, .14)], RHO)


if __name__ == '__main__':
    unittest.main()
