import copy,gzip,importlib.util,json,sys,unittest
import numpy as np
import check_ends as m
import mechanical
class ProxyTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  d=mechanical.build();cls.solids={s['id']:s for s in d['solids']};cls.term=next(t for t in d['wire_termination_regions'] if t['board']=='KA' and t['wire']==1);cls.collet=cls.solids['KA/w1/collet']
 def test_both_reviewed_lugs_accepted(self):
  for name in ['lug','lug-tongue']:
   q=m.lug_proxy(self.solids['KA/w1/'+name],self.collet,self.term);self.assertEqual(q['holes'][-1]['kind'],'proved_own_collet_annulus')
 def test_outside_grip_rejected(self):
  q=copy.deepcopy(self.solids['KA/w1/lug']);q['center_xyz_mm']=(np.array(q['center_xyz_mm'])+3*np.array(self.term['axis_from_land_xyz'])).tolist()
  with self.assertRaisesRegex(ValueError,'not confined'):m.lug_proxy(q,self.collet,self.term)
 def test_inside_bore_rejected(self):
  q=copy.deepcopy(self.solids['KA/w1/lug']);w=np.array(self.term['axis_from_land_xyz']);land=np.array(self.term['land_xyz_mm']);d=np.array(q['center_xyz_mm'])-land;rad=d-(d@w)*w;q['center_xyz_mm']=(np.array(q['center_xyz_mm'])-.9*rad).tolist()
  with self.assertRaisesRegex(ValueError,'not confined'):m.lug_proxy(q,self.collet,self.term)
 def test_extended_negative_has_no_artificial_endcap_penalty(self):
  q=m.lug_proxy(self.solids['KA/w1/lug'],self.collet,self.term);w=np.array(self.term['axis_from_land_xyz']);land=np.array(self.term['land_xyz_mm']);L=self.term['bridge_axis_length_mm'];p=land+(L+2.5)*w
  self.assertGreaterEqual(float(m.cg.primitive_distance([p],q)[0]),2.-1e-9)
 def test_cover_contains_axis_cell_end_disks(self):
  p,r=m.cover([0,0,0],[1,0,0],0,1,1,n=2)
  for j in range(2):
   for x in [j*.5,(j+1)*.5]:self.assertLessEqual(np.linalg.norm(np.array([x,1,0])-p[j]),r[j])
if __name__=='__main__':unittest.main()
