"""A01 explicit interface source and conditional pad-path allocations; no native CAD."""
import argparse,hashlib,json,math
from collections import defaultdict
from pathlib import Path
import assembly as a
import stage10_inventory as inventory
ROOT=a.ROOT;OUT=a.OUT/'stage10'
N='/A01/'
SIGNALS=['REF5','REFN5','IN_BUFFER','OFFSET_BUFFER','SUM_NEG','IN_REMOTE','Cc045d2_W','C38cac0_W']
PINMAP={
 'J-SIG':dict(zip(map(str,range(1,8)),[N+'REF5','AGND',N+'REFN5',N+'IN_BUFFER',N+'OFFSET_BUFFER',N+'SUM_NEG','AGND'])),
 'C-SIG':dict(zip(map(str,range(1,7)),[N+'REF5',N+'REFN5',N+'IN_REMOTE',N+'Cc045d2_W',N+'C38cac0_W','AGND'])),
 'J-PWR':{'1':'+12V','2':'-12V','3':'+5V','4':'AGND'},
 'K-PWR':{'1':'+12V','2':'-12V','3':'AGND'}}
FOOTPRINTS={7:'footprints/kicad/zudo-osc-hole-field.pretty/JST_GH7_BM_TopEntry.kicad_mod',3:'footprints/kicad/zudo-osc-hole-field.pretty/JST_GH3_BM_TopEntry.kicad_mod',4:'design/architecture-278/implementation/stage7/footprints/JST_GH4_BM_TopEntry_Candidate.kicad_mod',6:'design/architecture-278/implementation/stage10/footprints/JST_GH6_BM_TopEntry_Candidate.kicad_mod'}
DINMAP={f'{row}{i}':None for row in 'abc'for i in range(1,33)}
DINMAP.update({f'c{i}':N+n for i,n in enumerate(SIGNALS,1)});DINMAP.update({f'b{i}':'AGND'for i in range(1,9)})
def need(ok,msg):
 if not ok:raise ValueError(msg)
def transport_geometry(spec):
 """Mechanical author supplies eight poses; no reads of final mechanical report."""
 headers={};need({l['id']for l in spec['links']}==set(PINMAP)and len(spec['links'])==4,'four A01 harnesses')
 for link in spec['links']:
  need(link['pins']==PINMAP[link['id']],'exact A01 harness pinmap')
  n=len(link['pins']);path=FOOTPRINTS[n];pads=a.c.footprint_pads(path)
  need(set(pads)==set(link['pins'])|{'MP1','MP2'},'complete GH footprint')
  shape={'ref':'','owner':'added-transport','box':a.c.courtyard(path),'pads':pads,'pins':dict(link['pins'],MP1=None,MP2=None),'holes':[],'source':path,'units':[]}
  for end in ('local','middle'):
   pose=link[end];ref=f"A01:{link['id']}:{end}";shape['ref']=ref
   need(pose['quarter_turn']in range(4)and pose['side']in ('panel','rear')and all(math.isfinite(v)for v in pose['origin_mm']+[pose['pad_depth_mm']]),'finite header pose')
   q=a.located(a.face_shape(shape,pose['side']),pose['origin_mm'],pose['quarter_turn'],pose['board'],pose['side'])
   q.update({'link':link['id'],'end':end,'pad_depth_mm':pose['pad_depth_mm'],'pads_xyz_mm':{p:[xy+[pose['pad_depth_mm']]for xy in pts]for p,pts in q['pads_mm'].items()},'header_mpn':f'BM{n:02}B-GHS-TBT(LF)(SN)','housing_mpn':f'GHR-{n:02}V-S','contact_mpn':'SSHL-002T-P0.2','positions':n,'native_validated':False})
   headers[ref]=q
 return headers

def evidence():
 conn=json.loads((ROOT/'design/connectors/jst-gh.json').read_text());pdf=ROOT/conn['source']['path']
 need(hashlib.sha256(pdf.read_bytes()).hexdigest()==conn['source']['sha256'],'retained JST primary hash')
 for n,path in FOOTPRINTS.items():
  span=(n-1)*1.25;pads=a.c.footprint_pads(path)
  expected={str(i):[[span/2-(i-1)*1.25,0]]for i in range(1,n+1)}|{'MP1':[[-span/2-1.85,3.35]],'MP2':[[span/2+1.85,3.35]]}
  need(pads==expected,'drawing-derived GH pad positions')
  need(a.c.courtyard(path)==[-span/2-2.6,-1.1,span/2+2.6,5],'GH courtyard allocation')
  for node in a.c.sexpr((ROOT/path).read_text()):
   if isinstance(node,list)and node and node[0]=='pad':need(node[2:4]==['smd','rect']and list(map(float,a.c.field(node,'size')))==([1,2.8]if node[1].startswith('MP')else[.6,1.7]),'GH source land dimensions')
 return {'primary_source':conn['source'],'GH6_new_candidate':{'header':'BM06B-GHS-TBT(LF)(SN)','housing':'GHR-06V-S','contact':'SSHL-002T-P0.2','source_locator':'Retained eGH PDF six-circuit housing/header table rows; top-entry recommended mounting surface pattern','A_mm':6.25,'header_B_mm':10.75,'housing_B_mm':8.75,'pitch_mm':1.25,'native_validated':False},'contact_limits':{'initial_mated_max_ohm':.03,'after_test_mated_max_ohm':.05,'current_A':1,'current_condition':'AWG26; catalog testconditions only. Actual wire/crimp/bundle/temperature and installed acceptance unknown.'}}

def trace_length(x,y):
 dx,dy=sorted((abs(x[0]-y[0]),abs(x[1]-y[1])))
 return 1.15*(dy+(math.sqrt(2)-1)*dx)+7+abs(x[2]-y[2])

def graph_report(spec,mechanical,inv):
 """Complete source endpoint coverage, explicit transport graph, unrouted allocations."""
 headers=transport_geometry(spec);packages=mechanical['placements'];din=mechanical['din_connectors']
 need(mechanical['headers']==headers,'electrical/mechanical actual GH header geometry agreement')
 need(set(packages)==set(inv['packages'])and len(packages)==90,'all90 A01 packages')
 need(set(din)=={'middle','rear'},'DIN pair inventory')
 for ref,p in packages.items():
  q=inv['packages'][ref];need(p['pins']==q['pins']and sorted(p['units'])==sorted(q['units']),'source physical pin/unit parity '+ref)
  need(set(p['pads_xyz_mm'])==set(p['pins']),'all actual source pad positions '+ref)
  need(p['owner']==q['owner'],'source package ownership '+ref)
 for end,h in din.items():need(set(h['pads_xyz_mm'])==set(DINMAP)and h['pins']==DINMAP and all(len(v)==1 for v in h['pads_xyz_mm'].values()),'complete96 DIN physical pin/net/pad identity '+end)
 nodes={};edges=[];sources=[];nc=[]
 def addnode(key,net,xyz,kind,ref,pin):
  need(key not in nodes and len(xyz)==3 and all(math.isfinite(v)for v in xyz),'unique finite physical pad')
  nodes[key]={'id':key,'net':net,'pad_xyz_mm':xyz,'kind':kind,'ref':ref,'pin':pin}
 def edge(net,left,right,kind,length=None,wire=0,contacts=0):
  need(nodes[left]['net']==nodes[right]['net']==net,'graph net identity')
  allocation=trace_length(nodes[left]['pad_xyz_mm'],nodes[right]['pad_xyz_mm'])if length is None else length
  need(math.isfinite(allocation)and allocation>=0,'finite path allocation')
  edges.append({'net':net,'from':left,'to':right,'kind':kind,'allocated_developed_mm':allocation,'wire_cut_max_mm':wire,'mated_GH_contacts':contacts,'routed_mm':None})
 for ref,p in packages.items():
  for pin,net in p['pins'].items():
   need(len(p['pads_xyz_mm'][pin])==1,'single retained pad instance')
   key=f'{ref}:{pin}';addnode(key,net,p['pads_xyz_mm'][pin][0],'source',ref,pin)
   (nc if net is None else sources).append(key)
 for ref,h in headers.items():
  for pin,net in h['pins'].items():addnode(f'{ref}:{pin}',net,h['pads_xyz_mm'][pin][0],'GH',ref,pin)
 for end,h in din.items():
  for pin,net in DINMAP.items():addnode(f'DIN:{end}:{pin}',net,h['pads_xyz_mm'][pin][0],'DIN',h.get('ref',f'A01:DIN:{end}'),pin)
 tails=mechanical['terminal_extensions'];targetlands={r['id']:r for r in mechanical['terminal_lands']};ledlands={r['id']:r for r in mechanical['LED_wire_lands']};terminal_connections={};terminal_wires=[]
 expectedtails={f'{ref}:{pin}'for ref,p in packages.items()if p['panel_uid']and p['owner']=='front-jack'for pin,net in p['pins'].items()if net is not None}
 need(len(tails)==14 and {f"{t['ref']}:{t['pin']}"for t in tails}==expectedtails,'all14 fixed jack/LED tail endpoints')
 for t in tails:
  source=f"{t['ref']}:{t['pin']}";net=t['net'];need(nodes[source]['net']==net and nodes[source]['pad_xyz_mm']==t['source_terminal_xyz_mm'],'tail source pad/net identity')
  target=targetlands[t['target_land_id']];need(target['xyz_mm']==t['to_xyz_mm']and target['net']==net and (target['ref'],target['pin'])==(t['ref'],t['pin']),'tail target land identity')
  dest='TAIL:'+t['target_land_id'];addnode(dest,net,t['to_xyz_mm'],'terminal_land',t['ref'],t['pin'])
  start=source
  if t['from_LED_land_id']:
   land=ledlands[t['from_LED_land_id']];need(land['xyz_mm']==t['from_xyz_mm']and land['net']==net and (land['ref'],land['pin'])==(t['ref'],t['pin']),'LED wire land identity')
   start='TAIL:'+t['from_LED_land_id'];addnode(start,net,t['from_xyz_mm'],'LED_wire_land',t['ref'],t['pin'])
   local=sum(abs(x-y)for x,y in zip(t['from_xyz_mm'],t['source_terminal_xyz_mm']));need(math.isclose(local,t['local_terminal_copper_mm'],abs_tol=1e-9),'LED local copper/barrel allocation')
   edge(net,source,start,'LED_local_copper',local)
  else:need(t['from_xyz_mm']==t['source_terminal_xyz_mm']and t['local_terminal_copper_mm']==0,'direct tail datum')
  nominal,tol=t['wire_nominal_mm'],t['wire_tolerance_mm'];need(all(math.isfinite(v)and v>=0 for v in (nominal,tol))and nominal>tol,'tail cut values')
  slack=nominal-tol-math.dist(t['from_xyz_mm'],t['to_xyz_mm']);need(slack>=10,'tail endpoint slack')
  edge(net,start,dest,'permanent_terminal_wire',nominal+tol,nominal+tol)
  terminal_connections[source]=dest;terminal_wires.append({**t,'maximum_cut_mm':nominal+tol,'minimum_straight_proxy_slack_mm':slack,'wire_end_terminations':2,'mated_contacts':0,'scope':'Factory termination proposal; source terminal datum, actual wire/strain process and routing unqualified'})
 wires=[]
 for link in spec['links']:
  nominal=link['wire_cut_nominal_mm'];tol=link['wire_cut_tolerance_mm'];need(all(math.isfinite(v)and v>=0 for v in (nominal,tol))and nominal>tol,'wire cut values')
  for pin,net in link['pins'].items():
   left=f"A01:{link['id']}:local:{pin}";right=f"A01:{link['id']}:middle:{pin}"
   x,y=nodes[left]['pad_xyz_mm'],nodes[right]['pad_xyz_mm'];cases=[]
   for localmove in (0,15):
    for midmove in (0,15):
     xx=x[:2]+[x[2]+localmove];yy=y[:2]+[y[2]-midmove];cases.append(math.dist(xx,yy))
   slack=nominal-tol-max(cases);need(slack>=10,'GH service pad-proxy slack')
   wires.append({'link':link['id'],'pin':pin,'net':net,'from':left,'to':right,'wire_nominal_mm':nominal,'wire_tolerance_mm':tol,'wire_max_mm':nominal+tol,'service_pad_distances_mm':cases,'minimum_proxy_slack_mm':slack})
   edge(net,left,right,'GH_harness',nominal+tol+15,nominal+tol,2)
 for i,n in enumerate(SIGNALS,1):edge(N+n,f'DIN:middle:c{i}',f'DIN:rear:c{i}','DIN_mated_pair',25)
 for i in range(1,9):edge('AGND',f'DIN:middle:b{i}',f'DIN:rear:b{i}','DIN_mated_pair',25)
 for link in spec['links']:
  if not link['id'].endswith('SIG'):continue
  for pin,net in link['pins'].items():
   if net=='AGND':continue
   i=SIGNALS.index(net[len(N):])+1;edge(net,f"A01:{link['id']}:middle:{pin}",f'DIN:middle:c{i}','middle_copper')
 # Actual middle power handoff anchors; upstream POWER circuitry is not hosted here.
 for net,jpin,kpin in [('+12V','1','1'),('-12V','2','2')]:edge(net,f'A01:J-PWR:middle:{jpin}',f'A01:K-PWR:middle:{kpin}','middle_power_copper')
 groundstar='A01:J-PWR:middle:4'
 for key,node in list(nodes.items()):
  if node['net']=='AGND'and (key.startswith('DIN:middle:')or (node['kind']=='GH'and ':middle:'in key))and key!=groundstar:edge('AGND',groundstar,key,'middle_AGND_copper')
 # All local endpoints, including every power/return pad and whole-package spare, are inventoried.
 groups=defaultdict(list)
 for key in sources:groups[packages[nodes[key]['ref']]['owner'],nodes[key]['net']].append(key)
 local_groups=[]
 for (owner,net),keys in sorted(groups.items()):
  if net in (N+n for n in SIGNALS):
   if owner=='rear-core':transport=f'DIN:rear:c{SIGNALS.index(net[len(N):])+1}'
   else:
    link='J-SIG'if owner=='front-jack'else'C-SIG';pins=[p for p,n in PINMAP[link].items()if n==net];need(len(pins)==1,'crossing owner/net mapping');transport=f'A01:{link}:local:{pins[0]}'
   driver=':'.join(DRIVERS[net[len(N):]])
   anchor=driver if driver in keys else keys[0]
   edge(net,anchor,transport,'local_transport_branch')
  elif net in ('+12V','-12V','+5V','AGND'):
   link={'rear-core':'K-PWR','front-jack':'J-PWR','front-control':'C-SIG'}[owner];pins=[p for p,n in PINMAP[link].items()if n==net];need(len(pins)==1,'power/return source board mapping');anchor=f'A01:{link}:local:{pins[0]}'
  else:anchor=terminal_connections.get(keys[0],keys[0])
  for key in keys:
   endpoint=terminal_connections.get(key,key)
   if endpoint!=anchor:edge(net,anchor,endpoint,'local_source_copper')
  local_groups.append({'owner':owner,'net':net,'anchor':anchor,'source_endpoints':keys,'status':'Unrouted local connectivity allocation; sensitive loop obstacles/parasitics unqualified'})
 # Additional signal-return contacts join the same board AGND; no isolated ground fiction.
 for pin in ('2','7'):edge('AGND','A01:J-PWR:local:4',f'A01:J-SIG:local:{pin}','local_return_join')
 for i in range(1,9):edge('AGND','A01:K-PWR:local:3',f'DIN:rear:b{i}','local_return_join')
 need(len(wires)==20 and len(sources)+len(nc)==285,'physical wire/source endpoint conservation')
 return {'headers':headers,'DIN_pinmap':DINMAP,'nodes':nodes,'edges':edges,'wires':wires,'terminal_wires':terminal_wires,'source_endpoints':sources,'NC_source_endpoints':nc,'local_net_groups':local_groups,'upstream_power_boundaries':{n:f'A01:J-PWR:middle:{p}'for p,n in PINMAP['J-PWR'].items()},'source_evidence':evidence()}

DRIVERS={'REF5':('U7104','1'),'REFN5':('U7104','7'),'IN_BUFFER':('U7106','1'),'OFFSET_BUFFER':('U7106','7'),'SUM_NEG':('U7105','8'),'IN_REMOTE':('R7113','2'),'Cc045d2_W':('RV1307','2'),'C38cac0_W':('RV1308','2')}
def path_edges(graph,start,end):
 adjacent=defaultdict(list)
 for i,e in enumerate(graph['edges']):adjacent[e['from']].append((e['to'],i));adjacent[e['to']].append((e['from'],i))
 queue=[start];prior={start:None}
 for node in queue:
  if node==end:break
  for other,index in adjacent[node]:
   if other not in prior:prior[other]=(node,index);queue.append(other)
 need(end in prior,'disconnected endpoint '+end);result=[];node=end
 while node!=start:node,index=prior[node];result.append(index)
 return list(reversed(result))

def conditional_budgets(inv,graph):
 facts={}
 for name in ('ti-ref5050aidr','ti-opa4197ipwr','ti-opa4196idr','ti-lm393bidr'):
  f=json.loads((ROOT/f'.claude/skills/component-{name}/facts.json').read_text())['facts']
  facts[name]=[x for x in f if any(t in x['fact_id']for t in ('electrical-limits','quiescent-current','input-bias-current','input-offset-voltage'))]
 def source(ref,value,pins):
  p=inv['packages'][ref];need(len(p['unit_records'])==1 and p['unit_records'][0]['value']==value and p['pins']==pins,'analytical source branch changed '+ref)
 source('R7101','10000 Ω',{'1':N+'REF5','2':N+'C534b2a_INV'});source('R7102','10000 Ω',{'1':N+'REFN5','2':N+'C534b2a_INV'})
 source('R7103','22000 Ω',{'1':N+'REF5','2':N+'C534b2a_GATE_RAW'});source('R7104','100000 Ω',{'1':N+'C534b2a_GATE_RAW','2':'AGND'})
 source('RV1308','PTV09A-4020F-B104',{'1':N+'REFN5','2':N+'C38cac0_W','3':N+'REF5','4':None,'5':None})
 cap=[]
 for signal in SIGNALS:
  net=N+signal;wires=[w for w in graph['wires']if w['net']==net];length=sum(w['wire_max_mm']for w in wires)
  cap.append({'net':net,'physical_harness_branches':len(wires),'aggregate_wire_cut_max_mm':length,'wire_only_pF_at_proposed_100pF_per_m':length*.1,'actual_density_pF_per_m':None,'total_assembled_capacitance_pF':None,'required_limit_pF':1000,'scope':'All physical branches counted once; connector,PCB,input,mutual capacitance and actual wire unknown.100pF/m is sensitivity input, not manufacturer bound or acceptance.'})
 return {'primary_facts':facts,'reference_fanout':{'REF5_endpoints':[n for n in inv['net_endpoints'][N+'REF5']],'REFN5_endpoints':[n for n in inv['net_endpoints'][N+'REFN5']],
  'nominal_unloaded_REF5_source_A':5/10000+5/122000+10/100000,'nominal_unloaded_REFN5_sink_A':5/10000+10/100000,'assumptions':'Ideal±5V references,invertingampvirtualground,noinputbias,unloaded100kpot. Wiper10M/1k loading and comparator/opampbias add position/condition-dependent terms. These are subtotals, not2mA guarantees or referencequalification. REF5050 exact electrical limits remain unpromoted.'},
  'quiescent_rail_only':{'K_OPA4197_8sections_A':.012,'JR_OPA4197_4sections_A':.006,'JR_OPA4196_4sections_A':.001,'scope':'Conditioned full-temperature IO=0 maximum; does not automatically enter AGND. REF5050,LM393B,ADG5412F,reference/output/LED loads and fault/dynamic terms remain incomplete.'},
  'GH_power_return_contract':{'two_mated_contacts_initial_max_ohm':.06,'two_mated_contacts_after_test_max_ohm':.1,'retained_return_target_ohm':.0005,'retained_rail_target_ohm':.001,'retained_GH_contact_current_limit_A':.5,'retained_hot_distribution_limit_V':.020,'retained_full_path_loss_limit_V':.20,'initial_bound_to_return_target_ratio':120,'after_test_bound_to_return_target_ratio':200,'initial_bound_to_rail_target_ratio':60,'after_test_bound_to_rail_target_ratio':100,'result':'Available GH contact evidence does not establish compliance; source maxima exceed retainedtargets before wire/crimp/copper. Not a measuredminimum resistance or proofeveryactualcontactfails. No lowRstrap selected. POWER source/hosting remains outside scope.','drops_V_at_aftertest_bound':{str(i):i*.1 for i in (.001,.01,.1)},'sharing':'No equal current sharing/cancellation credited across J-SIG twoAGND contacts or eightDINreturns.'},
  'aggregate_crossing_capacitance':cap,'loaded_transfer_and_stability':'UNKNOWN; sourceallocation and macromodelavailability do not qualify assembled loops. 300mm applies retained cable/harness obligation; complete developedpadpath reported separately, not silently substituted.',
  'missing':['selectedwire resistance/capacitance/OD/crimpdetails','acceptedfrontfixedterminal wire/strain construction andalllocalrouting/returnplanes','DINcontact/railreturnimpedance andparasitics','externalpatchloads/protectionfaultreturns','completeDCaccuracy,clipheadroom,selectorpotloading andassembledfrequency/stability behavior']}

def analyze(spec,mechanical,inv):
 graph=graph_report(spec,mechanical,inv);paths=[]
 crossing={n for n in inv['crossing_nets']if n not in ('AGND','+12V','-12V','+5V')};need(crossing=={N+n for n in SIGNALS},'all eight crossing signals')
 for name,(ref,pin)in DRIVERS.items():
  net=N+name;start=f'{ref}:{pin}';need(graph['nodes'][start]['net']==net,'source drive boundary pin/net')
  expected={f"{r['ref']}:{r['pin']}"for r in inv['net_endpoints'][net]}
  actual={k for k in graph['source_endpoints']if graph['nodes'][k]['net']==net};need(expected==actual,'full net endpoint parity')
  for end in sorted(actual-{start}):
   indices=path_edges(graph,start,end);edges=[graph['edges'][i]for i in indices]
   paths.append({'net':net,'from':start,'to':end,'edge_indices':indices,'harness_wire_cut_max_mm':sum(e['wire_cut_max_mm']for e in edges),'complete_net_pad_path_allocation_mm':sum(e['allocated_developed_mm']for e in edges),'GH_mated_contacts':sum(e['mated_GH_contacts']for e in edges),'DIN_mated_contacts':sum(e['kind']=='DIN_mated_pair'for e in edges),'routed_mm':None,'scope':'Complete assigned physical net-pad path allocation, not whole transfer function or routed copper'})
 # Reachability includes every actual rail/return endpoint, including bypasses and unused units.
 power=[]
 for net,start in graph['upstream_power_boundaries'].items():
  for end in graph['source_endpoints']:
   if graph['nodes'][end]['net']!=net:continue
   indices=path_edges(graph,start,end);edges=[graph['edges'][i]for i in indices]
   power.append({'net':net,'source_boundary':start,'to':end,'edge_indices':indices,'allocated_developed_mm':sum(e['allocated_developed_mm']for e in edges),'wire_cut_max_mm':sum(e['wire_cut_max_mm']for e in edges),'scope':'One explicit connectivity path through joinednetwork; parallel currents/actualreturnchoice unresolved; upstream source excluded'})
 localpaths=[]
 for group in graph['local_net_groups']:
  for target in group['source_endpoints']:
   indices=path_edges(graph,group['anchor'],target);edges=[graph['edges'][i]for i in indices]
   localpaths.append({'net':group['net'],'owner':group['owner'],'from':group['anchor'],'to':target,'edge_indices':indices,'complete_net_pad_path_allocation_mm':sum(e['allocated_developed_mm']for e in edges),'all_wire_cut_max_mm':sum(e['wire_cut_max_mm']for e in edges),'scope':'Local connectivity allocation includes fixed tail/LED legs where applicable; notfulltransfer orrouting'})
 counts={'source_packages':90,'source_units':118,'source_pins_including_NC':285,'bypasses':17,'fixed_devices':9,'physical_GH_harnesses':4,'physical_wires':34,'GH_harness_wires':20,'permanent_terminal_wires':14,'permanent_wire_end_terminations':28,'GH_headers':8,'GH_housings':8,'crimp_contacts':40,'GH_mated_contacts':40,'GH_signal_wires':10,'GH_AGND_wires':5,'GH_rail_wires':5,'DIN_pairs':1,'DIN_physical_mated_contacts':96,'DIN_assigned_signal_contacts':8,'DIN_assigned_AGND_contacts':8,'DIN_NC_contacts':80,'physical_mated_contacts_total':136,'GH_electrical_pin_solder_joints':40,'GH_header_MP_joints':16,'DIN_pin_solder_joints':192,'DIN_assigned_pin_solder_joints':32,'DIN_NC_pin_solder_joints':160}
 electrical={'status':'A01 CONDITIONAL NET/PATH/RETURN SOURCE ALLOCATION; NOT ACCEPTED','counts':counts,'unselected_MPN_refs':inv['unselected_MPN_refs'],'signal_net_paths':paths,'power_and_return_endpoint_paths':power,'all_local_net_groups':graph['local_net_groups'],'local_endpoint_paths':localpaths,'terminal_wire_inventory':graph['terminal_wires'],'NC_source_endpoints':graph['NC_source_endpoints'],'bypass_associations':inv['bypass_associations'],'conditional_budgets':conditional_budgets(inv,graph),
 'driver_continuations':{'IN_REMOTE':'Net starts R7113:2 after100ohm; upstream U7104:14→R7113:1 onC8e6645_DRIVE and R7114 feedback are separate localgraph nets; 10kohm R7114 returns toU7104:13 viaFB. Not an unisolated opamp output.','wipers':'Potwiper netpaths end atR7115:1/R7119:1; respective1kohm series/inputbias/filter/receivercontinuations remain localgraph nets, not discarded source endpoints.','all_local':'Every nonNC pin appears in localnetgroups; allocations do not prove local feedback or fixedterminal wiring/obstacle routing.'},
 'allocation_model':{'copper':'1.15octileXY+5mm detour+2mm jointallocation+absZ barrel allowance pergraphsegment','GH_pair_mm':15,'DIN_pair_mm':25,'status':'Engineering allocations, not measuredinternalconductivegeometry or routing'},'mating':'GHsizes7/6/4/3distinctwithinA01. Keyedcarrier topreventcrossmoduleX1/OSCcompatiblemis-mate is proposed, actualkeyinggeometry/effectiveness UNKNOWN. Labels not claimed physicalkey.',
 'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','routing':'NOT RUN','physical':'NOT RUN'}
 graph.update({'status':'A01 PHYSICAL INTERFACE INVENTORY; SOURCE ONLY','counts':counts,'hardware_acceptance':False,'native':'NOT RUN'})
 return graph,electrical

def build():
 paths=[OUT/'interface-input.json',OUT/'mechanical-report.json',OUT/'inventory-report.json'];spec,mech,inv=[json.loads(p.read_text())for p in paths]
 for report in (mech,inv):
  need(bool(report.get('source_sha256')),'input source bindings')
  for name,digest in report['source_sha256'].items():need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'stale input '+name)
 results=analyze(spec,mech,inv)
 sources=paths+[Path(__file__),Path(__file__).with_name('test_stage10_interfaces.py'),Path(inventory.__file__),Path(a.__file__),ROOT/'design/connectors/jst-gh.json',ROOT/'design/connectors/sources/jst-gh.pdf',ROOT/'design/standard/electrical-standard.json',ROOT/'design/architecture-278/electrical.md',ROOT/'design/architecture-278/GATE.md']+[ROOT/p for p in FOOTPRINTS.values()]
 sources += [ROOT/f'.claude/skills/component-{name}/{f}.json'for name in ('ti-ref5050aidr','ti-opa4197ipwr','ti-opa4196idr','ti-lm393bidr')for f in ('facts','sources')]
 for result in results:result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sources}
 results[1]['interface_object_sha256']=hashlib.sha256((json.dumps(results[0],sort_keys=True,separators=(',',':'))+'\n').encode()).hexdigest()
 return results

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
 for name,result in zip(('interfaces','electrical'),build()):
  data=json.dumps(result,sort_keys=True,separators=(',',':'))+'\n';target=OUT/(name+'-report.json')
  if args.check:need(target.read_text()==data,'stale A01 '+name)
  else:target.write_text(data)
 print('A01 all285sourcepins/20GHwires/96DINcontacts accounted; electrical acceptance OPEN')
if __name__=='__main__':main()
