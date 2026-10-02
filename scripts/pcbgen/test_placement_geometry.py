"""Courtyards may not bridge concave cutouts or borrow the wrong board face."""
import math
import unittest
from scripts.pcbgen.placement_geometry import Box, inside_outline, placement_side_matches


class CourtyardContainmentTests(unittest.TestCase):
    def test_long_concave_edges_cross_box_despite_outside_midpoints(self):
        outline = [(-20,-20),(20,-20),(20,20),(-20,20),(-20,6),(5,5),(-20,4)]
        for points in (outline, list(reversed(outline))):
            self.assertFalse(inside_outline(Box(0,0,10,10), points, .25))
            self.assertTrue(inside_outline(Box(10,0,12,10), points, .25))

    def test_nonintersecting_notch_tip_still_requires_edge_clearance(self):
        outline = [(-20,-20),(20,-20),(20,20),(-20,20),(-20,12),(5,10.1),(-20,11)]
        self.assertFalse(inside_outline(Box(0,0,10,10), outline, .25))
        self.assertTrue(inside_outline(Box(0,0,10,9.8), outline, .25))

    def test_exact_clearance_and_existing_numeric_tolerance(self):
        outline = [(0,0),(20,0),(20,20),(0,20)]
        self.assertTrue(inside_outline(Box(.25,.25,19.75,19.75), outline, .25))
        self.assertFalse(inside_outline(Box(.25-2e-6,.25,19.75,19.75), outline, .25))
        self.assertFalse(inside_outline(Box(0,1,10,10), outline, 0))
        self.assertFalse(inside_outline(Box(-1,1,10,10), outline, 0))

    def test_diagonal_edge_distance_and_translation(self):
        outline = [(0,0),(20,0),(0,20)]
        box = Box(1,1,9,9)
        self.assertTrue(inside_outline(box, outline, 1))
        self.assertFalse(inside_outline(Box(1,1,9.8,9.8), outline, .3))
        self.assertTrue(inside_outline(box.shift(30,-40), [(x+30,y-40) for x,y in outline], 1))

    def test_invalid_numeric_geometry_is_rejected(self):
        outline = [(0,0),(20,0),(20,20),(0,20)]
        for box, polygon, gap in ((Box(1,1,1,3),outline,0), (Box(1,1,3,3),outline,-1),
                                  (Box(1,1,math.inf,3),outline,0),
                                  (Box(1,1,3,3),[(0,0),(20,0),(math.nan,20)],0)):
            with self.subTest(box=box,gap=gap), self.assertRaises(ValueError):
                inside_outline(box,polygon,gap)


class PlacementFaceTests(unittest.TestCase):
    def test_absent_and_explicit_source_face_agree(self):
        for side in ('F.Cu','B.Cu'):
            self.assertTrue(placement_side_matches(side,'',side))
            self.assertTrue(placement_side_matches(side,side,side))

    def test_actual_requested_and_template_region_must_agree(self):
        self.assertFalse(placement_side_matches('F.Cu','F.Cu','B.Cu'))
        self.assertFalse(placement_side_matches('F.Cu','B.Cu','F.Cu'))
        self.assertFalse(placement_side_matches('B.Cu','','F.Cu'))
        self.assertFalse(placement_side_matches('In1.Cu','','In1.Cu'))
