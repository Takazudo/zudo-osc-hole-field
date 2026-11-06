import copy,json,math,unittest
from unittest.mock import patch
from pathlib import Path
import stage7_mechanical as m
class MechanicalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.r=m.build();cls.spec=json.loads((m.OUT/'mechanical-input.json').read_text())
 def altered(self,spec):
  original=Path.read_text
  def read(path,*args,**kwargs):return json.dumps(spec)if path==m.OUT/'mechanical-input.json'else original(path,*args,**kwargs)
  with patch.object(Path,'read_text',read):return m.build()
 def test_complete_source_ownership(self):
  r=self.r;self.assertEqual(len(r['placements']),56);self.assertEqual(sum(len(p['units'])for p in r['placements'].values()),76);self.assertEqual(r['source_pins_including_NC'],182);self.assertEqual(len(r['bypass_associations']),10);self.assertEqual(sum(bool(p['panel_uid'])for p in r['placements'].values()),7)
 def test_all_bounded_exclusion_screens(self):
  for key,findings in self.r['source_checks'].items():self.assertEqual(findings,[],key)
 def test_all25_prior_pairs_classified(self):
  self.assertEqual(len(self.r['stage6_25_opposite_pairs']),25);self.assertTrue(all(x['classification']=='RESOLVED_BY_WHOLE_COURTYARD_EXCLUSION'for x in self.r['stage6_25_opposite_pairs']))
 def test_discrete_mounts_and_known_substrate_apertures(self):
  self.assertEqual(len(self.r['mounts']),7);self.assertEqual(len(self.r['foreign_through_pad_substrate_apertures']),42)
  self.assertTrue(all(x['connected_components']==1 for x in self.r['substrate_geometry_checks'].values()))
 def test_substrate_disconnection_is_reported(self):
  self.assertEqual(m.substrate_screen([0,0,10,10],[[4,0,6,10]])['connected_components'],2)
 def test_mount_clamp_straddles_board(self):
  s=copy.deepcopy(self.spec);s['mount']['spacer_z_mm']=[24.1,34]
  with self.assertRaisesRegex(AssertionError,'straddle'):self.altered(s)
 def test_fixed_panel_move_rejected(self):
  s=copy.deepcopy(self.spec);s['package_translations_from_stage6_mm']['J809']=[1,0]
  with self.assertRaisesRegex(AssertionError,'fixed'):self.altered(s)
 def test_collinear_mounts_rejected(self):
  s=copy.deepcopy(self.spec);s['boards']['X1-control']['mount_centres_mm']=[[108,269],[108,280],[108,289]]
  with self.assertRaisesRegex(AssertionError,'collinear'):self.altered(s)
 def test_package_outside_own_outline_rejected(self):
  s=copy.deepcopy(self.spec);s['package_translations_from_stage6_mm']['C3308']=[1000,0]
  with self.assertRaisesRegex(AssertionError,'own package/header outside'):self.altered(s)
 def test_header_outside_own_outline_rejected(self):
  interface=json.loads((m.OUT/'interface-input.json').read_text());headers=m.transport.transport_geometry(interface)
  header=next(h for h in headers.values()if h['board']=='X1-jack');header['box_mm']=[1000,1000,1010,1010]
  with patch.object(m.transport,'transport_geometry',return_value=headers):
   with self.assertRaisesRegex(AssertionError,'own package/header outside'):m.build()
 def test_current_bypass_distances_not_stale(self):
  rows={r['capacitor']:r for r in self.r['bypass_associations']};self.assertAlmostEqual(rows['C3308']['same_net_nearest_pad_mm']['+12V'],2.2975);self.assertAlmostEqual(rows['C3309']['same_net_nearest_pad_mm']['-12V'],2.3512775782539865)
  for b in rows.values():
   left=self.r['placements'][b['capacitor']];right=self.r['placements'][b['target']]
   for net,actual in b['same_net_nearest_pad_mm'].items():
    pts1=[xyz for pin,n in left['pins'].items()if n==net for xyz in left['pads_xyz_mm'][pin]];pts2=[xyz for pin,n in right['pins'].items()if n==net for xyz in right['pads_xyz_mm'][pin]];self.assertAlmostEqual(actual,min(math.dist(a,c)for a in pts1 for c in pts2))
 def test_five_fixture_bounds_not_hardware_claims(self):
  self.assertEqual(len(self.r['five_rear_fixture_projections']),5);self.assertTrue(all(not f['intersects_new_header_sweep']for f in self.r['five_rear_fixture_projections']));self.assertTrue(all('IF PROPOSED'in f['classification']for f in self.r['five_rear_fixture_projections']))
 def test_unknown_neighbors_and_structure_remain_open(self):
  self.assertFalse(self.r['physical_acceptance']);self.assertEqual(self.r['qualified_free_regions'],[]);self.assertTrue(self.r['historical_other_function_reservations']);self.assertIn('UNKNOWN',self.r['mount_load_path_acceptance'])
if __name__=='__main__':unittest.main()
