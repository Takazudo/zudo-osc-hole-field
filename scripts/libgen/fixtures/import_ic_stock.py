#!/usr/bin/env python3
"""One-time extraction of KiCad 10 stock source expressions for issue 15."""
from pathlib import Path
import sys,re
sys.path.insert(0,str(Path('scripts/kicad').resolve()))
from extract_stock import extract_symbol,extract_footprint
out=Path('circuit/sources/ic-library/cad');out.mkdir(parents=True,exist_ok=True)
syms={
 'OPA4196IDR':('Amplifier_Operational','OPA4196xD'),
 'OPA4197IPWR':('Amplifier_Operational','OPA4197xPW'),
 'LM393BIDR':('Comparator','LM393'),
 'SN74HC14DR':('74xx','74HC14'),
 'SN74HC74DR':('74xx','74HC74'),
 'SN74HC00DR':('74xx','74HC00'),
 'LM13700M_NOPB':('Amplifier_Operational','LM13700'),
 'LF398M_NOPB':('Analog','LF398_SOIC14'),
 'AS3340D':('Audio','AS3340'),
 'REF5050AIDR':('Reference_Voltage','REF5050AD'),
 'TLV75533PDBVR':('Regulator_Linear','TLV75533PDBV'),
 'BAT54S_215':('Diode','BAT54S'),
 'MMBT3904_215':('Transistor_BJT','MMBT3904'),
 'MMBT3906_215':('Transistor_BJT','MMBT3906'),
 '2N7002_215':('Transistor_FET','2N7002'),
}
footprints={
 'SOIC-14_3.9x8.7mm_P1.27mm':('Package_SO','SOIC-14_3.9x8.7mm_P1.27mm'),
 'TSSOP-14_4.4x5mm_P0.65mm':('Package_SO','TSSOP-14_4.4x5mm_P0.65mm'),
 'SOIC-16_3.9x9.9mm_P1.27mm':('Package_SO','SOIC-16_3.9x9.9mm_P1.27mm'),
 'TSSOP-16_4.4x5mm_P0.65mm':('Package_SO','TSSOP-16_4.4x5mm_P0.65mm'),
 'SOIC-8_3.9x4.9mm_P1.27mm':('Package_SO','SOIC-8_3.9x4.9mm_P1.27mm'),
 'SOT-23-5':('Package_TO_SOT_SMD','SOT-23-5'),
 'SOT-23':('Package_TO_SOT_SMD','SOT-23'),
 'SOT-363_SC-70-6':('Package_TO_SOT_SMD','SOT-363_SC-70-6'),
 'SOD-123':('Diode_SMD','D_SOD-123'),
 'DIP-8_W7.62mm':('Package_DIP','DIP-8_W7.62mm'),
 'R_0805_2012Metric':('Resistor_SMD','R_0805_2012Metric'),
 'R_1210_3225Metric':('Resistor_SMD','R_1210_3225Metric'),
 'Potentiometer_Bourns_TC33X_Vertical':('Potentiometer_SMD','Potentiometer_Bourns_TC33X_Vertical'),
}
for key,(lib,name) in syms.items():
 s=extract_symbol(lib,name)
 if s is None:print('MISSING SYMBOL',key,lib,name);continue
 (out/(key+'.stock.kicad_sympart')).write_text(s+'\n')
 parent=re.search(r'\(extends \"([^\"]+)\"\)',s)
 if parent:
  p=extract_symbol(lib,parent.group(1))
  if p is None:print('MISSING PARENT',key,parent.group(1))
  else:(out/(key+'.parent.kicad_sympart')).write_text(p+'\n')
 print('SYMBOL',key,lib,name)
for key,(lib,name) in footprints.items():
 s=extract_footprint(lib,name)
 if s is None:print('MISSING FOOTPRINT',key,lib,name);continue
 (out/(key+'.stock.kicad_mod')).write_text(s+'\n')
 print('FOOTPRINT',key,lib,name)
