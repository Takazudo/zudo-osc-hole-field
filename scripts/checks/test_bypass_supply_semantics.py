import ast,copy,json,sys,unittest,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.pcbgen import bypass_supply_pins as helper
from scripts.checks import partition35_floorplan as original
io=json.loads((ROOT/'design/reports/io-partition.json').read_text());parts={p['ref']:p for p in io['physical_packages']};pin_nets={p:{} for p in parts}
for u in io['package_units']:pin_nets[u['ref']].update(u['pins'])
ns=dict(original.__dict__);ns['source_bypass_binding']=helper.source_bypass_binding
for node in ast.parse((ROOT/'scripts/checks/partition35_floorplan.py').read_text()).body:
 if isinstance(node,ast.FunctionDef) and node.name in ('bypass_cells','check_bypasses'):exec(compile(ast.Module(body=[node],type_ignores=[]),'<staged actual functions>','exec'),ns)
class Fix(unittest.TestCase):
 def test_actual_vcc_not_same_net_logic(self):
  for cap,ic,wrong in [('C4247','U4230','2'),('C4249','U4232','4')]:
   self.assertEqual(next(n for n,v in pin_nets[ic].items() if v=='+5V'),wrong)
   self.assertEqual(helper.source_bypass_binding(ROOT,parts[ic],parts[cap],pin_nets),('1','+5V','14'))
 def test_actual_bypass_cells_correct_real_pad_distance(self):
  parent,cap=parts['U4232'],parts['C4249'];shapes={p['footprint']:original.footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm'] for p in (parent,cap)}
  cells=ns['bypass_cells'](parent,[cap],'F.Cu',shapes,pin_nets)
  for p,angle,(x,y) in cells:
   if p['ref']==cap['ref']:cap_point=original.pad_point(p['footprint'],'1','F.Cu',angle,x,y)
  target=original.pad_point(parent['footprint'],'14','F.Cu',0,0,0)
  import math
  self.assertLessEqual(math.dist(cap_point,target),3)
  # The selected rail is also present on logic pin4; proximity to it cannot establish supply locality.
  wrong_target=original.pad_point(parent['footprint'],'4','F.Cu',0,0,0)
  self.assertGreater(math.dist(cap_point,wrong_target),3)
 def test_selfcheck_uses_supply_pin_not_logic_pin(self):
  parent,cap=parts['U4232'],parts['C4249'];rows=[{'ref':'U4232','board':'K','x_mm':0,'y_mm':0,'rotation_deg':0,'side':'F.Cu'},{'ref':'C4249','board':'K','x_mm':0,'y_mm':0,'rotation_deg':0,'side':'F.Cu'}]
  save=ns['JACK_BOARDS'];ns['JACK_BOARDS']={'K'}
  try:records,errors=ns['check_bypasses']([parent,cap],rows,pin_nets)
  finally:ns['JACK_BOARDS']=save
  self.assertEqual(records[0]['IC_supply_pad'],'14')
 def test_filtered_rail_supported(self):self.assertEqual(helper.source_bypass_binding(ROOT,parts['U6101'],parts['C6110'],pin_nets)[1:],('/N1/NOISE_VDD','1'))
 def test_ambiguous_supply_rejected(self):
  nets=copy.deepcopy(pin_nets);nets['U4232']['7']='+5V'
  with self.assertRaisesRegex(ValueError,'ambiguous'):helper.source_bypass_binding(ROOT,parts['U4232'],parts['C4249'],nets)
 def test_signal_only_and_unknown_owner_rejected(self):
  nets=copy.deepcopy(pin_nets);nets['U4232']['14']='OTHER'
  with self.assertRaises(ValueError):helper.source_bypass_binding(ROOT,parts['U4232'],parts['C4249'],nets)
  wrong=copy.deepcopy(parts['C4249']);wrong['decouples_ref']='U4231'
  with self.assertRaises(ValueError):helper.source_bypass_binding(ROOT,parts['U4232'],wrong,pin_nets)
 def test_unknown_supply_semantics_rejected(self):
  parent=copy.deepcopy(parts['U4232']);parent['symbol']='RT0603BRD07100KL'
  with self.assertRaises(ValueError):helper.source_bypass_binding(ROOT,parent,parts['C4249'],pin_nets)
if __name__=='__main__':unittest.main()
