"""Rebind X1 physical interfaces and electrical allocations to Stage8 source geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import stage7_interfaces as interfaces
import stage7_electrical as electrical
import stage7_demonstrator as conservation

ROOT=interfaces.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage8'
PRIOR=OUT.parent/'stage7'

def bound(paths):
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def validate_bindings(report,root=ROOT):
    conservation.need(bool(report.get('source_sha256')),'missing source bindings')
    for name,digest in report['source_sha256'].items():
        conservation.need(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'stale source dependency '+name)

def validate_interface_object(interface,report):
    conservation.need(hashlib.sha256(encode(interface).encode()).hexdigest()==report['interface_object_sha256'],'electrical report bound to different interface object')

def build():
    mechanical_path=OUT/'mechanical-report.json'
    spec_path=OUT/'interface-input.json'
    if not spec_path.exists():spec_path=PRIOR/'interface-input.json'
    mechanical=json.loads(mechanical_path.read_text())
    validate_bindings(mechanical)
    spec=json.loads(spec_path.read_text())
    result=interfaces.build_from(spec,mechanical)
    conservation.verify_transport(result)
    ledger=json.loads((ROOT/'design/architecture-278/source-ledger.json').read_text())
    locked=json.loads((ROOT/'design/grid/placements.lock.json').read_text())
    old=json.loads((OUT.parent/'stage6/hosting-report.json').read_text())
    counts,overlay=conservation.verify_source(result['source_packages'],ledger,locked,old['whole_instrument_host_overlay'])
    result['whole_instrument_host_overlay']={ref:host.replace('stage7-','stage8-') for ref,host in overlay.items()}
    result['conservation_counts']=counts
    previous=json.loads((PRIOR/'interfaces-report.json').read_text())
    dependencies=[ROOT/p for p in previous['source_sha256'] if p not in {str(PRIOR.relative_to(ROOT))+'/mechanical-report.json',str(PRIOR.relative_to(ROOT))+'/interface-input.json'}]
    dependencies += [spec_path,mechanical_path,Path(__file__),Path(__file__).with_name('test_stage8_rebudget.py'),Path(conservation.__file__),OUT/'scope.json']
    result['source_sha256']=bound(dependencies)
    baseline=json.loads((OUT.parent/'stage6/candidate-report.json').read_text())
    report=electrical.analyze(result,baseline)
    locality_path=OUT/'locality-report.json'
    locality=json.loads(locality_path.read_text());validate_bindings(locality)
    critical=[]
    for row in locality['corridors']:
        critical.append({'net':row['net'],'endpoints':row['endpoints'],'status':row['status'],
                         'source_copper_centreline_mm':row.get('copper_centreline_mm'),
                         'source_via_barrel_mm':row.get('via_barrel_mm'),
                         'endpoint_THT_barrel_mm':row.get('endpoint_THT_barrel_mm'),
                         'developed_copper_and_barrel_mm':row.get('developed_copper_and_barrel_mm'),
                         'scope':'Obstacle-aware source corridor; not native routed copper or parasitic/return qualification.'})
    report['critical_source_corridor_lengths']=critical
    for row in report['local_feedback_branch_comparison']:
        endpoints={(row[k]['ref'],row[k]['pin']) for k in ('from','to')}
        matches=[c for c in critical if {(e['ref'],e['pin']) for e in c['endpoints']}==endpoints]
        if matches:row['stage8_critical_corridor']=matches[0]
    previous_e=json.loads((PRIOR/'electrical-report.json').read_text())
    sources=[ROOT/p for p in previous_e['source_sha256'] if p!=str((PRIOR/'interfaces-report.json').relative_to(ROOT))]
    report['source_sha256']=bound(sources+[Path(__file__),mechanical_path,spec_path,locality_path,OUT/'scope.json'])
    report['interface_object_sha256']=hashlib.sha256(encode(result).encode()).hexdigest()
    report['stage8_boundary']='Recomputed actual-pad allocations. Critical obstacle-aware corridors are separately supplied by locality report; other traces remain unrouted.'
    validate_interface_object(result,report)
    return result,report

def encode(value):return json.dumps(value,separators=(',',':'),sort_keys=True)+'\n'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    for name,result in zip(('interfaces','electrical'),build()):
        target=OUT/(name+'-report.json');data=encode(result)
        if args.check:conservation.need(target.read_text()==data,'stale Stage8 '+name)
        else:target.write_text(data)
    print('Stage8 X1 actual-pad interfaces/rail/return allocations reproduced; hardware qualification OPEN')

if __name__=='__main__':main()
