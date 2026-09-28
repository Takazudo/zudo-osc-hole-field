#!/usr/bin/env python3
"""Synthetic 3×10 jack/indicator routing stress slice; not a circuit design proposal."""
from __future__ import annotations
import json,re,sys
from dataclasses import replace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.schgen.core import Family,Instance,Part,LibrarySymbol,render
from design.spec.cells._builder import load_symbol
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware

SOURCE_COLUMN='--source-column' in sys.argv
ID='fixture-route-dense-source' if SOURCE_COLUMN else 'fixture-route-dense'
OUT=ROOT/'.circuit-cache/router'/('dense-source' if SOURCE_COLUMN else 'dense')
SYMS=('WQP518MA','OPA4196IDR','RC0603FR-07100KL','GRM188R71H104KA93D','0603Whitelight_C2290')

def build():
    definition=load_definition(ROOT/'design/boards'/f'{ID}.json')
    selected=selected_hardware(definition,load_lock(ROOT/'design/grid/placements.lock.json'))
    if len(selected)!=30:raise ValueError('dense slice needs 30 locked jacks')
    library={}
    for name in SYMS:
        sym=load_symbol(name);library[sym.lib_id]=sym
    conn='RouteFixture:Conn_02x20_Odd_Even'
    path=ROOT/'scripts/pcbgen/fixtures/Conn_02x20_Odd_Even.kicad_sympart'
    library[conn]=LibrarySymbol.from_fixture(conn,path)
    def part(key,symbol,prefix,ordinal,unit,pins,x,y,role,extra=None,ref=None):
        import re
        fp=re.search(r'\(property "Footprint" "([^"]*)"',library[symbol].body)[1]
        return Part(key,symbol,prefix,ordinal,unit,x,y,pins,footprint=fp,attributes={'Role':role,**(extra or {})},panel_refs=ref or {})
    jack='zudo-osc-hole-field:WQP518MA';amp='zudo-osc-hole-field:OPA4196IDR';res='zudo-osc-hole-field:RC0603FR-07100KL';cap='zudo-osc-hole-field:GRM188R71H104KA93D';led='zudo-osc-hole-field:0603Whitelight_C2290'
    families=[];instances=[];inputs=[]
    for i,hardware in enumerate(selected,1):
        cell=f'C{i}';input_net=f'INPUT_{i}';inputs.append(input_net)
        parts=[part('J1',jack,'J',1,0,{'T':input_net,'S':'GND','TN':None},50.8,50.8,'panel',ref={cell:hardware['ref']})]
        for unit,pins in [(1,{'1':'DRIVE','2':'FB','3':input_net}),(2,{'5':None,'6':None,'7':None}),(3,{'8':None,'9':None,'10':None}),(4,{'12':None,'13':None,'14':None}),(5,{'4':'+12V','11':'-12V'})]:
            parts.append(part(f'U1.{unit}',amp,'U',2,unit,pins,101.6+(unit-1)*30.48,50.8,'indicator_amp'))
        parts.extend([
            part('R_FB',res,'R',3,0,{'1':'DRIVE','2':'FB'},50.8,101.6,'feedback'),
            part('R_GND',res,'R',4,0,{'1':'FB','2':'GND'},101.6,101.6,'bias'),
            part('R_LED',res,'R',5,0,{'1':'DRIVE','2':'LED_A'},152.4,101.6,'led_series'),
            part('D_LED',led,'D',6,0,{'1':'LED_A','2':'GND'},203.2,101.6,'led'),
            part('C_DEC',cap,'C',7,0,{'1':'+12V','2':'GND'},254,101.6,'decouple',{'DecouplingOf':'indicator_amp'}),
        ])
        if SOURCE_COLUMN and i>10:
            parts=[replace(p,pins={number:None for number in p.pins}) for p in parts]
        families.append(Family(f'indicator{i:02d}',tuple(parts),global_nets=('+12V','-12V','GND',input_net)))
        instances.append(Instance(f'indicator{i:02d}',cell,i))
    connector_pins={str(n):(inputs[n-1] if n<=len(inputs) and (not SOURCE_COLUMN or n<=10) else None) for n in range(1,41)}
    connector=Part('J_EDGE',conn,'J',1,1,101.6,101.6,connector_pins,footprint='Connector_PinHeader_2.54mm:PinHeader_2x20_P2.54mm_Vertical',attributes={'Role':'edge_connector'})
    families.append(Family('edge',(connector,),global_nets=tuple(inputs)))
    instances.append(Instance('edge','EDGE',31))
    result=render(tuple(families),tuple(instances),library,ID)
    OUT.mkdir(parents=True,exist_ok=True)
    for name,body in result.items():
        target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body)
    (OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr "")) (lib (name "RouteFixture") (type "KiCad") (uri "${KIPRJMOD}/route-fixture.kicad_sym") (options "") (descr "")))\n')
    (OUT/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr "")) (lib (name "Connector_PinHeader_2.54mm") (type "KiCad") (uri "/usr/share/kicad/footprints/Connector_PinHeader_2.54mm.pretty") (options "") (descr "")))\n')
    (OUT/'route-fixture.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "zudo_fixture")\n'+path.read_text()+')\n')
    (OUT/(ID+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':ID+'.kicad_pro','version':1},'sheets':[],'text_variables':{}},indent=2)+'\n')
    print(f'dense slice: {len(selected)} jack/indicator cells, 1 × 40-pin edge connector')
if __name__=='__main__':build()
