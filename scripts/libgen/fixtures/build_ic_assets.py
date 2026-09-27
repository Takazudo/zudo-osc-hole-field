#!/usr/bin/env python3
"""Normalize retained KiCad 10 stock expressions into issue 15 project assets."""
from pathlib import Path
import re,json,sys
sys.path.insert(0,str(Path('scripts/kicad').resolve()))
from extract_stock import balanced_form
ROOT=Path(__file__).resolve().parents[3]
SRC=ROOT/'circuit/sources/ic-library/cad'
SYMS=ROOT/'symbols/src'
FPS=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'
LIB='zudo-osc-hole-field'
DATA={
'OPA4196IDR':('OPA4196IDR','Texas Instruments','C2057385','SOIC-14_3.9x8.7mm_P1.27mm','https://www.ti.com/lit/ds/symlink/opa4196.pdf'),
'OPA4197IPWR':('OPA4197IPWR','Texas Instruments','C2057327','TSSOP-14_4.4x5mm_P0.65mm','https://www.ti.com/lit/ds/symlink/opa4197.pdf'),
'LM393BIDR':('LM393BIDR','Texas Instruments','','SOIC-8_3.9x4.9mm_P1.27mm','https://www.ti.com/lit/ds/symlink/lm393b.pdf'),
'SN74HC14DR':('SN74HC14DR','Texas Instruments','','SOIC-14_3.9x8.7mm_P1.27mm','https://www.ti.com/lit/ds/symlink/sn74hc14.pdf'),
'SN74HC74DR':('SN74HC74DR','Texas Instruments','','SOIC-14_3.9x8.7mm_P1.27mm','https://www.ti.com/lit/ds/symlink/sn74hc74.pdf'),
'SN74HC00DR':('SN74HC00DR','Texas Instruments','','SOIC-14_3.9x8.7mm_P1.27mm','https://www.ti.com/lit/ds/symlink/sn74hc00.pdf'),
'LM13700M_NOPB':('LM13700M/NOPB','Texas Instruments','C1346265','SOIC-16_3.9x9.9mm_P1.27mm','https://www.ti.com/lit/ds/symlink/lm13700.pdf'),
'LF398M_NOPB':('LF398M/NOPB','Texas Instruments','C1346172','SOIC-14_3.9x8.7mm_P1.27mm','https://www.ti.com/lit/ds/symlink/lf398-n.pdf'),
'AS3340D':('AS3340D','ALFA RPAR','','SOIC-16_3.9x9.9mm_P1.27mm',''),
'REF5050AIDR':('REF5050AIDR','Texas Instruments','C27804','SOIC-8_3.9x4.9mm_P1.27mm','https://www.ti.com/lit/ds/symlink/ref50.pdf'),
'TLV75533PDBVR':('TLV75533PDBVR','Texas Instruments','','SOT-23-5','https://www.ti.com/lit/ds/symlink/tlv755p.pdf'),
'BAT54S_215':('BAT54S,215','Nexperia','','SOT-23','https://assets.nexperia.com/documents/data-sheet/BAT54S.pdf'),
'MMBT3904_215':('MMBT3904,215','Nexperia','','SOT-23','https://assets.nexperia.com/documents/data-sheet/MMBT3904.pdf'),
'MMBT3906_215':('MMBT3906,215','Nexperia','','SOT-23','https://assets.nexperia.com/documents/data-sheet/MMBT3906.pdf'),
'2N7002_215':('2N7002,215','Nexperia','','SOT-23','https://assets.nexperia.com/documents/data-sheet/2N7002.pdf'),
}
def prop_set(s,key,val):
 q=json.dumps(val)
 pat=r'\(property\s+"'+re.escape(key)+r'"\s+"(?:\\.|[^"\\])*"'
 if re.search(pat,s):return re.sub(pat,'(property "'+key+'" '+q,s,count=1)
 pos=s.find('\n');return s[:pos+1]+'  (property "'+key+'" '+q+' (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))\n'+s[pos+1:]
def own_symbol(raw,target):
 original=re.match(r'\(symbol\s+"([^"]+)"',raw).group(1)
 parent=re.search(r'\(extends\s+"([^"]+)"\)',raw)
 if parent:
  key=next(k for k in DATA if k==target)
  base=(SRC/(key+'.parent.kicad_sympart')).read_text()
  units=[]
  for m in re.finditer(r'\(symbol\s+"'+re.escape(parent.group(1))+r'_[^"\n]+"',base):
   units.append(balanced_form(base,m.start()).replace('"'+parent.group(1)+'_','"'+target+'_',1))
  if not units:raise ValueError(f'{target} parent has no units')
  raw=re.sub(r'\(extends\s+"[^"]+"\)','',raw,count=1)
  raw=raw.rstrip();raw=raw[:-1]+'\n'+'\n'.join(units)+'\n)'
 else:
  raw=re.sub(r'\(symbol\s+"'+re.escape(original)+r'_', '(symbol "'+target+'_',raw)
 raw=raw.replace('(symbol "'+original+'"','(symbol "'+target+'"',1)
 return raw
for key,(mpn,mfg,lcsc,foot,ds) in DATA.items():
 raw=(SRC/(key+'.stock.kicad_sympart')).read_text().strip()
 body=own_symbol(raw,key)
 if key=='LM393BIDR':body=body.replace('(name \"V-\"','(name \"GND\"')
 if key=='SN74HC00DR':
  for m in reversed(list(re.finditer(r'\(symbol\s+\"SN74HC00DR_\d+_2\"',body))):
   block=balanced_form(body,m.start());body=body[:m.start()]+body[m.start()+len(block):]
 for field,value in [('Reference','U' if foot.startswith(('SOIC','TSSOP','SOT')) else 'D'),('Value',key),('Footprint',LIB+':'+foot),('Datasheet',ds),('MPN',mpn),('Manufacturer',mfg),('LCSC',lcsc)]:body=prop_set(body,field,value)
 wrapper='(kicad_symbol_lib\n  (version 20231120)\n  (generator "kicad_symbol_editor")\n  (generator_version "8.0")\n'+body+'\n)\n'
 wrapper='\n'.join(line.rstrip() for line in wrapper.splitlines() if line.strip())+'\n'
 (SYMS/(key+'.kicad_sym')).write_text(wrapper)
 print('symbol',key)
for source in SRC.glob('*.stock.kicad_mod'):
 key=source.name.removesuffix('.stock.kicad_mod')
 raw=source.read_text().strip()
 raw=re.sub(r'\((?:footprint|module)\s+"[^"]+"','(footprint "'+key+'"',raw,count=1)
 for m in reversed(list(re.finditer(r'\(model\s+',raw))):
  body=balanced_form(raw,m.start());raw=raw[:m.start()]+raw[m.start()+len(body):]
 raw='\n'.join(line.rstrip() for line in raw.splitlines())
 (FPS/(key+'.kicad_mod')).write_text(raw+'\n')
 print('footprint',key)
