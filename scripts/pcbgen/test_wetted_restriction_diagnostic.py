"""Exact analytic source-trace and conservative subset regression fixtures."""
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
import numpy as np
from scripts.pcbgen.wetted_restriction_diagnostic import (
    bubble_floor, corrected_lower, rt_energy_lower, binary_p1_energy_upper,
    axial_gap_lower, choose_cells_and_bubble, validate_links, validate_union, source_terms)


class WettedRestrictionTests(unittest.TestCase):
    def test_finite_face_load_and_depth_constant_bubble(self):
        # Unit cube rho=1; q=(x,0,1-z) is divergence-free. Uniform unit
        # incoming normal current on z=0 exits on x=1. psi=T(x)T(y),
        # T=2min(x,1-x), is zero on the return and lateral cut boundaries.
        # f(psi)=1/4; E(psi)=8/3; full current energy=2/3, including
        # the vertical source-lift component. No terminal-total shortcut.
        bound=bubble_floor(F(1,4),F(8,3))
        self.assertEqual(F(bound),F(3,128))
        self.assertLessEqual(F(bound),F(2,3))
        self.assertEqual(bubble_floor(F(-1,4),F(8,3)),bound)
        # Same psi, equal opposite face densities at z=0 and z=1: exact
        # boundary functionals cancel even though a nonzero current can flow.
        self.assertEqual(bubble_floor(0,F(8,3)),0)
        self.assertEqual(bubble_floor(0,0),0)
        with self.assertRaises(ValueError):bubble_floor(1,0)

    def test_exact_rt_and_p1_triangle_energies(self):
        p=np.array([[0,0],[1,0],[0,1]],dtype=np.longdouble)
        # Unit constant x current, exact outward integrated face currents.
        self.assertEqual(rt_energy_lower(p,.5,[1,-1,0],1,1,1),.5)
        self.assertEqual(binary_p1_energy_upper(p,.5,[1,0,0],1,1,1),1)
        self.assertEqual(binary_p1_energy_upper(p,.5,[0,1,1],1,1,1),1)
        self.assertEqual(binary_p1_energy_upper(p,.5,[1,1,1],1,1,1),0)
        self.assertLessEqual(rt_energy_lower(p,.5,[1,-1,0],1,1,1.1),.5)
        self.assertGreaterEqual(binary_p1_energy_upper(p,.5,[1,0,0],1,1,1.1),1)

    def test_whole_stars_and_native_boundaries_define_zero_extension(self):
        xy=np.array([[0,0],[1,0],[1,1],[0,1],[.5,.5]],dtype=np.longdouble)
        tri=np.array([[0,1,4],[1,2,4],[2,3,4],[3,0,4]])
        sheet=SimpleNamespace(xy=xy,metric_xy=xy,triangles=tri)
        selected,nodal=choose_cells_and_bubble(sheet,(-1,-1,2,2))
        self.assertTrue(selected.all())
        np.testing.assert_array_equal(nodal,[0,0,0,0,1])
        selected,nodal=choose_cells_and_bubble(sheet,(.1,.1,.9,.9))
        # Every centroid can be near the rectangle, but no whole triangle fits.
        self.assertFalse(selected.any());self.assertEqual(nodal.sum(),0)

    def test_complete_norm_correction_cannot_raise_a_lower_energy(self):
        self.assertLessEqual(F(corrected_lower(1,F(1,100))),F(81,100))
        self.assertGreater(F(corrected_lower(1,F(1,100))),F(809999,1000000))
        self.assertEqual(corrected_lower(1,4),0)
        self.assertEqual(corrected_lower(0,0),0)

    def test_linked_artifact_and_disjoint_identity_guards(self):
        from pathlib import Path
        from copy import deepcopy
        from shapely.geometry import box,mapping
        manifest={k:k+'.json' for k in ('current_mesh','profiles','native','full_receipt','fields')}
        manifest['input_sha256']={path:'hash:'+key for key,path in manifest.items()}
        pair={'input_sha256':{str(Path(manifest[k]).resolve()):manifest['input_sha256'][manifest[k]] for k in ('current_mesh','profiles','native','full_receipt')},
              'raw_field_artifacts':{'current-fields.npz':manifest['input_sha256'][manifest['fields']]}}
        validate_links(manifest,pair)
        bad=deepcopy(manifest);bad['current_mesh']='foreign'
        with self.assertRaises(ValueError):validate_links(bad,pair)
        ownership=[{'uuid':str(i)} for i in range(75)]
        rows=[{'ref':ref,'layer':3,'tied_barrels':list(range(25*i,25*(i+1))),
               'maximum_wetting_geojson':mapping(box(i*10,0,i*10+4,4))}
              for i,ref in enumerate(('TP990031','TP990033','TP990035'))]
        self.assertEqual(validate_union(rows,ownership),75)
        bad=deepcopy(rows);bad[1]['tied_barrels']=bad[0]['tied_barrels']
        with self.assertRaisesRegex(ValueError,'two terminal'):validate_union(bad,ownership)
        bad=deepcopy(rows);bad[1]['maximum_wetting_geojson']=bad[0]['maximum_wetting_geojson']
        with self.assertRaisesRegex(ValueError,'overlapping'):validate_union(bad,ownership)

    def test_exact_signed_source_functional_and_partial_triangle_rejection(self):
        import shapely
        from shapely.geometry import box
        xy=np.array([[0,0],[1,0],[1,1],[0,1]],dtype=np.longdouble)
        tri=np.array([[0,1,2],[0,2,3]])
        polygons=shapely.polygons(np.asarray(xy[tri],dtype=float))
        sheet=SimpleNamespace(metric_xy=xy,triangles=tri,polygons=polygons,
                              tree=shapely.STRtree(polygons))
        selected=np.array([True,True]);nodal=np.array([0,1,1,0])
        full=box(0,0,1,1)
        loads,lifts,counts=source_terms(sheet,selected,nodal,
            [[(0,full,1)],[(0,full,-1)]],0,1,1)
        self.assertEqual(loads,[F(1,2),F(-1,2)])
        self.assertEqual(counts,[2,2])
        for value in lifts:
            self.assertLessEqual(F(value),F(1,3))
            self.assertGreater(F(value),F(333333,1000000))
        partial=box(0,0,.5,1)
        with self.assertRaisesRegex(ValueError,'exact complete grid triangle'):
            source_terms(sheet,selected,nodal,[[(0,partial,1)],[(0,full,-1)]],0,1,1)

    def test_shell_gap_lower_uses_balanced_trace_and_conservative_area(self):
        # One port per foil band, unit axial gap current. pi upper 22/7
        # and outward radius bounds make the result no greater than exact R.
        rows=[[1.,0.],[-1.,0.]];bands=[(0.,.1),(.9,1.)]
        result=axial_gap_lower(rows,bands,.15,1.)
        actual=.8/(np.pi*(.175**2-.15**2))
        self.assertGreater(result[0],0);self.assertLessEqual(result[0],actual)
        self.assertEqual(result[1],0)
        # A common port offset is annihilated by the exact balanced projector.
        shifted=axial_gap_lower([[3.,2.],[1.,2.]],bands,.15,1.)
        self.assertEqual(result,shifted)


if __name__=='__main__':unittest.main()
