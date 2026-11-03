import copy,json,unittest
import stage6_hosting as h
class HostingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=h.build();ledger=json.loads((h.ROOT/'design/architecture-278/source-ledger.json').read_text());cls.packages,cls.source=h.live_packages(ledger);cls.lock={p['ref']:p for p in json.loads((h.ROOT/'design/grid/placements.lock.json').read_text())['placements']if p['block']=='X1'}
 def test_complete_population_and_pad_nets(self):
  r=self.report;self.assertEqual((56,76,182),(len(r['placements']),sum(len(p['units'])for p in r['placements'].values()),r['source_pins_including_NC']));h.validate(r['placements'],self.packages,self.source,self.lock)
 def test_missing_package_rejected(self):
  p=copy.deepcopy(self.report['placements']);del p['C3306']
  with self.assertRaises(ValueError):h.validate(p,self.packages,self.source,self.lock)
 def test_missing_unit_rejected(self):
  p=copy.deepcopy(self.report['placements']);p['U3303']['units'].pop()
  with self.assertRaises(ValueError):h.validate(p,self.packages,self.source,self.lock)
 def test_fixed_switch_move_rejected(self):
  p=copy.deepcopy(self.report['placements']);p['SW608']['origin_mm'][0]+=.1
  with self.assertRaises(ValueError):h.validate(p,self.packages,self.source,self.lock)
 def test_host_split_rejected(self):
  p=copy.deepcopy(self.report['placements']);p['C3306']['owner']='front-jack'
  with self.assertRaises(ValueError):h.validate(p,self.packages,self.source,self.lock)
 def test_exact_crossing_and_rail_nodes(self):
  r=self.report;self.assertEqual({'/X1/A_BUFFER','/X1/B_BUFFER','/X1/SELECTOR_REMOTE'},set(r['cross_board_signal_interfaces']));self.assertEqual({'+12V','-12V','+5V','AGND'},set(r['rail_interfaces']))
  nodes=[(e['ref'],e['pin'])for group in [*r['local_net_nodes'].values(),*r['cross_board_signal_interfaces'].values(),*r['rail_interfaces'].values()]for e in group.get('nodes',group.get('source_endpoints',[]))]+[(e['ref'],e['pin'])for e in r['NC_endpoints']]
  expected=[(ref,pin)for ref,p in self.packages.items()for pin in p['pins']];self.assertCountEqual(expected,nodes)
 def test_no_unknown_fit_or_budget_promoted(self):
  r=self.report;self.assertFalse(r['adopted']);self.assertEqual([],r['qualified_free_regions']);self.assertIsNone(r['obstruction_screen']['new_other_function_occupied_geometry']);self.assertEqual(2572,r['counts']['other_K_packages_still_unhosted']);self.assertEqual(13,r['counts']['POWER_packages_still_unhosted'])
  for p in r['crossing_geometric_sensitivities']:self.assertIsNone(p['complete_developed_budget_mm']);self.assertGreaterEqual(p['via_reserved_handoffs_straight_sum_mm'],p['direct_pad_separation_mm'])
 def test_bypass_targets_and_spares_remain(self):
  r=self.report;self.assertEqual(10,len(r['bypass_associations']));p=r['placements'];self.assertEqual(p['U3305']['pins']['1'],p['U3305']['pins']['2']);self.assertEqual(p['U3305']['pins']['7'],p['U3305']['pins']['6']);self.assertEqual([1,2,3,4,5],p['U3303']['units'])
 def test_overlay_preserves_unrelated_hosts(self):
  old=json.loads((h.a.OUT/'stage5/hosting-options-report.json').read_text())['options']['candidate_front_redesign']['assignments'];new=self.report['whole_instrument_host_overlay'];self.assertEqual(5904,len(new));self.assertEqual(set(old),set(new))
  for ref in old:
   if ref not in self.packages:self.assertEqual(old[ref],new[ref])
 def test_rigid_bypass_refinement(self):
  r=self.report;old=r['inherited_seed_placements'];new=r['placements'];delta=[x-y for x,y in zip(new['U3303']['origin_mm'],old['U3303']['origin_mm'])]
  for ref in ('U3303','C3306','C3307'):
   for pin in old[ref]['pads_mm']:
    for a,b in zip(old[ref]['pads_mm'][pin],new[ref]['pads_mm'][pin]):
     for j in range(2):self.assertAlmostEqual(a[j]+delta[j],b[j])
 def test_obstructions_and_span_tradeoffs_not_hidden(self):
  r=self.report;s=r['obstruction_screen'];self.assertEqual(490,s['middle_DIN_screen_count']);self.assertEqual([],s['existing_OSC_front_envelope_intersections']);self.assertEqual([],s['support_perimeter_own_package_intersections']);self.assertTrue(s['support_perimeter_fixed_hardware_intersections']);self.assertTrue(s['internal_courtyard_pairs']);self.assertFalse(any(x['same_face']for x in s['internal_courtyard_pairs']));self.assertEqual(37,len(r['all_nonrail_net_span_changes']));self.assertTrue(any(x['delta_mm']>70 for x in r['all_nonrail_net_span_changes']));self.assertFalse(s['board_pair_screens'][0]['XY_intersection'])
if __name__=='__main__':unittest.main()
