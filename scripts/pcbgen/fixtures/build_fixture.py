#!/usr/bin/env python3
"""Generate the ten-jack schematic fixture; KiCad exports its netlist."""
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.schgen.core import LibrarySymbol,Family,Instance,Part,render
from scripts.libgen.build_symbol_lib import symbol_spans
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware

D=load_definition(ROOT/'design/boards/fixture-jacks.json')
lock=load_lock(ROOT/'design/grid/placements.lock.json')
items=selected_hardware(D,lock)
source=(ROOT/'symbols/src/WQP518MA.kicad_sym').read_text()
span=symbol_spans(source)[0]
out=ROOT/'boards/fixture-jacks';out.mkdir(parents=True,exist_ok=True)
fragment=out/'WQP518MA.kicad_sympart';fragment.write_text(source[span[0]:span[1]].replace('WQP518MA_0_1','WQP518MA_1_1')+'\n')
lib_id='zudo-osc-hole-field:WQP518MA'
library={lib_id:LibrarySymbol.from_fixture(lib_id,fragment)}
parts=[]
for n,p in enumerate(items):
 parts.append(Part(f'J{n+1}',lib_id,'J',n+1,1,40+(n%5)*30,55+(n//5)*30,
                   {'T':f'SIGNAL_{n+1}','S':'GND','TN':None},value='WQP518MA',
                   footprint='zudo-osc-hole-field:Jack_3.5mm_QingPu_WQP518MA',
                   panel_ref=p['ref'],attributes={'PanelUid':p['uid']}))
result=render((Family('jacks',tuple(parts),global_nets=('GND',)),),(Instance('jacks','JACKS',1),),library,'fixture-jacks')
for path,body in result.items():
 target=out/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body)
(out/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr "")))\n')
(out/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr "")))\n')
print(f'fixture schematic: {len(items)} lockfile jacks')
