"""Analytic and adversarial geometry/energy tests; no retained cache needed."""
from fractions import Fraction as F
import itertools
from types import SimpleNamespace
import unittest
import numpy as np
from scripts.pcbgen.partial_cell_energy import (
    area, triangle, intersect, erode, area_upper, covered_fraction, Budget,
    WorkCap, CanonicalChart, ConservativeIndex, p1_energy_interval, exact)


T = triangle([(0, 0), (2, 0), (0, 2)])


def sheet(points, triangles, faces=None):
    return SimpleNamespace(metric_xy=np.asarray(points, dtype=np.longdouble),
        triangles=np.asarray(triangles), metric_factors=np.ones(len(triangles)),
        interface_faces=faces or {})


def budget(**kw):
    return Budget({'clips': kw.get('clips', 100), 'overlap_checks': kw.get('overlap_checks', 100)})


class PartialCellTests(unittest.TestCase):
    def test_exact_half_sliver_and_boundary_contact(self):
        self.assertEqual(area(intersect(T, T)), 2)
        half = triangle([(0, 0), (2, 0), (0, 1)])
        self.assertEqual(area(intersect(T, half)), 1)
        tiny = F(1, 10**30)
        sliver = triangle([(0, 0), (2, 0), (0, tiny)])
        self.assertEqual(area(intersect(T, sliver)), tiny)
        touching = triangle([(2, 0), (3, 0), (2, 1)])
        self.assertEqual(area(intersect(T, touching)), 0)
        self.assertEqual(area(intersect(tuple(reversed(T)), half)), 1)

    def test_translation_and_all_vertex_box_corners(self):
        eps = F(1, 100)
        nominal = triangle([(900, 899), (902, 899), (900, 901)])
        inside = erode(nominal, eps)
        upper = area_upper(nominal, eps)
        areas = []
        for signs in itertools.product((-1, 1), repeat=6):
            actual = triangle([(p[0]+eps*signs[2*i], p[1]+eps*signs[2*i+1]) for i, p in enumerate(nominal)])
            self.assertEqual(area(intersect(inside, actual)), area(inside))
            self.assertLessEqual(area(actual), upper)
            areas.append(area(actual))
        # Nominal-area division would overstate the fraction on this member.
        self.assertGreater(max(areas), area(nominal))
        self.assertLess(area(inside)/upper, area(inside)/area(nominal))

    def test_uncertain_thin_cell_and_negative_epsilon_fail(self):
        with self.assertRaisesRegex(ValueError, 'orientation'):
            area_upper([(0, 0), (1, 0), (1, F(1, 10**8))], F(1, 10**7))
        with self.assertRaises(ValueError):
            erode(T, -1)

    def test_disjoint_current_pieces_and_duplicate_geometry(self):
        a = triangle([(0, 0), (1, 0), (0, 2)])
        b = triangle([(1, 0), (2, 0), (0, 2)])
        fraction, *_ = covered_fraction(T, 0, T, [(1, a, 0), (2, b, 0)], [], budget())
        self.assertEqual(fraction, 1)
        with self.assertRaisesRegex(ValueError, 'current witness overlap'):
            covered_fraction(T, 0, T, [(1, a, 0), (2, a, 0)], [], budget())
        with self.assertRaisesRegex(ValueError, 'duplicate current'):
            covered_fraction(T, 0, T, [(1, a, 0), (1, b, 0)], [], budget())

    def test_already_counted_potential_overlap_fails(self):
        with self.assertRaisesRegex(ValueError, 'potential overlap'):
            covered_fraction(T, 0, T, [(1, T, 0)], [(7, T)], budget())
        neighbor = triangle([(2, 0), (2, 2), (0, 2)])
        self.assertEqual(covered_fraction(T, 0, T, [(1, T, 0)], [(7, neighbor)], budget())[0], 1)

    def test_caps_do_not_produce_a_partial_success(self):
        with self.assertRaises(WorkCap):
            covered_fraction(T, 0, T, [(1, T, 0)], [], budget(clips=0))
        with self.assertRaises(WorkCap):
            covered_fraction(T, 0, T, [(1, T, 0)], [(2, [(2, 0), (2, 2), (0, 2)])], budget(overlap_checks=0))

    def test_affine_energy_two_profiles_gauge_and_metric_cost(self):
        for scale in (F(1), F(2)):
            values = [0, 2*scale, 0]
            target = 2*scale**2
            self.assertEqual(p1_energy_interval(T, values, [0]*3, 1), (target, target))
            self.assertEqual(p1_energy_interval(T, [x+10**30 for x in values], [0]*3, 1), (target, target))
            lo, hi = p1_energy_interval(T, values, [F(1, 100)]*3, 1, F(101, 100))
            self.assertLess(lo, target)
            self.assertGreater(hi, target)
            for signs in itertools.product((-1, 1), repeat=3):
                trial = [x+F(s, 100) for x, s in zip(values, signs)]
                actual = p1_energy_interval(T, trial, [0]*3, 1)[0]
                self.assertLessEqual(lo, actual)
                self.assertGreaterEqual(hi, actual)

    def test_coefficient_errors_cannot_be_omitted(self):
        lo, hi = p1_energy_interval(T, [0, 1, 0], [1, 0, 0], 1)
        self.assertEqual(lo, 0)
        self.assertGreater(hi, 1)
        with self.assertRaises(ValueError):
            p1_energy_interval(T, [0, 1, 0], [-1, 0, 0], 1)

    def test_exact_longdouble_conversion_keeps_extra_bits(self):
        value = np.longdouble(1)+np.finfo(np.longdouble).eps
        self.assertEqual(exact(value), 1+exact(np.finfo(np.longdouble).eps))
        self.assertNotEqual(exact(value), exact(float(value)))

    def test_grid_reconstruction_and_eta_mutation(self):
        s = sheet([[0, 0], [1, 0], [0, 1]], [[0, 1, 2]])
        chart = CanonicalChart(s, [])
        nominal, canonical, eps = chart.cell(0)
        self.assertEqual(canonical, tuple(tuple(map(F, p)) for p in [[0, 0], [1, 0], [0, 1]]))
        self.assertGreater(eps, 0)
        s.metric_xy[1, 0] += np.longdouble('1e-10')
        with self.assertRaisesRegex(ValueError, 'eta'):
            CanonicalChart(s, []).cell(0)

    def interface_fixture(self):
        # A non-grid affine interface vertex with retained extended-precision t.
        t = np.longdouble('0.33333333333333333334')
        vertices = [[0, 0], [float(.7), 0], [0, float(.9)]]
        middle = np.asarray(vertices[0], dtype=np.longdouble)+t*np.asarray(vertices[1], dtype=np.longdouble)
        coords = np.vstack((np.asarray(vertices, dtype=np.longdouble), middle))
        faces = {(0, 0): [{'vertices': (0, 3), 'parameters': (np.longdouble(0), t)},
                           {'vertices': (3, 1), 'parameters': (t, np.longdouble(1))}],
                 (0, 1): [{'vertices': (1, 2), 'parameters': (0, 1)}],
                 (0, 2): [{'vertices': (2, 0), 'parameters': (0, 1)}]}
        return sheet(coords, [[0, 3, 2], [3, 1, 2]], faces), [{'centre': [0, 0], 'relative': vertices}], t

    def test_interface_reconstruction_preserves_retained_t(self):
        s, interfaces, t = self.interface_fixture()
        chart = CanonicalChart(s, interfaces)
        self.assertEqual(chart.vertex(3)[1][0], exact(t)*exact(.7))
        self.assertNotEqual(chart.vertex(3)[1][0], F(round(exact(t)*exact(.7)*10**9), 10**9))
        s.metric_xy[3, 0] = np.longdouble(round(float(s.metric_xy[3, 0]), 9))
        with self.assertRaisesRegex(ValueError, 'eta'):
            CanonicalChart(s, interfaces).vertex(3)

    def test_interface_gap_and_exact_conflict_fail(self):
        s, interfaces, _ = self.interface_fixture()
        s.interface_faces[(0, 0)][0]['parameters'] = (0, F(1, 4))
        with self.assertRaisesRegex(ValueError, 'conflicting|telescope'):
            CanonicalChart(s, interfaces)
        s, interfaces, _ = self.interface_fixture()
        del s.interface_faces[(0, 2)]
        with self.assertRaisesRegex(ValueError, 'sector'):
            CanonicalChart(s, interfaces)

    def test_broad_phase_has_every_exact_small_fixture_overlap(self):
        near = np.nextafter(np.longdouble(1), np.longdouble(0))
        points = [[0, 0], [1, 0], [0, 1], [near, 0], [2, 0], [near, 1], [3, 0], [4, 0], [3, 1]]
        s = sheet(points, [[0, 1, 2], [3, 4, 5], [6, 7, 8]])
        index = ConservativeIndex(s)
        for i, ids in enumerate(s.triangles):
            candidates = set(index.query_box(index.boxes[i]))
            p = tuple(tuple(map(exact, s.metric_xy[j])) for j in ids)
            for j, other in enumerate(s.triangles):
                q = tuple(tuple(map(exact, s.metric_xy[k])) for k in other)
                if area(intersect(p, q)):
                    self.assertIn(j, candidates)


if __name__ == '__main__':
    unittest.main()
