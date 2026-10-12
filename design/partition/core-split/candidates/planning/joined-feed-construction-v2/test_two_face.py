import copy,sys,unittest,uuid
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from shapely.geometry import LineString,Point
import connectivity as c
import construct_access as ca
import two_face as tf

def pad(id,net,x,y=0,r=.05,layer='F.Cu',w=None):
 w=w or r
 return dict(id=id,kind='pad',net=net,ref='U1',pad=id,layers=[layer],center_mm=[x,y],polygon_mm=[[x-w,y-r],[x+w,y-r],[x+w,y+r],[x-w,y+r]])
def via(id,net,x,y=0,d=.6,drill=.3):return dict(id=id,kind='via',net=net,layers=list(ca.LAYERS),center_mm=[x,y],diameter_mm=d,drill_mm=drill)
def board(extra=()):
 # Feed terminal W1 (+12V) sits on B.Cu: no F.Cu feed copper exists, so a face-only route cannot close P.
 nets=['+12V','-12V','+5V','AGND','AGND','AGND']
 objs=[pad(f'CS247-KA-W{i+1}',n,i*10,layer='B.Cu' if i==0 else 'F.Cu') for i,n in enumerate(nets)]
 objs+=[pad('P','+12V',2.,w=.3,r=.15),via('T','+12V',1.)]+list(extra)
 src=dict(board='KA',objects=objs,loads=[dict(net='+12V',pad_id='P',ref='U1',pad='P')]+[dict(net=n,pad_id=objs[i]['id']) for i,n in enumerate(nets[1:4],1)])
 planes=dict(new_objects=[],clipped_sheets={n:[] for n in c.NET_LAYER})
 return src,planes
def census(graph):
 return dict(unresolved=[dict(pad_id=p['id']) for p in graph['physical_ports'] if not p['all_port_fragments_connected_to_feed']])
def attempt(src,planes,graph=None):
 graph=graph or c.build(src,planes);return tf.two_face_access(src,graph,census(graph),planes)

class TwoFace(unittest.TestCase):
 def test_route_through_existing_via_is_credited_by_the_graph(self):
  src,planes=board();before=c.build(src,planes)
  self.assertIn('P',[r['pad_id'] for r in census(before)['unresolved']])
  # The existing single-face route method cannot close it.
  self.assertEqual(next(x for x in ca.route_access(src,before,census(before))[1] if x['pad_id']=='P')['status'],'NO_ROUTE')
  added,results=attempt(src,planes,before);r=next(x for x in results if x['pad_id']=='P')
  self.assertEqual(r['status'],'ROUTED_TWO_FACE');self.assertEqual(r['transition']['id'],'T')
  self.assertEqual({o['layers'][0] for o in added},{'F.Cu','B.Cu'})
  self.assertTrue(all(v>tf.CONTACT_AREA for v in r['contact_area_mm2'].values()))
  after=c.build(dict(src,objects=src['objects']+added),planes)
  port=next(p for p in after['physical_ports'] if p['id']=='P');self.assertTrue(port['all_port_fragments_connected_to_feed'])
  self.assertTrue(after['object_connections']['T']['all_fragments_connected_to_feed'])
 def test_route_without_transition_copper_on_both_faces_is_not_credited(self):
  src,planes=board();before=c.build(src,planes);added,_=attempt(src,planes,before)
  # Drop the opposite-face leg: the pad now reaches only an isolated via.
  half=[o for o in added if o['layers']==['F.Cu']]
  after=c.build(dict(src,objects=src['objects']+half),planes)
  self.assertFalse(next(p for p in after['physical_ports'] if p['id']=='P')['all_port_fragments_connected_to_feed'])
 def test_foreign_net_transition_is_never_used(self):
  src,planes=board();next(o for o in src['objects'] if o['id']=='T')['net']='SIG'
  _,results=attempt(src,planes);r=next(x for x in results if x['pad_id']=='P')
  self.assertEqual(r['status'],'NO_TWO_FACE_ROUTE');self.assertIn('no_same_net_transition_in_window',r['reasons'])
 def test_transition_with_cut_barrel_wall_is_refused(self):
  src,planes=board();graph=c.build(src,planes)
  src['objects'].append(dict(id='NPTH:cut',kind='keepout',net='',layers=list(ca.LAYERS),center_mm=[1.2,0],drill_mm=.1))
  _,results=attempt(src,planes,graph);r=next(x for x in results if x['pad_id']=='P')
  self.assertEqual(r['status'],'NO_TWO_FACE_ROUTE');self.assertIn('transition_wall_cut',r['reasons'])
 def test_opposite_leg_keeps_foreign_drill_and_copper_clearance(self):
  blocker=via('X','SIG',.5,d=.3,drill=.15);src,planes=board([blocker]);added,results=attempt(src,planes)
  r=next(x for x in results if x['pad_id']=='P');self.assertEqual(r['status'],'ROUTED_TWO_FACE')
  for o in added:
   line=LineString(o['path_mm'])
   self.assertGreaterEqual(line.distance(Point(.5,0)),.15+ca.CLEARANCE+o['width_mm']/2-1e-6)
  after=c.build(dict(src,objects=src['objects']+added),planes)
  self.assertTrue(next(p for p in after['physical_ports'] if p['id']=='P')['all_port_fragments_connected_to_feed'])
 def test_duplicate_new_identity_is_refused(self):
  src,planes=board();graph=c.build(src,planes)
  clash=str(uuid.uuid5(ca.NS,'KA:P:two-face:0:0'));src['objects'].append(dict(pad('dummy','SIG',40.),id=clash))
  with self.assertRaisesRegex(ValueError,'duplicate object identity'):attempt(src,planes,graph)
 def test_already_feed_connected_transition_is_not_a_two_face_route(self):
  feed=dict(id='S',kind='segment',net='+12V',layers=['B.Cu'],path_mm=[[0,0],[1,0]],width_mm=.2)
  src,planes=board([feed])
  _,results=attempt(src,planes);r=next(x for x in results if x['pad_id']=='P')
  self.assertNotEqual(r.get('transition',{}).get('id'),'T')
  self.assertIn('transition_already_feed_connected',r.get('reasons',{}))

class Coaxial(unittest.TestCase):
 def test_transition_sharing_its_bore_with_another_object_is_refused(self):
  src,planes=board();graph=c.build(src,planes)
  src['objects'].append(dict(id='NPTH:coax',kind='keepout',net='',layers=list(ca.LAYERS),center_mm=[1.,0],drill_mm=.3))
  _,results=tf.two_face_access(src,graph,census(graph),planes);r=next(x for x in results if x['pad_id']=='P')
  self.assertEqual(r['status'],'NO_TWO_FACE_ROUTE');self.assertIn('transition_bore_shared',r['reasons'])

if __name__=='__main__':unittest.main()
