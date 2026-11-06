import copy
import json
import math
import unittest
import direct_study as d

class DirectStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=json.loads((d.OUT/'assembly-report.json').read_text())
        cls.audit=json.loads((d.OUT/'stage3-crossing-audit.json').read_text())
        cls.report=json.loads((d.OUT/'direct-study-report.json').read_text())
    def complete(self,best):d.complete_best(best,self.source,self.audit,self.source['config'])
    def test_exact_coverage(self):
        for best in self.report['best_by_variant'].values():
            self.complete(copy.deepcopy(best))
            self.assertEqual(225,len(best['paths']))
            self.assertEqual(9,len(best['shared_aggregate_capacitance']))
            self.assertEqual(len(self.source['alternatives']['five_card_two_rows']['returns']),len(best['returns']))
    def test_missing_receiver_rejected(self):
        best=copy.deepcopy(self.report['best']);best['paths'].pop()
        with self.assertRaisesRegex(ValueError,'coverage'):self.complete(best)
    def test_wrong_instance_rejected(self):
        best=copy.deepcopy(self.report['best']);best['paths'][0]['instance']='O9'
        with self.assertRaisesRegex(ValueError,'coverage'):self.complete(best)
    def test_noninjective_map_rejected(self):
        best=copy.deepcopy(self.report['best']);keys=list(best['common_DIN_signal_labels']);best['common_DIN_signal_labels'][keys[0]]=best['common_DIN_signal_labels'][keys[1]]
        with self.assertRaisesRegex(ValueError,'injective'):self.complete(best)
    def test_wrong_budget_sum_rejected(self):
        best=copy.deepcopy(self.report['best']);best['paths'][0]['total_mm']-=1
        with self.assertRaisesRegex(ValueError,'decomposition'):self.complete(best)
    def test_fixed_octave_and_allowances(self):
        original={d.identity(r):r for r in self.source['alternatives']['five_card_two_rows']['paths']}
        for best in self.report['best_by_variant'].values():
            for row in best['paths']:
                self.assertEqual(300,row['length_limit_mm']);self.assertEqual(1000,row['capacitance_limit_pF'])
                if row['net'].startswith('OSC_OCT'):self.assertEqual(original[d.identity(row)]['segments'],row['segments'])
                if 'link' in row:
                    self.assertEqual(63,row['segments']['wire_max_mm']);self.assertEqual(15,row['segments']['GH_pair_mm'])
    def test_cluster_rigidity(self):
        for variant,best in self.report['best_by_variant'].items():
            source=self.source['rear_placements'] if variant=='baseline' else json.loads((d.OUT/'cluster-refinement-report.json').read_text())['placements']
            old={p['ref']:p for p in source}
            for p in best['packages']:
                self.assertEqual(old[p['ref']]['units'],p['units'])
                for pin,pts in p['pads_mm'].items():
                    for i,xy in enumerate(pts):
                        self.assertAlmostEqual(math.dist(xy,p['origin_mm']),math.dist(old[p['ref']]['pads_mm'][pin][i],old[p['ref']]['origin_mm']))
    def test_unknown_space_never_free(self):
        self.assertEqual(240,self.report['case_count'])
        for case in self.report['cases']:
            self.assertFalse(case['geometry']['accepted'])
            self.assertIn('UNKNOWN_RESERVED',case['geometry']['other_28_occupied_volume'])
        self.assertGreater(self.report['best']['maximum_mm'],300)
    def test_same_card_collision_rejected(self):
        best=self.report['best'];fixture=copy.deepcopy(best['fixtures']);fixture[0]['box_mm']=best['packages'][0]['reserved_box_mm']
        self.assertTrue(d.geometry(best['packages'],fixture,self.report['spec'],best['origins_mm'])['proxy_errors'])

if __name__=='__main__':unittest.main()
