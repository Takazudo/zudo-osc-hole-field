"""Exact source supply-pin semantics for tagged bypasses; no pcbnew dependency."""
import hashlib,json
from pathlib import Path
from scripts.schgen.core import parse,tokens,children
# These exact owner-backed supplies are passive in the current symbols.
PASSIVE_SUPPLIES={
 'NOISE2':('component-electric-druid-noise2',{'1':'+5V supply'}),
 'LF398M_NOPB':('component-ti-lf398m-nopb',{'3':'V-','12':'V+'}),
 'CD74HC221M96':('component-ti-cd74hc221m96',{'16':'VCC'}),
 'TMUX6112PWR':('component-ti-tmux6112pwr',{'4':'VSS negative supply','13':'VDD positive supply'}),
 'TMUX7412FRRPR':('component-ti-tmux7412frrpr',{'2':'VSS negative supply','11':'VDD positive supply'}),
}
def supply_pins(root,symbol):
 path=root/'symbols/src'/(symbol+'.kicad_sym');tree,_=parse(tokens(path.read_text()));pins={}
 for lib in children(tree,'symbol'):
  for unit in children(lib,'symbol'):
   for pin in children(unit,'pin'):
    number=children(pin,'number')[0][1]
    if number in pins:raise ValueError('duplicate source symbol pin:'+symbol+'.'+number)
    pins[number]=pin[1]
 hashes={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest()}
 selected={n for n,kind in pins.items() if kind=='power_in'}
 if symbol in PASSIVE_SUPPLIES:
  slug,expected=PASSIVE_SUPPLIES[symbol];owner=root/'.claude/skills'/slug/'pin-map.json';data=json.loads(owner.read_text())
  maps=[m for m in data['pin_maps'] if m['symbol']==symbol]
  if len(maps)!=1:raise ValueError('ambiguous owner pin map:'+symbol)
  indexed={p['symbol_pin']:p for p in maps[0]['pins']}
  if len(indexed)!=len(maps[0]['pins']):raise ValueError('duplicate owner symbol pin:'+symbol)
  for n,function in expected.items():
   if pins.get(n)!='passive' or indexed[n]['footprint_pad']!=n or indexed[n]['function']!=function:raise ValueError('passive supply evidence drift:'+symbol+'.'+n)
  selected.update(expected);hashes[str(owner.relative_to(root))]=hashlib.sha256(owner.read_bytes()).hexdigest()
 if not selected:raise ValueError('no exact source supply semantics:'+symbol)
 return selected,hashes

def bypass_pairs(capacitor_pads,ic_pads,selected_supply_pins):
 """Pad maps number->net. Require tagged two-terminal supply-to-AGND topology.

 Untagged signal/storage/feedback capacitors never call this function. A
 wrongly tagged one fails instead of matching any same-net IC signal pin.
 """
 if len(capacitor_pads)!=2 or list(capacitor_pads.values()).count('AGND')!=1:
  raise ValueError('tagged bypass is not exact two-terminal supply-to-AGND')
 rail_pad=next(n for n,net in capacitor_pads.items() if net!='AGND');net=capacitor_pads[rail_pad]
 if not net:raise ValueError('unconnected bypass supply')
 missing=selected_supply_pins-set(ic_pads)
 if missing:raise ValueError('source supply pin missing from native IC:'+','.join(sorted(missing)))
 matches=sorted(n for n in selected_supply_pins if ic_pads[n]==net)
 if not matches:raise ValueError('bypass net does not reach exact IC supply pin')
 return rail_pad,net,matches

def source_bypass_binding(root,parent,capacitor,pin_nets):
 """Resolve exactly one source IC supply pad; tied logic pins cannot qualify."""
 if capacitor.get('decouples_ref')!=parent['ref']:
  raise ValueError('source bypass owner mismatch')
 if parent['ref'] not in pin_nets or capacitor['ref'] not in pin_nets:
  raise ValueError('source bypass pin map missing')
 selected,_=supply_pins(root,parent['symbol'])
 cap_pin,rail,ic_pins=bypass_pairs(pin_nets[capacitor['ref']],pin_nets[parent['ref']],selected)
 if len(ic_pins)!=1:
  raise ValueError('ambiguous source supply pad for bypass:'+capacitor['ref'])
 return cap_pin,rail,ic_pins[0]
