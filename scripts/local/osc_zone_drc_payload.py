"""Candidate export and bounded DRC for the single selected-zone fill (container payload).

Two modes, one container run each, both inside the existing 420 s payload budget:

candidate: normalize the frozen core (load/save control), fill only the +12V
  In4.Cu zone on a disposable copy, and export both boards with the pinned
  project and rules plus a manifest to the writable /output mount.
drc: verify the candidate manifest, run kicad-cli pcb drc (JSON, all
  severities, NO --refill-zones) on the unfilled control and on the
  single-zone-filled copy with per-run caps, and report counts, identities and
  the before/after delta split into items that mention the +12V net or the
  selected zone versus everything else. Never writes /work. No acceptance.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import osc_frozen_fill as fill
import osc_single_zone_payload as zone

PAYLOAD_SECONDS=zone.PAYLOAD_SECONDS
RESERVE=40
NORMALIZE_CAP=60
DRC_CAP=170
REPORT_LIMIT=fill.REPORT_LIMIT
BOARD_FILES=('osc-core.kicad_pcb','osc-core.kicad_pro','osc-core.kicad_dru')
CANDIDATE_STATUS='SINGLE_ZONE_CANDIDATE_EXPORTED_NOT_ACCEPTANCE'
DRC_STATUS='SINGLE_ZONE_DRC_OBSERVATIONS_NOT_ACCEPTANCE'
RELATED_MARKERS=('+12V',zone.TARGET_ZONE)

def require(condition,message):
    if not condition: raise ValueError(message)

def bounded(argv,cwd,seconds,log,record):
    deadline=time.monotonic()+seconds
    record.update(argv=argv,status='STARTED',start_monotonic_seconds=time.monotonic(),cap_seconds=seconds)
    proc=None
    try:
        with log.open('xb') as output:
            proc=subprocess.Popen(argv,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            while proc.poll() is None:
                if time.monotonic()>=deadline: raise TimeoutError('cap exhausted')
                if log.stat().st_size>fill.LOG_LIMIT: raise ValueError('log bound')
                time.sleep(.1)
        if proc.returncode!=0: raise ValueError('command exit '+str(proc.returncode))
        record['status']='COMPLETE'
    except BaseException as exc:
        record['status']='FAILED';record['error']=type(exc).__name__+': '+str(exc)[:300]
        if proc is not None and proc.poll() is None:
            import os,signal
            os.killpg(proc.pid,signal.SIGKILL)
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: record['reap_timeout']=True
        raise
    finally:
        record['end_monotonic_seconds']=time.monotonic();record['elapsed_seconds']=record['end_monotonic_seconds']-record['start_monotonic_seconds']
        record['exit_code']=proc.returncode if proc is not None else None
        if log.is_file():
            record['log_sha256']=fill.sha(log)
            with log.open('rb') as s: s.seek(max(0,log.stat().st_size-1024));record['log_tail']=s.read(1024).decode('utf-8',errors='replace')

def export_dir(src,dst,names=BOARD_FILES):
    dst.mkdir(parents=True,exist_ok=False);hashes={}
    for name in names:
        shutil.copyfile(src/name,dst/name);hashes[name]=fill.sha(dst/name)
    return hashes

def candidate(root,scratch,output,result):
    start=time.monotonic();deadline=start+PAYLOAD_SECONDS-RESERVE
    require(output.is_dir() and not any(output.iterdir()),'empty writable /output required')
    fill.record_memory(result,'preflight','before')
    result['input_before']=fill.verify_inputs(root)
    result['nonfill_input']=fill.semantic_hash(root/'osc-core.kicad_pcb')
    scratch.mkdir(exist_ok=False)
    for kind in ('input','before','after'):
        (scratch/kind).mkdir()
    for name in fill.PINS: shutil.copyfile(root/name,scratch/'input'/name)
    fill.record_memory(result,'preflight','after')
    fill.record_memory(result,'zone','before')
    result['normalize']={}
    bounded([sys.executable,'-B',str(Path(fill.__file__).resolve()),'--worker','normalize',str(scratch)],scratch,min(NORMALIZE_CAP,deadline-time.monotonic()),scratch/'normalize.log',result['normalize'])
    fill.capture_substages(result,scratch,'normalize',require_complete=True)
    result['command']={}
    zone.run_worker(scratch,deadline,result['command'])
    zone.capture_stages(result,scratch,require_complete=True)
    worker=json.loads((scratch/'zone.json').read_text())
    # The full worker receipt (cluster listings) is exported as zone.json; the payload receipt keeps a compact summary.
    result['worker_summary']={'fill':worker.get('fill'),'counts':worker.get('counts'),'selected_after':(worker.get('after') or {}).get('selected'),
        'connected':{phase:{k:v.get('connected') for k,v in (worker.get(phase) or {}).get('pairs',{}).items() if k!='ratsnest'} for phase in ('before','after','reloaded')},'failure':worker.get('failure')}
    require(result['worker_summary']['failure'] is None and result['worker_summary']['fill'].get('returned') is True,'worker fill')
    fill.record_memory(result,'zone','after')
    fill.record_memory(result,'verify','before')
    for kind in ('before','after'):
        for name in BOARD_FILES[1:]: shutil.copyfile(root/name,scratch/kind/name)
    result['nonfill_before']=fill.semantic_hash(scratch/'before'/'osc-core.kicad_pcb')
    result['nonfill_after']=fill.semantic_hash(scratch/'after'/'osc-core.kicad_pcb')
    require(result['nonfill_input']==result['nonfill_before']==result['nonfill_after'],'non-fill semantic change')
    result['before_owners']=zone.zone_fill_owners(scratch/'before'/'osc-core.kicad_pcb')
    result['after_owners']=zone.zone_fill_owners(scratch/'after'/'osc-core.kicad_pcb')
    require(result['before_owners']=={'zones':zone.COUNTS['zone'],'filled_polygon_by_zone':{}},'control must stay unfilled')
    require(result['after_owners']['zones']==zone.COUNTS['zone'] and set(result['after_owners']['filled_polygon_by_zone'])=={zone.TARGET_ZONE},'filled_polygon outside selected zone')
    result['exported']={kind:export_dir(scratch/kind,output/kind) for kind in ('before','after')}
    for name in ('normalize.json','zone.json','normalize-substages.jsonl','zone-substages.jsonl'): shutil.copyfile(scratch/name,output/name)
    result['exported_receipts']={name:fill.sha(output/name) for name in ('normalize.json','zone.json','normalize-substages.jsonl','zone-substages.jsonl')}
    result['input_after']=fill.verify_inputs(root)
    fill.record_memory(result,'verify','after')
    manifest={'status':CANDIDATE_STATUS,'target_zone':zone.TARGET_ZONE,'input':result['input_before'],'exported':result['exported'],
              'nonfill_sha256':{'input':result['nonfill_input'],'before':result['nonfill_before'],'after':result['nonfill_after']},
              'before_owners':result['before_owners'],'after_owners':result['after_owners'],'fill_seconds':result['worker_summary']['fill']['seconds'],
              'exported_receipts':result['exported_receipts'],'board_acceptance':False}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    result['manifest_sha256']=fill.sha(output/'manifest.json')
    require(time.monotonic()<=start+PAYLOAD_SECONDS,'payload deadline')
    result['status']=CANDIDATE_STATUS

def classify(identities):
    related={};other={}
    for key,count in identities.items():
        (related if any(marker in key for marker in RELATED_MARKERS) else other)[key]=count
    return related,other

def summarize_identities(identities,sample=48):
    rows=sorted(identities.items())
    return {'count':sum(identities.values()),'distinct':len(rows),'identity_sha256':fill.digest(rows),'sample':rows[:sample],'sample_complete':len(rows)<=sample}

def drc(candidate_dir,scratch,output,result):
    start=time.monotonic();deadline=start+PAYLOAD_SECONDS-RESERVE
    require(output.is_dir() and not any(output.iterdir()),'empty writable /output required')
    fill.record_memory(result,'preflight','before')
    manifest=json.loads((candidate_dir/'manifest.json').read_text())
    require(manifest.get('status')==CANDIDATE_STATUS and manifest.get('target_zone')==zone.TARGET_ZONE,'candidate manifest')
    result['candidate_manifest_sha256']=fill.sha(candidate_dir/'manifest.json')
    scratch.mkdir(exist_ok=False);result['candidate']={}
    for kind in ('before','after'):
        (scratch/kind).mkdir();hashes={}
        for name in BOARD_FILES:
            src=candidate_dir/kind/name;require(src.is_file() and not src.is_symlink(),'candidate file '+name)
            hashes[name]=fill.sha(src);require(hashes[name]==manifest['exported'][kind][name],'candidate hash '+kind+'/'+name)
            shutil.copyfile(src,scratch/kind/name)
        require(hashes['osc-core.kicad_pro']==fill.PINS['osc-core.kicad_pro'] and hashes['osc-core.kicad_dru']==fill.PINS['osc-core.kicad_dru'],'pinned project/rules')
        result['candidate'][kind]=hashes
    fill.record_memory(result,'preflight','after')
    reports={};result['commands']={}
    for kind in ('before','after'):
        fill.record_memory(result,'drc-'+kind,'before')
        report=scratch/('drc-'+kind+'.json');record={};result['commands'][kind]=record
        argv=['kicad-cli','pcb','drc','--format','json','--severity-all','--output',str(report),str(scratch/kind/'osc-core.kicad_pcb')]
        bounded(argv,scratch,min(DRC_CAP,deadline-time.monotonic()),scratch/('drc-'+kind+'.log'),record)
        require(report.is_file() and 0<report.stat().st_size<=REPORT_LIMIT,'report bound')
        counts,identities=fill.drc_summary(report);reports[kind]=identities
        shutil.copyfile(report,output/('drc-'+kind+'.json'))
        result['drc_'+kind]={'report_sha256':fill.sha(output/('drc-'+kind+'.json')),'report_bytes':report.stat().st_size,'counts':counts,'identities':summarize_identities(identities)}
        fill.record_memory(result,'drc-'+kind,'after')
    added=reports['after']-reports['before'];removed=reports['before']-reports['after']
    result['delta']={}
    for name,bag in (('added',added),('removed',removed)):
        related,other=classify(bag)
        result['delta'][name]={'total':summarize_identities(bag),'related_to_plus12v_or_selected_zone':summarize_identities(related),'other':summarize_identities(other)}
    result['delta']['meaning']='Identities keyed by category/type/severity/description/item UUIDs under identical conditions; related means the text mentions +12V or the selected zone UUID. Observations only, not a defect or improvement verdict.'
    manifest_out={'status':DRC_STATUS,'candidate_manifest_sha256':result['candidate_manifest_sha256'],'reports':{k:result['drc_'+k]['report_sha256'] for k in ('before','after')},'board_acceptance':False}
    (output/'drc-manifest.json').write_text(json.dumps(manifest_out,indent=2,sort_keys=True)+'\n')
    require(time.monotonic()<=start+PAYLOAD_SECONDS,'payload deadline')
    result['status']=DRC_STATUS

def main(mode):
    start=time.monotonic()
    root=Path('/work/boards/osc-core');scratch=Path('/scratch/osc-'+mode);output=Path('/output');candidate_dir=Path('/candidate')
    result={'status':'FAILED','mode':mode,'board_acceptance':False,'full_board_fill':False,'target_zone':zone.TARGET_ZONE,'refill_zones_option_used':False,
            'limits':'payload 420 s; candidate: normalize cap 60, zone worker stage caps; drc: 170 s per DRC run; no route edits'}
    try:
        if mode=='candidate': candidate(root,scratch,output,result)
        elif mode=='drc': drc(candidate_dir,scratch,output,result)
        else: raise ValueError('mode')
    except Exception as exc:
        result['failure']={'type':type(exc).__name__,'message':str(exc)[:500]}
        for log in sorted(scratch.glob('*.log')) if scratch.is_dir() else []:
            result.setdefault('log_tails',{})[log.name]=log.read_bytes()[-1024:].decode('utf-8',errors='replace')
        try: fill.record_memory(result,'failed','after')
        except Exception as check: result['telemetry_failure']=type(check).__name__+': '+str(check)[:160]
    result['elapsed_seconds']=time.monotonic()-start
    data=json.dumps(result,sort_keys=True)
    if len(data.encode())>zone.OUTPUT_LIMIT:
        for key in ('drc_before','drc_after'):
            if key in result: result[key]['identities'].pop('sample',None)
        data=json.dumps(result,sort_keys=True)
    if len(data.encode())>zone.OUTPUT_LIMIT:
        data=json.dumps({'status':'FAILED','mode':mode,'board_acceptance':False,'failure':{'type':'ValueError','message':'output bound'},'elapsed_seconds':time.monotonic()-start})
    print(data,flush=True)
    return 0 if result['status'] in (CANDIDATE_STATUS,DRC_STATUS) else 1

if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1] in ('candidate','drc'): sys.exit(main(sys.argv[1]))
    raise SystemExit('usage: osc_zone_drc_payload.py candidate|drc')
