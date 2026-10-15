"""X1 source-bound physical interface budgets; no simulator or native execution."""
import argparse
import json
import math
from pathlib import Path
import stage6_hosting as hosting

ROOT=hosting.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage7'
need=hosting.need
RAILS=hosting.RAILS

def segment(p,q):
    need(len(p)>=2 and len(q)>=2,'XY pads required')
    x,y=sorted([abs(p[0]-q[0]),abs(p[1]-q[1])])
    return 1.15*(y+(math.sqrt(2)-1)*x)+7+(abs(p[2]-q[2])if len(p)==len(q)==3 else 0)

def passive_pole(resistance,capacitance):
    need(resistance>0 and capacitance>0,'positive RC required')
    return {'R_ohm':resistance,'C_F':capacitance,'tau_s':resistance*capacitance,'pole_Hz':1/(2*math.pi*resistance*capacitance)}

def source_trace():
    fs,ins=hosting.specification();inst=next(i for i in ins if i.name=='X1');family=next(f for f in fs if f.name==inst.family)
    parts={(hosting.designator(p,inst),p.unit):p for p in family.parts}
    expected={
      ('U3305',1):('OPA4197IPWR',{'1':'A_BUFFER','2':'A_BUFFER','3':'A_SENSE'}),
      ('U3305',2):('OPA4197IPWR',{'7':'B_BUFFER','6':'B_BUFFER','5':'B_SENSE'}),
      ('U3305',3):('OPA4197IPWR',{'8':'OUT_BUFFERED','9':'C61b194_FB','10':'SELECTOR_REMOTE'}),
      ('U3303',1):('OPA4197IPWR',{'1':'C33d018_DRIVE','2':'C33d018_DRIVE','3':'SELECTOR_COMMON'}),
      ('R3309',0):('2.2 kΩ',{'1':'A_BUFFER','2':'SELECT_A_CONTACT'}),
      ('R3310',0):('2.2 kΩ',{'1':'B_BUFFER','2':'SELECT_B_CONTACT'}),
      ('R3311',0):('10 MΩ',{'1':'SELECTOR_COMMON','2':'AGND'}),
      ('SW608',0):('2MS1T1B1M2QES-5',{'3':'SELECT_A_CONTACT','2':'SELECTOR_COMMON','1':'SELECT_B_CONTACT'}),
      ('R3312',0):('499 Ω',{'1':'C33d018_DRIVE','2':'C33d018_ISO_MID'}),
      ('R3313',0):('499 Ω',{'1':'C33d018_ISO_MID','2':'SELECTOR_REMOTE'}),
      ('R3314',0):('499 Ω',{'1':'OUT_BUFFERED','2':'C61b194_ISO_MID'}),
      ('R3315',0):('499 Ω',{'1':'C61b194_ISO_MID','2':'OUT_TIP'}),
      ('R3316',0):('100 Ω',{'1':'OUT_TIP','2':'C61b194_FB'}),
      ('C3301',0):('1e-09 F',{'1':'OUT_BUFFERED','2':'C61b194_FB'}),
      ('R3301',0):('100000 Ω',{'1':'Cadd797_ENABLE','2':'AGND'}),
      ('R3305',0):('100000 Ω',{'1':'C9a8343_ENABLE','2':'AGND'}),
      ('R3302',0):('1000 Ω',{'1':'+5V','2':'Cadd797_ENABLE'}),
      ('R3306',0):('1000 Ω',{'1':'+5V','2':'C9a8343_ENABLE'})}
    rows=[]
    for (ref,unit),(value,pins) in expected.items():
        p=parts[ref,unit];need(p.value==value and p.pins==pins,'X1 source topology drift '+ref)
        rows.append({'ref':ref,'unit':unit,'value':value,'pins':pins,'role':p.attributes.get('Role')})
    return rows

def conditional_budgets():
    gh=json.loads((ROOT/'design/connectors/jst-gh.json').read_text())
    need(all(x['initial_contact_resistance_max_mohm']==30 and x['after_test_contact_resistance_max_mohm']==50 and x['rated_current_A_per_contact']==1 for x in gh['sizes']),'GH family rating drift')
    standard=json.loads((ROOT/'design/standard/electrical-standard.json').read_text())
    facts=json.loads((ROOT/'.claude/skills/component-ti-opa4197ipwr/facts.json').read_text())
    fact=next(f for f in facts['facts']if f['fact_id']=='fact-op-precision-input-bias-current-full-temperature')
    need(fact['value']['maximum']==15 and fact['unit']=='nA','OPA4197 bias evidence drift')
    need(standard['remote_controls']['max_harness_length_m']==.3 and standard['remote_controls']['max_harness_capacitance_F']==1e-9,'remote envelope drift')
    from design.spec.modules.build_manual_ab_current import build as current_build
    current=current_build();x1=next(x for x in current['instances']if x['instance']=='X1');planning=x1['planning_maximum_mA_per_rail']
    total=sum(planning.values())/1000
    return {'retained_current_planning':current,'planning_contact_sensitivities':{'per_rail_full_module_through_one_branch':[{'rail':rail,'planning_A':mA/1000,'initial_two_contact_drop_V':mA/1000*.06,'after_test_two_contact_drop_V':mA/1000*.1}for rail,mA in planning.items()],
       'sum_absolute_rail_planning_A':total,'if_sum_returned_through_one_branch_initial_V':total*.06,'if_sum_returned_through_one_branch_after_test_V':total*.1,
       'scope':'Conservative arithmetic sensitivity only, not actual simultaneous AGND current. Some quiescent current closes between ±rails; LED/source polarity and branch redistribution require circuit solution. Planning allowances omit faults/transients; no guaranteed bound and no equal-sharing credit.'},'retained_OPA4197_bias_fact':fact,'standard_obligations':{'remote_controls':standard['remote_controls'],'calibration':standard['calibration'],'precision_output':next(c for c in standard['cells']if c['id']=='precision_output'),'scope':'Global remote-controls envelope applies X1 buffered internal links:300mm cable and1nF aggregate remote-net capacitance. Complete developed path is separately reported; no300mm complete-path rule inferred. Precision output externalpatch load/stability/1mV loaderror and2mV static targets retained; model-screened source claims are not new assembled results.'},'status':'CALCULATED CONDITIONAL SENSITIVITIES; NOT DEVICE/ASSEMBLY QUALIFICATION',
      'source_assertions':source_trace(),
      'A_B':{'driver':'U3305:1/7 OPA4197IPWR local unity followers; local LED input U3304:3/5 remains on jack board',
       'receiver':'R3309/10:1 then2.2k, switch, SELECTOR_COMMON10M pulldown and U3303:3',
       'warning':'Harness capacitance loads follower output BEFORE remote2.2k. Do not credit that resistor as driver isolation or model A/B as998ohm lowpass.',
       'ideal_DC_selected_gain':1e7/(1e7+2200),'selected_5V_nominal_loading_error_V':5*2200/(1e7+2200),'selected_15nA_bias_sensitivity_V':15e-9*(2200*1e7/(2200+1e7)),
       'remaining_of_2mV_static_target_after_nominal_loading_only_V':.002-5*2200/(1e7+2200),'remaining_scope':'Arithmetic remaining amount only; combined offsets, tolerances, input protection/load, switch/contact, return and output errors not yet bounded. Not a revised target or proof of remaining sufficiency.',
       'bridged_A_plus10_B_minus10_ideal_current_A':20/4400,
       'bridge_scope':'Conditional ±10V ideal sources and nominal2.2k each; not fault safety, actual output drive or switch timing qualification.',
       'driver_output_impedance_ohm':None,'assembled_stability':'UNKNOWN'},
      'SELECTOR_REMOTE':{'driver':'U3303:1 local unity feedback then R3312+R3313=998ohm nominal; receiver U3305:10 high impedance',
       'series_nominal_ohm':998,'RC_sensitivities':[passive_pole(998,c)for c in (100e-12,300e-12,1e-9)],
       'bias_15nA_conditional_drop_V':998*15e-9,
       'scope':'RC uses ideal source and lumped downstream C; C values are sensitivity inputs, not extraction or acceptance limits.15nA retained OPA4197 source-conditioned table sensitivity, not asserted actual ±12V/alltemperature bound.'},
      'output_feedback':{'scope':'U3305:8 through two499ohm to OUT_TIP,100ohm remote feedback and1nF fast feedback remain local; external load/patch cable and ADG5412F/BAT54S input protection retained. Internal interconnect is not inherently superior to protected external patching.','loaded_transfer':'UNKNOWN; exact amplifier dynamics and actual parasitics required'},
      'return_contact_sensitivity':{'basis':'JST GH retained family30mohm initial/50mohm after-test maximum per mated contact; two ends per one branch; wire/PCB/crimp additions not included',
       'per_branch_contact_only_ohm':{'initial':.06,'after_test':.1},
       'current_grid_A':[.0001,.002,.0033333333333333335,.01,.1],
       'rows':[{'current_A':i,'initial_drop_V':i*.06,'after_test_drop_V':i*.1}for i in (.0001,.002,.0033333333333333335,.01,.1)],
       'retained_return_planning_V':.0002,'contact_only_current_ceiling_A':{'initial':.0002/.06,'after_test':.0002/.1},
       'comparison':'60/100mohm exceeds inherited0.5mohm illustrative common-return resistance by120/200times. This does not establish X1 branch current or universal X1 error target; cannot credit equal sharing across four AGND wires.',
       'joint_return_current_A':None,'actual_return_shift_V':None,'status':'OPEN; close via actual branch/common currents, topology and impedance or reviewed allocation change; no silent relaxation'},
      'power':{'plus5_enable_resistor_only_A':2*5/101000,'scope':'Nominal two1k+100k enable networks only; enable input current, all amplifier quiescent currents, LED current, signal-output current and transient demand remain additional. +5V connects jack board only.',
       'JST_family_rating_A':1,'rating_condition':'AWG26 retained primary family rating; simultaneous-contact derating/temperature/crimp/assembly qualification OPEN',
       'actual_current_bound_A':None,'source_supply_path':'UNKNOWN upstream POWER placement/distribution; no fabricated source pad'},
      'capacitance':{'nets':{n:{'aggregate_pF':None,'acceptance_limit_pF':1000,'scope':'global remote_controls envelope; sum both harnesses, all four mated contacts, three boards and receiver loading; retained1nF is unvalidated design envelope, not achieved qualification'}for n in ('/X1/A_BUFFER','/X1/B_BUFFER','/X1/SELECTOR_REMOTE')},'status':'UNKNOWN; full physical conductors counted once, receiver/fanout loads separately; model1nFdrive does not imply assembled stability'},
      'characterization':{'status':'PROPOSAL NOT APPROVED; NOT RUN','stimulus':'A/B DC−10..+10V within eventual source/supply limits; selected A/B, overlap/open transition, simultaneous opposing levels;100Hz/1kHz/10kHz and edge sweeps with actual loads/loom; source limits reviewed before execution',
       'observables':['DC selected gain/offset and return shift','input/output current and headroom','loop stability, ringing and settling','switch bounce/break-before-make/lever mapping','rail droop and LED modulation coupling','actual aggregatecapacitance and full common-return impedance'],
       'comparison':'compare to captured local-feedback/resistor network and actual-source model; no arbitrary flat20kHz or imported300mm whole-X1 criterion','bounded_return_comparison':'report measured/calculated deltaAGND versus retained200uV planning sensitivity; exceeding it requires explicit allocation review, not PASS'}}

def endpoint(packages,ref,pin):
    p=packages[ref]
    pts=p.get('pads_xyz_mm',{}).get(pin)
    if pts is None:pts=[xy+[p['conditional_pcb_depth_mm']]for xy in p['pads_mm'][pin]]
    need(len(pts)==1,'ambiguous endpoint pad multiplicity')
    return {'ref':ref,'pin':pin,'net':p['pins'][pin],'board':p['board'],'pad_xyz_mm':pts[0]}

def analyze(interface,baseline):
    packages=interface['packages'];links={r['id']:r for r in interface['links']}
    need(set(links)=={'J-SIG','J-PWR','C-SIG','C-PWR'},'physical harness inventory')
    need(len(packages)==56 and sum(len(p['units'])for p in packages.values())==76,'whole X1 packages')
    ledger=json.loads((ROOT/'design/architecture-278/source-ledger.json').read_text());live,source=hosting.live_packages(ledger)
    need(set(packages)==set(live),'X1 source package set')
    for ref,p in packages.items():
        need(p['pins']==live[ref]['pins']and sorted(p['units'])==sorted(live[ref]['units']),'X1 source pin/unit mismatch '+ref)
    bypass=[]
    for ref,record in source.items():
        if record['decouples_ref']:
            target=record['decouples_ref'];need(packages[ref]['board']==packages[target]['board'],'bypass split')
            bypass.append({'capacitor':ref,'target':target,'board':packages[ref]['board'],'pins':packages[ref]['pins'],'status':'source association retained; return loop impedance UNKNOWN'})
    need(len(bypass)==10,'complete bypass inventory')
    expected={'J-SIG':['/X1/A_BUFFER','/X1/B_BUFFER','/X1/SELECTOR_REMOTE','AGND'],'C-SIG':['/X1/A_BUFFER','/X1/B_BUFFER','/X1/SELECTOR_REMOTE','AGND'],'J-PWR':['+12V',None,'-12V',None,'+5V',None,'AGND'],'C-PWR':['+12V','-12V','AGND']}
    wires={};wire_rows=[]
    for name,link in links.items():
        need(link['pins']=={str(i):n for i,n in enumerate(expected[name],1)},'wrong connector pin/net')
        need(len(link['conductors'])==sum(n is not None for n in expected[name]),'missing/duplicate conductor')
        for w in link['conductors']:
            key=(name,w['pin']);need(key not in wires and w['net']is not None and w['net']==link['pins'][w['pin']],'wire pin/net duplication')
            need(w['front_header']=='X1:'+name+':front'and w['middle_header']=='X1:'+name+':middle','wrong harness host')
            need(math.isclose(w['wire_min_mm'],w['wire_cut_nominal_mm']-w['wire_cut_tolerance_mm'])and math.isclose(w['wire_max_mm'],w['wire_cut_nominal_mm']+w['wire_cut_tolerance_mm']),'wire cut mismatch')
            for end in ('front','middle'):
                header=interface['headers'][w[end+'_header']]
                need(header['pins'][w['pin']]==w['net'] and header['pads_xyz_mm'][w['pin']]==[w[end+'_pad_xyz_mm']],'wire actual header pad/net drift')
            dist=math.dist(w['front_pad_xyz_mm'],w['middle_pad_xyz_mm']);need(math.isclose(dist,w['straight_pad_distance_mm']),'wire actual pad distance')
            need(math.isclose(w['wire_min_mm']-dist,w['minimum_remaining_slack_mm']),'wire slack mismatch')
            wires[key]=w;wire_rows.append({'link':name,'pin':w['pin'],'net':w['net'],'minimum_cut_mm':w['wire_min_mm'],'maximum_cut_mm':w['wire_max_mm'],'straight_pad_distance_mm':dist,'minimum_remaining_slack_mm':w['minimum_remaining_slack_mm'],'mated_contacts':2,'installed_wire_length_mm':None,'cable_envelope_mm':300,'maximum_cut_within_envelope':w['wire_max_mm']<=300})
    need(len(wires)==15,'physical conductor count')
    need(len(interface['headers'])==8 and sum(n is None for h in interface['headers'].values()for pin,n in h['pins'].items()if pin.isdigit())==6,'transport NC/header inventory')
    expected_boundaries={'+12V':'1','-12V':'3','+5V':'5','AGND':'7'}
    need(len(interface['middle_upstream_power_boundaries'])==4,'upstream boundary coverage')
    for b in interface['middle_upstream_power_boundaries']:
        ep=b['actual_middle_pad'];need(ep['ref']=='X1:J-PWR:middle'and ep['pin']==expected_boundaries[b['net']]and ep['pad_xyz_mm']==interface['headers'][ep['ref']]['pads_xyz_mm'][ep['pin']][0],'wrong upstream power/return pad')
    need(all(l['GH_pair_developed_allocation_mm']==15 for l in links.values()),'changed GH allowance requires review')
    trace_edges=interface['middle_trace_edges']
    required_edges={(expected['J-SIG'][i-1],'X1:J-SIG:middle',str(i),'X1:C-SIG:middle',str(i))for i in (1,2,3)}
    required_edges|={(net,'X1:J-PWR:middle',jp,'X1:C-PWR:middle',cp)for net,jp,cp in [('+12V','1','1'),('-12V','3','2')]}
    required_edges|={('AGND','X1:J-PWR:middle','7','X1:'+link+':middle',pin)for link,pin in [('J-SIG','4'),('C-SIG','4'),('C-PWR','3')]}
    actual_edges={(e['net'],e['from']['ref'],e['from']['pin'],e['to']['ref'],e['to']['pin'])for e in trace_edges}
    need(len(trace_edges)==8 and actual_edges==required_edges,'middle signal/power/return topology changed')
    for edge in trace_edges:
        for end in ('from','to'):
            ep=edge[end];h=interface['headers'][ep['ref']];need(h['pins'][ep['pin']]==edge['net']and h['pads_xyz_mm'][ep['pin']]==[ep['pad_xyz_mm']],'middle edge actual pad/net drift')
        need(math.isclose(edge['allocation_mm'],segment(edge['from']['pad_xyz_mm'],edge['to']['pad_xyz_mm'])),'middle copper mismatch')
    paths=[]
    for net,driver,receiver,upstream in [('/X1/A_BUFFER',('U3305','1'),('R3309','1'),'local U3305 follower'),('/X1/B_BUFFER',('U3305','7'),('R3310','1'),'local U3305 follower'),('/X1/SELECTOR_REMOTE',('R3313','2'),('U3305','10'),'U3303:1 then R3312/R3313; complete upstream series isolation998ohm')]:
        src=endpoint(packages,*driver);dst=endpoint(packages,*receiver);need(src['net']==dst['net']==net,'driver/receiver net mismatch')
        forward=net!='/X1/SELECTOR_REMOTE';fl,tl=('J-SIG','C-SIG')if forward else('C-SIG','J-SIG');pin=str(expected['J-SIG'].index(net)+1);fw,tw=wires[fl,pin],wires[tl,pin]
        es=[e for e in trace_edges if e['net']==net];need(len(es)==1,'signal edge coverage')
        e=es[0];need({(e[k]['ref'],e[k]['pin'])for k in ['from','to']}=={(fw['middle_header'],pin),(tw['middle_header'],pin)},'wrong middle signal contact')
        segments={'driver_board_trace_mm':segment(src['pad_xyz_mm'],fw['front_pad_xyz_mm']),'first_wire_max_mm':fw['wire_max_mm'],'first_GH_pair_mm':links[fl]['GH_pair_developed_allocation_mm'],'middle_trace_mm':e['allocation_mm'],'second_wire_max_mm':tw['wire_max_mm'],'second_GH_pair_mm':links[tl]['GH_pair_developed_allocation_mm'],'receiver_board_trace_mm':segment(tw['front_pad_xyz_mm'],dst['pad_xyz_mm'])}
        paths.append({'net':net,'driver':src,'receiver':dst,'upstream_source':upstream,'physical_wire_ids':[fl+':'+pin,tl+':'+pin],'mated_contacts':4,'segments':segments,'complete_developed_allocation_mm':sum(segments.values()),'wire_cut_max_sum_mm':fw['wire_max_mm']+tw['wire_max_mm'],'pad_separation_mm':math.dist(src['pad_xyz_mm'],dst['pad_xyz_mm']),'GH_allowance_status':'15mm per mated cable pair retained engineering allowance, not measured electrical-path dimension','length_acceptance_limit_mm':None,'complete_remote_wire_sum_envelope_mm':300,'wire_sum_within_envelope':fw['wire_max_mm']+tw['wire_max_mm']<=300,'aggregate_capacitance_envelope_pF':1000,'actual_aggregate_capacitance_pF':None,'combined_acceptance':'UNKNOWN'})
    def to_power_boundary(name,pin,net):
        h='X1:'+name+':middle'
        if name=='J-PWR':return 0
        es=[x for x in trace_edges if x['net']==net and x['to']['ref']==h and x['to']['pin']==pin]
        need(len(es)==1,'missing endpoint to common boundary copper')
        return es[0]['allocation_mm']
    rails=[];returns=[];nc=[];local={}
    for ref,p in sorted(packages.items()):
        for pin,net in p['pins'].items():
            ep=endpoint(packages,ref,pin)
            if net is None:nc.append(ep);continue
            local.setdefault(net,[]).append(ep)
            side='J'if p['board']=='X1-jack'else'C';need(p['board']in ['X1-jack','X1-control'],'unknown X1 board')
            if net in RAILS-{'AGND'}:
                name=side+'-PWR';need(net in expected[name],'+5V forbidden on control host');wp=str(expected[name].index(net)+1);w=wires[name,wp]
                rails.append({'endpoint':ep,'transport_link':name,'transport_pin':wp,'board_branch_allocation_mm':segment(ep['pad_xyz_mm'],w['front_pad_xyz_mm']),'middle_allocation_mm':to_power_boundary(name,wp,net),'wire_max_mm':w['wire_max_mm'],'GH_pair_mm':15,'endpoint_to_power_boundary_allocation_mm':segment(ep['pad_xyz_mm'],w['front_pad_xyz_mm'])+to_power_boundary(name,wp,net)+w['wire_max_mm']+15,'upstream_not_included':True,'current_A':None,'rail_drop_V':None})
            if net=='AGND':
                alternatives=[]
                for suffix in ('SIG','PWR'):
                    name=side+'-'+suffix;wp=str(expected[name].index('AGND')+1);w=wires[name,wp]
                    alternatives.append({'transport_link':name,'pin':wp,'front_header_pad_xyz_mm':w['front_pad_xyz_mm'],'allocation_mm':segment(ep['pad_xyz_mm'],w['front_pad_xyz_mm']),'middle_to_common_boundary_allocation_mm':to_power_boundary(name,wp,'AGND'),'wire_max_mm':w['wire_max_mm'],'GH_pair_mm':15,'endpoint_to_common_boundary_allocation_mm':segment(ep['pad_xyz_mm'],w['front_pad_xyz_mm'])+to_power_boundary(name,wp,'AGND')+w['wire_max_mm']+15,'upstream_common_return_excluded':True})
                returns.append({'endpoint':ep,'possible_same_board_corridors':alternatives,'scope':'same AGND net; alternatives inventory, not two independent routed return paths or equal sharing','actual_return_current_A':None,'impedance_ohm':None})
    prior_packages=json.loads((hosting.a.OUT/'stage6/hosting-report.json').read_text())['placements']
    loop_pairs=[('U3305','1','U3305','2'),('U3305','7','U3305','6'),('U3303','1','U3303','2'),('U3305','8','C3301','1'),('C3301','2','U3305','9'),('R3316','2','U3305','9'),('R3316','1','J1009','T'),('U3304','2','R3317','1'),('U3304','6','R3318','1'),('U3304','9','R3319','1')]
    feedback=[]
    for ar,ap,br,bp in loop_pairs:
        left,right=endpoint(packages,ar,ap),endpoint(packages,br,bp);need(left['net']==right['net'],'feedback node mismatch')
        old=math.dist(prior_packages[ar]['pads_mm'][ap][0],prior_packages[br]['pads_mm'][bp][0]);new=math.dist(left['pad_xyz_mm'][:2],right['pad_xyz_mm'][:2])
        feedback.append({'net':left['net'],'from':left,'to':right,'prior_XY_pad_distance_mm':old,'current_XY_pad_distance_mm':new,'delta_XY_mm':new-old,'allocated_trace_mm':segment(left['pad_xyz_mm'],right['pad_xyz_mm']),'scope':'selected local feedback/indicator branch; geometric comparison not full loop inductance or routed length; positive delta is an explicit review tradeoff'})
    need(sum(len(p['pins'])for p in packages.values())==182,'complete pin inventory')
    need(len(paths)==3 and sum(1 for w in wires.values()if w['net']=='AGND')==4,'signal/return inventory')
    return {'status':'SOURCE/ALLOCATED GEOMETRY; ELECTRICAL QUALIFICATION OPEN','routing_obstacles':'Octile factors/extra7mm are engineering allocations, not obstacle-aware routing. Foreign-tail substrate apertures, mounting holes, courtyards, layers and copper clearance can require additional detours; no trace is asserted to cross them legally.','counts':{'source_packages':56,'units':76,'source_pins_including_NC':182,'physical_harnesses':4,'physical_wires':15,'signal_wires':6,'rail_wires':5,'AGND_wires':4,'mated_contact_interfaces':30,'crimp_contacts':30,'PCB_headers':8,'housings':8,'transport_NC_header_pins':6,'transport_header_pin_solder_joints':36,'mechanical_MP_solder_joints':16,'total_transport_header_solder_joints':52,'signal_driver_to_receiver_paths':3,'rail_endpoint_rows':len(rails),'AGND_endpoint_rows':len(returns),'NC_endpoint_rows':len(nc)},
      'local_feedback_branch_comparison':feedback,'bypass_associations':bypass,'signal_paths':paths,'wire_metrics':wire_rows,'rail_endpoint_branches':rails,'return_endpoint_branches':returns,'NC_endpoints':nc,'local_net_endpoint_inventory':local,
      'middle_trace_edges':trace_edges,'upstream_power_boundaries':interface['middle_upstream_power_boundaries'],
      'OSC_unchanged':{'path_count':len(baseline['candidate']['paths']),'return_count':len(baseline['candidate']['returns']),'maximum_mm':baseline['candidate']['maximum_mm'],'scope':'No X1 row merged into OSC baseline; complete file source hash retained'},
      'conditional_budgets':conditional_budgets(),'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN','combined_acceptance':'NOT QUALIFIED'}

def build():
    files=[OUT/'interfaces-report.json',hosting.a.OUT/'stage6/candidate-report.json']
    interface,baseline=[json.loads(p.read_text())for p in files]
    result=analyze(interface,baseline)
    sources=files+[hosting.a.OUT/'stage6/hosting-report.json',ROOT/'design/architecture-278/source-ledger.json',Path(__file__),Path(__file__).with_name('test_stage7_electrical.py'),ROOT/'design/connectors/jst-gh.json',ROOT/'design/connectors/sources/jst-gh.pdf',ROOT/'design/standard/electrical-standard.json',ROOT/'design/standard/rail-budget-preliminary.json',ROOT/'design/spec/modules/build_manual_ab_current.py',ROOT/'.claude/skills/component-ti-opa4197ipwr/facts.json',ROOT/'.claude/skills/component-ti-opa4197ipwr/sources.json',ROOT/'design/spec/modules/manual_ab.py',ROOT/'design/spec/modules/io_partition.py',hosting.a.OUT/'stage5-electrical-report.json']
    original=json.loads((hosting.a.OUT/'stage6/hosting-report.json').read_text())
    sources+= [ROOT/name for name in original['source_sha256'] if name.startswith('design/spec/')]+[Path(hosting.__file__)]
    result['source_sha256']=hosting.a.binding(sources)
    return result

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();s=json.dumps(r,indent=2,sort_keys=True)+'\n';path=OUT/'electrical-report.json'
    if args.check:need(path.read_text()==s,'stale Stage7 electrical report')
    else:path.write_text(s)
    print('Stage7 X1 physical wires15;signal paths3;electrical/native/simulation NOT QUALIFIED/NOT RUN')
if __name__=='__main__':main()
