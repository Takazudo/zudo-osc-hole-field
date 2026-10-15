"""Mutation checks protect reservation arithmetic, scope and accounting."""
import copy
import unittest
import mechanics

class MechanicalTests(unittest.TestCase):
    def setUp(self):
        self.p=mechanics.read(mechanics.SOURCES[-1])
    def test_adjacency_growth_rejected(self):
        self.p['card_width_mm']=18
        with self.assertRaises(AssertionError):mechanics.model(self.p)
    def test_control_path_overlength_rejected(self):
        self.p['middle_trace_max_mm']=140
        with self.assertRaises(AssertionError):mechanics.model(self.p)
    def test_selector_intersection_rejected(self):
        self.p['middle_face_z_mm']=-30
        with self.assertRaises(AssertionError):mechanics.model(self.p)
    def test_cover_intrusion_is_conflict_not_pass(self):
        self.p['cover_inner_z_mm']=-104
        r=mechanics.model(self.p)
        self.assertEqual(r['interference_table'][1]['status'],'CONFLICT; REVISE')
    def test_trim_loss_rejected(self):
        self.p['trim_y_mm'].pop()
        with self.assertRaises(AssertionError):mechanics.model(self.p)
    def test_middle_faces_counted(self):
        r=mechanics.model(self.p)
        self.assertEqual(sum(h['candidate_crimps'] for h in r['harnesses']),204)
        self.assertEqual(sum(h['candidate_mating_interfaces'] for h in r['harnesses']),204)
        self.assertEqual(len(r['existing_rear_terminals']),36)
        self.assertTrue(any(c['status']=='CONFLICT; REVISE' for c in r['interference_table']))
    def test_card_bounds_mutation_exposes_containment_and_svg(self):
        self.p['card_y_mm']=[40,250]
        r=mechanics.model(self.p)
        self.assertIn('y="40" width="15" height="210"',mechanics.drawing(r))
        self.assertTrue(any(c['status']=='CONFLICT; REVISE' and 'containment' in c['name'] for c in r['interference_table']))
    def test_access_envelope_mutations(self):
        for key,kind in [('probe_diameter_mm','probe'),('support_collar_diameter_mm','support'),('connector_reservation_width_mm','connector')]:
            p=copy.deepcopy(self.p);p[key]=40 if kind=='connector' else 30
            r=mechanics.model(p)
            c=next(c for c in r['interference_table'] if c['name']==f'adjacent {kind} reservations')
            self.assertEqual(c['status'],'CONFLICT; REVISE')
            self.assertNotEqual(mechanics.drawing(r),mechanics.drawing(mechanics.model(self.p)))
    def test_extraction_cannot_exceed_workspace(self):
        self.p['rear_extraction_stroke_mm']=1000
        self.p['rear_external_work_depth_mm']=1
        r=mechanics.model(self.p)
        c=next(c for c in r['interference_table'] if c['name']=='external workspace minus extraction stroke')
        self.assertEqual(c['margin_mm'],-999)
        self.assertEqual(c['status'],'CONFLICT; REVISE')
        self.assertIn('extraction: 1000 mm',mechanics.drawing(r))
        self.assertIn('Reserve 1 mm',mechanics.drawing(r))
    def test_bend_bound_cannot_be_weakened(self):
        self.p['cable_bend_radius_allocation_mm']=8
        with self.assertRaises(AssertionError):mechanics.model(self.p)
    def test_drawings_deterministic(self):
        r=mechanics.model(self.p)
        self.assertEqual(mechanics.drawing(r),mechanics.drawing(copy.deepcopy(r)))

if __name__=='__main__':unittest.main()
