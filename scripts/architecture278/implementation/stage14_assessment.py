"""Final Stage14 source/preservation/review gate. No native execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import stage11_assessment as common
import stage13_assessment as previous
import stage14_paths as paths
import stage14_electrical as electrical

ROOT=common.ROOT
OUT=paths.OUT
BASE='df671f7a1e2598de3294f375509d8a73dc508d9d'
need=common.need


def preserve(scope):
    need(scope['baseline_commit']==BASE,'incorrect Stage13 baseline')
    expected=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,*common.PREFIXES],cwd=ROOT,text=True).splitlines())-common.MUTABLE
    need(set(scope['preserved_prior_source_sha256'])==expected,'incomplete preserved inventory')
    for name,sha in scope['preserved_prior_source_sha256'].items():
        raw=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        need(hashlib.sha256(raw).hexdigest()==sha and common.digest(ROOT/name)==sha,'prior evidence changed '+name)
    need(scope['instrument_invariants']=={'OSC':5,'functions':33,'fixed_panel_centres':438},'instrument scope changed')
    return len(expected)


def historical_review_binding(path,sha):
    if path in common.MUTABLE:
        raw=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        need(hashlib.sha256(raw).hexdigest()==sha,'historical Stage13 binding changed '+path)
    else:
        need(common.digest(ROOT/path)==sha,'frozen Stage13 binding changed '+path)


def check_predecessor():
    preserve(json.loads((OUT/'scope.json').read_text()))
    expected=json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n'
    need((previous.OUT/'assessment-report.json').read_text()==expected,'stale frozen Stage13 assessment')
    for role in ('root','code','electrical','mechanical'):
        report=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(report.get('authorship_exclusion') and report.get('source_sha256'),'missing historical review')
        for path,sha in report['source_sha256'].items():historical_review_binding(path,sha)
    print('PASS frozen Stage13 evidence/reviews; mutable integration checked at '+BASE)


def reviews():
    for role in ('code','electrical'):
        report=json.loads((OUT/('review-'+role+'.json')).read_text())
        need(report.get('authorship_exclusion') and report.get('independent_review') is True,'independent review missing')
        common.bindings(report)
        required=['design/architecture-278/implementation/STAGE14.md']
        if role=='code':required+=['scripts/architecture278/implementation/check_source.py',
                                  'scripts/architecture278/implementation/stage14_assessment.py',
                                  'scripts/architecture278/implementation/stage14_paths.py']
        else:required+=['scripts/architecture278/implementation/stage14_electrical.py',
                       'design/architecture-278/implementation/stage14/electrical-input.json']
        need(set(required)<=set(report['source_sha256']),'review coverage incomplete '+role)


def build():
    scope=json.loads((OUT/'scope.json').read_text());count=preserve(scope)
    for name in ('interfaces','paths','rebudget','electrical'):
        report=json.loads((OUT/(name+'-report.json')).read_text())
        common.bindings(report);common.finite(report);common.acceptance(report)
    rebudget=json.loads((OUT/'rebudget-report.json').read_text())
    assessment=json.loads((OUT/'electrical-report.json').read_text())
    need(rebudget['counts']['power_return_endpoints']==106,'endpoint omission')
    need(assessment['disposition']=='CONDITIONAL_CANDIDATE' and
         assessment['startup_time_upper_bound_s'] is None and assessment['discharge_time_upper_bound_s'] is None,
         'unsupported disposition or timing guarantee')
    files=[OUT/(name+'.json') for name in ('scope','interfaces-report','paths-report','rebudget-report','electrical-input','electrical-report')]
    files += [Path(__file__),Path(__file__).with_name('test_stage14_assessment.py')]
    return {'status':'FINITE STAGE14 COMPLETE AS SOURCE WORK; ACCEPTANCE OPEN',
            'baseline_commit':BASE,'preserved_predecessor_files':count,
            'counts':rebudget['counts'],'disposition':assessment['disposition'],
            'validation_case_count':len(assessment['validation_cases']),
            'frozen_calibration_unchanged':True,'mechanical_support_strap_geometry_unchanged':True,
            'canonical_source_changed':False,'architecture_adopted':False,'hardware_acceptance':False,
            'native':'NOT RUN','CAD':'NOT RUN','ERC':'NOT RUN','DRC':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN',
            'source_sha256':{str(p.relative_to(ROOT)):common.digest(p) for p in files}}


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-predecessor',action='store_true');args=p.parse_args()
    if args.check_predecessor:check_predecessor();return
    text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';target=OUT/'assessment-report.json'
    if args.check:
        need(target.read_text()==text,'stale Stage14 composition');reviews()
    else:target.write_text(text)
    print('PASS Stage14 final source composition; acceptance OPEN')
if __name__=='__main__':main()
