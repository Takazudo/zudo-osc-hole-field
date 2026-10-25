import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import finite_network as fn

CASE=dict(rho_ohm_mm=2e-5,inner_copper_mm=.07,outer_copper_mm=.07,barrel_plating_mm=.018,wire_plus_termination_ohm=1e-3,ideal_join_ohm=1e-9)
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
def sq(x,y,r):return [[x-r,y-r],[x+r,y-r],[x+r,y+r],[x-r,y+r]]
def pad(id,net,x,y,r=.4):return dict(id=id,kind='pad',net=net,layers=['F.Cu'],polygon_mm=sq(x,y,r),center_mm=[x,y])
def via(id,net,x,y):return dict(id=id,kind='via',net=net,layers=LAYERS,center_mm=[x,y],diameter_mm=.6,drill_mm=.3)
def strip(net,x0,x1,y0=-1.,y1=1.):return dict(id=f'{net}-SHEET-0000',polygon_mm=[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],holes_mm=[])
def world(net,terms,loads,sheet,extra=()):
 objs=[pad(t,net,x,0) for t,x in terms]+[via(t+'v',net,x,0) for t,x in terms]
 objs+=[pad(l,net,x,0) for l,x in loads]+[via(l+'v',net,x,0) for l,x in loads]+list(extra)
 fed={o['id']:{'all_fragments_connected_to_feed':True} for o in objs}|{sheet['id']:{'all_fragments_connected_to_feed':True}}
 return dict(board='KA',objects=objs),dict(clipped_sheets={net:[sheet]}),dict(object_connections=fed)
def run(net,terms,loads,sheet,removed=(),pitch=.1,extra=()):
 s,p,g=world(net,terms,loads,sheet,extra);G,ports,wires,meta=fn.build(s,p,g,net,CASE,pitch,removed)
 return fn.solve(G,ports,wires,[l for l,_ in loads]),meta

class FiniteNetwork(unittest.TestCase):
 def test_strip_matches_sheet_barrel_and_wire_series_sum(self):
  # +12V: terminal W1 at x=0, load at x=10 on a 2 mm wide strip -> 5 squares.
  (sol,miss),meta=run('+12V',[('CS247-KA-W1',0.)],[('L',10.)],strip('+12V',-1,11))
  self.assertEqual(miss,[])
  sheet=CASE['rho_ohm_mm']/CASE['inner_copper_mm']*10/2;leg=fn.barrel_ohm(2e-5,fn.BOARD_THICKNESS,.3,.018)
  expect=sheet+2*leg+CASE['wire_plus_termination_ohm']
  self.assertAlmostEqual(sol['L']['potential_ohm'],expect,delta=.05*expect)
  self.assertAlmostEqual(sol['L']['wire_current_fraction'][1],1.,places=6)
 def test_three_returns_share_unequally_and_conserve_current(self):
  terms=[('CS247-KA-W4',0.),('CS247-KA-W5',4.),('CS247-KA-W6',20.)]
  (sol,_),_=run('AGND',terms,[('L',2.)],strip('AGND',-1,21))
  f=sol['L']['wire_current_fraction'];self.assertAlmostEqual(sum(f.values()),1.,places=6)
  self.assertGreater(f[4],f[6]);self.assertGreater(f[5],f[6]);self.assertGreater(f[6],0.)
 def test_return_removal_moves_current_to_the_remaining_wires(self):
  terms=[('CS247-KA-W4',0.),('CS247-KA-W5',4.),('CS247-KA-W6',20.)]
  (full,_),_=run('AGND',terms,[('L',2.)],strip('AGND',-1,21))
  (cut,_),_=run('AGND',terms,[('L',2.)],strip('AGND',-1,21),removed=(4,))
  self.assertNotIn(4,cut['L']['wire_current_fraction']);self.assertAlmostEqual(sum(cut['L']['wire_current_fraction'].values()),1.,places=6)
  self.assertGreater(cut['L']['potential_ohm'],full['L']['potential_ohm'])
 def test_port_on_unconnected_sheet_is_reported_missing(self):
  s,p,g=world('+12V',[('CS247-KA-W1',0.)],[('L',10.)],strip('+12V',-1,3))
  G,ports,wires,_=fn.build(s,p,g,'+12V',CASE,.1);sol,miss=fn.solve(G,ports,wires,['L'])
  self.assertEqual(miss,['L']);self.assertEqual(sol,{})
 def test_barrel_in_a_void_is_not_joined_to_a_neighbouring_piece(self):
  # The load via sits 0.3 mm outside the strip end: within reach of its cells but not inside the piece.
  s,p,g=world('+12V',[('CS247-KA-W1',0.)],[('L',11.3)],strip('+12V',-1,11))
  G,ports,wires,meta=fn.build(s,p,g,'+12V',CASE,.1);sol,miss=fn.solve(G,ports,wires,['L'])
  self.assertEqual(miss,['L']);self.assertEqual(meta['barrels_without_sheet_cell'],1)
 def test_face_trace_is_charged_once(self):
  # Load reached only by a 2 mm face trace to the terminal pad: R = trace + wire, no sheet or barrel.
  trace=dict(id='t',kind='segment',net='+12V',layers=['F.Cu'],path_mm=[[0,0],[2.,0]],width_mm=.25)
  objs=[pad('CS247-KA-W1','+12V',0,0,.1),pad('L','+12V',2.,0,.1),trace]
  fed={o['id']:{'all_fragments_connected_to_feed':True} for o in objs}
  G,ports,wires,_=fn.build(dict(board='KA',objects=objs),dict(clipped_sheets={'+12V':[]}),dict(object_connections=fed),'+12V',CASE,.1)
  sol,_=fn.solve(G,ports,wires,['L'])
  self.assertAlmostEqual(sol['L']['potential_ohm'],2e-5*2/(.25*.07)+1e-3,delta=1e-6)

if __name__=='__main__':unittest.main()
