"""Physical sheet/shared-barrel fixtures, including finite interface loading."""
import math
import json
from pathlib import Path
import unittest

import numpy as np
import shapely
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box
from scipy.sparse import block_diag, coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.sparse.linalg import splu

from scripts.pcbgen.sheet_mesh import Sheet, make_cells, make_adaptive_cells, barrel_edges
from scripts.pcbgen.sheet_flux import FluxSheet


RHO = 1.7241e-5*(1+.003947*50)
SHEET = RHO/.07


def solve(matrix, rhs):
    if connected_components(matrix, directed=False, return_labels=False) != 1:
        raise ValueError('disconnected physical sheet')
    voltage = np.zeros(matrix.shape[0])
    voltage[1:] = splu(matrix[1:, 1:]).solve(rhs[1:])
    if np.max(np.abs(matrix@voltage-rhs)) > 1e-7:
        raise ValueError('physical current conservation failed')
    return voltage


def multilayer(sheets, bridges):
    offsets = np.cumsum([0]+[len(s.xy) for s in sheets])[:-1]
    base = block_diag([s.matrix for s in sheets], format='csc')
    rows, cols, values, receipts = barrel_edges(sheets, offsets, bridges, RHO, 1.6, .025, SHEET)
    return base+coo_matrix((values, (rows, cols)), shape=base.shape).tocsc(), offsets, receipts


class SheetMeshTests(unittest.TestCase):
    def test_local_quadtree_shared_faces_and_fixed_source_under_origin_change(self):
        copper=box(0,0,4,3);patch=box(.225,.225,.475,.475)
        sink=LineString([(4,0),(4,3)])
        values=[]
        for coarse,fine,origin in ((.5,.125,(0,0)),(.25,.0625,(0,0)),(.25,.0625,(.017,.031))):
            cells=make_adaptive_cells(copper.bounds,coarse,fine,patch.buffer(.2),origin)
            sheet=Sheet(copper,cells,SHEET,source_patches=[patch]);trial=FluxSheet(sheet,SHEET)
            source=trial.area_current(patch,1.);fixed=trial.boundary_current(sink,1.)
            rhs=sheet.area_load(patch)-sheet.line_load(sink);voltage=solve(sheet.matrix,rhs)
            result,_=trial.reconstruct(fixed,voltage,source)
            self.assertLess(result['maximum_triangle_divergence_residual_A'],1e-8)
            self.assertLessEqual(float(rhs@voltage),result['joule_upper_ohm']+1e-12)
            values.append(result['joule_upper_ohm'])
        self.assertLess(abs(values[-1]-values[-2])/values[-1],.02)

    def test_fixed_main_patch_has_exact_rt_source_under_origin_refinement(self):
        copper = box(0, 0, 2, 2)
        patch = box(.225, .225, .475, .475)
        sink = LineString([(2, 0), (2, 2)])
        results = []
        for fine, origin in ((.125, (0, 0)), (.0625, (0, 0)), (.0625, (.017, .031))):
            mesh = Sheet(copper, make_cells(copper.bounds, .5, fine, patch.buffer(.3), origin),
                         SHEET, source_patches=[patch])
            trial = FluxSheet(mesh, SHEET)
            sources = trial.area_current(patch, 1)
            self.assertAlmostEqual(sources.sum(), 1, places=11)
            rhs = mesh.area_load(patch)-mesh.line_load(sink)
            voltage = solve(mesh.matrix, rhs)
            receipt, _ = trial.reconstruct(trial.boundary_current(sink, 1), voltage, sources)
            results.append((rhs@voltage, receipt['joule_upper_ohm']))
            self.assertGreaterEqual(results[-1][1]+1e-12, results[-1][0])
        self.assertLess(results[1][1]-results[1][0], results[0][1]-results[0][0])
        self.assertAlmostEqual(FluxSheet.one_face_source_lift_ohm(patch, RHO, .07),
                               RHO*.07/(3*.0625), places=14)
        bare = Sheet(copper, make_cells(copper.bounds, .5, .125), SHEET)
        with self.assertRaisesRegex(ValueError, 'whole triangles'):
            FluxSheet(bare, SHEET).area_current(patch, 1)

    def test_retained_native_j900001_pad2_cut_has_finite_refining_energy(self):
        data = json.loads((Path(__file__).parent/'fixtures/ground-gh-native.json').read_text())
        self.assertEqual(data['actual_courtyard_cut_mm'], [119.875, 84.905])
        geometry = data['native_local_common_copper']
        copper = Polygon(geometry['shell'], geometry['holes'])
        source = LineString(data['source_face_mm']); sink = LineString(data['return_face_mm'])
        results = []
        for fine, origin in ((.125, (0, 0)), (.0625, (0, 0)), (.0625, (.017, .031))):
            mesh = Sheet(copper, make_cells(copper.bounds, .5, fine, source.buffer(.5), origin), SHEET)
            rhs = mesh.line_load(source)-mesh.line_load(sink)
            voltage = solve(mesh.matrix, rhs); trial = FluxSheet(mesh, SHEET)
            receipt, _ = trial.reconstruct(trial.boundary_current(source, -1)+trial.boundary_current(sink, 1), voltage)
            results.append((float(rhs@voltage), receipt['joule_upper_ohm']))
        self.assertTrue(all(upper >= lower for lower, upper in results))
        self.assertLess(results[1][1]-results[1][0], results[0][1]-results[0][0])
        self.assertLess(abs(results[2][0]-results[1][0]), max(upper-lower for lower, upper in results))

    def test_conserved_flux_energy_matches_analytic_rectangle(self):
        copper = box(119, 83, 125, 86)
        mesh = Sheet(copper, make_cells(copper.bounds, 1, .25, box(120, 84, 122, 85)), SHEET)
        source = LineString([(119, 83), (119, 86)]); sink = LineString([(125, 83), (125, 86)])
        rhs = mesh.line_load(source)-mesh.line_load(sink)
        voltage = solve(mesh.matrix, rhs)
        trial = FluxSheet(mesh, SHEET)
        receipt, _ = trial.reconstruct(trial.boundary_current(source, -1)+trial.boundary_current(sink, 1), voltage)
        self.assertAlmostEqual(receipt['joule_upper_ohm'], 2*SHEET, places=11)

    def test_cut_has_conserved_upper_energy_and_refinement_gap(self):
        copper = box(0, 0, 4, 3).difference(box(0, 1.375, 1.7, 1.625))
        source = LineString([(1.7, 1.375), (1.7, 1.625)])
        sink = LineString([(4, 0), (4, 3)])
        gaps = []
        for fine in (.125, .0625):
            mesh = Sheet(copper, make_cells(copper.bounds, .5, fine, source.buffer(.5)), SHEET)
            rhs = mesh.line_load(source)-mesh.line_load(sink)
            voltage = solve(mesh.matrix, rhs)
            trial = FluxSheet(mesh, SHEET)
            receipt, _ = trial.reconstruct(trial.boundary_current(source, -1)+trial.boundary_current(sink, 1), voltage)
            lower = rhs@voltage; upper = receipt['joule_upper_ohm']
            self.assertGreater(upper, lower)
            gaps.append(upper-lower)
        self.assertLess(gaps[-1], gaps[0])

    def test_rectangle_with_finite_faces_and_adaptive_shared_boundaries(self):
        copper = box(0, 0, 6, 3)
        feature = box(1.2, .7, 2.6, 2.2)
        for origin in ((0, 0), (.17, .09)):
            mesh = Sheet(copper, make_cells(copper.bounds, 1, .25, feature, origin), SHEET)
            rhs = mesh.line_load(LineString([(0, 0), (0, 3)]))-mesh.line_load(LineString([(6, 0), (6, 3)]))
            resistance = rhs@solve(mesh.matrix, rhs)
            self.assertAlmostEqual(resistance, SHEET*6/3, places=11)
            self.assertLess(abs(mesh.area_error_mm2), 1e-8)

    def test_actual_width_cut_can_span_multiple_cells(self):
        copper = box(0, 0, 4, 3).difference(box(0, 1.375, 1.7, 1.625))
        face = LineString([(1.7, 1.375), (1.7, 1.625)])
        results = []
        for fine, origin in ((.125, (0, 0)), (.0625, (0, 0)), (.0625, (.017, .031))):
            mesh = Sheet(copper, make_cells(copper.bounds, .5, fine, face.buffer(.4), origin), SHEET)
            rhs = mesh.line_load(face)-mesh.line_load(LineString([(4, 0), (4, 3)]))
            self.assertAlmostEqual(rhs.sum(), 0, places=12)
            results.append(rhs@solve(mesh.matrix, rhs))
        self.assertLess(abs(results[-1]-results[-2])/results[-1], .025)

    def test_disconnected_gap_is_not_numerically_bridged(self):
        copper = shapely.union_all([box(0, 0, 1, 1), box(1.05, 0, 2, 1)])
        mesh = Sheet(copper, make_cells(copper.bounds, .5, .125), SHEET)
        self.assertEqual(connected_components(mesh.matrix, directed=False, return_labels=False), 2)

    def test_finite_patch_must_be_supported_by_real_copper(self):
        copper = box(0, 0, 2, 2).difference(Point(1, 1).buffer(.15))
        mesh = Sheet(copper, make_cells(copper.bounds, .5, .125), SHEET)
        with self.assertRaisesRegex(ValueError, 'not fully represented'):
            mesh.area_load(box(.9, .9, 1.1, 1.1))

    def test_annular_sheet_and_one_finite_barrel_match_analytic(self):
        ri, ro = .15, .6
        hole = Point(0, 0).buffer(ri/math.cos(math.pi/128), quad_segs=32)
        copper = Point(0, 0).buffer(ro, quad_segs=32).difference(hole)
        cells = make_cells(copper.bounds, .5, .0625, copper)
        sheets = [Sheet(copper, cells, SHEET) for _ in range(2)]
        matrix, offsets, receipts = multilayer(sheets, [{'uuid': 'one', 'x_mm': 0, 'y_mm': 0, 'drill_mm': 2*ri}])
        lines = []
        for a, b in sheets[0].boundary_edges:
            xy = sheets[0].xy[[a, b]]
            if np.min(np.linalg.norm(xy, axis=1)) > ro-.001:
                lines.append(xy.tolist())
        electrode = MultiLineString(lines)
        rhs = np.r_[sheets[0].line_load(electrode), -sheets[1].line_load(electrode)]
        resistance = rhs@solve(matrix, rhs)
        analytic = RHO*1.6/(2*math.pi*ri*.025)+2*SHEET*math.log(ro/ri)/(2*math.pi)
        self.assertLess(abs(resistance-analytic)/analytic, .005)
        self.assertAlmostEqual(receipts[0]['represented_angle_rad'], 2*math.pi, places=8)

    def test_actual_4mm_land_and_25_shared_barrels(self):
        bridges = [{'uuid': f'{i}:{j}', 'x_mm': .7*i, 'y_mm': .7*j, 'drill_mm': .3}
                   for i in range(-2, 3) for j in range(-2, 3)]
        holes = shapely.union_all([Point(b['x_mm'], b['y_mm']).buffer(.15/math.cos(math.pi/128), quad_segs=32) for b in bridges])
        copper = box(-2, -2, 2, 2).difference(holes)
        cells = make_cells(copper.bounds, .5, .125, copper)
        sheets = [Sheet(copper, cells, SHEET) for _ in range(2)]
        matrix, offsets, receipts = multilayer(sheets, bridges)
        source = sheets[0].area_load(box(.225, .225, .475, .475))
        sink = sheets[1].line_load(box(-2, -2, 2, 2).boundary)
        rhs = np.r_[source, -sink]
        resistance = rhs@solve(matrix, rhs)
        ideal_barrel = RHO*1.6/(2*math.pi*.15*.025)
        self.assertGreater(resistance, ideal_barrel/25)
        self.assertLess(resistance, ideal_barrel)
        self.assertEqual(len(receipts), 25)
        self.assertTrue(all(abs(r['represented_angle_rad']-2*math.pi) < 1e-7 for r in receipts))

    def test_unequal_contacts_share_one_barrel_and_reciprocal_voltage_bound(self):
        hole = Point(0, 0).buffer(.15/math.cos(math.pi/128), quad_segs=32)
        copper = box(-1, -1, 1, 1).difference(hole)
        cells = make_cells(copper.bounds, .5, .125, copper)
        sheets = [Sheet(copper, cells, SHEET) for _ in range(2)]
        matrix, offsets, receipts = multilayer(sheets, [{'uuid': 'shared', 'x_mm': 0, 'y_mm': 0, 'drill_mm': .3}])
        sink = sheets[1].line_load(LineString([(-1, -1), (1, -1)]))
        first = np.r_[sheets[0].area_load(box(-.8, -.2, -.55, .05)), -sink]
        second = np.r_[sheets[0].area_load(box(.45, .4, .7, .65)), -sink]
        va = solve(matrix, first); vb = solve(matrix, second)
        self.assertAlmostEqual(first@vb, second@va, places=11)
        barrel = RHO*1.6/(2*math.pi*.15*.025)
        self.assertGreater(first@vb, barrel*.5)
        self.assertEqual(len(receipts), 1)
        self.assertAlmostEqual(receipts[0]['represented_angle_rad'], 2*math.pi, places=8)
        # The largest reciprocal voltage span covers arbitrary load location,
        # including nodes outside either header electrode.
        forcing = np.zeros(len(va)); forcing[len(sheets[0].xy)//2] = 4.6
        forcing[-1] = -4.6
        actual = abs(first@solve(matrix, forcing))
        self.assertLessEqual(actual, 4.6*(max(va)-min(va))+1e-10)


if __name__ == '__main__':
    unittest.main()
