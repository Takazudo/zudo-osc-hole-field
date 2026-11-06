"""Conditioned charge/load accounting and finite validation disposition; no simulation."""
import argparse
import json
from pathlib import Path
import stage14_paths as paths
import stage11_assessment as common
ROOT=common.ROOT
OUT=paths.OUT
need=common.need


def analyze(inp, capacitor, inventory, graph):
    need(inp['device']=='REF5050AIDR' and inp['buffer']=='OPA4197IPWR','exact reference/buffer identity')
    need(inp['disposition']=='CONDITIONAL_CANDIDATE','finite disposition required')
    raw='/A01/C534b2a_RAW_5V'
    raw_endpoints=sorted(k for k,v in graph['nodes'].items() if v['kind']=='source' and v['net']==raw)
    need(raw_endpoints==['C7102:1','U7101:6','U7104:3'],'raw reference load topology changed')
    for ref,mpn in [('U7101',inp['device']),('U7104',inp['buffer'])]:
        need(inventory['packages'][ref]['attributes']['MPN']==mpn,'exact source MPN mismatch')
    ref=inp['reference_conditions']
    need(ref['operating_output_current_A']==[-.01,.01] and ref['guaranteed_startup_current_A'] is None,
         'operating current promoted to startup')
    need(ref['short_circuit_typical_A']==.025 and ref['turn_on_typical_s']==.0002 and
         ref['turn_on_test_capacitance_F']==1e-6 and ref['guaranteed_off_state_sink_A'] is None,
         'typical or off-state evidence changed')
    need(inp['buffer_conditions']['PW_bias_max_full_temperature_A']==15e-9 and
         inp['buffer_conditions']['off_state_input_current_bound_A'] is None,'bias/offstate conflation')
    need(inp['added_components']==[] and inp['calibration_changed'] is False,'scope expansion')
    expected_cases={'normal','fast_start','slow_brownout','reference_supply_loss','buffer_supply_loss',
                    'unequal_rails','rapid_restart','reverse_ringing','discharge_service','stability'}
    cases=inp['validation_cases']
    need(len(cases)==len(expected_cases) and {c['id'] for c in cases}==expected_cases,'validation case coverage')
    need(all(c['status']=='NOT RUN' and c['observables'] and c['criterion'] for c in cases),'validation promoted or incomplete')
    rows=[]
    for name,voltage in [('C7101',13.2),('C7102',5)]:
        part=capacitor['parts'][name]
        expected='T491C475K050AT' if name=='C7101' else 'T491D226K035AT'
        need(part['MPN']==expected,'another capacitor selected')
        need(part['effective_service_C_guaranteed_F'] is None,'service capacitance guarantee invented')
        interval=part['initial_120Hz25C_interval_F']
        rows.append({'ref':name,'MPN':part['MPN'],'voltage_V':voltage,
                     'initial_C_interval_F':interval,
                     'initial_charge_interval_C':[c*voltage for c in interval],
                     'initial_energy_interval_J':[.5*c*voltage**2 for c in interval],
                     'assumed_linear_ramp_sensitivities':[{'assumed_ramp_s':t,'capacitor_current_interval_A':[c*voltage/t for c in interval],
                         'actual_ramp_or_current_guaranteed':False} for t in (.001,.01,.1)],
                     'leakage_conditions':'Rated voltage after5min/25C;85/125C multipliers are separate temperature qualification steps, not startup or combined lifetime bounds',
                     'conditioned_leakage_A':{t:part['leakage_max_5min25C_A']*m for t,m in [('25',1),('85',10),('125',12)]},
                     'continuous_reverse_allowed':False,
                     'short_transient_reverse_limits_V':{t:part['rated_voltage_at85C_V']*f for t,f in [('25',.15),('85',.05),('125',.01)]},
                     'actual_peak_current_A':None,'guaranteed_discharge_time_s':None,
                     'scope':'Independent initial-tolerance capacitor arithmetic at stated voltage. No actual ramp, effective service C, inrush or qualified energy discharge path asserted.'})
    output=rows[1];inputcap=rows[0]
    bias=inp['buffer_conditions']['PW_bias_max_full_temperature_A']
    rawloads=[{'temperature_C':int(t),'C7102_conditioned_leakage_A':leak,
               'buffer_abs_bias_sensitivity_A':bias,
               'raw_reference_load_subtotal_A':leak+bias,
               'complete_or_joint_condition_bound':False,
               'scope':'Conservative15nA PW bias sensitivity plus separately conditioned rated-voltage capacitor leakage; no board leakage, transient charging, off-state injection or shared-condition guarantee.'}
              for t,leak in output['conditioned_leakage_A'].items()]
    supply=[{'temperature_C':int(t),'reference_IQ_conditioned_A':ref['IQ_max_full_temperature_A'],
             'input_cap_leakage_conditioned_A':inputcap['conditioned_leakage_A'][t],
             'raw_output_load_subtotal_A':row['raw_reference_load_subtotal_A'],
             'represented_supply_current_subtotal_A':ref['IQ_max_full_temperature_A']+inputcap['conditioned_leakage_A'][t]+row['raw_reference_load_subtotal_A'],
             'complete_or_joint_condition_bound':False} for t,row in zip(('25','85','125'),rawloads)]
    # The source net is behind a follower; buffer-output currents do not flow in RAW5V.
    downstream=paths.read('stage11/electrical-report.json')['reference_load']
    return {'status':'CONDITIONAL CANDIDATE; NOT QUALIFIED','disposition':inp['disposition'],
            'raw_reference_endpoints':raw_endpoints,'capacitor_accounting':rows,
            'raw_reference_conditioned_load_subtotals':rawloads,'supply_conditioned_subtotals':supply,
            'retained_C7107_nominal_charge_at13p2V_C':100e-9*13.2,
            'retained_C7107_scope':'Separate nominal100nF sensitivity, not added to a guaranteed interval; C7107 unchanged.',
            'buffer_output_loads_historical':downstream,
            'load_separation':'REF5050 feeds C7102 and U7104:3 input. U7104 output supplies REF5 pot/divider/inverter loads from amplifier rails; these are not direct RAW5V DC loads. C7101 leakage/charging draw from+12V and return AGND; C7102 leakage/charging draw from REF and return AGND. Startup and all other source loads remain additional.',
            'reference_conditions':ref,'buffer_conditions':inp['buffer_conditions'],
            'charge_balance':'I_REF_out = Ceff*dVraw/dt + I_C7102_leak + I_U7104_input + I_board + I_injection; supply also bears C7101/C7107 charge and leakage plus REF IQ. No available startup-current guarantee => no guaranteed rise time.',
            'discharge_balance':'I_discharge(V,t,state) has no guaranteed positive lower bound. Maximum leakage and operating sink rating cannot establish a safe wait time. Charged RAW5V can inject into an unpowered buffer through rail ESD steering; REF VOUT-to-VIN reverse current is unspecified here.',
            'discharge_time_upper_bound_s':None,'startup_time_upper_bound_s':None,
            'effective_service_C_and_ESR_qualified':False,'backfeed_qualified':False,
            'ESR_scope':'C7102 max0.7ohm at100kHz25C only. Neither full-condition ESR<=1.5ohm stability nor1..1.5ohm noise recommendation is established.',
            'validation_cases':cases,'disposition_reason':inp['disposition_reason'],
            'accuracy_recommendation':inp['accuracy_recommendation'],
            'hardware_acceptance':False,'architecture_adopted':False,
            'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}


def build():
    files=[OUT/'electrical-input.json',OUT.parent/'stage13/capacitor-report.json',
           OUT.parent/'stage10/inventory-report.json',OUT/'interfaces-report.json']
    data=[json.loads(p.read_text()) for p in files]
    for report in data[1:]:common.bindings(report)
    result=analyze(*data)
    files += [Path(__file__),Path(__file__).with_name('test_stage14_electrical.py'),
              OUT.parent/'stage11/electrical-report.json',OUT.parent/'stage13/calibration-report.json',
              OUT.parent/'stage13/capacitor-input.json']
    result['source_sha256']={str(p.relative_to(ROOT)):common.digest(p) for p in files}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';target=OUT/'electrical-report.json'
    if args.check:need(target.read_text()==text,'stale Stage14 electrical')
    else:target.write_text(text)
    print('PASS conditioned charge/load source arithmetic; CONDITIONAL_CANDIDATE, electrical acceptance OPEN')
if __name__=='__main__':main()
