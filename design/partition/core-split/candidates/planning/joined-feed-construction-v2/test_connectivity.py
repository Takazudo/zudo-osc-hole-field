import sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import connectivity as c

def pad(id,net,x,y=0,r=.05,layer='F.Cu'):
 return dict(id=id,kind='pad',net=net,layers=[layer],polygon_mm=[[x-r,y-r],[x+r,y-r],[x+r,y+r],[x-r,y+r]])
def base():
 nets=['+12V','-12V','+5V','AGND','AGND','AGND'];objs=[pad(f'CS247-KA-W{i+1}',n,i*10) for i,n in enumerate(nets)]
 return dict(board='KA',objects=objs,loads=[dict(net=n,pad_id=objs[i]['id']) for i,n in enumerate(nets[:4])]),dict(new_objects=[],clipped_sheets={n:[] for n in c.NET_LAYER})
class Tests(unittest.TestCase):
 def test_control(self):
  s,p=base();self.assertEqual(c.build(s,p)['status'],'SOURCE_ALL_DIRECT_LOADS_CONNECTED')
 def test_missing_net(self):
  s,p=base();s['loads']=[x for x in s['loads'] if x['net']!='+5V']
  with self.assertRaisesRegex(ValueError,'four-net'):c.build(s,p)
 def test_foreign_drill_erases_port(self):
  s,p=base();s['objects'] += [dict(id='foreign-hole',kind='keepout',net='FOREIGN',layers=['F.Cu'],center_mm=[0,0],drill_mm=.2)]
  self.assertEqual(len(c.build(s,p)['disconnected_loads']),1)
 def test_partial_pad_is_not_complete(self):
  s,p=base();s['objects'][0]=pad('CS247-KA-W1','+12V',0,r=.2)
  a=pad('partial','+12V',1,r=.1);a['polygon_mm']=[[-.1,-.1],[2.1,-.1],[2.1,.1],[-.1,.1]]
  s['objects'] += [a,dict(id='foreign-hole',kind='keepout',net='OTHER',layers=['F.Cu'],center_mm=[1,0],drill_mm=1.2)]
  s['loads'][0]['pad_id']='partial';r=c.build(s,p);port=next(x for x in r['physical_ports'] if x['id']=='partial')
  self.assertTrue(port['any_fragment_connected']);self.assertFalse(port['all_port_fragments_connected_to_feed'])
 def test_split_via_remote_piece_not_barrel(self):
  s,p=base();s['objects'][0]=pad('CS247-KA-W1','+12V',.22,r=.025)
  s['objects'] += [dict(id='split-via',kind='via',net='+12V',layers=['F.Cu','B.Cu'],center_mm=[0,0],diameter_mm=2.,drill_mm=.3),pad('remote','+12V',.96,r=.015,layer='B.Cu')]
  s['objects'] += [dict(id=f'foreign{i}',kind='keepout',net='OTHER',layers=['F.Cu','B.Cu'],center_mm=[.6,y],drill_mm=.62) for i,y in enumerate([-.6,0,.6])]
  s['loads'][0]['pad_id']='remote';r=c.build(s,p);self.assertTrue(any(x['pad_id']=='remote' for x in r['disconnected_loads']))
 def test_other_drill_cuts_wall_refused(self):
  s,p=base();s['objects'] += [dict(id='v',kind='via',net='+12V',layers=['F.Cu','B.Cu'],center_mm=[0,0],diameter_mm=.7,drill_mm=.3),dict(id='cut',kind='keepout',net='OTHER',layers=['F.Cu'],center_mm=[.2,0],drill_mm=.1)]
  with self.assertRaisesRegex(ValueError,'cuts declared continuous barrel wall'):c.build(s,p)
 def test_coaxial_equal_bore_allowed(self):
  s,p=base();s['objects'][0]=pad('CS247-KA-W1','+12V',.25,r=.03)
  s['objects'] += [dict(id='v',kind='via',net='+12V',layers=['F.Cu','B.Cu'],center_mm=[0,0],diameter_mm=.7,drill_mm=.3),dict(id='same',kind='keepout',net='OTHER',layers=['F.Cu'],center_mm=[0,0],drill_mm=.3)]
  self.assertEqual(c.build(s,p)['status'],'SOURCE_ALL_DIRECT_LOADS_CONNECTED')
if __name__=='__main__':unittest.main()
