import copy
import unittest
import stage3_reservations as s

class ReservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=s.build();cls.config=cls.report['input']
    def test_other_functions_accounted(self):
        self.assertEqual((28,24,2572,3385),(self.report['other_function_count'],self.report['other_K_function_count'],self.report['other_K_package_count'],self.report['all_K_package_count']))
        front_only={r['function'] for r in self.report['other_functions'] if not r['retained_K_package_count']}
        self.assertEqual({'B1','B2','X1','X2'},front_only)
        self.assertTrue(all(r['new_stack_occupied_volume'] is None for r in self.report['other_functions']))
    def test_unknown_never_becomes_free_with_empty_obstacles(self):
        q={'id':'empty-looking','xy_mm':[215,140,250,170],'z_mm':[50,70]}
        result=s.classify_query(q,self.config,[],[100,101.6])
        self.assertFalse(result['qualified_free']);self.assertTrue(result['space_status'].startswith('UNKNOWN'))
    def test_retained_K_blocks_removal_not_static_core(self):
        k=self.report['historical_K_board'];base={'id':'test','xy_mm':[5,82,102,197]}
        self.assertFalse(s.classify_query(dict(base,z_mm=[69.2,74.2]),self.config,k['xy_rectangles_mm'],k['board_depth_mm'])['historical_K_conflict_if_retained'])
        self.assertTrue(s.classify_query(dict(base,z_mm=[69.2,127.2],phase='service_cover_removed'),self.config,k['xy_rectangles_mm'],k['board_depth_mm'])['historical_K_conflict_if_retained'])
    def test_unjustified_free_and_depth_mutations_rejected(self):
        cfg=copy.deepcopy(self.config);cfg['qualified_free_regions']=[[0,0,318,298]]
        with self.assertRaises(AssertionError):s.validate_input(cfg)
        cfg=copy.deepcopy(self.config);cfg['depths_mm']['cover']=120
        with self.assertRaises(AssertionError):s.validate_input(cfg)
    def test_static_volume_cannot_use_service_workspace(self):
        q={'id':'deep','xy_mm':[140,220,180,240],'z_mm':[100,106.6]}
        self.assertTrue(s.classify_query(q,self.config,[],[100,101.6])['space_status'].startswith('OUTSIDE_CURRENT_ENVELOPE'))
        q['phase']='service_cover_removed'
        self.assertTrue(s.classify_query(q,self.config,[],[100,101.6])['space_status'].startswith('UNKNOWN'))
    def test_outline_decomposition_keeps_notch(self):
        r=self.report['historical_K_board']['xy_rectangles_mm']
        self.assertEqual(85464,sum(s.area(b) for b in r))
        self.assertFalse(any(s.overlap([270,260,280,270],b) for b in r))
    def test_pad_locality_not_package_origin(self):
        cap=next(p for p in self.report['rear_bypass_actual_pad_ranking'] if p['capacitor']=='C1129')
        self.assertEqual('16',cap['target_pin']);self.assertAlmostEqual(20.286,cap['direct_pad_distance_mm'],places=3)
        self.assertIn('OPEN',cap['return_loop_status'])

if __name__=='__main__':unittest.main()
