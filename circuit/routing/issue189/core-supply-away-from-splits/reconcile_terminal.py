"""Reconcile timed-out native core evidence without treating partial audits as acceptance."""
import collections,hashlib,importlib.util,json,re,subprocess,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting,new_silk_identities
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
sha=lambda b:hashlib.sha256(b).hexdigest();source='47bb19a42f6612a114e4aff51c4b120301fe5e71';bid='osc-core'
def blob(p):return subprocess.check_output(['git','show',source+':'+p])
board=blob(f'boards/{bid}/{bid}.kicad_pcb');assert sha(board)=='fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10'
proposal=json.loads(blob('circuit/routing/issue189/core-supply-away-from-splits/proposal.json'));assert len(proposal['copper'])==118 and not proposal['removed_uuids']
spec=importlib.util.spec_from_file_location('guard',Path.cwd()/'circuit/routing/issue189/core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
archive=Path('/tmp/issue189-core-supply-terminal.zip');digest='0855bdbccdc250a3a273511b8d519cedc3f110a86cc0c887ac08a5f94596d8e4'
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
with zipfile.ZipFile(archive) as z:
 def path(s):
  names=[n for n in z.namelist() if n.endswith(s)];assert len(names)==1,(s,names);return names[0]
 def read(s):return json.loads(z.read(path(s)))
 assert len(z.namelist())==len(set(z.namelist()))
 assert not any(n.endswith('shards-issue189-supply-away-from-splits.json') for n in z.namelist()),'No completed adoption receipt expected'
 stages={};summaries={};source_copper=collections.Counter(v for rows in copper_block_groups(board.decode()).values() for v in rows);assert sum(source_copper.values())==133551
 for key in ('start','merge','fresh'):
  folder=bid+'-grid-shards-'+key;raw=z.read(path(folder+'/'+bid+'.kicad_pcb'));dump=read(folder+'/dump.json');drc=read(folder+'/drc.json');assert sha(raw)==dump['board_sha256'];assert drc['kicad_version']=='10.0.6' and not drc['schematic_parity'] and not any(v['severity']=='error' for v in drc['violations'])
  for suffix in ('.kicad_pro','.kicad_dru'):assert z.read(path(folder+'/'+bid+suffix))==blob(f'boards/{bid}/{bid}'+suffix)
  if key=='start':assert sha(raw)=='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66';before=dump;before_drc=drc;before_text=raw.decode()
  for field in ('pads','edges','keepouts','layers'):assert dump[field]==before[field]
  assert zone_metadata(raw.decode())==zone_metadata(board.decode());assert unchanged_nonrouting(board.decode(),raw.decode())==3807
  change=delta(board.decode(),raw.decode());assert not change['removed'];expected=[] if key=='start' else proposal['copper'];assert len(change['added'])==len(expected);assert {r['uuid'] for r in change['added']}=={r['uuid'] for r in expected};guard.require_known_geometry(change['added'],expected)
  gate=promotion_gate(before,dump,before_drc,drc);assert dump['open_edges']==(1402 if key=='start' else 1311)
  if key!='start':assert not gate['adopted'] and len(gate['split_pad_groups'])==2 and all(g['net']=='AGND' for g in gate['split_pad_groups']) and not gate['new_warning_identities']
  if key!='start':
   for group in gate['split_pad_groups']:
    ids=set(group['previously_connected_pads']);parts=[sorted(ids.intersection(component)) for component in dump['islands']['AGND'] if ids.intersection(component)];group['after_partitions']=parts
  counts=collections.Counter(v for rows in copper_block_groups(raw.decode()).values() for v in rows);assert not source_copper-counts
  summaries[key]={'board_sha256':sha(raw),'open_edges':dump['open_edges'],'open_by_net':{n:len(g)-1 for n,g in dump['islands'].items() if n in ('AGND','+12V','-12V','+5V')},'drc_errors':0,'parity':0,'raw_warnings':sum(v['severity']=='warning' for v in drc['violations']),'retained_copper':133551,'added':len(expected),'removed':0,'unchanged_nonrouting':3807,'raw_gate':gate};stages[key]=dump
 assert connectivity_signature(stages['merge'])==connectivity_signature(stages['fresh']);assert summaries['merge']['board_sha256']==summaries['fresh']['board_sha256']=='4f90bfc16d5e338cc31adc3a41f0da8ff8f289a24b963ab8f9c9caf9d98cec10'
 audit='osc-core-grid-shards-complete-warnings/native-audits/';zone_result=read(audit+'zones/result.json');assert zone_result=={'status':'STARTED; NO COMPLETE ZONE EVIDENCE','version':'10.0.6','before_sha256':summaries['start']['board_sha256'],'after_sha256':summaries['fresh']['board_sha256']}
 assert not any(n.endswith('native-audits/proof.json') for n in z.namelist())
 uid='601e02b2-8ccb-5c28-83e5-03789d47fbbd';scope=read(audit+'zones/zone-'+uid+'-scope.json');assert len(scope['selected_item_uuids'])==1833;selected=scope['selected_item_uuids'];batches=[selected[i:i+16] for i in range(0,len(selected),16)];assert len(batches)==115
 progress=[json.loads(line) for line in z.read(path(audit+'zones/zone-'+uid+'-progress.jsonl')).decode().splitlines()];assert len(progress)==146
 assert [(r['stage'],r['batch_index'],r['item_uuids']) for r in progress]==[(stage,i,b) for stage in (0,1) for i,b in enumerate(batches)][:146]
 for row in progress:
  folder=audit+'zones/zone-'+uid+f"/{row['stage']}-batch-{row['batch_index']:04d}/";fixture=z.read(path(folder+bid+'.kicad_pcb'));assert sha(fixture)==row['fixture_sha256'];report_raw=z.read(path(folder+'drc.json'));assert sha(report_raw)==row['report_sha256'];report=json.loads(report_raw);assert report['kicad_version']=='10.0.6' and set(report['included_severities'])=={'error','warning','exclusion'}
  for suffix in ('.kicad_pro','.kicad_dru'):assert z.read(path(folder+bid+suffix))==blob(f'boards/{bid}/{bid}'+suffix)
  actual={(v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in new_silk_identities(report,uid)};assert actual=={(a,b,tuple(ids)) for a,b,ids in row['identities']}
 log=z.read(path('adoption.log'));settled=[]
 for step,count in re.findall(r'refill pass (\d+): (\d+) open edges',log.decode()):
  step,count=int(step),int(count)
  if step==1:settled.append([])
  assert step==len(settled[-1])+1;settled[-1].append(count)
 assert settled==[[1402]*3,[1311]*3,[1311]*3];assert b'KeyboardInterrupt' in log
 result={'status':'REJECTED CORE CANDIDATE: TWO ORIGINAL AGND GROUPS SPLIT; AUDIT ALSO TIMED OUT','source_commit':source,'run':38023611361,'artifact':11666004488,'artifact_sha256':digest,'native_log_sha256':sha(log),'settled_native_passes':settled,'stages':summaries,'completed_zone':{'zone_uuid':uid,'selected_artwork':1833,'planned_paired_batches':230,'hash_verified_ordered_completed_prefix':146,'remaining_in_this_zone':84,'last_completed':[1,30],'native_reconstruction_for_resume':'NOT RUN LOCALLY; required by existing resume validator on pinned oracle'},'zone_result':zone_result,'complete_warning_audit':'INCOMPLETE; full proof absent','publication_refill_and_canonical_promotion':'NOT RUN','next_action':'Do not resume audits or adopt unchanged1311 candidate. Identify and repair or omit whole supply cases that split the two original AGND groups, then run new bounded native snapshots and all strict acceptance gates.'}
 Path('/tmp/issue189-core-supply-partial-proof.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
