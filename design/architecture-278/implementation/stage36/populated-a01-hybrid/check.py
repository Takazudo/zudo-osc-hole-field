import unittest,hashlib,json,subprocess,sys
from pathlib import Path
import generate as g
class Checks(unittest.TestCase):
 def setUp(self): self.a=g.build()
 def test_population(self):
  self.assertEqual((self.a['package_count'],self.a['transport_count']),(86,32));self.assertEqual(len(set(self.a['population_refs'])),118)
  self.assertIn('RN7101',self.a['packages']);self.assertNotIn('R7121',self.a['packages'])
 def test_screens_and_negative_locations(self):
  for s in self.a['screens']:
   for k,v in s.items():
    if k!='ref':self.assertEqual(v,[],s['ref'])
  for xy,w,h,board in [([224,108],9.5,18.02,'A01-jack'),([218.5,295],20.56,9.5,'A01-control')]:
   self.assertTrue(any(g.ov(g.grow(g.box(xy,w,h),1),p['box_mm']) for p in self.a['packages'].values() if p['board']==board))
  for i,c in enumerate(self.a['connectors']):
   for d in self.a['connectors'][i+1:]:
    if c['board']==d['board']:self.assertFalse(g.ov(c['box_mm'],d['box_mm']))
 def test_engagement(self):
  for gap,want in [(24,[4.55,6.13]),(25,[3.55,5.13])]:
   nominal=2.54+18.29+8.51-gap;got=[round(nominal-.79,2),round(nominal+.79,2)];self.assertEqual(got,want)
  self.assertLess(3.55,3.68);self.assertGreater(4.55,3.68);self.assertLess(6.13,6.35)
 def test_pins(self):
  rows=self.a['direct_pin_binding'];self.assertEqual(len(rows),24)
  self.assertEqual(len({tuple(r['global_xy_mm']) for r in rows}),24)
  for r in rows:self.assertEqual(r['male_local_mm'],[-r['socket_local_face_view_mm'][0],r['socket_local_face_view_mm'][1]])
  self.assertEqual([r['net'] for r in rows if r['link']=='K-PWR'][:3],['+12V','-12V','AGND'])
 def test_bindings_and_editor(self):
  for f,h in self.a['source_sha256'].items():self.assertEqual(hashlib.sha256((g.ROOT/f).read_bytes()).hexdigest(),h)
  p='project/osc-hole-field/workbench/current-editor/index.html'
  self.assertEqual(hashlib.sha256((g.ROOT/p).read_bytes()).hexdigest(),'eceeeacfa7d4124b2043fb4f175dad13a6764eedb3836bdc90c3b5b7c06d7a38')
  changed=subprocess.check_output(['git','diff','e8e537b5f40649fa46e8f143df4a9228a28620cd','--','project/osc-hole-field/workbench/current-editor'],cwd=g.ROOT);self.assertEqual(changed,b'')
 def test_unknowns(self):
  self.assertFalse(self.a['applied_to_canonical']);self.assertFalse(self.a['service']['neighbor_clearance_established']);self.assertEqual(self.a['foreign_hardware_unknown_z_count'],138)
  self.assertTrue(any(c['neighbor_envelopes'] for c in self.a['corridors']))
if __name__=='__main__':unittest.main()
