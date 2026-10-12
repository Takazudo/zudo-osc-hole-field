import unittest
import board_context as b

class ProducerContractTests(unittest.TestCase):
 def via(self,kind,layers):
  return {'id':'KA-test','kind':'via','via_type':kind,'layers':layers,'net':'AGND','center_mm':[20,30],'diameter_mm':.15,'drill_mm':.075,'source_pad_uuid':'test-pad'}
 def test_staged_producer_microvia_alias(self):
  out=b.serialize_new(self.via('microvia',['B.Cu','In4.Cu']))
  self.assertIn('(via micro ',out);self.assertIn('(layers "In4.Cu" "B.Cu")',out);self.assertIn('(at 120.000000000 80.000000000)',out)
 def test_staged_producer_buried_alias(self):
  out=b.serialize_new(self.via('buried_via',['In2.Cu','In3.Cu']))
  self.assertIn('(via buried ',out)
 def test_new_required_process_overrides_old_global_default(self):
  obj=self.via('microvia',['F.Cu','In1.Cu']);obj['filled_and_capped_required']=True
  out=b.serialize_new(obj);self.assertIn('(capping yes)',out);self.assertIn('(filling yes)',out)
 def test_no_implicit_short_across_layers(self):
  with self.assertRaisesRegex(ValueError,'adjacent'):b.serialize_new(self.via('microvia',['F.Cu','In4.Cu']))
  with self.assertRaisesRegex(ValueError,'all layers'):b.serialize_new(self.via('through',['F.Cu','In1.Cu']))
 def test_unknown_process_rejected(self):
  with self.assertRaisesRegex(ValueError,'known via'):b.serialize_new(self.via('magic',['F.Cu','In1.Cu']))
 def test_positive_explicit_bands_keep_fixed_thickness(self):
  _,rows=b.stack();self.assertEqual(len(rows),11)
  self.assertAlmostEqual(rows[-1]['depth_band_mm'][1],1.6)
  for a,c in zip(rows,rows[1:]):self.assertAlmostEqual(a['depth_band_mm'][1],c['depth_band_mm'][0])
  self.assertEqual([r['layer'] for r in rows if r['layer'].endswith('.Cu')],b.LAYERS)
 def test_source_plane_is_not_native_fill(self):
  out=b.serialize_new({'id':'test','kind':'zone','net':'AGND','layers':['In1.Cu'],'new_source_polygon_unfilled':True,'polygon_mm':[[0,0],[10,0],[10,10],[0,10]]})
  self.assertIn('(polygon ',out);self.assertNotIn('filled_polygon',out)

if __name__=='__main__':unittest.main()
