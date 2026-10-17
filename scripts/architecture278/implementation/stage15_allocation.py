"""Coherent ten-state signed counterfactual allocation; no circuit implementation."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import stage15_electrical as prior
import stage15_load_allocation as load

ROOT=prior.ROOT
OUT=prior.OUT.parent/'stage15-completion'
need=prior.need
FACTORS=('reference_inverter_ratio','attenuverter_ratio','manual_loading','atten_loading')


def affine(vin,cv,a,x,p,removed=(),reference_fraction=0):
    """Exact nominal-pot DC law, explicit attribution order retaining cross-products."""
    kn=1 if 'reference_inverter_ratio' in removed else p['kn']
    ka=1 if 'attenuverter_ratio' in removed else p['ka']
    da=1 if 'atten_loading' in removed else 1e7/(1e7+1000+10000*a*(1-a))
    dx=1 if 'manual_loading' in removed else 1e7/(1e7+1000+100000*x*(1-x))
    ref=5*(1+reference_fraction)
    gs=p['gr']*p['ga'];gm=p['gr']*p['gm'];gc=p['gr']*p['gcv']
    kin=gs*((1+ka)*a*da-ka)
    intercept=gm*ref*dx*((1+kn)*x-kn)
    ideal=(2*a-1)*vin+cv+5*(2*x-1)
    parts={'CV_slope':(gc-1)*cv,'IN_network_gain':(gs-1)*(2*a-1)*vin,
        'IN_control_loading':gs*2*a*(da-1)*vin,
        'IN_attenuverter_ratio':gs*(ka-1)*(a*da-1)*vin,
        'manual_network_ratio':(gm-1)*5*(2*x-1),
        'reference_initial':gm*(ref-5)*(2*x-1),
        'manual_control_loading':gm*ref*(dx-1)*(2*x-1),
        'reference_inverter_intercept':-gm*ref*dx*(1-x)*(kn-1)}
    value=kin*vin+gc*cv+intercept
    need(math.isclose(sum(parts.values()),value-ideal,abs_tol=1e-12),'signed decomposition must close')
    return {'out_V':value,'ideal_knob_law_V':ideal,'fixed_setting_residual_V':value-ideal,
            'signed_terms_V':parts,'IN_gain':kin,'CV_gain':gc,'zero_input_intercept_V':intercept,
            'manual_ideal_V':5*(2*x-1),'manual_loading_factor':dx,'atten_loading_factor':da}


def coefficients(a,x,p,removed=()):
    ka=1 if 'attenuverter_ratio' in removed else p['ka'];kn=1 if 'reference_inverter_ratio' in removed else p['kn']
    q=affine(0,0,a,x,p,removed);gr=p['gr'];ga=p['ga'];gm=p['gm'];gc=p['gcv'];dx=q['manual_loading_factor'];beta=a*q['atten_loading_factor']
    return {'IN_buffer':q['IN_gain'],'remote_buffer':gr*ga*(1+ka)*beta,'atten_amp':gr*ga*(1+ka),
            'manual_amp':gr*gm,'CV_buffer':gr*gc,'summer':-gr*(1+ga+gm+gc),
            'restore':1+gr,'output':1,'REF_positive':gr*gm*dx*((1+kn)*x-kn),
            'REF_negative':gr*gm*dx*(1-x)*(1+kn)}


def allowance(row,coefs,reserve):
    remaining=.002-abs(row['fixed_setting_residual_V']);usable=max(0,remaining)
    common=sum(abs(v) for v in coefs.values())
    # Each is a one-at-a-time necessary ceiling. They cannot all consume usable simultaneously.
    return {'signed_known_residual_V':row['fixed_setting_residual_V'],'remaining_absolute_budget_V':remaining,
        'remaining_after_analysis_reserve_V':remaining-reserve,'additional_error_allowance_V':usable,
        'already_exceeds_target_by_V':max(0,-remaining),
        'common_equal_Vos_ceiling_V':usable/common if common else None,
        'IN_input_referred_ceiling_V':usable/abs(row['IN_gain']) if row['IN_gain'] else None,
        'CV_input_referred_ceiling_V':usable/abs(row['CV_gain']),
        'receiver_return_shift_ceiling_V':usable,
        'reference_source_error_ceiling_V':usable/abs(coefs['REF_positive']) if coefs['REF_positive'] else None,
        'required_missing_parameters':{
            'amplifier':'Each of ten signed input offsets at same actual supply/common-mode/temp/load plus per-pin bias and source impedances; common Vos ceiling is one-at-a-time, not guaranteed achievable.',
            'input':'External source Thevenin resistance and source error; ADG powered on-resistance/leakage at same rail/commonmode/temp;100k pulldown and10k sense tolerance plus actual follower bias.',
            'output':'DC Aol and output resistance at actual +/-12V/commonmode/output/load; load-dependent offset/bias and shield/ground shifts; load report provides algebra and inverted ceilings.',
            'return':'Actual source-to-receiver ground voltage (or every shared edge resistance and signed actual downstream current), excluding duplicate edge-use counts.',
            'reference':'Raw/reference-buffer initial error and reference-inverter error must be treated once via shown coefficient; actual effectiveCL/ESR and line/load/temp conditions remain required.',
            'temperature_aging':'Chosen operating deltaT and time, each offset drift/bias at temperature, resistor/pot tracking and reference drift/aging. No operating envelope adopted.'},
        'allocation_rule':'One-at-a-time necessary ceilings from this exact coherent witness. A complete proof needs the SUM of simultaneous absolute additional contributions <= allowance; no cancellation credit, no budget reset, no hypothetical calibration. None means zero sensitivity only, not unspecified performance.'}


def analyze(inp):
    need(inp['baseline_commit']=='10e3fbbdc2fcfe954da7aa7df5b02db1230ff8f0','exact approved baseline')
    need(inp['counterfactual_factors']==list(FACTORS),'fixed counterfactual factors')
    need(inp['network_matching_fraction']==.0001 and inp['retained_discrete_tolerance_fraction']==.001,'common25C initial model only')
    need(inp['static_target_V']==.002 and inp['load_change_target_V']==.001,'retained criteria')
    need(inp['reference_initial_fraction']==.001 and inp['unknown_reserve_example_V']==.0005,'explicit analysis inputs')
    need(inp['component_geometry_changed'] is False,'analysis only')
    cases=list(prior.all_cases(inp['network_matching_fraction'],inp['retained_discrete_tolerance_fraction']))
    masks=[tuple(f for f,on in zip(FACTORS,bits) if on) for bits in itertools.product((False,True),repeat=4)]
    nominal={'ka':1,'kn':1,'ga':1,'gm':1,'gcv':1,'gr':1}
    scenarios=[]
    for removed in masks:
        rows=[]
        for name,vin,cv,a,x in prior.STATES:
            lo=hi=None;lo_ref=hi_ref=None;paired_cv=[];paired_in=[]
            max_coeff={k:0 for k in coefficients(a,x,nominal,removed)}
            for i,(p,s,r,d) in enumerate(cases):
                q=affine(vin,cv,a,x,p,removed)
                w={**q,'corner_index':i,'params':p,'network_summer_elements':s,'network_restore_elements':r,'discrete_elements':d,'reference_fraction':0}
                if lo is None or w['fixed_setting_residual_V']<lo['fixed_setting_residual_V']:lo=w
                if hi is None or w['fixed_setting_residual_V']>hi['fixed_setting_residual_V']:hi=w
                paired_cv.append(q['CV_gain']);paired_in.append(q['IN_gain'])
                for k,v in coefficients(a,x,p,removed).items():max_coeff[k]=max(max_coeff[k],abs(v))
                for sign in (-1,1):
                    f=sign*inp['reference_initial_fraction'];q=affine(vin,cv,a,x,p,removed,f)
                    w={**q,'corner_index':i,'params':p,'network_summer_elements':s,'network_restore_elements':r,'discrete_elements':d,'reference_fraction':f}
                    if lo_ref is None or w['fixed_setting_residual_V']<lo_ref['fixed_setting_residual_V']:lo_ref=w
                    if hi_ref is None or w['fixed_setting_residual_V']>hi_ref['fixed_setting_residual_V']:hi_ref=w
            worst=max((lo,hi),key=lambda q:abs(q['fixed_setting_residual_V']))
            worst_ref=max((lo_ref,hi_ref),key=lambda q:abs(q['fixed_setting_residual_V']))
            ranking=[{'term':k,'signed_V':v} for k,v in sorted(worst_ref['signed_terms_V'].items(),key=lambda kv:abs(kv[1]),reverse=True)]
            # Counterfactual delta always compares SAME physical corner/reference, not unrelated extrema.
            origin=affine(vin,cv,a,x,worst_ref['params'],(),worst_ref['reference_fraction'])
            n=affine(vin,cv,a,x,nominal,removed)
            load_cases=[]
            for lc in json.loads((OUT/'load-input.json').read_text())['engineering_scenarios']:
                values=[]
                for w in (lo_ref,hi_ref):
                    opened=load.output_dc(w['out_V'],lc['A0'],lc['ro_DC_ohm'],None)
                    loaded=load.output_dc(w['out_V'],lc['A0'],lc['ro_DC_ohm'],10000)
                    terms={**w['signed_terms_V'],'output_finite_loop_open':opened-w['out_V'],'output_load_change':loaded-opened}
                    values.append({'corner_index':w['corner_index'],'reference_fraction':w['reference_fraction'],
                        'open_fixed_residual_V':opened-w['ideal_knob_law_V'],'loaded_fixed_residual_V':loaded-w['ideal_knob_law_V'],
                        'load_change_V':loaded-opened,'loaded_signed_terms_V':terms,
                        'ranked_loaded_terms':[{'term':k,'signed_V':v} for k,v in sorted(terms.items(),key=lambda kv:abs(kv[1]),reverse=True)]})
                load_cases.append({'parameters':lc,'endpoint_witnesses':values,
                    'loaded_signed_interval_V':[v['loaded_fixed_residual_V'] for v in values],
                    'maximum_abs_load_change_V':max(abs(v['load_change_V']) for v in values),
                    'scope':'Exact monotone output equation over same coherent resistor/reference extrema; A0/ro engineering assumptions, Vos/Ib/leakage zero here and explicitly allocated separately. Not an actual-condition bound.'})
            rows.append({'state':name,'vin_V':vin,'CV_V':cv,'atten_fraction':a,'manual_fraction':x,
                'nominal':n,'conditioned_output_load_cases':load_cases,'resistor_only_signed_interval_V':[lo['fixed_setting_residual_V'],hi['fixed_setting_residual_V']],
                'resistor_only_worst_witness':worst,'with_reference_initial_signed_interval_V':[lo_ref['fixed_setting_residual_V'],hi_ref['fixed_setting_residual_V']],
                'with_reference_initial_worst_witness':worst_ref,'ranked_signed_terms_at_same_witness':ranking,
                'paired_CV_gain_interval':[min(paired_cv),max(paired_cv)],'paired_IN_gain_interval':[min(paired_in),max(paired_in)],
                'paired_CV_10V_span_error_interval_V':[10*(min(paired_cv)-1),10*(max(paired_cv)-1)],
                'paired_IN_10V_span_error_interval_V':[10*(min(paired_in)-(2*a-1)),10*(max(paired_in)-(2*a-1))],
                'same_corner_counterfactual_delta_V':worst_ref['out_V']-origin['out_V'],
                'maximum_abs_offset_coefficients_sensitivity_only':max_coeff,
                'remaining_at_same_worst_witness':allowance(worst_ref,coefficients(a,x,worst_ref['params'],removed),inp['unknown_reserve_example_V']),
                'witness_count':len(cases),'reference_signs_per_witness':2,
                'scope':'Finite coherent initial25C resistor/reference sensitivity at fixed electrical fractions; not continuous pot/tolerance/temperature or physical accuracy proof. Componentwise coefficient maxima not summed into a claimed compatible-corner bound.'})
        ranked=sorted(rows,key=lambda r:abs(r['with_reference_initial_worst_witness']['fixed_setting_residual_V']),reverse=True)
        scenarios.append({'removed_nonidealities':list(removed),'state_rows':rows,
            'ranked_states':[{'state':r['state'],'signed_worst_V':r['with_reference_initial_worst_witness']['fixed_setting_residual_V']} for r in ranked],
            'maximum_abs_resistor_only_V':max(abs(r['resistor_only_worst_witness']['fixed_setting_residual_V']) for r in rows),
            'maximum_abs_with_reference_initial_V':max(abs(r['with_reference_initial_worst_witness']['fixed_setting_residual_V']) for r in rows),
            'all_ten_within_2mV_from_modeled_terms_only':all(abs(r['with_reference_initial_worst_witness']['fixed_setting_residual_V'])<=.002 for r in rows)})
    gain=(1+inp['network_matching_fraction'])**2
    network_at5=5*(gain-1);reserve=inp['unknown_reserve_example_V']
    return {'status':'STAGE15 WHOLE-CELL ANALYSIS COMPLETION; HARDWARE ACCEPTANCE OPEN','scenarios':scenarios,
        'definitions':{'absolute_fixed_setting':'Output minus ideal electrical-fraction law with SAME physical corner,reference,input/knob state. No zero/gain correction applied.',
            'paired_gain':'[out(+5)-out(-5)]/10 at same other input,knobs,corner and constant errors. Cancels intercept only under stated invariance; not absolute fixedsetting precision or actual calibrated residual.',
            'ideal_knob_law':'(2a-1)*IN +5*(2x-1)+CV. a,x are electrical fractions, not shaft position or factory calibration.',
            'signed_attribution':'CV slope; IN network/attenuation loading/atten ratio; manual network/reference initial/loading/inverter intercept. Products kept in explicit order. Attribution order stated; only totals and same-corner counterfactual differences are order-independent.'},
        'necessary_next_conditions':{'network_only_5V_high_V':network_at5,'analysis_only_other_error_reserve_V':reserve,
            'perfect_four_corrections_manual_endpoint_reference_fraction_ceiling':max(0,(.002-reserve-network_at5)/(5*gain)),
            'ceiling_scope':'Necessary symmetric reference-error ceiling with all four listed corrections ideal and high network ratio;0.5mV reserved for ALL remaining terms. Algebraic requirement, not adopted envelope, calibration, achievable part claim or sufficient wholecell proof.',
            'existing_reference_initial_fraction':.001,
            'single_correction_suffices':False,'joint_four_corrections_suffice':False},
        'temperature_scope':'All counterfactuals use initial25C evidence sensitivities; LT5400 full-temperature matching and1ppm/C tracking not added. Unchanged parts/amp/reference/pots require compatible operating evidence; no temperature/aging acceptance or lifetime bound.',
        'hardware_acceptance':False,'component_geometry_changed':False,'native':'NOT RUN','CAD':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}


def build():
    files=[OUT/'allocation-input.json',Path(__file__),Path(__file__).with_name('test_stage15_allocation.py'),Path(prior.__file__),Path(prior.previous.__file__),prior.OUT/'electrical-input.json',prior.OUT/'electrical-report.json',Path(load.__file__),OUT/'load-input.json']
    r=analyze(json.loads(files[0].read_text()));r['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files};return r


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();text=json.dumps(build(),indent=2,sort_keys=True,allow_nan=False)+'\n';dest=OUT/'allocation-report.json'
    if args.check:need(dest.read_text()==text,'stale Stage15 allocation')
    else:dest.write_text(text)
    print('PASS ten-state signed/counterfactual analysis; no single correction proves precision')
if __name__=='__main__':main()
