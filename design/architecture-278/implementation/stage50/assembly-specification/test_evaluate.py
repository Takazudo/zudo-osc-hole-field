import importlib.util
import json
import math
from pathlib import Path
import unittest
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stage50_evaluate',HERE/'evaluate.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class SpecificationTests(unittest.TestCase):
    def test_external_corner_distance(self):
        self.assertAlmostEqual(m.gap((3,4),(0,0,0,0),1),4)
    def test_overlap_and_touch_are_not_clear(self):
        self.assertEqual(m.gap((0,0),(-1,-1,1,1),.3),-.3)
        self.assertAlmostEqual(m.gap((2,0),(-1,-1,1,1),1),0)
    def test_invalid_or_unknown_geometry_rejected(self):
        for bounds in [(0,0,math.nan,1),(1,0,0,1)]:
            with self.assertRaises(ValueError):m.gap((0,0),bounds,.3)
    def test_recorded_result_replays(self):
        self.assertEqual(m.evaluate(),json.loads((HERE/'result.json').read_text()))
    def test_no_identity_or_assembly_promotion(self):
        result=m.evaluate()
        self.assertEqual(result['populated_identity'],'UNRESOLVED')
        self.assertEqual(result['assembly_acceptance'],'UNRESOLVED')
        self.assertLess(result['ink_plug_screen_margin_above_0_35_mm'],0)
    def test_full_rotation_bound(self):
        result=m.evaluate();bound=result['all_rotation_combined_radial_error_budget_mm']
        # Independent corner sweep: circumcircle bound must be conservative.
        for degrees in range(360):
            a=math.radians(degrees)
            for x,y in [(-.85,-.45),(-.85,.45),(.85,-.45),(.85,.45)]:
                px=270.31+x*math.cos(a)-y*math.sin(a)
                py=133.94+x*math.sin(a)+y*math.cos(a)
                self.assertGreaterEqual(math.hypot(px-271.32,py-132.8)-.3+1e-9,bound)
    def test_retained_source_and_history_bindings(self):m.verify_bindings()
if __name__=='__main__':unittest.main()
