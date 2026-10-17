import copy
import unittest
import stage3_direct_mechanical as s

class DirectMechanicalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=s.build()
    def test_both_variants_cannot_inherit_card_local_clearance(self):
        self.assertEqual({'baseline','bypass_refined'},set(self.report['variants']))
        for r in self.report['variants'].values():
            self.assertEqual({'U1601','C1601','C1603','R1615'},{p['b']for p in r['same_middle_face_reservation_conflicts']})
            self.assertIn('NOT ACCEPTED',r['status'])
            self.assertEqual(0,r['counts']['qualified_free_queries'])
    def test_face_flip_changes_class_not_silent_clearance(self):
        d={'box_mm':[48.5,85,63.5,185],'side':'rear'};p={'box_mm':[50,135,60,145],'side':'rear'}
        self.assertEqual('SAME_FACE_RESERVATION',s.middle_conflict_class(d,p))
        p['side']='panel'
        self.assertEqual('OPPOSITE_FACE_PROJECTION',s.middle_conflict_class(d,p))
        p['box_mm']=[70,135,80,145]
        self.assertIsNone(s.middle_conflict_class(d,p))
    def test_all_five_extraction_and_handle_obligations(self):
        for r in self.report['variants'].values():
            self.assertEqual(5,r['counts']['historicalK_service_intersections'])
            self.assertEqual(1,r['counts']['handle_finger_pairs_per_card'])
            self.assertGreater(r['counts']['through_contact_inside_GH'],0)
    def test_changed_origins_have_distinct_screens(self):
        a=self.report['variants']['baseline'];b=self.report['variants']['bypass_refined']
        self.assertNotEqual(a['origins_mm'],b['origins_mm'])
        self.assertNotEqual(a['counts']['through_contact_inside_GH'],b['counts']['through_contact_inside_GH'])
        self.assertNotEqual(a['counts']['new_DIN_hardware_XY'],b['counts']['new_DIN_hardware_XY'])

if __name__=='__main__':unittest.main()
