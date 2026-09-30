#!/usr/bin/env python3
"""Assert pinned-oracle results for the fixed panel-control pitch fixtures."""
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from gen_courtyards import courtyard_box, parse, node_name

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.circuit-cache/topic12-fixtures'
F=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'

def box(name):
 return courtyard_box((F/f'{name}.kicad_mod').read_text())

def violations(name):
 p=OUT/f'{name}-drc.json'
 if not p.exists():raise RuntimeError(f'{p} missing; run build_panel_controls_fixture.py and oracle DRC first')
 j=json.loads(p.read_text())
 if j['kicad_version']!='10.0.6':raise AssertionError(f"oracle mismatch: {j['kicad_version']}")
 return Counter(x['type'] for x in j['violations'])

def pads(name):
 tree=parse((F/f'{name}.kicad_mod').read_text())
 result={}
 for item in tree[1:]:
  if isinstance(item,list) and node_name(item)=='pad':
   at=next(child for child in item if isinstance(child,list) and node_name(child)=='at')
   result[item[1]]=(float(at[1]),float(at[2]))
 return result

pot_pads=pads('PTV09A-4020F')
assert pot_pads['1']==(-2.5,7.0) and pot_pads['2']==(0.0,7.0) and pot_pads['3']==(2.5,7.0)
assert pot_pads['4']==(-5.3,0.0) and pot_pads['5']==(5.3,0.0)
selector_pads=pads('SRBV160803')
assert [selector_pads[str(i)] for i in [5,4,3,2,1]]==[(-5.0+2.5*x,9.15) for x in range(5)]
assert [selector_pads[str(i)] for i in [6,7,8,9,10]]==[(-5.0+2.5*x,-9.15) for x in range(5)]
assert selector_pads['MP1']==(-8.0,-1.1) and selector_pads['MP2']==(8.0,-1.1)

pot=box('PTV09A-4020F');pw=pot[2]-pot[0];ph=pot[3]-pot[1]
assert pw < 17 and ph < 14
assert not violations('pot'),violations('pot')
selector=box('SRBV160803');sw=selector[2]-selector[0]
assert sw>17
v=violations('selector')
assert v['hole_to_hole']>=4,v
assert v['courtyards_overlap']>=4,v
print(f'pot 17 x 14 mm pitch: courtyard clearance X={17-pw:.2f} mm Y={14-ph:.2f} mm; KiCad DRC 0 violations')
print(f'selector 17 mm pitch: drawing Ø2 hole centers 1 mm apart (1 mm bore overlap; solid-leg dimensions not established); courtyard overlap={sw-17:.2f} mm; KiCad DRC {sum(v.values())} violations ({dict(v)})')
print('PASS: fixture detects the unresolved selector interference; original coplanar fixture remains rejected; selected stepped candidate is checked by fixtures/check_selector_assembly.sh')
