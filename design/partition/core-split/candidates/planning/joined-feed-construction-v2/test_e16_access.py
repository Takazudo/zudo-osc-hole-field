import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from shapely.geometry import Point,Polygon
from shapely.strtree import STRtree
import normalize_board as nb
import clip_sheets as cs
import construct_access as ca

PCB='''(kicad_pcb (footprint "x" (layer "F.Cu") (uuid "fp") (at 110 60 90)
 (property "Reference" "U1" (at 0 0))
 (pad "1" smd roundrect (at 1 0 90) (size 2 1) (layers "F.Cu" "F.Mask") (roundrect_rratio .25) (net "AGND") (uuid "p1"))
 (pad "2" thru_hole circle (at -1 0 90) (size 1 1) (drill .5) (layers "*.Cu") (net "SIG") (uuid "p2"))
 (pad "" np_thru_hole circle (at 0 2 90) (size 1 1) (drill 1) (layers "*.Cu") (uuid "h1")))
 (segment (start 100 50) (end 101 50) (width .2) (layer "In2.Cu") (net "SIG") (uuid "s1"))
 (via (at 105 55) (size .6) (drill .3) (layers "F.Cu" "B.Cu") (net "SIG") (uuid "v1")))'''

def port(id,net,direct=True):return dict(board='KA',id=id,ref='U1',pad='1',net=net,source_direct_load_member=direct)

class Normalize(unittest.TestCase):
 def setUp(self):self.out=nb.normalize('KA',nb.parse(PCB),[],[port('p1','AGND')])
 def obj(self,i):return next(o for o in self.out['objects'] if o['id']==i)
 def test_pad_rotation_and_offset(self):
  # Footprint at (110,60) rotated 90 deg: local (+1,0) lands at (10,9) after the -(100,50) offset.
  p=self.obj('p1');self.assertEqual(p['center_mm'],[10.,9.])
  b=Polygon(p['polygon_mm']).bounds;self.assertAlmostEqual(b[2]-b[0],1.);self.assertAlmostEqual(b[3]-b[1],2.)
 def test_through_items_span_every_foil(self):
  self.assertEqual(self.obj('p2')['layers'],nb.LAYERS);self.assertEqual(self.obj('v1')['layers'],nb.LAYERS)
  self.assertEqual(self.obj('NPTH:h1')['kind'],'keepout')
 def test_rail_pad_set_must_equal_reviewed_ports(self):
  with self.assertRaisesRegex(ValueError,'differs from reviewed'):nb.normalize('KA',nb.parse(PCB),[],[])
 def test_loads_come_from_direct_members(self):
  self.assertEqual(self.out['loads'],[{'pad_id':'p1','net':'AGND','ref':'U1','pad':'1'}])

def via(id,net,x,y,d=.6):return dict(id=id,kind='via',net=net,layers=list(nb.LAYERS),center_mm=[x,y],diameter_mm=d,drill_mm=.3)
OUTLINE=[[0,0],[10,0],[10,10],[0,10]]

class Clip(unittest.TestCase):
 def test_other_net_copper_and_drill_are_cut_same_net_is_kept(self):
  src=dict(board='KA',objects=[via('a','AGND',3,3),via('b','SIG',7,7)])
  sheets,_=cs.clip(src,OUTLINE);g=Polygon(sheets['AGND'][0]['polygon_mm'],sheets['AGND'][0]['holes_mm'])
  self.assertTrue(g.contains(Point(3,3).buffer(.29)))
  self.assertFalse(g.intersects(Point(7,7).buffer(.3+cs.CLEARANCE_MM-.01)))
 def test_neck_below_min_width_is_removed(self):
  wall=[dict(id=f'w{i}',kind='segment',net='SIG',layers=['In1.Cu'],path_mm=[[5,y0],[5,y1]],width_mm=.2) for i,(y0,y1) in enumerate([(-1,4.9),(5.15,11)])]
  sheets,_=cs.clip(dict(board='KA',objects=wall),OUTLINE)
  self.assertEqual(len(sheets['AGND']),2)

class Access(unittest.TestCase):
 def sheet(self,y0,y1):
  # Two large blocks joined by one horizontal neck between y0 and y1.
  g=Polygon([[0,0],[4,0],[4,10],[0,10]]).union(Polygon([[6,0],[10,0],[10,10],[6,10]])).union(Polygon([[3.9,y0],[6.1,y0],[6.1,y1],[3.9,y1]]))
  return {'+5V':(STRtree([g]),[g])}
 def test_severance_guard_rejects_cut_of_narrow_neck(self):
  sheets=self.sheet(4.7,5.3)
  self.assertTrue(ca.severs(Point(5.,5.),'AGND',sheets))
  self.assertFalse(ca.severs(Point(2.,2.),'AGND',sheets))
  self.assertFalse(ca.severs(Point(5.,5.),'+5V',sheets))
 def test_cumulative_guard_uses_earlier_placements(self):
  sheets=self.sheet(4.2,5.8);first=ca.antipad(Point(5.,4.2))
  self.assertFalse(ca.severs(Point(5.,5.4),'AGND',sheets))
  self.assertTrue(ca.severs(Point(5.,5.4),'AGND',sheets,[('AGND',first)]))
 def test_route_reaches_feed_copper_around_foreign_pad(self):
  pad=dict(id='p',net='AGND',ref='U1',pad='11',layers=['F.Cu'],center_mm=[0,0],polygon_mm=[[-.75,-.3],[.75,-.3],[.75,.3],[-.75,.3]])
  blocker=dict(id='nc',kind='pad',net='NC',layers=['F.Cu'],center_mm=[0,1.27],polygon_mm=[[-.75,.97],[.75,.97],[.75,1.57],[-.75,1.57]])
  target=Polygon([[-.75,2.24],[.75,2.24],[.75,2.84],[-.75,2.84]])
  pts,why=ca.local_route(pad,'F.Cu','AGND',.25,ca.Obstacles([blocker]),ca.Obstacles([]),STRtree([target]))
  self.assertIsNone(why);(path,site)=pts;self.assertIsNone(site)
  self.assertGreater(max(x for x,_ in path),.75+ca.CLEARANCE)

if __name__=='__main__':unittest.main()
