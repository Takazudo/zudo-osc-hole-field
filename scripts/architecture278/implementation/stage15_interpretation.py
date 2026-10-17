"""Correct acceptance interpretation without changing historical arithmetic or hardware."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import stage15_completion as previous
import stage11_assessment as common
ROOT=common.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage15-interpretation'
BASE='cc1b3dc68bce927f5299d3e090016f940addca86'
need=common.need

def preserve():
    scope=json.loads((OUT/'scope.json').read_text())
    names=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,*common.PREFIXES],cwd=ROOT,text=True).splitlines())-common.MUTABLE
    need(scope['baseline_commit']==BASE and set(scope['preserved_prior_source_sha256'])==names,'historical inventory')
    for name,sha in scope['preserved_prior_source_sha256'].items():
        need(common.digest(ROOT/name)==sha==hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest(),'preserved '+name)
    return len(names)

def predecessor():
    preserve()
    need((previous.OUT/'assessment-report.json').read_text()==json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n','historical completion report')
    for role in ('root','code','electrical'):
        r=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'historical review authorship')
        for name,sha in r['source_sha256'].items():
            actual=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest() if name in common.MUTABLE else common.digest(ROOT/name)
            need(actual==sha,'historical review binding '+name)

def analyze(standard,allocation,contract):
    precision=next(c for c in standard['cells'] if c['id']=='precision_output')
    note=next(n for n in precision['notes'] if 'after factory calibration' in n)
    need(standard['calibration']['static_precision_error_V']==.002,'unchanged static criterion')
    need(standard['calibration']['precision_output_load_error_V']==.001,'unchanged load criterion')
    need('no load to 10 kohm' in note,'load conditions')
    need(contract['status']=='PROPOSED_UNADOPTED' and not contract['calibration_performed'],'no calibration adoption')
    need(set(contract['lanes'])=={'fixed_setting','paired_CV','calibrated_path','same_setting_load'},'four separate metrics')
    for lane in contract['lanes'].values():
        need(all(k in lane for k in ('stimulus','held_controls','reference','load','allowed_adjustments','metric')),'complete measurement contract')
    need(contract['lanes']['calibrated_path']['acceptance_status']=='OPEN_MISSING_FACTORY_PROCEDURE','no postcal result')
    allfour=next(s for s in allocation['scenarios'] if len(s['removed_nonidealities'])==4)
    rows={r['state']:r for r in allfour['state_rows']}
    manual=rows['manual_high']['with_reference_initial_worst_witness']
    need(abs(manual['fixed_setting_residual_V']-.006001050049998291)<1e-14,'retain manual endpoint number')
    need(manual['signed_terms_V']['CV_slope']==0,'manual endpoint is not CV stimulus')
    cv=rows['CV_only']
    return {'canonical_static_target_V':.002,'canonical_static_condition':'after factory calibration',
        'canonical_load_change_target_V':.001,'canonical_precision_output_note':note,
        'unchanged_diagnostic_numbers':{'existing_sampled_fixed_setting_max_V':allocation['scenarios'][0]['maximum_abs_with_reference_initial_V'],
            'four_idealized_manual_endpoint_max_V':manual['fixed_setting_residual_V'],
            'manual_endpoint_signed_terms_V':manual['signed_terms_V'],
            'four_idealized_CV_5V_fixed_setting_interval_V':cv['with_reference_initial_signed_interval_V'],
            'paired_CV_gain_interval':cv['paired_CV_gain_interval'],
            'paired_CV_10V_span_error_interval_V':cv['paired_CV_10V_span_error_interval_V']},
        'supersedes':['STAGE15-ALLOCATION.md Decision blanket joint-redesign necessity and abandonment of2mV fixed-setting claim as a canonical requirement',
            'stage15-completion/assessment-report.json recommendation','stage15-completion/allocation-report.json single_correction_suffices/joint_four_corrections_suffice as calibrated acceptance conclusions; these remain only fixed-setting diagnostic statements',
            '99.970005ppm reference ceiling as a required product specification; retained only for its hypothetical uncalibrated endpoint budget'],
        'corrected_disposition':'No demonstrated calibrated-path pass or failure and no blanket joint-redesign necessity follows from the fixed-setting matrix. Preserve2mV after-calibration and1mV load-change targets. Define the factory measurement/adjustment contract before selecting any correction.',
        'manual_endpoint_scope':'6.00105mV is manual ±5V endpoint/reference initial sensitivity under four diagnostic idealizations, not external CV transfer or measured post-calibration error.',
        'front_control_limit':'ATTEN changes IN contribution and OFFSET changes manual contribution; neither independently trims external CV gain gr*gcv. Existing two controls cannot independently correct every gain.',
        'product_decision_needed':'Decide whether nominal manual ±5V endpoints and full knob law are precision acceptance requirements, or control range/characterization; approve path-specific factory procedure, permitted adjustments, references and load without assuming calibration can remove every gain error.',
        'measurement_contract':contract,'calibrated_static_residual_V':None,'calibrated_result_status':'NOT MEASURED; factory procedure and permitted adjustments missing',
        'hardware_acceptance':False,'component_geometry_changed':False,'calibration_performed':False,'native':'NOT RUN','CAD':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}

def build():
    count=preserve()
    files=[ROOT/'design/standard/electrical-standard.json',previous.OUT/'allocation-report.json',OUT/'measurement-contract.json']
    r=analyze(*[json.loads(p.read_text()) for p in files])
    files += [ROOT/'doc/src/content/docs/architecture/osc-block-ao.mdx',OUT/'scope.json',ROOT/'design/spec/modules/offset.py',Path(__file__),Path(__file__).with_name('test_stage15_interpretation.py'),ROOT/'design/architecture-278/implementation/STAGE15-INTERPRETATION.md']
    r.update(baseline_commit=BASE,preserved_predecessor_files=count,source_sha256={str(p.relative_to(ROOT)):common.digest(p) for p in files})
    return r

def reviews():
    for role in ('code','electrical'):
        r=json.loads((OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'review authorship')
        common.bindings(r)
        need({'scripts/architecture278/implementation/stage15_interpretation.py','design/architecture-278/implementation/STAGE15-INTERPRETATION.md'}<=set(r['source_sha256']),'review coverage')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-predecessor',action='store_true');args=p.parse_args()
    if args.check_predecessor:predecessor();print('PASS frozen completion evidence; interpretation superseded separately');return
    r=build();common.finite(r);common.acceptance(r);text=json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n';dest=OUT/'interpretation-report.json'
    if args.check:need(dest.read_text()==text,'stale interpretation');reviews()
    else:dest.write_text(text)
    print('PASS corrected acceptance interpretation; no calibrated result or redesign adoption')
if __name__=='__main__':main()
