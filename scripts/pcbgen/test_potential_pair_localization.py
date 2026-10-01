"""Analytic complete-foil/barrel Green signs and correction-reference tests."""
from fractions import Fraction as F
import unittest
import numpy as np
from scripts.pcbgen.potential_pair_localization import (
    balanced_collar_reference,green_work,foil_extension_trace,quadratic_upper,
    mismatch_interval,check_complete_mismatch,sheet_energy_bounds,finite_source_loads,complete_foil_work)


class PotentialLocalizationTests(unittest.TestCase):
    def test_multi_foil_green_with_nonzero_layer_sources(self):
        # Two finite foil interfaces, two uniform angular sectors each.
        # One ampere leaves lower foil through the barrel and enters upper foil.
        currents=[F(-1,2),F(-1,2),F(1,2),F(1,2)]
        potentials=[3,5,1,1]
        # Incoming source totals are opposite the barrel-outward layer totals.
        source_totals=[1,-1]
        # A finite face source has its own average potential; do not replace
        # these actual source integrals by the barrel endpoint potentials.
        source_load=[6,-2]
        barrel,foil,nets=green_work(currents,potentials,2,source_load,source_totals,[0,0])
        self.assertEqual(barrel,-3)
        self.assertEqual(foil,[-2,1])
        self.assertEqual(barrel+sum(foil),-sum(source_load))
        # Layer net currents are NONZERO. Centering must change the complete
        # source functional too; otherwise this equality would fail.
        shifted=green_work(currents,potentials,2,source_load,source_totals,[7,-11])
        self.assertEqual(shifted[1],foil)
        # The vertical source lift pairs zero with depth-constant potential,
        # but its finite boundary load is the source_load above and remains.
        self.assertNotEqual(source_load,[source_totals[i]*potentials[2*i] for i in range(2)])

    def test_multiple_barrels_charge_complete_source_once(self):
        work=[F(-11,2),F(2)];net=[F(-3,2),F(3,2)]
        load=[F(9),F(-3)];sources=[F(3,2),F(-3,2)]
        foils=[complete_foil_work(work[i],net[i],load[i],sources[i],[7,-11][i]) for i in range(2)]
        self.assertEqual(foils,[F(-7,2),F(1)])
        self.assertEqual(sum(work)+sum(foils),-sum(load))

    def fixture_sheet(self):
        from types import SimpleNamespace
        import shapely
        xy=np.array([[0,0],[1,0],[1,1],[0,1]],dtype=np.longdouble)
        tri=np.array([[0,1,2],[0,2,3]])
        polygons=shapely.polygons(np.asarray(xy[tri],dtype=float))
        return SimpleNamespace(metric_xy=xy,triangles=tri,areas=np.array([.5,.5]),
            metric_factors=np.ones(2),polygons=polygons,tree=shapely.STRtree(polygons))

    def test_streamed_current_potential_metrics_and_excluded_cells(self):
        from shapely.geometry import box
        sheet=self.fixture_sheet()
        nodes=np.array([[0,0],[1,2],[1,2],[0,0]],dtype=float)
        result=sheet_energy_bounds(sheet,nodes,np.zeros_like(nodes),1.,1.,'potential',box(-1,-1,2,2),block=1)
        for k,energy in enumerate((1.,4.)):
            self.assertLessEqual(result['energy_interval_ohm'][k][0],energy)
            self.assertGreaterEqual(result['energy_interval_ohm'][k][1],energy)
        crossing=sheet_energy_bounds(sheet,nodes,np.zeros_like(nodes),1.,1.,'potential',box(0,0,1,1),block=1)
        self.assertEqual(crossing['guaranteed_inner_cells'],0)
        self.assertEqual(crossing['energy_interval_ohm'][0][0],0)
        self.assertGreaterEqual(crossing['excluded_or_crossing_cell_energy_upper_ohm'][0],1)
        q=np.array([[1,-1,0],[0,-1,1]],dtype=float)
        q=np.stack((q,2*q),axis=2)
        current=sheet_energy_bounds(sheet,q,None,1.,1.,'current',block=1)
        for k,energy in enumerate((1.,4.)):
            self.assertLessEqual(current['energy_interval_ohm'][k][0],energy)
            self.assertGreaterEqual(current['energy_interval_ohm'][k][1],energy)

    def test_same_field_exact_finite_source_functionals(self):
        from shapely.geometry import box
        sheet=self.fixture_sheet();sheets=[sheet,sheet]
        indices=[np.arange(4),np.arange(4,8)]
        field=np.array([[3,-5],[4,-3],[4,-3],[3,-5],[1,-7],[2,-5],[2,-5],[1,-7]],dtype=float)
        weights=np.array([1/3,1/6,1/3,1/6])
        rhs=np.repeat(np.r_[weights,-weights][:,None],2,axis=1)
        profile=[(0,box(0,0,1,1),1),(1,box(0,0,1,1),-1)]
        loads,net,receipt=finite_source_loads(sheets,indices,field,rhs,[profile,profile])
        self.assertEqual(loads,[[F(7,2),F(-4)],[F(-3,2),F(6)]])
        self.assertEqual(net,[[1,1],[-1,-1]])
        self.assertEqual([sum(row[k] for row in loads) for k in range(2)],[2,2])
        bad=[indices[0].copy(),indices[1]];bad[0][0]=-1
        with self.assertRaisesRegex(ValueError,'non-unit'):finite_source_loads(sheets,bad,field,rhs,[profile,profile])
        partial=[(0,box(0,0,.5,1),1),(1,box(0,0,1,1),-1)]
        with self.assertRaisesRegex(ValueError,'partially'):finite_source_loads(sheets,indices,field,rhs,[partial,profile])

    def test_imbalanced_raw_ports_have_nonzero_collar_shift(self):
        raw=[F(3,2),F(-1,2)] # nonzero mean: a constant projector alone hides it
        balanced,shift=balanced_collar_reference(raw,[2,8])
        self.assertEqual(balanced,[F(1),F(-1)])
        self.assertEqual(F(shift),F(5,2))
        self.assertGreater(shift,0)
        with self.assertRaises(ValueError):green_work(raw,[1,0],2,[0,0],[0,0],[0,0])

    def test_foil_extension_zeroes_every_other_band(self):
        values=[2,3,4,5,6,7]
        self.assertEqual(foil_extension_trace(values,1,3,1),[0,0,3,4,0,0])
        with self.assertRaises(ValueError):foil_extension_trace(values,3,3,1)

    def test_fractional_coefficients_are_enclosed_before_energy(self):
        matrix=np.array([[2.,-1.],[-1.,2.]])
        x=[F(1,3),F(-2,7)]
        exact=2*x[0]**2-2*x[0]*x[1]+2*x[1]**2
        self.assertGreaterEqual(F(quadratic_upper(matrix,x)),exact)

    def test_impossible_mismatch_is_rejected_not_clipped(self):
        with self.assertRaisesRegex(ValueError,'negative'):
            mismatch_interval([1,1],[1,1],[-2,-2])
        self.assertEqual(mismatch_interval([1,2],[1,2],[-2,-1]),[0.,2.])
        with self.assertRaisesRegex(ValueError,'complete gap'):
            mismatch_interval([2,2],[2,2],[0,0],3)
        with self.assertRaisesRegex(ValueError,'summed'):
            check_complete_mismatch([[2,3],[2,3]],3)


if __name__=='__main__':unittest.main()
