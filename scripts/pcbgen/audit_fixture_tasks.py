"""Content-bound zone audit tasks. No cached pass flags or partial promotion.

Legacy trust is an externally approved immutable artifact+producer anchor;
new checkpoints become reusable only through a separately pinned ledger hash.
"""
import argparse,copy,hashlib,io,json,os,re,subprocess,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.audit_zone_silk_scope import artwork_batches,zone_fixture_parts,zone_fixture_batch_text,native_zone_signature
from scripts.pcbgen.zone_fixture_validation import isolated_fixture_check,text_rows
from scripts.pcbgen.zone_batch_evidence import artwork_ids,verify_result
from scripts.pcbgen.audit_added_mask import new_silk_identities
from scripts.pcbgen.complete_native_warnings import SILK_TARGET_LAYERS
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE
IMAGE='kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
VERSION='10.0.6'
KERNEL_FILES=('scripts/pcbgen/zone_fixture_validation.py','scripts/pcbgen/audit_zone_silk_scope.py','scripts/pcbgen/zone_batch_resume.py','scripts/pcbgen/audit_added_mask.py','scripts/pcbgen/zone_batch_evidence.py','scripts/pcbgen/complete_native_warnings.py','scripts/kicad/run.sh','scripts/kicad/pin.env')
SHA=lambda b:hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def identity(v):return SHA(canonical(v))
def policy(repo,revision=None):
 repo=Path(repo);blobs={}
 for name in KERNEL_FILES:
  if revision is not None:data=subprocess.check_output(['git','show',revision+':'+name],cwd=repo)
  elif (repo/name).exists():data=(repo/name).read_bytes()
  else:data=subprocess.check_output(['git','show','HEAD:'+name],cwd=repo)
  blobs[name]=SHA(data)
 return dict(image=IMAGE,version=VERSION,validator_revision=identity(blobs),kernel_blobs=blobs)
def atomic(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(canonical(value)+b'\n');os.replace(tmp,path)
def sources(before,after):
 paths=[Path(before),Path(after)];raw=[p.read_bytes() for p in paths];texts=[b.decode() for b in raw];contexts=[{s:p.with_suffix(s).read_bytes() for s in ('.kicad_pro','.kicad_dru')} for p in paths]
 if contexts[0]!=contexts[1]:raise ValueError('source context changed')
 return paths,raw,texts,contexts[0]
def zone_blocks(text):
 return {UUID_RE.search(text[a:b])[1]:text[a:b] for a,b in top_level_spans(text) if text[a:b].startswith('(zone')}
def expected_zones(text):
 rows=set()
 for uid,b in zone_blocks(text).items():
  if re.search(r'\(keepout\s',b):continue
  layers=re.search(r'\(layers?\s+([^)]*)\)',b)
  if layers is None:raise ValueError('malformed native zone layers')
  rows.update((uid,l) for l in re.findall(r'"([^"]+)"',layers[1]) if l in SILK_TARGET_LAYERS)
 return rows
class Bundle(dict):
 def __getitem__(self,key):
  value=super().__getitem__(key);return value() if callable(value) else value
def task_payload(t):return {k:v for k,v in t.items() if k!='task_id'}
def build_manifest(required,before,after,kernel):
 if kernel.get('image')!=IMAGE or kernel.get('version')!=VERSION or kernel.get('validator_revision')!=identity(kernel.get('kernel_blobs')):raise ValueError('invalid image/validator policy')
 paths,raw,texts,ctx=sources(before,after);source_hashes=[SHA(x) for x in raw]
 if required.get('version')!=VERSION or required.get('batch_size')!=16:raise ValueError('scope version/batch changed')
 if [required.get('before_sha256'),required.get('after_sha256')]!=source_hashes:raise ValueError('scope source changed')
 rows=required['zones'];expected=expected_zones(texts[1]);actual={(r['uuid'],r['layer']) for r in rows}
 if len(rows)!=len(expected) or actual!=expected:raise ValueError('whole native zone scope incomplete')
 art=[artwork_ids(x) for x in texts]
 if art[0]!=art[1]:raise ValueError('source artwork changed')
 blocks=[zone_blocks(t) for t in texts];tasks=[]
 rules=json.loads(ctx['.kicad_pro'])['board']['design_settings']['rules'];margin=max(0,int(__import__('math').ceil(rules['min_silk_clearance']*1e6)))+5_000_000
 for row in rows:
  if row['native_added_shape_empty']:continue
  s=row['required_scope'];selected=s['selected_item_uuids']
  if s.get('conservative_margin_nm')!=margin:raise ValueError('malformed native scope margin')
  if (selected!=sorted(selected) or len(selected)!=len(set(selected)) or not set(selected)<=art[1] or s['zone_uuid']!=row['uuid'] or s['layer']!=row['layer'] or s['artwork_count']!=len(art[1])):raise ValueError('malformed native scope')
  if len(s['growth_boxes_nm'])!=row['native_added_outline_count'] or any(len(b)!=4 or any(type(n) is not int for n in b) or min(b[2:])<=0 for b in s['growth_boxes_nm']):raise ValueError('malformed native growth scope')
  batches=artwork_batches(selected,16)
  if s['planned_paired_fixtures']!=2*len(batches):raise ValueError('scope batch coverage changed')
  for stage in (0,1):
   ref=dict(method='exact_native_coordinates_no_arcs',source_board_sha256=source_hashes[stage],zone_uuid=row['uuid'],layer=row['layer'],source_zone_bytes_sha256=SHA(blocks[stage][row['uuid']].encode()))
   for index,ids in enumerate(batches):
    task=dict(schema=1,zone_uuid=row['uuid'],layer=row['layer'],stage=stage,batch_index=index,item_uuids=ids,source_sha256=source_hashes,context_sha256={s:SHA(v) for s,v in ctx.items()},scope_sha256=identity(s),expected_geometry=ref,policy=kernel)
    task['task_id']=identity(task);tasks.append(task)
 if len(tasks)!=required['planned_paired_fixtures']:raise ValueError('whole task count differs from native scope')
 return dict(schema=1,source_sha256=source_hashes,context_sha256={s:SHA(v) for s,v in ctx.items()},policy=kernel,required_scope=required,tasks=tasks)
def validate_manifest(m,before,after,kernel):
 rebuilt=build_manifest(m['required_scope'],before,after,kernel)
 if rebuilt!=m:raise ValueError('manifest source/context/validator/task changed')
 return {t['task_id']:t for t in m['tasks']}
def fixture_bytes(t,texts,art,parts):
 key=(t['zone_uuid'],t['stage'])
 if key not in parts:parts[key]=zone_fixture_parts(texts[t['stage']],t['zone_uuid'],art[t['stage']])
 return zone_fixture_batch_text(parts[key],t['item_uuids']).encode()
def verify_leaf(m,t,bundle,before,after,kernel,geometry,provenance,source_cache=None):
 # Provenance is provided by a pinned artifact/ledger reader, never by a
 # boolean inside the leaf. Its kernel identity is independently compared.
 if provenance['policy']!=kernel or t['policy']!=kernel:raise ValueError('stale native image/validator provenance')
 if bundle['task_id']!=t['task_id']:raise ValueError('wrong task ID')
 if source_cache is None:
  paths,raw,texts,ctx=sources(before,after);source_cache=(texts,ctx,[artwork_ids(x) for x in texts],{})
 texts,ctx,art,parts=source_cache
 pcb=bundle['fixture'];wanted=fixture_bytes(t,texts,art,parts)
 if pcb!=wanted:raise ValueError('fixture differs from exact source')
 if bundle['context']!=ctx:raise ValueError('task context changed')
 proof=json.loads(bundle['native_validation']);expected=dict(version=VERSION,fixture_sha256=SHA(pcb),context_sha256={s:SHA(v) for s,v in ctx.items()},native_geometry_sha256=geometry)
 if proof!=expected:raise ValueError('native receipt altered or geometry mismatch')
 raw_report=bundle['report'];report=json.loads(raw_report)
 if report.get('kicad_version')!=VERSION or set(report.get('included_severities',[]))!={'error','warning','exclusion'}:raise ValueError('raw native report scope changed')
 identities=sorted((v['type'],v['severity'],tuple(sorted(x['uuid'] for x in v['items']))) for v in new_silk_identities(report,t['zone_uuid']))
 receipt=bundle['receipt']
 if (receipt['task_id']!=t['task_id'] or receipt['fixture_sha256']!=SHA(pcb) or receipt['native_validation_sha256']!=SHA(bundle['native_validation']) or receipt['report_sha256']!=SHA(raw_report) or receipt['native_geometry_sha256']!=geometry or receipt['identities']!=json.loads(json.dumps(identities))):raise ValueError('leaf native/report/identity hash mismatch')
 return receipt

def reviewed_legacy_anchor(compact,metadata,repo,kernel):
 # This allowlist is deliberately limited to the peer-reviewed terminal run.
 # New producers/checkpoints require a new externally reviewed anchor, not
 # arbitrary self-declared source IDs supplied inside task output.
 expected_source='63f9541aa68ae3e05ee9700ae71dcaea6dfe02f6'
 compact_sha='b2f5f4d7356eed1b0954e64a6eb7bef7b6195f7ff5a2d1535633eeae42ba2342'
 native_sha='aa953bd5537e320eabe7ef1119065856bad5f65fad4af3aab750040e9dda6dcb'
 if (metadata['run']!=38069793801 or metadata['tested_sha']!=expected_source or metadata['diagnostics']['id']!=11679136451 or metadata['native']['id']!=11679236513 or metadata['diagnostics']['digest']!='sha256:'+compact_sha or metadata['native']['digest']!='sha256:'+native_sha):raise ValueError('unapproved legacy producer/artifact')
 for key in ('native','diagnostics'):
  if metadata[key]['workflow_run']['head_sha']!=expected_source:raise ValueError('artifact producer commit changed')
 if policy(repo,expected_source)!=kernel or SHA(Path(compact).read_bytes())!=compact_sha:raise ValueError('producer validator/archive differs from reviewed kernel')
 with zipfile.ZipFile(compact) as z:
  names=[n for n in z.namelist() if n.endswith('terminal-inventory.json')]
  if len(names)!=1:raise ValueError('ambiguous legacy inventory')
  inventory_sha=SHA(z.read(names[0]))
 return dict(kind='externally reviewed immutable GitHub producer',run=38069793801,producer_commit=expected_source,compact_sha256=compact_sha,native_archive_sha256=native_sha,inventory_sha256=inventory_sha,policy=kernel,raw_report_ancestry=[dict(artifact=11671963117,sha256='d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5'),dict(artifact=11673646039,sha256='2cd2463554fdd63a672bf3b59dae5e3473a960017f51c142f9fc0fd7e4ebeaf4')])

def import_legacy(compact,anchor,m,before,after,kernel):
 """External approval of this exact immutable producer is REQUIRED.

The compact artifact is sufficient only under the explicit producer trust
model: its pinned worker code generated bound native receipts and inventory.
The full raw artifact remains separately pinned; this does not claim to have
locally downloaded that ZIP. No caller-controlled leaf pass flag is used.
 """
 blob=Path(compact).read_bytes()
 if SHA(blob)!=anchor['compact_sha256'] or anchor['policy']!=kernel:raise ValueError('legacy anchor image/validator/archive changed')
 if not re.fullmatch('[0-9a-f]{40}',anchor['producer_commit']) or not re.fullmatch('[0-9a-f]{64}',anchor['native_archive_sha256']):raise ValueError('unbound producer provenance')
 tasks=validate_manifest(m,before,after,kernel);z=zipfile.ZipFile(io.BytesIO(blob))
 pick=lambda suffix:next(n for n in z.namelist() if n.endswith(suffix))
 inv_raw=z.read(pick('terminal-inventory.json'));inventory=json.loads(inv_raw);inv={r['path']:r for r in inventory['inventory']}
 if len(inv)!=len(inventory['inventory']) or SHA(inv_raw)!=anchor['inventory_sha256']:raise ValueError('legacy inventory changed')
 small=z.read(pick('diagnostics.zip'))
 if SHA(small)!=inventory['diagnostics_sha256']:raise ValueError('legacy diagnostic payload changed')
 d=zipfile.ZipFile(io.BytesIO(small))
 if len(d.namelist())!=len(set(d.namelist())):raise ValueError('duplicate diagnostic paths')
 for name in d.namelist():
  p=Path(name);data=d.read(name)
  if p.is_absolute() or '..' in p.parts or name not in inv or SHA(data)!=inv[name]['sha256'] or len(data)!=inv[name]['bytes']:raise ValueError('legacy payload hash mismatch')
 required=json.loads(d.read('zones/required-scope.json'))
 if required!=m['required_scope']:raise ValueError('legacy native scope changed')
 # Actual pinned Docker use is in immutable producer stderr, not inferred
 # merely from a matching version string.
 if IMAGE not in d.read('audit.stderr').decode():raise ValueError('legacy native image evidence missing')
 mapping={(t['zone_uuid'],t['stage'],t['batch_index']):t for t in tasks.values()};bindings={};leaves={}
 paths,raw,texts,ctx=sources(before,after);art=[artwork_ids(x) for x in texts];parts={}
 for name in d.namelist():
  if not name.endswith('-progress.jsonl'):continue
  rows=[json.loads(x) for x in d.read(name).decode().splitlines()];uid=re.search(r'zone-([^/]+)-progress',name)[1]
  expected=[t for t in m['tasks'] if t['zone_uuid']==uid]
  if [(r['stage'],r['batch_index'],r['item_uuids']) for r in rows]!=[(t['stage'],t['batch_index'],t['item_uuids']) for t in expected[:len(rows)]]:raise ValueError('legacy progress not exact prefix')
  for r in rows:
   t=mapping[(uid,r['stage'],r['batch_index'])];folder=f"zones/zone-{uid}/{r['stage']}-batch-{r['batch_index']:04d}/";pcb=fixture_bytes(t,texts,art,parts)
   if SHA(pcb)!=inv[folder+'osc-core.kicad_pcb']['sha256'] or SHA(pcb)!=r['fixture_sha256']:raise ValueError('legacy exact fixture bytes changed')
   for s,v in ctx.items():
    if inv[folder+'osc-core'+s]['sha256']!=SHA(v):raise ValueError('legacy context changed')
   native=d.read(folder+'native-validation.json');report=d.read(folder+'drc.json');ref=identity(t['expected_geometry']);sig=r['native_geometry_sha256']
   if ref in bindings and bindings[ref]!=sig:raise ValueError('inconsistent native source geometry')
   bindings[ref]=sig
   receipt=dict(task_id=t['task_id'],fixture_sha256=SHA(pcb),native_validation_sha256=SHA(native),report_sha256=SHA(report),native_geometry_sha256=sig,identities=r['identities'])
   bundle=Bundle(task_id=t['task_id'],fixture=lambda t=t:fixture_bytes(t,texts,art,parts),context=ctx,native_validation=native,report=report,receipt=receipt,provenance=anchor)
   # All immutable blob hashes have already been checked above. This local
   # adapter records equivalent prior native proof; it never reruns LoadBoard.
   proof=json.loads(native);expected_proof=dict(version=VERSION,fixture_sha256=SHA(pcb),context_sha256={s:SHA(v) for s,v in ctx.items()},native_geometry_sha256=sig)
   if proof!=expected_proof or SHA(report)!=r['report_sha256']:raise ValueError('legacy native receipt/report changed')
   report_json=json.loads(report)
   if report_json.get('kicad_version')!=VERSION or set(report_json.get('included_severities',[]))!={'error','warning','exclusion'}:raise ValueError('legacy raw report scope changed')
   actual=sorted((v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in new_silk_identities(report_json,uid))
   if json.loads(json.dumps(actual))!=r['identities']:raise ValueError('legacy identity receipt changed')
   if t['task_id'] in leaves:raise ValueError('duplicate legacy task')
   leaves[t['task_id']]=bundle
 return leaves,bindings

def selection(m,leaves,packets):
 required={t['task_id'] for t in m['tasks']};used=set()
 if not set(leaves)<=required:raise ValueError('unknown cached task ID')
 for packet in packets:
  if not packet or len(packet)!=len(set(packet)):raise ValueError('empty/duplicate task packet')
  if not set(packet)<=required-set(leaves) or used&set(packet):raise ValueError('wrong/nonmissing/overlapping task IDs')
  used.update(packet)
 return sorted(required-set(leaves))
def write_checkpoint(root,t,bundle):
 folder=Path(root)/t['task_id'];folder.mkdir(parents=True,exist_ok=True)
 # Completed metadata is last and atomic. A killed DRC leaves no completed
 # checkpoint, even if it left a partial raw report.
 for name,key in [('osc-core.kicad_pcb','fixture'),('native-validation.json','native_validation'),('drc.json','report')]:
  path=folder/name;tmp=path.with_name(path.name+'.tmp');tmp.write_bytes(bundle[key]);os.replace(tmp,path)
 for suffix,data in bundle['context'].items():(folder/('osc-core'+suffix)).write_bytes(data)
 atomic(folder/'complete.json',bundle['receipt']);return SHA((folder/'complete.json').read_bytes())
def read_checkpoint(root,task_id,expected_hash,provenance):
 folder=Path(root)/task_id;path=folder/'complete.json'
 if SHA(path.read_bytes())!=expected_hash:raise ValueError('checkpoint ledger hash mismatch')
 receipt=json.loads(path.read_bytes())
 if receipt['task_id']!=task_id:raise ValueError('checkpoint wrong ID')
 return dict(task_id=task_id,fixture=(folder/'osc-core.kicad_pcb').read_bytes(),context={s:(folder/('osc-core'+s)).read_bytes() for s in ('.kicad_pro','.kicad_dru')},native_validation=(folder/'native-validation.json').read_bytes(),report=(folder/'drc.json').read_bytes(),receipt=receipt,provenance=provenance)
def run_missing(m,before,after,task_ids,output,kernel,bindings):
 """Run only explicitly selected tasks; new tasks always use fresh validator.

Container image/aggregate resource ownership is enforced by the host pilot
controller. This function alone never supplies an image provenance anchor.
 """
 tasks=validate_manifest(m,before,after,kernel)
 if len(task_ids)!=len(set(task_ids)) or not set(task_ids)<=set(tasks):raise ValueError('duplicate/wrong task IDs')
 version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
 if version!=VERSION:raise ValueError('requires pinned native10.0.6')
 import pcbnew
 paths,raw,texts,ctx=sources(before,after);art=[artwork_ids(x) for x in texts];parts={};native_sources={};ledger={};output=Path(output)
 if output.exists():raise ValueError('worker output must be disjoint/new')
 output.mkdir(parents=True)
 for task_id in task_ids:
  t=tasks[task_id];ref=identity(t['expected_geometry'])
  if ref not in bindings:raise ValueError('expected native geometry lacks reviewed binding')
  stage=t['stage']
  if stage not in native_sources:native_sources[stage]=pcbnew.LoadBoard(str(paths[stage]))
  board=native_sources[stage];layer=pcbnew.F_Cu if t['layer']=='F.Cu' else pcbnew.B_Cu;zone=next(z for z in board.Zones() if z.m_Uuid.AsString()==t['zone_uuid']);sig=native_zone_signature(zone.GetFilledPolysList(layer))
  if sig!=bindings[ref]:raise ValueError('source native geometry binding changed')
  folder=output/task_id;folder.mkdir();fixture=folder/'osc-core.kicad_pcb';fixture.write_bytes(fixture_bytes(t,texts,art,parts))
  for suffix,data in ctx.items():fixture.with_suffix(suffix).write_bytes(data)
  isolated_fixture_check(fixture,t['zone_uuid'],layer,t['item_uuids'],text_rows(board),sig)
  report=folder/'drc.json';subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--output',str(report),str(fixture)],check=True)
  native=(folder/'native-validation.json').read_bytes();raw_report=report.read_bytes();rows=sorted((v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in new_silk_identities(json.loads(raw_report),t['zone_uuid']))
  receipt=dict(task_id=task_id,fixture_sha256=SHA(fixture.read_bytes()),native_validation_sha256=SHA(native),report_sha256=SHA(raw_report),native_geometry_sha256=sig,identities=json.loads(json.dumps(rows)))
  bundle=dict(task_id=task_id,fixture=fixture.read_bytes(),context={s:fixture.with_suffix(s).read_bytes() for s in ctx},native_validation=native,report=raw_report,receipt=receipt)
  verify_leaf(m,t,bundle,before,after,kernel,sig,dict(policy=kernel),(texts,ctx,art,parts))
  ledger[task_id]=write_checkpoint(output,t,bundle);atomic(output/'ledger.json',dict(status='PARTIAL TASK CHECKPOINTS; NOT FULL COVERAGE',tasks=ledger))
 return ledger

def final_union(m,before,after,bundles,kernel,bindings):
 tasks=validate_manifest(m,before,after,kernel);by_id={}
 for b in bundles:
  key=b['task_id']
  if key not in tasks or key in by_id:raise ValueError('unknown/duplicate final task ID')
  by_id[key]=b
 if set(by_id)!=set(tasks):raise ValueError('incomplete final task coverage')
 paths,raw,texts,ctx=sources(before,after);source_cache=(texts,ctx,[artwork_ids(x) for x in texts],{})
 for key,b in by_id.items():
  t=tasks[key];ref=identity(t['expected_geometry'])
  if ref not in bindings:raise ValueError('missing native geometry binding')
  verify_leaf(m,t,b,before,after,kernel,bindings[ref],b['provenance'],source_cache)
 result=dict(status='DERIVED FULL TASK UNION; CALLER GATES STILL REQUIRED',version=VERSION,before_sha256=m['source_sha256'][0],after_sha256=m['source_sha256'][1],zone_silk_scope_complete=True,zones=copy.deepcopy(m['required_scope']['zones']),new_zone_silk_identities=[])
 access={};all_new=set()
 for row in result['zones']:
  if row['native_added_shape_empty']:continue
  s=row['required_scope'];uid=row['uuid'];fixtures=[];unions=[set(),set()];geometry={}
  access[f'zone-{uid}-scope.json']=canonical({k:v for k,v in s.items() if k not in ('planned_paired_fixtures','resume_prefix_count','required_new_reports')})
  for t in m['tasks']:
   if t['zone_uuid']!=uid:continue
   b=by_id[t['task_id']];r=b['receipt'];geometry[str(t['stage'])]=r['native_geometry_sha256'];folder=f"zone-{uid}/{t['stage']}-batch-{t['batch_index']:04d}/"
   access[folder+'osc-core.kicad_pcb']=b['fixture'];access[folder+'drc.json']=b['report']
   for suffix,data in b['context'].items():access[folder+'osc-core'+suffix]=data
   fixtures.append(dict(stage=t['stage'],batch_index=t['batch_index'],item_uuids=t['item_uuids'],fixture_sha256=r['fixture_sha256'],native_geometry_sha256=r['native_geometry_sha256'],report_sha256=r['report_sha256'],identities=r['identities']))
   unions[t['stage']].update((a,c,tuple(ids)) for a,c,ids in r['identities'])
  delta=unions[1]-unions[0];all_new.update(delta);row['native_silk_pairs']=dict(artwork_batch_size=16,selected_item_uuids=s['selected_item_uuids'],conservative_margin_nm=s['conservative_margin_nm'],native_geometry_method='exact_native_coordinates_no_arcs',source_geometry_sha256=geometry,fixtures=fixtures,before_identities=sorted(unions[0]),after_identities=sorted(unions[1]),new_identities=sorted(delta))
 result['new_zone_silk_identities']=sorted(all_new);access['result.json']=canonical(result)
 proof=verify_result(lambda name:access[name],Path(before),Path(after))
 if proof['new_zone_silk_identities']:raise ValueError('new full native zone warning identities')
 # Never perform publication or infer complete_reports success here.
 return result,proof
