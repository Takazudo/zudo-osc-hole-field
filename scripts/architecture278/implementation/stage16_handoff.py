"""Propose real-control verification after owner intended-use decision; preserve historical evidence."""
import argparse
import csv
import re
import shutil
import hashlib
import json
import subprocess
from pathlib import Path
import stage15_detent as previous
import stage11_assessment as common
ROOT=common.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage16'
BASE='07d045df573b15e00259200259d44b04fe5f7e8a'
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
    need((previous.OUT/'detent-report.json').read_text()==json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n','historical interpretation report')
    for role in ('code','electrical'):
        r=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'historical review authorship')
        for name,sha in r['source_sha256'].items():
            actual=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest() if name in common.MUTABLE else common.digest(ROOT/name)
            need(actual==sha,'historical review binding '+name)

def build():
    count=preserve()
    inp=json.loads((OUT/'inputs-report.json').read_text());common.bindings(inp)
    need(inp['packages'] and inp['nets'],'complete candidate inputs')
    contract=json.loads((OUT/'execution-contract.json').read_text())
    need(contract['native_admission_granted'] is False and contract['prototype_availability']=='UNCONFIRMED','preparation only')
    files=[ROOT/'scripts/kicad/run.sh',ROOT/'scripts/kicad/pin.env',ROOT/'scripts/kicad/README.md',OUT/'scope.json',OUT/'inputs-report.json',OUT/'execution-contract.json',Path(__file__),Path(__file__).with_name('test_stage16_handoff.py'),ROOT/'design/architecture-278/implementation/STAGE16.md']
    return {'status':'PREPARATION PACKET; NATIVE MATERIALIZATION NOT COMPLETE','baseline_commit':BASE,'preserved_predecessor_files':count,
        'counts':inp['counts'],'materialization_gaps':inp['gaps'],'execution_contract':contract,
        'runnable_now':'python3 scripts/architecture278/implementation/stage16_handoff.py --export-run a01-preflight-001',
        'next_source_action':'Use exported exact BOM/pin-net/NC/placement contracts to implement missing candidate-native asset/schematic adapter in isolation; no geometry/component substitutions. Do not export canonical OFFSET as the candidate.',
        'native_next_action':'Only after actual isolated candidate files and exact-run admission exist, export schematic netlist through pinned10.0.6 and compare an independently extracted observation; then ERC and PCB pad/net/placement/DRC checks under separate exact commands.',
        'prototype_availability':'UNCONFIRMED','hardware_acceptance':False,'component_geometry_changed':False,'native':'NOT RUN','CAD':'NOT RUN','ERC':'NOT RUN','DRC':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN',
        'source_sha256':{str(p.relative_to(ROOT)):common.digest(p) for p in files}}

def safe_source(name):
    p=ROOT/name
    need(not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve().is_relative_to(ROOT.resolve()),'unsafe source path')
    need(p.is_file(),'missing source '+name)
    return p

def run_path(run_id):
    need(re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',run_id) is not None,'invalid isolated run id')
    p=OUT/'runs'/run_id
    need(p.resolve().is_relative_to((OUT/'runs').resolve()) and not (OUT/'runs').is_symlink() and not p.is_symlink(),'unsafe run directory')
    return p

def export_run(run_id):
    packet=build();inp=json.loads((OUT/'inputs-report.json').read_text())
    files={**inp['source_sha256'],**packet['source_sha256']}
    files[str((OUT/'handoff-report.json').relative_to(ROOT))]=common.digest(OUT/'handoff-report.json')
    need((OUT/'handoff-report.json').read_text()==json.dumps(packet,indent=2,sort_keys=True,allow_nan=False)+'\n','stale handoff before export')
    for n,sha in files.items():need(common.digest(safe_source(n))==sha,'export source drift '+n)
    need(sum(safe_source(n).stat().st_size for n in files)<=512*1024*1024,'source export exceeds512MiB limit')
    dest=run_path(run_id);dest.mkdir(parents=True,exist_ok=False)
    copied={}
    for n,sha in sorted(files.items()):
        q=dest/'sources'/n;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe_source(n),q)
        need(common.digest(q)==sha,'copy changed');copied['sources/'+n]=sha
    payload={'packages':inp['packages'],'nets':inp['nets'],'NC_endpoints':inp['NC_endpoints'],'endpoint_aliases':inp['endpoint_aliases'],'network_elements':inp['network_elements'],'transport_contract':inp['transport_contract']}
    q=dest/'candidate.json';q.write_text(json.dumps(payload,indent=2,sort_keys=True,allow_nan=False)+'\n');copied[q.name]=common.digest(q)
    q=dest/'bom.csv'
    with q.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['ref','selected_mpn','identity_status','candidate_footprint','footprint_status'])
        for ref,p in sorted(inp['packages'].items()):w.writerow([ref,p['selected_mpn'] or '',p['identity_status'],p['footprint']['path'] or '',p['footprint']['status']])
    copied[q.name]=common.digest(q)
    q=dest/'pin-net.csv'
    with q.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['ref','pin','net','NC'])
        for ref,p in sorted(inp['packages'].items()):
            for pin,net in sorted(p['pins'].items()):w.writerow([ref,pin,net or '',net is None])
    copied[q.name]=common.digest(q)
    manifest={'schema':1,'run_id':run_id,'candidate_input_sha256':common.digest(OUT/'inputs-report.json'),'preparation_only':True,'native_admission_granted':False,'files':copied}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print('EXPORTED source-only packet '+str(dest));return dest

def verify_export(run_id):
    dest=run_path(run_id);m=json.loads((dest/'manifest.json').read_text())
    need(m['run_id']==run_id and m['preparation_only'] is True and m['native_admission_granted'] is False,'export scope')
    packet=build();inp=json.loads((OUT/'inputs-report.json').read_text())
    sources={**inp['source_sha256'],**packet['source_sha256']}
    sources[str((OUT/'handoff-report.json').relative_to(ROOT))]=common.digest(OUT/'handoff-report.json')
    need(set(m['files'])=={'sources/'+n for n in sources}|{'candidate.json','bom.csv','pin-net.csv'},'incomplete export inventory')
    for name,sha in sources.items():need(m['files']['sources/'+name]==sha,'export manifest source mismatch')
    want={k:inp[k] for k in ('packages','nets','NC_endpoints','endpoint_aliases','network_elements','transport_contract')}
    need(json.loads((dest/'candidate.json').read_text())==want,'candidate payload differs')
    with (dest/'bom.csv').open(newline='') as f:rows=list(csv.reader(f))
    need(rows==[['ref','selected_mpn','identity_status','candidate_footprint','footprint_status']]+[[ref,p['selected_mpn'] or '',p['identity_status'],p['footprint']['path'] or '',p['footprint']['status']] for ref,p in sorted(inp['packages'].items())],'BOM payload differs')
    with (dest/'pin-net.csv').open(newline='') as f:rows=list(csv.reader(f))
    need(rows==[['ref','pin','net','NC']]+[[ref,pin,net or '',str(net is None)] for ref,p in sorted(inp['packages'].items()) for pin,net in sorted(p['pins'].items())],'pin-net payload differs')
    for name,sha in m['files'].items():
        p=dest/name;need(not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve().is_relative_to(dest.resolve()),'unsafe export member')
        need(common.digest(p)==sha,'export drift '+name)
    need(m['candidate_input_sha256']==common.digest(OUT/'inputs-report.json'),'export belongs to different inputs')
    print('PASS exported bytes; no native or hardware evidence')

def compare_observation(obs,inp):
    need(obs['oracle_version']=='10.0.6','exact candidate oracle version required')
    need(obs['candidate_input_sha256']==common.digest(OUT/'inputs-report.json'),'observation input binding')
    need(obs['kind']=='schematic_pin_net_observation','observation lane')
    want={ref:{'pins':p['pins'],'selected_mpn':p['selected_mpn']} for ref,p in inp['packages'].items()}
    need(obs['packages']==want,'observed package/pin/net/MPN mismatch')
    need(obs.get('artifact_sha256') and re.fullmatch('[0-9a-f]{64}',obs['artifact_sha256']),'artifact hash required')
    return {'structural_comparison':'PASS','provenance_verified':False,'native_execution_authorized':False,'hardware_acceptance':False,'scope':'Compares supplied86-circuit-package observation only; transport, symbolunits, footprints, placement andgraphedges are separate unverifiedlanes. Native extraction command/log/artifact provenance and genuine exact-run admission must be independently reviewed; this function cannot attest them.'}

def reviews():
    required={'code':{'stage16_handoff.py','stage16_inputs.py','check_source.py'},'electrical':{'stage16_handoff.py'},'root':{'stage16_inputs.py','test_stage16_inputs.py'}}
    for role,names in required.items():
        r=json.loads((OUT/('review-'+role+'.json')).read_text());need(r.get('independent_review') and r.get('authorship_exclusion'),'review attribution');common.bindings(r)
        need(names<={Path(n).name for n in r['source_sha256']},'review coverage '+role)

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-predecessor',action='store_true');p.add_argument('--export-run');p.add_argument('--verify-export');p.add_argument('--compare-observation',type=Path);args=p.parse_args()
    if args.check_predecessor:predecessor();print('PASS historical detent and all prior evidence');return
    if args.export_run:export_run(args.export_run);return
    if args.verify_export:verify_export(args.verify_export);return
    if args.compare_observation:print(json.dumps(compare_observation(json.loads(args.compare_observation.read_text()),json.loads((OUT/'inputs-report.json').read_text())),indent=2));return
    r=build();common.finite(r);common.acceptance(r);text=json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n';dest=OUT/'handoff-report.json'
    if args.check:need(dest.read_text()==text,'stale handoff');reviews()
    else:dest.write_text(text)
    print('PASS source preparation handoff; no native readiness/admission claimed')
if __name__=='__main__':main()
