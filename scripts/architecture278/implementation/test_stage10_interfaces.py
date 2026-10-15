import copy,json,unittest
import stage10_interfaces as s
class InterfacesTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.spec=json.loads((s.OUT/'interface-input.json').read_text());cls.mech=json.loads((s.OUT/'mechanical-report.json').read_text());cls.inv=json.loads((s.OUT/'inventory-report.json').read_text())
 def test_complete_inventory(self):
  graph,e=s.analyze(self.spec,self.mech,self.inv)
  self.assertEqual(len(graph['wires']),20);self.assertEqual(len(graph['source_endpoints'])+len(graph['NC_source_endpoints']),285)
  self.assertEqual(e['counts']['physical_wires'],34);self.assertEqual(len(graph['terminal_wires']),14);self.assertEqual(e['counts']['DIN_NC_contacts'],80);self.assertFalse(e['hardware_acceptance'])
 def test_gh_source_evidence(self):self.assertEqual(s.evidence()['GH6_new_candidate']['A_mm'],6.25)
 def test_pinmap_mutation(self):
  x=copy.deepcopy(self.spec);x['links'][0]['pins']['1']='+12V'
  with self.assertRaisesRegex(ValueError,'pinmap'):s.transport_geometry(x)
 def test_missing_package_or_pin(self):
  x=copy.deepcopy(self.mech);x['placements'].pop('U7104')
  with self.assertRaisesRegex(ValueError,'all90'):s.graph_report(self.spec,x,self.inv)
  x=copy.deepcopy(self.mech);x['placements']['U7104']['pins']['1']='AGND'
  with self.assertRaisesRegex(ValueError,'parity'):s.graph_report(self.spec,x,self.inv)
 def test_split_unit(self):
  x=copy.deepcopy(self.mech);x['placements']['U7104']['units'].pop()
  with self.assertRaisesRegex(ValueError,'parity'):s.graph_report(self.spec,x,self.inv)
 def test_short_wire(self):
  x=copy.deepcopy(self.spec);x['links'][0]['wire_cut_nominal_mm']=10
  with self.assertRaisesRegex(ValueError,'slack'):s.graph_report(x,self.mech,self.inv)
 def test_disconnected_path(self):
  with self.assertRaisesRegex(ValueError,'disconnected'):s.path_edges({'edges':[]},'source','sink')
 def test_reference_full_fanout(self):
  g,e=s.analyze(self.spec,self.mech,self.inv)
  refs=next(x for x in e['conditional_budgets']['aggregate_crossing_capacitance']if x['net']=='/A01/REF5')
  self.assertEqual(refs['physical_harness_branches'],2);self.assertIsNone(refs['total_assembled_capacitance_pF'])
 def test_local_feedback_does_not_detour_to_connector(self):
  g,e=s.analyze(self.spec,self.mech,self.inv)
  for driver,receiver in [('U7104:1','U7104:2'),('U7106:1','U7106:2'),('R7113:2','R7114:1')]:
   edges=[g['edges'][i]for i in s.path_edges(g,driver,receiver)]
   self.assertEqual(len(edges),1);self.assertEqual(edges[0]['kind'],'local_source_copper')
 def test_mechanical_header_detachment(self):
  x=copy.deepcopy(self.mech);next(iter(x['headers'].values()))['pads_xyz_mm']['1'][0][0]+=.1
  with self.assertRaisesRegex(ValueError,'geometry agreement'):s.graph_report(self.spec,x,self.inv)
 def test_DIN_net_mutation_rejected(self):
  x=copy.deepcopy(self.mech);x['din_connectors']['rear']['pins']['c1']='AGND'
  with self.assertRaisesRegex(ValueError,'DIN physical'):s.graph_report(self.spec,x,self.inv)
 def test_tail_missing_and_net_mutation(self):
  x=copy.deepcopy(self.mech);x['terminal_extensions'].pop()
  with self.assertRaisesRegex(ValueError,'all14'):s.graph_report(self.spec,x,self.inv)
  x=copy.deepcopy(self.mech);x['terminal_extensions'][0]['net']='AGND'
  with self.assertRaisesRegex(ValueError,'tail source'):s.graph_report(self.spec,x,self.inv)
 def test_all_tail_paths_have_actual_wire(self):
  g,e=s.analyze(self.spec,self.mech,self.inv)
  for t in g['terminal_wires']:
   key=t['ref']+':'+t['pin'];row=next(p for p in e['local_endpoint_paths']if p['to']==key)
   self.assertGreaterEqual(row['all_wire_cut_max_mm'],88)
   self.assertTrue(any(g['edges'][i]['kind']=='permanent_terminal_wire'for i in row['edge_indices']))
 def test_power_target_not_waived(self):
  g,e=s.analyze(self.spec,self.mech,self.inv);p=e['conditional_budgets']['GH_power_return_contract']
  self.assertEqual(p['retained_return_target_ohm'],.0005);self.assertEqual(p['after_test_bound_to_return_target_ratio'],200)
if __name__=='__main__':unittest.main()
