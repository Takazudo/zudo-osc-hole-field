"""Source-derived passive requirements and drawing coordinates, never CAD/native output."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
REL = 'design/architecture-278/implementation/'
OUT = ROOT / REL / 'stage22'
BASE = '052eb53bfc59c5dae17e94f0b5d3df5893b0e81c'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(x):
    return json.dumps(x, sort_keys=True, indent=2, allow_nan=False) + '\n'


def positive(*values):
    need(all(type(v) in (float, int) and math.isfinite(v) and v > 0 for v in values), 'finite positive physical values')


def power(voltage, resistance, tolerance=0):
    positive(resistance)
    need(math.isfinite(voltage) and math.isfinite(tolerance) and 0 <= tolerance < 1, 'voltage/tolerance domain')
    return voltage**2 / (resistance * (1-tolerance))


def divider(supply, top, bottom):
    positive(top, bottom)
    current = supply/(top+bottom)
    return {'current_A': current, 'drop_top_V': current*top, 'power_top_W': current**2*top, 'output_V': current*bottom}


def wiper(alpha, low, high, pot, series, fail, cap):
    positive(pot, series, fail, cap)
    need(0 <= alpha <= 1 and all(math.isfinite(v) for v in (alpha, low, high)), 'wiper domain')
    thevenin = series + pot*alpha*(1-alpha)
    unloaded = low+(high-low)*alpha
    loaded = unloaded*fail/(fail+thevenin)
    tau = thevenin*fail/(thevenin+fail)*cap
    return {'unloaded_V': unloaded, 'loaded_V': loaded, 'loading_error_V': loaded-unloaded,
            'thevenin_ohm': thevenin, 'tau_s': tau, 'settling_to_1_percent_s': -math.log(.01)*tau}


def bipolar_worst_loading(pot, series, fail):
    positive(pot, series, fail)
    # Exact stationary point of x*(A-B*x²)/(Rf+A-B*x²), x=2*alpha-1.
    a, b = series+pot/4, pot/4
    d = (3*fail+2*a)**2-4*a*(fail+a)
    y = 2*a*(fail+a)/(b*(3*fail+2*a+math.sqrt(d)))
    return min(1, (1+math.sqrt(y))/2)


def attenuation(alpha, frequency, resistance, capacitance):
    positive(resistance, capacitance)
    need(0 <= alpha <= 1 and math.isfinite(frequency) and frequency >= 0, 'frequency/alpha domain')
    zratio = 1/(1+2j*math.pi*frequency*resistance*capacitance)
    return alpha+(alpha-1)*zratio


def drawing_coordinates(drawing):
    need(drawing['holes'] == 96 and drawing['pitch_mm'] == 2.54
         and drawing['left_to_right'] == [32, 1], 'exact 96-contact drawing grid')
    rows = drawing['top_to_bottom']
    need(rows == (['a','b','c'] if drawing['view'] == 'A' else ['c','b','a'])
         and drawing['view'] in ('A','B'), 'drawing view handedness')
    need(drawing['hole_diameter_mm'] == 1 and drawing['hole_tolerance_mm'] == .1
         and drawing['position_diameter_mm'] == .05, 'exact solder-part hole callout')
    return {f'{row}{col}': [round((16.5-col)*2.54, 6), round((1-i)*2.54, 6)]
            for i,row in enumerate(rows) for col in range(1,33)}


def analyze(packages, standard, prior, assumptions):
    need(assumptions['status'] == 'PROPOSED_SENSITIVITIES_NOT_OWNER_APPROVED'
         and assumptions['owner_approved'] is False, 'sensitivity is not owner approval')
    positive(assumptions['rail_magnitude_sensitivity_V'], assumptions['audio_frequency_sensitivity_Hz'])
    need(assumptions['local_ambient_sensitivity_C'] == 85, 'reviewed thermal sensitivity')
    refs = set(prior['selections'])
    need(len(refs) == 19, 'complete passive roster')
    for ref in refs:
        need(packages[ref] == prior['selections'][ref]['captured_source'], 'source topology/value/unit drift '+ref)
    def value(ref):
        return float(packages[ref]['unit_records'][0]['value'].split()[0])
    for ref, expected in {'R7104':100000,'R7105':100000,'R7109':100000,'R7117':100000,'R7118':100000,'C7103':1e-10}.items():
        need(value(ref) == expected, 'adjacent source value drift '+ref)
    need(packages['RV1307']['selected_mpn'] == 'PTV09A-4020F-B103'
         and packages['RV1308']['selected_mpn'] == 'PTV09A-4020F-B104', 'exact nominal pot identities')
    cells = {c['id']:c for c in standard['cells']}
    need(standard['signals']['rails_V'] == {'+12V':12,'-12V':-12,'+5V':5}
         and standard['signals']['bipolar_cv_nominal_V'] == [-5,5]
         and standard['signals']['input_continuous_fault_V'] == [-12,12], 'source nominal/fault envelope')
    result = {}
    for ref in sorted(refs):
        role = packages[ref]['unit_records'][0]['attributes']['Role']
        cell, local = role.split(':')
        part = next(p for p in cells[cell]['parts'] if p['ref'] == local)
        need(part['value'] == value(ref), 'cell/source value disagreement '+ref)
        mpn = prior['selections'][ref]['candidate_mpn']
        ratings = prior['sources'][mpn]['ratings']
        row = {'role':role,'value_SI':value(ref),'candidate_mpn':mpn,'candidate_adopted':False,
               'model_scope':'Source-derived ideal DC or explicitly conditional bound; not electrical acceptance.'}
        if ref.startswith('R'):
            row['existing_tolerance_target_fraction'] = standard['passive_policy']['resistors'][part['part_id']]['tolerance_percent']/100
            row['candidate_meets_tolerance_target'] = ratings['tolerance_fraction'] <= row['existing_tolerance_target_fraction']
            row['power_rating_W_at_70C'] = ratings['power_W_at_70C']
        result[ref] = row
    def setrows(refs, model, metrics, remaining):
        for ref in refs:
            result[ref].update(model=model, metrics=metrics, remaining=remaining)
    for ref in ('R7101','R7102'):
        setrows([ref], 'Ideal negative-reference unity inverter; 5 V across each resistor.',
                {'normal_drop_V':5,'normal_power_W':power(5,value(ref)), 'fixed_5V_power_at_Rmin_W':power(5,value(ref),.001)},
                'Independent tolerance allows 10.010 mV ratio error at 5 V before drift; reference accuracy allocation remains open.')
    setrows(['R7103'], 'Loaded only by the retained 100 kohm lower divider and ideal buffer input.',
            divider(5,value('R7103'),value('R7104')), 'Input bias and ratio/temperature error remain; divider dissipation is derived.')
    for ref, lower in [('R7106','R7105'),('R7110','R7109')]:
        normal = divider(5,value(ref),value(lower))
        normal['enable_grounded_power_W_at_Rmin'] = power(5,value(ref),.001)
        setrows([ref], '5 V digital enable feed into 100 kohm pull-down, excluding logic-input leakage/clamps.', normal,
                'Normal and enable-grounded power are bounded at nominal 5 V. Missing rails or pin clamp behavior require device sequencing evidence, not patch-input fault assumptions.')
    setrows(['R7108','R7112'], 'Series input resistor: DC drop is input/clamp leakage times resistance, not full signal amplitude.',
            {'drop_V_per_nA':1e-9*value('R7108'),'conditional_24V_power_W':power(24,value('R7108'),.001),
             'condition':'Both nodes within nominal +/-12 V; not proof the protection enforces this during every fault.'},
            'Device leakage versus temperature and actual clamp/rail fault states remain; 200 nA would consume the entire 2 mV static budget across 10 kohm.')
    setrows(['R7113'], 'Internal driver current obligation is at most 2 mA DC; feedback senses after isolation.',
            {'conditional_current_A':.002,'power_at_Rmax_W':.002**2*value('R7113')*1.001,
             'drop_at_Rmax_V':.002*value('R7113')*1.001,'conditional_24V_power_W':power(24,value('R7113'),.001)},
            'Continuous internal-harness short is not qualified by the 2 mA normal-load obligation. Harness <=300 mm and <=1 nF still needs loop stability verification.')
    setrows(['R7114'], 'Feedback-input bias sensitivity; no ideal DC load through the feedback resistor.',
            {'drop_V_per_nA':1e-9*value('R7114'),'C_FAST_F':value('C7103'),
             'feedback_R_C_frequency_Hz':1/(2*math.pi*value('R7114')*value('C7103'))},
            'RC frequency is not loop crossover or phase margin; finite op-amp gain, harness capacitance and loading remain technical verification work.')
    for ref in ('R7115','R7119'):
        setrows([ref], 'Nominal wiper bias-return current <=5 V / 10 Mohm, excluding input leakage.',
                {'dc_drop_bound_V':5/1e7*value(ref),'dc_power_bound_W':(5/1e7)**2*value(ref)},
                'Loaded control law and bias sensitivity are calculated separately; DC filter charging pulses need separate treatment.')
    for ref in ('R7116','R7120'):
        setrows([ref], 'Nominal wiper range +/-5 V to ground.',
                {'normal_power_W':power(5,value(ref)), 'fixed_5V_power_at_Rmin_W':power(5,value(ref),.01),
                 'open_wiper_offset_V_per_nA':1e-9*value(ref)},
                'An open wiper exposes 10 mV per nA leakage sensitivity; failsafe is a tendency, not a guaranteed zero or precise endpoint.')
    for ref in ('R7130','R7131','R7132'):
        setrows([ref], 'Ideal magnitude-loop sense equals monitor while the amplifier has headroom.',
                {'at_5V_current_A':5/value(ref),'at_5V_power_W':power(5,value(ref)),
                 'at_10V_power_W':power(10,value(ref)), 'conditional_12V_to_ground_power_W':power(12,value(ref),.001)},
                'The output monitor can clip because the ideal A01 sum reaches +/-15 V; LED/op-amp headroom and optical brightness remain. Rail envelope is conditional, not measured.')
    setrows(['R7135'], 'Clip LED path spans +12 V to an open-collector output approaching -12 V.',
            {'zero_LED_drop_current_bound_A':24/(value('R7135')*.999),
             'zero_LED_drop_power_bound_W':power(24,value('R7135'),.001)},
            'Zero LED and transistor drop is a conservative nominal-rail power bound; forward voltage/headroom determine actual brightness. R_LED does not set the +/-10 V comparison threshold.')
    setrows(['C7104'], '10 pF shunts the retained 100 kohm attenuverter feedback resistor.',
            {'ideal_normal_voltage_bound_V':5,'nominal_feedback_pole_Hz':1/(2*math.pi*value('R7118')*value('C7104'))},
            'Ideal frequency-dependent center leakage is derived below. Feedback compensation still requires finite-amplifier stability verification.')
    setrows(['C7105'], '10 nF from bipolar manual-control wiper sense to ground.',
            {'ideal_normal_voltage_bound_V':5,'candidate_voltage_rating_V':50,
             'ideal_full_10V_step_resistive_dissipation_J':.5*value('C7105')*10**2,
             'R7119_initial_10V_step_power_W_at_Rmin':power(10,value('R7119'),.001)},
            'Full reversal is a conditional charging event, not a continuous 100 mW load. Effective capacitance, pulse rating and c_small control-filter dielectric classification remain explicit design decisions.')
    alpha = bipolar_worst_loading(100000,value('R7119'),value('R7120'))
    control = {'scope':'Nominal 100 kohm pot, ideal +/-5 V references, nominal R/C; no temperature, bias, pot tolerance or aging guarantee.',
               'centre':wiper(.5,-5,5,100000,value('R7119'),value('R7120'),value('C7105')),
               'endpoint':wiper(1,-5,5,100000,value('R7119'),value('R7120'),value('C7105')),
               'worst_loading_alpha':alpha,
               'worst_loading':wiper(alpha,-5,5,100000,value('R7119'),value('R7120'),value('C7105'))}
    frequency = assumptions['audio_frequency_sensitivity_Hz']
    r,c = value('R7118'),value('C7104')
    ac = {'scope':'Equal nominal 100 kohm resistors, infinite op-amp, ideal alpha=0.5, IN_REMOTE=IN_BUFFER; excludes pot loading and parasitics. 20 kHz is a proposed sensitivity, not an approved requirement.',
          'center_transfer_magnitude':abs(attenuation(.5,frequency,r,c)),
          'negative_endpoint_transfer_magnitude':abs(attenuation(0,frequency,r,c)),
          'frequency_Hz':frequency,'frequency_for_0_5_percent_center_leakage_Hz':.01/math.sqrt(1-.01**2)/(2*math.pi*r*c),
          'closed_loop_stability_proven':False}
    return {'references':result,'manual_control':control,'attenuverter_AC':ac,
            'reference_ratio_error_max_V_at_5V':5*((1.001/.999)-1),
            'individual_tolerance_needed_if_entire_2mV_budget_were_allocated':.002/(10+.002),
            'electrical_acceptance':False,'native_execution':'NONE','candidate_adoption':False}


def validate_evidence(evidence):
    need(evidence['adopted'] is False and evidence['physical_qualified'] is False, 'drawing evidence is not fabrication adoption')
    expected_hashes = {
        'female-pcb':'7407cda816d40767c5e91704643fca147bf3b7481f998b573cec238e577e7269',
        'male-drawing':'9de9adb81c578210219edf3206d81b3952a98a419bac0fef22d8e692d513fbf4',
        'yageo-mount':'591634ace247f61e9c6a263ca1ac98d7672fc163f5e87334c3460956f5c68b7b',
        'RT-series':'00a9148c2958122200e8a93292e389392a795adcfe40562d6ca4f690d1e5d7d1'}
    for sid, sha in expected_hashes.items():
        need(evidence['sources'][sid]['sha256'] == sha and evidence['sources'][sid]['authority'] == 'MANUFACTURER_PRIMARY', 'exact primary drawing/guide '+sid)
    for sex, mpn, view in [('female','09032966824','A'),('male','09031966922','B')]:
        d=evidence['DIN'][sex]
        need(d['mpn'] == mpn and d['view'] == view, 'exact DIN identity/view')
        drawing_coordinates(d)
    female=evidence['DIN']['female'];male=evidence['DIN']['male']
    need(female['fixing_board_holes'] == {'diameter_mm':2.8,'plus_tolerance_mm':.1,'centre_distance_mm':90,'centre_distance_tolerance_mm':.1,'offset_from_row_b_toward_a_mm':.3,'offset_tolerance_mm':.1}, 'female fixing pattern')
    need(male['fixing_board_holes'] is None, 'body flange hole is not PCB hole')
    need(evidence['resistor_mounting']['reflow_mm'] == {'outer_span':2.6,'gap':.8,'pad_length':.9,'pad_width':.8}
         and evidence['resistor_mounting']['wave_mm'] == {'outer_span':2.7,'gap':.9,'pad_length':.9,'pad_width':.8}, 'resistor process-specific mounting')
    curve=evidence['RT_derating']
    need((curve['full_power_temperature_C'],curve['zero_power_temperature_C'],curve['rated_power_W']) == (70,155,.1)
         and curve['installed_thermal_qualified'] is False, 'RT0603 curve is not installed qualification')
    for mpn,sku in [('RT0603BRD0722K1L','YAG1590CT-ND'),('C0603C100J5GACTU','399-C0603C100J5GACTUCT-ND'),('C0603C103J5RACTU','399-C0603C103J5RACTUCT-ND')]:
        source=evidence['sources']['digikey-'+mpn]
        need(source['mpn']==mpn and source['supplier_code_cut_tape']==sku and source['identity_resolved'] is True, 'exact distributor SKU')
        need(source['stock_quantity'] is None and source['allocation_confirmed'] is False
             and source['JLC_LCSC_code'] is None and source['authority']=='SUPPLIER_CATALOG_WEB_EXTRACTION', 'catalog identity is not stock or JLC allocation')
    return True


def protected():
    changed = subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed) <= {REL+'WORK.md'}, 'protected historical bytes changed')
    added = subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    added += subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    allowed = {'scripts/architecture278/implementation/'+n for n in ('stage22_requirements.py','test_stage22_requirements.py')}
    need(all(p.startswith(REL+'stage22/') or p in allowed for p in added), 'out-of-scope addition')
    return {'baseline_commit':BASE,'all_preexisting_bytes_preserved_except':[REL+'WORK.md']}


def validate_criteria(criteria):
    need(criteria['static_target_V'] == .002 and criteria['new_criteria_approved'] is False,
         'retained static criterion changed; rederive budget before use')


def build(check_cache=False):
    files = [ROOT/REL/'stage16/inputs-report.json',ROOT/'design/standard/electrical-standard.json',
             ROOT/REL/'stage21/inventory-input.json', OUT/'assumptions.json', OUT/'evidence.json']
    packages = read(files[0])['packages']; standard,prior,assumptions,evidence = map(read,files[1:])
    criteria = read(ROOT/REL/'stage15/electrical-input.json')['criteria']
    validate_criteria(criteria)
    result = analyze(packages,standard,prior,assumptions)
    result['retained_criteria'] = criteria
    validate_evidence(evidence)
    t=assumptions['local_ambient_sensitivity_C']; rail=assumptions['rail_magnitude_sensitivity_V']
    result['proposed_sensitivity'] = {
        'RT0603_curve_power_W':.1*(155-t)/(155-70),
        'R7135_zero_drop_power_W':power(2*rail,22100,.001),
        'R_SENSE_rail_to_ground_power_W':power(rail,5600,.001),
        'R_LIMIT_12V_external_opposite_internal_rail_power_W':power(12+rail,10000,.001),
        'scope':'Proposed 85 C and +/-13.2 V sensitivity only. No installed thermal or fault qualification.'}
    result['DIN_drawing_view_coordinates_mm'] = {sex:drawing_coordinates(d) for sex,d in evidence['DIN'].items()}
    result['coordinate_scope'] = 'Drawing-view x right / y up, origin at array center. Not a PCB side, assembly transform, footprint or drill tool size.'
    result['preservation'] = protected()
    if check_cache:
        for sid,source in evidence['sources'].items():
            p=ROOT/source['raw_cache'];need(p.is_file() and digest(p)==source['sha256'] and p.stat().st_size==source['bytes'],'evidence bytes '+sid)
            if sid.startswith('digikey-'):
                text=p.read_text();need(source['supplier_code_cut_tape'] in text and 'Manufacturer Product Number  | '+source['mpn'] in text,'supplier identity extraction')
    files += [ROOT/'design/spec/modules/offset.py',ROOT/REL/'stage15/electrical-input.json',OUT/'README.md',Path(__file__),Path(__file__).with_name('test_stage22_requirements.py')]
    result['source_sha256'] = {str(p.relative_to(ROOT)):digest(p) for p in files}
    result['assumptions'] = assumptions
    result['evidence'] = evidence
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-cache',action='store_true');args=p.parse_args()
    body=dump(build(args.check_cache));out=OUT/'requirements-report.json'
    if args.check:need(out.read_text()==body,'Stage22 deterministic report drift')
    else:out.write_text(body)
    print('PASS Stage22 source derivation: 19 passive roles and 192 drawing-view contacts; no adoption or electrical acceptance')


if __name__=='__main__':main()
