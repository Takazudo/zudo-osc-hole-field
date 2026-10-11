"""Independently reconcile the exact read-only jl-u8202 native cut pilot; never adopt."""
import argparse,collections,hashlib,json,re,subprocess,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
from scripts.pcbgen.uuid_tools import top_level_spans
def reviewed_cut_nonrouting(before,after):
 def blocks(text):
  return collections.Counter(text[a:b] for a,b in top_level_spans(text) if text[a+1:b].split(None,1)[0].rstrip(')') not in ('segment','via','zone'))
 old,new=blocks(before),blocks(after);assert old==new,'Nonrouting geometry/settings changed'
 return sum(old.values())
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--artifact',required=True,type=int);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
source='94c5c311265abfb8cf73b736e572642d76db3bef';run=38040356008;bid='osc-jack-left';name=bid+'-grid-189-jl117-u8202-via-branch'
def blob(path):return subprocess.check_output(['git','show',source+':'+path])
planbytes=blob('circuit/routing/issue189/jl117-u8202-via-branch/plan.json');plan=json.loads(planbytes);boundaries_source=json.loads(blob('circuit/routing/issue189/jl117-u8202-via-branch/boundary-endpoints.json'));selected={'boundary_endpoints':boundaries_source,'via':{'net':boundaries_source[0]['victim_net']}};cuts=set(plan['stage']['repair_source_uuids']);assert len(cuts)==3
source_board=blob('boards/'+bid+'/'+bid+'.kicad_pcb');assert sha(source_board)==plan['input_board_sha256']
context={s:blob('boards/'+bid+'/'+bid+s) for s in ('.kicad_pro','.kicad_dru')}
with a.archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==a.sha256
with zipfile.ZipFile(a.archive) as z:
 names=z.namelist();assert len(names)==len(set(names))
 def path(suffix,optional=False):
  matches=[n for n in names if n.endswith(suffix)]
  if optional and not matches:return None
  assert len(matches)==1,(suffix,matches);return matches[0]
 def read(suffix):return json.loads(z.read(path(suffix)))
 receipt=read('issue189-local-'+bid+'/result.json');assert receipt['adopted'] is False and receipt['input_board_sha256']==plan['input_board_sha256'] and receipt['plan_sha256']==sha(planbytes)
 stages={}
 for key,folder in [('base',bid+'-grid-189-local-base'),('cut',name+'-cut'),('candidate',name),('fresh',name+'-verify')]:
  files=[path(folder+'/'+f,optional=True) for f in (bid+'.kicad_pcb','dump.json','drc.json')]
  if not all(files):continue
  data=z.read(files[0]);dump=json.loads(z.read(files[1]));drc=json.loads(z.read(files[2]));assert sha(data)==dump['board_sha256'];assert drc['kicad_version']=='10.0.6'
  ctx={s:z.read(path(folder+'/'+bid+s)) for s in context};assert ctx==context
  stages[key]={'bytes':data,'text':data.decode(),'dump':dump,'drc':drc}
 assert 'base' in stages and 'cut' in stages,'Native baseline and cut topology are mandatory'
 before=stages['base'];assert before['bytes']==source_board and before['dump']['open_edges']==117
 base=collections.Counter(v for vs in copper_block_groups(before['text']).values() for v in vs);assert sum(base.values())==33425
 summaries={};gates={}
 for key,s in stages.items():
  for field in ('pads','edges','layers','keepouts'):assert s['dump'][field]==before['dump'][field]
  assert zone_metadata(s['text'])==zone_metadata(before['text']);assert reviewed_cut_nonrouting(before['text'],s['text'])==1111
  assert s['dump']['open_edges']==sum(len(g)-1 for g in s['dump']['islands'].values())
  counts=collections.Counter(v for vs in copper_block_groups(s['text']).values() for v in vs);change=delta(before['text'],s['text']);removed={x['uuid'] for x in change['removed']};added={x['uuid'] for x in change['added']}
  assert removed==(set() if key=='base' else cuts),removed
  assert not added.intersection({x['uuid'] for x in before['dump']['tracks']+before['dump']['vias']}),'Existing UUID replaced'
  assert sum((base-counts).values())==(0 if key=='base' else 3)
  if key=='cut':assert not change['added']
  if key not in ('base','cut'):gates[key]=promotion_gate(before['dump'],s['dump'],before['drc'],s['drc'])
  summaries[key]={'board_sha256':sha(s['bytes']),'open_edges':s['dump']['open_edges'],'drc_errors':sum(v['severity']=='error' for v in s['drc']['violations']),'parity':len(s['drc']['schematic_parity']),'warnings':sum(v['severity']=='warning' for v in s['drc']['violations']),'retained_copper':sum((base&counts).values()),'added_copper':sum((counts-base).values()),'removed_copper':sum((base-counts).values()),'unchanged_nonrouting_objects':1111}
 boundaries=[]
 for endpoint in selected['boundary_endpoints']:
  retained=[t for t in before['dump']['tracks'] if t['uuid'] not in cuts and t['net']==endpoint['victim_net'] and t['layer']==endpoint['layer'] and endpoint['xy'] in (t['a'],t['b'])]
  assert len(retained)==1,(endpoint,retained);uid=retained[0]['uuid'];memberships={}
  for key,s in stages.items():
   assert any(t['uuid']==uid for t in s['dump']['tracks']);groups=s['dump']['islands'].get(endpoint['victim_net'])
   if groups is None:memberships[key]={'fully_connected_net':True}
   else:
    found=[(i,g) for i,g in enumerate(groups) if uid in g];assert len(found)==1,(key,uid)
    memberships[key]={'component':found[0][0],'members':found[0][1]}
  boundaries.append({**endpoint,'retained_uuid':uid,'native_membership':memberships})
 fresh='candidate' in stages and 'fresh' in stages and connectivity_signature(stages['candidate']['dump'])==connectivity_signature(stages['fresh']['dump'])
 if 'fresh' in stages:assert fresh
 if 'gate' in receipt:
  assert 'candidate' in gates and json.loads(json.dumps(gates['candidate']))==receipt['gate'];assert receipt['candidate_sha256']==summaries['candidate']['board_sha256']
  replaybytes=z.read(path('issue189-local-'+bid+'/copper.json'));assert sha(replaybytes)==receipt['replay_sha256'];assert json.loads(replaybytes)==delta(source_board.decode(),stages['candidate']['text'])
  assert receipt['retained_copper']['removed_objects']==3 and not receipt['retained_copper']['changed_existing_uuids']
 log=z.read(path('local-repair.log'));settled=[]
 for step,count in re.findall(r'refill pass (\d+): (\d+) open edges',log.decode()):
  step,count=int(step),int(count)
  if step==1:settled.append([])
  assert settled and step==len(settled[-1])+1;settled[-1].append(count)
 # Native stage retries may add intermediate checks; preserve them rather than mislabel them.
 for key,s in stages.items():assert any(len(v)>=3 and v[-3:]==[s['dump']['open_edges']]*3 for v in settled),(key,settled)
 victim=selected['via']['net'];victim_restored='fresh' in stages and victim not in stages['fresh']['dump']['islands']
 eligible=bool(fresh and victim_restored and receipt.get('gate',{}).get('adopted'))
 result={'status':'INDEPENDENT READ-ONLY NATIVE CUT RECONCILIATION; NOT ADOPTED','run':run,'source_commit':source,'artifact':a.artifact,'artifact_sha256':a.sha256,'native_log_sha256':sha(log),'settled_native_passes':settled,'pilot_receipt':receipt,'stages':summaries,'gates':gates,'boundary_obligations':boundaries,'victim_fully_reconnected':victim_restored,'fresh_agrees':fresh,'pilot_eligible':eligible,'complete_warning_evidence':False,'next_gate':'Full warning adoption, exact-head CI and integration still required even if pilot eligible'}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('pilot_receipt','gates','boundary_obligations')},indent=2))
