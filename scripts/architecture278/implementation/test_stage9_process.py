import copy
import json
import unittest
import stage9_process as p
class ProcessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.e=json.loads((p.OUT/'process-evidence.json').read_text());cls.m=json.loads((p.OUT.parent/'stage8/mechanical-report.json').read_text())
    def test_actual_clearance_limit(self):
        r=p.analyze(self.e,self.m);self.assertAlmostEqual(r['derived_limits']['maximum_combined_allowance_mm'],.135);self.assertLess(r['derived_limits']['euro_standard_worst_land_gap_mm'],0)
        self.assertFalse(r['JLC_precision_size_screen']['X1-control']['meets_minimum_size_only']);self.assertFalse(r['published_precision_cutout_acceptance'])
    def test_general_publication_cannot_be_acceptance(self):
        e=copy.deepcopy(self.e);e['sources'][0]['supplier_acceptance_of_X1']=True
        with self.assertRaisesRegex(ValueError,'cannot imply'):p.analyze(e,self.m)
    def test_hole_position_cannot_replace_profile_position(self):
        e=copy.deepcopy(self.e);e['sources'][1]['facts']['profile_cutout_to_hole_position_plusminus_mm']=.05
        with self.assertRaisesRegex(ValueError,'separate profile'):p.analyze(e,self.m)
    def test_wrong_capability_column(self):
        e=copy.deepcopy(self.e);e['sources'][3]['facts']['shape_below_0p10_mm_column']='Non-standard review'
        with self.assertRaisesRegex(ValueError,'column'):p.analyze(e,self.m)
    def test_same_sum_different_separate_bounds(self):
        m=copy.deepcopy(self.m);m['requested_precision_process']['dimension_tolerance_plusminus_mm']=.04;m['requested_precision_process']['position_tolerance_plusminus_mm']=.06
        with self.assertRaisesRegex(ValueError,'separate requested'):p.analyze(self.e,m)
    def test_geometry_drift_invalidates_limit(self):
        m=copy.deepcopy(self.m);m['actual_pad_cut_margins'][0]['minimum_cut_boundary_gap_mm']=-.01
        with self.assertRaisesRegex(ValueError,'actual land gap'):p.analyze(self.e,m)
if __name__=='__main__':unittest.main()
