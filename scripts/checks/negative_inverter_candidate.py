#!/usr/bin/env python3
"""Unselected inverter: exact DC corners and explicit source-applicability gaps."""
import argparse
from fractions import Fraction as F
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    'spec':'design/power/negative-inverter-candidate.json',
    'sources':'design/power/negative-inverter-candidate-sources.json',
    'supply':'design/power/supply-architecture-input.json',
    'capture':'design/power/monitor-permit-draft.json',
    'current':'design/power/monitor-permit-current-report.json',
    'owner_facts':'.claude/skills/component-monitor-permit-candidates/facts.json',
    'owner_sources':'.claude/skills/component-monitor-permit-candidates/sources.json',
}
REPORT = 'design/power/negative-inverter-candidate-report.json'
CURRENT_INPUTS = {
 '.claude/skills/component-monitor-permit-candidates/facts.json',
 '.claude/skills/component-monitor-permit-candidates/manifest.json',
 '.claude/skills/component-monitor-permit-candidates/sources.json',
 'design/power/monitor-permit-draft.json',
 'design/power/monitor-permit-parts.json',
 'design/power/supply-architecture-input.json',
 'scripts/checks/monitor_permit_behavior.py',
 'scripts/checks/monitor_permit_current.py',
}
EXPECTED_OBSERVATIONS = {'opa': {'mpn': 'OPA388IDBVR',
         'pins': {'1': 'OUT', '2': 'V-', '3': '+IN', '4': '-IN', '5': 'V+'},
         'recommended_supply_V': [2.5, 5.5],
         'specified_temperature_C': [-40, 125],
         'input_common_mode_absolute_offsets_V': [-0.5, 0.5],
         'differential_absolute_supply_plus_V': 0.2,
         'input_absolute_current_A': 0.01,
         'offset_full_temperature_max_V': 7.5e-06,
         'bias_full_temperature_max_A': 7e-10,
         'aol_full_temperature_10k_min_dB': 120,
         'iq_5p5V_full_temperature_max_A': 0.0026,
         'iq_2p5V_full_temperature_max_A': 0.0024,
         'dbv_RthetaJA_C_per_W': 145.7,
         'common_conditions': 'VCM=VOUT=VS/2; RLOAD=10kohm connected to VS/2; TA=25C unless '
                              'otherwise noted.',
         'offset_conditions': 'OPA388, -40..125C, VS=2.5..5.5V; common VCM/output/load conditions '
                              'retained.',
         'bias_conditions': 'OPA388, RIN=100kohm, -40..125C; common VCM/output/load conditions '
                            'retained.',
         'aol_conditions': 'OPA388, -40..125C, RLOAD=10kohm; V-+0.15V<VOUT<V+-0.15V; common '
                           'VCM/load reference retained.',
         'iq_conditions': 'VS=5.5V or 2.5V endpoint rows, IO=0A, -40..125C; no interpolation to '
                          'actual 4.81..5.2V.',
         'cmrr_full_temperature_rows': [{'supply_V': 2.5,
                                         'min_dB': 114,
                                         'common_mode_offsets_V': [0, 0.1]},
                                        {'supply_V': 5.5,
                                         'min_dB': 124,
                                         'common_mode_offsets_V': [-0.05, 0.1]}],
         'typical_only': {'slew_V_per_us': 5,
                          'settling_0p01percent_s': 2e-06,
                          'overload_recovery_s': 1e-05,
                          'short_circuit_at_5p5V_A': 0.06,
                          'short_circuit_at_2p5V_A': 0.03},
         'maximum_startup_or_settling_s': None},
 'tps': {'mpn': 'TPS37044MJOFDDFRQ1',
         'sense2_pin': '3',
         'nominal_V': 0.4,
         'window_fraction': 0.07,
         'accuracy_fraction': 0.016,
         'hysteresis_fraction': [0.011, 0.017],
         'sense_absolute_V': [-0.3, 6.5],
         'sense_recommended_V': [0, 6],
         'adjustable_input_current_max_A': 3.5e-07,
         'input_current_condition': 'VSENSEx=5.5V; not a uniform bound at the candidate 0.4V node.',
         'detect_max_s': 1e-05,
         'timing_conditions': {'overdrive_fraction': 0.1,
                               'fixed_reset_delay_s': 0.01,
                               'fixed_reset_delay_greater_than_s': 0.001,
                               'pullup_ohm': 10000,
                               'load_F': 1e-11,
                               'supply_V': [1.7, 6],
                               'temperature_C': [-40, 125]},
         'startup_nominal_s': 0.001,
         'startup_max_s': None},
 'resistor': {'tolerance_fraction': 0.001,
              'tcr_abs_per_C': 2.5e-05,
              'rated_power_W': 0.1,
              'rated_power_temperature_C': 70,
              'continuous_voltage_V': 75,
              'temperature_C': [-55, 155],
              'power_voltage_scope': '75V maximum continuous voltage at full rated power; no '
                                     'full-temperature derating curve retained.'}}
SOURCE_HASHES = {
 'OPA388IDBVR':'bfaa584834295abba9cab4c66cda702ada12def5d50e49b1beb0d7444f0775e7',
 'RT0603BRD07150KL':'08a1992f43928ac375b2c9dd372c2d909e60ad32a3e82b02cacec2a4a878fb71',
 'RT0603BRD071KL':'3d889ebb14494a772b7a2b4e5e151d89a6faabbdc7856454ffa31cafcdb7e0fd',
 'RT0603BRD074K99L':'005fe939225cedc0f6960c2269d427f19b411a5738d5b97c5b6a92b60a90a186',
 'RT0603BRD07150RL':'c4983015d73907a7770f61723c7a7e59ce84d833d0430fb32177494874bf3b21',
 'supervisor':'cbe435f8182a08c0249f54d79814bd692040febe79411ab58f98402b061f5028',
}
TOPOLOGY = [
 ('RN1','RT0603BRD07150KL',150000,['VN','RN_MID']),
 ('RN2','RT0603BRD071KL',1000,['RN_MID','NEG_SUM']),
 ('RF','RT0603BRD074K99L',4990,['NEG_MAG','NEG_SUM']),
 ('RG','RT0603BRD07150RL',150,['NEG_SUM','AGND']),
]


def number(x):
    if isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x):
        raise ValueError('finite numeric operand required')
    return F(str(x))


def display(x, upper=False):
    y=float(x)
    if not math.isfinite(y): raise ValueError('float overflow')
    if (F(y)<x if upper else F(y)>x): y=math.nextafter(y,math.inf if upper else -math.inf)
    return y


def interval(values):
    return [display(min(values)),display(max(values),True)]


def keyed(rows,key):
    d={r[key]:r for r in rows}
    if len(d)!=len(rows): raise ValueError('duplicate '+key)
    return d


def validate(data):
    s=data['spec']; evidence=data['sources']; obs=evidence['observations']
    if any(s[k] is not False for k in ('selected','qualification_accepted','canonical_protection_implemented')):
        raise ValueError('no candidate admission')
    if json.dumps(obs,sort_keys=True,allow_nan=False)!=json.dumps(EXPECTED_OBSERVATIONS,sort_keys=True,allow_nan=False):
        raise ValueError('reviewed primary value/condition changed')
    sources=keyed(evidence['sources'],'id')
    if set(sources)!=set(SOURCE_HASHES): raise ValueError('required evidence closure differs')
    for k,h in SOURCE_HASHES.items():
        r=sources[k]
        if (r['sha256']!=h or r['availability']!='AVAILABLE' or r['authority']!='MANUFACTURER_PRIMARY'
                or r['mpn']!=('TPS37044MJOFDDFRQ1' if k=='supervisor' else k)
                or type(r['bytes']) is not int or r['bytes']<=0 or not r['locators']):
            raise ValueError('source identity/retention differs')
    parts=keyed(s['resistors'],'ref')
    if set(parts)!={r[0] for r in TOPOLOGY}: raise ValueError('resistor topology differs')
    for ref,mpn,ohm,pins in TOPOLOGY:
        p=parts[ref]; source=sources[mpn]
        if (p['mpn']!=mpn or number(p['ohm'])!=ohm or p['pins']!=pins or p.get('dnp',False) is not False
                or source['resistance_ohm']!=ohm or source['tolerance_fraction']!=.001 or source['tcr_abs_per_C']!=25e-6):
            raise ValueError('exact resistor value/connection/source differs')
    if (s['amplifier_mpn']!='OPA388IDBVR' or s['amplifier_pins']!={'1':'NEG_MAG','2':'AGND','3':'AGND','4':'NEG_SUM','5':'+5V'}):
        raise ValueError('amplifier pin identity differs')
    c=s['conditions']
    if (c['resistor_reference_C']!=25 or c['resistor_temperature_C']!=[-40,125]
            or c['forced_VN_V']!=[-12.48,12.48] or c['forced_output_V']!=[0,5.2]
            or c['negative_fault_witness_V']!=-10.9):
        raise ValueError('reviewed scenario envelope changed')
    if not 0<=number(c['cold_current_sensitivity_each_A'])<=F('.001'):
        raise ValueError('sensitivity current outside 0..1mA study domain')
    bands=data['supply']['source_requirement']['required_load_voltage_magnitude_V']
    if bands['-12V']!=[11.74,12.37] or bands['+5V']!=[4.81,5.2]:
        raise ValueError('source normal band changed; reassess candidate')
    cap=keyed(data['capture']['components'],'ref')['U101']
    if cap['mpn']!='TPS37044MJOFDDFRQ1' or cap['pins']!={'1':'+5V','2':'REF_SENSE','3':None,'4':'AGND','5':'P12_SENSE','6':'P5_SENSE','7':'FAULT_N','8':'FAULT_N'}:
        raise ValueError('existing spare-channel/interface premise changed')
    interface=s['hypothetical_interface']
    if (interface['TPS_part']!='U101' or interface['SENSE2_pin']!='3' or interface['new_net']!='NEG_MAG'
            or interface['previously_unused'] is not True or interface['SENSE1_pin']!='2' or interface['future_unused_net'] is not None):
        raise ValueError('hypothetical interface differs')
    fs=keyed(data['owner_facts']['facts'],'fact_id'); os=keyed(data['owner_sources']['sources'],'source_id')
    sid='src-monitor-tps37044mjofddfrq1-datasheet'
    if os[sid]['sha256']!=SOURCE_HASHES['supervisor'] or os[sid]['availability']!='AVAILABLE':
        raise ValueError('existing supervisor source differs')
    expected={'programmed-window':{'sense1_2_nominal_V':.4,'sense3_4_nominal_V':.8,'window_fraction':.07},
              'accuracy':{'at_0p4V_fraction':.016,'at_0p8V_fraction':.01},
              'hysteresis':{'at_0p4V_min':.011,'at_0p4V_max':.017,'at_0p8V_min':.004,'at_0p8V_max':.01}}
    for suffix,value in expected.items():
        f=fs['fact-monitor-tps37044mjofddfrq1-'+suffix]
        if f['value']!=value or f['source_id']!=sid or f['verdict']!='PASS - primary-source confirmed':
            raise ValueError('supervisor source bridge differs')
    if data['current']['qualification_accepted'] is not False: raise ValueError('current report admission changed')
    for ref,mpn,units in [('U102','TLV9022DR',2),('U103','REF3433TIDBVR',1)]:
        row=data['current']['active_device_source_rows'][ref]
        if row['mpn']!=mpn or row['units_per_package']!=units or row['application_qualified'] is not False:
            raise ValueError('removed current block identity/scope changed')
    current=data['current']
    old=current['states']['both_paths_conservative_dc_screen']['conditional_dc_A']
    if set(old)!={'+5V','+12V','-12V'} or any(number(v)<0 for v in old.values()):
        raise ValueError('invalid current comparison inputs')
    if current['original_auxiliary_allowance_mA']!={'+5V':20,'+12V':20,'-12V':20}:
        raise ValueError('original auxiliary allocation changed')
    removed=number(current['reference_output_total_A'])
    if removed<0: raise ValueError('invalid reference demand')
    for ref in ('U102','U103'):
        row=current['active_device_source_rows'][ref]
        package=number(row['package_table_sum_A'])
        if package<0 or package!=number(row['table_max_A'])*row['units_per_package']:
            raise ValueError('invalid removed package current')
        removed+=package
    if removed>number(old['+5V']): raise ValueError('removed demand exceeds original ledger')
    return sources


def node(vn,vo,rn,rf,rg,injection=F(0)):
    # Prescribed output port; positive injection enters NEG_SUM.
    return (vn/rn+vo/rf+injection)/(1/rn+1/rf+1/rg)


def factors(tolerance,tcr,reference,temperatures):
    t,k,r=map(number,(tolerance,tcr,reference)); temps=list(map(number,temperatures))
    if len(temps)!=2 or temps[0]>temps[1] or k<0 or not 0<=t<1: raise ValueError('invalid resistor condition')
    drift=k*max(abs(x-r) for x in temps)
    if drift>=1: raise ValueError('nonpositive resistance corner')
    return (1-t)*(1-drift),(1+t)*(1+drift)


def passive_screen(low,high,rg0,leak):
    corners=list(itertools.product((low,high),repeat=4)); forced=[]; cold=[]
    drops={k:[] for k in ('RN1','RN2','RF','RG')}; currents={k:[] for k in drops}
    for a,b,c,d in corners:
        r1,r2,rf,rg=150000*a,1000*b,4990*c,rg0*d;rn=r1+r2
        for vn,vo,sign in itertools.product((F('-12.48'),F('12.48')),(F(0),F('5.2')),(-1,1)):
            vs=node(vn,vo,rn,rf,rg,sign*leak)
            forced.append({'VN':vn,'OUT':vo,'SUM':vs})
            values={'RN1':(vn-vs)*r1/rn,'RN2':(vn-vs)*r2/rn,'RF':vo-vs,'RG':vs}
            for k,r in zip(drops,(r1,r2,rf,rg)):
                drops[k].append(values[k]);currents[k].append(values[k]/r)
        for vn,si,so in itertools.product((F('-12.48'),F('12.48')),(-1,1),(-1,1)):
            # Two independent sensitivity currents; OUT has no other branch.
            vs=(vn/rn+(si+so)*leak)/(1/rn+1/rg);vo=vs+so*leak*rf
            cold.append((vs,vo))
    # Voltage extrema are linear-fractional in each positive resistance and
    # affine in forced ports/currents. Corners enclose every point in the box.
    # Power is NOT assumed corner-extremal: bound Vdrop^2/R using interval
    # voltage extrema and the independent minimum resistance.
    powers={k:display(max(map(abs,drops[k]))**2/(r*low),True) for k,r in zip(drops,(150000,1000,4990,rg0))}
    return {'RG_nominal_ohm':rg0,'forced_sum_V':interval([r['SUM'] for r in forced]),
            'forced_sum_inside_cold_differential_0p2V':max(abs(r['SUM']) for r in forced)<F('.2'),
            'forced_output_cases':[{'VN_V':float(vn),'OUT_V':float(vo),'sum_V':interval([r['SUM'] for r in forced if r['VN']==vn and r['OUT']==vo])} for vn,vo in itertools.product((F('-12.48'),F('12.48')),(F(0),F('5.2')))],
            'forced_branch_current_A':{k:interval(v) for k,v in currents.items()},
            'forced_branch_voltage_V':{k:interval(v) for k,v in drops.items()},
            'forced_branch_power_upper_W':powers,
            'cold_highZ_sum_V':interval([v[0] for v in cold]),'cold_highZ_output_V':interval([v[1] for v in cold]),
            'scope':'Prescribed ports and current sensitivity only; cold high-Z excludes internal output clamps. Absolute-stress screen is not operation or survival qualification. Branch currents do not bound amplifier current into an externally forced/shorted OUT port.'}


def calculate(data):
    validate(data);s=data['spec'];obs=data['sources']['observations'];c=s['conditions']
    low,high=factors(obs['resistor']['tolerance_fraction'],obs['resistor']['tcr_abs_per_C'],c['resistor_reference_C'],c['resistor_temperature_C'])
    gain=F(4990,151000);glo= gain*low/high;ghi=gain*high/low
    nlo,nhi=map(number,data['supply']['source_requirement']['required_load_voltage_magnitude_V']['-12V'])
    t=obs['tps'];nom,w,a,h=map(number,(t['nominal_V'],t['window_fraction'],t['accuracy_fraction'],t['hysteresis_fraction'][1]))
    uvlo=nom*(1-w)*(1-a);uvhi=nom*(1-w)*(1+a);ovlo=nom*(1+w)*(1-a);ovhi=nom*(1+w)*(1+a)
    recover_lo=uvhi*(1+h);recover_hi=ovlo*(1-h)
    margins=(nlo*glo-recover_lo,recover_hi-nhi*ghi);budget=min(margins)
    if budget<=0: raise ValueError('normal band has no strict total-error allowance')
    ng=1+ghi+F(4990,150)*high/low
    # Source-point illustrations, not an application maximum: retain each
    # table's different common-mode, supply and loading conditions in output.
    illustrative_offset=number(obs['opa']['offset_full_temperature_max_V'])*ng
    illustrative_bias=number(obs['opa']['bias_full_temperature_max_A'])*4990*high
    normal_load=nhi/(151000*low)
    fault=abs(number(c['negative_fault_witness_V']));fault_high=fault*ghi+budget
    current=data['current'];old=current['states']['both_paths_conservative_dc_screen']['conditional_dc_A']
    old_removed=number(current['reference_output_total_A'])+number(current['active_device_source_rows']['U102']['package_table_sum_A'])+number(current['active_device_source_rows']['U103']['package_table_sum_A'])
    assumed_added=number(obs['opa']['iq_5p5V_full_temperature_max_A'])+normal_load+number(t['adjustable_input_current_max_A'])
    new5=number(old['+5V'])-old_removed+assumed_added
    return {'status':'UNSELECTED CONDITIONED DC STUDY; NO NATIVE CAPTURE OR PROTECTION ADMISSION',
      'selected':False,'qualification_accepted':False,'canonical_protection_implemented':False,
      'normal':{'negative_magnitude_V':[float(nlo),float(nhi)],'gain':interval([glo,ghi]),'ideal_output_V':interval([nlo*glo,nhi*ghi]),
          'strict_common_static_recovery_window_V':[display(recover_lo,True),display(recover_hi)],
          'output_error_margin_lower_V':[display(x) for x in margins],
          'strict_total_additive_output_error_budget_V':display(budget),'exact_budget_fraction':str(budget),
          'noise_gain_upper':display(ng,True),'offset_only_input_budget_V':display(budget/ng),
          'bias_only_input_current_budget_A':display(budget/(4990*high)),
          'borrowed_source_point_offset_contribution_V':display(illustrative_offset,True),
          'borrowed_source_point_bias_contribution_V':display(illustrative_bias,True),
          'actual_joint_error_max_V':None,'ideal_feedback_output_source_current_upper_A':display(normal_load,True),
          'source_10k_to_midsupply_load_sink_current_at_candidate_output_A':interval([
              (number(data['supply']['source_requirement']['required_load_voltage_magnitude_V']['+5V'][0])/2-nhi*ghi)/10000,
              (number(data['supply']['source_requirement']['required_load_voltage_magnitude_V']['+5V'][1])/2-nlo*glo)/10000]),
          'conditions':'Strict |total additive output error| below budget; includes offset, bias, CMRR, finite gain, supply/load effects, noise and transients if claimed. No such total bound is established. Normal linear calculation assumes closed-loop action.'},
      'static_trip_magnitude_envelopes_at_error_budget_closure_V':{
          'UV':interval([(uvlo-budget)/ghi,(uvhi+budget)/glo]),'OV':interval([(ovlo-budget)/ghi,(ovhi+budget)/glo])},
      'negative_fault_witness':{'VN_V':float(-fault),'output_upper_with_budget_closure_V':display(fault_high,True),
          'lowest_UV_trip_V':display(uvlo),'conditional_below_every_UV_trip':fault_high<uvlo,
          'minimum_UV_overdrive_fraction':display((uvlo-fault_high)/uvlo),
          'at_least_10percent_UV_overdrive_all_corners':fault_high<=F('.9')*uvlo,
          'maximum_total_detection_s':None,'condition':'The same hypothetical additive-error bound is additionally assumed at this fault point; normal-band compatibility does not prove fault-point error.'},
      'outside_normal_band_no_trip_countermodel':{
          'VN_V':-12.48,'nominal_ideal_output_V':display(F('12.48')*gain,True),
          'nominal_UV_OV_trip_V':[display(nom*(1-w)),display(nom*(1+w),True)],
          'inside_nominal_trip_window':nom*(1-w)<F('12.48')*gain<nom*(1+w),
          'scope':'Zero-error nominal DC with previously released reset; outside the project normal band but no negative-channel trip. Not a measured trajectory or a waiver of fault coverage.'},
      'ten_percent_overdrive_necessary_magnitude_boundaries_V':{
          'UV_at_most':display((F('.9')*uvlo-budget)/ghi),
          'OV_at_least':display((F('1.1')*ovhi+budget)/glo,True),
          'scope':'Geometric margin only; the table test is exactly 10% and no monotonic timing guarantee is inferred for larger margins. Amplifier timing, valid supply, reset load and other channel remain separate.'},
      'passive_ports':passive_screen(low,high,150,number(c['cold_current_sensitivity_each_A'])),
      'rejected_RG_1k_countermodel':passive_screen(low,high,1000,number(c['cold_current_sensitivity_each_A'])),
      'port_state_coverage':[
          {'state':'Normal -12 rail, +5 valid, AGND intact','result':'Conditional linear DC only; actual joint error, output loading and compensation unproved.'},
          {'state':'Both VN polarities, output externally held LOW or HIGH','result':'Passive KCL screen includes RF backfeed. Output holding source also contends with the amplifier; amplifier drive/short-circuit current is not bounded by these resistor branch currents. No device output-state guarantee.'},
          {'state':'Cold amplifier, TPS powered or cold, output high impedance','result':'Two independent +/- current sensitivities only; actual TPS/OPA cold leakage and output clamps remain UNSOURCED.'},
          {'state':'Partial supply or reversed VN, startup/collapse/recovery','result':'Forced-port screen is not a semiconductor trajectory. A reversed VN demands a negative linear output and instead invokes unqualified saturation/recovery.'},
          {'state':'OUT forced below -0.3 V','result':'Direct TPS input absolute-rating conflict; RG does not isolate NEG_MAG from TPS. No bound excludes this trajectory.'},
          {'state':'Local AGND open or return lost','result':'AGND-relative assumptions fail; no independent observable or ground-loss qualification.'}],
      'hypothetical_current_comparison':{
          'old_conditional_both_paths_A':old,'removed_reference_and_comparator_5V_A':display(old_removed,True),
          'borrowed_OPA_IQ_plus_ideal_feedback_and_TPS_load_A':display(assumed_added,True),
          'new_conditional_5V_A':display(new5,True),'new_conditional_negative_rail_A':display(normal_load,True),
          'positive_12V_unchanged_A':old['+12V'],'original_auxiliary_allowance_mA':current['original_auxiliary_allowance_mA'],
          'application_qualified':False,'dynamic_current_max_A':None,
          'scope':'Arithmetic substitution only: removes all old REF output demand, REF IQ and dual comparator IQ once, replaces old negative divider load with ideal inverter load. Retains all other conservative old branches. Borrows OPA IQ at 5.5V/IO0 and TPS input current at 5.5V as assumptions, not actual 4.81..5.2V/0.4V guarantees. Zero other leakage; no new bypass/inrush/return/clamp current bound.'},
      'source_observations':obs,'sensitivity_current_each_A':c['cold_current_sensitivity_each_A'],
      'thermal_scope':'Passive power upper bounds apply only to the stated forced-port box; 0.1W is rated at 70C. Full-temperature derating and installed temperatures are not established. DBV RthetaJA is a source test-board metric, not an installed thermal bound.',
      'native_dynamic_bench':'NOT RUN: unselected analytical study; no vendor IC model or native assembly captured.',
      'open_gates':s['open_gates']}


def snapshot(root=ROOT):
    paths=sorted(set(INPUTS.values()) | CURRENT_INPUTS | {'scripts/checks/negative_inverter_candidate.py'})
    return {p:(root/p).read_bytes() for p in paths}


def verify_unchanged(frozen,root=ROOT):
    for p,b in frozen.items():
        if (root/p).read_bytes()!=b: raise ValueError('source changed during evaluation: '+p)


def build(frozen):
    data={k:json.loads(frozen[p]) for k,p in INPUTS.items()}
    declared=data['current']['input_sha256']
    if set(declared)!=CURRENT_INPUTS or any(hashlib.sha256(frozen[p]).hexdigest()!=h for p,h in declared.items()):
        raise ValueError('current report is stale or dependency closure differs')
    result=calculate(data)
    result['input_sha256']={p:hashlib.sha256(b).hexdigest() for p,b in frozen.items()}
    return result


def run(check=False,verify_retained=False):
    frozen=snapshot();result=build(frozen)
    if verify_retained:
        for r in json.loads(frozen[INPUTS['sources']])['sources']:
            b=(ROOT/r['file']).read_bytes()
            if not b.startswith(b'%PDF-') or len(b)!=r['bytes'] or hashlib.sha256(b).hexdigest()!=r['sha256']:
                raise ValueError('retained primary bytes differ: '+r['id'])
    verify_unchanged(frozen)
    text=json.dumps(result,indent=2,allow_nan=False)+'\n';path=ROOT/REPORT
    if check:
        if path.read_text()!=text: raise ValueError('candidate report drift')
    else:path.write_text(text)
    verify_unchanged(frozen)
    print('PASS: unselected inverter arithmetic/source closure; actual error, timing, current and protection qualification remain open')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--verify-retained',action='store_true');a=p.parse_args();run(a.check,a.verify_retained)
