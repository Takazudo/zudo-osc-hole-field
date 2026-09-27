#!/usr/bin/env python3
"""Draft exact-identity passive/trim symbols for issue 15."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'symbols/src'
parts={p['id']:p for p in json.loads((ROOT/'design/standard/parts-shortlist.json').read_text())['parts']}
foot={
 'trim_102':'Potentiometer_Bourns_TC33X_Vertical',
 'trim_103':'Potentiometer_Bourns_TC33X_Vertical',
 'r_general':'R0603','r_precision':'R0603','r_ladder':'R_0805_2012Metric','r_power':'R_1210_3225Metric',
 'c_bypass':'C0603','c_bulk':'C0805','c_small':'C0603','c_hold':'C0805','c_slew':'C1206',
}
refs={'trim':'RV','r_':'R','c_':'C'}
def pin(n,name,x,y,rot):return f'   (pin passive line (at {x} {y} {rot}) (length 2.54) (name "{name}" (effects (font (size 1.27 1.27)))) (number "{n}" (effects (font (size 1.27 1.27)))))\n'
for id,fn in foot.items():
 p=parts[id];name=p['mpn'];ref='RV' if id.startswith('trim') else ('R' if id.startswith('r_') else 'C')
 ds='https://www.bourns.com/docs/product-datasheets/tc33.pdf' if id.startswith('trim') else ''
 s='(kicad_symbol_lib\n (version 20231120)\n (generator "kicad_symbol_editor")\n (generator_version "8.0")\n'
 s+=f' (symbol {json.dumps(name)}\n  (in_bom yes) (on_board yes)\n  (property "Reference" "{ref}" (at 0 5.08 0) (effects (font (size 1.27 1.27))))\n  (property "Value" {json.dumps(name)} (at 0 -5.08 0) (effects (font (size 1.27 1.27))))\n'
 for key,value in [('Footprint','zudo-osc-hole-field:'+fn),('Datasheet',ds),('MPN',name),('Manufacturer',p['manufacturer']),('LCSC',p.get('lcsc',''))]:
  s+=f'  (property {json.dumps(key)} {json.dumps(value)} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
 s+=f'  (symbol {json.dumps(name+"_0_1")}\n   (rectangle (start -2.54 3.81) (end 2.54 -3.81) (stroke (width 0.254) (type default)) (fill (type background)))\n'
 if id.startswith('trim'):
  s+=pin(1,'CCW',-5.08,2.54,0)+pin(2,'Wiper',-5.08,0,0)+pin(3,'CW',-5.08,-2.54,0)
 else:s+=pin(1,'',-5.08,0,0)+pin(2,'',5.08,0,180)
 s+='  )\n )\n)\n';(OUT/(name+'.kicad_sym')).write_text(s)
 print('symbol',id,name)
