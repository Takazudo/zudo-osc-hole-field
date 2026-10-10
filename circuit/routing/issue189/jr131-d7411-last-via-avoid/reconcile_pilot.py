"""Independently reconcile the fixed additive JR pilot; never adopt."""
import argparse,collections,hashlib,importlib.util,json,re,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata
spec=importlib.util.spec_from_file_location('geometry_guard',ROOT/'circuit/routing/issue189/core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--run',type=int,required=True);p.add_argument('--sha256',required=True);p.add_argument('--artifact',required=True,type=int);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
with a.archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==a.sha256
bid='osc-jack-right';local=ROOT/'circuit/routing/issue189/jr131-d7411-last-via-avoid';proposal=json.loads((local/'proposal.json').read_text());expected='7bb70ac47e12c8bb2e2362d78f7602bdf99c2a69214c68aebeef273b0ce11965'
assert a.run==38031328950
source_commit='790c75f851e15fe76052b6aa1e6f4c6a133025dc'
source_board=subprocess.check_output(['git','show',source_commit+':boards/'+bid+'/'+bid+'.kicad_pcb'],cwd=ROOT)
assert sha(source_board)==expected
source_context={s:subprocess.check_output(['git','show',source_commit+':boards/'+bid+'/'+bid+s],cwd=ROOT) for s in ('.kicad_pro','.kicad_dru')}
with zipfile.ZipFile(a.archive) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 def path(suffix,optional=False):
  matches=[n for n in z.namelist() if n.endswith(suffix)]
  if optional and not matches:return None
  assert len(matches)==1,(suffix,matches);return matches[0]
 def read(suffix):return json.loads(z.read(path(suffix)))
 receipt=read('issue189-local-'+bid+'/result.json');assert receipt['input_board_sha256']==expected and receipt['adopted'] is False
 assert receipt['plan_sha256']==sha((local/'plan.json').read_bytes())
 stage_names={'base':bid+'-grid-189-local-base','candidate':bid+'-grid-189-jr131-d7411-last-via-avoid','fresh':bid+'-grid-189-jr131-d7411-last-via-avoid-fresh'}
 stages={}
 for key,folder in stage_names.items():
  board_path=path(folder+'/'+bid+'.kicad_pcb',optional=True);dump_path=path(folder+'/dump.json',optional=True);drc_path=path(folder+'/drc.json',optional=True)
  if not all((board_path,dump_path,drc_path)):continue
  text=z.read(board_path).decode();dump=json.loads(z.read(dump_path));drc=json.loads(z.read(drc_path));digest=sha(text.encode())
  assert dump['board_sha256']==digest and drc['kicad_version']=='10.0.6'
  context={s:z.read(path(folder+'/'+bid+s)) for s in ('.kicad_pro','.kicad_dru')}
  stages[key]=dict(text=text,dump=dump,drc=drc,sha256=digest,context=context)
 assert 'base' in stages and stages['base']['sha256']==expected
 before=stages['base'];assert before['dump']['open_edges']==131 and before['text'].encode()==source_board and before['context']==source_context
 base_copper=collections.Counter(b for rows in copper_block_groups(before['text']).values() for b in rows);assert sum(base_copper.values())==51402
 summaries={};gates={}
 for key,data in stages.items():
  assert data['context']==before['context']
  for field in ('pads','edges','keepouts','layers'):assert data['dump'][field]==before['dump'][field]
  assert zone_metadata(data['text'])==zone_metadata(before['text'])
  assert data['dump']['open_edges']==sum(len(g)-1 for g in data['dump']['islands'].values())
  count=unchanged_nonrouting(before['text'],data['text']);assert count==1080
  copper=collections.Counter(b for rows in copper_block_groups(data['text']).values() for b in rows)
  assert not base_copper-copper
  added=copper-base_copper
  if key!='base':
   replay=delta(before['text'],data['text']);assert not replay['removed']
   assert {r['uuid'] for r in replay['added']}=={r['uuid'] for r in proposal['copper']}
   guard.require_known_geometry(replay['added'],proposal['copper']);assert sum(added.values())==172
   gates[key]=promotion_gate(before['dump'],data['dump'],before['drc'],data['drc'])
  summaries[key]=dict(board_sha256=data['sha256'],open_edges=data['dump']['open_edges'],drc_errors=sum(v['severity']=='error' for v in data['drc']['violations']),parity=len(data['drc']['schematic_parity']),warnings=sum(v['severity']=='warning' for v in data['drc']['violations']),retained_copper=sum(base_copper.values()),added_copper=sum(added.values()),removed_copper=0,unchanged_nonrouting_objects=count)
 fresh='candidate' in stages and 'fresh' in stages and connectivity_signature(stages['candidate']['dump'])==connectivity_signature(stages['fresh']['dump'])
 if 'fresh' in stages:assert fresh
 if 'gate' in receipt:
  assert 'fresh' in gates and json.loads(json.dumps(gates['fresh']))==receipt['gate']
  assert receipt['candidate_sha256']==stages['fresh']['sha256']
  replay_path=path('issue189-local-'+bid+'/copper.json');assert sha(z.read(replay_path))==receipt['replay_sha256']
 log_bytes=z.read(path('local-repair.log'));settled=[]
 for step,count in re.findall(r'refill pass (\d+): (\d+) open edges',log_bytes.decode()):
  step,count=int(step),int(count)
  if step==1:settled.append([])
  assert settled and step==len(settled[-1])+1
  settled[-1].append(count)
 assert len(settled)==len(stages),(settled,list(stages))
 for passes,(stage,data) in zip(settled,stages.items()):assert len(passes)>=3 and passes[-3:]==[data['dump']['open_edges']]*3
 eligible=bool(fresh and receipt.get('gate',{}).get('adopted'))
 result=dict(status='INDEPENDENT PILOT RECONCILIATION; NOT ADOPTED',adopted=False,run=a.run,source_commit='790c75f851e15fe76052b6aa1e6f4c6a133025dc',artifact=a.artifact,artifact_sha256=a.sha256,settled_native_passes=settled,native_log_sha256=sha(log_bytes),pilot_receipt=receipt,stages=summaries,native_gates=gates,fresh_agrees=fresh,native_pilot_eligible=eligible,complete_warning_evidence=False,next_gate='Complete source-bound warning evidence and a fresh full adoption replay are still mandatory; raw silk categories are capped')
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('pilot_receipt','native_gates')},indent=2))
