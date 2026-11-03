"""TI OPAx196 archive inspection and closed-form passive budgets; never simulation."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import zipfile
import stage5_electrical as prior

ROOT,OUT=prior.ROOT,prior.OUT/'stage6'
URL='https://www.ti.com/lit/zip/SBOMAF9'
ARCHIVE_SHA='9c264813a36536f743c166b6a101904b76ed08f049f2eeb127a438cc6e8ccdf5'
LIB_SHA='31142f5dbd71b758d887ee8a411692fc4c1309c8f47100af4ba5bed7e173c430'
CACHE=ROOT/'.circuit-cache/sources/architecture278-SBOMAF9/SBOMAF9.zip'

def need(ok,msg):
    if not ok:raise ValueError(msg)

def spice_number(token):
    match=re.fullmatch(r'([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[Ee][+-]?[0-9]+)?)([A-Za-z]*)',token)
    need(match is not None,'unrecognized model scalar')
    scales={'':1,'P':1e-12,'N':1e-9,'U':1e-6,'M':1e-3,'K':1e3,'MEG':1e6,'G':1e9,'T':1e12,'F':1e-15}
    need(match.group(2).upper() in scales,'unsupported model suffix')
    return float(match.group(1))*scales[match.group(2).upper()]

def extract_parameters(lines):
    text='\n'.join(lines)
    def match(pattern):
        hits=re.findall(pattern,text,re.M);need(len(hits)==1,'ambiguous/missing model parameter '+pattern)
        return spice_number(hits[0])
    def element(name):return match(r'^'+re.escape(name)+r'\s+.*?\s+(\S+)\s*$')
    cm=element('C_C_COM0');need(cm==element('C_C_COM1'),'asymmetric model common capacitance')
    ri=element('R_R1');need(ri==element('R_R2'),'asymmetric input resistance')
    rc=element('R_R3');need(rc==element('R_R4'),'asymmetric common resistance')
    dc=match(r'^\.SUBCKT VOS_DRIFT_OPAx196 .*?DC=(\S+)')
    drift=match(r'^\.SUBCKT VOS_DRIFT_OPAx196 .*?DRIFT=(\S+)')
    need(dc==match(r'^X_U4 .*?DC=(\S+)'),'Vos instance/default mismatch')
    need(drift==match(r'^\+\s+DRIFT=(\S+)'),'drift instance/default mismatch')
    return {'I_I_B_A':element('I_I_B'),'I_I_OS_A':element('I_I_OS'),'I_I_Q_A':element('I_I_Q'),
        'Vos_internal_DC_V':dc,'Vos_internal_drift_V_per_C':drift,'Vos_reference_temperature_C':match(r'^E1 VOS\+ VOS- .*?TEMP-([0-9]+)\)'),
        'C_common_each_F':cm,'C_differential_F':element('C_C_DIFF'),'R_common_each_ohm':rc,'R_differential_ohm':element('R_R_DIFF'),'R_input_each_ohm':ri}

def validate_evidence(evidence):
    need(evidence['archive_sha256']==ARCHIVE_SHA and evidence['member_sha256']==LIB_SHA,'unreviewed model identity')
    need(evidence['subcircuit_pin_order']==['IN+','IN-','VCC','VEE','OUT'],'wrong model interface')
    need(extract_parameters([x['text'] for x in evidence['inspected_line_evidence']])==evidence['parameters'],'offline parameter/evidence inconsistency')

def inspect_archive(path):
    data=Path(path).read_bytes();need(hashlib.sha256(data).hexdigest()==ARCHIVE_SHA,'different TI archive; review new source, never repin blindly')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names=z.namelist();need(len(names)==len(set(names)),'duplicate archive members')
        need('OPAx196.LIB' in names,'missing exact model member')
        lib=z.read('OPAx196.LIB');need(hashlib.sha256(lib).hexdigest()==LIB_SHA,'model member hash mismatch')
        lines=lib.decode('ascii').splitlines();text='\n'.join(lines)
        m=re.search(r'^\.SUBCKT OPAx196 (.+)$',text,re.M);need(m is not None,'missing model entry')
        pins=m.group(1).split();need(pins==['IN+','IN-','VCC','VEE','OUT'],'wrong model pin order')
        need('OPA196, OPA2196, OPA4196' in text,'quad family applicability not documented')
        tokens=['Date:','Model Version:','model is used for','.SUBCKT OPAx196','C_C_COM0','C_C_COM1','C_C_DIFF','I_I_B ','I_I_OS ','I_I_Q ','R_R1 ','R_R2 ','R_R3 ','R_R4 ','R_R_DIFF','X_U4 ','+  DRIFT=','SUBCKT VOS_DRIFT','VALUE={DC+POL']
        return {'url':URL,'archive_sha256':ARCHIVE_SHA,'archive_bytes':len(data),'member':'OPAx196.LIB','member_sha256':LIB_SHA,'member_bytes':len(lib),
            'member_inventory':[{'name':n,'bytes':len(z.read(n)),'sha256':hashlib.sha256(z.read(n)).hexdigest()}for n in names if not n.endswith('/')],
            'model_family':['OPA196','OPA2196','OPA4196'],'version':'Final1.5','release_date':'29AUG2022','subcircuit':'OPAx196','subcircuit_pin_order':pins,
            'inspected_line_evidence':[{'line':i,'text':line.strip()} for i,line in enumerate(lines,1) if any(t in line for t in tokens)],
            'declared_model_capabilities':['Aol/phase withRL/CL','GBW','CMRR/PSRR','Zid/Zic','frequency-dependentZo','supply/outputcurrent','noise','swing/currentlimit','settling/overshoot/slew','overload','bias/offset/offsetdrift/commonmode','ESD cells'],
            'dialect_features':['PSpice PARAMS','VALUE/IF/LIMIT/TABLE/PWR behavioral expressions','VSWITCH','temperature expression TEMP','R_NOISELESS RES T_ABS=-273.15'],
            'availability':'AVAILABLE manufacturer family model; no execution or simulator validation',
            'parameters':extract_parameters(lines),
            'parameter_scope':'inspected internal macro-model element values only; no guaranteed device bounds or solved terminal behavior',
            'limitations':['TI as-is model with no warranty; model may change.','Per-channel generic family model does not qualify package crosstalk/thermal coupling, fittedPCB, contacts, tolerance or fault states.','Source availability does not establish simulator dialect compatibility, convergence, regression against TI reference cases or exact-run native admission.','No simulator,model testcircuit,native tool or model executable launched.']}

def loaded_wiper(x,rpot,rseries,rf,vlo,vhi):
    r=rseries+rpot*x*(1-x);ideal=vlo+(vhi-vlo)*x;loaded=ideal*rf/(rf+r)
    return {'position':x,'thevenin_with_series_ohm':r,'ideal_V':ideal,'loaded_V':loaded,'error_V':loaded-ideal}

def peak_wiper(rpot,rseries,rf,vlo,vhi):
    """Stationary points on the two monotonic-voltage halves, symmetric/0..V pots."""
    need(rpot>0 and rseries>0 and rf>0 and vhi>0 and vlo in (0,-vhi),'unsupported peak domain')
    def derivative(x):
        r=rseries+rpot*x*(1-x);rp=rpot*(1-2*x);v=vlo+(vhi-vlo)*x;vp=vhi-vlo
        return vp*r*(rf+r)+v*rp*rf
    points=[0,.5,1]
    for lo,hi in ((0,.5),(.5,1)):
        if derivative(lo)*derivative(hi)>=0:continue
        for _ in range(80):
            mid=(lo+hi)/2
            if derivative(lo)*derivative(mid)<=0:hi=mid
            else:lo=mid
        points.append((lo+hi)/2)
    return max((loaded_wiper(x,rpot,rseries,rf,vlo,vhi) for x in points),key=lambda r:abs(r['error_V']))

def two_node_rc(rpot,x,rseries,rf,cwire,cfilter):
    """Exact passive transfer Vsense/Videal=1/(a*s²+b*s+c), ideal reference source."""
    need(rpot>0 and 0<=x<=1 and rseries>0 and rf>0 and cwire>=0 and cfilter>0,'invalid passive values')
    r0=rpot*x*(1-x);a=r0*rseries*cwire*cfilter;b=(r0+rseries)*cfilter+r0*(1+rseries/rf)*cwire;c=1+(r0+rseries)/rf
    if a==0:taus=[b/c]
    else:
        disc=b*b-4*a*c;need(disc>=0,'unexpected nonreal passive poles');q=-.5*(b+math.sqrt(disc));taus=sorted([-a/q,-q/c],reverse=True)
    return {'numerator':1,'denominator_s2_s_1':[a,b,c],'DC_gain':1/c,'time_constants_s':taus,'pole_Hz':[1/(2*math.pi*t)for t in taus],
            'scope':'analytical passive network; no amplifier dynamics, finite reference impedance or extracted parasitics; no simulation'}

def model_binding(ctx):
    pinmap={1:['3','2','4','11','1'],2:['5','6','4','11','7'],3:['10','9','4','11','8'],4:['12','13','4','11','14']};out=[]
    for p in ctx['rows']:
        if p['symbol'].split(':')[-1]!='OPA4196IDR' or p['unit'] not in pinmap:continue
        pins=pinmap[p['unit']];nodes={}
        for name,pin in zip(('IN+','IN-','VCC','VEE','OUT'),pins):
            source,net=ctx['bypin'][p['ref'],pin];need(source['ref']==p['ref'],'wrong package');need(source['pin_types'].get(pin)==('output' if name=='OUT' else 'input' if name.startswith('IN') else 'power_in'),'wrong physical pin role');nodes[name]={'pin':pin,'net':net}
        need(nodes['VCC']['net']=='+12V' and nodes['VEE']['net']=='-12V','unexpected amplifier supply')
        out.append({'instance':p['instance'],'ref':p['ref'],'unit':p['unit'],'MPN':'OPA4196IDR','symbol':p['symbol'],'logical_key':p['attributes'].get('LogicalCellKey',p['key']),'macro':'OPAx196','macro_pin_binding':nodes,'status':'source pin binding only; no instantiated simulation deck'})
    return out

def build():
    evidence=json.loads((OUT/'opax196-evidence.json').read_text());validate_evidence(evidence)
    ctx=prior.source_context();capture=prior.assert_capture(ctx);p=evidence['parameters'];binding=model_binding(ctx)
    peaks={name:peak_wiper(120000,1010,9.9e6,lo,5.025) for name,lo in (('bipolar_TUNE_FINE',-5.025),('unipolar_PW',0))}
    rc={f'x{x}_Cwire{cw:g}':two_node_rc(120000,x,1010,9.9e6,cw,10.5e-9) for x in (0,.25,.5,.75,1) for cw in (0,100e-12,1e-9)}
    r=prior.parallel(4010,9.9e6);internal_offset={str(t):p['Vos_internal_DC_V']+p['Vos_internal_drift_V_per_C']*(t-p['Vos_reference_temperature_C'])for t in (-40,25,27,85)}
    analytical={'position_correlated_control_loading':{'planning_Rpot_ohm':120000,'planning_Rseries_ohm':1010,'planning_Rfail_ohm':9.9e6,'reference_extreme_V':5.025,'peaks':peaks,'old_independent_bound_V':prior.budgets()['control_wiper']['fail_load_error_conservative_bound_V'],
        'meaning':'tighter position-correlated ideal-reference DC calculation; sourceR,bias,leakage,offset,temperature and calibration remain separate; not guaranteed assembled error'},
        'two_node_control_RC':rc,
        'model_parameter_sensitivities':{'FM_receiver_external_passive_R_ohm':r,'I_I_B_contribution_input_V':r*p['I_I_B_A'],'I_I_OS_contribution_input_V':r*p['I_I_OS_A'],
            'internal_Vos_parameter_vs_temperature_V':internal_offset,'nominal_gain2_times_internal27C_Vos_V':2*p['Vos_internal_DC_V'],
            'Cmatrix_internal_F':[[p['C_common_each_F']+p['C_differential_F'],-p['C_differential_F']],[-p['C_differential_F'],p['C_common_each_F']+p['C_differential_F']]],
            'same_voltage_both_inputs_cap_each_F':p['C_common_each_F'],'opposite_input_held_cap_each_F':p['C_common_each_F']+p['C_differential_F'],
            'scope':'isolated internal parameter contributions only; two current sources are on different nodes, not summed as pinIB. Input capacitance depends on moving opposite input andMID. Values do not replace Stage5 unknown manufacturerlimits or prove closedloopbehavior.'},
        'return_budget_reconciliation':{'existing_proposed_return_V':.0002,'planning_current_A':.7045,'required_resistance_for200uV_ohm':.0002/.7045,'historical_resistance_goal_ohm':.0005,'historical_drop_V':.7045*.0005,
            'collective_pitch_proposal_V':1/1200,'remaining_after_historical_drop_V':1/1200-.7045*.0005,'approval':'PROPOSAL NOT APPROVED; no resistance/voltage measured'},
        'unchanged_dependency':'Nine direct sharedcap budgets andfive1k/100nF switchingloads unchanged; TI OPAx196 model doesnotbind OPA4197 sharedreference drivers or AS3340/HC receiver models.'}
    paths=[Path(__file__),Path(__file__).with_name('test_stage6_electrical.py'),OUT/'opax196-evidence.json',Path(prior.__file__),prior.OUT/'stage5-electrical-report.json',ROOT/'design/spec/modules/oscillator.py',ROOT/'design/standard/electrical-standard.json']
    return {'status':'MANUFACTURER MODEL AVAILABLE; SOURCE INSPECTED ONLY; NO SIMULATION/NATIVE ADMISSION','source_sha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in paths},
        'model_evidence':evidence,'candidate_OPA4196_channels':binding,'capture_assertion_count':len(capture),'analytical_refinement':analytical,
        'dependency_update':{'previous':'Stage5 lacked an acquired validated OPA4196 dynamic model','now':'Official OPAx196 family macro acquired and inspected; exact quad family applicability documented','still_open':['simulator dialect compatibility','manufacturer testbench reproduction','model behavior validation for actualrails/load/temperature','closedloopactualcircuit stability','package/sharedsupply coupling','route parasitics andrealreturn','worstcase manufacturerdata','separate exactrunadmission fornative work']},
        'reproduction':{'download_url':URL,'ignored_archive':str(CACHE.relative_to(ROOT)),'verify_command':'python3 scripts/architecture278/implementation/stage6_electrical.py --verify-archive .circuit-cache/sources/architecture278-SBOMAF9/SBOMAF9.zip','offline_check':'python3 scripts/architecture278/implementation/stage6_electrical.py --check','note':'Offline reproduction uses committed inspected evidence; --verify-archive independently rechecks exact rawbytes/membermetadata. Missing rawcache is not fabricated availability.'},
        'simulator_execution':'NOT RUN','native':'NOT RUN','bench':'NOT RUN','accepted':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--verify-archive',type=Path);ap.add_argument('--write-evidence',type=Path);args=ap.parse_args()
    if args.write_evidence:
        (OUT/'opax196-evidence.json').write_text(json.dumps(inspect_archive(args.write_evidence),indent=2,sort_keys=True)+'\n');print('TI source evidence written; nothing executed')
    elif args.verify_archive:
        expected=json.loads((OUT/'opax196-evidence.json').read_text());need(inspect_archive(args.verify_archive)==expected,'source evidence differs');print('Exact TI archive/member/source inspection verified; nothing executed')
    else:
        report=build();data=json.dumps(report,indent=2,sort_keys=True)+'\n';dest=OUT/'electrical-report.json'
        if args.check:need(dest.read_text()==data,'stale stage6 electrical report')
        else:dest.write_text(data)
        print('Stage6 source model bindings',len(report['candidate_OPA4196_channels']),'channels;passive analytical refinement only;simulation/native NOT RUN')
