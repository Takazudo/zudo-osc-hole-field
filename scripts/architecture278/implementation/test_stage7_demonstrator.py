import copy,json,unittest
import stage7_demonstrator as s
class DemonstratorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ledger=json.loads((s.ROOT/'design/architecture-278/source-ledger.json').read_text());cls.locked=json.loads((s.ROOT/'design/grid/placements.lock.json').read_text());old=json.loads((s.ROOT/'design/architecture-278/implementation/stage6/hosting-report.json').read_text());cls.overlay=old['whole_instrument_host_overlay'];cls.interface=json.loads((s.OUT/'interfaces-report.json').read_text());cls.packages=cls.interface['source_packages']
 def run_case(self,p=None,overlay=None):return s.verify_source(p or self.packages,self.ledger,self.locked,overlay or self.overlay)
 def test_complete_source(self):
  c,o=self.run_case();self.assertEqual(76,c['units']);self.assertEqual(5904,len(o))
 def test_omitted_package(self):
  p=copy.deepcopy(self.packages);p.pop('C3306')
  with self.assertRaisesRegex(ValueError,'56package'):self.run_case(p)
 def test_rail_rewired(self):
  p=copy.deepcopy(self.packages);p['U3303']['pins']['4']='AGND'
  with self.assertRaisesRegex(ValueError,'identity'):self.run_case(p)
 def test_NC_connected(self):
  p=copy.deepcopy(self.packages);p['J809']['pins']['TN']='AGND'
  with self.assertRaisesRegex(ValueError,'identity'):self.run_case(p)
 def test_spare_unit_lost(self):
  p=copy.deepcopy(self.packages);p['U3303']['units'].remove(4)
  with self.assertRaisesRegex(ValueError,'units'):self.run_case(p)
 def test_panel_moved(self):
  p=copy.deepcopy(self.packages);p['SW608']['origin_mm'][0]+=.1
  with self.assertRaisesRegex(ValueError,'panel device'):self.run_case(p)
 def test_bypass_split(self):
  p=copy.deepcopy(self.packages);p['C3306']['board']='another-host'
  with self.assertRaisesRegex(ValueError,'bypass'):self.run_case(p)
 def test_whole_cluster_wrong_host(self):
  p=copy.deepcopy(self.packages)
  for ref in ('U3303','C3306','C3307'):p[ref]['board']='X1-jack'
  with self.assertRaisesRegex(ValueError,'owner/host'):self.run_case(p)
 def test_power_omitted_from_overlay(self):
  o=copy.deepcopy(self.overlay);ref=next(p['ref']for p in self.ledger['packages']if p['instance']=='POWER');del o[ref]
  with self.assertRaisesRegex(ValueError,'ownership'):self.run_case(overlay=o)
 def test_physical_transport(self):
  r=s.verify_transport(self.interface);self.assertEqual(15,r['conductors']);self.assertEqual(36,r['header_pin_solder_joints_including_NC'])
 def test_missing_wire(self):
  p=copy.deepcopy(self.interface);p['links'][0]['conductors'].pop()
  with self.assertRaisesRegex(ValueError,'wire/pin'):s.verify_transport(p)
 def test_wire_detached_from_pad(self):
  p=copy.deepcopy(self.interface);p['links'][0]['conductors'][0]['front_pad_xyz_mm'][0]+=.1
  with self.assertRaisesRegex(ValueError,'detached'):s.verify_transport(p)
 def test_return_star_cross_net(self):
  p=copy.deepcopy(self.interface);p['middle_trace_edges'][-1]['net']='+12V'
  with self.assertRaisesRegex(ValueError,'same-net'):s.verify_transport(p)
 def test_return_star_duplicate_edge(self):
  p=copy.deepcopy(self.interface);p['middle_trace_edges'][-1]=copy.deepcopy(p['middle_trace_edges'][-2])
  with self.assertRaisesRegex(ValueError,'connectivity'):s.verify_transport(p)
 def test_NC_joint_omission(self):
  p=copy.deepcopy(self.interface);p['transport_BOM']['total_header_solder_joints']=46
  with self.assertRaisesRegex(ValueError,'NC solder'):s.verify_transport(p)
if __name__=='__main__':unittest.main()
