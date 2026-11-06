import copy
import json
import unittest
import stage10_assessment as s
class AssessmentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.inv=json.loads((s.OUT/'inventory-report.json').read_text());cls.scope=json.loads((s.OUT/'scope.json').read_text())
  cls.faces={'A01-fixed':{'panel':20,'rear':21.6},'A01-jack':{'panel':35,'rear':36.6},'A01-control':{'panel':10,'rear':11.6},'A01-core':{'panel':69.2,'rear':70.8}}
  fixed={p['ref']:p for p in cls.inv['fixed_controls']};cls.placements={}
  for ref,p in cls.inv['packages'].items():
   board='A01-fixed'if p['owner']=='front-jack'and p['attributes']['PanelUid']else{'front-jack':'A01-jack','front-control':'A01-control','rear-core':'A01-core'}[p['owner']];f=fixed.get(ref);origin=[f['x_mm'],f['y_mm']]if f else[0,0];turn=f['rot_deg']//90 if f else 0
   path='footprints/kicad/zudo-osc-hole-field.pretty/'+p['footprint'].split(':')[1]+'.kicad_mod';pads={}
   for pin,points in s.source_geometry.footprint_pads(path).items():
    pads[pin]=[]
    for x,y in points:
     for _ in range(turn):x,y=-y,x
     pads[pin].append([x+origin[0],y+origin[1],cls.faces[board]['panel']])
   cls.placements[ref]={'pins':p['pins'],'units':p['units'],'owner':p['owner'],'board':board,'source':path,'origin_mm':origin,'quarter_turn':turn,'side':'panel','pads_xyz_mm':pads}
 def test_complete_source_composition(self):self.assertEqual(s.population(self.inv,self.placements,self.faces)['K'],29)
 def test_removed_package_or_unit(self):
  p=copy.deepcopy(self.placements);p.pop(next(iter(p)))
  with self.assertRaisesRegex(ValueError,'population'):s.population(self.inv,p,self.faces)
  p=copy.deepcopy(self.placements);ref=next(r for r,q in p.items()if len(q['units'])>1);p[ref]['units'].pop()
  with self.assertRaisesRegex(ValueError,'units'):s.population(self.inv,p,self.faces)
 def test_NC_rewired_or_pad_omitted(self):
  ref,pin=next((r,n)for r,p in self.placements.items()for n,v in p['pins'].items()if v is None)
  p=copy.deepcopy(self.placements);p[ref]['pins'][pin]='AGND'
  with self.assertRaisesRegex(ValueError,'pin/net/NC'):s.population(self.inv,p,self.faces)
  p=copy.deepcopy(self.placements);p[ref]['pads_xyz_mm'].pop(pin)
  with self.assertRaisesRegex(ValueError,'pad transform|physical pad'):s.population(self.inv,p,self.faces)
 def test_fixed_control_moved(self):
  p=copy.deepcopy(self.placements);p['RV1308']['origin_mm'][0]+=.1
  with self.assertRaisesRegex(ValueError,'pad transform|fixed centre'):s.population(self.inv,p,self.faces)
 def test_bypass_split(self):
  p=copy.deepcopy(self.placements);p[self.inv['bypass_associations'][0]['bypass_ref']]['board']='unowned-board'
  with self.assertRaisesRegex(ValueError,'unowned physical board|bypass'):s.population(self.inv,p,self.faces)
 def test_nonfinite_or_empty_pad(self):
  ref=next(iter(self.placements));pin=next(iter(self.placements[ref]['pins']))
  for pts in ([],[[float('nan'),0,0]]):
   p=copy.deepcopy(self.placements);p[ref]['pads_xyz_mm'][pin]=pts
   with self.assertRaisesRegex(ValueError,'pad transform|geometry'):s.population(self.inv,p,self.faces)
 def test_finite_fake_pad_or_wrong_plane(self):
  for axis in (0,2):
   p=copy.deepcopy(self.placements);ref=next(iter(p));pin=next(iter(p[ref]['pads_xyz_mm']));p[ref]['pads_xyz_mm'][pin][0][axis]+=.1
   with self.assertRaisesRegex(ValueError,'pad transform'):s.population(self.inv,p,self.faces)
 def test_whole_bypass_cluster_on_unowned_board(self):
  p=copy.deepcopy(self.placements);pair=self.inv['bypass_associations'][0]
  for ref in (pair['bypass_ref'],pair['target_ref']):p[ref]['board']='unowned-board'
  with self.assertRaisesRegex(ValueError,'unowned physical board'):s.population(self.inv,p,self.faces)
 def test_prior_stage_mutation(self):
  p=copy.deepcopy(self.scope);p['preserved_prior_source_sha256'][next(iter(p['preserved_prior_source_sha256']))]='0'*64
  with self.assertRaisesRegex(ValueError,'prior candidate'):s.preserve(p)
 def test_missing_or_stale_binding(self):
  for r in ({},{'source_sha256':{'design/architecture-278/implementation/stage10/scope.json':'0'*64}}):
   with self.assertRaises(ValueError):s.bindings(r)
class TransportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.inv=json.loads((s.OUT/'inventory-report.json').read_text());cls.graph=json.loads((s.OUT/'interfaces-report.json').read_text());cls.elec=json.loads((s.OUT/'electrical-report.json').read_text());cls.placed=json.loads((s.OUT/'mechanical-report.json').read_text())['placements']
 def test_full_graph_composition(self):self.assertEqual(s.transport(self.inv,self.graph,self.elec,self.placed)['physical_wires'],34)
 def test_graph_binding_or_endpoint_omission(self):
  g=copy.deepcopy(self.graph);g['wires'].pop()
  with self.assertRaisesRegex(ValueError,'binding'):s.transport(self.inv,g,self.elec,self.placed)
  e=copy.deepcopy(self.elec);e['local_endpoint_paths'].pop()
  with self.assertRaisesRegex(ValueError,'coverage'):s.transport(self.inv,self.graph,e,self.placed)
 def test_wrong_net_or_length(self):
  for key,value in [('net','AGND'),('complete_net_pad_path_allocation_mm',0)]:
   e=copy.deepcopy(self.elec);e['signal_net_paths'][0][key]=value
   with self.assertRaisesRegex(ValueError,'net|sum'):s.transport(self.inv,self.graph,e,self.placed)
 def test_omitted_tail_count(self):
  e=copy.deepcopy(self.elec);e['counts']['physical_wires']=20
  with self.assertRaisesRegex(ValueError,'wire inventory'):s.transport(self.inv,self.graph,e,self.placed)
 def test_detached_source_node(self):
  for key,value in [('net','wrong'),('pad_xyz_mm',[0,0,0])]:
   g=copy.deepcopy(self.graph);g['nodes']['U7104:1'][key]=value;e=copy.deepcopy(self.elec)
   e['interface_object_sha256']=s.hashlib.sha256((json.dumps(g,sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
   with self.assertRaisesRegex(ValueError,'node detached'):s.transport(self.inv,g,e,self.placed)
 def test_wire_metric_and_contacts(self):
  for key in ('harness_wire_cut_max_mm','GH_mated_contacts'):
   e=copy.deepcopy(self.elec);e['signal_net_paths'][0][key]+=1
   with self.assertRaisesRegex(ValueError,'wire metric|contact count'):s.transport(self.inv,self.graph,e,self.placed)
if __name__=='__main__':unittest.main()
