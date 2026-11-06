"""Exact declared DC output/input equations and conditioned allocation, no simulation."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import stage15_electrical as inherited
ROOT=inherited.ROOT
OUT=inherited.OUT.parent/'stage15-completion'
need=inherited.need
RS=998.
RF=100.


def output_dc(u,A,ro,load_ohm,vos=0,ib=0):
    """Ib enters minus pin; A is internal unloaded Thevenin gain, ro separate DC ohms."""
    need(all(math.isfinite(x) for x in (u,A,ro,vos,ib)) and A>0 and ro>=0,'finite positive gain/nonnegative DC resistance')
    need(load_ohm is None or load_ohm>0,'positive load or None=open')
    conductance=0 if load_ohm is None else 1/load_ohm
    return (A*(u+vos+RF*ib)-(RS+ro)*ib)/(A+1+(RS+ro)*conductance)


def load_delta(u,A,ro,load_ohm=10000,vos=0,ib=0):
    return output_dc(u,A,ro,load_ohm,vos,ib)-output_dc(u,A,ro,None,vos,ib)


def output_with_cap_leak(u,A,ro,load_ohm,vos=0,ib=0,icap=0):
    """Positive icap from DRIVE to FB. This is DC leakage, not displacement current."""
    g=0 if load_ohm is None else 1/load_ohm
    return output_dc(u,A,ro,load_ohm,vos,ib)+(-A*RF+RS)*icap/(A+1+(RS+ro)*g)


def allowable_z(vopen,budget,load_ohm=10000):
    need(budget>0 and load_ohm>0,'positive allocation')
    return None if abs(vopen)<=budget else load_ohm*budget/(abs(vopen)-budget)


def input_error(vin,series_ohm,pulldown_ohm=100000,sense_ohm=10000,drain_leak_A=0,sense_current_A=0):
    """Positive currents leave protected/sense nodes; sense current is Ib+net clamp leakage."""
    need(series_ohm>=0 and pulldown_ohm>0 and sense_ohm>=0,'input impedance signs')
    rp=series_ohm*pulldown_ohm/(series_ohm+pulldown_ohm)
    return -vin*series_ohm/(series_ohm+pulldown_ohm)-rp*drain_leak_A-(rp+sense_ohm)*sense_current_A


def input_allowances(output_budget,vin,gain,series_ohm=10,pulldown_ohm=100000,sense_ohm=10000):
    """Each value spends entire allocation alone. Never add independent allowances as a budget."""
    need(output_budget>0 and series_ohm>=0,'positive allocation')
    g=abs(gain)
    if g==0:return {'gain_to_output':gain,'first_order_input_allocation':'No first-order input coupling in this declared state; actual ratio/setting departure must be included.'}
    b=output_budget/g;rp=series_ohm*pulldown_ohm/(series_ohm+pulldown_ohm)
    divider=abs(vin)*series_ohm/(pulldown_ohm+series_ohm)
    return {'gain_to_output':gain,'output_allocation_V':output_budget,'input_equivalent_allocation_V':b,
        'series_resistance_limit_if_no_other_input_errors_ohm':None if abs(vin)<=b else b*pulldown_ohm/(abs(vin)-b),
        'net_sense_current_limit_if_only_term_A':b/(sense_ohm+rp),
        'drain_leak_limit_if_only_term_A':None if rp==0 else b/rp,
        'declared_series_divider_output_error_abs_V':g*divider,
        'remaining_after_declared_divider_V':output_budget-g*divider,
        'scope':'Independent one-term ceilings, not simultaneous grants. Series is external source+cable+switch; actual switch/leakage conditions must match.'}


def internal_bias_allowances(output_budget,a,x,params=None):
    """Known retained circuit impedance ceilings; unknown positive-input/source impedances excluded."""
    need(output_budget>=0,'nonnegative remaining budget')
    p={'ga':1,'gm':1,'gr':1,'ka':1,'kn':1,'gcv':1} if params is None else params
    terms=inherited.known_bias_coefficients(p,a,x,.075)
    total=sum(terms.values())
    return {'known_absolute_coefficients_ohm':terms,'output_allocation_V':output_budget,
        'common_independent_pin_current_ceiling_A':output_budget/total,
        'per_pin_sole_term_ceiling_A':{k:None if value==0 else output_budget/value for k,value in terms.items()},
        'conditional_known_bias_at20pA25C_V':total*20e-12,
        'conditional_known_bias_at15nA_fulltemp_V':total*15e-9,
        'scope':'Known retained impedance magnitudes, including7.5percent network absolute resistance. Per-pin ceilings share one budget;20pA25C and15nAfulltemp are separate condition sensitivities, never added. Positive input external/protection/reference-source/return impedances remain excluded named terms. Counterfactual topology correction has no implied new bias impedance.'}


def topology(inventory,standard):
    p=inventory['packages'];drive='/A01/C2073e0_DRIVE';mid='/A01/C2073e0_ISO_MID';jack='/A01/OUT_TIP';fb='/A01/C2073e0_FB'
    expected={'R7127':({'1':drive,'2':mid},'499 Ω'),'R7128':({'1':mid,'2':jack},'499 Ω'),
        'R7129':({'1':jack,'2':fb},'100 Ω'),'C7106':({'1':drive,'2':fb},'1e-09 F')}
    for ref,(pins,value) in expected.items():need(p[ref]['pins']==pins and p[ref]['unit_records'][0]['value']==value,'captured output topology '+ref)
    need(p['U7106']['attributes']['MPN']=='OPA4197IPWR' and all(p['U7106']['pins'][k]==v for k,v in {'12':'/A01/OUT_INTERNAL','13':fb,'14':drive}.items()),'exact output amplifier pins')
    for ref in ('U7102','U7103'):need(p[ref]['attributes']['MPN']=='ADG5412FBRUZ','exact input switch')
    for ref in ('D7101','D7102'):need(p[ref]['attributes']['MPN']=='BAT54S,215','exact input clamp')
    for switch,pd,limit,diode,amp_pin,tip,protected,sense in [
        ('U7102','R7107','R7108','D7101','3','/A01/IN_TIP','/A01/IN_PROTECTED','/A01/C3833e3_SENSE'),
        ('U7103','R7111','R7112','D7102','5','/A01/OFFSET_TIP','/A01/OFFSET_PROTECTED','/A01/C360350_SENSE')]:
        need(p[switch]['pins']['3']==tip and p[switch]['pins']['2']==protected,'source-facing protection switch')
        need(p[pd]['pins']=={'1':protected,'2':'AGND'} and p[pd]['unit_records'][0]['value']=='100000 Ω','input pulldown binding')
        need(p[limit]['pins']=={'1':protected,'2':sense} and p[limit]['unit_records'][0]['value']=='10000 Ω','sense resistor binding')
        need(p[diode]['pins']=={'1':'-12V','2':'+12V','3':sense} and p['U7106']['pins'][amp_pin]==sense,'input clamp/sense binding')
    need(standard['calibration']['precision_output_load_error_V']==.001,'retained load criterion')
    return {'output_amplifier':'U7106 unit4 pins12/13/14','series':'R7127+R7128=998ohm nominal','feedback':'R7129=100ohm JACK→FB','fast_feedback':'C7106=1nF DRIVE→FB; open only idealDC; separate leakage coefficient retained','matched_prior_stage15_untouched':True}


def analyze(inp,inventory,standard):
    bound=topology(inventory,standard)
    need(inp['assumptions']['series_ohm']==998 and inp['assumptions']['feedback_ohm']==100,'actual resistor model')
    need(inp['assumptions']['load_ohm']==10000 and inp['criteria']['load_change_target_V']==.001,'same load criterion')
    need(inp['common_condition']['OPA_bias_25C_max_A']==20e-12 and inp['common_condition']['OPA_PW_bias_fulltemp_max_A']==15e-9,'25C/fulltemp bias split')
    need(inp['common_condition']['A_DC_at_actual_conditions'] is None and inp['common_condition']['ro_DC_at_actual_conditions'] is None,'no imported fictitious DC limits')
    states=[(name,inherited.previous.transfer(vin,cv,a,x)['internal_V'],vin,cv,a,x) for name,vin,cv,a,x in inherited.STATES]
    outputs=[('criterion_'+str(v),v,None,None,None,None) for v in (-5,0,5)]+states
    scenarios=[]
    for case in inp['engineering_scenarios']:
        A,ro=case['A0'],case['ro_DC_ohm'];rows=[]
        for name,u,*_ in outputs:
            vo=output_dc(u,A,ro,None);vl=output_dc(u,A,ro,10000);z=(RS+ro)/(A+1)
            rows.append({'state':name,'internal_demand_V':u,'open_V':vo,'loaded_10k_V':vl,
                'static_open_model_error_V':vo-u,'load_change_V':vl-vo,'closed_loop_DC_impedance_ohm':z,
                'model_load_criterion_met':abs(vl-vo)<=.001,'hardware_load_criterion_met':None,
                'drive_10k_V':vl*(1+RS/10000),'output_current_10k_A':vl/10000,
                'headroom_requirement':'Verify actual DRIVE swing and current at these signed values under same supplies/temperature; mathematical result does not grant headroom.'})
        scenarios.append({**case,'scope':'Engineering parameter sensitivity only; no datasheet qualification, no incompatible primary corner combination.','rows':rows})
    allowances=[]
    for name,u,vin,cv,a,x in states:
        beta=inherited.previous.old.wiper(a,10000,0,1)['sense_V'];gain=2*beta-1
        allowances.append({'state':name,'declared_output_open_V':u,'full_1mV_load_limit_Zcl_ohm':allowable_z(u,.001),
            'half_0p5mV_loop_allocation_limit_Zcl_ohm':allowable_z(u,.0005),
            'IN':input_allowances(inp['illustrative_single_input_allocation_V'],vin,gain),
            'CV':input_allowances(inp['illustrative_single_input_allocation_V'],cv,1),
            'internal_bias':internal_bias_allowances(inp['illustrative_single_input_allocation_V'],a,x),
            'allocation_status':'Illustrative separate ceilings, not accepted whole-cell allocation; root signed residual matrix determines usable remaining budget.'})
    return {'status':'ANALYSIS ONLY; CONDITIONED COMPUTABLE LOAD AND INPUT ALLOCATION','topology':bound,
        'DC_equations':{'vFB':'vJ−Rf*Ib; ideal capacitor open at DC','internal_source':'e=A0*(u+Vos−vFB); DRIVE=e−ro*(vJ/RL+Ib)',
            'output':'vJ=[A0*(u+Vos+Rf*Ib)−(Rs+ro)*Ib]/[A0+1+(Rs+ro)/RL]',
            'same_parameter_load_delta':'Δv=−vopen*Zcl/(RL+Zcl), Zcl=(Rs+ro)/(A0+1)',
            'cap_DC_leak_coefficient':'dvJ/dIcap=(-A0*Rf+Rs)/(A0+1+(Rs+ro)/RL), Icap positiveDRIVE→FB',
            'finite_parameters':'A0 is unloaded internal Thevenin gain; do not substitute load-specified datasheetAOL and independently add ro without conversion.',
            'load_dependent_parameters':'Exact paired evaluation is output_dc(uL,AL,roL,RL,vosL,ibL)−output_dc(uO,AO,roO,None,vosO,ibO), plus leakage/return changes. Common static offsets cancel only to the stated model extent.'},
        'five_volt_loop_requirement':{'full_1mV_Zcl_max_ohm':allowable_z(5,.001),'half_0p5mV_Zcl_max_ohm':allowable_z(5,.0005),
            'minimum_A0_for_ro0_full_1mV':RS/allowable_z(5,.001)-1,
            'direct_validation_alternative':'A same-condition measured/bounded closed-loop DC transfer impedance atactual rails,temperature,output current can establish this term without separatingA0/ro.'},
        'engineering_scenarios':scenarios,'per_state_allowances':allowances,'common_condition':inp['common_condition'],
        'required_parameters':inp['required_parameters'],'input_equation':'eIN=−Vin*S/(Rp+S)−(S||Rp)*ID−(Rlim+S||Rp)*(Ib+Iclamp); S=Rsource+cable+RON; positive currents leave nodes.',
        'input_signed_examples':[{'vin_V':v,'series_ohm':s,'error_V':input_error(v,s),'scope':'Nominal100k pulldown, no injected current, declared series sensitivity;10ohm is NOT claimed actual±12VADGlimit.'} for v in (-5,0,5) for s in (0,10,100,1000)],
        'output_load_allowance_ledger':{'illustrative_split_V':{'finite_loop':.0005,'all_remaining_paired_changes':.0005},
            'accepted_allocation':False,'remaining_equation':'|Δ(u+Vos)| +100ohm*|ΔIb| +100ohm*|ΔIcap| +|Δlocal_to_receiver_ground| +parameter-change remainder <=0.5mV in high-gain sensitivity only; use exactpaired equations for finiteA.',
            'individual_ceilings_if_sole_remaining_term':{'delta_effective_input_V':.0005,'delta_feedback_bias_A':5e-6,'delta_cap_leak_A':5e-6,'delta_ground_V':.0005},
            'warning':'These are per-term ceilings sharing one residual budget, not four simultaneous0.5mV allocations. Settling, noise, output current/headroom and switching transient criteria remain separate.'},
        'actual_complete_load_bound_V':None,'reason_no_actual_load_bound':'No same-condition A0/ro or closed-loopDCimpedance bound at±12V and paired load-dependent offset/bias/source/ground changes; required parameter conditions/ceilings listed individually.',
        'criterion_V':.001,'hardware_acceptance':False,'native':'NOT RUN','CAD':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}


def build():
    files=[OUT/'load-input.json',inherited.OUT.parent/'stage10/inventory-report.json',ROOT/'design/standard/electrical-standard.json']
    result=analyze(*[json.loads(p.read_text()) for p in files])
    files.extend([Path(__file__),Path(__file__).with_name('test_stage15_load_allocation.py'),Path(inherited.__file__),
        ROOT/'design/spec/modules/offset.py',inherited.OUT/'electrical-input.json',inherited.OUT/'electrical-report.json'])
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=json.dumps(build(),indent=2,sort_keys=True,allow_nan=False)+'\n';dest=OUT/'load-report.json'
    if args.check:need(dest.read_text()==text,'stale load allocation')
    else:dest.write_text(text)
    print('PASS conditioned exact DC allocation; actual electrical acceptance OPEN')
if __name__=='__main__':main()
