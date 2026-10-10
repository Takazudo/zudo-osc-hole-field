"""Review-gated, shared-budget audit pilot. Never route/adopt/publish."""
import argparse,hashlib,importlib.util,json,os,signal,subprocess,sys,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen import audit_fixture_tasks as a
ORCHESTRATION_FILES=('scripts/pcbgen/audit_fixture_tasks.py','scripts/pcbgen/core_audit_pilot.py','scripts/pcbgen/freeze_core_audit_tasks.py','circuit/routing/issue189/core236-audit-recovery/recover_isolated.py','.github/workflows/core-audit-task-pilot.yml','.github/workflows/routing-benchmark.yml','scripts/pcbgen/core_audit_waves.py','scripts/pcbgen/core_audit_geometry.py','scripts/pcbgen/core_audit_sequence.py')
REPO=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('audit_resource_util',REPO/ORCHESTRATION_FILES[3]);resource=importlib.util.module_from_spec(spec);spec.loader.exec_module(resource)
def revision(repo,commit=None):
 blobs={p:a.SHA(subprocess.check_output(['git','show',commit+':'+p],cwd=repo) if commit else (Path(repo)/p).read_bytes()) for p in ORCHESTRATION_FILES}
 return dict(blobs=blobs,sha256=a.identity(blobs))
def stop_reason(sample,now,deadline):
 if now>=deadline:return 'INCOMPLETE_SHARED_40_MINUTE_BUDGET'
 if sample['available_kib']<2097152 or sample['total_rss_kib']>12582912:return 'INCOMPLETE_MEMORY_GUARD'
def validate_packets(m,leaves,plan,bindings):
 packets=plan['packets'];a.selection(m,leaves,packets)
 if len(packets)!=2 or any(len(p)!=8 for p in packets):raise ValueError('pilot requires two disjoint eight-task packets')
 tasks={t['task_id']:t for t in m['tasks']}
 for packet,start in zip(packets,(15,23)):
  rows=[tasks[k] for k in packet]
  if [(t['zone_uuid'],t['layer'],t['stage'],t['batch_index']) for t in rows]!=[('e389d344-872d-538e-9bfc-39577adb1686','B.Cu',0,i) for i in range(start,start+8)]:raise ValueError('pilot packet scope changed')
  if any(a.identity(t['expected_geometry']) not in bindings for t in rows):raise ValueError('unbound pilot native geometry')
 for k,v in dict(max_workers=2,command_seconds=2400,job_minutes=50,maximum_aggregate_rss_kib=12582912,minimum_available_kib=2097152).items():
  if plan.get(k)!=v:raise ValueError('pilot guard/budget changed')
 return packets

OLD_APPROVAL_SHA='fe548a14a5e6aa810d0a39178a38ed2defa7b09c7eb6307d15c7e635c74044c1'
OLD_PRODUCER='53c3034aea893f4f64848789f3d57302c066919a'
# Only the five complete, independently accepted before-wave artifacts.
# The failed bootstrap is deliberately absent. Original approvals never change.
REVIEWED_WAVE_ORCHESTRATION='2c6bf3e38116aeff707a5b218574ca5e6c9655a90198ac93e827c6fa043b542d'
REVIEWED_WAVES={
 ('f67bef8211b40e43e93a8e16004ac1d77079f12f', 38085831915, 11682309044, 'fdaf3588096971f2100f2911e4c54e0667eb70388e7b513743161f6330ab59a4', '7283f40ef77d149a334642fa4b98c079f52f1f8dcb4ecc05a138d0b96bef9974'),
 ('a56f2041484231066b2248ff873d3863ccb0802a', 38089049943, 11682929243, 'fa3fa35ec67b820fde98489626f337bc4296041a6eed715b4a587f62a822960f', '28718d64dabd5a9ff41b7d7fb8e6a78507a4e0ccf09322e9a48463a5179d2eb1'),
 ('a56f2041484231066b2248ff873d3863ccb0802a', 38090289618, 11684820415, '9fb008673bc220fcac938081232909e5dece071daa0e933d1da3741eeee5a859', 'd61b8654cfc6647d3a39184c285622d543086fcb9aca9ddf0fd537f64d8ba4cb'),
 ('a56f2041484231066b2248ff873d3863ccb0802a', 38092513020, 11685885272, 'f600bd16eff60453c3b65bf5986d484de2fe2224997a706c027b6dea9009c692', '83897aeed9a8514b8f0b4c48984f6566ccb19f87b3f56c16ecc033f3af76ded9'),
 ('a56f2041484231066b2248ff873d3863ccb0802a', 38094496794, 11685642798, '8444360cb096f468cf5f9348a86a3b1f2bdfaa34df25856322214cf4b48c9f93', 'b183e03d688e680d556a2316f89af57120b59897d2b31c6d51c696f4242b8576'),
}
def approved_orchestration(pin,approval_sha,repo):
 if pin['producer_commit']==OLD_PRODUCER:
  if approval_sha!=OLD_APPROVAL_SHA or pin['run']!=38081076014 or pin['artifact_id']!=11681470375 or pin['artifact_sha256']!='448b59dc66125efbb3a3027ccf5fc1752325dc8e46025956a39a53611a3cf7ec' or pin['orchestration']['sha256']!='9233e904a77736ca0eb61a201c2fe88002b1805d29c7dc5597d313b36773be79':return False
  # Only the exact independently reviewed old approval is compatible. Never
  # recompute/rewrite its revision using the new orchestration file list.
  blobs={name:a.SHA(subprocess.check_output(['git','show',OLD_PRODUCER+':'+name],cwd=repo)) for name in pin['orchestration']['blobs']}
  return pin['orchestration']==dict(blobs=blobs,sha256=a.identity(blobs))
 key=(pin['producer_commit'],pin['run'],pin['artifact_id'],pin['artifact_sha256'],approval_sha)
 if key in REVIEWED_WAVES:
  # Rehash all nine ORIGINAL source blobs; exact artifact/approval identities
  # are reviewed exceptions, not producer-wide or kernel-only equivalence.
  original=revision(repo,pin['producer_commit'])
  return original['sha256']==REVIEWED_WAVE_ORCHESTRATION and pin['orchestration']==original
 return pin['orchestration']==revision(repo,pin['producer_commit'])==revision(repo)
def load_approved(m,kernel,source_root,config,repo,resume):
 before=source_root/'before/osc-core.kicad_pcb';after=source_root/'after/osc-core.kicad_pcb'
 anchor=a.reviewed_legacy_anchor(source_root/'compact.zip',json.loads((source_root/'metadata.json').read_bytes()),repo,kernel)
 leaves,bindings=a.import_legacy(source_root/'compact.zip',anchor,m,before,after,kernel)
 if len(leaves)!=235:raise ValueError('legacy coverage changed')
 old=config/'pilot-38081076014/authenticated-artifact-approval.json'
 refs=[dict(approval=json.loads(old.read_bytes()),approval_sha256=OLD_APPROVAL_SHA)]+resume
 paths,raw,texts,ctx=a.sources(before,after);cache=(texts,ctx,[a.artwork_ids(s) for s in texts],{})
 from scripts.pcbgen.core_audit_waves import reconcile_wave
 plan=json.loads((config/'before-wave-plan.json').read_bytes())
 for i,ref in enumerate(refs):
  pin=ref['approval'];path=source_root/('approval-'+str(i)+'.json');a.atomic(path,pin)
  new=authenticate_checkpoints(source_root/('checkpoint-'+str(i)+'.zip'),path,ref['approval_sha256'],m,kernel,repo,source_root/('verified-'+str(i)))
  if set(leaves)&set(new):raise ValueError('duplicate prior task')
  for key,b in new.items():
   t=next(t for t in m['tasks'] if t['task_id']==key);a.verify_leaf(m,t,b,before,after,kernel,bindings[a.identity(t['expected_geometry'])],b['provenance'],cache)
   if any(v['severity']=='error' for v in json.loads(b['report'])['violations']):raise ValueError('prior native failure')
  producer=json.loads((source_root/('verified-'+str(i))/'producer.json').read_bytes())
  if i==0:
   if len(new)!=16 or producer['status']!='PILOT_TASKS_FINISHED; FULL_426_GATES_NOT_RUN' or producer['cleanup_errors'] or producer['owned_containers_remaining'] or producer['process_tree_after_cleanup']:raise ValueError('reviewed old pilot incomplete')
   leaves.update(new)
  else:leaves=reconcile_wave(m,plan,i-1,leaves,new,producer,before,after,kernel,bindings)
 return leaves,bindings
def authenticate_checkpoints(archive,approval,approval_sha,m,kernel,repo,destination):
 """Caller must pin reviewed approval bytes; native artifacts authenticate via gh.

Exact producer orchestration is compared with this reviewed checkout, separately
from the original native kernel. No leaf JSON can create a VerifiedAuthority.
 """
 if a.SHA(Path(approval).read_bytes())!=approval_sha:raise ValueError('reviewed approval hash mismatch')
 pin=json.loads(Path(approval).read_bytes())
 if pin['manifest_sha256']!=a.identity(m) or pin['policy']!=kernel or not approved_orchestration(pin,approval_sha,repo):raise ValueError('producer/manifest/kernel/orchestration changed')
 artifact,execution=a.authenticate_artifact(pin['artifact_id'],pin['run'],pin['producer_commit'],pin['artifact_sha256'])
 if execution['path']!='.github/workflows/routing-benchmark.yml':raise ValueError('unapproved producer workflow')
 with Path(archive).open('rb') as f:
  if hashlib.file_digest(f,'sha256').hexdigest()!=pin['artifact_sha256']:raise ValueError('native checkpoint artifact digest mismatch')
 destination=Path(destination)
 if destination.exists():raise ValueError('checkpoint extraction must be disjoint/new')
 destination.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:
  names=z.namelist()
  if len(names)!=len(set(names)):raise ValueError('duplicate artifact paths')
  for info in z.infolist():
   p=Path(info.filename)
   if p.is_absolute() or '..' in p.parts or (info.external_attr>>16)&0o170000==0o120000:raise ValueError('unsafe artifact path')
   if info.is_dir():continue
   out=destination/p;out.parent.mkdir(parents=True,exist_ok=True)
   with z.open(info) as src,out.open('wb') as dst:
    import shutil
    shutil.copyfileobj(src,dst,1024*1024)
 producer=json.loads((destination/'producer.json').read_bytes())
 expected={k:pin[k] for k in ('producer_commit','run','manifest_sha256','policy','orchestration')}
 if any(producer.get(k)!=v for k,v in expected.items()) or producer.get('image')!=a.IMAGE or producer.get('inspected_image_id')!=producer.get('expected_image_id') or not producer.get('expected_image_id'):raise ValueError('native producer image/source evidence changed')
 if producer['ledgers']!=pin['ledgers']:raise ValueError('approved ledger inventory changed')
 receipts={};locations={}
 tasks={t['task_id']:t for t in m['tasks']}
 for relative,digest in pin['ledgers'].items():
  p=Path(relative)
  if p.is_absolute() or '..' in p.parts:raise ValueError('unsafe ledger path')
  path=destination/p
  if a.SHA(path.read_bytes())!=digest:raise ValueError('checkpoint ledger digest mismatch')
  ledger=json.loads(path.read_bytes())
  for key,leaf_digest in ledger['tasks'].items():
   if key not in tasks or key in receipts:raise ValueError('wrong/duplicate authenticated task ID')
   b=a.read_checkpoint(path.parent,key,leaf_digest,None);receipts[key]=a.identity(b['receipt']);locations[key]=(path.parent,leaf_digest)
 authority=a.VerifiedAuthority(a._SEAL,m,kernel,receipts,pin)
 return {k:a.read_checkpoint(root,k,digest,authority) for k,(root,digest) in locations.items()}

def authenticate_geometry(archive,approval,approval_sha,m,kernel,repo,destination,bindings):
 leaves=authenticate_checkpoints(archive,approval,approval_sha,m,kernel,repo,destination)
 root=Path(destination);producer=json.loads((root/'producer.json').read_bytes());path=root/'shard-0/geometry-receipt.json'
 if leaves or producer['ledgers'] or list(root.glob('shard-*/*/complete.json')) or list(root.rglob('drc.json')):raise ValueError('bootstrap cannot create completed DRC tasks')
 if producer.get('mode')!='geometry-bootstrap' or producer['status']!='GEOMETRY_BOOTSTRAP_FINISHED; NO_DRC_TASKS' or producer['cleanup_errors'] or producer['owned_containers_remaining'] or producer['process_tree_after_cleanup'] or producer['requested_task_ids']:raise ValueError('bootstrap failure/guard/cleanup/task scope')
 if a.SHA(path.read_bytes())!=producer.get('geometry_receipt_sha256'):raise ValueError('bootstrap native receipt hash changed')
 from scripts.pcbgen.core_audit_geometry import validate_receipt
 result=validate_receipt(m,kernel,bindings,json.loads(path.read_bytes()))
 return dict(result,source_sha256=m['source_sha256'],context_sha256=m['context_sha256'],image=a.IMAGE,validator_revision=kernel['validator_revision'],manifest_sha256=a.identity(m),artifact_approval_sha256=approval_sha,producer=json.loads(Path(approval).read_bytes()),native_receipt_sha256=a.SHA(path.read_bytes()),stage_review_required=True)
def controller(repo,source_root,config,output,reviewed_commit,deadline,mode="pilot",wave=0,resume=None):
 """Deadline is shared and includes preflight, startup and both workers."""
 repo=Path(repo).resolve();source_root=Path(source_root).resolve();config=Path(config).resolve();output=Path(output).resolve()
 if output.exists():raise ValueError('pilot output must be new/disjoint')
 output.mkdir(parents=True);containers=[];processes=[];logs=[];status='INCOMPLETE_PREFLIGHT';image_id=None;image_ids=[];native_pids=set()
 producer=dict(adopted=False,producer_commit=reviewed_commit,run=int(os.environ['GITHUB_RUN_ID']),orchestration=revision(repo),ledgers={})
 try:
  head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
  dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=repo,text=True)
  if head!=reviewed_commit or dirty:raise ValueError('reviewed clean producer commit required')
  if revision(repo)!=json.loads((config/'orchestration-revision.json').read_bytes()):raise ValueError('reviewed taskrunner/controller/aggregation revision changed')
  m=json.loads((config/'manifest.json').read_bytes());kernel=a.policy(repo);a.validate_manifest(m,source_root/'before/osc-core.kicad_pcb',source_root/'after/osc-core.kicad_pcb',kernel)
  leaves,bindings=load_approved(m,kernel,source_root,config,repo,resume or [])
  if len(m['tasks'])!=426:raise ValueError('reviewed full scope changed')
  if bindings!=json.loads((config/'native-geometry-bindings.json').read_bytes()):raise ValueError('reviewed geometry binding changed')
  if mode=='before-wave':
   if len(resume or [])!=wave:raise ValueError('exact preceding wave approval count required')
   from scripts.pcbgen.core_audit_waves import select_wave
   packets=select_wave(m,leaves,json.loads((config/'before-wave-plan.json').read_bytes()),wave,bindings)
  elif mode=='geometry-bootstrap':packets=[[]]
  elif mode=='pilot':packets=validate_packets(m,leaves,json.loads((config/'pilot-plan.json').read_bytes()),bindings)
  else:raise ValueError('unsupported audit mode')
  if mode in ('before-wave','geometry-bootstrap'):
   prior_runs=a.github_json('actions/workflows/378789207/runs?branch='+os.environ['GITHUB_REF_NAME']+'&event=workflow_dispatch&per_page=100')['workflow_runs']
   admitted={int(os.environ['GITHUB_RUN_ID'])}|{ref['approval']['run'] for ref in (resume or [])}
   if any(r['head_sha']==reviewed_commit and r['id'] not in admitted for r in prior_runs):raise ValueError('unreconciled exact-source admission; never replay')
  producer.update(mode=mode,wave=wave,prior_task_ids=sorted(leaves),requested_task_ids=sorted(k for packet in packets for k in packet))
  producer.update(manifest_sha256=a.identity(m),policy=kernel,image=a.IMAGE)
  for i,p in enumerate(packets):a.atomic(output/('packet-'+str(i)+'.json'),p)
  if stop_reason(dict(available_kib=resource.available(),total_rss_kib=0),time.monotonic(),deadline):raise ValueError('preflight exhausted shared guard/budget')
  subprocess.run(['docker','pull',a.IMAGE],check=True,timeout=max(1,deadline-time.monotonic()))
  image_id=subprocess.check_output(['docker','image','inspect',a.IMAGE,'--format','{{.Id}}'],text=True).strip();producer['expected_image_id']=image_id
  for i in range(len(packets)):
   if stop_reason(dict(available_kib=resource.available(),total_rss_kib=0),time.monotonic(),deadline):raise ValueError('startup exhausted shared guard/budget')
   name='core189-'+os.environ['GITHUB_RUN_ID']+'-'+str(i)
   cmd=['docker','create','--name',name,'--network','none','--memory','6g','--memory-swap','6g','--user',str(os.getuid())+':'+str(os.getgid()),'-v',str(repo)+':/repo:ro','-v',str(source_root)+':/inputs:ro','-v',str(config)+':/plan:ro','-v',str(output)+':/output:rw','-w','/repo',a.IMAGE,'python3','scripts/pcbgen/core_audit_pilot.py','worker','--packet','/output/packet-'+str(i)+'.json','--output','/output/shard-'+str(i),'--mode',mode]
   cid=subprocess.check_output(cmd,text=True,timeout=10).strip();containers.append(cid)
   item=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=5))[0]
   if item['Config']['Image']!=a.IMAGE or item['Image']!=image_id:raise ValueError('actual container image mismatch')
   image_ids.append(item['Image']);log=(output/('shard-'+str(i)+'.log')).open('w');logs.append(log);processes.append(subprocess.Popen(['docker','start','-a',cid],stdout=log,stderr=subprocess.STDOUT,start_new_session=True))
  producer['inspected_image_id']=image_ids[0];status='INCOMPLETE_RUNNING'
  while True:
   roots=[os.getpid(),*[p.pid for p in processes]]
   for cid in containers:
    item=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=5))[0]
    if item['State']['Pid']:roots.append(item['State']['Pid']);native_pids.add(item['State']['Pid'])
   tree=resource.process_tree(roots);sample=dict(epoch=time.time(),tree_rss_kib=tree,total_rss_kib=sum(tree.values()),available_kib=resource.available())
   with (output/'telemetry.jsonl').open('a') as f:f.write(json.dumps(sample)+'\n')
   reason=stop_reason(sample,time.monotonic(),deadline)
   if reason:status=reason;break
   if all(p.poll() is not None for p in processes):status=('GEOMETRY_BOOTSTRAP_FINISHED; NO_DRC_TASKS' if mode=='geometry-bootstrap' else 'PILOT_TASKS_FINISHED; FULL_426_GATES_NOT_RUN') if all(p.returncode==0 for p in processes) else 'INCOMPLETE_WORKER_FAILURE';break
   time.sleep(2)
 except BaseException as error:
  producer.update(error_type=type(error).__name__,error=str(error));status='INCOMPLETE_INTERRUPTED' if isinstance(error,KeyboardInterrupt) else 'INCOMPLETE_CONTROLLER_FAILURE'
  raise
 finally:
  # Cleanup faults must not prevent sealing partial completed checkpoints.
  faults=[];remaining=[]
  for cid in containers:
   try:subprocess.run(['docker','kill',cid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
   except Exception as error:faults.append(str(error))
  for p in processes:
   try:resource.clean(p,[])
   except Exception as error:faults.append(str(error))
  for cid in containers:
   try:
    item=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=5))[0]
    if item['State']['Running'] or item['State']['Pid']:remaining.append(cid)
    subprocess.run(['docker','rm',cid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
   except Exception as error:remaining.append(cid);faults.append(str(error))
  for log in logs:log.close()
  producer.update(status=status,cleanup_errors=faults,owned_containers_remaining=remaining,process_tree_after_cleanup=resource.process_tree([*[p.pid for p in processes],*native_pids]))
  if faults or remaining or producer['process_tree_after_cleanup']:producer['status']='FAILED_OWNED_CLEANUP'
  geometry=output/'shard-0/geometry-receipt.json'
  if geometry.exists():producer['geometry_receipt_sha256']=a.SHA(geometry.read_bytes())
  for p in output.glob('shard-*/ledger.json'):producer['ledgers'][str(p.relative_to(output))]=a.SHA(p.read_bytes())
  a.atomic(output/'producer.json',producer)
 if not producer['status'].startswith(('PILOT_TASKS_FINISHED','GEOMETRY_BOOTSTRAP_FINISHED')):raise SystemExit(2)

def worker(packet,output,mode="pilot"):
 m=json.loads(Path('/plan/manifest.json').read_bytes());kernel=a.policy('/repo');bindings=json.loads(Path('/plan/native-geometry-bindings.json').read_bytes())
 if mode=='geometry-bootstrap':
  from scripts.pcbgen.core_audit_geometry import bootstrap
  return bootstrap(m,'/inputs/before/osc-core.kicad_pcb','/inputs/after/osc-core.kicad_pcb',bindings,output,kernel)
 a.run_missing(m,'/inputs/before/osc-core.kicad_pcb','/inputs/after/osc-core.kicad_pcb',json.loads(Path(packet).read_bytes()),output,kernel,bindings)
def prepare(output,resume=None):
 import io
 root=Path(output);root.mkdir(parents=True,exist_ok=False)
 def download(artifact,digest,name):
  metadata=a.github_json('actions/artifacts/'+str(artifact));run=metadata['workflow_run']['id'];commit=metadata['workflow_run']['head_sha'];a.authenticate_artifact(artifact,run,commit,digest)
  path=root/name
  with path.open('wb') as f:subprocess.run(['gh','api','repos/Takazudo/zudo-osc-hole-field/actions/artifacts/'+str(artifact)+'/zip'],stdout=f,check=True)
  with path.open('rb') as f:
   if hashlib.file_digest(f,'sha256').hexdigest()!=digest:raise ValueError('downloaded artifact bytes differ')
  return path,metadata
 compact,diag=download(11679136451,'b2f5f4d7356eed1b0954e64a6eb7bef7b6195f7ff5a2d1535633eeae42ba2342','compact.zip')
 native=a.github_json('actions/artifacts/11679236513')
 a.atomic(root/'metadata.json',dict(run=38069793801,tested_sha='63f9541aa68ae3e05ee9700ae71dcaea6dfe02f6',diagnostics=diag,native=native))
 old=json.loads((REPO/'circuit/routing/issue189/core236-task-checkpoints/pilot-38081076014/authenticated-artifact-approval.json').read_bytes())
 for i,ref in enumerate([dict(approval=old,approval_sha256=OLD_APPROVAL_SHA)]+(resume or [])):
  pin=ref['approval']
  if a.SHA(a.canonical(pin)+b'\n')!=ref['approval_sha256']:raise ValueError('resume approval bytes changed')
  download(pin['artifact_id'],pin['artifact_sha256'],'checkpoint-'+str(i)+'.zip')
 source,_=download(11671779973,'c5971fa98d5235861294e015150242572cb71dd5fc94a862c0587f8f979d881e','source.zip')
 wanted={('osc-core-grid-shards-'+stage+'/osc-core'+suffix):(label,suffix) for label,stage in [('before','start'),('after','fresh')] for suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru')};found={}
 def visit(z,depth=0):
  if depth>3:raise ValueError('unexpected nested source ZIP')
  for name in z.namelist():
   for suffix,key in wanted.items():
    if name.endswith(suffix):
     if key in found:raise ValueError('ambiguous source fixture')
     found[key]=z.read(name)
   if name.endswith('.zip'):
    with zipfile.ZipFile(io.BytesIO(z.read(name))) as nested:visit(nested,depth+1)
 with zipfile.ZipFile(source) as z:visit(z)
 if set(found)!=set(wanted.values()):raise ValueError('immutable source artifact missing board/context')
 for (label,suffix),data in found.items():
  folder=root/label;folder.mkdir(exist_ok=True);(folder/('osc-core'+suffix)).write_bytes(data)
 a.validate_manifest(json.loads((REPO/'circuit/routing/issue189/core236-task-checkpoints/manifest.json').read_bytes()),root/'before/osc-core.kicad_pcb',root/'after/osc-core.kicad_pcb',a.policy(REPO))
def main():
 started=time.monotonic();parser=argparse.ArgumentParser();sub=parser.add_subparsers(dest='command',required=True)
 w=sub.add_parser('worker');w.add_argument('--packet',required=True);w.add_argument('--output',required=True);w.add_argument('--mode',default='pilot')
 verify=sub.add_parser('verify-checkpoints');verify.add_argument('--artifact',required=True);verify.add_argument('--approval',required=True);verify.add_argument('--approval-sha',required=True);verify.add_argument('--config',required=True);verify.add_argument('--source-root',required=True);verify.add_argument('--destination',required=True)
 prep=sub.add_parser('prepare');prep.add_argument('--output',required=True);prep.add_argument('--resume-json',default='[]')
 c=sub.add_parser('controller');c.add_argument('--source-root',required=True);c.add_argument('--config',required=True);c.add_argument('--output',required=True);c.add_argument('--reviewed-commit',required=True);c.add_argument('--mode',default='pilot');c.add_argument('--wave',type=int,default=0);c.add_argument('--resume-json',default='[]')
 args=parser.parse_args()
 if args.command=='worker':
  if not Path('/.dockerenv').exists():raise ValueError('worker requires reviewed host-owned container')
  worker(args.packet,args.output,args.mode)
 elif args.command=='prepare':prepare(args.output,json.loads(args.resume_json))
 elif args.command=='verify-checkpoints':
  config=Path(args.config);m=json.loads((config/'manifest.json').read_bytes());kernel=a.policy(REPO);root=Path(args.source_root);before=root/'before/osc-core.kicad_pcb';after=root/'after/osc-core.kicad_pcb';tasks=a.validate_manifest(m,before,after,kernel)
  leaves=authenticate_checkpoints(args.artifact,args.approval,args.approval_sha,m,kernel,REPO,args.destination);bindings=json.loads((config/'native-geometry-bindings.json').read_bytes());paths,raw,texts,ctx=a.sources(before,after);cache=(texts,ctx,[a.artwork_ids(t) for t in texts],{})
  for key,b in leaves.items():
   t=tasks[key];a.verify_leaf(m,t,b,before,after,kernel,bindings[a.identity(t['expected_geometry'])],b['provenance'],cache)
  print(json.dumps(dict(verified_task_ids=sorted(leaves),adopted=False,full_gates_run=False)))
 else:controller(REPO,args.source_root,args.config,args.output,args.reviewed_commit,started+2400,args.mode,args.wave,json.loads(args.resume_json))
if __name__=='__main__':main()
