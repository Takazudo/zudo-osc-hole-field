import copy,json,unittest
import stage5_rebudget as r
class RebudgetTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base=json.loads((r.a.OUT/'stage4/candidate-report.json').read_text())['candidate'];cls.a=json.loads((r.a.OUT/'assembly-report.json').read_text())
 def test_zero_move_roundtrip(self):
  candidate,changes=r.apply_moves(self.base,self.a,{'moves':[]});self.assertEqual([],changes['changed_path_indices']);self.assertEqual([],changes['changed_return_indices'])
  for p,q in zip(candidate['paths'],self.base['paths']):self.assertAlmostEqual(p['total_mm'],q['total_mm']);self.assertEqual(p['actual_identity'],q['actual_identity'])
 def test_final_repair_preserves_nonheader_endpoints(self):
  candidate=r.build()['candidate'];self.assertEqual(225,len(candidate['paths']));self.assertEqual(240,len(candidate['returns']));self.assertEqual(85,len(candidate['middle_header_placements_all_instances']));self.assertEqual(270,len(candidate['wire_checks']))
  for p,q in zip(candidate['paths'],self.base['paths']):
   for key in ('actual_identity','front_pad_mm','other_pad_mm','DIN_pad_mm','length_limit_mm','capacitance_limit_pF'):self.assertEqual(p[key],q[key])
   self.assertAlmostEqual(sum(p['segments'].values()),p['total_mm'])
  self.assertGreaterEqual(candidate['tolerance_service']['wire_minimum_slack_mm'],10)
 def test_whole_header_shift(self):
  move={'instance':'O3','header_ref':'M:FRONT-J:O1.SAW','delta_mm':[1,0]};c,_=r.apply_moves(self.base,self.a,{'moves':[move]});h=next(p for p in c['middle_header_placements_all_instances']if p['instance']=='O3'and p['ref']==move['header_ref']);old=next(p for p in self.a['middle_header_placements']if p['ref']==move['header_ref'])
  for pin,pts in old['pads_mm'].items():self.assertEqual([[x+35,y]for x,y in pts],h['pads_mm'][pin])
 def test_duplicate_move_rejected(self):
  m={'instance':'O3','header_ref':'M:K-O1-1','delta_mm':[0,0]}
  with self.assertRaises(ValueError):r.apply_moves(self.base,self.a,{'moves':[m,m]})
 def test_unknown_header_rejected(self):
  with self.assertRaises(ValueError):r.apply_moves(self.base,self.a,{'moves':[{'instance':'O3','header_ref':'FAKE','delta_mm':[0,0]}]})
 def test_missing_slack_rejected(self):
  with self.assertRaisesRegex(ValueError,'slack'):r.apply_moves(self.base,self.a,{'moves':[{'instance':'O3','header_ref':'M:K-O1-1','delta_mm':[100,0]}]})
 def test_rear_returns_unchanged(self):
  c=r.build()['candidate']
  for p,q in zip(c['returns'],self.base['returns']):
   if 'link'not in p:self.assertEqual(p,q)
if __name__=='__main__':unittest.main()
