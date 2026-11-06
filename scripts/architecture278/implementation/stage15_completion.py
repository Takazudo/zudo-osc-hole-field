"""Analysis-only continuation guard; preserve all Stage15 hardware and historical evidence."""
import argparse
import json
import hashlib
import subprocess
from pathlib import Path
import stage15_assessment as previous
import stage11_assessment as common
ROOT=common.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage15-completion'
BASE='10e3fbbdc2fcfe954da7aa7df5b02db1230ff8f0'
need=common.need

def preserve():
    scope=json.loads((OUT/'scope.json').read_text())
    need(scope['baseline_commit']==BASE,'wrong baseline')
    names=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,*common.PREFIXES],cwd=ROOT,text=True).splitlines())-common.MUTABLE
    need(set(scope['preserved_prior_source_sha256'])==names,'complete historical inventory')
    for name,sha in scope['preserved_prior_source_sha256'].items():
        need(common.digest(ROOT/name)==sha==hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest(),'preserved '+name)
    return len(names)

def predecessor():
    preserve()
    need((previous.OUT/'assessment-report.json').read_text()==json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n','frozen Stage15 assessment')
    for role in ('root','code','electrical'):
        r=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(r.get('authorship_exclusion'),'prior authorship')
        for name,sha in r['source_sha256'].items():
            actual=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest() if name in common.MUTABLE else common.digest(ROOT/name)
            need(actual==sha,'prior review '+name)

def build():
    count=preserve()
    reports={n:json.loads((OUT/(n+'-report.json')).read_text()) for n in ('allocation','load')}
    for r in reports.values():common.bindings(r);common.finite(r);common.acceptance(r)
    a=reports['allocation'];need(len(a['scenarios'])==16,'all counterfactuals')
    for s in a['scenarios']:
        need(len(s['state_rows'])==10,'all states')
        for r in s['state_rows']:need(bool(r['conditioned_output_load_cases']),'load computed')
    need(not a['hardware_acceptance'] and not a['component_geometry_changed'],'analysis scope')
    files=[OUT/'scope.json',OUT/'allocation-report.json',OUT/'load-report.json',Path(__file__),ROOT/'design/architecture-278/implementation/STAGE15-ALLOCATION.md']
    return {'status':'FINITE WHOLE-CELL ANALYSIS COMPLETE; PRECISION NOT ESTABLISHED','baseline_commit':BASE,'preserved_predecessor_files':count,'states':10,'counterfactual_combinations':16,'recommendation':'No single listed correction suffices; jointly address reference inverter, attenuverter ratio and both control loading terms, then reference accuracy and compatible amplifier/input/output allocation. No implementation authorized by this report.','hardware_acceptance':False,'component_geometry_changed':False,'frozen_calibration_unchanged':True,'native':'NOT RUN','CAD':'NOT RUN','ERC':'NOT RUN','DRC':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN','source_sha256':{str(p.relative_to(ROOT)):common.digest(p) for p in files}}

def reviews():
    required={'root':{'stage15_load_allocation.py','test_stage15_load_allocation.py','test_stage15_completion.py','test_stage15_allocation_independent.py'},'code':{'stage15_allocation.py','stage15_load_allocation.py','stage15_completion.py','check_source.py'},'electrical':{'stage15_allocation.py','stage15_completion.py'}}
    for role in ('root','code','electrical'):
        r=json.loads((OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'review authorship '+role)
        common.bindings(r)
        need({Path(n).name for n in r['source_sha256']} >= required[role],'review coverage '+role)

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-predecessor',action='store_true');args=p.parse_args()
    if args.check_predecessor:predecessor();print('PASS frozen Stage15 evidence at '+BASE);return
    text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';dest=OUT/'assessment-report.json'
    if args.check:need(dest.read_text()==text,'stale completion assessment');reviews()
    else:dest.write_text(text)
    print('PASS finite whole-cell analysis; electrical acceptance OPEN')
if __name__=='__main__':main()
