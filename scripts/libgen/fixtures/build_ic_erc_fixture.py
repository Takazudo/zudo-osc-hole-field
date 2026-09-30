#!/usr/bin/env python3
"""Create a throwaway schematic that places every electrical unit in issue 15."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.libgen.build_symbol_lib import symbol_spans
from scripts.schgen.core import parse,tokens,children,Pin,LibrarySymbol,Part,Family,Instance,render
NAMES=[
 'OPA4196IDR','OPA4197IPWR','ADG5412FBRUZ','LM393BIDR','SN74HC14DR','SN74HC74DR','SN74HC00DR','CD74HC221M96','LM13700M_NOPB','LF398M_NOPB','AS3340D','NOISE2','REF5050AIDR','TLV75533PDBVR','BAT54S_215','MMBT3904_215','MMBT3906_215','2N7002_215','BCM847BS_115',
 'TC33X-2-102E','TC33X-2-103E','RC0603FR-07100KL','RT0603BRD07100KL','TNPW080510K0BEEA','RC1210FR-07499RL','GRM188R71H104KA93D','GRM21BR61E475KA12L','C0603C101J5GACTU','C0805C103J5GACTU','1206CG104J500NT'
]
def library_symbol(name):
 path=ROOT/'symbols/src'/(name+'.kicad_sym')
 raw=path.read_text();spans=symbol_spans(raw)
 if len(spans)!=1:raise ValueError(name)
 body=raw[spans[0][0]:spans[0][1]]
 tree,_=parse(tokens(body))
 units={}
 for u in children(tree,'symbol'):
  match=re.fullmatch(re.escape(name)+r'_(\d+)_(\d+)',u[1])
  if not match:continue
  number=int(match[1]);pins=[]
  for pin in children(u,'pin'):
   at=children(pin,'at')[0]
   pins.append(Pin(str(children(pin,'number')[0][1]),float(at[1]),float(at[2]),int(float(at[3])),str(pin[1])))
  if pins:
   existing={x.number:x for x in units.get(number,())}
   for p in pins:existing.setdefault(p.number,p)
   units[number]=tuple(existing.values())
 if not units:raise ValueError(f'{name} has no placed units')
 return LibrarySymbol('zudo-osc-hole-field:'+name,body.replace(f'(symbol "{name}"',f'(symbol "zudo-osc-hole-field:{name}"',1),units)
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: build_ic_erc_fixture.py <output-directory>')
 out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
 lib={};parts=[];placed=0
 for ordinal,name in enumerate(NAMES,1):
  symbol=library_symbol(name);lib[symbol.lib_id]=symbol
  prefix='RV' if name.startswith('TC33') else ('R' if name.startswith(('RC','RT','TNPW')) else ('C' if name.startswith(('GRM','C0603','C0805','1206CG')) else ('Q' if name.startswith(('MMBT','2N7002','BCM')) else ('D' if name.startswith('BAT54') else 'U'))))
  for unit in sorted(symbol.units):
   x=35.56+(placed%7)*38.10;y=35.56+(placed//7)*33.02;placed+=1
   parts.append(Part(f'{name}.{unit}',symbol.lib_id,prefix,ordinal,unit,x,y,{p.number:None for p in symbol.units[unit]},value=name))
 files=render((Family('ic-units',tuple(parts)),),(Instance('ic-units','ICPROBE',1),),lib,'ic-library-probe')
 for name,body in files.items():
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(body)
 (out/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr "")))\n')
 (out/'ic-library-probe.kicad_pro').write_text(json.dumps({'meta':{'filename':'ic-library-probe.kicad_pro','version':1},'sheets':[],'text_variables':{}},indent=2)+'\n')
 print(f'Built issue-15 ERC fixture: {len(NAMES)} new symbols, {placed} electrical units, {sum(len(p.pins) for p in parts)} placed pins')
if __name__=='__main__':main()
