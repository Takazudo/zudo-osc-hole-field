"""Stage15 composition and historical preservation; source acceptance only."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import stage11_assessment as common
import stage14_assessment as previous
import stage15_packages as packages

ROOT=common.ROOT
OUT=packages.OUT
BASE='cc005dc4d45bd516f9f00dd91eaa9a4243822b01'
need=common.need


def preserve(scope):
    need(scope['baseline_commit']==BASE,'wrong Stage14 baseline')
    expected=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,*common.PREFIXES],cwd=ROOT,text=True).splitlines())-common.MUTABLE
    need(set(scope['preserved_prior_source_sha256'])==expected,'incomplete historical inventory')
    for name,sha in scope['preserved_prior_source_sha256'].items():
        raw=subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)
        need(hashlib.sha256(raw).hexdigest()==sha and common.digest(ROOT/name)==sha,'prior evidence changed '+name)
    need(scope['instrument_invariants']=={'OSC':5,'functions':33,'fixed_panel_centres':438},'instrument invariant')
    return len(expected)


def check_predecessor():
    preserve(json.loads((OUT/'scope.json').read_text()))
    expected=json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n'
    need((previous.OUT/'assessment-report.json').read_text()==expected,'frozen Stage14 assessment')
    for role in ('root','code','electrical'):
        report=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(report.get('authorship_exclusion') and report.get('source_sha256'),'historical reviewer attribution')
        for path,sha in report['source_sha256'].items():
            actual=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)).hexdigest() if path in common.MUTABLE else common.digest(ROOT/path)
            need(actual==sha,'historical review binding '+path)
    print('PASS Stage14 frozen evidence; mutable integration verified at '+BASE)


def reviews():
    required={'code':['stage15_packages.py','stage15_paths.py','stage15_electrical.py','stage15_assessment.py','check_source.py'], 'electrical':['stage15_packages.py','stage15_paths.py'], 'root':['stage15_electrical.py']}
    for role,names in required.items():
        report=json.loads((OUT/('review-'+role+'.json')).read_text())
        need(report.get('independent_review') is True and report.get('authorship_exclusion'),'independent review '+role)
        common.bindings(report)
        need({f'scripts/architecture278/implementation/{n}' for n in names}<=set(report['source_sha256']),'review coverage '+role)


def build():
    count=preserve(json.loads((OUT/'scope.json').read_text()))
    reports={name:json.loads((OUT/(name+'-report.json')).read_text()) for name in ('package','interfaces','paths','rebudget','electrical')}
    for r in reports.values():common.bindings(r);common.finite(r);common.acceptance(r)
    p=reports['package'];e=reports['electrical'];g=reports['interfaces']
    need(reports['rebudget']['counts']['power_return_endpoints']==108,'return coverage')
    need(e['device']=='LT5400AIMS8E-2#PBF' and e['complete_static_error_bound_V'] is None and e['complete_load_error_bound_V'] is None,'no unsupported whole-cell bound')
    for ref,n in e['networks'].items():
        need(p['placements'][ref]['candidate_MPN']==e['device'],'exact MPN binding')
        need(p['placements'][ref]['pins']['9']==n['EP9']=='AGND' and g['nodes'][ref+':9']['net']=='AGND','shield binding')
        for name,old in n['elements'].items():
            pins=e['pin_pairs'][name]
            need([p['endpoint_aliases'][old+':'+str(i+1)] for i in range(2)]==[ref+':'+pin for pin in pins],'electrical element/graph binding')
        for name in n['unused_elements']:
            for pin in e['pin_pairs'][name]:need(p['placements'][ref]['pins'][pin] is None,'unused resistor termination')
    files=[OUT/'scope.json']+[OUT/(n+'-report.json') for n in reports]+[Path(__file__),Path(__file__).with_name('test_stage15_assessment.py')]
    return {'status':'FINITE STAGE15 SOURCE IMPLEMENTATION COMPLETE; ELECTRICAL ACCEPTANCE OPEN','baseline_commit':BASE,'preserved_predecessor_files':count,'counts':reports['rebudget']['counts'],'disposition':'CONDITIONAL_CANDIDATE; complete2mV static and1mV load-change NOT ESTABLISHED','canonical_source_changed':False,'fixed_controls_preserved':True,'frozen_calibration_unchanged':True,'architecture_adopted':False,'hardware_acceptance':False,'native':'NOT RUN','CAD':'NOT RUN','ERC':'NOT RUN','DRC':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN','source_sha256':{str(p.relative_to(ROOT)):common.digest(p) for p in files}}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--check-predecessor',action='store_true');args=parser.parse_args()
    if args.check_predecessor:check_predecessor();return
    text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';dest=OUT/'assessment-report.json'
    if args.check:need(dest.read_text()==text,'stale Stage15 assessment');reviews()
    else:dest.write_text(text)
    print('PASS Stage15 source composition; hardware acceptance OPEN')
if __name__=='__main__':main()
