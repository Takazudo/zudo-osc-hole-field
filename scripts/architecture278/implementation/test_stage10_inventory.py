import copy,json,unittest
import stage10_inventory as s
class InventoryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ledger=json.loads((s.ROOT/'design/architecture-278/source-ledger.json').read_text());cls.prior=json.loads((s.a.OUT/'stage7/demonstrator-report.json').read_text())['whole_instrument_host_overlay'];cls.packages,_=s.live_packages(cls.ledger)
 def test_exact_population(self):
  r=s.build();self.assertEqual(r['counts']['pins_including_NC'],285);self.assertEqual(len(r['bypass_associations']),17);self.assertEqual(len(r['fixed_controls']),9)
 def test_live_net_mutation(self):
  q=copy.deepcopy(self.ledger);u=next(u for u in q['package_units']if u['ref']=='U7101');u['pins']['2']='-12V'
  with self.assertRaisesRegex(ValueError,'net drift'):s.live_packages(q)
 def test_NC_mutation(self):
  q=copy.deepcopy(self.ledger);u=next(u for u in q['package_units']if u['ref']=='J1308');u['pins']['TN']='AGND'
  with self.assertRaisesRegex(ValueError,'net drift'):s.live_packages(q)
 def test_unit_omission(self):
  q=copy.deepcopy(self.ledger);p=next(p for p in q['packages']if p['ref']=='U7104');p['units'].pop()
  with self.assertRaisesRegex(ValueError,'whole package'):s.live_packages(q)
 def test_bypass_target_mutation(self):
  q=copy.deepcopy(self.ledger);next(p for p in q['packages']if p['ref']=='C7107')['decouples_ref']='U7104'
  with self.assertRaisesRegex(ValueError,'bypass association'):s.live_packages(q)
 def test_identity_preserved(self):
  self.assertEqual(self.packages['RV1308']['attributes']['MPN'],'PTV09A-4020F-B104')
  q=copy.deepcopy(self.ledger);next(p for p in q['packages']if p['ref']=='RV1308')['mpn']='PTV09A-4020F-B103'
  with self.assertRaisesRegex(ValueError,'identity'):s.live_packages(q)
 def test_exact_reconciliation(self):
  r,overlay=s.reconcile(self.ledger,self.prior,self.packages);self.assertEqual(len(r['remaining_nonOSC_K_refs']),2543);self.assertEqual(len(overlay),5904)
  self.assertEqual({ref for ref in overlay if overlay[ref]!=self.prior[ref]},set(self.packages))
 def test_missing_prior_package(self):
  q=dict(self.prior);q.pop('U7101')
  with self.assertRaisesRegex(ValueError,'overlay'):s.reconcile(self.ledger,q,self.packages)
 def test_prior_K_ownership_drift(self):
  q=dict(self.prior);q['U7101']='accepted-board'
  with self.assertRaisesRegex(ValueError,'unhosted'):s.reconcile(self.ledger,q,self.packages)
if __name__=='__main__':unittest.main()
