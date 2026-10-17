"""X1 operating-state current paths and conditional ground-error arithmetic.

No simulator, native KiCad, routed copper, hardware execution or guaranteed
assembled bound. Signed diagnostic KCL never earns cancellation/sharing credit.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import stage7_electrical as prior

ROOT=prior.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage8'
need=prior.need
BUNDLES=('ti-opa4197ipwr','ti-opa4196idr','adi-adg5412fbruz','nexperia-bas16gw-qx','nexperia-bat54s-215')


def source_capture(interface):
    """Bind every unit, physical source pin and bypass; preserve actual board roles."""
    ledger=json.loads((ROOT/'design/architecture-278/source-ledger.json').read_text())
    live,source=prior.hosting.live_packages(ledger)
    packages=interface['packages']
    need(set(packages)==set(live)and len(packages)==56,'complete X1 source packages')
    for ref,p in packages.items():
        need(p['pins']==live[ref]['pins']and sorted(p['units'])==sorted(live[ref]['units']),'source pin/NC/unit drift '+ref)
        need(p['board']==('X1-control'if live[ref]['owner']=='front-control'else'X1-jack'),'source board ownership drift')
    fs,instances=prior.hosting.specification();instance=next(i for i in instances if i.name=='X1');family=next(f for f in fs if f.name==instance.family)
    units=[];byunit={}
    for p in family.parts:
        ref=prior.hosting.designator(p,instance)
        row={'ref':ref,'unit':p.unit,'value':p.value,'symbol':p.symbol,'pins':p.pins,'board':packages[ref]['board'],'role':p.attributes.get('Role','')}
        units.append(row);byunit[ref,p.unit]=row
    need(len(units)==76 and sum(len(p['pins'])for p in packages.values())==182,'full source unit/pin count')
    # Prior exact selector/output-feedback assertions plus current-bearing branches.
    prior.source_trace()
    def expect(ref,unit,value,pins):
        p=byunit[ref,unit];need(p['value']==value and p['pins']==pins,'current path source drift '+ref)
    for r,n in [('R3303','A_PROTECTED'),('R3307','B_PROTECTED')]:expect(r,0,'100000 Ω',{'1':n,'2':'AGND'})
    for r,left,right in [('R3304','A_PROTECTED','A_SENSE'),('R3308','B_PROTECTED','B_SENSE')]:expect(r,0,'10000 Ω',{'1':left,'2':right})
    for ref,n in [('D3301','A_SENSE'),('D3302','B_SENSE')]:expect(ref,1,'BAT54S,215',{'1':'-12V','2':'+12V','3':n})
    for ref,stem,en in [('U3301','A','Cadd797_ENABLE'),('U3302','B','C9a8343_ENABLE')]:
        expect(ref,1,'ADG5412FBRUZ',{'3':stem+'_TIP','1':en,'2':stem+'_PROTECTED'})
        expect(ref,5,'ADG5412FBRUZ',{'13':'+12V','4':'-12V','5':'AGND','12':None})
        for unit,pins in [(2,('14','16','15')),(3,('11','9','10')),(4,('6','8','7'))]:expect(ref,unit,'ADG5412FBRUZ',{p:'AGND'for p in pins})
    led=[]
    for unit,stem,r,ds,panel,monitor,opins in [(1,'C025c3f','R3317',('D3303','D3304','D3305','D3306'),'D809','A_BUFFER',('1','2','3')),(2,'Cc6c62b','R3318',('D3308','D3309','D3310','D3311'),'D909','B_BUFFER',('7','6','5')),(3,'C7971de','R3319',('D3313','D3314','D3315','D3316'),'D1009','OUT_BUFFERED',('8','9','10'))]:
        expect(r,0,'5600 Ω',{'1':stem+'_SENSE','2':'AGND'})
        expect('U3304',unit,'OPA4196IDR',{opins[0]:stem+'_DRIVE',opins[1]:stem+'_SENSE',opins[2]:monitor})
        for ref,pins in zip(ds,[{'2':stem+'_DRIVE','1':stem+'_LED_A'},{'2':stem+'_SENSE','1':stem+'_LED_A'},{'2':stem+'_LED_K','1':stem+'_DRIVE'},{'2':stem+'_LED_K','1':stem+'_SENSE'}]):expect(ref,1,'BAS16GW-QX',pins)
        expect(panel,0,'APHHS1005QWF/D',{'1':stem+'_LED_K','2':stem+'_LED_A'})
        led.append({'monitor':monitor,'amplifier':f'U3304:{unit}','sense_resistor':r,'positive_current_path':[f'U3304:{opins[0]}',ds[0]+':2->1',panel+':2->1',ds[3]+':2->1',r+':1->2','jack AGND'],
                    'negative_current_path':['jack AGND',r+':2->1',ds[1]+':2->1',panel+':2->1',ds[2]+':2->1',f'U3304:{opins[0]}','-12V via output stage'],
                    'signed_ground_current':'MONITOR/5600, conditional on linear feedback/headroom; LED sees magnitude, ground current retains sign'})
    for ref,mpn in [('U3303','OPA4197IPWR'),('U3304','OPA4196IDR'),('U3305','OPA4197IPWR')]:
        expect(ref,5,mpn,{'4':'+12V','11':'-12V'})
        need(set(packages[ref]['units'])=={1,2,3,4,5},'whole quad including unused sections')
    bypass=[]
    for ref,p in source.items():
        if not p['decouples_ref']:continue
        target=p['decouples_ref'];unit=byunit[ref,0]
        need(unit['value']=='100 nF'and set(unit['pins'].values())in ({'+12V','AGND'},{'-12V','AGND'}),'source bypass value/net drift')
        need(packages[ref]['board']==packages[target]['board'],'source bypass host split')
        bypass.append({'ref':ref,'target':target,'board':packages[ref]['board'],'rail':next(n for n in unit['pins'].values()if n!='AGND'),'capacitance_F':100e-9,'pins':unit['pins']})
    need(len(bypass)==10,'ten source bypasses')
    return {'unit_inventory':units,'counts':{'packages':56,'units':76,'pins_including_NC':182,'amplifier_sections':12,'unused_amplifier_sections':5,'fault_switch_packages':2,'active_protected_inputs':2,'unused_grounded_switch_channels':6,'bypasses':10},
            'LED_polarity_paths':led,'bypasses':bypass,'unused_ground_input_refs':['U3303:5','U3303:10','U3303:12','U3304:12','U3305:12'],
            'external_ground_ports':[{'ref':r,'pin':'S','net':'AGND','board':packages[r]['board'],'tip_normal_pin':'TN','tip_normal_net':packages[r]['pins']['TN']}for r in ('J809','J909','J1009')]}


def facts(config):
    bundles={name:json.loads((ROOT/f'.claude/skills/component-{name}/facts.json').read_text())for name in BUNDLES}
    get=lambda bundle,id:next(f for f in bundles[bundle]['facts']if f['fact_id']==id)
    q197=get('ti-opa4197ipwr','fact-op-precision-quiescent-current');q196=get('ti-opa4196idr','fact-op-audio-quiescent-current')
    need(q197['value']['maximum_full_temperature']==1.5 and q196['value']['maximum_full_temperature']==250,'quiescent fact units/values changed')
    need(q197['unit']=='mA per amplifier'and q196['unit']=='uA per amplifier','quiescent units')
    source=next(s for s in json.loads((ROOT/'.claude/skills/component-adi-adg5412fbruz/sources.json').read_text())['sources']if s['source_id']=='src-fault-switch-datasheet')
    adg=config['ADG5412F_primary_ground_evidence'];need(adg['sha256']==source['sha256']and adg['revision']==source['revision']=='C','unreviewed ADG primary identity')
    need(all(adg[k]==v for k,v in {'normal_typical_A':.0004,'normal_full_temperature_max_A':.0006,'fault_typical_A':.0008,'fault_full_temperature_max_A':.0011,'normal_IDD_typical_A':.0009,'normal_ISS_typical_A':.0005,'normal_IDD_full_temperature_max_A':.0013,'normal_ISS_full_temperature_max_A':.0007}.items()),'reviewed ADG current table changed')
    diode=json.loads((ROOT/'.claude/skills/component-nexperia-bas16gw-qx/pin-map.json').read_text())
    pins=diode['pin_maps'][0]['pins'];need({p['symbol_pin']:p['function']for p in pins}=={'1':'K cathode','2':'A anode'},'bridge diode polarity source')
    return {'OPA4197_IQ':q197,'OPA4196_IQ':q196,'OPA4197_input_bias':get('ti-opa4197ipwr','fact-op-precision-input-bias-current-full-temperature'),
            'ADG_ground_current':adg,'ADG_grounded_off_leakage':get('adi-adg5412fbruz','fact-fault-switch-grounded-off-leakage'),'ADG_floating_off_leakage':get('adi-adg5412fbruz','fact-fault-switch-floating-off-leakage'),
            'BAS16GW_QX_polarity':diode['pin_maps'][0],
            'scope':'Manufacturer facts retain their exact conditions. Quiescent rows have IO=0 and are not total active supply-current bounds. ADG ±16.5V figures used at project ±12V are conditional sensitivity only.'}


def topology(interface):
    expected={'J-SIG':{'1':'/X1/A_BUFFER','2':'/X1/B_BUFFER','3':'/X1/SELECTOR_REMOTE','4':'AGND'},'C-SIG':{'1':'/X1/A_BUFFER','2':'/X1/B_BUFFER','3':'/X1/SELECTOR_REMOTE','4':'AGND'},'J-PWR':{'1':'+12V','2':None,'3':'-12V','4':None,'5':'+5V','6':None,'7':'AGND'},'C-PWR':{'1':'+12V','2':'-12V','3':'AGND'}}
    links={l['id']:l for l in interface['links']};need(set(links)==set(expected),'four actual harnesses required')
    grounds=[]
    for name,pins in expected.items():
        link=links[name];need(link['pins']==pins,'harness source pinmap drift')
        active={p:n for p,n in pins.items()if n is not None};need({w['pin']:w['net']for w in link['conductors']}==active and len(link['conductors'])==len(active),'one wire per active contact; NC unwired')
        for w in link['conductors']:
            for side in ('front','middle'):
                h=interface['headers'][w[side+'_header']];need(h['pins'][w['pin']]==w['net']and h['pads_xyz_mm'][w['pin']][0]==w[side+'_pad_xyz_mm'],'actual contact/pad mismatch')
            if w['net']=='AGND':grounds.append({'link':name,'pin':w['pin'],'from_board':'X1-jack'if name.startswith('J-')else'X1-control','front_header':w['front_header'],'middle_header':w['middle_header'],'front_pad_xyz_mm':w['front_pad_xyz_mm'],'middle_pad_xyz_mm':w['middle_pad_xyz_mm'],'wire_max_mm':w['wire_max_mm'],'mated_contacts':2,'wire_copper_crimp_R_ohm':None,'current_sharing_fraction':None})
    edges=interface['middle_trace_edges'];defs=[('/X1/'+n,'J-SIG',str(k),'C-SIG',str(k))for k,n in enumerate(('A_BUFFER','B_BUFFER','SELECTOR_REMOTE'),1)]+[('+12V','J-PWR','1','C-PWR','1'),('-12V','J-PWR','3','C-PWR','2')]+[('AGND','J-PWR','7',n,p)for n,p in [('J-SIG','4'),('C-SIG','4'),('C-PWR','3')]]
    expected_edges={(n,'X1:'+a+':middle',ap,'X1:'+b+':middle',bp)for n,a,ap,b,bp in defs}
    need(len(edges)==8 and {(e['net'],e['from']['ref'],e['from']['pin'],e['to']['ref'],e['to']['pin'])for e in edges}==expected_edges,'middle graph missing/duplicate/crossnet edge')
    for e in edges:
        for side in ('from','to'):
            p=e[side];h=interface['headers'][p['ref']];need(h['pins'][p['pin']]==e['net']and h['pads_xyz_mm'][p['pin']][0]==p['pad_xyz_mm'],'middle edge actual pad')
    return {'ground_branches':grounds,'middle_AGND_star':{'header':'X1:J-PWR:middle','pin':'7','pad_xyz_mm':interface['headers']['X1:J-PWR:middle']['pads_xyz_mm']['7'][0]},'middle_edges':edges,
            'upstream_boundaries':interface['middle_upstream_power_boundaries'],'interpretation':'Each board has signal-AGND and power-AGND branches joined by actual PCB AGND net and middle star; no isolated return domains, zero board resistance, equal sharing or current cancellation assumed. Any load may use either available AGND branch according to actual impedance.'}


def selector(a,b,mode,r_a,r_b,r_bias,g_control=0):
    need(mode in ('A','B','bridge','open'),'unsupported physical selector state')
    need(all(math.isfinite(x)for x in (a,b,r_a,r_b,r_bias,g_control))and min(r_a,r_b,r_bias)>0,'finite positive source network')
    ga=1/r_a if mode in ('A','bridge')else 0;gb=1/r_b if mode in ('B','bridge')else 0;gg=1/r_bias;den=ga+gb+gg
    v=(a*ga+b*gb+g_control*gg)/den
    ia=(a-v)*ga;ib=(b-v)*gb;ground=(v-g_control)*gg
    need(math.isclose(ia+ib,ground,abs_tol=1e-14),'selector KCL')
    return {'common_voltage_relative_J_AGND_V':v,'A_signal_current_A':ia,'B_signal_current_A':ib,'control_bias_ground_current_A':ground,'control_to_jack_ground_coupling':gg/den,'A_gain':ga/den,'B_gain':gb/den}


def state_case(config,state,resistance,adg_ground):
    n=config['nominal']
    expected={'selector_series_each_ohm':2200,'selector_bias_ohm':10000000,'indicator_sense_ohm':5600,'input_pulldown_ohm':100000,'enable_supply_V':5,'enable_feed_ohm':1000,'enable_pulldown_ohm':100000}
    need(all(n[k]==v for k,v in expected.items())and n['output_load_ohm']>=10000,'numerical source network drift')
    need(resistance['mated_GH_contact_ohm']in (.03,.05),'reviewed GH contact cases')
    v_a,v_b=state['A_V'],state['B_V'];rc=resistance['mated_GH_contact_ohm']
    need(all(math.isfinite(v)and v>=0 for k,v in resistance.items()if k!='id'),'nonnegative finite resistance case')
    rsignal=4*rc+resistance['extra_signal_route_ohm'];s=selector(v_a,v_b,state['switch'],n['selector_series_each_ohm']+rsignal,n['selector_series_each_ohm']+rsignal,n['selector_bias_ohm'])
    out=s['common_voltage_relative_J_AGND_V'];load=out/n['output_load_ohm']
    output_drive=out+998*load  # R3314+R3315; LED senses OUT_BUFFERED, not OUT_TIP.
    led=[v/n['indicator_sense_ohm']for v in (v_a,v_b,output_drive)]
    inputs=[v/n['input_pulldown_ohm']for v in (v_a,v_b)];enable=2*n['enable_supply_V']/(n['enable_feed_ohm']+n['enable_pulldown_ohm'])
    # No accidental cancellation or equal current splitting in these envelopes.
    j_envelope=sum(map(abs,led))+abs(load)+sum(map(abs,inputs))+enable+2*abs(adg_ground)+15e-9
    c_envelope=abs(s['control_bias_ground_current_A'])+3*15e-9
    common_envelope=j_envelope+c_envelope
    branch=2*rc+resistance['extra_return_branch_ohm'];local=resistance['board_local_common_ohm'];upstream=resistance['upstream_common_ohm']
    j_local=j_envelope*(branch+local);c_local=c_envelope*(branch+local);diff=j_local+c_local;common=common_envelope*upstream
    coefficient=s['control_to_jack_ground_coupling'];signal_currents=[s['A_signal_current_A'],s['B_signal_current_A']]
    pos=lambda xs:sum(max(x,0)for x in xs)
    neg=lambda xs:sum(max(-x,0)for x in xs)
    adg=config['ADG5412F_primary_ground_evidence']
    need(adg_ground in (adg['normal_typical_A'],adg['normal_full_temperature_max_A']),'unreviewed ADG ground case')
    suffix='typical_A'if adg_ground==adg['normal_typical_A']else'full_temperature_max_A'
    idd,iss=adg['normal_IDD_'+suffix],adg['normal_ISS_'+suffix]
    return {'state':state,'resistance_case':resistance['id'],'ADG_each_IGND_sensitivity_A':adg_ground,'selector':s,
      'ideal_output_voltages_V':{'OUT_TIP':out,'OUT_BUFFERED':output_drive,'scope':'Nominal linear precision feedback,998ohm output isolation and stated load. Extra PCB resistance, bias/leakage and amplifier/LED headroom remain unknown; no clipping guarantee.'},
      'signed_diagnostic_terms_A':{'LED_A_B_OUT_to_jack_ground':led,'external_output_load':load,'external_input_pulldowns':inputs,'enable_direct_ground':enable,'ADG_two_ground_pins':2*adg_ground,'OPA4197_unused_ground_input_magnitude_sensitivity':{'jack':15e-9,'control':45e-9}},
      'external_return_scope':'Input pulldown current may close through its own patch sleeve or share middle/upstream ground. Output load return may enter local jack sleeve or another external ground. Fractions are UNKNOWN; envelopes include all magnitudes, signed terms are not credited as cancellation.',
      'quiescent_between_rails_A':{'jack':.007,'control':.006,'all12_amplifiers':.013,'scope':'Source-conditioned full-temperature IO=0 maxima:8precisionsections×1.5mA+4indicatorsections×250uA; includes5unusedsections. Not directly injected intoAGND; active output terms and nonideal input currents separate.'},
      'ADG_supply_sensitivity_case':suffix,'conditional_rail_current_A':{'J_plus12':.007+2*idd+pos(led)+max(load,0)+pos(signal_currents),'J_minus12_magnitude':.007+2*iss+neg(led)+max(-load,0)+neg(signal_currents),'C_plus12':.006,'C_minus12_magnitude':.006,'J_plus5_enable_resistors_only':enable,'C_plus5':None},
      'rail_scope':'Mixes explicitly conditioned IQ maxima, ADG table supply sensitivities and nominal ideal output currents. IDD/ISS/IGND independent maxima need not occur together; not a self-consistent solved semiconductor operating point or guaranteed total. No +5V control connection. Bias, leakage, dynamic crossover, faults and transients remain unknown.',
      'modeled_current_magnitude_envelopes_A':{'jack_AGND':j_envelope,'control_AGND':c_envelope,'upstream_AGND':common_envelope},
      'ground_voltage_bounds_for_modeled_terms_V':{'jack_to_middle':j_local,'control_to_middle':c_local,'control_minus_jack_absolute':diff,'middle_to_upstream':common,'jack_to_upstream':j_local+common,'control_to_upstream':c_local+common},
      'ground_scope':'Conservative modeled-term bound charges each board total to one full-resistance return branch; no parallel benefit. Shared middle anchor cancels only as coordinate reference for C−J; upstream/external measurement errors remain separately present. Unknown branch/copper impedance means these are scenarios, not assembled bounds.',
      'ideal_selected_output_error_from_C_minus_J_ground_bound_V':coefficient*diff,
      'coupling_scope':'Only the captured selector10M-to-controlground DC term. Unity followers track absolute voltage: selected coupling=Rseries/(Rbias+Rseries), bridge roughlyhalf, open=1. Localjack ground gradients, external source/receiver ground mismatch, PSRR/inputbias and dynamic behavior are NOT covered or cancelled.',
      'retained_200uV_ground_comparison':{'planning_V':config['ground_error_planning_V'],'jack_scenario_exceeds':j_local+common>config['ground_error_planning_V'],'control_scenario_exceeds':c_local+common>config['ground_error_planning_V'],'scope':'Planning comparison only, no blanketX1pass/fail or automaticunitygain outputerror'},
      'total_guaranteed_current_bound_A':None,'total_guaranteed_output_error_V':None,'qualified':False}


def build(interface=None):
    config_path=OUT/'current-input.json';config=json.loads(config_path.read_text())
    if interface is None:interface=json.loads((OUT/'interfaces-report.json').read_text())
    capture=source_capture(interface);primary=facts(config);graph=topology(interface)
    standard=json.loads((ROOT/'design/standard/electrical-standard.json').read_text())
    need(config['dynamic_sensitivities']['remote_net_capacitance_envelope_F']==standard['remote_controls']['max_harness_capacitance_F'],'retained remote capacitance envelope drift')
    need(config['ground_error_planning_V']==.0002,'retained ground allocation changed without review')
    need(len(config['states'])==9 and len({s['id']for s in config['states']})==9,'operating-state coverage')
    cases=[state_case(config,s,r,ground)for s in config['states']for r in config['resistance_cases']for ground in (config['ADG5412F_primary_ground_evidence']['normal_typical_A'],config['ADG5412F_primary_ground_evidence']['normal_full_temperature_max_A'])]
    caps={board:{rail:sum(c['capacitance_F']for c in capture['bypasses']if c['board']==board and c['rail']==rail)for rail in ('+12V','-12V')}for board in ('X1-jack','X1-control')}
    dyn=config['dynamic_sensitivities'];need(dyn['rail_ramp_duration_s']>0,'positive ramp duration')
    startup={b:{rail:cap*dyn['rail_ramp_delta_V']/dyn['rail_ramp_duration_s']for rail,cap in rails.items()}for b,rails in caps.items()}
    report={'status':'SOURCE-BOUND CONDITIONAL X1 CURRENT/ERROR STUDY; NO HARDWARE ACCEPTANCE','source_capture':capture,'primary_facts_with_conditions':primary,'physical_return_topology':graph,'cases':cases,
      'operating_state_model':'Algebraic resistor-network DC and conditional current budgets, not a simulator. Nominal linear feedback is an assumption; signed terms do not reduce the no-cancellation magnitude envelopes.',
      'selector_equations':{'node':'V=(VA/RA whenAclosed +VB/RB whenBclosed +GC/Rbias)/(1/RA whenAclosed +1/RB whenBclosed +1/Rbias)','ground_coupling':'dV/d(GC−GJ)=(1/Rbias)/sumconductances','open_bias_sensitivity_V':15e-9*config['nominal']['selector_bias_ohm'],'open_scope':'150mV conditional15nA×10M source-conditioned bias sensitivity, not actual open voltage or guaranteed hold/mute. Switch open interval, node capacitance and leakage unknown.'},
      'dynamic_and_bypass':{'actual_source_bypass_capacitance_F':caps,'rail_ramp_sensitivity':dyn,'rail_cap_current_magnitude_A':startup,'unbalanced_ground_current_rule':'Each cap current=C*dVrail/dt; +rail rising injectsground, -rail falling withdrawsground. Do not credit simultaneous cancellation; unknown ramp order, supply impedance and unallocatedboardbulk remain.',
        'remote_cap_current_grid':[{'C_F':dyn['remote_net_capacitance_envelope_F'],'slew_V_per_us':v,'current_A':dyn['remote_net_capacitance_envelope_F']*v*1e6}for v in dyn['signal_slew_V_per_us']],
        'scope':'1nF is retainedremote-envelope, not extractedcapacitance. Displacement-current destination can beAGND/rails/adjacentnets; driverdynamic/headroom/chargecapacity unvalidated. No cap current assigned to an AGND branch without physicalcapmatrix.'},
      'unknowns':[
       {'id':'AGND_IMPEDANCE_SHARING','missing':'actualfourwire/crimp/copper/common-plane impedances, branchjunctions andexternalgroundloops','consequence':'No guaranteed current split, common-mode shift or input/outputgrounderror. Signalreturn can carryLED/supplycurrent becauseAGNDnetsjoin.'},
       {'id':'ADG_AT_PROJECT_RAILS','missing':'IGND/IDD/ISS acrossproject±12V,actualdigitalinputlevels,temperature andsequence','consequence':'Retained±16.5V table reused only conditionally; faulttable±55V neither projectfault envelope nor qualification.'},
       {'id':'ACTIVE_BIAS_LEAKAGE','missing':'actualOPA4196inputbias/offset versusconditions, clamp leakage,ADGchannel/digitalcurrents and packageground behavior','consequence':'Known modeled subtotal is not complete upperbound;15nAOPA4197mid-supply fact notuniversalactualcommonmode bound.'},
       {'id':'LOCAL_GROUND_GRADIENT','missing':'LED/ADG/enable/current return path relative inputpulldown/outputreference andprecisionfeedbackpads','consequence':'Small calculatedC-Jcoupling does not bound localjackgradient or externalpatchreferenceerror.'},
       {'id':'FAULT_UNPOWERED','missing':'allrailramp/floating/one-rail-loss states,continuousfault/clampcurrents,outputshort/backdrive andconnector interruptions','consequence':'Groundedoff100nA sourceleakage applies onlyexactgroundedconditions;floatingoff10uA istypical,no maximum. No faultcurrentlimit/safehotplug claim.'},
       {'id':'SELECTOR_TRANSITIONS','missing':'maintainedswitchlevermap,break/make/bounce interval,parasiticnodecharge','consequence':'Open/bridge rows are hypotheticalstates; opposing-inputoverlap source-current path exists evenwhenAGNDsignedtermnearzero.'},
       {'id':'DYNAMIC_STABILITY','missing':'assembledRLC/activebehavior/actualsourceandloadcapacitance','consequence':'DCalgebra/IQ/1nF envelope cannotqualify transientreturnorloopstability.'}],
      'hosting_service_recommendation':'Keep X1 as conditionalsourcecandidate. PreserveLEDbridge+amp+sense+bypass locality androuteLED/ADG/enable returns to power-return landing without crossinginput/reference/feedback groundregions; this is a proposedcopper/current-pathrequirement,notisolatedgrounds or proofexistingroutesdoit. RetainadjacentsignalAGNDbutdo notcredititwithzero loadcurrent. Completecarrier/strainrelief/serviceclearance andrealPOWERhandoff before anotherfunctionisclaimedclosed; no newmoduleimplemented.',
      'qualified':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
    locality_path=OUT/'locality-report.json'
    locality=json.loads(locality_path.read_text())
    report['local_bypass_return_corridors']=[{'net':r['net'],'endpoints':r['endpoints'],'status':r['status'],'copper_centreline_mm':r.get('copper_centreline_mm'),'scope':'source geometric connection only; not extractedimpedance, nativecopper or proofcompletepowersupplyloop'}for r in locality['corridors']if r['net']=='AGND']
    report['bypass_loop_scope']='U3305 hasV+/V−pins,no dedicatedGNDpin. Railpad-to-capcorridors alone do not close thebypassloop; C3308:2↔C3309:2 AGNDconnection, capESR/ESL andbothsupplypaths matter. Anygroundcorridor listedabove is a boundedsourcegeometryclaim only. C3301 fastfeedback isDRIVE↔FB anddoesnot acquirean inventedAGNDleg.'
    sources=[locality_path,config_path,OUT/'interfaces-report.json',Path(__file__),Path(__file__).with_name('test_stage8_currents.py'),Path(prior.__file__),Path(prior.hosting.__file__),ROOT/'design/architecture-278/source-ledger.json',ROOT/'design/standard/electrical-standard.json',ROOT/'design/spec/modules/manual_ab.py',ROOT/'design/spec/modules/io_partition.py',ROOT/'design/connectors/jst-gh.json',ROOT/'design/partition/sources/opa4197-layout.pdf',ROOT/'design/partition/sources/opa4196-layout.pdf']
    for bundle in BUNDLES:sources +=[ROOT/f'.claude/skills/component-{bundle}/{name}.json'for name in ('facts','sources','pin-map')]
    sources += [ROOT/'design/spec/instrument.py',ROOT/'design/standard/parts-shortlist.json']+list((ROOT/'design/spec/modules').glob('*.py'))
    report['source_sha256']=prior.hosting.a.binding(sources)
    return report


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();body=json.dumps(r,indent=2,sort_keys=True)+'\n';path=OUT/'currents-report.json'
    if args.check:need(path.read_text()==body,'stale Stage8 current report')
    else:path.write_text(body)
    print('X1 current study54 conditional cases;12 amplifiersections;4AGNDbranches;totalcurrent/error guarantees UNKNOWN; simulation/native NOT RUN')
if __name__=='__main__':main()
