"""Conditioned rail-monitor study; no installed protection or permit admission."""
import argparse
import hashlib
import itertools
import json
import math
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT/'design/power/rail-monitor-candidate.json'
SOURCES = ROOT/'design/power/rail-monitor-candidate-sources.json'
REPORT = ROOT/'design/power/rail-monitor-candidate-report.json'


def number(x):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ValueError('finite numeric monitor operand required')
    return F(str(x))


def display(x, upper):
    out = float(x)
    if (F(out) < x if upper else F(out) > x):
        out = math.nextafter(out, math.inf if upper else -math.inf)
    return out


def divider_bounds(row, device, resistors):
    temperature = max(abs(number(t)-number(resistors['reference_C'])) for t in resistors['evaluated_C'])
    tolerance=number(resistors['tolerance_fraction'])
    drift=temperature*number(resistors['tcr_abs_per_C'])
    if not 0 <= tolerance < 1 or not 0 <= drift < 1:
        raise ValueError('invalid resistor envelope')
    lower_factor=(1-tolerance)*(1-drift);upper_factor=(1+tolerance)*(1+drift)
    top = sum((number(p['ohm']) for p in row['top']), F())
    bottom = sum((number(p['ohm']) for p in row['bottom']), F())
    if min(top,bottom) <= 0 or row['sense_inputs'] not in (1,2):
        raise ValueError('positive divider and one/two input loads required')
    nominal = number(device['nominal_threshold_V'])
    window = number(device['window_fraction'])
    accuracy = number(device['absolute_threshold_accuracy_fraction'])
    hys = list(map(number,device['hysteresis_fraction_of_trip']))
    bias = number(device['adjustable_input_current_table_max_A'])*row['sense_inputs']
    if not 0 < window < 1 or not 0 <= accuracy < 1 or not 0 <= hys[0] <= hys[1] < 1 or bias < 0:
        raise ValueError('invalid threshold/current envelope')
    limits = {}
    for event in ('UV_trip','UV_recover','OV_trip','OV_recover'):
        values = []
        for ru,rd,a,h,i in itertools.product(
                (top*lower_factor,top*upper_factor),(bottom*lower_factor,bottom*upper_factor),
                (1-accuracy,1+accuracy),hys,(-bias,bias)):
            threshold = nominal*(1-window if event.startswith('UV') else 1+window)*a
            if event=='UV_recover': threshold *= 1+h
            if event=='OV_recover': threshold *= 1-h
            # Input current positive into the device: Vin=Vs*(1+Ru/Rd)+Ib*Ru.
            values.append(threshold*(1+ru/rd)+i*ru)
        limits[event] = (min(values),max(values))
    return limits


def delay_bound(device, context):
    condition = device['delay_conditions']
    supply=number(context['supply_V']);temperature=number(context['temperature_C'])
    matched = (
        number(device['fixed_reset_delay_s']) > number(condition['fixed_reset_delay_greater_than_s'])
        and number(context['overdrive_fraction']) == number(condition['overdrive_fraction'])
        and number(context['pullup_ohm']) == number(condition['pullup_ohm'])
        and number(context['load_F']) == number(condition['load_F'])
        and number(condition['supply_V'][0]) <= supply <= number(condition['supply_V'][1])
        and number(condition['temperature_C'][0]) <= temperature <= number(condition['temperature_C'][1]))
    return device['detect_delay_max_s'] if matched else None


def isolator_state(vcc1, vcc2, signal, spec):
    for v in (vcc1,vcc2): number(v)
    if signal not in ('LOW','HIGH','OPEN'):
        raise ValueError('unknown isolator input')
    low = spec['isolator_powered_down_max_V']; high = spec['isolator_powered_min_V']
    maximum = spec['isolator_supply_max_V']
    if not 0 <= vcc1 <= maximum or not high <= vcc2 <= maximum:
        return 'UNDEFINED'
    if vcc1 <= low:
        # A driven HIGH can parasitically power VCC1 through IN; the source
        # explicitly excludes treating that case as an unconditional default.
        return 'UNDEFINED' if signal=='HIGH' else 'LOW'
    if vcc1 < high:
        return 'UNDEFINED'
    return 'LOW' if signal=='OPEN' else signal


def validate_sources(spec, verify_retained=False):
    records = json.loads(SOURCES.read_text())['sources']
    by_id = {r['id']:r for r in records}
    if len(by_id)!=len(records) or spec['protection_implemented'] or spec['floating_negative_trial']['admitted']:
        raise ValueError('duplicate source or forbidden protection admission')
    if (spec['supervisor']['mpn']!='TPS37044MJOFDDFRQ1'
            or by_id['supervisor']['mpn']!=spec['supervisor']['mpn']
            or spec['supervisor']['used_channels']!=[3,4]):
        raise ValueError('exact supervisor option/channel mismatch')
    d=spec['supervisor']
    if (d['nominal_threshold_V']!=.8 or d['window_fraction']!=.07
            or d['absolute_threshold_accuracy_fraction']!=.01
            or d['hysteresis_fraction_of_trip']!=[.004,.01]
            or d['detect_delay_max_s']!=10e-6 or d['fixed_reset_delay_s']!=.01
            or d['adjustable_input_current_table_max_A']!=350e-9
            or d['delay_conditions']!={
                'fixed_reset_delay_greater_than_s':.001,'overdrive_fraction':.10,
                'pullup_ohm':10000,'load_F':10e-12,'supply_V':[1.7,6.0],
                'temperature_C':[-40,125]}
            or d['startup_max_s'] is not None
            or spec['comparison']['propagation_max_s'] is not None):
        raise ValueError('source-backed option/timing observations changed; new evidence review required')
    f=spec['floating_negative_trial']
    if (f['isolator_mpn']!='ISO7710FDR' or f['ldo_mpn']!='TPS70933DBVR'
            or f['isolator_connections']['1']!=f['isolator_connections']['3']
            or f['isolator_connections']['7']!='NC'
            or f['ldo_connections']['3']!='NC enabled by internal pullup'):
        raise ValueError('exact floating-domain device/pin identity changed')
    for row in spec['divider_candidates']:
        for part in row['top']+row['bottom']:
            source=by_id[part['mpn']]
            if (source['resistance_ohm']!=part['ohm']
                    or source['tolerance_fraction']!=spec['resistor_condition']['tolerance_fraction']
                    or source['tcr_abs_per_C']!=spec['resistor_condition']['tcr_abs_per_C']):
                raise ValueError('divider differs from exact resistor source')
    for r in records:
        if r['availability']!='AVAILABLE' or r['authority']!='MANUFACTURER_PRIMARY' or len(r['sha256'])!=64 or set(r['sha256'])=={'0'}:
            raise ValueError('retained primary metadata required')
        if verify_retained:
            path=ROOT/r['file']; data=path.read_bytes()
            if not data.startswith(b'%PDF-') or len(data)!=r['bytes'] or hashlib.sha256(data).hexdigest()!=r['sha256']:
                raise ValueError('retained PDF bytes differ: '+r['id'])


def calculate(spec):
    supply=json.loads((ROOT/spec['normal_voltage_source']).read_text())
    bands=supply['source_requirement']['required_load_voltage_magnitude_V']
    device=spec['supervisor']; rows=[]
    for row in spec['divider_candidates']:
        limits=divider_bounds(row,device,spec['resistor_condition'])
        low,high=map(number,bands[row['rail']])
        lower=limits['UV_recover'][1];upper=limits['OV_recover'][0]
        rows.append({'rail':row['rail'],'normal_load_magnitude_V':bands[row['rail']],
            'threshold_magnitude_intervals_V':{k:[display(a,False),display(b,True)] for k,(a,b) in limits.items()},
            'normal_recovery_lower_margin_V':display(low-lower,False),
            'normal_recovery_upper_margin_V':display(upper-high,False),
            'conditional_static_recovery_covers_normal_band':low>lower and high<upper,
            'scope':'Conditional input-bias/thermal envelope; no startup, dynamic or whole-protection admission.'})
    floating=spec['floating_negative_trial']; negative=next(r for r in spec['divider_candidates'] if r['rail']=='-12V')
    ru=sum(p['ohm'] for p in negative['top']);rd=sum(p['ohm'] for p in negative['bottom'])
    stresses=[]
    for vn in floating['pin_stress_VN_cases_V']:
        vin=-vn;sense=vin*rd/(ru+rd)
        stresses.append({'VN_relative_AGND_V':vn,'ldo_IN_relative_GND_V':vin,
            'unloaded_sense_relative_VN_V':sense,'ldo_input_absolute_rating_violated':vin<floating['ldo_input_absolute_min_V'],
            'unloaded_monitor_sense_outside_absolute_rating':not device['pin_absolute_V'][0]<=sense<=device['pin_absolute_V'][1],
            'sense_scope':'Unloaded divider prediction; actual clamp/injection behavior is unresolved.'})
    contexts=[
        {'name':'table matched','overdrive_fraction':.10,'pullup_ohm':10000,'load_F':10e-12,'supply_V':3.3,'temperature_C':125},
        {'name':'near-threshold fault','overdrive_fraction':.01,'pullup_ohm':10000,'load_F':10e-12,'supply_V':3.3,'temperature_C':25},
        {'name':'lighter pullup is a different condition','overdrive_fraction':.10,'pullup_ohm':100000,'load_F':10e-12,'supply_V':3.3,'temperature_C':25},
        {'name':'added logic/gate capacitance','overdrive_fraction':.10,'pullup_ohm':10000,'load_F':100e-12,'supply_V':3.3,'temperature_C':25}]
    return {'status':'UNSELECTED conditioned monitor study; protection unimplemented',
        'protection_implemented':False,'static_divider_cases':rows,
        'timing_cases':[{**c,'matched_detection_upper_s':delay_bound(device,c)} for c in contexts],
        'startup_maximum_s':None,
        'startup_reason':'Nominal startup time plus a bounded reset delay is not a maximum startup guarantee.',
        'floating_negative_pin_stress':stresses,
        'floating_negative_scope':floating['counterexample_scope'],
        'isolator_power_states':[{'VCC1_V':a,'VCC2_V':b,'input':signal,'output':isolator_state(a,b,signal,floating)}
                                 for a,b,signal in itertools.product((0,1.9,3.3),(0,1.9,5),('OPEN','LOW','HIGH'))],
        'all_rail_arrival_orders_required':[list(p) for p in itertools.permutations(('+12V','-12V','+5V'))],
        'all_rail_failure_orders_required':[list(p) for p in itertools.permutations(('+12V','-12V','+5V'))],
        'state_sequence_validation':'NOT RUN: surviving power, real AND/latch/driver and independent return monitor are not captured.',
        'native_dynamic_bench':'NOT RUN: no implemented monitor assembly',
        'input_current_scope':device['input_current_table_condition'],
        'resistor_reference_scope':spec['resistor_condition']['reference_temperature_scope'],
        'open_obligations':spec['open_obligations']}


def run(check=False, verify_retained=False):
    spec=json.loads(SPEC.read_text());validate_sources(spec,verify_retained)
    report=calculate(spec)
    paths=(SPEC,SOURCES,ROOT/spec['normal_voltage_source'],Path(__file__).resolve())
    report['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    text=json.dumps(report,indent=2,allow_nan=False)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text:raise ValueError('rail-monitor report drift')
    else:REPORT.write_text(text)
    print('PASS: conditional monitor arithmetic/source metadata only; protection remains OPEN')
    print('Retained PDF verification: '+('PASS' if verify_retained else 'NOT RUN (use --verify-retained)'))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');p.add_argument('--verify-retained',action='store_true')
    args=p.parse_args();run(args.check,args.verify_retained)
