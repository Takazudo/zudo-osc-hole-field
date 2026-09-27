"""Generated, isolated one-of-each-cell schematic for the OSC-ES-1 proposal."""
from __future__ import annotations
from pathlib import Path
import json
from scripts.schgen.core import Family,Instance,Part,LibrarySymbol,render
from ._builder import ROOT,STANDARD,CELLS,SHORTLIST,CATALOG,load_symbol,cell_parts

PROJECT='osc-standard-cells'
OUT=ROOT/'schematic/cells'

def representative_uid(cell_id):
 bindings=STANDARD['pot_bindings']
 row=next((r for r in bindings if r['role']==cell_id),None)
 if row:return row['panel_uid']
 placements=json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']
 led_kind={'magnitude_indicator':'mag','clip_detector':'clip','stage_indicator':'stage'}.get(cell_id)
 if led_kind:return next(p['uid'] for p in placements if p.get('kind')=='led' and p.get('led_type')==led_kind)
 if cell_id=='octave_reference':return next(p['uid'] for p in placements if p.get('kind')=='octave')
 if cell_id=='switch_button_input':return next(p['uid'] for p in placements if p.get('kind')=='button')
 kind='led' if cell_id in ('magnitude_indicator','clip_detector','stage_indicator') else 'jack' if 'input' in cell_id or 'output' in cell_id else 'pot'
 return next(p['uid'] for p in placements if p.get('kind')==kind)

def specification():
 families=[];instances=[]
 for i,id in enumerate(CELLS,1):
  parts=list(cell_parts(id,representative_uid(id)))
  # Test-only sources and loads represent the module ports left open by an
  # isolated cell. They do not become circuit parts in cell_parts().
  lib=library();by_net={}
  for part in parts:
   for pin in lib[part.symbol].units[part.unit]:
    net=part.pins[pin.number]
    if net is not None and net not in ('+12V','-12V','+5V','AGND'):
     by_net.setdefault(net,[]).append(pin.electrical)
  ordinal=len(CELLS[id]['parts'])
  for net,types in sorted(by_net.items()):
   if len(types)!=1:continue
   ordinal+=1;x=50.8+((len(parts))%7)*50.8;y=50.8+((len(parts))//7)*25.4
   if types[0] in ('input','power_in'):
    parts.append(Part(f'TEST_SOURCE_{ordinal}','Fixture:PWR_FLAG','#FLG',ordinal,0,x,y,{'1':net},value='PORT_SOURCE'))
   else:
    parts.append(Part(f'TEST_LOAD_{ordinal}','Fixture:Conn_01x02','J',ordinal,1,x,y,{'1':net,'2':None},value='PORT_LOAD'))
  parts=tuple(parts)
  families.append(Family(id,parts,global_nets=('+12V','-12V','+5V','AGND')))
  instances.append(Instance(id,id.upper(),i))
 flags=tuple(Part(f'RAIL_{i}','Fixture:PWR_FLAG','#FLG',i,0,50.8+i*25.4,50.8,{'1':net},value='HARNESS_SUPPLY') for i,net in enumerate(('+12V','-12V','+5V','AGND'),1))
 families.append(Family('test_power',flags,global_nets=('+12V','-12V','+5V','AGND')))
 instances.append(Instance('test_power','TEST_POWER',20))
 return tuple(families),tuple(instances)

def library():
 result={}
 for cell in CELLS.values():
  for part in cell['parts']:
   role=part.get('opamp_role');id=STANDARD['roles'][role]['part_id'] if role else part['part_id']
   name=CATALOG[SHORTLIST[id]['mpn']]
   symbol=load_symbol(name);result[symbol.lib_id]=symbol
 for name in ('PWR_FLAG','Conn_01x02'):
  lib_id='Fixture:'+name
  result[lib_id]=LibrarySymbol.from_fixture(lib_id,ROOT/'scripts/schgen/fixtures'/f'{name}.kicad_sympart')
 return result

def generate(check=False):
 families,instances=specification();files=render(families,instances,library(),PROJECT)
 files['sym-lib-table']='(sym_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr "")) (lib (name "Fixture") (type "KiCad") (uri "${KIPRJMOD}/../../scripts/schgen/fixtures/fixture.kicad_sym") (options "") (descr "Harness only")))\n'
 files['fp-lib-table']='(fp_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr "")))\n'
 files[f'{PROJECT}.kicad_pro']=json.dumps({'meta':{'filename':PROJECT+'.kicad_pro','version':1},'sheets':[],'text_variables':{}},indent=2)+'\n'
 drift=[]
 for name,body in files.items():
  path=OUT/name
  if not path.is_file() or path.read_text()!=body:drift.append(name)
  if not check:
   path.parent.mkdir(parents=True,exist_ok=True);path.write_text(body)
 if check and drift:raise SystemExit('Harness drift: '+', '.join(drift))
 print(f'{"Checked" if check else "Generated"} 19 proposal cells plus test supply, {sum(len(f.parts) for f in families)} symbol units')

if __name__=='__main__':
 import sys
 generate('--check' in sys.argv)
