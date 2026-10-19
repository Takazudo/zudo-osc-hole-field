import copy
import json
import math
import unittest
import stage36_interface_cassette as s

class C36(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.I=json.loads((s.OUT/'interface-input.json').read_text())
        _,cls.P,cls.T,cls.rules,cls.c=s.s35.context()

    def test_locked_constraints_reject_mutation(self):
        for key in ('radius_mm','withdrawal_mm','core_extraction_mm','margin_mm','K4_mm'):
            i=copy.deepcopy(self.I);i[key]+=1
            with self.assertRaises((ValueError,AssertionError)):s.validate(i)

    def test_continuous_forward_reverse_sweep(self):
        p=s.box('test',[1,2,4,8],[3,6]);q=s.sweep(p,15)
        self.assertEqual(p['z'],[3,6])
        for t in (0,.1,3.8,7.5,14.99,15):
            self.assertLessEqual(q['z'][0],p['z'][0]+t)
            self.assertGreaterEqual(q['z'][1],p['z'][1]+t)
            self.assertLessEqual(q['z'][0],p['z'][0]+15-t)
            self.assertGreaterEqual(q['z'][1],p['z'][1]+15-t)

    def test_plain_guide_fails_and_relative_errors_remain(self):
        a=s.alignment(self.I,self.c)
        self.assertAlmostEqual(a['guide_path_bound_mm'],2.044,places=10)
        self.assertFalse(a['path_contract_met'])
        self.assertAlmostEqual(a['possible_bow_change_between_fits_mm'],.015*math.hypot(82,150))
        self.assertIsNone(a['manufacturer_capture_window_mm'])

    def test_support_stack_and_stud_engagement(self):
        i=self.I
        self.assertEqual(i['post_z_mm'][1],i['roof_z_mm'][1]-i['bushing_length_mm'])
        self.assertGreaterEqual(i['service_stud_shaft_z_mm'][1],i['roof_z_mm'][1]+15)
        self.assertEqual(101-16,85)  # short screw tip; five mm into thread84..90
        self.assertEqual(i['service_stud_thread_z_mm'],[84,90])

    def test_stud_head_blocks_requested_removal(self):
        i=self.I
        self.assertGreater(i['service_stud_hex_diameter_mm'],i['bushing_bore_mm'])
        stop=i['service_stud_shaft_z_mm'][1]-i['roof_z_mm'][1]
        self.assertEqual(stop,32)
        self.assertGreaterEqual(stop,15)
        self.assertLess(stop,i['removal_translation_mm'])

    def test_unknown_neighbor_never_erased_by_cap(self):
        # Representative foreign-depth obstacle, intentionally intersected above
        # its historical proxy. A proposed cap must not turn that into a pass.
        obs=s.s35.occupied_obstacles(self.c,250)
        o=next(o for o in obs if o['kind']=='unknown_depth')
        p=copy.deepcopy(o);p.update(id='probe',z=[100,101])
        a=s.obstacle_audit(self.I,self.c,self.P,self.T,self.rules,[p])
        self.assertFalse(a['unknown_space_treated_free'])
        self.assertAlmostEqual(next(r for r in a['minimum_by_obstacle'] if r['obstacle']==o['id'])['registration_box_norm_mm'],math.sqrt(3))
        self.assertTrue(any(r['obstacle']==o['id'] for r in a['blocking_rows']))
        cap=next(r for r in a['proposed_neighbor_obligations'] if r['obstacle']==o['id'])
        self.assertFalse(cap['accepted'])
        self.assertGreater(o['z'][1],101)

    def test_no_physical_claim_or_keeper_invention(self):
        self.assertIsNone(self.I['keeper_capture_clearance_mm'])
        self.assertIsNone(self.I['keeper_allowable_force_N'])
        self.assertIsNone(self.I['wire_selection'])
        self.assertEqual(self.I['status'],'PROPOSED_INTERFACE_CONTRACT_NOT_ADOPTED')

if __name__=='__main__':unittest.main()
