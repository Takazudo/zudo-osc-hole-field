"""Captured-circuit electrical budgets and bounded characterization, no simulation.

Numerical sensitivities are not assembled stability/accuracy guarantees. No native
calls, substitutions, changed canonical limits or fabricated parasitics.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import stage3_crossing_audit as audit
import stage4_requirements as requirements

ROOT,OUT=audit.ROOT,audit.OUT
BUNDLES=('ti-opa4197ipwr','ti-opa4196idr','ti-sn74hc14dr','ti-lm393bidr','nexperia-bat54s-215','adi-adg5412fbruz')

def parallel(a,b):return a*b/(a+b)
def pole(r,c):return {'tau_s':r*c,'pole_Hz':1/(2*math.pi*r*c)}
def require(ok,msg):
    if not ok:raise ValueError(msg)

def source_context():
    ctx=audit.context();families,instances=audit.specification();families={f.name:f for f in families}
    values={}
    for instance in instances:
        if instance.name not in audit.INSTANCES+['OCTAVE_REF']:continue
        for p in families[instance.family].parts:values[audit.designator(p,instance),p.unit]=p.value
    for row in ctx['rows']:row['value']=values[row['ref'],row['unit']]
    return ctx

def trace_net(net,ctx,max_passive_steps=3):
    """Bounded possible circuit paths, not switch-state solution or complete graph.

    Cross only physical two-terminal R/C and panel pots/switches. Active outputs
    and inputs terminate each trace. Capacitor paths are AC-only; switch branches
    are conditional on state and never simultaneous short-circuit assumptions.
    """
    adjacent=defaultdict(list)
    for p in ctx['rows']:
        for pin,n in p['pins'].items():
            if n is not None and n not in audit.POWER:adjacent[n].append((p,pin))
    found={};seen=set()
    def walk(n,path,depth,ac=False,sw=False):
        marker=(n,depth,ac,sw)
        if marker in seen:return
        seen.add(marker)
        for p,pin in adjacent[n]:
            typ=p['pin_types'].get(pin);endpoint=p['ref']+':'+pin
            item={'endpoint':endpoint,'net':n,'unit':p['unit'],'key':p['key'],'symbol':p['symbol'],'value':p['value'],'path':path+[endpoint],'AC_only':ac,'switch_or_pot_state_dependent':sw}
            if typ in ('input','output'):
                item['pin_type']=typ;found[endpoint,ac,sw]=item;continue
            if depth==max_passive_steps:continue
            passive=p['ref'].startswith(('R','C','SW'))
            if not passive:continue
            # Never bridge active packages, diodes or arbitrary multi-terminal parts.
            nets=[(q,m) for q,m in p['pins'].items() if m and m!=n and m not in audit.POWER]
            for nextpin,nextnet in nets:
                walk(nextnet,path+[endpoint,p['ref']+':'+nextpin],depth+1,ac or p['ref'].startswith('C'),sw or p['ref'].startswith(('SW','RV')))
    walk(net,[],0)
    return {'net':net,'max_passive_steps':max_passive_steps,'active_terminals':sorted(found.values(),key=lambda p:(p['endpoint'],p['AC_only'],p['switch_or_pot_state_dependent'])),
            'scope':'bounded possible branches; active units terminate traversal; feedback inputs may appear alongside downstream inputs; no switch simultaneity or DC conduction through capacitors inferred'}

def assert_capture(ctx):
    """Reject source changes that invalidate the explicit numerical circuit model."""
    expected={
        'R1119':('1000 Ω',{'1':'/O1/C1eb779_W','2':'/O1/C1eb779_W_SENSE'}),
        'R1129':('1000 Ω',{'1':'/O1/C83f36b_W','2':'/O1/C83f36b_W_SENSE'}),
        'R1135':('1 kΩ',{'1':'/O1/OCT_SELECTED','2':'/O1/OCT_FILTER'}),
        'R1140':('100 kΩ',{'1':'/O1/1V_BUFFER','2':'/O1/EXPO_SUM'}),
        'R1156':('100000 Ω',{'1':'/O1/SYNC_BUFFER','2':'/O1/C99bd37_GATE_SENSE'}),
        'R1157':('33200 Ω',{'1':'/O1/LOCAL_REF5','2':'/O1/C99bd37_GATE_SENSE'}),
        'R1158':('10000 Ω',{'1':'OSC_GATE_REF','2':'/O1/C99bd37_THRESH'}),
        'R1159':('390000 Ω',{'1':'/O1/C99bd37_CMP_OUT','2':'/O1/C99bd37_THRESH'}),
        'R1160':('4700 Ω',{'1':'+5V','2':'/O1/C99bd37_CMP_OUT'}),
        'R1161':('100 kΩ',{'1':'/O1/SOFT_DRIVE','2':'AGND'}),
        'R1162':('10 kΩ',{'1':'/O1/SOFT_DRIVE','2':'/O1/SOFT_EDGE'}),
        'R1163':('100 kΩ',{'1':'/O1/HARD_DRIVE','2':'AGND'}),
        'R1164':('10 kΩ',{'1':'/O1/HARD_DRIVE','2':'/O1/HARD_EDGE'})}
    for ref,(value,pins) in expected.items():
        p=ctx['bypin'][ref,next(iter(pins))][0]
        require(p['value']==value and p['pins']==pins,'changed captured model '+ref)
    additional={'R1117':'100 Ω','R1118':'10000 Ω','R1120':'1e+07 Ω','R1130':'1e+07 Ω','C1105':'1e-08 F','C1106':'1e-08 F','R1136':'10 MΩ','C1108':'100 nF','C1113':'1 nF','C1114':'1 nF','RB1110':'100 Ω','RB1111':'100 Ω','C1115':'1 nF','RV104':'PTV09A-4020F-B104','RV106':'PTV09A-4020F-B103'}
    for ref,value in additional.items():
        part=next(p for p in ctx['rows'] if p['ref']==ref)
        require(part['value']==value,'changed captured model '+ref)
        expected[ref]=(value,part['pins'])
    for ref,(value,pins) in expected.items():
        part=next(p for p in ctx['rows'] if p['ref']==ref)
        for inst in audit.INSTANCES:
            other=ctx['bykey'][inst,part['key'],part['unit']]
            require(other['value']==value and other['pins']=={pin:(net.replace('/O1/','/'+inst+'/') if net else net) for pin,net in pins.items()},'five-instance model mismatch '+ref)
    return [{'ref':ref,'value':v,'pins':pins} for ref,(v,pins) in expected.items()]

def gate_threshold(output):
    # KCL includes Rpull only in high/open-collector state; low uses ideal VOL0.
    gref=5*100000/122000
    if output=='high':thresh=(gref/10000+5/(390000+4700))/(1/10000+1/(390000+4700))
    else:thresh=gref*390000/400000
    return thresh*(1+100000/33200)-5*100000/33200

def budgets():
    rcontrol=120000/4+1010;rfail=9.9e6
    rwiper=12000/4+1010
    alpha=33200/(100000+33200);rt=parallel(10000,390000+4700);rs=parallel(100000,33200)
    return {
      'control_wiper':{'captured':'100k nominal B104 pot;1k series;10M failure pulldown;10nF local shunt; TUNE/FINE OPA4197; PW OPA4196',
        'basis':'pot+20%, fixed1% and reference5.025V are retained planning inputs; no fitted exact tolerance guarantee',
        'thevenin_nominal_max_ohm':25000,'thevenin_with_series_planning_max_ohm':rcontrol,
        'fail_load_error_conservative_bound_V':5.025*rcontrol/(rfail+rcontrol),
        'fail_load_bound_scope':'independent worst voltage and resistance bounds; deliberately loose, not simultaneous position-exact maximum',
        'bias15nA_sensitivity_V':15e-9*parallel(rcontrol,rfail),
        'bias_scope':'OPA4197PW source-conditioned15nA at datasheet default midsupply; not universal at actual reference/common-mode; OPA4196 bound UNKNOWN',
        'nominal_filter':pole(26000,10e-9),'planning_filter_with_direct1nF_lumped_upper_delay':pole(parallel(rcontrol,rfail),11.5e-9),
        'filter_scope':'10nF+5% local capacitor plus1nF diagnostic direct load conservatively lumped behind totalR; upper RC-delay sensitivity, not exact two-node transfer or amplifier stability',
        'exact_small_signal_model':'pot ideal Vw through Rp*x*(1-x)+Zreference to wire node; Ch at wire node;1k to sense node;10M||10nF||Zinput at sense; solve two-node network, include return separately'},
      'FM_PWM_wiper':{'captured':'10k pot;1k series;10M failure pulldown;OPA4196 noninverting input;100k/100k attenuverter gives ideal output2*Vw-Vbuffer',
        'thevenin_nominal_max_ohm':2500,'with_series_planning_max_ohm':rwiper,
        'fail_load_error_input_bound_V':5.025*rwiper/(rfail+rwiper),'attenuverter_noise_gain_nominal':2,
        'bias_1uA_proposal_sensitivity_output_V':2e-6*parallel(rwiper,rfail),
        'bias_status':'1uA is retained oscillator planning sensitivity only; not manufacturer OPA4196 guarantee',
        'diagnostic_1nF_pole':pole(rwiper,1e-9),'dynamic_scope':'lumped high-Z diagnostic; actual cable at wiper before1k, input/feedback poles and driver model remain required'},
      'pitch_input':{'captured':'J1V fault switch→100k pulldown/10k limiter/clamp→OPA4197 follower U1118:1→100k R1140→AS3340 EXPO_SUM; not an ordinary CMOS input',
        'ideal_5V_pitch_resistor_current_A':5/100000,'source_output_impedance_ohm':None,
        'input_limit_15nA_bias_sensitivity_V':10000*15e-9,'input_offset_25C_table_limit_V':100e-6,
        'offset_scope':'OPA4197 source table at±18V/midsupply25C; not a universal project±12V/full-temperature limit',
        'fault_switch_16_5ohm_100k_loading_at5V_V':5*16.5/(100000+16.5),
        'switch_scope':'16.5ohm specified13.5V bipolar rails and stated current; sensitivity only at actual±12V. Clamp leakage and externalsourceR remain UNKNOWN.',
        'return_shift_1mV_equivalent_cents':1.2,'whole_chain_5cents_V':5/1200,
        'conditional_error_formula':'Verror=driver offset+Ibias*Zsource+clamp/leakage*Znode+Iload*Rcontact+DeltaAGND+gain/reference/core errors; correlations and calibration explicitly modeled'},
      'remote_buffer':{'captured':'OPA4196 output→100ohm isolation→FM/PWM_REMOTE;10k local DC feedback plus100pF fast path;10k pot load',
        '5_025V_8k_pot_current_A':5.025/8000,'100ohm_isolation_drop_at_that_load_V':100*5.025/8000,
        'interpretation':'local post-isolation feedback may correct DC resistor drop within headroom; do NOT book full62.8mV as output error or assume correction at AC',
        'reference_driver':'OPA4197 local reference variant uses100ohm isolation,100ohm feedback,1nF compensation; distinct from100pF/10k FM driver',
        '100ohm_direct1nF_diagnostic':pole(100,1e-9),'driver_output_impedance_ohm':None,'phase_margin_deg':None,
        'model_dependency':'validated exact OPA4196 dynamic model and actual harness unavailable; OPA4197 is not a substitute'},
      'SYNC_BUFFER':{'captured':'OPA4196 U1116:8→100k R1156→LM393B U1106:2;33.2k R1157 to LOCAL_REF5; biased analog input',
        'signal_to_comparator_gain':alpha,'sense_thevenin_ohm':rs,
        'rising_ideal_V':gate_threshold('high'),'falling_ideal_V':gate_threshold('low'),
        'existing_rising_window_V':[1.35,1.65],'existing_falling_window_V':[.85,1.15],
        'comparator_4mV_input_referred_sensitivity_V':.004/alpha,
        'two_50nA_bias_worst_sign_input_referred_sensitivity_V':50e-9*(rs+rt)/alpha,
        'limits_scope':'LM393B fact4mV/50nA are source-table conditions; actual+12V/common-mode applicability unqualified; ignores resistor/reference/VOL/OPA4196 errors'},
      'OSC_GATE_REF':{'captured':'OPA4197 U1602:8 buffered22k/100k division→five10k/390k hysteresis branches',
        'nominal_reference_V':5*100000/122000,
        'one_low_state_hysteresis_branch_current_A':(5*100000/122000)/(10000+390000),
        'five_low_state_branch_current_A':5*(5*100000/122000)/(10000+390000),
        'reference_error_to_external_gate_threshold_gain':(390000/400000)/alpha,
        'source_impedance_and_transient_error_V':None,'classification':'DC reference with load-state changes; not logic pulse transport'},
      'SYNC_GATE':{'captured':'SN74HC14 U1107:2→SW103 common→selected HARD/SOFT branch',
        'selected100k_pulldown_at5V_A':5/100000,'ideal_DC_blocked10k_series_current_A':0,
        'steady_scope':'ideal DC block by1nF; core clamp/leakage may invalidate zero; switch both/open states require explicit treatment',
        'VOH_min_V':None,'VOL_max_V':None,'actual5V_drive_to_1nF_delay_s':None,
        'retained_delay_point':{'maximum_s':31e-9,'VCC_V':4.5,'CL_F':50e-12,'input_edge_max_s':6e-9,'temperature_C':[-40,85]},
        'delay_scope':'manufacturer point only; neither interpolation to1nF nor linear scaling establishes actual transport/pulse limit'},
      'HARD_SOFT_DRIVE':{'captured':'selectedHC output→switch→100k pulldown;10k series→1nF AC coupling→AS3340 HARD_PIN6/SOFT_PIN9',
        'series10k_1nF_time_product_s':1e-5,'ideal5V_step_initial_current_limit_A':5/10000,
        'AC_scope':'10us is R*C arithmetic, not pulse decay or accepted minimum pulse width without AS3340 input impedance/clamps and actual driverR',
        'AS3340_receiver_impedance_ohm':None,'minimum_sync_pulse_s':None,'false_edge_rate':None},
      'octave_five_receivers':{'captured':'six shared buffered taps→eachselector→1k→100nF||10M→OPA4197 receiver; five selected loads may share one tap',
        'one_nominal_RC':pole(parallel(1000,1e7),100e-9),'one_dc_load_at3V_A':3/(1e7+1000),
        'one3V_fail_load_error_V':3*1000/(1e7+1000),'one15nA_bias_error_V':15e-9*parallel(1000,1e7),
        'one5V_switch_step_initial_current_A':5/1000,'five5V_step_initial_current_A':5*5/1000,
        'five5V_step_charge_C':5*100e-9*5,'ideal_step_settle_to2mV_s':parallel(1000,1e7)*100e-9*math.log(5/.002),
        'interpretation':'25mA initial demand/2.5uC charge are ideal resistor-capacitor sensitivities, NOT proof buffer can supply them. Simultaneous and staggered switching, contact bounce and current limiting must be modeled.',
        'five_receiver_admittance':'5/(1kohm + 1/(1/10Mohm+s*100nF+Yinput)); add distinct direct interconnect capacitance once by net segment union',
        'direct_capacitance_limit_F':1e-9,'direct_capacitance_extracted_F':None},
      'shared_reference_DC':{'captured':'OSC_REF5 drives10k inversion input,40k+10k onevolt divider,22k+100k gate divider and15localreferencebuffer inputs;OSC_REFN5 drives15localbuffer inputs',
        'positive_fixed_network_current_A':5/10000+5/50000+5/122000,
        'fifteen15nA_input_sensitivity_A':15*15e-9,
        'positive_total_conditioned_sensitivity_A':5/10000+5/50000+5/122000+15*15e-9,
        'negative_input_only_conditioned_sensitivity_A':15*15e-9,
        'scope':'nominal DC networks plus source-conditioned OPA4197 input bias magnitude; input offset/leakage/feedback/transient output demand not included; no fullstate maximum claim',
        'six_octave_direct_net_budget_proposal_pF':{'shared_trace':50,'shared_probe':50,'five_branches_each':160,'aggregate':900,'headroom_to1000':100},
        'capacitance_status':'architecture278900pF allocation applies per octave tap across five branches; remainingthree shared reference nets retain1000pF aggregate ceiling with no900pF split inferred. No extraction and no receiver100nF substitution'},
      'return_error':{'reference':'architecture278 electrical.md proposal:200uV remote return term;0.5mohm whole-return planning goal; not achieved',
        'planning_return_magnitude_A':.7045,'at_0_5mohm_V':.7045*.0005,
        'equivalent_pitch_cents':1200*.7045*.0005,'actual_return_resistance_ohm':None,
        'scope':'sum-of-rail-magnitudes conservative load example; no rail cancellation/current-sharing credit;200uV allocated term not guaranteed by0.5mohm at this load'}
    }

def characterization():
    return {'status':'PROPOSAL bounded characterization specification; no simulation/native/bench execution',
        'common_ranges':{'supply_V':{'+12':[11.4,12,12.6],'-12':[-12.6,-12,-11.4],'+5':[4.75,5,5.25]},'supply_scope':'±12V retained planning envelope;±5%5V is proposed sensitivity, not adopted supply guarantee',
            'temperature_C':[-40,25,85],'temperature_scope':'proposed characterization points within SN74/LM393 grade; does not establish allassembly rating',
            'pot_fraction':[0,.1,.25,.5,.75,.9,1],'direct_capacitance_F':[0,100e-12,1e-9],
            'capacitance_scope':'diagnostic sweep points only,0ideal comparator notphysical claim; geometry extraction remains null',
            'return_shift_V':[-.001,-.0002,0,.0002,.001],'contact_series_ohm':[0,.02,.1,1],
            'contact_scope':'proposal sensitivity cases, not connector guarantee/failure distribution; actual source/common return measured separately'},
        'experiments':[
            {'id':'pitch_and_wipers','input':'0..5V pitch in1V steps;TUNE/FINE/PW all pot points;DC plus1Hz/100Hz/1kHz/10kHz modulation where function accepts modulation','observables':['DCoffset/input-referredcents','temperaturedrift','step settling/overshoot','gain/phase/crosstalk'],'existing_targets':['whole-chain5cents at25C after calibration,0..5V','octave adjacent step<=2mV'],'proposed_targets':{'approval':'PROPOSAL NOT APPROVED; no result evaluated','collective_pitch_interconnect_error_V':1/1200,'allocation_basis':'20% of retained5cent wholechain target=1cent input-referred at1V/oct, across allsimultaneous interconnect contributions, not perwire','remaining_chain_error_V':4/1200,'remaining_chain_scope':'4cents reserved jointly forcore,calibration,reference andamplifier terms outside definedinterconnect boundary; no proofremainingbudget sufficient','interconnect_boundary':'driveroutputpad toreceiverinputpad includingseriescontacts,loading-inducederror,returnshift andpickedupnoise; applyactualpitch pathgain beforecombining. Do notdoublecountamplifier/source errors.','return_suballocation_V':.0002,'remaining_interconnect_error_V':1/1200-.0002,'return_tradeoff':'retains existing200uV planningterm;704.5mA/0.5mohm examplealreadyexceedsit; newallocationisnotachieved','modulation_transfer':'Compare actual transfer withcaptured position-dependent two-nodeRC baseline includingintentional10nF; do notrequireflat20kHz TUNE/FINE/PW. Proposedextra harness deviation <=1%difference incomplexgain relativebaseline wherebaseline magnitude>=0.1DCgain; belowthat floorreportabsoluteoutputerror instead ofsingularrelativeerror.','complex_gain_error_fraction':.01,'baseline_relative_floor':.1,'modulation_tradeoff':'1% is a reviewproposal foraddedinterconnectdistortion, not source-specified audibility or accepted design requirement; exactdriver/passivemodel dependencies mustbeavailable beforeapplying.'}},
            {'id':'remote_driver','input':'FM/PWM±5V step and swept sine,8/10/12k pots,actualinput/parasitic networks','observables':['loop/phase margin if valid model supports it','ringing/settling','sourcecurrent/headroom','output error after local feedback'],'target':'No sustained oscillation; quantitative margin/settling targets require reviewed application allocation','blocker':'validated exact OPA4196 model unavailable; no OPA4197 orideal-source substitution for qualification'},
            {'id':'gate_classes','input':'SYNC_BUFFER amplitude around0.85..1.65V plus0/5V pulses;proposedpulse widths1us,10us,100us,1ms;edge times10ns,100ns,1us,100us;HARD/SOFT/alloff states','observables':['threshold/hysteresis','actualVOH/VOL receiver margin','ringing/overshoot/undershoot','falseedges/missedpulses','core sync response'],'existing_targets':['rising1.35..1.65V,falling0.85..1.15V'],'proposed_targets':{'approval':'PROPOSAL NOT APPROVED; no measured pass','false_edges':0,'missed_edges':0,'scope':'For0/5V fullamplitude pulses in thedeclared finitegrid, countone risingandonefalling SYNC_GATE transition perinputpulse withSYNC heldselected; no extraedges. ForHARD/SOFT separatelyrecordcore synchronization; no universal lockclaim withoutphase/frequency/inputmodel.','pulse_width_definition':'timebetween50% crossingsof successiveedges; useonlyedge_time<=0.1*pulse_width combinations','pulses_per_grid_case':100,'reason':'bounded deterministic diagnostic record; zeroevents in100pulses doesnotestablish statisticalreliability','minimum_supported_pulse_s':None,'timing_scope':'1us..1ms are proposed testpoints, not promisedminimum; failingconditions mapoperatingenvelope andrequire laterreview'}},
            {'id':'shared_nine_nets','input':'all five receivers on same tap,oppositeextremetap transitions,oneatatime andsimultaneous;stagger0/10/100us;open/contactbounce cases','observables':['unique-segmentdirectcapacitance','peak/sourcecurrent','sharedsource droop','everyreceiver settling andadjacentsteperror','reference/groundshift'],'existing_targets':['direct1nF planning envelope distinct from five100nFbehind1k','adjacentstep<=2mV;wholechain5centstargetseparate'],'blocker':'actualswitch bounce,sourceimpedance/currentlimit andparasitics unknown'}],
        'required_models':['exactOPA4196 validated retained model before driver stability','source-conditionedOPA4197 with outputcurrent/headroom andvalid range','LM393B/SN74HC14 dynamic andI/Olimits at actualsupply','AS3340 hard/soft input impedance/clamps','actualharness/contact/probeC,R,L/returngeometry','switchstates/bounce andfive receiver networks'],
        'unknown_handling':'Unknown parameters staynull; sensitivity ranges are explicit proposals, never fitted evidence. No passing result exists.'}

def build():
    ctx=source_context();capture=assert_capture(ctx);paths=json.loads((OUT/'stage4/candidate-report.json').read_text())['candidate']['paths'];facts={};factpaths=[]
    for bundle in BUNDLES:
        path=ROOT/('.claude/skills/component-'+bundle+'/facts.json');factpaths.append(path);facts[bundle]=json.loads(path.read_text())['facts']
    byfact={f['fact_id']:f for ff in facts.values() for f in ff}
    require(byfact['fact-op-precision-input-bias-current-full-temperature']['value']['maximum']==15,'changed precision bias fact')
    require(byfact['fact-op-precision-input-offset-voltage']['value']['maximum_at_25C']==100,'changed precision offset fact')
    require(byfact['fact-comparator-input-offset-voltage']['value']['maximum_full_temperature']==4,'changed comparator offset fact')
    require(byfact['fact-comparator-input-bias-current']['value']['maximum_full_temperature']==50,'changed comparator bias fact')
    nets=sorted({r['actual_identity']['actual_net'] for r in paths});traces={net:trace_net(net,ctx) for net in nets}
    rows=[{'actual_identity':r['actual_identity'],'signal_class':requirements.classify(r),'trace_net':r['actual_identity']['actual_net']} for r in paths]
    sourcepaths=[Path(__file__),Path(__file__).with_name('test_stage5_electrical.py'),Path(audit.__file__),Path(requirements.__file__),OUT/'stage4/candidate-report.json',ROOT/'design/standard/electrical-standard.json',ROOT/'design/spec/modules/oscillator.py',ROOT/'design/spec/modules/oscillator-reference.json',ROOT/'design/spec/cells/run_spice.py',ROOT/'design/architecture-278/electrical.md']+factpaths
    return {'status':'NUMERICAL CAPTURED-CIRCUIT SENSITIVITY BUDGET; all hardware qualification OPEN','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sourcepaths},
        'source_capture_assertions':capture,'crossing_count':len(rows),'crossings':rows,'bounded_active_endpoint_traces':traces,'retained_manufacturer_facts':facts,
        'budgets':budgets(),'characterization':characterization(),'nine_shared_aggregate_budgets':json.loads((OUT/'stage4/candidate-report.json').read_text())['candidate']['shared_aggregate_capacitance'],
        'unknowns':{'OPA4196_bias_A':None,'OPA4196_offset_V':None,'OPA4196_validated_dynamic_model':None,'actual_driver_output_impedance_ohm':None,'BAT54_hot_leakage_A':None,'project12V_switch_ron_ohm':None,'actual_route_RLC':None,'assembled_phase_margin_deg':None,'actual_HC5V_VOH_VOL_and1nFdelay':None,'AS3340_sync_input_model':None},
        'limits':'All numerical bounds retain stated source conditions.1nF diagnostic load is not assembled stability.300mm is not physical failure threshold. Existing canonical envelopes unchanged; no architecture selected.',
        'native':'NOT RUN','simulation':'NOT RUN','bench':'NOT RUN'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();dest=OUT/'stage5-electrical-report.json';text=json.dumps(r,indent=2,sort_keys=True)+'\n'
    if args.check:require(dest.read_text()==text,'stale stage5 electrical report')
    else:dest.write_text(text)
    print('Stage5 numerical budgets:',len(r['budgets']),'classes;',r['crossing_count'],'crossings;simulation/native/bench NOT RUN')
