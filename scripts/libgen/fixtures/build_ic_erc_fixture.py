#!/usr/bin/env python3
"""Create a throwaway schematic that places every electrical unit in issue 15."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.libgen.build_symbol_lib import symbol_spans
from scripts.schgen.core import parse,tokens,children,Pin,LibrarySymbol,Part,Family,Instance,render
def shortlist_symbols():
 """Resolve every current exact MPN; missing or ambiguous CAD must fail."""
 parts=json.loads((ROOT/'design/standard/parts-shortlist.json').read_text())['parts']
 by_mpn={}
 for path in sorted((ROOT/'symbols/src').glob('*.kicad_sym')):
  tree,_=parse(tokens(path.read_text()))
  for symbol in children(tree,'symbol'):
   props={p[1]:p[2] for p in children(symbol,'property')}
   if 'MPN' in props:
    by_mpn.setdefault(props['MPN'],[]).append((symbol[1],props.get('Reference')))
 selected=[]
 for part in parts:
  matches=by_mpn.get(part['mpn'],[])
  if len(matches)!=1:
   raise ValueError(f"{part['id']}: expected one symbol for {part['mpn']}, found {matches}")
  name,prefix=matches[0]
  if not prefix or not re.fullmatch('[A-Za-z]+',prefix):
   raise ValueError(f'{name}: missing/invalid reference prefix {prefix!r}')
  selected.append((name,prefix))
 return selected
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
 selected=shortlist_symbols()
 for ordinal,(name,prefix) in enumerate(selected,1):
  symbol=library_symbol(name);lib[symbol.lib_id]=symbol
  for unit in sorted(symbol.units):
   x=35.56+(placed%9)*38.10;y=35.56+(placed//9)*33.02;placed+=1
   parts.append(Part(f'{name}.{unit}',symbol.lib_id,prefix,ordinal,unit,x,y,{p.number:None for p in symbol.units[unit]},value=name))
 files=render((Family('ic-units',tuple(parts)),),(Instance('ic-units','ICPROBE',1),),lib,'ic-library-probe')
 for name,body in files.items():
  dest=out/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(body)
 (out/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr "")))\n')
 (out/'ic-library-probe.kicad_pro').write_text(json.dumps({'meta':{'filename':'ic-library-probe.kicad_pro','version':1},'sheets':[],'text_variables':{}},indent=2)+'\n')
 print(f'Built issue-15 ERC fixture: {len(selected)} current shortlist symbols, {placed} electrical units, {sum(len(p.pins) for p in parts)} placed pins')
if __name__=='__main__':main()
