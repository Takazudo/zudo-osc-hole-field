"""Bounded additive search preserves geometry; these are synthetic, not native tests."""
import copy
import unittest
import numpy as np
from scripts.pcbgen.grid_router import Raster, route, copper_rows, island_mask
from scripts.pcbgen.test_grid_router import board, MM


class BoundedRasterTests(unittest.TestCase):
    def test_outside_island_vias_neither_wrap_nor_index_out_of_bounds(self):
        dump=board();raster=Raster(dump,res=.1,bounds_mm=(3,2,9,6))
        dump['vias']=[{'uuid':str(i),'xy':xy} for i,xy in enumerate(
            [(5*MM,4*MM),(2*MM,4*MM),(-50*MM,4*MM),(50*MM,4*MM)])]
        mask=island_mask(raster,dump,[str(i) for i in range(4)])
        j,i=raster.cell(5*MM,4*MM)
        self.assertTrue(mask[:,j,i].all())
        self.assertEqual(int(mask.sum()),len(raster.layers))

    def test_off_window_geometry_has_empty_slices(self):
        raster=Raster(board(),res=.1,bounds_mm=(3,2,9,6))
        for lo,hi in [((-20*MM,3*MM),(-19*MM,4*MM)),
                      ((20*MM,3*MM),(21*MM,4*MM)),
                      ((4*MM,-20*MM),(5*MM,-19*MM)),
                      ((4*MM,20*MM),(5*MM,21*MM))]:
            sl=raster.window(lo,hi)
            self.assertEqual(raster.label[0][sl].size,0)

    def test_local_occupancy_matches_full_lattice_and_keeps_crossing_copper(self):
        dump=board(walls=((6,'B.Cu'),))
        full=Raster(dump,res=.1)
        local=Raster(dump,res=.1,bounds_mm=(3.03,2.07,8.91,6.02))
        x=int(round((local.x0-full.x0)/full.step))
        y=int(round((local.y0-full.y0)/full.step))
        sl=(slice(y,y+local.h),slice(x,x+local.w))
        np.testing.assert_array_equal(local.label,full.label[:,sl[0],sl[1]])
        np.testing.assert_array_equal(local.fixed_label,full.fixed_label[:,sl[0],sl[1]])
        np.testing.assert_array_equal(local.hole,full.hole[sl])
        self.assertTrue((local.d_edge<=full.d_edge[sl]+1e-9).all())
        self.assertLess(local.label.nbytes,full.label.nbytes)
        self.assertTrue((local.label[-1]==local.net_id['B']).any())

    def test_additive_path_stays_inside_window_and_input_is_unchanged(self):
        dump=board(walls=((6,'B.Cu'),));original=copy.deepcopy(dump)
        results,removed=route(dump,res=.1,clearance=.2,signal_width=.2,
                              bounds_mm=(0,2,12,6),log=lambda m:None)
        self.assertTrue(any(r['path'] for r in results))
        self.assertEqual(removed,[])
        self.assertEqual(dump,original)
        rows,_=copper_rows(results,'fixture','bounded')
        for row in rows:
            points=[row['at_nm']] if row['kind']=='via' else [row['start_nm'],row['end_nm']]
            for x,y in points:
                self.assertGreater(x,0);self.assertLess(x,12*MM)
                self.assertGreater(y,2*MM);self.assertLess(y,6*MM)

    def test_rip_up_and_invalid_windows_are_rejected(self):
        for kwargs in ({'rip':['A']},{'rip_first':True},{'rrr_rounds':1}):
            with self.assertRaisesRegex(ValueError,'additive only'):
                route(board(),bounds_mm=(1,1,11,7),**kwargs)
        for bounds in [(4,1,3,7),(1,1,11),(1,1,float('inf'),7),(50,50,60,60)]:
            with self.assertRaises(ValueError):
                Raster(board(),bounds_mm=bounds)

    def test_native_island_members_outside_window_are_not_discarded(self):
        dump=board();original=copy.deepcopy(dump['islands'])
        raster=Raster(dump,res=.1,bounds_mm=(3,2,9,6))
        self.assertEqual(raster.dump['islands'],original)
        self.assertEqual(len(raster.dump['pads']),2)
        self.assertEqual(raster.dump['board_sha256'],dump['board_sha256'])


if __name__=='__main__':
    unittest.main()
