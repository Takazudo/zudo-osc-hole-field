import copy,json,unittest
import stage7_interfaces as s
class InterfaceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.spec=json.loads((s.OUT/'interface-input.json').read_text());cls.fixture={'placements':json.loads((s.a.OUT/'stage6/hosting-report.json').read_text())['placements']}
  for p in cls.fixture['placements'].values():p['conditional_pad_depth_mm']=21.6 if p['side']=='rear'else 20
  cls.report=s.build_from(cls.spec,cls.fixture)
 def test_whole_source_and_transport_counts(self):
  r=self.report;self.assertEqual((56,182,8,4),(len(r['packages']),len(r['source_endpoint_inventory']),len(r['headers']),len(r['links'])));self.assertEqual(15,r['transport_BOM']['physical_wire_conductors']);self.assertEqual(30,r['transport_BOM']['crimp_contacts']);self.assertEqual(52,r['transport_BOM']['total_header_solder_joints']);self.assertEqual(6,r['transport_BOM']['NC_header_pin_solder_joints']);self.assertEqual(5904,len(r['whole_instrument_host_overlay']))
 def test_actual_footprints_and_depths(self):
  for h in self.report['headers'].values():
   self.assertEqual(h['positions']+2,len(h['pads_xyz_mm']));self.assertEqual(21.6 if h['end']=='front'else 48.4,h['pad_depth_mm'])
   self.assertIsNone(h['pins']['MP1']);self.assertIsNone(h['pins']['MP2'])
 def test_cross_net_pin_mutation_rejected(self):
  p=copy.deepcopy(self.spec);p['links'][0]['pins']['1']='AGND'
  with self.assertRaises(ValueError):s.transport_geometry(p)
 def test_missing_link_rejected(self):
  p=copy.deepcopy(self.spec);p['links'].pop()
  with self.assertRaises(ValueError):s.transport_geometry(p)
 def test_wrong_face_depth_rejected(self):
  p=copy.deepcopy(self.spec);p['links'][0]['front']['pad_depth_mm']=20
  with self.assertRaises(ValueError):s.transport_geometry(p)
 def test_missing_source_pin_rejected(self):
  p=copy.deepcopy(self.fixture);del p['placements']['U3305']['pins']['1']
  with self.assertRaises(ValueError):s.build_from(self.spec,p)
 def test_middle_graph_and_plus5_boundary(self):
  r=self.report;self.assertEqual(8,len(r['middle_trace_edges']));self.assertEqual(3,sum(e['net']=='AGND'for e in r['middle_trace_edges']));self.assertFalse(any(e['net']=='+5V'for e in r['middle_trace_edges']))
  for e in r['middle_trace_edges']:
   for end in ('from','to'):self.assertEqual(e['net'],r['headers'][e[end]['ref']]['pins'][e[end]['pin']])
  self.assertEqual(1,sum(w['net']=='+5V'for l in r['links']for w in l['conductors']));self.assertTrue(all(p['identical_net_pinmap']for p in r['mating_compatibility']['same_size_pairs']))
 def test_wire_sweep_and_slack_not_native_pass(self):
  for l in self.report['links']:
   for w in l['conductors']:
    self.assertEqual(4,len(w['service_endpoint_cases']));self.assertAlmostEqual(w['wire_min_mm']-max(c['straight_separation_mm']for c in w['service_endpoint_cases']),w['minimum_service_proxy_slack_mm']);self.assertEqual(2,w['crimp_terminations'])
  self.assertFalse(self.report['accepted']);self.assertEqual('NOT RUN',self.report['native'])
 def test_too_short_wire_exposed_not_hidden(self):
  p=copy.deepcopy(self.spec);p['links'][0]['wire']['nominal_mm']=20
  r=s.build_from(p,self.fixture);self.assertFalse(r['all_wire_slack_screens_pass'])
 def test_no_parallel_return_credit_or_upstream_invention(self):
  self.assertEqual(4,self.report['transport_BOM']['AGND_wire_conductors'])
  for b in self.report['middle_upstream_power_boundaries']:self.assertIsNone(b['upstream_source_connector']);self.assertIsNone(b['source_return_impedance_ohm'])
  self.assertAlmostEqual(.1,self.report['source_evidence']['rating_scope']['per_harness_two_contacts_after_test_ohm'])
 def test_front_connections_and_NC_cavities(self):
  r=self.report;nodes=[x for n in r['front_net_connections']for x in n['source_endpoints']]
  self.assertCountEqual([(x['ref'],x['pin'])for x in r['source_endpoint_inventory']if x['net']is not None],[(x['ref'],x['pin'])for x in nodes])
  self.assertTrue(r['all_wire_slack_screens_pass'])
  p=next(l for l in r['links']if l['id']=='J-PWR');self.assertEqual({'1','3','5','7'},{w['pin']for w in p['conductors']});self.assertEqual(7,len(p['pins']))
 def test_final_mechanical_coordinates_consumed(self):
  m=json.loads((s.OUT/'mechanical-report.json').read_text());r=s.build_from(self.spec,m)
  for ref,p in m['placements'].items():
   self.assertEqual(p['pads_mm'],r['packages'][ref]['pads_mm']);self.assertEqual(p['conditional_pad_depth_mm'],r['packages'][ref]['pads_xyz_mm'][next(iter(p['pins']))][0][2])
if __name__=='__main__':unittest.main()
