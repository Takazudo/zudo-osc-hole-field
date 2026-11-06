import copy
import json
import math
import unittest
import stage4_candidate as s

class Stage4CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=s.build();cls.c=cls.r['candidate']
        cls.old=json.loads((s.a.OUT/'direct-study-report.json').read_text())['best_by_variant']['baseline']
        cls.assembly=json.loads((s.a.OUT/'assembly-report.json').read_text())
    def test_complete_endpoint_correspondence(self):
        self.assertEqual(sorted(map(s.d.identity,self.old['paths'])),sorted(map(s.d.identity,self.c['paths'])))
        self.assertEqual(225,len(self.c['paths']));self.assertEqual(65,self.r['changed_shared_path_count'])
    def test_returns_and_nonshared_unchanged(self):
        self.assertEqual(self.old['returns'],self.c['returns']);self.assertEqual(240,len(self.c['returns']))
        for a,b in zip(self.old['paths'],self.c['paths']):
            if not a['net'].startswith('OSC_'):self.assertEqual(a,b)
    def test_shared_whole_packages_preserved(self):
        self.assertEqual(30,len(self.c['shared_middle_placements']))
        for old,new in zip(self.assembly['shared_middle_placements'],self.c['shared_middle_placements']):
            self.assertEqual(old['units'],new['units']);self.assertEqual(set(old['pads_mm']),set(new['pads_mm']))
            for pin,pts in old['pads_mm'].items():
                for p,q in zip(pts,new['pads_mm'][pin]):self.assertEqual([p[0]+6,p[1]],q)
    def test_all_path_arithmetic_and_limits(self):
        for row in self.c['paths']:
            self.assertAlmostEqual(sum(row['segments'].values()),row['total_mm'])
            self.assertEqual(300,row['length_limit_mm']);self.assertEqual(1000,row['capacitance_limit_pF']);self.assertIsNone(row['capacitance_pF'])
        self.assertEqual(9,len(self.c['shared_aggregate_capacitance']))
    def test_two_grips_and_local_clearance(self):
        handles=[p for p in self.c['fixtures']if p['id'].startswith('handle')]
        self.assertEqual(2,len(handles));centres=[(p['box_mm'][0]+p['box_mm'][2])/2 for p in handles]
        self.assertEqual([11,33],centres);self.assertGreater(centres[1]-centres[0],20)
        self.assertFalse(self.c['geometry']['proxy_errors'])
    def test_no_acceptance_or_split_inference(self):
        self.assertFalse(self.c['geometry']['accepted']);self.assertIn('UNKNOWN_RESERVED',self.r['occupied_volume'])
        self.assertGreater(self.c['maximum_mm'],300);self.assertEqual(38,self.c['overlength_count'])
        self.assertIn('NOT investigated',self.r['comparisons']['split_interface'])
    def test_pure_transform_does_not_mutate_source(self):
        original=copy.deepcopy(self.assembly['shared_middle_placements'][0]);before=copy.deepcopy(original)
        s.translate_package(original,[6,0]);self.assertEqual(before,original)

if __name__=='__main__':unittest.main()
