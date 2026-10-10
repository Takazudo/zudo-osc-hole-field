"""One hash-bound guarded fresh-process audit continuation; never publish."""
import hashlib,json,os,re,signal,subprocess,sys,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.zone_batch_resume import completed_prefix,verified_report
from scripts.pcbgen.audit_zone_silk_scope import artwork_batches
ROOT=Path('.circuit-cache/core236-isolated-recovery')
BEFORE='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'
AFTER='f27efe521f4ed4f6c0ceb53f45f58a82a824c05475ef012a2034a0d1d2a154d1'
ARCHIVES={'original.zip':'d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5','original-inspection.zip':'c5971fa98d5235861294e015150242572cb71dd5fc94a862c0587f8f979d881e','recovery.zip':'2cd2463554fdd63a672bf3b59dae5e3473a960017f51c142f9fc0fd7e4ebeaf4','recovery-inspection.zip':'c6ae91f2848f6a164983847e8ba78c0729238968cd905caa759eda25efc28e7e'}
def sha(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def manifest_from(archive,suffix):
 with zipfile.ZipFile(archive) as z:
  names=[n for n in z.namelist() if n.endswith(suffix)];assert len(names)==1
  return z.read(names[0])
def extract_verified(archive,destination,manifest):
 inventory={r['path']:r for r in manifest['inventory']};assert len(inventory)==len(manifest['inventory'])
 assert sha(archive)==manifest['archive_sha256'] and archive.stat().st_size==manifest['archive_bytes']
 with zipfile.ZipFile(archive) as z:
  names=[n for n in z.namelist() if not n.endswith('/')];assert len(names)==len(set(names)) and set(names)==set(inventory)
  for item in z.infolist():
   if item.is_dir():continue
   p=Path(item.filename);assert not p.is_absolute() and '..' not in p.parts and (item.external_attr>>16)&0o170000!=0o120000
   data=z.read(item);r=inventory[item.filename];assert len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
   out=destination/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(data)
def verify_prefix(resume,before,after):
 result=json.loads((resume/'result.json').read_text());assert result['version']=='10.0.6' and result['before_sha256']==sha(before)==BEFORE and result['after_sha256']==sha(after)==AFTER
 counts={};proof=[]
 for path in sorted(resume.glob('zone-*-scope.json')):
  scope=json.loads(path.read_text());uid=scope['zone_uuid'];batches=artwork_batches(scope['selected_item_uuids'],16);rows=completed_prefix(resume,uid,scope,batches);counts[uid]=len(rows)
  for (stage,index),row in rows.items():
   label=f'{stage}-batch-{index:04d}';fixture=resume/f'zone-{uid}'/label/'osc-core.kicad_pcb'
   data=verified_report(resume,uid,label,fixture,row,row['native_geometry_sha256'])
   for suffix in ('.kicad_pro','.kicad_dru'):
    if not fixture.with_suffix(suffix).read_bytes()==before.with_suffix(suffix).read_bytes()==after.with_suffix(suffix).read_bytes():raise ValueError('saved native context differs from immutable sources')
   proof.append(dict(zone_uuid=uid,stage=stage,batch_index=index,fixture_sha256=sha(fixture),report_sha256=hashlib.sha256(data).hexdigest(),native_geometry_sha256=row['native_geometry_sha256']))
 assert counts=={'601e02b2-8ccb-5c28-83e5-03789d47fbbd':220,'e389d344-872d-538e-9bfc-39577adb1686':1},counts
 return dict(status='221 SAVED REPORT HASHES/SCOPES VERIFIED; FRESH NATIVE RECONSTRUCTION STILL REQUIRED',before_sha256=BEFORE,after_sha256=AFTER,resume_artifact=11673646039,counts=counts,reports=proof)
def prepare():
 inputs=Path('.circuit-cache/core236-isolated-input');ROOT.mkdir(parents=True,exist_ok=False)
 for name,digest in ARCHIVES.items():assert sha(inputs/name)==digest
 original_manifest=manifest_from(inputs/'original-inspection.zip','archive-inventory.json');(ROOT/'original-inventory.json').write_bytes(original_manifest)
 from importlib.util import spec_from_file_location,module_from_spec
 spec=spec_from_file_location('saved_recovery',Path(__file__).with_name('recover_audit.py'));module=module_from_spec(spec);spec.loader.exec_module(module)
 module.extract(inputs/'original.zip',ROOT/'original',ROOT/'original-inventory.json')
 failure_manifest=json.loads(manifest_from(inputs/'recovery-inspection.zip','failure-inventory.json'));(ROOT/'resume-inventory.json').write_text(json.dumps(failure_manifest,indent=2)+'\n')
 extract_verified(inputs/'recovery.zip',ROOT/'resume',failure_manifest)
 original=ROOT/'original/.circuit-cache';before=original/'osc-core-grid-shards-start/osc-core.kicad_pcb';after=original/'osc-core-grid-shards-fresh/osc-core.kicad_pcb'
 proof=verify_prefix(ROOT/'resume/core236-zone-recovery',before,after);proof['archives']=ARCHIVES;(ROOT/'verified-inputs.json').write_text(json.dumps(proof,indent=2)+'\n')
def owned_containers():
 result=[]
 for cid in subprocess.check_output(['docker','ps','-q'],text=True,timeout=5).split():
  check=subprocess.run(['docker','inspect',cid],capture_output=True,text=True,timeout=5)
  if check.returncode:
   if 'No such object' in check.stderr or 'No such container' in check.stderr:continue
   raise subprocess.CalledProcessError(check.returncode,check.args,check.stdout,check.stderr)
  item=json.loads(check.stdout)[0];cmd=item['Config'].get('Cmd',[])
  if 'scripts/pcbgen/audit_zone_silk_scope.py' in cmd and str(ROOT/'zones') in cmd and item['State']['Pid']>0:result.append((cid,item['State']['Pid']))
 return result
def process_tree(roots):
 rows={}
 for p in Path('/proc').glob('[0-9]*/status'):
  try:
   s=p.read_text();rows[int(p.parent.name)]=(int(re.search(r'PPid:\s+(\d+)',s)[1]),int(re.search(r'VmRSS:\s+(\d+)',s)[1]) if 'VmRSS:' in s else 0)
  except (OSError,TypeError):continue
 ids=set(roots)
 while True:
  more={pid for pid,(parent,rss) in rows.items() if parent in ids}
  if more<=ids:break
  ids|=more
 return {pid:rows[pid][1] for pid in ids if pid in rows}
def available():return int(re.search(r'MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text())[1])
def stop_reason(sample,now,deadline):
 if now>=deadline:return 'INCONCLUSIVE_100_MINUTE_BUDGET'
 if sample['available_kib']<2*1024*1024 or sample['total_rss_kib']>12*1024*1024:return 'INCONCLUSIVE_EARLY_MEMORY_STOP'
 return None
def clean(proc,owned):
 for cid,pid in owned:
  try:subprocess.run(['docker','kill',cid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
  except (OSError,subprocess.TimeoutExpired):pass
 if proc.poll() is None:
  try:os.killpg(proc.pid,signal.SIGTERM)
  except ProcessLookupError:pass
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:
   try:os.killpg(proc.pid,signal.SIGKILL)
   except ProcessLookupError:pass
   proc.wait(timeout=5)
def controller():
 proof=json.loads((ROOT/'verified-inputs.json').read_text());assert sum(proof['counts'].values())==221 and proof['resume_artifact']==11673646039
 original=ROOT/'original/.circuit-cache'
 audit=['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/audit_zone_silk_scope.py',str(original/'osc-core-grid-shards-start/osc-core.kicad_pcb'),str(original/'osc-core-grid-shards-fresh/osc-core.kicad_pcb'),str(ROOT/'zones'),'--classify','--batch-size','16','--resume-from',str(ROOT/'resume/core236-zone-recovery'),'--isolate-fixture-processes']
 gates=[sys.executable,str(Path(__file__).with_name('recover_audit.py')),'combine',str(ROOT/'original'),str(ROOT/'zones'),str(ROOT/'eligibility')]
 out=dict(status='STARTED; NO COMPLETE EVIDENCE',adopted=False,phases=[],budget_seconds=6000,minimum_available_kib=2*1024*1024,maximum_process_tree_rss_kib=12*1024*1024,resume_reports=221)
 deadline=time.monotonic()+6000;reason=None;proc=None
 try:
  for phase,command in [('audit',audit),('original_downstream_gates',gates)]:
   if time.monotonic()>=deadline:reason='INCONCLUSIVE_100_MINUTE_BUDGET';break
   owned={}
   with (ROOT/(phase+'.stdout')).open('w') as stdout,(ROOT/(phase+'.stderr')).open('w') as stderr:
    proc=subprocess.Popen(command,stdout=stdout,stderr=stderr,start_new_session=True)
    try:
     while proc.poll() is None:
      current=owned_containers();owned.update(current);tree=process_tree([proc.pid,*[p for c,p in current]])
      sample=dict(epoch=time.time(),phase=phase,tree_rss_kib=tree,total_rss_kib=sum(tree.values()),available_kib=available())
      with (ROOT/'telemetry.jsonl').open('a') as f:f.write(json.dumps(sample)+'\n')
      reason=stop_reason(sample,time.monotonic(),deadline)
      if reason:break
      time.sleep(2)
    finally:
     try:owned.update(owned_containers())
     finally:clean(proc,list(owned.items()))
     remaining=owned_containers();after=dict(epoch=time.time(),phase='after_cleanup',operation=phase,tree_rss_kib=process_tree([proc.pid,*owned.values()]),owned_containers_remaining=remaining,available_kib=available())
     with (ROOT/'telemetry.jsonl').open('a') as f:f.write(json.dumps(after)+'\n')
     if remaining or after['tree_rss_kib']:reason='FAILED_OWNED_DESCENDANT_CLEANUP'
    out['phases'].append(dict(operation=phase,command=command,exit_status=proc.returncode,reason=reason))
    if reason or proc.returncode!=0:out['status']=reason or 'FAILED_'+phase.upper();break
  else:out['status']='ORIGINAL COMPLETE WARNING/PRESERVATION ELIGIBILITY PASS; NO ADOPTION/PUBLICATION'
  if reason:out['status']=reason
 except BaseException as error:
  if isinstance(error,KeyboardInterrupt) and time.monotonic()>=deadline-2:reason='INCONCLUSIVE_100_MINUTE_BUDGET'
  out.update(status=reason or 'INCOMPLETE_INTERRUPTED_OR_CONTROLLER_FAILURE',error_type=type(error).__name__,error=str(error),exit_status=proc.returncode if proc else None);raise
 finally:(ROOT/'controller-result.json').write_text(json.dumps(out,indent=2)+'\n')
 if not out['status'].startswith('ORIGINAL COMPLETE'):raise SystemExit(2)
def seal():
 ROOT.mkdir(parents=True,exist_ok=True)
 inventory=[]
 with zipfile.ZipFile(ROOT/'diagnostics.zip','w',zipfile.ZIP_DEFLATED) as export:
  for p in sorted(ROOT.rglob('*')):
   if not p.is_file() or p.name in ('diagnostics.zip','terminal-inventory.json'):continue
   rel=p.relative_to(ROOT).as_posix();inventory.append(dict(path=rel,bytes=p.stat().st_size,sha256=sha(p)))
   if not rel.startswith(('original/','resume/')) and p.suffix not in ('.kicad_pcb','.kicad_prl','.kicad_pro','.kicad_dru') and p.name!='native-validation-request.json':export.write(p,rel)
 (ROOT/'terminal-inventory.json').write_text(json.dumps(dict(status='RAW OUTPUT FILE INVENTORY; NOT A COMPLETION CLAIM',inventory=inventory,diagnostics_sha256=sha(ROOT/'diagnostics.zip')),indent=2)+'\n')
if __name__=='__main__':
 def interrupt(sig,frame):raise KeyboardInterrupt('external fixed-budget stop')
 signal.signal(signal.SIGINT,interrupt);signal.signal(signal.SIGTERM,interrupt)
 mode=sys.argv[1]
 if mode=='prepare':
  try:prepare()
  except BaseException as error:
   ROOT.mkdir(parents=True,exist_ok=True);(ROOT/'preflight-failure.json').write_text(json.dumps(dict(status='FAILED_PREFLIGHT; NO NATIVE EXECUTION',error_type=type(error).__name__,error=str(error)))+'\n');raise
 elif mode=='controller':controller()
 elif mode=='seal':seal()
 else:raise ValueError('unknown operation')
