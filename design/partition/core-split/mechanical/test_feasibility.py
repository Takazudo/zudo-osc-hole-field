import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('feasibility',HERE/'feasibility.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)

class FeasibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=f.build()
    def test_strict_gap_proposals_do_not_relax_requirement(self):
        rows=self.report['strict_gap_proposals']
        self.assertEqual(len(rows),40)
        for r in rows:
            self.assertAlmostEqual(r['before_gap_mm'],.349999)
            self.assertGreaterEqual(r['minimum_same_face_gap_after_mm'],.35)
            self.assertEqual(sum(abs(v) for v in r['delta_xy_mm']),.001)
            self.assertFalse(r['new_strict_conflicts']);self.assertTrue(r['outline_pass'])
            self.assertTrue(r['affected_pad_identities'])
    def test_continuous_translation_blocker_and_nonempty_satellite(self):
        search=self.report['endpoint_placement_search']
        for r in search['two-A']:self.assertFalse(r['continuous_translation_screen']['feasible_event_origins_mm'])
        self.assertTrue(search['two-B'][0]['continuous_translation_screen']['feasible_event_origins_mm'])
        self.assertFalse(search['two-B'][1]['continuous_translation_screen']['feasible_event_origins_mm'])
    def test_event_sweep_handles_contact_and_subgrid_opening(self):
        # 0.1 mm slot in allowed x region: no integer origin; continuous search must find it.
        rows=[('left',[4,8,10.2,246]),('right',[101.3,8,314,246])]
        result=f.continuous_origins(91,200,rows)['feasible_event_origins_mm']
        self.assertIn([10.2,8.3],result)
        self.assertFalse(f.continuous_origins(91.2,200,rows)['feasible_event_origins_mm'])
    def test_stack_and_edge_boundaries(self):
        self.assertFalse(self.report['cardinal_edge_escape']['fitting_91x28_rectangles_mm'])
        options=self.report['stack_options']
        self.assertAlmostEqual(28+1.6+5,options['body_allowance_clear']['required_pitch_mm'])
        self.assertEqual(options['body_allowance_clear']['contact_margin_mm'],0)
        self.assertEqual(self.report['service_wire_boundary']['qualified_loop_length_mm'],None)
    def test_nonrectangular_geometry_is_not_silently_bounded(self):
        with self.assertRaises(ValueError):f.box([[[0,0],[1,0],[1,1],[.5,.5],[0,1]]])
    def test_outputs_are_deterministic(self):
        self.assertEqual(self.report,f.build())
        self.assertEqual(f.svg(self.report),f.svg(f.build()))

if __name__=='__main__':unittest.main()
