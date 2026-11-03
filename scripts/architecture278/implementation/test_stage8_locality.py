import copy,json,unittest
import stage8_locality as s
class Locality(unittest.TestCase):
 def setUp(self):
  self.seed=json.loads((s.a.OUT/'stage7/mechanical-report.json').read_text())['placements'];self.spec=json.loads((s.OUT/'placement-input.json').read_text())
 def test_complete_package_conservation(self):
  p=s.placements_from(self.seed,self.spec)
  self.assertEqual(len(p),56)
  for ref in p:
   for field in ['pins','units','side','board','source','panel_uid']:self.assertEqual(p[ref][field],self.seed[ref][field])
   if p[ref]['panel_uid']:self.assertEqual(p[ref],self.seed[ref])
 def test_fixed_move_rejected(self):
  self.spec['translations_from_stage7_mm']['J1009']=[1,0]
  with self.assertRaises(AssertionError):s.placements_from(self.seed,self.spec)
 def test_source_feedback_improved(self):
  p=s.placements_from(self.seed,self.spec)
  for ra,pa,rb,pb in [s.PAIRS[i]for i in [0,1,3]]:
   distance=lambda pop:s.math.dist(pop[ra]['pads_xyz_mm'][pa][0],pop[rb]['pads_xyz_mm'][pb][0])
   self.assertLess(distance(p),distance(self.seed))
 def test_segment_tangency_rejected(self):
  self.assertTrue(s.hit([0,1],[3,1],[1,1,2,2]))
 def test_width_clearance_blocks_gap(self):
  obs=[{'kind':'substrate','ref':'x','layers':[0,1],'box_mm':[2,2,3,3]}]
  self.assertTrue(s.free_segment([0,1.6],[5,1.6],obs,0,.3))
  self.assertFalse(s.free_segment([0,1.8],[5,1.8],obs,0,.3))
 def test_endpoint_exemption_not_hole(self):
  obs=[{'kind':'substrate','ref':'U','layers':[0,1],'box_mm':[2,2,3,3]}]
  self.assertFalse(s.free_segment([0,2.5],[5,2.5],obs,0,.1,'U'))
 def test_pad_sizes_bound_to_source(self):
  pads=s.pad_obstacles(self.seed)
  self.assertEqual(len(pads),sum(len(v)for p in self.seed.values()for v in p['pads_mm'].values()))
  self.assertEqual(next(p for p in pads if p['ref']=='J1009'and p['pin']=='T')['layers'],[0,1])
 def test_blocking_wall_cannot_be_crossed(self):
  settings=dict(self.spec['routing_proposal'],grid_step_mm=.25)
  end=lambda ref,x:{'ref':ref,'pad_xyz_mm':[x,5,20],'layers':[0],'box_mm':[x-.2,4.8,x+.2,5.2]}
  obs=[{'id':'wall','kind':'substrate','ref':'wall','layers':[0,1],'box_mm':[4,0,6,10]}]
  self.assertEqual(s.route(end('a',2),end('b',8),obs,[0,0,10,10],settings)['status'],'BLOCKED')
 def test_substrate_edge_clearance_is_distinct(self):
  obs=[{'kind':'substrate','ref':'cut','layers':[0,1],'box_mm':[2,2,3,3],'additional_edge_clearance_mm':.05}]
  self.assertFalse(s.free_segment([0,1.67],[5,1.67],obs,0,.3))
 def test_two_faces_require_explicit_vias(self):
  settings=dict(self.spec['routing_proposal'],grid_step_mm=.25)
  end=lambda ref,x:{'ref':ref,'pad_xyz_mm':[x,5,20],'layers':[0],'box_mm':[x-.2,4.8,x+.2,5.2]}
  obs=[{'id':'wall','kind':'courtyard','ref':'wall','layers':[0],'box_mm':[4,0,6,10]}]
  r=s.route(end('a',2),end('b',8),obs,[0,0,10,10],settings)
  self.assertEqual(r['status'],'CONDITIONAL_CORRIDOR');self.assertEqual(len(r['vias']),2)
  for v in r['vias']:self.assertEqual(v['drill_mm'],.3)
 def test_reserved_copper_blocks_other_net(self):
  o={'kind':'reserved_trace','ref':'earlier','layers':[1],'box_mm':[2,0,2.2,10]}
  self.assertFalse(s.free_segment([0,5],[5,5],[o],1,.3))
  self.assertTrue(s.free_segment([0,5],[5,5],[o],0,.3))
 def test_THT_terminal_barrel_separate_from_vias(self):
  ends=[{'ref':'J','pin':'T','layers':[0,1],'pad_xyz_mm':[1,1,20]},{'ref':'C','pin':'1','layers':[1],'pad_xyz_mm':[2,1,21.6]}]
  rows=s.endpoint_barrels([[1,1,1],[2,1,1]],ends)
  self.assertAlmostEqual(sum(r['barrel_mm']for r in rows),1.6)
  ends[0]['layers']=[0]
  with self.assertRaises(AssertionError):s.endpoint_barrels([[1,1,1],[2,1,1]],ends)
 def test_rotation_preserves_pad_net_identity(self):
  original=self.seed['C3308'];q=s.rotate_package(original,2)
  self.assertEqual(q['pins'],original['pins']);self.assertEqual(q['units'],original['units'])
  for pin,pts in original['pads_mm'].items():
   for p,new in zip(pts,q['pads_mm'][pin]):
    for i in (0,1):self.assertAlmostEqual(p[i]+new[i],2*original['origin_mm'][i])
  self.assertEqual(q['quarter_turn'],(original['quarter_turn']+2)%4)
if __name__=='__main__':unittest.main()
