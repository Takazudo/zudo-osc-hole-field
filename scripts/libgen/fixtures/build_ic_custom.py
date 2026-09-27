#!/usr/bin/env python3
"""Source-backed custom multi-unit symbols for issue 15."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'symbols/src'
LIB='zudo-osc-hole-field'
header='(kicad_symbol_lib\n  (version 20231120)\n  (generator "kicad_symbol_editor")\n  (generator_version "8.0")\n'
def prop(k,v):return f'  (property {json.dumps(k)} {json.dumps(v)} (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'
def pin(n,nm,x,y,rot,kind='passive'):return f'    (pin {kind} line (at {x} {y} {rot}) (length 2.54) (name {json.dumps(nm)} (effects (font (size 1.27 1.27)))) (number {json.dumps(str(n))} (effects (font (size 1.27 1.27)))))\n'
def unit(name,index,pins):
 s=f'  (symbol "{name}_{index}_1"\n    (rectangle (start -3.81 5.08) (end 3.81 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))\n'
 left=[p for p in pins if p[2]=='L'];right=[p for p in pins if p[2]=='R']
 for side,ps in [('L',left),('R',right)]:
  for j,(num,label,_) in enumerate(ps):
   y=3.81-j*2.54
   kind='passive' if label in ('VDD','VSS','GND','VCC','+5V','0V') else ('output' if label in ('FF','WHITE OUT','PINK OUT','1Q','1Qbar','2Q','2Qbar') else ('input' if label.startswith('IN') or label.endswith(('A','B','R')) else 'passive'))
   s+=pin(num,label,-6.35 if side=='L' else 6.35,y,0 if side=='L' else 180,kind)
 return s+'  )\n'
def symbol(name,mpn,mfg,lcsc,foot,ds,units):
 s=header+f' (symbol "{name}"\n  (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
 s+=f'  (property "Reference" "U" (at 0 7.62 0) (effects (font (size 1.27 1.27))))\n  (property "Value" "{name}" (at 0 -7.62 0) (effects (font (size 1.27 1.27))))\n'
 for k,v in [('Footprint',LIB+':'+foot),('Datasheet',ds),('MPN',mpn),('Manufacturer',mfg),('LCSC',lcsc)]:s+=prop(k,v)
 for i,p in enumerate(units,1):s+=unit(name,i,p)
 s+=' )\n)\n';(OUT/(name+'.kicad_sym')).write_text(s)
symbol('ADG5412FBRUZ','ADG5412FBRUZ','Analog Devices','C579073','TSSOP-16_4.4x5mm_P0.65mm','https://www.analog.com/media/en/technical-documentation/data-sheets/adg5412f_5413f.pdf',[
 [('3','S1','L'),('1','IN1','L'),('2','D1','R')],
 [('14','S2','L'),('16','IN2','L'),('15','D2','R')],
 [('11','S3','L'),('9','IN3','L'),('10','D3','R')],
 [('6','S4','L'),('8','IN4','L'),('7','D4','R')],
 [('13','VDD','L'),('4','VSS','L'),('5','GND','R'),('12','FF','R')]
])
symbol('CD74HC221M96','CD74HC221M96','Texas Instruments','C133954','SOIC-16_3.9x9.9mm_P1.27mm','https://www.ti.com/lit/ds/symlink/cd74hc221.pdf',[
 [('1','1A','L'),('2','1B','L'),('3','1R','L'),('14','1CX','L'),('15','1RXCX','L'),('4','1Q','R'),('13','1Qbar','R')],
 [('9','2A','L'),('10','2B','L'),('11','2R','L'),('6','2CX','L'),('7','2RXCX','L'),('12','2Q','R'),('5','2Qbar','R')],
 [('16','VCC','L'),('8','GND','R')]
])
symbol('NOISE2','NOISE2','Electric Druid','','DIP-8_W7.62mm','https://electricdruid.net/datasheets/NOISE2Datasheet.pdf',[
 [('1','+5V','L'),('2','Unused','L'),('4','Unused','L'),('5','Unused','L'),('6','Unused','L'),('8','0V','R'),('3','WHITE OUT','R'),('7','PINK OUT','R')]
])
symbol('BCM847BS_115','BCM847BS,115','Nexperia','','SOT-363_SC-70-6','https://assets.nexperia.com/documents/data-sheet/BCM847BS.pdf',[
 [('2','B1','L'),('6','C1','R'),('1','E1','R')],
 [('5','B2','L'),('3','C2','R'),('4','E2','R')]
])
