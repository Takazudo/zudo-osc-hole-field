"""Guard-admitted exact-input four-phase native campaign; never promotes."""
import argparse,math,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from adapter import mapping,settled,validate_protocol,warning_compare
from policy import check_policy

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical_checkpoint(root):
 """Start bytes: the adopted osc-core checkpoint board, or its receipt-verified metadata-only successor."""
 checkpoint=root/'circuit/routing/osc-pcb-current-checkpoint.json'
 adopted=json.loads(checkpoint.read_text())['boards']['osc-core'];current=sha(root/adopted['board'])
 if current==adopted['board_sha256']:return current,[]
 meta=adopted.get('metadata_successor')
 if not meta or meta.get('successor_board_sha256')!=current:raise ValueError('canonical board is neither the adopted checkpoint nor its recorded metadata successor')
 from scripts.checks.metadata_successor import successor_for
 receipt=successor_for(adopted['board'],current,root,root)
 if receipt is None or receipt['path']!=meta['path'] or receipt['receipt_sha256']!=meta['sha256'] or receipt['adopted']['sha256']!=adopted['board_sha256']:raise ValueError('metadata successor receipt does not bind the adopted checkpoint')
 return current,[root/meta['path'],root/'scripts/checks/metadata_successor.py']
def main():
 ap=argparse.ArgumentParser();ap.add_argument('admission',type=Path);ap.add_argument('--execute',action='store_true');a=ap.parse_args()
 if not a.execute:raise SystemExit('NOT RUN: explicit parent guard admission required')
 root=Path.cwd().resolve();policy=check_policy(root);cfg=json.loads(a.admission.read_text());here=Path(__file__).resolve().parent
 if not (root/'.git').is_file() or subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()!=cfg['commit']:raise ValueError('exact linked worktree required')
 if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('dirty tracked source')
 if os.environ.get('KICAD_CLI_BIN'):raise ValueError('oracle override forbidden')
 before=root/cfg['before'];after=root/cfg['after'];manifest=root/cfg['manifest'];out=(root/cfg['output']).resolve()
 if out.parent!=root/'.circuit-cache' or out.exists():raise ValueError('fresh ignored output required')
 checkpoint=root/'circuit/routing/osc-pcb-current-checkpoint.json'
 current,successor_inputs=canonical_checkpoint(root)
 if sha(before)!=current:raise ValueError('input is not exact current canonical checkpoint board')
 required=[here/'oracle-policy.json',*successor_inputs,*[root/p for p in policy['source_sha256']],checkpoint,root/'design/boards/osc-core.json',root/'schematic/boards/osc-core.net',root/'design/grid/placements.lock.json',before,after,manifest,a.admission.resolve(),*here.glob('*.py'),root/'scripts/kicad/run.sh',root/'scripts/kicad/pin.env']
 for label,path in cfg['sha256'].items():
  if sha(root/label)!=path:raise ValueError('admission source hash drift:'+label)
 if any(str(p.relative_to(root)) not in cfg['sha256'] for p in required if p!=a.admission.resolve()):raise ValueError('admission lacks producer/input binding')
 # Explicit matching entire canonical context trees, including sheets and library tables.
 if type(cfg['start_new_phase_budget_seconds']) not in (int,float) or not math.isfinite(cfg['start_new_phase_budget_seconds']) or cfg['start_new_phase_budget_seconds']<=0:raise ValueError('explicit finite positive phase budget required')
 context=root/cfg['context_directory']
 for p in context.rglob('*'):
  if p.is_file() and p.suffix in ('.kicad_sch','.kicad_pro','.kicad_dru') or p.is_file() and p.name in ('fp-lib-table','sym-lib-table'):
   if str(p.relative_to(root)) not in cfg['sha256']:raise ValueError('context file missing admission hash')
 from scripts.pcbgen.copper_identity import load_board_text
 maps=mapping(load_board_text(before),load_board_text(after),json.loads(manifest.read_text()))
 frozen={root/p:h for p,h in cfg['sha256'].items()};frozen[a.admission.resolve()]=sha(a.admission)
 if shutil.which('docker') is None:raise ValueError('pinned Docker oracle required; no native fallback')
 image=json.loads(subprocess.check_output(['docker','image','inspect',policy['image']],text=True))
 if len(image)!=1 or policy['image'] not in image[0].get('RepoDigests',[]):raise ValueError('local image digest mismatch')
 out.mkdir(parents=True);(out/'oracle-image.json').write_text(json.dumps(image,indent=2)+'\n');calls=[];phases={};reports={};phase_paths={};started=time.monotonic()
 def write(name,value):(out/name).write_text(json.dumps(value,indent=2)+'\n')
 def check_sources():
  current={str(p.relative_to(root)):sha(p) if p.is_file() else None for p in frozen};write('sources-after.json',current)
  if any(current[str(p.relative_to(root))]!=h for p,h in frozen.items()):raise ValueError('frozen source changed')
 def native(args,label):
  command=['bash','scripts/kicad/run.sh',*args];o=out/(label+'.stdout');e=out/(label+'.stderr');t=time.monotonic()
  with o.open('w') as so,e.open('w') as se:proc=subprocess.run(command,stdout=so,stderr=se,cwd=root)
  calls.append(dict(command=command,exit=proc.returncode,seconds=time.monotonic()-t,stdout_sha256=sha(o),stderr_sha256=sha(e)));write('calls.json',calls);check_sources()
  if proc.returncode:raise ValueError('native command failed; raw output retained')
 def rel(p):return str(p.relative_to(root))
 try:
  for phase in ('before','after','before_fresh','after_fresh'):
   if time.monotonic()-started>cfg['start_new_phase_budget_seconds']:raise ValueError('phase admission budget exhausted; not a completed gate')
   # Copy context into fresh phase location; no shared cache or mutable canonical board.
   folder=out.parent/(out.name+'-'+phase);folder.mkdir(exist_ok=False);phase_paths[phase]=folder;board=folder/'osc-core.kicad_pcb'
   for p in context.iterdir():
    if p.name=='sheets':shutil.copytree(p,folder/p.name)
    elif p.name in ('fp-lib-table','sym-lib-table','osc-core.kicad_pro','osc-core.kicad_sch','osc-core.kicad_dru'):shutil.copyfile(p,folder/p.name)
   source=before if phase=='before' else after if phase=='after' else phase_paths[phase.replace('_fresh','')]/'osc-core.kicad_pcb'
   shutil.copyfile(source,board);rows=[];phases[phase]=rows
   for i in range(6):
    drc=folder/f'drc-{i}.json';obs=folder/f'observation-{i}.json';label=f'{phase}-{i}'
    native(['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--save-board','--format','json','--severity-all','-o',rel(drc),rel(board)],label+'-drc')
    report=json.loads(drc.read_text())
    if report.get('kicad_version')!='10.0.6' or report.get('schematic_parity') or any(r['severity']=='error' for r in report['violations']):raise ValueError('native DRC/parity failed')
    native(['python3',rel(here/'collect.py'),rel(before),rel(after),rel(manifest),rel(board),rel(obs),'--phase',phase],label+'-collect')
    row=json.loads(obs.read_text());rows.append(row);reports[phase]=report;write('progress.json',{'phases':phases,'adopted':False})
    if settled(rows):break
   else:raise ValueError('native state did not settle within six passes')
  result=validate_protocol(phases);result['warning_comparison']=warning_compare(reports['before'],reports['after'],maps)
  result['fresh_warning_comparison']={}
  for side in ('before','after'):
   index=0 if side=='before' else 1
   result['fresh_warning_comparison'][side]=warning_compare(reports[side],reports[side+'_fresh'],[maps[index],maps[index]])
  result['adopted']=False;result['status']='CHECKPOINT ONLY; independent review and complete warning gate required'
  write('result.json',result)
 finally:
  check_sources();write('artifact-hashes.json',{str(p.relative_to(root)):sha(p) for folder in [out,*phase_paths.values()] for p in folder.rglob('*') if p.is_file() and p.name!='artifact-hashes.json'})
if __name__=='__main__':main()
