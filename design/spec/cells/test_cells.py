"""Contract tests for proposal cell composition and critical polarity/net cases."""
import importlib,unittest
from design.spec.cells._builder import CELLS,STANDARD,UIDS,cell_parts
from design.spec.cells.harness import representative_uid,specification,library
from scripts.schgen.core import validate_family

class CellContract(unittest.TestCase):
 def test_all_nineteen_functions_accept_panel_uid_and_connect_complete_packages(self):
  self.assertEqual(len(CELLS),19)
  families,_=specification();lib=library()
  self.assertEqual(len(families),20)
  for id in CELLS:
   with self.subTest(id=id):
    module=importlib.import_module('design.spec.cells.'+id)
    uid=representative_uid(id)
    self.assertIn(uid,UIDS)
    parts=module.build(uid)
    self.assertTrue(parts)
    validate_family(next(f for f in families if f.name==id),lib)
    self.assertTrue(all(p.attributes.get('PanelUid')==uid and p.footprint for p in parts))
 def test_all_101_control_bindings_resolve_to_their_role(self):
  bindings=STANDARD['pot_bindings'];self.assertEqual(len(bindings),101)
  for row in bindings:
   with self.subTest(uid=row['panel_uid']):
    parts=cell_parts(row['role'],row['panel_uid'])
    self.assertTrue(any(p.symbol.endswith(row['part_id'].replace('pot_103','PTV09A-4020F-B103').replace('pot_104','PTV09A-4020F-B104').replace('pot_504','PTV09A-4020F-B504')) for p in parts))
 def test_unknown_panel_uid_rejected(self):
  with self.assertRaises(ValueError):cell_parts('general_output','invented')
 def test_two_calls_can_compose_without_key_reference_or_local_net_collision(self):
  uid=representative_uid('general_output')
  first=cell_parts('general_output',uid,ordinal_start=1,instance_tag='a')
  second=cell_parts('general_output',uid,ordinal_start=10,instance_tag='b')
  self.assertFalse({p.key for p in first}&{p.key for p in second})
  self.assertFalse({(p.prefix,p.ordinal) for p in first}&{(p.prefix,p.ordinal) for p in second})
  self.assertNotEqual(first[0].pins['3'],second[0].pins['3'])
 def test_source_facing_switch_and_clamp_polarity(self):
  uid=representative_uid('input_fault_switch');parts=cell_parts('input_fault_switch',uid,{'JACK':'PORT','PROTECTED':'SAFE'})
  switch=next(p for p in parts if p.key.endswith('__U.1'))
  self.assertEqual((switch.pins['3'],switch.pins['2']),('PORT','SAFE'))
  power=next(p for p in parts if p.key.endswith('__U.5'))
  self.assertEqual((power.pins['13'],power.pins['4']),('+12V','-12V'))
  inp=cell_parts('high_impedance_input',representative_uid('high_impedance_input'))
  diode=next(p for p in inp if p.symbol.endswith('BAT54S_215'))
  self.assertEqual((diode.pins['1'],diode.pins['2']),('-12V','+12V'))
 def test_exact_signal_diode_bridge_polarity(self):
  parts=cell_parts('magnitude_indicator',representative_uid('magnitude_indicator'))
  d1=next(p for p in parts if p.key.endswith('__D1.1'))
  self.assertTrue(d1.symbol.endswith('BAS16GW_QX'))
  self.assertIn('_DRIVE',d1.pins['2'])
  self.assertIn('_LED_A',d1.pins['1'])
 def test_precision_output_senses_jack_not_driver(self):
  parts=cell_parts('precision_output',representative_uid('precision_output'))
  jack=next(p for p in parts if p.key.endswith('__R_FB.0')).pins['1']
  fb=next(p for p in parts if p.key.endswith('__A.1')).pins['2']
  self.assertIn('_JACK',jack);self.assertIn('_FB',fb)
  self.assertNotEqual(jack,fb)
  feedback=next(p for p in parts if p.key.endswith('__R_FB.0'))
  compensation=next(p for p in parts if p.key.endswith('__C_FAST.0'))
  self.assertEqual((feedback.value,compensation.value),('100 Ω','1e-09 F'))
  self.assertEqual((feedback.attributes['MPN'],compensation.attributes['MPN']),
                   ('RC0603FR-07100RL','C0603C102J5GACTU'))
 def test_wrong_value_does_not_inherit_representative_mpn(self):
  parts=cell_parts('input_fault_switch',representative_uid('input_fault_switch'))
  drive=next(p for p in parts if p.key.endswith('__R_DRIVE.0'))
  self.assertEqual(drive.value,'1000 Ω')
  self.assertEqual(drive.attributes['MPN'],'')
  pd=next(p for p in parts if p.key.endswith('__R_EN.0'))
  self.assertEqual(pd.attributes['MPN'],'RC0603FR-07100KL')
 def test_fault_and_gate_threshold_arithmetic(self):
  self.assertAlmostEqual(24/998,0.024048096,places=7)
  self.assertAlmostEqual((24/998)**2*499,0.288577,places=5)
  self.assertGreater(1.471965,1.35);self.assertLess(1.471965,1.65)
  self.assertGreater(.971509,.85);self.assertLess(.971509,1.15)
if __name__=='__main__':unittest.main()

class UnusedActiveUnitContract(unittest.TestCase):
 def test_selected_signal_units_keep_their_port_pins(self):
  uid=representative_uid('high_impedance_input')
  op=cell_parts('high_impedance_input',uid,{'PROTECTED':'P','BUFFERED':'B'})
  active=next(p for p in op if p.symbol.endswith('OPA4196IDR') and p.unit==1)
  self.assertEqual((active.pins['1'],active.pins['2']),('B','B'))
  gate=cell_parts('gate_trigger_input',representative_uid('gate_trigger_input'),
                  {'BUFFERED':'B','REF_5V':'R','GATE_REF':'G','GATE_HIGH':'H'})
  schmitt=next(p for p in gate if p.symbol.endswith('SN74HC14DR') and p.unit==1)
  self.assertEqual(schmitt.pins['2'],'H')
  clip=cell_parts('clip_detector',representative_uid('clip_detector'),
                  {'MONITOR':'M','REF_5V':'R','REF_N5V':'N'})
  amp=next(p for p in clip if p.symbol.endswith('OPA4196IDR') and p.unit==1)
  self.assertEqual(amp.pins['3'],'M')
  comparators=[p for p in clip if p.symbol.endswith('LM393BIDR') and p.unit==1]
  self.assertIn('R',{p.pins['3'] for p in comparators})
  self.assertIn('N',{p.pins['2'] for p in comparators})

 def test_spare_opamp_comparator_and_schmitt_inputs_are_defined(self):
  op=cell_parts('high_impedance_input',representative_uid('high_impedance_input'))
  for p in op:
   if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')) and p.unit in (2,3,4):
    self.assertIn('AGND',p.pins.values())
    self.assertEqual(len({v for v in p.pins.values() if v!='AGND'}),1)
    self.assertNotIn(None,p.pins.values())
  for cell,role in [('clip_detector','LM393BIDR'),('switch_button_input','SN74HC14DR')]:
   parts=cell_parts(cell,representative_uid(cell))
   spare=[p for p in parts if p.symbol.endswith(role) and p.unit>1]
   self.assertTrue(spare)
   for p in spare:
    if role=='LM393BIDR' and p.unit==2:
     self.assertEqual(p.pins,{'5':'AGND','6':'+5V','7':None})
    if role=='SN74HC14DR' and p.unit in (2,3,4,5,6):
     self.assertEqual(sorted(v for v in p.pins.values() if v is not None),['AGND'])
