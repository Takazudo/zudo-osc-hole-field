"""Reconcile one exact successful complete-warning adoption artifact; never publish."""
import argparse,collections,hashlib,importlib.util,json,re,subprocess,sys,zipfile
from pathlib import Path,PurePosixPath
ROOT=Path.cwd();sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature,warning_identities
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata
from scripts.pcbgen.complete_native_warnings import complete_reports
spec=importlib.util.spec_from_file_location('geometry_guard',ROOT/'circuit/routing/issue189/core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
CONFIG={
 'osc-core':dict(run=38023611361,source='47bb19a42f6612a114e4aff51c4b120301fe5e71',label='issue189-supply-away-from-splits',input='fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10',filled_before='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66',filled_after=None,before=1402,after=None,retained=133551,added=118,nonrouting=3807,proposal='core-supply-away-from-splits/proposal.json'),
 'osc-jack-right':dict(run=38024958370,source='b16a7853a3bbbb1b37630045a14771f541b1db22',label='issue189-in3-two-whole',input='22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd',filled_before='22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd',filled_after='7bb70ac47e12c8bb2e2362d78f7602bdf99c2a69214c68aebeef273b0ce11965',before=133,after=131,retained=51256,added=146,nonrouting=1080,proposal='jr-layer-escape/proposal.json')}

p=argparse.ArgumentParser();p.add_argument('board',choices=CONFIG);p.add_argument('archive',type=Path);p.add_argument('--sha256',required=True);p.add_argument('--artifact',required=True,type=int);p.add_argument('--destination',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args();c=CONFIG[a.board];bid=a.board;sha=lambda b:hashlib.sha256(b).hexdigest()
with a.archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==a.sha256
board_path=f'boards/{bid}/{bid}.kicad_pcb';source=subprocess.check_output(['git','show',c['source']+':'+board_path],cwd=ROOT);assert sha(source)==c['input']
source_context={suffix:subprocess.check_output(['git','show',c['source']+':'+f'boards/{bid}/{bid}'+suffix],cwd=ROOT) for suffix in ('.kicad_pro','.kicad_dru')}
proposal=json.loads(subprocess.check_output(['git','show',c['source']+':circuit/routing/issue189/'+c['proposal']],cwd=ROOT));assert len(proposal['copper'])==c['added'] and not proposal['removed_uuids']
a.destination.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(a.archive) as z:
 assert len(z.namelist())==len(set(z.namelist()))
 def path(suffix):
  matches=[n for n in z.namelist() if n.endswith(suffix)];assert len(matches)==1,(suffix,matches);return matches[0]
 def read(suffix):return json.loads(z.read(path(suffix)))
 if c['after'] is None:
  observed=read(bid+'-grid-shards-fresh/dump.json')
  c['after']=sum(len(groups)-1 for groups in observed['islands'].values())
  assert c['after']==observed['open_edges'] and 0<=c['after']<c['before']
  c['filled_after']=sha(z.read(path(bid+'-grid-shards-fresh/'+bid+'.kicad_pcb')))
  assert c['filled_after']==observed['board_sha256']
 log_bytes=z.read(path('.circuit-cache/adoption.log'));settled=[]
 for step,count in re.findall(r'refill pass (\d+): (\d+) open edges',log_bytes.decode()):
  step,count=int(step),int(count)
  if step==1:settled.append([])
  assert settled and step==len(settled[-1])+1
  settled[-1].append(count)
 assert len(settled) in (3,4),settled
 for i,passes in enumerate(settled):
  assert len(passes)>=3 and passes[-3:]==[c['before'] if i==0 else c['after']]*3,settled
 receipt_name=path(f'boards/{bid}/reports/grid-routing/shards-{c["label"]}.json');receipt=json.loads(z.read(receipt_name))
 assert receipt['adopted'] is True,receipt.get('rejection_reason')
 assert receipt['input_board_sha256']==c['input'] and receipt['native_zone_batch_size']==16
 assert receipt['independent_connectivity_agrees'] and receipt['copper_added']==c['added'] and receipt['copper_removed']==0
 assert not receipt['native_errors'] and receipt['drc_errors']==receipt['parity']==0
 assert receipt['split_pad_groups']==receipt['new_warning_identities']==[]
 folders={s:bid+'-grid-shards-'+s for s in ('start','merge','fresh')};stages={};extracted=[]
 def extract(name,relative):
  rel=PurePosixPath(relative);info=z.getinfo(name)
  assert not rel.is_absolute() and '..' not in rel.parts and (info.external_attr>>16)&0o170000!=0o120000
  data=z.read(name);dest=a.destination/rel;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();dest.write_bytes(data)
  extracted.append(dict(archive_path=name,path=str(rel),bytes=len(data),sha256=sha(data)));return dest
 for stage,folder in folders.items():
  for name in (bid+'.kicad_pcb',bid+'.kicad_pro',bid+'.kicad_dru','dump.json','drc.json'):extract(path(folder+'/'+name),stage+'/'+name)
  root=a.destination/stage;text=(root/(bid+'.kicad_pcb')).read_text();dump=json.loads((root/'dump.json').read_text());drc=json.loads((root/'drc.json').read_text())
  assert dump['board_sha256']==sha(text.encode())==(c['filled_before'] if stage=='start' else c['filled_after'])
  assert drc['kicad_version']=='10.0.6' and not drc['schematic_parity'] and not any(v['severity']=='error' for v in drc['violations'])
  for suffix,data in source_context.items():assert (root/(bid+suffix)).read_bytes()==data
  stages[stage]=dict(text=text,dump=dump,drc=drc,root=root)
 before=stages['start'];fresh=stages['fresh'];base_copper=collections.Counter(b for rows in copper_block_groups(before['text']).values() for b in rows)
 assert base_copper==collections.Counter(b for rows in copper_block_groups(source.decode()).values() for b in rows) and sum(base_copper.values())==c['retained']
 assert before['dump']['open_edges']==c['before'] and fresh['dump']['open_edges']==c['after']
 for stage in ('merge','fresh'):
  data=stages[stage]
  for field in ('pads','edges','keepouts','layers'):assert data['dump'][field]==before['dump'][field]
  assert zone_metadata(data['text'])==zone_metadata(before['text']) and unchanged_nonrouting(before['text'],data['text'])==c['nonrouting']
  change=delta(before['text'],data['text']);assert not change['removed'] and len(change['added'])==c['added']
  assert {r['uuid'] for r in change['added']}=={r['uuid'] for r in proposal['copper']};guard.require_known_geometry(change['added'],proposal['copper'])
 assert connectivity_signature(stages['merge']['dump'])==connectivity_signature(fresh['dump'])
 raw=promotion_gate(before['dump'],fresh['dump'],before['drc'],fresh['drc']);assert json.loads(json.dumps(raw))==receipt['raw_promotion_gate']
 audit_suffix=bid+'-grid-shards-complete-warnings/native-audits/proof.json';audit_prefix=path(audit_suffix)[:-len('proof.json')]
 for info in z.infolist():
  if info.filename.startswith(audit_prefix) and not info.is_dir():extract(info.filename,'native-audits/'+info.filename[len(audit_prefix):])
 audit=a.destination/'native-audits'
 full_before,full_after,proof=complete_reports(before['root']/(bid+'.kicad_pcb'),fresh['root']/(bid+'.kicad_pcb'),before['drc'],fresh['drc'],audit/'holes-before',audit/'holes-after',audit/'silk',audit/'zones')
 assert proof==receipt['complete_native_warning_evidence']==json.loads((audit/'proof.json').read_text())
 gate=promotion_gate(before['dump'],fresh['dump'],full_before,full_after);assert gate['adopted'] and all(receipt[k]==json.loads(json.dumps(v)) for k,v in gate.items())
 published=fresh['text'].encode();publication_fresh=False
 if receipt['publication_cache']:
  compact=bid+'-grid-189-compact';refill=compact+'-refill'
  published=z.read(path(compact+'/'+bid+'.kicad_pcb'));refilled=read(refill+'/dump.json');report=read(refill+'/drc.json')
  assert sha(z.read(path(refill+'/'+bid+'.kicad_pcb')))==refilled['board_sha256']==receipt['publication_cache']['refilled_board_sha256']
  assert report['kicad_version']=='10.0.6' and not report['schematic_parity'] and not any(v['severity']=='error' for v in report['violations'])
  assert connectivity_signature(refilled)==connectivity_signature(fresh['dump']) and warning_identities(report)==warning_identities(fresh['drc'])
  for key in ('pads','tracks','vias'):assert sorted(json.dumps(v,sort_keys=True) for v in refilled[key])==sorted(json.dumps(v,sort_keys=True) for v in fresh['dump'][key])
  assert not delta(fresh['text'],published.decode())['removed'] and not delta(fresh['text'],published.decode())['added']
  assert zone_metadata(published.decode())==zone_metadata(fresh['text']) and unchanged_nonrouting(fresh['text'],published.decode())==c['nonrouting']
  publication_fresh=True
 assert sha(published)==receipt['candidate_board_sha256'] and receipt['native_filled_board_sha256']==c['filled_after']
 replay_path=path(receipt['copper_replay']['path']);replay_bytes=z.read(replay_path);replay=json.loads(replay_bytes)
 assert sha(replay_bytes)==receipt['copper_replay']['sha256'] and replay['base_sha256']==c['input'] and not replay['removed'] and len(replay['added'])==c['added']
 guard.require_known_geometry(replay['added'],proposal['copper'])
 (a.destination/'published.kicad_pcb').write_bytes(published);(a.destination/'receipt.json').write_bytes(z.read(receipt_name));(a.destination/'copper.json').write_bytes(replay_bytes)
 result=dict(status='COMPLETE NATIVE ADOPTION ARTIFACT RECONCILED; MAIN INTEGRATION NOT PERFORMED BY THIS SCRIPT',run=c['run'],source_commit=c['source'],artifact=a.artifact,artifact_sha256=a.sha256,worker_adopted=True,main_adopted=False,settled_native_passes=settled,native_log_sha256=sha(log_bytes),board=bid,input_board_sha256=c['input'],native_filled_board_sha256=c['filled_after'],published_board_sha256=sha(published),replay_sha256=sha(replay_bytes),open_edges_before=c['before'],open_edges_after=c['after'],drc_errors=0,parity=0,retained_copper=c['retained'],added_copper=c['added'],removed_copper=0,unchanged_nonrouting_objects=c['nonrouting'],fresh_agrees=True,publication_refill_agrees=publication_fresh,raw_gate=raw,complete_gate=gate,complete_warning_proof=proof,original_findings=[len(before['drc']['violations']),len(fresh['drc']['violations'])],complete_findings=[len(full_before['violations']),len(full_after['violations'])],extracted_files=extracted)
 a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('extracted_files','raw_gate')},indent=2))
