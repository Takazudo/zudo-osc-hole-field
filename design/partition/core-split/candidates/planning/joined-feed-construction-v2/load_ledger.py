#!/usr/bin/env python3
"""Signed per-pad DC current ledger for the E16 KA/KB core boards; a conditional load study, not a compliance claim.

Sign: positive current flows FROM the copper network INTO the device pin (a draw);
a device returning current into AGND or -12V copper appears negative there.
Pad rows carry only datasheet-backed or explicitly assumed device supply-pin
currents. Planning worksheet totals are whole-module responsibility (K/JL/JR/P/EL)
and are never divided over pads or parts: their unmapped remainder is a
board/net-level allowance with no pad. Feeds (CS247, KA main lands) are supports
with current null, solved later.
"""
import argparse,csv,gzip,hashlib,json,math,re,sys
from collections import Counter,defaultdict
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
RAILS=('+12V','-12V','+5V');NETS=RAILS+('AGND',);BOARDS=('KA','KB')
POWER='design/partition/core-split/power/';EV='design/partition/core-split/candidates/planning/joined-feed-construction-v2/evidence/'
SKILLS='.claude/skills/';INVENTORY=SKILLS+'component-spec-audit/references/inventory.json'
# symbol -> (fact_id, amplifiers per package or 1, value keys per scenario, provenance)
FACTS={'OPA4196IDR':('fact-op-audio-quiescent-current',4,{'normal-typ-v1':'typical_at_25C','normal-max-v1':'maximum_full_temperature'},'supported_pin_current'),
 'OPA4197IPWR':('fact-op-precision-quiescent-current',4,{'normal-typ-v1':'typical_at_25C','normal-max-v1':'maximum_full_temperature'},'supported_pin_current'),
 'SN74HC14DR':('fact-schmitt-quiescent-table-max',1,{'normal-typ-v1':None,'normal-max-v1':None},'conditional_assumption'),
 'SN74HC74DR':('fact-flipflop-quiescent-table-max',1,{'normal-typ-v1':None,'normal-max-v1':None},'conditional_assumption')}
UNIT={'uA per amplifier':1e-6,'mA per amplifier':1e-3,'A':1.}
SCENARIOS={'normal-typ-v1':'All fitted KA/KB ICs powered at +/-12 V and +5 V; OPA4196/OPA4197 typical 25 C quiescent current, IO=0 (no output/signal load); '
 'SN74HC14/HC74 static ICC table maximum (VCC=6 V, IO=0, inputs at rails) as the only bundle-backed +5 V value; EL harness demand at the contract ceiling; everything else unmapped.',
 'normal-max-v1':'As normal-typ-v1 but OPA4196/OPA4197 full-temperature (-40..125 C) maximum quiescent current, IO=0; not a worst-case or fault total.'}
LOGIC_RULE='Static ICC table max at VCC=6 V, TA=-40..85 C, IO=0 used for the 5 V state (no 5 V typical in the bundle); all of it enters VCC pin 14 and leaves GND pin 7; switching current omitted.'
OPA_RULE='Quiescent current per amplifier x 4 amplifiers (unused channels biased); no AGND pin, so by KCL all of it enters V+ (pin 4) and leaves V- (pin 11).'
EL_LIMIT='return_and_fault_contract.existing_EL_bounds.EL_rail_current_contract_mA'
TOL=1e-12
def need(c,m):
 if not c:raise ValueError(m)
def rnd(x):return None if x is None else round(x,12)
def canon(o):return json.dumps(o,sort_keys=True,separators=(',',':'))
class Inputs:
 def __init__(s):s.sha={}
 def raw(s,rel):b=(ROOT/rel).read_bytes();s.sha[rel]=hashlib.sha256(b).hexdigest();return b
 def json(s,rel):b=s.raw(rel);return json.loads(gzip.decompress(b) if rel.endswith('.gz') else b)
def bundle_of(inv,symbol):
 key=lambda m:re.sub('[^A-Z0-9]','',m.upper());hit=[l['owner_skill'] for l in inv['lines'] if key(l['mpn'])==key(symbol)]
 need(len(hit)==1,'one owner bundle for '+symbol);return SKILLS+hit[0]+'/facts.json'
def supply_value(inp,inv,symbol,scen):
 """Per-package current (A) from the owner bundle fact, with its source and condition."""
 fid,amps,keys,prov=FACTS[symbol];path=bundle_of(inv,symbol);facts={f['fact_id']:f for f in inp.json(path)['facts']}
 f=facts[fid];need(f['verdict'].startswith('PASS'),'unsupported fact '+fid);need(f['unit'] in UNIT,'unit '+f['unit'])
 if amps>1:need('OUT D' in next(v['value'] for k,v in facts.items() if k.endswith('-pinout')),'quad pinout')
 v=f['value'][keys[scen]] if keys[scen] else f['value']
 return rnd(v*UNIT[f['unit']]*amps),{'source':f'{path}#{fid}'+(f'.{keys[scen]}' if keys[scen] else ''),'condition':f['conditions'],'locator':f['locator'],
  'derivation':f'{v} {f["unit"]}'+(f' x {amps} amplifiers' if amps>1 else ' per package'),'provenance':prov,'rule':OPA_RULE if amps>1 else LOGIC_RULE}
def unmapped_reason(inp,inv,symbol):
 if symbol=='ADG5412FBRUZ':return 'Bundle has only normal-mode IDD maximum (VDD/VSS=+/-16.5 V, full temperature); no typical, no ISS/GND return split, so device KCL cannot be closed.'
 path=bundle_of(inv,symbol);facts=inp.json(path)['facts']
 lim=[f['fact_id'] for f in facts if f['fact_id'].endswith('electrical-limits')]
 return f'No supply/quiescent-current fact in owner bundle {path}'+(f' ({lim[0]} not promoted)' if lim else '')+'.'
def build():
 inp=Inputs();contract=inp.json(POWER+'contract.json');harness=inp.json(POWER+'harness-contract.json');iface=inp.json(POWER+'joined/interfaces.json')['two']
 parts={r['ref']:r for r in csv.DictReader(inp.raw(POWER+'package-ownership.csv').decode().splitlines())}
 inv=inp.json(INVENTORY);review=inp.json(EV+'mandatory-physical-ports-review.json');two=contract['options']['two']
 mand={p['id']:p for p in review['mandatory_ports']}
 jpins={e['pcb_reference']:(h['id'],h['source_boards'],e['pin_map']) for h in harness['harnesses'] for e in h['endpoints'] if e['board']=='K'}
 lands={l['reference']:l for l in contract['existing_main_lands']};wires={r:w['id'] for w in contract['existing_main_wires'] for r in w['terminal_refs']}
 need(sorted(iface['old_main_lands']['KA'])==sorted(r for r,l in lands.items() if l['candidate_owner']=='KA') and not iface['old_main_lands']['KB'],'main lands are KA only')
 cs_wire={f'CS247-{e["board"]}-W{c["id"][-1]}':c['id'] for c in iface['new_conductors'] for e in c['ends']}
 ports={};unresolved={}
 for b in BOARDS:
  g=inp.json(EV+f'e16/{b}-t2-port-graph.json.gz');need(g['board']==b,'board');ports[b]=g['physical_ports']
  ob=inp.json(EV+f'e16/{b}-t2-port-obligations.json');need(ob['physical_pad_count']==len(ports[b]),'obligation pad count');unresolved[b]={u['pad_id'] for u in ob['unresolved']}
 symbols=sorted({f['symbol'] for b in BOARDS for f in two['boards'][b]['fitted_ic_supply_pins']})
 values={(s,sc):supply_value(inp,inv,s,sc) for s in FACTS for sc in SCENARIOS}
 reasons={s:unmapped_reason(inp,inv,s) for s in symbols if s not in FACTS}
 # Non-rail supply nets (AS3340D VEE5, NOISE2 NOISE_VDD) are fed through parts found in the package netlist.
 net_parts=defaultdict(set)
 for r,p in parts.items():
  for n in json.loads(p['pins']).values():net_parts[n].add(r)
 mediated={}
 for b in BOARDS:
  for f in two['boards'][b]['fitted_ic_supply_pins']:
   for pin,n in f['supply_pins'].items():
    if n in NETS:continue
    full=f'/{f["instance"]}/{n}';hop=[]
    for r in sorted(net_parts[full]-{f['ref']}):
     pins=json.loads(parts[r]['pins'])
     if not r.startswith('R'):continue
     for q,m in pins.items():
      if m in RAILS:hop.append({'pad_ref':r,'pad':q,'net':m,'kind':'passive_mediated','path':f'{f["ref"]}.{pin} {full} -> {r} ({parts[r]["value"]}) -> {m}'})
      elif m!=full:
       for u in sorted(net_parts[m]):
        if u.startswith('U') and u!=f['ref']:
         up=json.loads(parts[u]['pins'])
         at=[k for k,v in up.items() if v==m]
         hop+=[{'pad_ref':u,'pad':k,'net':v,'kind':'active_mediated','path':f'{f["ref"]}.{pin} {full} -> {r} ({parts[r]["value"]}) -> {m} -> {u}.{"/".join(at)} -> {u}.{k} {v}'} for k,v in up.items() if v=='-12V']
    mediated[(f['ref'],pin)]=hop
 med_pad={}
 for hops in mediated.values():
  for h in hops:med_pad.setdefault((h['pad_ref'],h['pad']),h)
 # Pad rows.
 rows=[];groups=[];census_ic={}
 for b in BOARDS:
  fit={f['ref']:f for f in two['boards'][b]['fitted_ic_supply_pins']};dnp=set(two['boards'][b]['dnp_refs'])
  el=defaultdict(list)
  for sc in SCENARIOS:
   for p in ports[b]:
    ref,pad,net,pid=p['ref'],p['pad'],p['net'],p['id'];need(net in NETS,'rail pad census');m=mand[pid];need(m['board']==b,'review board')
    row=dict(scenario_id=sc,board=b,ref=ref,pad=pad,pad_id=pid,net=net,current_A=None,units='A',operating_condition=SCENARIOS[sc],physical_owner=None,source=None,
     provenance='no_amount',mapping_status=None,pad_class=None,structurally_unresolved=pid in unresolved[b],direct_load_member=m['source_direct_load_member'],note=None)
    if pid.startswith('CS247-'):
     row.update(physical_owner={'interface':cs_wire[pid]},source=POWER+'joined/interfaces.json#two.new_conductors',pad_class='network_support',mapping_status='interface_support_solved_later')
    elif ref in lands:
     need(lands[ref]['candidate_owner']==b and lands[ref]['net']==net,'main land identity')
     row.update(physical_owner={'interface':wires[ref]},source=POWER+'contract.json#existing_main_lands',pad_class='network_support',mapping_status='interface_support_solved_later')
    elif ref.startswith('J'):
     hid,src,pm=jpins[ref];need(pm[pad]==net,'harness pin net')
     row.update(physical_owner={'interface':hid,'boards':src},source=POWER+'harness-contract.json#harnesses')
     if net in RAILS:
      need('EL' in src,'only EL harnesses carry rails');el[net].append(pid)
      row.update(pad_class='external_interface_rail',mapping_status='interface_demand_group_member',note='EL demand booked once on the group record; per-pad split solved later (no equal-current assertion).')
     else:row.update(pad_class='interface_ground_return',mapping_status='interface_return_unallocated',note='GH/harness AGND return; signal and EL return currents unallocated.')
    elif ref in fit:
     f=fit[ref];sym=f['symbol'];row['physical_owner']={'ref':ref,'instance':f['instance'],'symbol':sym}
     if f['supply_pins'].get(pad)==net:
      row['pad_class']='ic_supply_pin'
      if sym in FACTS:
       v,meta=values[(sym,sc)];sign=-1 if net in('-12V','AGND') else 1
       need((sym.startswith('OPA') and net in('+12V','-12V')) or (sym.startswith('SN74') and net in('+5V','AGND')),'supply pin role')
       row.update(current_A=rnd(sign*v),source=meta['source'],provenance=meta['provenance'],mapping_status='supported' if meta['provenance']=='supported_pin_current' else 'conditional',
        note=f"{meta['derivation']}; {meta['rule']} Condition: {meta['condition']}")
      else:row.update(source=POWER+'contract.json#options.two.boards.'+b+'.fitted_ic_supply_pins',mapping_status='unmapped_supply_pin',note=reasons[sym])
     else:row.update(pad_class='ic_rail_tied_nonsupply_pin',source=POWER+'package-ownership.csv',mapping_status='unmapped_nonsupply_rail_pin',note='Rail/AGND-tied IC pin outside the contract supply map; leakage/signal current omitted.')
     hop=med_pad.get((ref,pad))
     if hop:row['note']=(row['note'] or '')+f" Also carries unsupported active-mediated supply current: {hop['path']}."
    else:
     part=parts[ref];need(part['two_owner']==b and json.loads(part['pins']).get(pad)==net,'netlist pad');row['physical_owner']={'ref':ref,'instance':part['instance'],'value':part['value'] or part['mpn']}
     row['source']=POWER+'package-ownership.csv'
     if ref in dnp or part['dnp']=='True':need(ref in dnp and part['dnp']=='True','DNP agreement');row.update(current_A=0.0,pad_class='dnp_part',mapping_status='dnp_zero_dc')
     elif ref.startswith('C'):row.update(current_A=0.0,pad_class='capacitor',mapping_status='passive_zero_dc')
     elif ref.startswith('TP'):row.update(current_A=0.0,pad_class='test_point',mapping_status='test_point_zero_dc')
     elif (ref,pad) in med_pad:h=med_pad[(ref,pad)];row.update(pad_class='passive_mediated_supply',mapping_status='unmapped_passive_mediated',note=f"Conditional mapping of an unmapped IC supply: {h['path']}.")
     elif ref.startswith('R'):row.update(pad_class='resistive_rail_path',mapping_status='unmapped_resistive_path',note='Resistive DC path to a rail/AGND; operating-point current unsupported.')
     elif ref[:1] in 'DQ':row.update(pad_class='semiconductor_rail_pin',mapping_status='unmapped_semiconductor',note='Diode/transistor/LED rail pin; operating current unsupported.')
     else:raise ValueError('unclassified pad '+ref)
    rows.append(row)
  for sc in SCENARIOS:
   lim=contract['return_and_fault_contract']['existing_EL_bounds']['EL_rail_current_contract_mA']
   for net in NETS:
    pads=sorted({pid for pid in el.get(net,[])}) if net in RAILS else sorted({p['id'] for p in ports[b] if p['ref'] and p['ref'] in jpins and 'EL' in jpins[p['ref']][1] and p['net']=='AGND'})
    if not pads:continue
    sign=-1 if net=='-12V' else 1
    groups.append(dict(scenario_id=sc,board=b,id=f'EL-harness-{net}',net=net,pad_ids=pads,current_A=rnd(sign*lim[net]/1000) if net in RAILS else None,units='A',
     provenance='external_interface_demand',source=POWER+'contract.json#'+EL_LIMIT,physical_owner={'interface':'EL-E1..EL-E6','module':'EL'},
     operating_condition='Contract ceiling for the whole EL board, not a typical value; split across parallel harness pads solved later.' if net in RAILS else
      'EL AGND return not booked: signed EL +/-12 V split unsupported, so its return cannot be derived without invented values.'))
  for f in two['boards'][b]['fitted_ic_supply_pins']:
   sym=f['symbol'];hops=[h for pin in f['supply_pins'] for h in mediated.get((f['ref'],pin),[])]
   if sym in FACTS:st,why=('mapped','Quiescent supply current at IO=0; output/signal current omitted.') if FACTS[sym][3]=='supported_pin_current' else ('partially_mapped',LOGIC_RULE)
   else:st,why='unmapped',reasons[sym]
   census_ic[f['ref']]=dict(board=b,ref=f['ref'],instance=f['instance'],symbol=sym,status=st,reason=why,mediated_supply=hops)
 rows.sort(key=lambda r:(r['scenario_id'],r['board'],r['net'],r['ref'] or '',r['pad'] or '',r['pad_id']))
 groups.sort(key=lambda g:(g['scenario_id'],g['board'],g['id']))
 allowances,recon=reconcile_build(two,contract,rows,groups)
 ledger=dict(status='CONDITIONAL_LOAD_SCENARIO',sign_convention='current_A > 0: from copper INTO the device pin (draw); < 0: device injects into that copper; null: no amount booked (support or unmapped).',
  scenarios=SCENARIOS,records=rows,interface_demands=groups,allowances=allowances)
 ledger['ledger_sha256']=hashlib.sha256(canon({k:ledger[k] for k in ('records','interface_demands','allowances')}).encode()).hexdigest()
 ledger.update(census=census(rows,ports,census_ic),reconciliation=recon,kcl=kcl(rows),double_count_issues=double_counts(ledger),
  omissions=omissions(rows,census_ic),full_scope_budget_acceptance=False,
  acceptance_blockers=['Most fitted IC supply currents unmapped (no bundle-backed value); their planning share stays a pad-less allowance.',
   'Resistive, diode/transistor/LED, rail-tied pin and passive/active-mediated supply currents unsupported.',
   'EL demand is a contract ceiling with no per-pad split and no signed AGND return.',
   'Planning worksheet is whole-module responsibility across K/JL/JR/P/EL, not allocated core-pad current.',
   'Some current-carrying pads are structurally unresolved (feed-disconnected) in the t2 graph.'],
  input_sha256=dict(sorted(inp.sha.items())),method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 return ledger
def reconcile_build(two,contract,rows,groups):
 al=[];rec=[]
 for sc in SCENARIOS:
  for b in BOARDS:
   plan=two['boards'][b]['module_responsibility_planning_mA']
   for net in RAILS:
    amt=lambda prov:math.fsum(r['current_A'] for r in rows if r['scenario_id']==sc and r['board']==b and r['net']==net and r['provenance']==prov and r['current_A'] is not None)
    s,c=abs(amt('supported_pin_current'))*1e3,abs(amt('conditional_assumption'))*1e3
    e=abs(math.fsum(g['current_A'] for g in groups if g['scenario_id']==sc and g['board']==b and g['net']==net and g['current_A'] is not None))*1e3
    # EL demand is an external interface ceiling whose overlap with the KB worksheet is unresolved
    # (worksheet charges 0.55 mA per EL stage LED; the EL contract charges 4.63 mA): it is not taken out of KB's planning total.
    u=plan[net]-s-c;sign=-1 if net=='-12V' else 1
    al.append(dict(scenario_id=sc,id=f'{b}:{net}:module-responsibility-remainder',board=b,net=net,pad_id=None,current_A=rnd(sign*max(u,0)/1e3),units='A',provenance='unmapped_allowance',
     source=POWER+f'contract.json#options.two.boards.{b}.module_responsibility_planning_mA',operating_condition='Planning residue (upper planning units), not a typical load; no pad assignment.'))
    rec.append(dict(scenario_id=sc,board=b,net=net,planning_mA=plan[net],supported_pin_mA=rnd(s),conditional_mA=rnd(c),external_interface_mA=rnd(e),unmapped_remainder_mA=rnd(max(u,0)),
     identity_holds=abs(s+c+u-plan[net])<1e-9,over_allocated=u<-1e-9,external_interface_relation='UNRESOLVED: EL ceiling booked once as external demand, outside this planning total' if e else None,
     note='Supported and conditional amounts are subsets of the whole-module planning total, counted once; package Iq is not added on top. The remainder is planning minus those amounts; over_allocated flags a negative remainder. External interface demand (EL ceiling) is reported separately and is not assumed to lie inside the planning total.'))
  for k,label in (('global_allowances_charged_once_mA','GLOBAL'),('noncore_only_planning_mA','NONCORE_ONLY')):
   for net in RAILS:
    sign=-1 if net=='-12V' else 1
    al.append(dict(scenario_id=sc,id=f'{label}:{net}:{k}',board=label,net=net,pad_id=None,current_A=rnd(sign*two[k][net]/1e3),units='A',provenance='unmapped_allowance',source=POWER+'contract.json#options.two.'+k,
     operating_condition='Charged once at instrument level; not allocated to KA/KB copper.' if label=='GLOBAL' else 'Non-core modules (B1/B2/X1/X2); outside core copper.'))
 for net in RAILS:
  need(abs(sum(two['boards'][b]['module_responsibility_planning_mA'][net] for b in BOARDS)+two['noncore_only_planning_mA'][net]+two['global_allowances_charged_once_mA'][net]-two['total_planning_mA'][net])<1e-5,'planning conservation')
 al.sort(key=lambda a:(a['scenario_id'],a['id']))
 return al,dict(per_board_net=rec,excluded_reserves={'new_protection_auxiliary_share_mA_per_rail':{b:two['boards'][b]['new_protection_auxiliary_share_mA_per_rail'] for b in BOARDS},
  'continuous_requirement_reserve_mA':two['continuous_requirement_reserve_mA'],'note':'Reserves, not loads; no pad, not counted.'},total_planning_mA=two['total_planning_mA'])
def kcl(rows):
 dev=defaultdict(list);bn=defaultdict(list)
 for r in rows:
  if r['current_A'] is None:continue
  bn[(r['scenario_id'],r['board'],r['net'])].append(r['current_A'])
  if r['current_A']:dev[(r['scenario_id'],r['board'],r['ref'])].append(r['current_A'])
 out={}
 for sc in SCENARIOS:
  d={k[2]:math.fsum(v) for k,v in dev.items() if k[0]==sc}
  boards={b:{n:rnd(math.fsum(bn.get((sc,b,n),[]))) for n in NETS} for b in BOARDS}
  out[sc]=dict(devices_included=len(d),max_abs_device_residual_A=max(map(abs,d.values()),default=0.0),
   board_net_sum_A=boards,board_residual_A={b:rnd(math.fsum(boards[b].values())) for b in BOARDS},global_residual_A=rnd(math.fsum(v for b in boards.values() for v in b.values())),
   agnd_injection_A={b:boards[b]['AGND'] for b in BOARDS},
   scope='Included set = pad rows with nonzero current (device supply pins). Interface supports and EL group demand are outside device KCL.')
 return out
def census(rows,ports,ic):
 out={}
 for sc in SCENARIOS:
  rs=[r for r in rows if r['scenario_id']==sc];ids=Counter(r['pad_id'] for r in rs)
  out[sc]=dict(rows=len(rs),unique_pad_ids=len(ids),graph_pads=sum(len(p) for p in ports.values()),cs247_terminals=sum(1 for r in rs if r['pad_id'].startswith('CS247-')),
   every_graph_pad_exactly_once=set(ids)=={p['id'] for v in ports.values() for p in v} and max(ids.values())==1,
   by_class={f"{b}|{c}|{n}":k for (b,c,n),k in sorted(Counter((r['board'],r['pad_class'],r['net']) for r in rs).items())},
   by_status={f"{b}|{s}":k for (b,s),k in sorted(Counter((r['board'],r['mapping_status']) for r in rs).items())},
   current_on_unresolved_pads=sum(1 for r in rs if r['current_A'] and r['structurally_unresolved']))
 ics=sorted(ic.values(),key=lambda x:x['ref'])
 out['fitted_ics']=dict(summary={f"{b}|{s}":k for (b,s),k in sorted(Counter((i['board'],i['status']) for i in ics).items())},
  by_symbol={f"{b}|{y}|{s}":k for (b,y,s),k in sorted(Counter((i['board'],i['symbol'],i['status']) for i in ics).items())},devices=ics)
 return out
def double_counts(ledger):
 issues=[];seen=Counter((r['scenario_id'],r['board'],r['pad_id'],r['net']) for r in ledger['records'])
 issues+=[f'duplicate pad record {k}' for k,n in seen.items() if n>1]
 for name in ('interface_demands','allowances'):
  c=Counter((g['scenario_id'],g['id']) for g in ledger[name]);issues+=[f'duplicate {name} {k}' for k,n in c.items() if n>1]
 grp={(g['scenario_id'],p) for g in ledger['interface_demands'] for p in g['pad_ids']}
 issues+=[f'pad amount also in an interface group {r["pad_id"]}' for r in ledger['records'] if r['current_A'] and (r['scenario_id'],r['pad_id']) in grp]
 issues+=[f'pad row carries an allowance {r["pad_id"]}' for r in ledger['records'] if r['provenance']=='unmapped_allowance']
 issues+=[f'allowance has a pad {a["id"]}' for a in ledger['allowances'] if a['pad_id'] is not None]
 return sorted(issues)
def omissions(rows,ic):
 return ['Op-amp/comparator/logic output and signal load currents (no supported values); they do not alter the supply-to-supply/ground KCL of included rows.',
  'Switching/dynamic and capacitor charge currents (DC ledger only).',
  'Unmapped fitted IC supply currents: '+', '.join(f"{s} x{n}" for s,n in sorted(Counter(i['symbol'] for i in ic.values() if i['status']=='unmapped').items()))+'.',
  'AS3340D VEE5 current: supplied via R1x48 100 ohm from an OPA4197 VEE_DRIVE output, so it appears on that op-amp -12V pad; amount unsupported.',
  'NOISE2 NOISE_VDD current: supplied from +5V through R6101 22 ohm; amount unsupported.',
  'Resistive rail paths, diodes/transistors/LEDs and rail-tied IC pins: current null.',
  'GH/harness AGND return currents and the EL AGND return: unallocated.',
  f"Supply-voltage condition of the OPA4196/OPA4197 quiescent facts is not stated in the bundle facts; values applied at +/-12 V."]
def main():
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',required=True);a.add_argument('--check',action='store_true');o=a.parse_args()
 led=build();text=json.dumps(led,indent=1,sort_keys=True)+'\n';path=Path(o.output)/'load-ledger.json'
 if o.check:
  ok=path.read_text()==text;print(('MATCH ' if ok else 'MISMATCH ')+led['ledger_sha256']);sys.exit(0 if ok else 1)
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
 k=led['kcl'];print(json.dumps(dict(ledger_sha256=led['ledger_sha256'],issues=led['double_count_issues'],kcl={s:k[s]['board_net_sum_A'] for s in k}),indent=1))
if __name__=='__main__':main()
