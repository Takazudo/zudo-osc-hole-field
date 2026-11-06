"""Exact A01 source inventory and candidate ownership delta; no CAD execution."""
import argparse
from collections import Counter,defaultdict
import json,sys
from pathlib import Path
import assembly as a
sys.path.insert(0,str(a.ROOT))
from design.spec.instrument import specification
from scripts.schgen.core import designator
ROOT=a.ROOT;OUT=a.OUT/'stage10'
OWNERS={'K':'rear-core','JR':'front-jack','P':'front-control'}
def need(ok,msg):
 if not ok:raise ValueError(msg)
def live_packages(ledger):
 source={p['ref']:p for p in ledger['packages']if p['instance']=='A01'}
 families,instances=specification();inst=next(i for i in instances if i.name=='A01');family=next(f for f in families if f.name==inst.family)
 records=defaultdict(list)
 for index,u in enumerate(ledger['package_units']):
  if u['ref']in source:records[u['ref']].append((index,u))
 logical_refs={part.key.rsplit('.',1)[0]:designator(part,inst)for part in family.parts}
 result={}
 for part in family.parts:
  ref=designator(part,inst);need(ref in source,'unretained live package '+ref)
  pins={pin:net if net is None or net in family.global_nets else '/A01/'+net for pin,net in part.pins.items()}
  attrs={k:v.replace('${SHEETNAME}','A01')for k,v in part.attributes.items()}
  need({'core':'K','jack':'JR','control':'P'}[attrs['BoardRegion']]==source[ref]['current_board'],'live source region drift '+ref)
  need(logical_refs.get(attrs.get('Decouples'))==source[ref]['decouples_ref'],'live bypass association drift '+ref)
  matches=[u for _,u in records[ref]if u['unit']==part.unit];need(len(matches)==1 and matches[0]['pins']==pins,'live/source unit or net drift '+ref)
  q=result.setdefault(ref,{'ref':ref,'footprint':part.footprint,'owner':OWNERS[source[ref]['current_board']],'current_board':source[ref]['current_board'],'pins':{},'units':[],'attributes':attrs,'unit_records':[],'unit_pin_record_indices':[i for i,_ in records[ref]],'source_package':source[ref]})
  need(q['footprint']==part.footprint and q['attributes']['MPN']==attrs['MPN'],'split physical package '+ref)
  need(not set(q['pins'])&set(pins),'duplicate physical pin '+ref)
  need(attrs['MPN']==source[ref]['mpn'] and part.dnp==source[ref]['dnp'],'identity/DNP drift '+ref)
  q['pins'].update(pins);q['units'].append(part.unit);q['unit_records'].append({'unit':part.unit,'pins':pins,'value':part.value,'attributes':attrs})
 need(set(result)==set(source)and len(result)==90,'A01 complete population')
 need(Counter(p['current_board']for p in result.values())=={'K':29,'JR':59,'P':2},'A01 board partition')
 for ref,q in result.items():need(sorted(q['units'])==sorted(source[ref]['units']),'whole package units '+ref)
 need(sum(len(q['units'])for q in result.values())==118 and sum(len(q['pins'])for q in result.values())==285,'unit/pin count')
 return result,source

def reconcile(ledger,prior,packages):
 need(len(ledger['packages'])==5904 and len(ledger['package_units'])==8226 and len(ledger['functions'])==33,'instrument conservation')
 refs={p['ref']for p in ledger['packages']};need(set(prior)==refs,'prior whole instrument overlay')
 nonosc={f['id']for f in ledger['functions']if f['family']!='OSC'}
 unresolved={p['ref']for p in ledger['packages']if p['instance']in nonosc and p['current_board']=='K'}
 power={p['ref']for p in ledger['packages']if p['instance']=='POWER'}
 need(len(unresolved)==2572 and len(power)==13,'prior K/POWER inventory')
 selected={r for r,p in packages.items()if p['current_board']=='K'}
 need(len(selected)==29 and selected<=unresolved,'A01 K subset')
 need(all(prior[r]=='proposed-nonOSC-carrier'for r in unresolved),'prior unhosted K proposal drift')
 overlay=dict(prior)
 for ref,p in packages.items():overlay[ref]='candidate-A01:'+p['owner']
 need({r for r in refs if overlay[r]!=prior[r]}==set(packages),'unexpected ownership delta')
 return {'prior_nonOSC_K_refs':sorted(unresolved),'newly_assigned_A01_K_refs':sorted(selected),'remaining_nonOSC_K_refs':sorted(unresolved-selected),'POWER_refs_unchanged':sorted(power),'counts':{'prior_nonOSC_K':2572,'new_candidate_K_assignments':29,'remaining_nonOSC_K':2543,'POWER_unknown':13},'status':'Candidate source ownership only; physical hosting not accepted'},overlay

def build():
 ledger_path=ROOT/'design/architecture-278/source-ledger.json';prior_path=a.OUT/'stage7/demonstrator-report.json';lock_path=ROOT/'design/grid/placements.lock.json'
 ledger=json.loads(ledger_path.read_text());prior=json.loads(prior_path.read_text());locked=json.loads(lock_path.read_text())
 packages,source=live_packages(ledger);fixed=[p for p in locked['placements']if p['block']=='A01'];need(len(locked['placements'])==438 and len(fixed)==9,'fixed hardware population')
 function=next(f for f in ledger['functions']if f['id']=='A01');need(set(function['source_packages'])==set(packages)and set(function['panel_uids'])=={p['uid']for p in fixed},'function source coverage')
 need({p['attributes']['PanelUid']for p in packages.values()if p['attributes']['PanelUid']}=={p['uid']for p in fixed},'live fixed ownership')
 nets=defaultdict(list);nc=[];bypasses=[]
 for ref,p in packages.items():
  for pin,net in p['pins'].items():
   endpoint={'ref':ref,'pin':pin,'owner':p['owner']}
   (nc if net is None else nets[net]).append(endpoint)
  target=source[ref]['decouples_ref']
  if target:
   need(target in packages and packages[target]['owner']==p['owner'],'bypass split')
   bypasses.append({'bypass_ref':ref,'target_ref':target,'owner':p['owner'],'bypass_pins':p['pins'],'target_pins':packages[target]['pins']})
 need(len(bypasses)==17,'bypass association count')
 reconciliation,overlay=reconcile(ledger,prior['whole_instrument_host_overlay'],packages)
 paths=[ledger_path,prior_path,lock_path,ROOT/'scripts/schgen/core.py',ROOT/'scripts/architecture278/implementation/assembly.py',ROOT/'scripts/architecture278/implementation/candidate.py',Path(__file__),Path(__file__).with_name('test_stage10_inventory.py')]
 paths += [ROOT/'design/standard/electrical-standard.json',ROOT/'design/standard/parts-shortlist.json']+list((ROOT/'symbols/src').glob('*.kicad_sym'))
 paths+=list((ROOT/'design/spec').rglob('*.py'))+list((ROOT/'design/spec/cells').rglob('*.json'))
 return {'status':'A01 SOURCE INVENTORY; NO PHYSICAL ACCEPTANCE','packages':packages,'fixed_controls':fixed,'function':function,'bypass_associations':bypasses,'net_endpoints':dict(nets),'crossing_nets':{n:rows for n,rows in nets.items()if len({r['owner']for r in rows})>1},'NC_endpoints':nc,'prior_hosting_reconciliation':reconciliation,'whole_instrument_host_overlay':overlay,'metadata_findings':[{'ref':'RV1308','captured_package_MPN':source['RV1308']['mpn'],'panel_component':next(p['component']for p in fixed if p['ref']=='RV1308'),'status':'B104 captured circuit versus B103 panel metadata; preserved, unresolved identity/assembly evidence; no substitution'}],'unselected_MPN_refs':[r for r,p in source.items()if not p['mpn']],'counts':{'packages':90,'units':118,'pins_including_NC':285,'NC_pins':len(nc),'connected_nets':len(nets),'bypass_associations':17,'fixed_devices':9,'K':29,'JR':59,'P':2},'source_sha256':a.binding(paths),'native':'NOT RUN','simulation':'NOT RUN','hardware_acceptance':False}
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();body=json.dumps(build(),sort_keys=True,separators=(',',':'))+'\n';path=OUT/'inventory-report.json'
 if args.check:need(path.read_text()==body,'stale Stage10 inventory')
 else:path.write_text(body)
 print('A01 inventory90/118/285;29K assignments;2543remainingK+13POWER unknown')
if __name__=='__main__':main()
