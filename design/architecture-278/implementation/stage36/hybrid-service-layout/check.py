import unittest,json,hashlib,subprocess
from pathlib import Path
import generate as g
class Checks(unittest.TestCase):
 def setUp(self):self.a=g.build()
 def test_legacy_compatibility(self):
  t=json.loads(g.T.read_text())
  for link,v in self.a['pin_maps'].items():
   for ref in v['refs']:
    for k,net in t[ref]['pins'].items():
     if k.isdigit():self.assertEqual(v['pins'][k],net)
   self.assertTrue(all(net is None for pin,net in v['pins'].items() if pin not in v['legacy_active_pins']))
  self.assertEqual(self.a['pin_maps']['J-PWR']['pins']['3'],'+5V')
  self.assertEqual(self.a['pin_maps']['J-SIG']['pins']['1'],'/A01/REF5')
  self.assertEqual(self.a['pin_maps']['C-SIG']['pins']['2'],'/A01/REFN5')
 def test_orientation(self):
  for c in self.a['connector_coordinates']:
   for p in c['pins']:
    x,y=p['header_face_xy'];sx,sy=p['socket_face_xy'];self.assertEqual([x,y],[sx,-sy])
   self.assertLess(c['pins'][0]['header_face_xy'][1],0)
   self.assertGreater(c['pins'][0]['socket_face_xy'][1],0)
   self.assertEqual(len({tuple(p['global_xy']) for p in c['pins']}),len(c['pins']))
  j=next(c for c in self.a['connector_coordinates'] if c['ref']=='J17905')
  self.assertEqual(j['rotation_deg'],90);self.assertGreater(j['pins'][0]['global_xy'][0],j['centre_mm'][0])
 def test_supports_and_preserved_failure(self):
  self.assertEqual(self.a['known_obstacle_hits'],[]);self.assertEqual(self.a['new_fastener_package_hits'],[]);self.assertEqual(self.a['new_crossbar_retained_support_hits'],[])
  bars=[s for s in self.a['supports'] if s['id'].startswith('middle-load')];rails=[s for s in self.a['supports'] if s['id'].startswith('middle-rails')]
  self.assertTrue(any(g.hit(a,b) for a in bars for b in rails))
  old={'xy':[208,303,229,307],'z':[12,20]};header=next(b for b in self.a['known_obstacles'] if b['id']=='J17901');self.assertTrue(g.hit(old,header))
 def test_subtract_conserves_volume(self):
  b={'xy':[0,0,10,10],'z':[0,10]};c={'xy':[2,2,8,8],'z':[2,8]};pieces=g.subtract(b,c)
  vol=lambda q:(q['xy'][2]-q['xy'][0])*(q['xy'][3]-q['xy'][1])*(q['z'][1]-q['z'][0])
  self.assertEqual(sum(map(vol,pieces)),1000-216)
  self.assertTrue(all(not g.hit(q,c) for q in pieces))
  self.assertTrue(all(not g.hit(q,r) for i,q in enumerate(pieces) for r in pieces[i+1:]))
 def test_unknowns_not_cleared(self):
  r=self.a['neighbor_recovery'];self.assertEqual((r['unique_refs'],r['repeated_projection_rows'],len(r['pots_with_relative_source_depth'])),(85,138,21));self.assertEqual(r['qualified_free_regions'],[])
  self.assertTrue(any(q['ref']=='RV1408' and q['support']=='control-right-lower' for q in self.a['unknown_support_projection_hits']))
  self.assertTrue(all(q['absolute_z'] is None for q in self.a['unknown_obstacles']))
 def test_cad_rejected_inference(self):
  a=json.loads((g.H/'cad-report.json').read_text())
  for n in ['8','10','14']:
   self.assertIsNone(a[n]['relief_installed_height']);self.assertGreater(a[n]['closed_body_cap_intersection_mm3'],100)
   self.assertEqual(a[n]['native_key_fit_plastic_intersection_mm3']['(0, 1, 0)'],0)
   self.assertGreater(a[n]['native_key_fit_plastic_intersection_mm3']['(1, 0, 0)'],15)
 def test_bindings_preservation(self):
  for f,h in self.a['source_sha256'].items():self.assertEqual(hashlib.sha256((g.R/f).read_bytes()).hexdigest(),h)
  changed=subprocess.check_output(['git','diff','51aa218dc5eb17c22fd13531e04c115da87c8520','--','project/osc-hole-field/workbench/current-editor','design/grid/placements.lock.json'],cwd=g.R);self.assertEqual(changed,b'')
if __name__=='__main__':unittest.main()
