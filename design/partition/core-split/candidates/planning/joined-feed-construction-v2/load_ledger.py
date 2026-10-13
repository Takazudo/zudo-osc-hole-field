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
FACTS={'OPA4196IDR':('fact-op-audio-quiescent-current',4,{'normal-typ-v1':'typical_at_25C','normal-max-25c-v1':'maximum_at_25C','normal-max-v1':'maximum_full_temperature'},'supported_pin_current'),
 'OPA4197IPWR':('fact-op-precision-quiescent-current',4,{'normal-typ-v1':'typical_at_25C','normal-max-25c-v1':'maximum_at_25C','normal-max-v1':'maximum_full_temperature'},'supported_pin_current'),
 'SN74HC14DR':('fact-schmitt-quiescent-table-max',1,{'normal-typ-v1':None,'normal-max-25c-v1':None,'normal-max-v1':None},'conditional_assumption'),
 'SN74HC74DR':('fact-flipflop-quiescent-table-max',1,{'normal-typ-v1':None,'normal-max-25c-v1':None,'normal-max-v1':None},'conditional_assumption')}
UNIT={'uA per amplifier':1e-6,'mA per amplifier':1e-3,'A':1.}
SCENARIOS={'normal-typ-v1':'All fitted KA/KB ICs powered at +/-12 V and +5 V; OPA4196/OPA4197 typical 25 C quiescent current, IO=0 (no output/signal load); '
 'SN74HC14/HC74 static ICC table maximum (VCC=6 V, IO=0, inputs at rails) as the only bundle-backed +5 V value; EL harness demand at the contract ceiling; everything else unmapped.',
 'normal-max-25c-v1':'As normal-typ-v1 but OPA4196/OPA4197 maximum quiescent current at 25 C, IO=0; not a worst-case or fault total.',
 'normal-max-v1':'As normal-typ-v1 but OPA4196/OPA4197 full-temperature (-40..125 C) maximum quiescent current, IO=0; not a worst-case or fault total.'}
LOGIC_RULE='Static ICC table max at VCC=6 V, TA=-40..85 C, IO=0 used for the 5 V state (no 5 V typical in the bundle); all of it enters VCC pin 14 and leaves GND pin 7; switching current omitted.'
OPA_RULE='Quiescent current per amplifier x 4 amplifiers (unused channels biased); no AGND pin, so by KCL all of it enters V+ (pin 4) and leaves V- (pin 11).'
EL_LIMIT='return_and_fault_contract.existing_EL_bounds.EL_rail_current_contract_mA'
SCENARIO_CONDITIONS={
 'normal-typ-v1':{'opa_statistic':'typical','opa_temperature_C':25,'logic_statistic':'maximum','logic_temperature_C':[-40,85],'logic_supply_V':6,'project_logic_supply_V':5},
 'normal-max-25c-v1':{'opa_statistic':'maximum','opa_temperature_C':25,'logic_statistic':'maximum','logic_temperature_C':[-40,85],'logic_supply_V':6,'project_logic_supply_V':5},
 'normal-max-v1':{'opa_statistic':'maximum','opa_temperature_C':[-40,125],'logic_statistic':'maximum','logic_temperature_C':[-40,85],'logic_supply_V':6,'project_logic_supply_V':5}}
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
 """Per-package current (A) from the exact owner fact; source and application remain distinct."""
 fid,amps,keys,prov=FACTS[symbol];path=bundle_of(inv,symbol);owner=path.rsplit('/',1)[0]
 facts={f['fact_id']:f for f in inp.json(path)['facts']};f=facts[fid]
 records=inp.json(owner+'/manifest.json')['records'];record=next(r for r in records if r['record_id']==f['record_id'])
 line=next(l for l in inv['lines'] if l['owner_skill']==owner[len(SKILLS):] and l['mpn']==record['mpn'])
 need(record['manufacturer']==line['manufacturer']=='Texas Instruments' and record['mpn']==symbol and record['lcsc']==line['lcsc'] and record['package']==line['package'],'exact supply identity '+symbol)
 need(fid in record['fact_ids'] and f['source_id'] in record['source_ids'],'fact ownership '+fid)
 source=next(x for x in inp.json(owner+'/sources.json')['sources'] if x['source_id']==f['source_id'])
 need(source['record_id']==record['record_id'] and source['availability']=='AVAILABLE' and source['authority_class']=='MANUFACTURER_PRIMARY','unsupported source '+fid)
 need(re.fullmatch('[0-9a-f]{64}',source['sha256']) and source['sha256']!='0'*64,'source hash '+fid)
 need(f['verdict']=='PASS - primary-source confirmed' and f['provenance']=='PRIMARY-SPEC','unsupported fact '+fid)
 need(f['unit'] in UNIT,'unit '+f['unit'])
 if amps>1:need('OUT D' in next(v['value'] for k,v in facts.items() if k.endswith('-pinout')),'quad pinout')
 pin_map=next(pm for pm in inp.json(owner+'/pin-map.json')['pin_maps'] if pm['record_id']==record['record_id'])
 supply_names={'V+':'+12V','V-':'-12V'} if amps>1 else {'VCC':'+5V','GND':'AGND'}
 supply_pins={pin['footprint_pad']:supply_names[pin['name']] for pin in pin_map['pins'] if pin['name'] in supply_names}
 need(supply_pins==({'4':'+12V','11':'-12V'} if amps>1 else {'14':'+5V','7':'AGND'}),'owner supply/return pin map '+symbol)
 v=f['value'][keys[scen]] if keys[scen] else f['value'];need(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0,'current value '+fid)
 return rnd(v*UNIT[f['unit']]*amps),{'source':f'{path}#{fid}'+(f'.{keys[scen]}' if keys[scen] else ''),'condition':f['conditions'],'locator':f['locator'],
  'derivation':f'{v} {f["unit"]}'+(f' x {amps} amplifiers' if amps>1 else ' per package'),'provenance':prov,'rule':OPA_RULE if amps>1 else LOGIC_RULE,
  'evidence':{'manufacturer':record['manufacturer'],'mpn':record['mpn'],'package':record['package'],'lcsc':record['lcsc'],
   'record_id':record['record_id'],'fact_id':fid,'value_key':keys[scen],'fact_class':f['class'],'fact_provenance':f['provenance'],'verdict':f['verdict'],
   'fact_conditions':f['conditions'],'fact_locator':f['locator'],'source_id':source['source_id'],'source_sha256':source['sha256'],
   'source_authority':source['authority_class'],'source_availability':source['availability'],
   'application_condition_status':'CONDITIONAL: source voltage is 6 V; project voltage is 5 V' if amps==1 else 'CONDITIONAL: supply voltage not explicit in the quiescent fact; applied at +/-12 V',
   'current_scope':'quiescent only; output/signal/dynamic load omitted','package_multiplier':amps,'supply_pin_map':supply_pins}}
def unmapped_reason(inp,inv,symbol):
 path=bundle_of(inv,symbol);facts=inp.json(path)['facts']
 lim=[f['fact_id'] for f in facts if f['fact_id'].endswith('electrical-limits')]
 return f'No signed supply/quiescent-current and complete return fact in owner bundle {path}'+(f' ({lim[0]} not promoted)' if lim else '')+'.'
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
  need(all(ref not in dnp and parts[ref]['dnp']!='True' for ref in fit),'fitted supply census includes a DNP device')
  el=defaultdict(list)
  for sc in SCENARIOS:
   for p in ports[b]:
    ref,pad,net,pid=p['ref'],p['pad'],p['net'],p['id'];need(net in NETS,'rail pad census');m=mand[pid];need(m['board']==b,'review board')
    row=dict(scenario_id=sc,board=b,ref=ref,pad=pad,pad_id=pid,net=net,current_A=None,units='A',operating_condition=SCENARIOS[sc],physical_owner=None,source=None,
     provenance='no_amount',supply_evidence=None,mapping_status=None,pad_class=None,structurally_unresolved=pid in unresolved[b],direct_load_member=m['source_direct_load_member'],note=None)
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
       v,meta=values[(sym,sc)];need(meta['evidence']['supply_pin_map'].get(pad)==net,'source-backed supply pad identity');sign=-1 if net in('-12V','AGND') else 1
       need((sym.startswith('OPA') and net in('+12V','-12V')) or (sym.startswith('SN74') and net in('+5V','AGND')),'supply pin role')
       row.update(current_A=rnd(sign*v),source=meta['source'],provenance=meta['provenance'],supply_evidence=dict(meta['evidence'],signed_pin_role='draw' if sign>0 else 'return',sign=sign,derivation=meta['derivation'],kcl_rule=meta['rule']),mapping_status='supported' if meta['provenance']=='supported_pin_current' else 'conditional',
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
     provenance='external_interface_demand',source=POWER+'contract.json#'+(EL_LIMIT if net in RAILS else 'return_and_fault_contract.existing_EL_bounds.EL_return_sum_bound_mA'),
     demand_kind='rail_contract_ceiling' if net in RAILS else 'unsigned_return_bound',
     maximum_absolute_current_A=rnd(lim[net]/1000) if net in RAILS else rnd(contract['return_and_fault_contract']['existing_EL_bounds']['EL_return_sum_bound_mA']/1000),
     signed_return_status='UNSUPPORTED',per_pad_split_status='UNSUPPORTED',eligible_for_device_solve=False,physical_owner={'interface':'EL-E1..EL-E6','module':'EL'},
     operating_condition='Contract ceiling for the whole EL board, not a typical value; split across parallel harness pads solved later.' if net in RAILS else
      'EL AGND return not booked: signed EL +/-12 V split unsupported, so its return cannot be derived without invented values.'))
  for f in two['boards'][b]['fitted_ic_supply_pins']:
   sym=f['symbol'];hops=[h for pin in f['supply_pins'] for h in mediated.get((f['ref'],pin),[])]
   if sym in FACTS:st,why=('mapped','Quiescent supply current at IO=0; output/signal current omitted.') if FACTS[sym][3]=='supported_pin_current' else ('partially_mapped',LOGIC_RULE)
   else:st,why='unmapped',reasons[sym]
   census_ic[f['ref']]=dict(board=b,ref=f['ref'],instance=f['instance'],symbol=sym,status=st,reason=why,mediated_supply=hops,supply_pins=f['supply_pins'])
 rows.sort(key=lambda r:(r['scenario_id'],r['board'],r['net'],r['ref'] or '',r['pad'] or '',r['pad_id']))
 groups.sort(key=lambda g:(g['scenario_id'],g['board'],g['id']))
 allowances,recon=reconcile_build(two,contract,rows,groups)
 ledger=dict(status='CONDITIONAL_LOAD_SCENARIO',sign_convention='current_A > 0: from copper INTO the device pin (draw); < 0: device injects into that copper; null: no amount booked (support or unmapped).',
  scenarios=SCENARIOS,scenario_conditions=SCENARIO_CONDITIONS,records=rows,interface_demands=groups,allowances=allowances)
 ledger['ledger_sha256']=hashlib.sha256(canon({k:ledger[k] for k in ('records','interface_demands','allowances')}).encode()).hexdigest()
 ledger.update(census=census(rows,ports,census_ic),reconciliation=recon,kcl=kcl(rows),double_count_issues=double_counts(ledger),
  omissions=omissions(rows,census_ic),full_scope_budget_acceptance=False,
  acceptance_blockers=['Most fitted IC supply currents unmapped (no bundle-backed value); their planning share stays a pad-less allowance.',
   'Resistive, diode/transistor/LED, rail-tied pin and passive/active-mediated supply currents unsupported.',
   'EL demand is a contract ceiling with no per-pad split and no signed AGND return.',
   'Planning worksheet is whole-module responsibility across K/JL/JR/P/EL, not allocated core-pad current.',
   'Some current-carrying pads are structurally unresolved (feed-disconnected) in the t2 graph.'],
  input_sha256=dict(sorted(inp.sha.items())),method_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
 ledger['device_service']={sc:device_service(ledger,sc,{r['pad_id'] for r in rows if r['scenario_id']==sc and not r['structurally_unresolved']}) for sc in SCENARIOS}
 ledger['external_boundaries']=external_boundaries(inp,harness,ledger)
 ledger['input_sha256']=dict(sorted(inp.sha.items()))
 return ledger
def device_service(ledger,scenario_id,served_pad_ids):
 """Admit whole ICs only, using the caller's complete all-board/all-net coverage.

 The supplied pad set must include finite support and a path to the declared feed.
 It is not inferred from one board/net: a missing rail or return excludes every
 current row of the IC. Evidence mapping, connectivity and scenario eligibility
 are separate results. Historical ledgers without the complete supply-pin census
 cannot opt in to the correction by silently falling back to individual pad loads.
 """
 need(served_pad_ids is not None,'device service requires explicit all-net served pads')
 need(scenario_id in ledger['scenarios'],'unknown service scenario '+scenario_id)
 rows=[r for r in ledger['records'] if r['scenario_id']==scenario_id]
 served=set(served_pad_ids);known={r['pad_id'] for r in rows}
 need(served<=known,'device service coverage contains unknown pads')
 by_pin=defaultdict(list)
 for row in rows:by_pin[(row['board'],row['ref'],row['pad'])].append(row)
 devices=[];eligible=set();included=[]
 for ic in ledger['census']['fitted_ics']['devices']:
  need('supply_pins' in ic and ic['supply_pins'],'ledger lacks required supply pins for '+ic['ref'])
  required=[];issues=[];currents=[]
  for pin,net in sorted(ic['supply_pins'].items()):
   candidates=by_pin[(ic['board'],ic['ref'],pin)]
   row=candidates[0] if len(candidates)==1 else None
   pad_id=row['pad_id'] if row else None
   mapped=row is not None and row['net']==net and row['pad_class']=='ic_supply_pin' and row['current_A'] is not None and row['provenance'] in ('supported_pin_current','conditional_assumption')
   if mapped:
    current=row['current_A'];sign=-1 if net in ('-12V','AGND') else 1
    mapped=isinstance(current,(int,float)) and not isinstance(current,bool) and math.isfinite(current) and sign*current>=0
   if not mapped:issues.append('missing, duplicate, unsupported or invalid signed supply row: '+pin+' '+net)
   else:currents.append(row)
   required.append({'pin':pin,'net':net,'pad_id':pad_id,'served':pad_id in served if pad_id else False,'current_mapped':mapped})
  count=sum(p['served'] for p in required)
  connectivity='complete' if count==len(required) else 'partial' if count else 'unserved'
  residual=math.fsum(r['current_A'] for r in currents) if len(currents)==len(required) else None
  if residual is not None and abs(residual)>TOL:issues.append('device signed supply/return KCL does not close')
  # Any extra nonzero row on the package is outside the supported quiescent model.
  pins=set(ic['supply_pins'])
  extras=[r for r in rows if r['board']==ic['board'] and r['ref']==ic['ref'] and r['pad'] not in pins and r['current_A'] not in (None,0,0.)]
  if extras:issues.append('non-supply package current outside this quiescent model')
  evidence='unmapped' if issues else 'conditional' if any(r['provenance']=='conditional_assumption' for r in currents) else 'supported'
  status='unmapped' if issues else 'supported' if connectivity=='complete' else connectivity
  admitted=status=='supported'
  if admitted:
   eligible.update(r['pad_id'] for r in currents);included.extend(currents)
  devices.append({'board':ic['board'],'ref':ic['ref'],'symbol':ic['symbol'],'required_pins':required,
   'evidence_status':evidence,'connectivity_status':connectivity,'service_status':status,'eligible_for_solve':admitted,
   'signed_package_residual_A':rnd(residual),'reasons':issues if issues else [] if admitted else ['At least one required supply/return pin has no finite path to its feed; no package current is injected.']})
 by_net={b:{net:rnd(math.fsum(r['current_A'] for r in included if r['board']==b and r['net']==net)) for net in NETS} for b in BOARDS}
 nonzero={r['pad_id'] for r in rows if r['current_A'] not in (None,0,0.) and r['provenance'] in ('supported_pin_current','conditional_assumption')}
 return {'scenario_id':scenario_id,'scope':'Complete declared supply/return service for the quiescent scenario only; output, signal, dynamic and external-interface currents omitted.',
  'devices':devices,'summary':{s:sum(d['service_status']==s for d in devices) for s in ('supported','partial','unserved','unmapped')},
  'eligible_pad_ids':sorted(eligible),'excluded_pad_ids':sorted(nonzero-eligible),'served_pad_ids':sorted(served),
  'included_board_net_sum_A':by_net,'included_global_residual_A':rnd(math.fsum(r['current_A'] for r in included))}
def external_boundaries(inp,harness,ledger):
 """Name every GH AGND conductor without inventing a load or an equal-current split."""
 budget=inp.json(POWER+'joined/budget.json');limit=budget['limits']['GH_A']
 first=next(iter(ledger['scenarios']));pads={(r['board'],r['ref'],r['pad']):r for r in ledger['records'] if r['scenario_id']==first and r['ref']}
 conductors=[]
 # The K-only harness contract omits four JL-P returns. The joined interface
 # ledger owns all inherited conductors, including these external-only paths.
 interfaces=inp.json(POWER+'joined/interfaces.json')['two']
 for conductor in interfaces['legacy_conductors']:
  if conductor['net']!='AGND':continue
  core=[]
  for end in conductor['ends']:
   if end['board'] not in BOARDS:continue
   row=pads.get((end['board'],end['ref'],end['pin']));need(row is not None and row['net']=='AGND','GH return has no core ledger pad')
   core.append({'board':row['board'],'pad_id':row['pad_id'],'structurally_unresolved':row['structurally_unresolved']})
  conductors.append({'id':conductor['id'],'net':'AGND','source_boards':[end['board'] for end in conductor['ends']],
   'source':POWER+'joined/interfaces.json#two.legacy_conductors','core_pads':core,'current_A':None,'current_operator_status':'UNSUPPORTED',
   'limit_A':limit,'limit_source':POWER+'joined/budget.json#limits.GH_A',
   'compliance_status':'NOT EVALUATED','reason':'Signed external return demand, its split and a complete conductor current operator are unsupported; no zero or equal-sharing assumption.'})
 return {'GH':{'compliance_status':'NOT EVALUATED','limit_A':limit,'limit_source':POWER+'joined/budget.json#limits.GH_A',
   'conductors':conductors,'total_conductors':len(conductors),'core_conductors':sum(bool(c['core_pads']) for c in conductors),
   'scope':'All inherited GH AGND conductors, including those without a KA/KB end. Patch sleeves are not substituted as power returns.'},
  'EL':{'demand_status':'CONTRACT CEILINGS ONLY','signed_return_status':'UNSUPPORTED','per_pad_split_status':'UNSUPPORTED',
   'return_absolute_bound_A':inp.json(POWER+'contract.json')['return_and_fault_contract']['existing_EL_bounds']['EL_return_sum_bound_mA']/1000,
   'source':POWER+'contract.json#return_and_fault_contract.existing_EL_bounds','injected_in_device_service':False}}

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
