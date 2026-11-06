"""Bounded source proposal and allocation; no native tools or adopted circuit edits."""
import argparse
import datetime
import hashlib
import json
import math
import re
from pathlib import Path
import subprocess
import stage22_requirements as prior
import stage23_jlc as catalog

ROOT = Path(__file__).resolve().parents[3]
REL = 'design/architecture-278/implementation/'
OUT = ROOT / REL / 'stage25'
BASE = '88b75411d61d705fd5c89281b62b3462837db007'
TERMS = (
    'achieved_baseline_setting', 'measurement_uncertainty',
    'external_input_and_protection_change', 'amplifier_bias_commonmode_and_nonlinearity_change',
    'reference_control_and_ratio_change', 'source_receiver_return_change',
    'output_loading_and_finite_gain_change', 'noise_aging_and_repeatability_change',
)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_text())


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def supplier_observation(html, code):
    blocks = re.findall(r'self\.__next_f\.push\((\[1,.*?\])\)</script>', html)
    frames = catalog.flight_frames(''.join(json.loads(b)[1] for b in blocks))
    decoder = json.JSONDecoder()
    merged = {}
    for body in frames.values():
        for match in re.finditer(r'"componentInfo":', body):
            row = decoder.raw_decode(body[match.end():].lstrip())[0]
            if isinstance(row, str):
                need(re.fullmatch(r'\$[0-9a-f]+', row) and row[1:] in frames, 'product reference')
                row = decoder.raw_decode(frames[row[1:]])[0]
            need(isinstance(row, dict) and row.get('componentCode') == code, 'exact supplier code')
            for key in catalog.KEYS:
                if key in row and row[key] != '$undefined':
                    need(key not in merged or merged[key] == row[key], 'conflicting supplier field')
                    merged[key] = row[key]
    need(merged, 'missing supplier product')
    visible = catalog.Visible(); visible.feed(html)
    merged['visible_services'] = {key: sorted({visible.parts[i+1] for i,t in enumerate(visible.parts[:-1]) if t == key})
                                  for key in ('Assembly Type', 'PCBA Type')}
    merged.update(stock_is_allocated=False, order_accepted=False)
    return merged


def positive(*values):
    need(all(type(x) in (float, int) and math.isfinite(x) and x > 0 for x in values), 'positive finite domain')


def validate_receipt(receipt):
    need(receipt['final_url'] == receipt['url'], 'unexpected source redirect')
    stamp = datetime.datetime.fromisoformat(receipt['retrieved_UTC'])
    need(stamp.tzinfo is not None and stamp.utcoffset() == datetime.timedelta(0), 'UTC retrieval timestamp required')
    need(re.fullmatch('[0-9a-f]{64}', receipt['sha256']) is not None
         and receipt['sha256'] != '0'*64 and type(receipt['bytes']) is int
         and receipt['bytes'] > 0, 'available source receipt')


def pot_screen(rpot, rseries=1000, rreturn=1e7, cap=1e-8, reference=5):
    positive(rpot, rseries, rreturn, cap, reference)
    alpha = prior.bipolar_worst_loading(rpot, rseries, rreturn)
    result = prior.wiper(alpha, -reference, reference, rpot, rseries, rreturn, cap)
    z = rseries + rpot / 4
    return {
        'worst_nominal_fraction': alpha,
        'maximum_abs_ideal_loading_error_V': abs(result['loading_error_V']),
        'center_source_impedance_before_return_ohm': z,
        'center_bias_impedance_ohm': z * rreturn / (z + rreturn),
        'center_1percent_settling_s': math.log(100) * cap * z * rreturn / (z + rreturn),
        'reference_to_reference_current_A': 2 * reference / rpot,
        'total_track_power_W': (2 * reference) ** 2 / rpot,
        'open_wiper_V_per_nA': rreturn * 1e-9,
        'contact_noise_taper_tracking_and_temperature_guaranteed': False,
    }


def static_allocation(delta, terms):
    need(type(delta) in (int, float) and math.isfinite(delta) and 0 <= delta <= .01, 'matching domain')
    need(set(terms) == set(TERMS), 'complete disjoint remainder ledger')
    for value in terms.values():
        need(value is None or (type(value) in (int, float) and math.isfinite(value) and value >= 0), 'unknown is not zero; nonnegative finite bound')
    ratio = 5 * ((1 + delta) ** 2 - 1)
    known = sum(v for v in terms.values() if v is not None)
    complete = all(v is not None for v in terms.values())
    total = ratio + known if complete else None
    return {'network_ratio_bound_V': ratio, 'one_shared_remainder_V': .002 - ratio,
            'remaining_after_known_terms_V': .002 - ratio - known,
            'terms_V': terms, 'complete_bound_V': total,
            'mathematical_allocation_within_target': total <= .002 if complete else None,
            'hardware_acceptance': False}


def baseline_residual(cv, target, achieved, gain, changes=0):
    need(all(math.isfinite(x) for x in (cv, target, achieved, gain, changes)), 'finite actual setup')
    # Target must be declared before physical adjustment; never redefine it to achieved.
    return achieved - target + (gain - 1) * cv + changes


def hole_route(layers, finish, nominal=1, tighter=False):
    need(type(layers) is int and layers >= 1 and math.isfinite(nominal) and nominal > 0, 'hole route domain')
    eligible = layers >= 4 and finish == 'ENIG' and .55 <= nominal <= 2
    need(not tighter or eligible, 'documented tighter option needs multilayer ENIG and eligible circular hole')
    minus, plus = (.05, .05) if tighter else (.08, .13)
    low, high = nominal - minus, nominal + plus
    return {'diameter_interval_mm': [low, high],
            'diameter_contains_only_drawing_allowed_values': low >= .9 and high <= 1.1,
            'position_guaranteed': False, 'fixing_holes_guaranteed': False,
            'finished_hole_interpretation_confirmed': False, 'complete_route_qualified': False}


def validate_candidate(c, package, metadata):
    need(c['status'] == 'PROPOSED_NOT_ADOPTED' and c['baseline_commit'] == BASE, 'proposal authority')
    need(c['static_target_V'] == .002 and c['load_change_target_V'] == .001, 'fixed criteria')
    need(c['prescribed_voltage_at_knob_positions'] is False, 'owner intended use')
    need(c['hardware_qualification'] is False and c['native_execution'] == 'NONE'
         and c['factory_protocol_approved'] is False and c['approved_temperature_time_envelope'] is None, 'unapproved qualification')
    need(set(c['changes']) == {'RV1308'}, 'bounded one-package candidate')
    change = c['changes']['RV1308']
    need(change['before_mpn'] == package['selected_mpn'] == 'PTV09A-4020F-B104'
         and change['after_mpn'] == 'PTV09A-4020F-B103'
         and change['manufacturer'] == 'Bourns' and change['supplier_code'] == 'C5848782', 'exact candidate identity')
    need(change['before_nominal_ohm'] == 100000 and change['after_nominal_ohm'] == 10000, 'pot values')
    need(change['pins'] == package['pins'] and change['retained_placement'] == package['placement']
         and change['retained_source_unit_metadata'] == metadata, 'pin/NC/geometry/unit identity')
    need(c['retained'] == {'series_ohm':1000, 'return_ohm':10000000, 'cap_F':1e-8,
                          'negative_reference_resistors_ohm':[10000,10000], 'reference':'REF5050AIDR',
                          'amplifier':'OPA4197IPWR', 'spare_RN7102_elements':'R3/R4 both ends remain NC'}, 'unapproved reference/loop change')
    expected = {'pot_tolerance_fraction':.2, 'series_tolerance_fraction':.001,
                'return_tolerance_fraction':.01, 'cap_tolerance_fraction':.05,
                'reference_nominal_V':5, 'reference_initial_fraction':.001,
                'reference_full_box_ppm_per_C':8, 'reference_box_temperature_C':[-40,125],
                'higher_grade_box_ppm_per_C':3, 'pot_temperature_rating_C':[-10,50],
                'pot_power_rating_W':.05, 'pot_voltage_rating_V':20,
                'opamp_bias_25C_A':20e-12, 'opamp_bias_PW_full_temperature_A':15e-9,
                'network_ratio_25C_fraction':.0001, 'network_ratio_full_temperature_fraction':.000125}
    need(c['bounds'] == expected, 'reviewed evidence bounds changed')


def protected():
    changed = subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed) <= {REL+'WORK.md'}, 'protected prior bytes changed')
    added = subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    added += subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    allowed = {'scripts/architecture278/implementation/'+x for x in ('stage25_correction.py','test_stage25_correction.py')}
    need(all(p.startswith(REL+'stage25/') or p in allowed for p in added), 'out-of-scope addition')
    return {'baseline':BASE, 'only_preexisting_mutable_path':REL+'WORK.md'}


def build(check_cache=False):
    files = [OUT/'candidate.json', OUT/'sources.json', OUT/'supplier-observations.json',
             ROOT/REL/'stage16/inputs-report.json', ROOT/REL/'stage18/compatibility-report.json',
             ROOT/REL/'stage15-procedure/owner-decision.json', ROOT/REL/'stage15/electrical-input.json',
             ROOT/'design/standard/electrical-standard.json']
    c, sources, suppliers, inp, parity, owner, electrical, standard = map(read, files)
    validate_candidate(c, inp['packages']['RV1308'], parity['unit_metadata']['RV1308.0'])
    need(owner['prescribed_voltage_at_knob_positions'] is False and owner['criteria_unchanged'], 'retained owner authority')
    need(standard['calibration']['static_precision_error_V'] == .002 and standard['calibration']['precision_output_load_error_V'] == .001, 'canonical fixed criteria')
    need(electrical['matching']['ratio_error_25C_fraction'] == .0001 and electrical['matching']['ratio_error_I_full_temperature_fraction'] == .000125, 'source network bounds')
    need((parity['source_parity']['packages'],parity['source_parity']['physical_pins'],parity['source_parity']['symbol_units']) == (118,561,154), 'full historical source completeness')
    identities = {'C5848782':('PTV09A-4020F-B103','BOURNS','Plugin-3P','Wave Soldering','manualWeld'),
                  'C27804':('REF5050AIDR','Texas Instruments','SOIC-8','SMT Assembly','smtWeld'),
                  'C2057327':('OPA4197IPWR','Texas Instruments','TSSOP-14','SMT Assembly','smtWeld')}
    need(set(suppliers) == set(identities), 'complete supplier observations')
    for code, (mpn,brand,package,service,mode) in identities.items():
        row = suppliers[code]
        need([row[k] for k in ('componentModelEn','componentBrandEn','componentSpecificationEn','assemblyMode')] == [mpn,brand,package,mode]
             and row['componentCode'] == code and row['visible_services'] == {'Assembly Type':[service],'PCBA Type':['Economic and Standard']}, 'exact supplier/assembly identity')
        need(row['stock_is_allocated'] is False and row['order_accepted'] is False, 'no allocation or order')
    for source in sources.values():
        validate_receipt(source)
        if check_cache:
            p = ROOT/source['raw_cache']
            need(sha(p) == source['sha256'] and p.stat().st_size == source['bytes'], 'source receipt bytes')
    expected_urls = {
        'ptv09':'https://www.bourns.com/docs/product-datasheets/PTV09.pdf',
        'ref50':'https://www.ti.com/lit/ds/symlink/ref50.pdf',
        'opa4197':'https://www.ti.com/lit/ds/symlink/opa4197.pdf',
        'jlc-pcb':'https://jlcpcb.com/capabilities/pcb-capabilities',
        'jlc-pad-hole':'https://jlcpcb.com/help/article/difference-and-tolerance-explanation-between-via-and-pad-holes',
        'jlc-assembly':'https://jlcpcb.com/capabilities/pcb-assembly-capabilities',
        **{code:'https://jlcpcb.com/partdetail/'+code for code in identities},
    }
    need({k:v['url'] for k,v in sources.items()} == expected_urls, 'source identity set')
    if check_cache:
        for code in identities:
            need(supplier_observation((ROOT/sources[code]['raw_cache']).read_text(), code) == suppliers[code], 'supplier raw observation drift')
    old = pot_screen(100000); new = pot_screen(10000)
    # Component-tolerance screen only: contact resistance/taper/TC are not silently zeroed.
    corners = [pot_screen(r, s, ret, cap) for r in (8000,12000) for s in (999,1001)
               for ret in (9.9e6,10.1e6) for cap in (.95e-8,1.05e-8)]
    terms = {name:None for name in TERMS}
    b = c['bounds']
    reference_box = 5*b['reference_full_box_ppm_per_C']*1e-6*165
    result = {
        'status':'REVIEWABLE_ONE_PART_CANDIDATE; COMPLETE_ERROR_BOUND_OPEN',
        'dated_supplier_stock':{code:{'observed_quantity':row.get('overseasStockCount'),
                                     'retrieved_UTC':sources[code]['retrieved_UTC'],
                                     'allocated':False,'order_accepted':False}
                                for code,row in suppliers.items()},
        'candidate_change':c['changes'], 'before':old, 'candidate':new,
        'component_corner_screen':{'corners':len(corners),
            'max_abs_loading_V':max(x['maximum_abs_ideal_loading_error_V'] for x in corners),
            'max_center_settling_s':max(x['center_1percent_settling_s'] for x in corners),
            'max_nominal_10V_track_power_W':max(x['total_track_power_W'] for x in corners),
            'max_nominal_10V_track_current_A':max(x['reference_to_reference_current_A'] for x in corners),
            'full_reference_buffer_current_budget_A':None,
            'scope':'Total track current; other buffer loads and asymmetry remain additional. Track rating requires rated conditions, not arbitrary hot derating.'},
        'allocation':{'initial_25C':static_allocation(.0001,terms),
                      'network_I_grade_only':static_allocation(.000125,terms),
                      'equation':'abs(e_setup) + 5*abs(Gcv-1) + sum(disjoint change/uncertainty bounds) <= 0.002',
                      'IN_and_mixed_paths':'Separate gain-setting, nonlinear and headroom characterization; CV-only allocation is not whole-cell acceptance.',
                      'load_change_target_V':.001,'load_change_bound_V':None},
        'reference_alternatives':{
            'retained_initial_source_sensitivity_V':.005,
            'retained_inverter_initial_ratio_sensitivity_V':5*(1.001/.999-1),
            'spare_matched_initial_ratio_sensitivity_V':[.0005,.000625],
            'spare_max_resistance_ohm':107500,
            'spare_bias_25C_table_absolute_sensitivity_V':107500*20e-12,
            'spare_bias_PW_full_temperature_absolute_sensitivity_V':107500*15e-9,
            'spare_between_two_arbitrary_full_temperature_points_sensitivity_V':2*107500*15e-9,
            'spare_adopted':False,'spare_recommendation':'Do not rewire; no CV-slope benefit, tenfold impedance, NC/topology change.',
            'retained_reference_full_spec_box_span_V':reference_box,
            'higher_grade_full_spec_box_span_V':5*3e-6*165,
            'box_not_local_derivative':True,
            'local_temperature_delta_bound_V':None,
            'higher_grade_exact_JLC_candidate_qualified':False,
            'noise_hysteresis_aging_guaranteed_max':False,
            'post_setup_reference_error_bound_V':None},
        'stability':{'new_active_loops':0,'new_direct_capacitive_loads':0,
                     'minimum_filter_series_isolation_ohm':999,
                     'reference_buffer_track_load_min_ohm':8000,
                     'filter_pole_moves_up_factor_nominal':old['center_1percent_settling_s']/new['center_1percent_settling_s'],
                     'existing_reference_output_and_remote_feedback_qualification':'OPEN; unchanged is not proven stable',
                     'loop_phase_margin_degrees':None,'bench':'NOT RUN'},
        'DIN':{'standard':hole_route(4,'ENIG'), 'documented_tighter_diameter':hole_route(4,'ENIG',tighter=True),
               'position_drawing_diameter_mm':.05,'published_position_mm':.075,
               'female_fixing_hole_required_mm':[2.8,2.9],
               'diameter_option_applies_to_female_fixing_holes':False,
               'assembly':'Mixed SMT/THT documented; exact connector/process acceptance unknown',
               'recommended_route':'Retain exact DIN; unsent tighter-hole + position + fixing + solder-process specification.',
               'all_JLC_routes_proven_incompatible':False,'arbitrary_pad_or_hole_enlargement':False},
        'historical_source_counts':parity['source_parity'], 'source_units_retained':True,
        'native_execution':'NONE','next_native_request':'NONE','production_CAD_changed':False,
        'electrical_acceptance':False,'preservation':protected(),
    }
    files += [OUT/'README.md', OUT/'fabrication-request.md', OUT/'evidence.json', Path(prior.__file__), Path(catalog.__file__),
              ROOT/REL/'STAGE15-PROCEDURE.md', ROOT/REL/'STAGE15-INTERPRETATION.md',
              ROOT/REL/'stage22/evidence.json', ROOT/REL/'stage24/definitions.json', ROOT/REL/'stage24/sources.json',
              Path(__file__),Path(__file__).with_name('test_stage25_correction.py')]
    result['source_sha256'] = {str(p.relative_to(ROOT)):sha(p) for p in files}
    return result


def main():
    p=argparse.ArgumentParser(); p.add_argument('--check',action='store_true');p.add_argument('--check-cache',action='store_true');args=p.parse_args()
    body=dump(build(args.check_cache)); dest=OUT/'correction-report.json'
    if args.check:need(dest.read_text()==body,'deterministic correction report drift')
    else:dest.write_text(body)
    print('PASS candidate source/math/preservation; complete electrical and fabrication qualification OPEN; native NONE')


if __name__ == '__main__':
    main()
