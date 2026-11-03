"""Independent Stage13 composition: candidate source checks, no execution admission."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

import stage11_assessment as common

ROOT = common.ROOT
OUT = ROOT / 'design/architecture-278/implementation/stage13'
BASE = '5452566c3622f8c382f5be026f23b29b511abdca'
need = common.need
digest = common.digest


def preserve(scope):
    need(scope['baseline_commit'] == BASE, 'wrong Stage12 baseline')
    paths = set(subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', BASE, *common.PREFIXES],
        cwd=ROOT, text=True).splitlines()) - common.MUTABLE
    hashes = scope['preserved_prior_source_sha256']
    need(set(hashes) == paths and len(paths) == 289, 'incomplete frozen predecessor inventory')
    for path, sha in hashes.items():
        raw = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
        need(hashlib.sha256(raw).hexdigest() == sha and digest(ROOT / path) == sha,
             'frozen predecessor changed ' + path)
    need(scope['instrument_invariants'] == {'OSC': 5, 'functions': 33, 'fixed_panel_centres': 438},
         'instrument scope changed')
    return len(paths)


def reviews():
    for role in ('root', 'code', 'electrical', 'mechanical'):
        path = OUT / ('review-' + role + '.json')
        need(path.exists(), 'missing independent review ' + role)
        report = json.loads(path.read_text())
        need(bool(report.get('authorship_exclusion')), 'review authorship boundary')
        common.bindings(report)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-11)


def independent_transfer(params, vin, cv, a, x):
    """Closed-form reduction independent of the authored calibration solver."""
    get = lambda key, default=1: params.get(key, default)
    err = params.get('errors', {})
    e = lambda key: err.get(key, 0)
    ra, rp = get('ra', 10000), get('rp', 100000)
    series, load = get('rseries', 1000), get('rload', 1e7)
    beta = a * load / (load + series + ra * a * (1-a))
    damp = load / (load + series + rp * x * (1-x))
    ka, kn, ga, gm, gc, gr = [get(key) for key in ('ka','kn','ga','gm','gcv','gr')]
    ref = get('ref', 5) + e('REF_positive')
    atten = (1+ka) * (beta*(vin+e('IN_buffer')+e('remote_buffer')) + e('atten_amp')) - ka*(vin+e('IN_buffer'))
    manual = damp * ((1-x)*(-kn*ref+(1+kn)*e('REF_negative')) + x*ref) + e('manual_amp')
    return gr*(ga*atten+gm*manual+gc*(cv+e('CV_buffer'))-(1+ga+gm+gc)*e('summer')) + (1+gr)*e('restore') + e('output')


def calibration(report):
    need(report['existing_controls'] == {'ATTEN':'RV1307','OFFSET':'RV1308'}, 'invented calibration actuator')
    obs = report['observability']
    need(obs['generic_control_rank'] == 2 and obs['mathematical_identification_rank'] == 3 and
         obs['single_zero_input_observation_rank'] == 1, 'observation and actuator rank conflated')
    need(obs['control_jacobian_structure'] == [['dG_IN/da',0],[0,0],['dB/da','dB/dx']], 'control coupling omitted')
    need(report['criteria']['static_target_V'] == .002 and report['criteria']['load_induced_target_V'] == .001,
         'retained criteria changed')
    need(report['complete_static_criterion_met'] is None and report['load_criterion_met'] is None,
         'unqualified calibration acceptance')
    names = [row['name'] for row in report['cases']]
    expected = {'nominal'} | {f'stage12_case{i}_{label}' for i in range(5)
                            for label in ('minimum_error','maximum_error')}
    need(len(names) == len(set(names)) and expected == set(names), 'missing retained calibration case')
    old_budget = json.loads((OUT.parent/'stage12/budget-report.json').read_text())
    expected_params = {'nominal':{}}
    for i,row in enumerate(old_budget['coherent_physical_resistor_corners']):
        for label in ('minimum_error','maximum_error'):
            R = {r:1+fraction for r,fraction in row[label]['physical_resistor_fraction'].items()}
            expected_params[f'stage12_case{i}_{label}'] = {'ka':R['R7118']/R['R7117'], 'ga':R['R7124']/R['R7121'],
                'gm':R['R7124']/R['R7122'], 'gcv':R['R7124']/R['R7123'], 'gr':R['R7126']/R['R7125'], 'kn':R['R7102']/R['R7101']}
    need(all(row['params']==expected_params[row['name']] for row in report['cases']), 'retained physical corner parameters')
    residual_count = 0
    extra = report['offset_coupling_examples']
    need(len(extra)==2, 'offset coupling/stress coverage')
    combined = report['cases'] + [{'name':'offset_example', 'params':r['params'], 'bounded_presets':[r['preset']]} for r in extra]
    for case in combined:
        params = case['params']
        presets = case['bounded_presets']
        need([p['requested_gain'] for p in presets] == ([0] if case['name']=='offset_example' else [-1,0,1]), 'missing endpoint/centre observation')
        for preset in presets:
            a, x = [preset[key]['setting'] for key in ('atten_setting','offset_setting')]
            need(0 <= a <= 1 and 0 <= x <= 1, 'control setting outside physical range')
            base = independent_transfer(params,0,0,a,x)
            coefficients = {'IN_gain': independent_transfer(params,1,0,a,x)-base,
                            'CV_gain': independent_transfer(params,0,1,a,x)-base, 'offset_V':base}
            need(all(close(preset['observed_coefficients'][key], val) for key,val in coefficients.items()),
                 'incorrect actual control coefficients')
            jac = preset['actual_control_jacobian']
            h = 1e-5
            left_a, right_a = max(0,a-h), min(1,a+h)
            left_x, right_x = max(0,x-h), min(1,x+h)
            gain = lambda aa: independent_transfer(params,1,0,aa,x)-independent_transfer(params,0,0,aa,x)
            expected_jac = [[(gain(right_a)-gain(left_a))/(right_a-left_a),0], [0,0],
                            [(independent_transfer(params,0,0,right_a,x)-independent_transfer(params,0,0,left_a,x))/(right_a-left_a),
                             (independent_transfer(params,0,0,a,right_x)-independent_transfer(params,0,0,a,left_x))/(right_x-left_x)]]
            need(all(math.isclose(jac[i][j],expected_jac[i][j],rel_tol=1e-5,abs_tol=1e-8)
                     for i in range(3) for j in range(2)), 'control sensitivity derivative')
            fit = preset['mathematical_fit']
            need(fit['realized_in_hardware'] is False and preset['load_criterion_met'] is None and
                 preset['complete_static_criterion_met'] is None, 'mathematical fit promoted to hardware')
            rows = preset['residuals']
            need(len(rows)==9 and {(r['vin_V'],r['CV_V']) for r in rows} ==
                 {(v,c) for v in (-5,0,5) for c in (-5,0,5)}, 'residual grid incomplete')
            for row in rows:
                val = independent_transfer(params,row['vin_V'],row['CV_V'],a,x)
                target = preset['requested_gain']*row['vin_V'] + row['CV_V']
                need(close(row['actual_loaded_model_V'],val) and close(row['target_V'],target) and
                     close(row['residual_V'],val-target), 'calibration residual arithmetic')
                need(row['output_load_change_V'] is None and row['actual_headroom_proven'] is False,
                     'unknown load/headroom promoted')
            need(close(preset['maximum_abs_DC_model_residual_V'],max(abs(r['residual_V']) for r in rows)) and
                 close(preset['CV_only_residual_at5V'],5*(coefficients['CV_gain']-1)), 'hidden CV residual')
            for key, fn, target in (
                ('atten_setting', lambda aa: independent_transfer(params,1,0,aa,.5)-independent_transfer(params,0,0,aa,.5), preset['requested_gain']),
                ('offset_setting', lambda xx: independent_transfer(params,0,0,a,xx), 0)):
                setting = preset[key]
                lo, hi = fn(0), fn(1)
                need(close(setting['interval'][0],lo) and close(setting['interval'][1],hi) and
                     close(setting['achieved'],fn(setting['setting'])), 'setting interval detached')
                need(setting['reachable'] == (lo <= target <= hi), 'unreachable preset promoted')
                need(close(setting['achieved'],min(max(target,lo),hi)), 'bounded setting not solved')
            residual_count += len(rows)
    saturations = report['saturation_cases']
    need(len(saturations)==4 and {(r['gain_setting'],r['vin_V']) for r in saturations}=={(g,v) for g in (-1,1) for v in (-5,5)}, 'saturation case coverage')
    for row in saturations:
        vin = row['vin_V']; x = 1 if vin>0 else 0
        val = independent_transfer({},vin,vin,(row['gain_setting']+1)/2,x)
        need(row['CV_V']==vin and row['manual_pot_setting']==x and close(row['mathematical_output_V'],val) and
             row['over_supply_rail']==(abs(val)>=12) and row['hardware_output_V'] is None, 'overrail arithmetic/acceptance')
    return {'cases':len(names), 'residual_points':residual_count, 'hardware_calibration_qualified':False}


def capacitor_package(cap, package, inventory, before, graph):
    expected = {'C7101':('T491C475K050AT',4.7e-6,50,1.4,[6.3,3.5,2.8]),
                'C7102':('T491D226K035AT',22e-6,35,.7,[7.6,4.6,3.1])}
    need(set(cap['parts']) == set(package['overlays']) == set(expected), 'capacitor/package scope mismatch')
    places = package['placements']
    need(set(places)==set(inventory['packages']) and len(places)==90, 'whole package inventory')
    for ref, source in inventory['packages'].items():
        need(places[ref]['pins']==source['pins'] and places[ref]['units']==source['units'], 'source topology changed')
        if ref not in expected:
            need(places[ref]==before['placements'][ref], 'unrelated package relocated')
    for ref,(mpn,C,V,esr,body) in expected.items():
        row = cap['parts'][ref]
        place = places[ref]
        geom = place['candidate_geometry_source']
        need(row['MPN']==place['candidate_MPN']==mpn and row['nominal_F']==C and
             row['rated_voltage_at85C_V']==V and row['ESR_max_100kHz25C_ohm']==esr and
             row['body_max_mm']==geom['body_max_mm']==body, 'exact capacitor identity/geometry mismatch')
        need(all(close(a,b) for a,b in zip(row['initial_120Hz25C_interval_F'],[C*.9,C*1.1])), 'initial capacitance arithmetic')
        for t,delta in (('-55',.1),('85',.1),('125',.2)):
            need(all(close(a,b) for a,b in zip(row['temperature_qualification_intervals_F'][t],[C*.9*(1-delta),C*1.1*(1+delta)])), 'temperature qualification arithmetic')
        need(row['effective_service_C_guaranteed_F'] is None and row['DC_bias_numeric_guarantee'] is None and
             row['continuous_reverse_allowed'] is False, 'conditional evidence promoted')
        need(row['startup']['actual_peak_inrush_A'] is None and row['startup']['actual_startup_time_s'] is None,
             'startup qualification invented')
        need(place['board']=='A01-core' and place['side']=='rear', 'candidate board face changed')
        for pin, local in (('1',row['pin1_positive_local_xy_mm']),('2',row['pin2_negative_local_xy_mm'])):
            need(all(close(a,b) for a,b in zip(geom['pads_mm'][pin],local)) and geom['pad_sizes_mm'][pin]==row['land_pad_size_xy_mm'], 'polarity or land mismatch')
            x,y = -local[0],local[1]
            for _ in range(place['quarter_turn']): x,y = -y,x
            target = [place['origin_mm'][0]+x,place['origin_mm'][1]+y,70.8]
            need(all(close(a,b) for a,b in zip(place['pads_xyz_mm'][pin][0],target)), 'candidate pad transform')
    comparison = cap['output_comparison']
    need(comparison['ESR_max_100kHz25C_ohm']==.7 and comparison['stability_qualified'] is False and
         comparison['noise_1_to1p5ohm_recommendation_established'] is False and
         comparison['full_temperature_frequency_ESR_ohm'] is None, 'ESR condition or noise conflation')
    need(cap['conservation']['packages']==90 and cap['conservation']['units']==118 and
         cap['conservation']['changed_refs']==sorted(expected) and
         cap['conservation']['unchanged_refs']==sorted(set(places)-set(expected)), 'capacitor conservation')
    paths = package['local_reference_pad_paths']
    need(len(paths)==6 and {p['from'] for p in paths}=={r+':'+pin for r in ('C7101','C7102','C7107') for pin in ('1','2')}, 'bypass/return coverage')
    for row in paths:
        ref,pin = row['from'].split(':')
        dest,dp = row['to'].split(':')
        start,end = places[ref]['pads_xyz_mm'][pin][0],places[dest]['pads_xyz_mm'][dp][0]
        old = before['placements'][ref]['pads_xyz_mm'][pin][0]
        need(dest=='U7101' and places[ref]['pins'][pin]==places[dest]['pins'][dp]==row['net'] and
             row['from_xyz_mm']==start and row['to_xyz_mm']==end, 'bypass actual net/pad mismatch')
        need(close(row['before_straight_floor_mm'],math.dist(old,end)) and close(row['after_straight_floor_mm'],math.dist(start,end)) and
             close(row['after_rectilinear_floor_mm'],sum(abs(a-b) for a,b in zip(start,end))), 'bypass separation arithmetic')
    invalidation = package['endpoint_delta_and_invalidation']
    need(invalidation['current_overlay_complete_path_metrics'] is None, 'stale full path metrics promoted')
    rows = invalidation['changed_source_pads']
    need(len(rows)==4 and {r['node'] for r in rows}=={r+':'+p for r in expected for p in ('1','2')}, 'changed endpoint coverage')
    for row in rows:
        ref,pin = row['node'].split(':')
        need(row['before_xyz_mm']==graph['nodes'][row['node']]['pad_xyz_mm'] and
             row['after_xyz_mm']==places[ref]['pads_xyz_mm'][pin][0] and
             row['invalidated_incident_graph_edges']==[i for i,e in enumerate(graph['edges']) if row['node'] in (e['from'],e['to'])], 'moved endpoint invalidation')
    return {'packages_preserved':90,'units_preserved':118,'local_pad_paths':6,'changed_pad_endpoints':4,
            'full_overlay_paths_qualified':False,'capacitor_application_qualified':False}


def historical_review_binding(path, sha, current_digest=digest):
    """Historical mutable integration bytes are checked at the reviewed checkpoint."""
    if path in common.MUTABLE:
        raw = subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        need(hashlib.sha256(raw).hexdigest()==sha, 'historical integration binding mismatch '+path)
    else:
        need(current_digest(ROOT/path)==sha, 'frozen historical review source changed '+path)


def check_predecessor():
    import stage12_assessment as prior
    preserve(json.loads((OUT/'scope.json').read_text()))
    text = json.dumps(prior.build(),sort_keys=True,indent=2,allow_nan=False)+'\n'
    need((prior.OUT/'assessment-report.json').read_text()==text, 'stale Stage12 report')
    for role in ('root','code','electrical','mechanical'):
        report=json.loads((prior.OUT/('review-'+role+'.json')).read_text())
        need(bool(report.get('authorship_exclusion')) and bool(report.get('source_sha256')), 'historical review incomplete')
        for path,sha in report['source_sha256'].items():
            historical_review_binding(path,sha)
    print('PASS frozen Stage12 report/reviews; historical integration bytes verified at '+BASE)


def build():
    paths = {name: OUT / (name + '.json') for name in
             ('scope', 'capacitor-report', 'package-report', 'calibration-report')}
    reports = {name: json.loads(path.read_text()) for name, path in paths.items()}
    count = preserve(reports['scope'])
    for name in ('capacitor-report', 'package-report', 'calibration-report'):
        common.bindings(reports[name])
        common.finite(reports[name])
        common.acceptance(reports[name])
    calibration_counts = calibration(reports['calibration-report'])
    prior_paths = [OUT.parent/'stage10'/(name+'.json') for name in ('inventory-report','mechanical-report','interfaces-report')]
    cross = capacitor_package(reports['capacitor-report'],reports['package-report'],*[json.loads(p.read_text()) for p in prior_paths])
    sources = [*paths.values(), *prior_paths, Path(__file__), Path(common.__file__),
               Path(__file__).with_name('test_stage13_assessment.py')]
    return {
        'status': 'BOUNDED A01 SOURCE STUDY; ACCEPTANCE OPEN',
        'baseline_commit': BASE,
        'preserved_predecessor_files': count,
        'calibration_crosscheck': calibration_counts,
        'capacitor_package_crosscheck':cross,
        'instrument_invariants': reports['scope']['instrument_invariants'],
        'strap_cassette_support_changed': False,
        'dual_resistance_reports_changed': False,
        'canonical_source_changed': False,
        'architecture_adopted': False, 'hardware_acceptance': False,
        'native': 'NOT RUN', 'ERC': 'NOT RUN', 'DRC': 'NOT RUN',
        'simulation': 'NOT RUN', 'physical': 'NOT RUN',
        'source_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sources},
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--check-predecessor', action='store_true')
    args = parser.parse_args()
    if args.check_predecessor:
        check_predecessor()
        return
    text = json.dumps(build(), sort_keys=True, indent=2, allow_nan=False) + '\n'
    path = OUT / 'assessment-report.json'
    if args.check:
        need(path.read_text() == text, 'stale Stage13 assessment')
        reviews()
    else:
        path.write_text(text)
    print('PASS Stage13 source composition; acceptance OPEN')


if __name__ == '__main__':
    main()
