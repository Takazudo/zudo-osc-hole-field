"""Bounded comparison evidence assembly, not architecture/hardware acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import stage9_process as process
ROOT=process.ROOT;OUT=process.OUT
need=process.check

def validate_bindings(report):
    need(bool(report.get('source_sha256')),'missing source bindings')
    for path,digest in report['source_sha256'].items():
        need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'stale binding '+path)

def preserve(scope,baseline,alternative):
    for path,digest in scope['preserved_stage8_sha256'].items():
        need(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'Stage8 changed '+path)
    need(len(baseline)==len(alternative)==56 and set(baseline)==set(alternative),'whole package inventory')
    fixed=[]
    for ref,p in baseline.items():
        q=alternative[ref]
        for key in ('pins','units','source','origin_mm','quarter_turn','board'):
            need(q[key]==p[key],'source package changed '+ref+':'+key)
        if p.get('panel_uid'):
            need(q.get('panel_uid')==p['panel_uid'],'fixed panel identity changed '+ref)
            need(q['pads_xyz_mm']==p['pads_xyz_mm'],'fixed terminal plane changed '+ref);fixed.append(ref)
    need(len(fixed)==7,'fixed device count')
    return {'whole_source_packages':56,'fixed_panel_devices':7,'changed_source_circuitry':False,'old_stage8_preserved':True}

def build():
    files={n:OUT/(n+'.json')for n in ('scope','history-evidence','process-report','support-report','electrical-delta-report')}
    reports={k:json.loads(p.read_text())for k,p in files.items()}
    for key in ('history-evidence','process-report','support-report','electrical-delta-report'):validate_bindings(reports[key])
    baseline_path=OUT.parent/'stage8/mechanical-report.json';baseline=json.loads(baseline_path.read_text())
    conservation=preserve(reports['scope'],baseline['placements'],reports['support-report']['placements'])
    need(not reports['process-report']['published_precision_cutout_acceptance'],'unreviewed precision acceptance')
    need(not reports['electrical-delta-report']['hardware_acceptance'],'unreviewed electrical acceptance')
    need(reports['support-report']['physical_acceptance'] is False,'unreviewed mechanical acceptance')
    result={'status':'BOUNDED CONDITIONAL COMPARISON COMPLETE; NO ADOPTION','conservation':conservation,
            'enclosure_authority':reports['history-evidence']['conclusions'],
            'recommendation':'Develop the elevated continuous-board arrangement conditionally; avoid assuming precision cutouts are accepted. Use integrated support and explicitly bounded service access, not a separate loose fixture.',
            'smallest_next_evidence':['exact panel/bushing/clamp stack engagement and fixed-hardware load reaction for proposed integrated supports','factory terminal/strain-relief construction and documented access geometry for the proposed service subassemblies'],
            'owner_choice_boundary':'No conflicting accepted numeric enclosure requirement found in bounded history. Proposed service granularity must be reconsidered if owner requires independent front-PCB replacement without fixed-hardware removal. No such requirement inferred.',
            'later_K_study':reports['scope']['later_K_study'],'stage8_electrical_unknowns_preserved':True,'architecture_adopted':False,'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
    paths=[*files.values(),baseline_path,Path(__file__),Path(__file__).with_name('test_stage9_comparison.py')]
    result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
    return result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();body=json.dumps(build(),indent=2,sort_keys=True)+'\n';p=OUT/'comparison-report.json'
    if args.check:need(p.read_text()==body,'stale Stage9 comparison')
    else:p.write_text(body)
    print('Stage9 comparison reproduced; Stage8/circuit inventory preserved; conditional arrangement only')
if __name__=='__main__':main()
