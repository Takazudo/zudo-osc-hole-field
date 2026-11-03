import copy,json,unittest
import revision_electrical as r
class RevisionElectrical(unittest.TestCase):
 def setUp(self):self.c=json.loads((r.PACK/'interface-contract.json').read_text())
 def test_faces_conserved(self):
  x=r.build(self.c);self.assertEqual(len(x['original_conductors']),51);self.assertEqual(x['active_rear_contacts'],51)
 def test_missing_conductor_rejected(self):
  for f in self.c['harnesses'][0]['faces']:f['pin_map'].pop('1')
  with self.assertRaises(ValueError):r.build(self.c)
 def test_opposite_face_polarity_rejected(self):
  self.c['harnesses'][0]['faces'][0]['pin_map']['1']='AGND'
  with self.assertRaises(ValueError):r.build(self.c)
 def test_both_faces_corrupted_rejected(self):
  for f in self.c['harnesses'][0]['faces']:f['pin_map']['1']='AGND'
  with self.assertRaises(ValueError):r.build(self.c)
 def test_shared_reference_charged_once(self):
  p=[x for x in r.build(self.c)['paths'] if x['owner']=='shared-middle-reference']
  self.assertEqual([(x['rail'],x['planning_allowance_mA']) for x in p],[('+12V',26),('-12V',26)])
 def test_wiper_routes_are_complete_positive_segments(self):
  p=r.build(self.c)['remote_paths'];self.assertEqual(len(p),10)
  self.assertTrue(all(x['connector_path_allocation_mm']>=19.2 for x in p))
  self.assertTrue(all(x['total_mm']>x['middle_diagonal_with_detour_mm'] for x in p))
  self.assertTrue(all(x['within_length_allocation'] for x in p))
 def test_all_conductors_get_length_bill(self):
  x=r.build(self.c);self.assertEqual(len(x['all_51_transport_lengths']),51);self.assertEqual(x['O1_front_wire_total_proposed_mm'],3060)
 def test_functional_regrouping_conserves_and_counts_added_refs(self):
  x=r.build(self.c);self.assertEqual(sum(p['conductors'] for p in x['functional_front_links']),24);self.assertEqual(x['functional_front_regrouping']['crimps'],108)
 def test_whole_card_rotation_preserves_local_trace_distances(self):
  x=r.build(self.c);m=json.loads((r.PACK/'revision-mechanical-report.json').read_text())
  base=r.compare_front_banks(self.c,m,x['rear_connector_pinout'],x['functional_front_links'])
  baseline={(p['harness'],p.get('pin')):p for p in base if p.get('instance')=='O2' and 'total_mm' in p}
  for a in (90,180,270):
   rows=r.compare_front_banks(self.c,m,x['rear_connector_pinout'],x['functional_front_links'],{'O2':a})
   for p in rows:
    if p.get('instance')=='O2' and 'total_mm' in p:self.assertAlmostEqual(p['rear_to_source_or_receivers_mm'],baseline[p['harness'],p['pin']]['rear_to_source_or_receivers_mm'])
 def test_changed_connector_bank_fails_closed(self):
  m=json.loads((r.PACK/'revision-mechanical-report.json').read_text());m['config']['connector_box_mm'][0]+=1
  with self.assertRaisesRegex(ValueError,'connector_box_mm'):r.validate_geometry(m)
 def test_changed_tile_fails_closed(self):
  m=json.loads((r.PACK/'revision-mechanical-report.json').read_text());m['config']['tile_mm'][0]+=5
  with self.assertRaisesRegex(ValueError,'tile_mm'):r.validate_geometry(m)
 def test_connector_stack_tolerance_cannot_exceed_pair_range(self):
  m=json.loads((r.PACK/'revision-mechanical-report.json').read_text());m['config']['stack_tolerance_mm']=1
  with self.assertRaises(ValueError):r.validate_geometry(m)
 def test_service_loss_rejected(self):
  self.c['shared_services'].pop()
  with self.assertRaises(ValueError):r.build(self.c)
 def test_five_wipers_required(self):
  self.c['controls'][0]['type']='buffered'
  with self.assertRaises(ValueError):r.build(self.c)
 def test_octave_source_not_routed_to_rear(self):
  x=r.build(self.c);self.assertEqual(sum(c['rear_pin'] is None for c in x['original_conductors']),6)
  self.assertFalse(any((p['net'] or '').startswith('OSC_OCT') for p in x['rear_connector_pinout']))
 def test_keying_has_no_signal(self):
  x=r.build(self.c);self.assertEqual(len(x['rear_connector_pinout']),96)
  self.assertTrue(set(x['removed_key_positions']).isdisjoint(p['pin'] for p in x['rear_connector_pinout']))
 def test_switched_current_exceeds_historical_condition(self):
  d=r.build(self.c)['octave_dynamics'];self.assertEqual(d['initial_all5_current_mA'],25);self.assertGreater(d['initial_all5_current_mA'],d['historical_driver_planning_limit_mA'])
 def test_no_load_state_promoted_to_zero(self):
  self.assertTrue(all(v is None for p in r.build(self.c)['paths'] for v in p['state_maxima_mA'].values()))
 def test_power_rejection_and_whole_return_remainder(self):
  p=r.build(self.c)['power_bound'];self.assertGreater(p['DIN_contact_max_mOhm'],p['return_total_limit_mOhm']);self.assertAlmostEqual(p['remaining_return_budget_mOhm']+p['bulk_mOhm']+p['two_joint_allocation_mOhm'],.5)
if __name__=='__main__':unittest.main()
