"""Regenerate a bounded per-cell current worksheet from OSC-ES-1 planning loads."""
from pathlib import Path
import json
from ._builder import ROOT,STANDARD,CELLS
RAILS=('+12V','-12V','+5V')
SOURCE='design/standard/rail-budget-preliminary.json'
BUDGET=json.loads((ROOT/SOURCE).read_text())
LOADS={r['id']:r for r in BUDGET['loads']}
OUT=ROOT/'design/reports/current/cells.json'

def build():
 rows=[]
 for cell in CELLS.values():
  subtotal={r:0.0 for r in RAILS};basis=[];unquantified=[]
  for part in cell['parts']:
   role=part.get('opamp_role');id=part.get('part_id')
   load_id='opamp_precision' if role=='precision' else 'opamp_indicator' if role=='indicator' else 'opamp_audio' if role=='audio' else 'opamp_cv' if role=='cv' else 'fault_switches' if id=='fault_switch' else 'comparators' if id=='comparator' else None
   if load_id:
    load=LOADS[load_id];numbers=dict(load['planning_unit_mA'])
    if id=='comparator' and cell['id']=='gate_trigger_input':numbers['-12V']=0
    for rail in RAILS:subtotal[rail]+=numbers[rail]
    basis.append({'ref':part['ref'],'load_id':load_id,'planning_mA':numbers,'scope':'whole package allocation for isolated cell; shared packages must be reallocated in module budget'})
  dynamic={'dc_control_source':'dc_pots','magnitude_indicator':'magnitude_leds','clip_detector':'clip_leds','stage_indicator':'stage_leds','general_output':'output_loads','precision_output':'output_loads'}
  if cell['id'] in dynamic:
   load=LOADS[dynamic[cell['id']]];numbers=load['planning_unit_mA']
   for rail in RAILS:subtotal[rail]+=numbers[rail]
   basis.append({'ref':'cell dynamic load','load_id':load['id'],'planning_mA':numbers,'scope':load['basis']})
  for part in cell['parts']:
   if part.get('part_id') in ('reference','schmitt','led_white','led_red','npn','mosfet','signal_diode','clamp_diode'):
    unquantified.append(part['ref']+': '+part['part_id'])
  if cell['id']=='decoupling_bulk':unquantified.append('RAIL binding and per-board/whole-instrument bleeder allocation')
  if cell['id']=='input_fault_switch':unquantified.append('1 kohm enable-feed +5 V current and switching/fault currents')
  if cell['id']=='reference_generator':unquantified.append('REF5050 supply current, reference load and output drive')
  rows.append({'id':cell['id'],'status':'PLANNING PARTIAL - NOT A CELL MAXIMUM','known_planning_mA':{r:round(subtotal[r],6) for r in RAILS},'basis':basis,'unquantified':unquantified,'qualification':'Sum only after exact package sharing, loads, duty cycles, source facts and netlist are resolved; no passing instrument budget is claimed.'})
 return {'schema_version':1,'standard_id':'OSC-ES-1','authority':STANDARD['authority'],'status':'Unvalidated partial planning worksheet; not a maximum or a board budget','source':SOURCE,'rail_ceiling_warning':'-12 V preliminary estimate is 712.655 mA versus 640 mA ceiling; #34 reduction required.','cells':rows}

def main(check=False):
 body=json.dumps(build(),indent=2,ensure_ascii=False)+'\n'
 if check:
  if not OUT.is_file() or OUT.read_text()!=body:raise SystemExit('cell current worksheet drift')
 else:
  OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(body)
 print(f'{"Checked" if check else "Generated"} 19 partial planning current figures')
if __name__=='__main__':
 import sys
 main('--check' in sys.argv)
