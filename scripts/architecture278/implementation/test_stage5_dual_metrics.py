import copy,json,unittest
import stage5_dual_metrics as m
class DualTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=json.loads((m.d.OUT/'stage4/candidate-report.json').read_text())['candidate'];cls.config=json.loads((m.d.OUT/'assembly-report.json').read_text())['config'];cls.expected=sorted(map(m.d.identity,cls.c['paths']))
 def wired(self):return copy.deepcopy(next(r for r in self.c['paths']if 'link'in r))
 def test_full_metrics_and_no_green(self):
  r=m.build();self.assertEqual([38,50,38,38],[v['summary']['historical_complete_over300_count']for v in r['variants'].values()])
  for v in r['variants'].values():
   self.assertEqual(225,v['summary']['electrical_UNKNOWN_rows']);self.assertEqual(160,v['summary']['unique_signal_wire_conductors']);self.assertEqual(0,v['summary']['qualified_rows'])
   for p in v['rows']:self.assertEqual('NOT QUALIFIED',p['combined_acceptance'])
 def test_wire_not_total(self):
  p=m.metric(max(self.c['paths'],key=lambda r:r['total_mm']),self.config);self.assertEqual(63,p['wire']['cut_maximum_mm']);self.assertGreater(p['complete_developed_allocation_mm'],300);self.assertEqual('PASS ALLOCATION',p['wire']['length_only_result'])
 def test_no_wire_not_zero_pass(self):
  p=m.metric(next(r for r in self.c['paths']if 'link'not in r),self.config);self.assertIsNone(p['wire']['cut_maximum_mm']);self.assertTrue(p['wire']['length_only_result'].startswith('NOT APPLICABLE'))
 def test_missing_wire_rejected(self):
  p=self.wired();del p['segments']['wire_max_mm']
  with self.assertRaises(ValueError):m.metric(p,self.config)
 def test_reduced_contact_rejected(self):
  p=self.wired();p['segments']['GH_pair_mm']=0
  with self.assertRaises(ValueError):m.metric(p,self.config)
 def test_false_extracted_capacitance_rejected(self):
  p=self.wired();p['capacitance_pF']=100
  with self.assertRaises(ValueError):m.metric(p,self.config)
 def test_total_mismatch_rejected(self):
  p=self.wired();p['total_mm']-=10
  with self.assertRaises(ValueError):m.metric(p,self.config)
 def test_duplicate_endpoint_rejected(self):
  c=copy.deepcopy(self.c);c['paths'][-1]=c['paths'][0]
  with self.assertRaises(ValueError):m.summarize('bad',c,self.config,self.expected)
 def test_return_omission_rejected(self):
  c=copy.deepcopy(self.c);c['returns'].pop()
  with self.assertRaises(ValueError):m.summarize('bad',c,self.config,self.expected)
if __name__=='__main__':unittest.main()
