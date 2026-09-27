#!/usr/bin/env python3
"""Generate source schematics/netlists for deterministic placer oracle fixtures."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.schgen.core import Family,Instance,Part,LibrarySymbol,render
from design.spec.cells._builder import load_symbol
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware

CASE={'one':1,'six':6,'island':1,'overflow':1}

def build(case):
 if case not in CASE:raise ValueError(case)
 board_id='fixture-place-'+case
 definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
 hardware=selected_hardware(definition,load_lock(ROOT/'design/grid/placements.lock.json'))
 refs={f'S{i+1}':hardware[i]['ref'] for i in range(CASE[case])}
 lib={}
 for name in ('WQP518MA','OPA4196IDR','RC0603FR-07100KL','GRM188R71H104KA93D'):
  sym=load_symbol(name);lib[sym.lib_id]=sym
 flag='Fixture:PWR_FLAG'
 lib[flag]=LibrarySymbol.from_fixture(flag,ROOT/'scripts/schgen/fixtures/PWR_FLAG.kicad_sympart')
 def part(key,symbol,prefix,ordinal,unit,pins,x,y,role,extra=None,refs=None):
  sym=lib[symbol]
  import re
  fp=re.search(r'\(property "Footprint" "([^\"]+)"',sym.body)[1]
  attrs={'Role':role,**(extra or {})}
  return Part(key,symbol,prefix,ordinal,unit,x,y,pins,footprint=fp,attributes=attrs,panel_refs=refs or {})
 jack='zudo-osc-hole-field:WQP518MA';amp='zudo-osc-hole-field:OPA4196IDR';res='zudo-osc-hole-field:RC0603FR-07100KL';cap='zudo-osc-hole-field:GRM188R71H104KA93D'
 parts=[part('J1',jack,'J',1,0,{'T':'SOURCE','S':'GND','TN':None},50.8,50.8,'panel',refs=refs)]
 for unit,pins in [(1,{'1':'OUT','2':'FB','3':'SENSE'}),(2,{'5':None,'6':None,'7':None}),(3,{'8':None,'9':None,'10':None}),(4,{'12':None,'13':None,'14':None}),(5,{'4':'+12V','11':'-12V'})]:
  parts.append(part(f'U1.{unit}',amp,'U',2,unit,pins,101.6+(unit-1)*30.48,50.8,'amp'))
 parts += [part('R_IN',res,'R',3,0,{'1':'SOURCE','2':'SENSE'},50.8,88.9,'input'),part('R_FB',res,'R',4,0,{'1':'OUT','2':'FB'},101.6,88.9,'feedback'),part('R_GND',res,'R',5,0,{'1':'FB','2':'GND'},152.4,88.9,'bias'),part('C_DEC',cap,'C',6,0,{'1':'+12V','2':'GND'},203.2,88.9,'decouple',{'DecouplingOf':'amp'})]
 if case=='island':
  parts.append(part('R_ISLAND',res,'R',7,0,{'1':'SOURCE','2':'GND'},254,88.9,'jack_island',{'Island':hardware[0]['uid']}))
 families=(Family('cluster',tuple(parts),global_nets=('+12V','-12V','GND')),
           Family('power',tuple(Part(f'P{i}',flag,'#FLG',i,0,50.8+i*25.4,50.8,{'1':net},value='TEST_SUPPLY') for i,net in enumerate(('+12V','-12V','GND'),1)),global_nets=('+12V','-12V','GND')))
 instances=tuple(Instance('cluster',f'S{i+1}',i+1) for i in range(CASE[case]))+(Instance('power','POWER',CASE[case]+1),)
 result=render(families,instances,lib,board_id)
 out=ROOT/'.circuit-cache/placer'/case;out.mkdir(parents=True,exist_ok=True)
 for name,body in result.items():
  target=out/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body)
 (out/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr "")) (lib (name "Fixture") (type "KiCad") (uri "${KIPRJMOD}/../../../scripts/schgen/fixtures/fixture.kicad_sym") (options "") (descr "")))\n')
 (out/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr "")))\n')
 (out/(board_id+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':board_id+'.kicad_pro','version':1},'sheets':[],'text_variables':{}},indent=2)+'\n')
 print(f'{case}: {CASE[case]} cluster instances; {len(parts)} source parts per instance')
if __name__=='__main__':
 for case in (sys.argv[1:] or CASE):build(case)
