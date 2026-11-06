"""Explicit post-packing idle-package removal, rendered only into disposable paths."""
from pathlib import Path
from dataclasses import asdict,replace
from collections import defaultdict,Counter
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[5];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from design.spec.instrument import specification
from design.spec.modules.io_partition import AMP_MAPS,channel_signatures
from design.spec.cells._builder import load_symbol
from scripts.schgen.core import designator,render,LibrarySymbol
from scripts.schgen.generate import FIXTURES,PROJECT
from scripts.schgen.verify_netlist import expected_pin_nets
TARGET={f'U{i+n}':('OPA4197IPWR' if n in (16,17,18) else 'OPA4196IDR') for i in (100,200) for n in (12,13,16,17,18,19)}
CAPS={f'C{i+n}' for i in (100,200) for n in (28,29,31,32,33,34,40,41,42,43,44,45)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def sig(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def write(p,data):p.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
def prepare(families,instances):
 family=next(f for f in families if f.name=='sample_hold');insts=[i for i in instances if i.family==family.name]
 require([i.name for i in insts]==['H1','H2'],'exact instances')
 pins=expected_pin_nets(families,instances);members=defaultdict(set)
 for key,net in pins.items():members[net].add(key)
 removed_keys=set();rows=[];all_caps=set();private=set()
 for inst in insts:
  packages=defaultdict(list)
  for p in family.parts:
   if p.prefix=='U':packages[designator(p,inst)].append(p)
  for ref,symbol in sorted(TARGET.items()):
   if ref not in packages:continue
   units=packages[ref];byunit={p.unit:p for p in units};stem=units[0].key.rsplit('.',1)[0]
   require(set(byunit)=={1,2,3,4,5} and len(units)==5,'complete package '+ref)
   require(all(not p.dnp and p.in_bom and p.on_board and p.symbol.endswith(':'+symbol) for p in units),'exact fitted identity '+ref)
   require(byunit[5].pins=={'4':'+12V','11':'-12V'},'supply pins '+ref)
   followers=[]
   for unit,(out,minus,plus) in enumerate(AMP_MAPS,1):
    p=byunit[unit];net=p.pins[out];full=pins[(ref,out)]
    require(p.pins[minus]==net and p.pins[plus]=='AGND' and net not in (None,'AGND','+12V','-12V','+5V'),'idle follower '+ref)
    require(not p.attributes.get('LogicalCellKey') and not p.attributes.get('PanelUid'),'active role/panel '+ref)
    require(members[full]=={(ref,out),(ref,minus)},'external follower-net user '+ref)
    private.add(full);followers.append({'unit':unit,'pins':dict(p.pins),'native_semantic_net':full})
   caps=[p for p in family.parts if p.attributes.get('Decouples')==stem]
   require(len(caps)==2 and {tuple(sorted(p.pins.values())) for p in caps}=={tuple(sorted((r,'AGND'))) for r in ('+12V','-12V')},'bypass ownership '+ref)
   require(all(p.prefix=='C' and p.value=='100 nF' and not p.dnp and p.attributes.get('MPN')=='GRM188R71H104KA93D' for p in caps),'exact bypass '+ref)
   caprefs=[designator(p,inst) for p in caps];all_caps.update(caprefs)
   rows.append({'ref':ref,'instance':inst.name,'mpn':symbol,'stem':stem,'followers':followers,'supply_pins':byunit[5].pins,'bypasses':[{'ref':designator(p,inst),'key':p.key,'mpn':p.attributes['MPN'],'value':p.value,'pins':p.pins} for p in caps]})
   removed_keys.update(p.key for p in units+caps)
 require({r['ref'] for r in rows}==set(TARGET) and all_caps==CAPS and len(private)==48,'exact removal inventory')
 candidate=replace(family,parts=tuple(p for p in family.parts if p.key not in removed_keys))
 require(channel_signatures(family)==channel_signatures(candidate),'active channel loss')
 require(all(p in family.parts for p in candidate.parts),'surviving fields changed')
 newfamilies=tuple(candidate if f.name==family.name else f for f in families)
 after=expected_pin_nets(newfamilies,instances);removed_refs=set(TARGET)|CAPS
 require(after=={k:v for k,v in pins.items() if k[0] not in removed_refs},'surviving pin/net mutation')
 removed_nets=set(pins.values())-set(after.values());require(removed_nets==private,'unexpected removed net')
 panel=lambda fs:sorted((i.name,p.key,designator(p,i),p.attributes.get('PanelUid'),p.pins) for i in instances for f in fs if f.name==i.family for p in f.parts if p.attributes.get('PanelUid'))
 require(panel(families)==panel(newfamilies),'panel change')
 return newfamilies,{'status':'PROPOSAL ONLY; source no-active-function-loss, not physical validation','packages':rows,'removed_refs':sorted(removed_refs),'removed_family_part_keys':sorted(removed_keys),'removed_private_nets':sorted(private),'physical_package_count_removed':12,'physical_bypass_count_removed':24,'retained_pin_count':len(after),'before_pin_count':len(pins),'retained_pin_net_sha256':sig(sorted((r,p,n) for (r,p),n in after.items())),'active_channel_signatures_unchanged':True,'panel_bindings_unchanged':True,'retained_part_fields_unchanged':True,'analog_rail_bypass_reduction_uF':{'+12V':1.2,'-12V':1.2},'limits':'Removes only private followers and their supply/bypass branches. No guarantee of hardware behavior, decoupling/layout suitability, ERC/DRC or supply capacity.'}
def generated(families,instances):
 symbols={lib:LibrarySymbol.from_fixture(lib,ROOT/'scripts/schgen/fixtures'/f'{name}.kicad_sympart') for name,lib in FIXTURES.items()}
 for f in families:
  for p in f.parts:
   if p.symbol.startswith('zudo-osc-hole-field:') and p.symbol not in symbols:symbols[p.symbol]=load_symbol(p.symbol.split(':')[1])
 return render(families,instances,symbols,PROJECT)
def run(output,check=False):
 families,instances=specification();new,proposal=prepare(families,instances)
 before=generated(families,instances);after=generated(new,instances)
 require(set(before)==set(after),'schematic file roster')
 for name,body in before.items():require((ROOT/'schematic'/name).read_text()==body,'canonical generator drift '+name)
 require([p for p in before if before[p]!=after[p]]==['sheets/sample_hold.kicad_sch'],'unexpected schematic change')
 proposal['canonical_schematic_sha256']={p:sha(ROOT/'schematic'/p) for p in sorted(before)}
 proposal['candidate_schematic_sha256']={p:hashlib.sha256(body.encode()).hexdigest() for p,body in sorted(after.items())}
 if check:require(json.loads((HERE/'proposal.json').read_text())==proposal,'proposal replay drift')
 else:write(HERE/'proposal.json',proposal)
 if output is not None:
  require(output.resolve().parent==ROOT/'.circuit-cache' and not output.exists(),'new disposable sibling directory required');output.mkdir()
  for name,body in after.items():p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
  for name in ('sym-lib-table','fp-lib-table',PROJECT+'.kicad_pro'):
   body=(ROOT/'schematic'/name).read_text().replace('${KIPRJMOD}/../','${KIPRJMOD}/../../');(output/name).write_text(body)
 print('PASS explicit12quads+24owned bypass proposal; no canonical edits')
 return new,proposal
if __name__=='__main__':run(None if '--check' in sys.argv else Path(sys.argv[1]),'--check' in sys.argv)
