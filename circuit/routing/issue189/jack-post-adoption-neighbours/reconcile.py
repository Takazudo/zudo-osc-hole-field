"""Independently reconcile the fixed additive JR pilot; never adopt."""
import argparse,collections,hashlib,importlib.util,json,sys,zipfile
from pathlib import Path
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata
spec=importlib.util.spec_from_file_location('geometry_guard',ROOT/'circuit/routing/issue189/core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
p=argparse.ArgumentParser();p.add_argument('archive',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--artifact',required=True,type=int);p.add_argument('--output',type=Path,required=True);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
with a.archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==a.sha256
bid='osc-jack-right';local=ROOT/'circuit/routing/issue189/jack-post-adoption-neighbours';proposal=json.loads((local/'proposal.json').read_text());expected='35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445'
with zipfile.ZipFile(a.archive) as z:
 def path(suffix,optional=False):
  matches=[n for n in z.namelist() if n.endswith(suffix)]
  if optional and not matches:return None
  assert len(matches)==1,(suffix,matches);return matches[0]
 def read(suffix):return json.loads(z.read(path(suffix)))
 receipt=read('issue189-local-'+bid+'/result.json');assert receipt['input_board_sha256']==expected and receipt['adopted'] is False
 assert receipt['plan_sha256']==sha((local/'plan.json').read_bytes())
 stage_names={'base':bid+'-grid-189-local-base','candidate':bid+'-grid-189-jr134-post-adoption-neighbours','fresh':bid+'-grid-189-jr134-post-adoption-neighbours-fresh'}
 stages={}
 for key,folder in stage_names.items():
  board_path=path(folder+'/'+bid+'.kicad_pcb',optional=True);dump_path=path(folder+'/dump.json',optional=True);drc_path=path(folder+'/drc.json',optional=True)
  if not all((board_path,dump_path,drc_path)):continue
  text=z.read(board_path).decode();dump=json.loads(z.read(dump_path));drc=json.loads(z.read(drc_path));digest=sha(text.encode())
  assert dump['board_sha256']==digest and drc['kicad_version']=='10.0.6'
  context={s:z.read(path(folder+'/'+bid+s)) for s in ('.kicad_pro','.kicad_dru')}
  stages[key]=dict(text=text,dump=dump,drc=drc,sha256=digest,context=context)
 assert 'base' in stages and stages['base']['sha256']==expected
 before=stages['base'];base_copper=collections.Counter(b for rows in copper_block_groups(before['text']).values() for b in rows);assert sum(base_copper.values())==51177
 summaries={};gates={}
 for key,data in stages.items():
  assert data['context']==before['context']
  for field in ('pads','edges','keepouts','layers'):assert data['dump'][field]==before['dump'][field]
  assert zone_metadata(data['text'])==zone_metadata(before['text'])
  count=unchanged_nonrouting(before['text'],data['text']);copper=collections.Counter(b for rows in copper_block_groups(data['text']).values() for b in rows)
  assert not base_copper-copper
  added=copper-base_copper
  if key!='base':
   replay=delta(before['text'],data['text']);assert not replay['removed']
   assert {r['uuid'] for r in replay['added']}=={r['uuid'] for r in proposal['copper']}
   guard.require_known_geometry(replay['added'],proposal['copper']);assert sum(added.values())==118
   gates[key]=promotion_gate(before['dump'],data['dump'],before['drc'],data['drc'])
  summaries[key]=dict(board_sha256=data['sha256'],open_edges=data['dump']['open_edges'],drc_errors=sum(v['severity']=='error' for v in data['drc']['violations']),parity=len(data['drc']['schematic_parity']),warnings=sum(v['severity']=='warning' for v in data['drc']['violations']),retained_copper=sum(base_copper.values()),added_copper=sum(added.values()),removed_copper=0,unchanged_nonrouting_objects=count)
 fresh='candidate' in stages and 'fresh' in stages and connectivity_signature(stages['candidate']['dump'])==connectivity_signature(stages['fresh']['dump'])
 if 'fresh' in stages:assert fresh
 if 'gate' in receipt:
  assert 'fresh' in gates and json.loads(json.dumps(gates['fresh']))==receipt['gate']
  assert receipt['candidate_sha256']==stages['fresh']['sha256']
  replay_path=path('issue189-local-'+bid+'/copper.json');assert sha(z.read(replay_path))==receipt['replay_sha256']
 eligible=bool(fresh and receipt.get('gate',{}).get('adopted'))
 result=dict(status='INDEPENDENT PILOT RECONCILIATION; NOT ADOPTED',adopted=False,run=38014685459,source_commit='4c462ea81d1526461c283f075af55568f13d7d75',artifact=a.artifact,artifact_sha256=a.sha256,pilot_receipt=receipt,stages=summaries,native_gates=gates,fresh_agrees=fresh,native_pilot_eligible=eligible,complete_warning_evidence=False,next_gate='Complete source-bound warning evidence and a fresh full adoption replay are still mandatory; raw silk categories are capped')
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('pilot_receipt','native_gates')},indent=2))
