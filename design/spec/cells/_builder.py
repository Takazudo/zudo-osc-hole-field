"""Compile OSC-ES-1 proposal cell terminal tables into reusable schematic Parts.

Part values and functions come from the standard. A missing exact passive value has an
empty instance MPN and remains a sourcing gate; a series representative is never
promoted as that value's orderable identity.
"""
from __future__ import annotations
from pathlib import Path
import hashlib,json,re
from scripts.schgen.core import LibrarySymbol, Part, Pin, parse, tokens, children
from scripts.libgen.build_symbol_lib import symbol_spans

ROOT=Path(__file__).resolve().parents[3]
STANDARD=json.loads((ROOT/'design/standard/electrical-standard.json').read_text())
SHORTLIST={p['id']:p for p in json.loads((ROOT/'design/standard/parts-shortlist.json').read_text())['parts']}
CELLS={c['id']:c for c in STANDARD['cells']}
UIDS={p['uid'] for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
CATALOG={}
for path in (ROOT/'symbols/src').glob('*.kicad_sym'):
 text=path.read_text()
 match=re.search(r'\(property "MPN" "([^\"]*)"',text)
 if match:CATALOG[match.group(1)]=path.stem

PIN_ALIASES={
 'fault_switch':{'S':'3','D':'2','IN':'1','VDD':'13','VSS':'4','GND':'5'},
 'clamp_diode':{'A':'1','MID':'3','K':'2'},
 'reference':{'VIN':'2','GND':'4','OUT':'6','TRIM':'5','TEMP':'3'},
 'comparator':{'PLUS':'3','MINUS':'2','OUT':'1','VCC':'8','GND':'4'},
 'schmitt':{'IN':'1','OUT':'2','VCC':'14','GND':'7'},
 'signal_diode':{'A':'2','K':'1'},
 'led_white':{'A':'1','K':'2'},'led_red':{'A':'2','K':'1'},
 'npn':{'B':'1','E':'2','C':'3'},'mosfet':{'G':'1','S':'2','D':'3'},
 'pot_103':{'CCW':'1','WIPER':'2','CW':'3'},
 'pot_104':{'CCW':'1','WIPER':'2','CW':'3'},
 'pot_504':{'END1':'1','WIPER':'2','END2':'3'},
 'trim_102':{'END1':'1','WIPER':'2','END2':'3'},
 'trim_103':{'END1':'1','WIPER':'2','END2':'3'},
}
AMP={'IN+':'3','IN-':'2','OUT':'1','V+':'4','V-':'11'}
PREFIX={'r_general':'R','r_precision':'R','r_power':'R','r_ladder':'R','c_small':'C','c_bypass':'C','c_bulk':'C','c_slew':'C','signal_diode':'D','clamp_diode':'D','led_white':'D','led_red':'D','pot_103':'RV','pot_104':'RV','pot_504':'RV','trim_102':'RV','trim_103':'RV','npn':'Q','mosfet':'Q'}


def load_symbol(name):
 path=ROOT/'symbols/src'/f'{name}.kicad_sym';raw=path.read_text();spans=symbol_spans(raw)
 if len(spans)!=1:raise ValueError(name)
 body=raw[spans[0][0]:spans[0][1]].strip()
 tree,end=parse(tokens(body));assert end==len(tokens(body))
 units={}
 for u in children(tree,'symbol'):
  match=re.fullmatch(re.escape(name)+r'_(\d+)_\d+',u[1]);assert match,u[1]
  number=int(match[1]);pins=list(units.get(number,()))
  for pin in children(u,'pin'):
   at=children(pin,'at')[0];p=Pin(str(children(pin,'number')[0][1]),float(at[1]),float(at[2]),int(float(at[3])),str(pin[1]))
   if p.number not in {x.number for x in pins}:pins.append(p)
  units[number]=tuple(pins)
 return LibrarySymbol('zudo-osc-hole-field:'+name,body.replace(f'(symbol "{name}"',f'(symbol "zudo-osc-hole-field:{name}"',1),units)


def resolve(part):
 role=part.get('opamp_role');part_id=STANDARD['roles'][role]['part_id'] if role else part['part_id']
 record=SHORTLIST[part_id];name=CATALOG[record['mpn']]
 return part_id,record,load_symbol(name)


def _value(part):
 value=part.get('value')
 if value is None:return None
 unit=part.get('unit')
 if unit=='ohm':return f'{value:g} Ω'
 if unit=='F':return f'{value:g} F'
 return str(value)


def _exact_value(part,record):
 if part.get('value') is None:return True
 # The shortlist contains one exact representative per passive role. No inferred
 # value can be assigned to that MPN; only a documented value match can clear it.
 val=part['value'];id=record['id']
 known={'r_general':100000,'r_precision':100000,'r_power':499,'r_ladder':10000,'c_small':1e-10,'c_bypass':1e-7,'c_bulk':4.7e-6,'c_slew':1e-7}
 return id in known and abs(val-known[id]) <= abs(known[id])*1e-9


def cell_parts(cell_id,panel_uid,nets=None,*,ordinal_start=1,instance_tag=''):
 """Return every physical unit for one cell, with caller-supplied port net names.

 `nets` maps standard terminal names to module nets; unspecified names are local
 to this cell and namespaced by panel UID, preventing accidental joining.
 """
 if cell_id not in CELLS:raise KeyError(cell_id)
 if panel_uid not in UIDS:raise ValueError(f'unknown panel UID: {panel_uid}')
 nets=nets or {};cell=CELLS[cell_id];out=[]
 namespace=re.sub(r'[^A-Za-z0-9_]', '_', f'{cell_id}_{panel_uid}_{instance_tag}')
 label_prefix='C'+hashlib.sha1(namespace.encode()).hexdigest()[:6]
 if ordinal_start<1 or ordinal_start+len(cell['parts'])-1>99:raise ValueError('cell ordinals must fit 1..99')
 def net(value):
  if value=='NC':return None
  if value in ('+12V','-12V','+5V','AGND'):return nets.get(value,value)
  return nets.get(value,f'{label_prefix}_{value}')
 for ordinal,spec in enumerate(cell['parts'],ordinal_start):
  part_id,record,symbol=resolve(spec);term=spec['terminals'];aliases=AMP if spec.get('opamp_role') else PIN_ALIASES.get(part_id,{})
  assigned={aliases.get(key,key):net(value) for key,value in term.items()}
  if part_id=='fault_switch':
   # Unused switch channels are off; FF is intentionally not connected.
   assigned.update({n:net('AGND') for n in ('14','15','16','11','10','9','6','7','8')})
  if part_id=='reference':assigned.update({'1':None,'7':None,'8':None})
  if part_id.startswith('pot_'):assigned.update({'4':None,'5':None})
  key=namespace+'__'+re.sub('[^A-Za-z0-9_]','_',spec['ref'])
  prefix=PREFIX.get(part_id,'U')
  footprint_match=re.search(r'\(property "Footprint" "([^\"]+)"',symbol.body)
  if not footprint_match:raise ValueError(f'{symbol.lib_id}: footprint missing')
  footprint=footprint_match[1]
  # Values unresolved to an exact orderable passive are retained as values only.
  identity=record['mpn'] if _exact_value(spec,record) else ''
  attributes={'Role':f'{cell_id}:{spec["ref"]}','PanelUid':panel_uid,'MPN':identity,'Manufacturer':record['manufacturer'] if identity else '', 'LCSC':record.get('lcsc','') if identity else ''}
  for unit in sorted(u for u,pins in symbol.units.items() if pins):
   pins={pin.number:assigned.get(pin.number) for pin in symbol.units[unit]}
   # The selected active unit is 1; remaining sections are deliberate NCs.
   if part_id=='fault_switch' and unit in (2,3,4):pins={n:net('AGND') for n in pins}
   x=50.8+((len(out))%7)*50.8;y=50.8+((len(out))//7)*25.4
   out.append(Part(f'{key}.{unit}',symbol.lib_id,prefix,ordinal,unit,x,y,pins,value=_value(spec) or record['mpn'],footprint=footprint,attributes=attributes))
 return tuple(out)
