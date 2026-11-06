import unittest,json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[4]
class ReviewSource(unittest.TestCase):
 def setUp(self): self.d=json.loads((P/'view-data.json').read_text())
 def test_exact_fixed_markers_and_complete_functions(self):
  self.assertEqual(self.d['placements'],json.loads((R/'design/grid/placements.lock.json').read_text())['placements'])
  self.assertEqual({x['id'] for x in self.d['coverage']},{x['id'] for x in json.loads((R/'project/osc-hole-field/block-contracts.json').read_text())})
  self.assertEqual(len(self.d['coverage']),33);self.assertEqual(len(self.d['placements']),438)
 def test_every_block_has_middle_rear_and_no_free_space_claim(self):
  for b in self.d['coverage']:
   for layer in ['middle','rear']:self.assertTrue(any(x['block']==b['id'] and x['layer']==layer for x in self.d['boxes']))
  self.assertGreater(len(self.d['overlaps']),0);self.assertEqual(self.d['rules']['capacity'],'UNKNOWN')
 def test_overlap_identity(self):
  byname={b['name']:b['block'] for b in self.d['boxes']}
  for x in self.d['overlaps']:self.assertEqual(x['blocks'],[byname[x['a']],byname[x['b']]])
 def test_sources(self):
  for p,h in self.d['sources'].items():self.assertEqual(hashlib.sha256((R/p).read_bytes()).hexdigest(),h,p)
 def test_a01_preserved(self):
  prior=json.loads((P.parent/'structure-review/view-data.json').read_text())
  for q in prior['boxes']:
   if q['layer'] in ['front','middle','rear']:
    b=next(x for x in self.d['boxes'] if x['name']==q['name']);self.assertEqual(b['xy'],q['xy']);self.assertEqual(b['z'],q['z'])
 def test_incumbent_polygons_exact_sign_conversion(self):
  inc=json.loads((R/'design/partition/partition.json').read_text())
  self.assertEqual(len(self.d['incumbent']),len(inc['boards']))
  for b,q in zip(self.d['incumbent'],inc['boards']):self.assertEqual(b['polygon'],q['outline']);self.assertEqual(b['z'],-q['face_z_mm'])
if __name__=='__main__':unittest.main()
