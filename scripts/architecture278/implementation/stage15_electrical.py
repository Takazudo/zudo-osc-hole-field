"""Candidate LT5400 ratio improvement and complete A01 error ledger, no simulation."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import stage12_budget as previous

ROOT=previous.ROOT
OUT=previous.OUT.parent/'stage15'
need=previous.need
ERRORS=('IN_buffer','remote_buffer','atten_amp','manual_amp','CV_buffer','summer','restore','output','REF_positive','REF_negative')
# No new knob optimization: fixed electrical fractions and independent stimuli.
STATES=[('CV_only',0,5,.5,.5),('IN_positive',5,0,1,.5),('IN_negative',5,0,0,.5),
        ('IN_centre',5,0,.5,.5),('manual_low',0,0,.5,0),('manual_high',0,0,.5,1),
        ('manual_quarter',0,0,.5,.25),('manual_three_quarter',0,0,.5,.75),
        ('mixed',1,1,.75,.75),('zero',0,0,.5,.5)]


def network_cases(delta):
    """Coherent element witnesses obey largest/smallest<=1+delta, no independent ratios."""
    for summer in itertools.product((1.,1.+delta),repeat=4):
        for restore in itertools.product((1.,1.+delta),repeat=2):
            yield {'ga':summer[3]/summer[0],'gm':summer[3]/summer[1],
                   'gcv':summer[3]/summer[2],'gr':restore[1]/restore[0]},list(summer),list(restore)


def all_cases(delta,tolerance):
    for network,s,r in network_cases(delta):
        for signs in itertools.product((-1,1),repeat=4):
            d=[1+tolerance*k for k in signs]
            yield {**network,'ka':d[1]/d[0],'kn':d[3]/d[2]},s,r,d


def offset_coefficients(params,a,x):
    zero=previous.transfer(0,0,a,x,**params)['out_V']
    return {key:previous.transfer(0,0,a,x,errors={key:1},**params)['out_V']-zero for key in ERRORS}


def known_bias_coefficients(params,a,x,absolute_tolerance):
    ga,gm,gr,ka=(params[k] for k in ('ga','gm','gr','ka'))
    za=1/(1/(1000+10000*a*(1-a))+1/1e7)
    zm=1/(1/(1000+100000*x*(1-x))+1/1e7)
    damp=1e7/(1e7+1000+100000*x*(1-x))
    beta=previous.old.wiper(a,10000,0,1)['sense_V']
    # Absolute resistance maxima are conservative independent sensitivities; no common temp added.
    return {'atten_noninverting':abs(gr*ga*(1+ka)*za),
            'manual_noninverting':abs(gr*gm*zm),
            'atten_inverting':abs(gr*ga)*100100,
            'summer_inverting':abs(gr)*100000*(1+absolute_tolerance),
            'restore_inverting':100000*(1+absolute_tolerance),
            'remote_inverting':abs(gr*ga*(1+ka)*beta)*10010,
            'negative_reference_inverting':abs(gr*gm*damp*(1-x))*10010,
            'output_inverting':100}


def loading_budget(inp):
    data=inp['network_loading'];rmin,rmax=data['absolute_resistance_interval_ohm']
    need((rmin,rmax)==(92500,107500),'absolute resistance loading interval')
    envelope=data['assumed_terminal_difference_envelope_V'];need(envelope==12,'declared differential envelope')
    need(data['limits']=={'any_two_pins_absolute_max_V':80,'operating_voltage_feature_V':75,
        'each_resistor_absolute_max_W':.8,'junction_absolute_max_C':150,'package_theta_JA_C_per_W':40,
        'package_theta_JC_C_per_W':10,'resistor_to_EP_typical_pF':5.5,'resistor_to_resistor_typical_pF':1.4},'primary ratings/parasitics')
    names=('R7121','R7122','R7123','R7124','R7125','R7126')
    rows=[]
    for name,vin,cv,a,x in STATES:
        maxima={r:0. for r in names}
        for p,_,_,_ in all_cases(.000125,.001):
            tr=previous.transfer(vin,cv,a,x,**p)
            summer=-tr['internal_V']/p['gr']
            potentials=(tr['atten_V'],tr['manual_V'],cv,summer,summer,tr['internal_V'])
            for ref,v in zip(names,potentials):maxima[ref]=max(maxima[ref],abs(v))
        need(all(v<=envelope for v in maxima.values()),'witness exceeds conditional linear envelope')
        branches={r:{'maximum_abs_witness_differential_V':v,'current_at_min_R_A':v/rmin,
                     'power_at_min_R_W':v*v/rmin} for r,v in maxima.items()}
        rows.append({'state':name,'branches':branches,'scope':'Ideal virtual-ground linear witness potentials; dividing by minimum absolute resistance is conservative sensitivity, not simultaneous exact extrema or total rail current.'})
    return {'resistance_interval_ohm':[rmin,rmax],'per_state_branch_allocations':rows,
        'declared_12V_differential_allocation_per_used_element':{'maximum_current_A':envelope/rmin,
            'maximum_power_W':envelope**2/rmin,'not_guaranteed_signal_or_fault_bound':True},
        'package_conditional_power_W':{'RN7101':4*envelope**2/rmin,'RN7102':2*envelope**2/rmin},
        'package_thetaJA_temperature_rise_sensitivity_C':{'RN7101':40*4*envelope**2/rmin,'RN7102':40*2*envelope**2/rmin},
        'output_loading_map':{'atten_amplifier':['R7121'],'manual_buffer':['R7122'],'CV_input_buffer':['R7123'],
            'summer_amplifier':['R7124','R7125'],'restore_amplifier':['R7126']},
        'buffer_scope':'Sum actual signed branch currents at each output once; summer output supplies both feedback R7124 and restore input R7125. Other existing loads, feedback currents, rail IQ and transient parasitics remain additional. Not a total rail current guarantee.',
        'unused_and_EP':{'RN7102_R3_R4':'Both terminals NC: zero ideal DC current/power; actual leakage, parasitic pickup and assembly faults not bounded.',
            'EP9_each':'Quiet local AGND, no internal DC resistor-terminal connection. No additional modeled DC load; displacement current and shared return coupling are not zero or quantified.'},
        'ratings':data['limits'],'rating_scope':'800mW per resistor is absolute maximum, not unrestricted operating allowance; keep junction below150C and derate with ambient using total package power. ThetaJA40C/W sensitivity presumes relevant thermal installation, not verified board performance. +/-12V node envelope would span24V any-to-any, below75V operating feature and80V absolute; faults/ESD remain unqualified.',
        'parasitic_scope':'5.5pF resistor-to-EP and1.4pF resistor-to-resistor are typical, not maximum lumped capacitor guarantees. No pole, settling/noise/stability or EMI acceptance inferred.'}


def analyze(inp):
    need(inp['device']=='LT5400AIMS8E-2#PBF' and inp['candidate_only'],'exact candidate required')
    need(inp['pin_pairs']=={'R1':['1','8'],'R2':['2','7'],'R3':['3','6'],'R4':['4','5']},'primary pin pairs')
    expected={'RN7101':{'elements':{'R1':'R7121','R2':'R7122','R3':'R7123','R4':'R7124'},'unused_elements':[],'EP9':'AGND'},
              'RN7102':{'elements':{'R1':'R7125','R2':'R7126'},'unused_elements':['R3','R4'],'EP9':'AGND'}}
    need(inp['networks']==expected,'matched mapping/unused/EP changed')
    matching=inp['matching']
    need(matching['ratio_error_25C_fraction']==.0001 and matching['ratio_error_I_full_temperature_fraction']==.000125 and
         matching['specified_temperature_C']==[-40,85] and matching['absolute_resistor_tolerance_fraction']==.075,
         'exact grade or matching conditions changed')
    need(not matching['CMRR_special_bound_used'] and not inp['calibration_changed'],'CMRR or calibration promotion')
    need(inp['criteria']=={'static_target_V':.002,'output_load_change_target_V':.001,'new_criteria_approved':False,'pitch_guarantee':False},'criteria changed')
    tol=inp['retained_discrete_pairs']['individual_tolerance_fraction'];need(tol==.001,'retained discrete tolerance')
    need(len(inp['required_unknown_terms'])>=8,'complete unknown ledger missing')
    sensitivities=inp['conditional_sensitivities']
    need(sensitivities['each_opamp_offset_V']==.0001 and sensitivities['PW_each_input_bias_A']==15e-9 and sensitivities['reference_initial_fraction']==.001,'conditioned sensitivity changed')
    temperature_rows=[]
    for label,delta in [('25C',matching['ratio_error_25C_fraction']),('I_grade_minus40_to85C',matching['ratio_error_I_full_temperature_fraction'])]:
        states=[]
        for name,vin,cv,a,x in STATES:
            baseline=previous.transfer(vin,cv,a,x)
            nominal=baseline['out_V'];ideal=baseline['ideal_control_law_V']
            values=[];coefficient_max={key:0. for key in ERRORS};bias_max={}
            witness_min=witness_max=None
            for params,s,r,d in all_cases(delta,tol):
                result=previous.transfer(vin,cv,a,x,**params)
                error=result['out_V']-ideal
                witness={'error_V':error,'params':params,'summer_normalized_elements':s,'restore_normalized_used_elements':r,'remaining_discrete_normalized_elements':d}
                if witness_min is None or error<witness_min['error_V']:witness_min=witness
                if witness_max is None or error>witness_max['error_V']:witness_max=witness
                values.append(error)
                for key,value in offset_coefficients(params,a,x).items():coefficient_max[key]=max(coefficient_max[key],abs(value))
                for key,value in known_bias_coefficients(params,a,x,.075).items():bias_max[key]=max(bias_max.get(key,0),value)
            # REF_positive combines source error plus one buffer offset. Source contribution added once separately.
            offsets=sum(coefficient_max.values())*sensitivities['each_opamp_offset_V']
            bias=sum(bias_max.values())*sensitivities['PW_each_input_bias_A']
            ref=coefficient_max['REF_positive']*5*sensitivities['reference_initial_fraction']
            partial=max(abs(min(values)),abs(max(values)))+offsets+bias+ref
            states.append({'state':name,'vin_V':vin,'CV_V':cv,'atten_fraction':a,'manual_fraction':x,
                'nominal_loaded_V':nominal,'ideal_control_law_V':ideal,'nominal_loading_error_V':nominal-ideal,
                'coherent_resistor_witness_count':len(values),'minimum_witness':witness_min,'maximum_witness':witness_max,
                'ratio_witness_scope':'Coherent endpoint witnesses, not exhaustive all-error or continuous-temperature optimization. Each network largest/smallest<=1+delta. Shared summer feedback element retained.',
                'maximum_abs_opamp_offset_coefficients':coefficient_max,'conditional_100uV_each_offset_sum_V':offsets,
                'known_abs_bias_coefficients_ohm':bias_max,'conditional_15nA_known_bias_sum_V':bias,
                'conditional_reference_0p1percent_initial_sum_V':ref,
                'conditional_partial_absolute_sum_V':partial,'static_target_remaining_after_conditional_partial_V':.002-partial,
                'partial_is_complete_bound':False,'complete_error_bound_V':None,'complete_static_criterion_met':None,
                'within_nominal_supply_rails':abs(nominal)<12,'actual_headroom_established':False})
        low=(1/(1+delta))**2;high=(1+delta)**2
        temperature_rows.append({'network_ratio_condition':label,'network_delta_fraction':delta,
            'CV_gain_interval':[low,high],'CV5V_network_only_error_interval_V':[5*(low-1),5*(high-1)],
            'CV5V_remaining_static_allocation_before_other_terms_V':.002-5*(high-1),
            'ratio_interval_scope':'Conservative product of two within-network ratios; no cross-package matching assumed. Network-only gain envelope, not whole-cell accuracy.',
            'remaining_discrete_scope':'Unchanged0.1% initial resistor sensitivity only; no full-temperature guarantee for remaining discrete pairs.',
            'states':states})
    return {'status':'CANDIDATE MATCHED RATIOS; COMPLETE A01 ACCURACY UNRESOLVED','device':inp['device'],
        'pin_pairs':inp['pin_pairs'],'networks':inp['networks'],'termination_scope':inp['termination_scope'],
        'network_loading':loading_budget(inp),
        'temperature_accounting':matching['temperature_accounting'],'conditioned_error_allocation':temperature_rows,
        'before_after_CV_gain':{'prior_independent_four_resistor_0p1percent_5V_error_interval_V':[5*((.999/1.001)**2-1),5*((1.001/.999)**2-1)],
            'after_scope':'Candidate two-network ratio-only bounds above; historical Stage13 controls/calibration result unchanged.'},
        'error_ledger':{'modeled':'Nominal loaded wipers plus coherent shared summer/restore ratio witnesses and unchanged atten/negative-reference ratios.',
            'offsets':'Ten amplifier contributions with actual coherent gain coefficients.100uV table-conditioned sensitivity, not guaranteed installed +/-12V full-temperature error. No offset calibration subtraction.',
            'bias':'Known impedance sensitivities include network absolute tolerance7.5%, separate from ratio precision. Unknown input-source/protection, REF output and return impedances remain additional.15nA PW evidence is conditioned, not a universal off-state/commonmode bound.',
            'reference':'Common source initial-error sensitivity enters REF_positive once; inversion propagates it. REF_positive amplifier offset and REF_negative amplifier offset are distinct. Drift/noise/regulation/charge/stability remain open.',
            'temperature':'Full-temperature network ratio spec used once. No additional matchingTC or absoluteTC added. Remaining resistors/pots/amplifiers/reference/thermal gradients need separate operating evidence.',
            'return':'Actual source-to-receiver ground displacement times each signal gain plus shared return paths; no equal sharing, allocation-as-copper or blanket2mV assignment.',
            'load':'Same setting open-to10k at-5/0/+5V; existing feedback controls998ohm feedforward drop while linear. Neither that drop nor zero from this load-free model is a residual-load result.',
            'calibration':'No knob fitting performed. Existing two user pots remain rank2; improved CV matching is passive ratio control, not a third adjustment actuator or permanent calibration.'},
        'required_unknown_terms':inp['required_unknown_terms'],'criteria':inp['criteria'],
        'load_change_cases':[{'output_V':v,'open_to_10k_change_V':None,'criterion_V':.001,'criterion_met':None} for v in (-5,0,5)],
        'complete_static_error_bound_V':None,'complete_load_error_bound_V':None,'pitch_acceptance':False,
        'finite_recommendation':inp['finite_recommendation'],'architecture_adopted':False,'hardware_acceptance':False,
        'native':'NOT RUN','CAD':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}


def build():
    p=OUT/'electrical-input.json';result=analyze(json.loads(p.read_text()))
    files=[p,Path(__file__),Path(__file__).with_name('test_stage15_electrical.py'),Path(previous.__file__),
        previous.OUT/'budget-report.json',previous.OUT.parent/'stage13/calibration-report.json',
        previous.OUT.parent/'stage14/electrical-input.json',previous.OUT.parent/'stage14/electrical-report.json']
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=json.dumps(build(),indent=2,sort_keys=True,allow_nan=False)+'\n';target=OUT/'electrical-report.json'
    if args.check:need(target.read_text()==text,'stale Stage15 electrical report')
    else:target.write_text(text)
    print('PASS Stage15 conditioned source allocation; complete static/load acceptance OPEN')
if __name__=='__main__':main()
