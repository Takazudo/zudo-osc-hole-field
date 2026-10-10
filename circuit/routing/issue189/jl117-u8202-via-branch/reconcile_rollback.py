"""Verify exact rejected joint stages and complete rollback; never adopt."""
import collections,hashlib,importlib.util,json,re,subprocess,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
sha=lambda b:hashlib.sha256(b).hexdigest();source='c0665fffed85e4790aaa2ffb921cf8334ee6c0f0';bid='osc-jack-left'
def blob(p):return subprocess.check_output(['git','show',source+':'+p])
board=blob(f'boards/{bid}/{bid}.kicad_pcb');assert sha(board)=='e984c0a01156b5f282f0c849077c61572df30ee0c70dfe6c9db94fbfcfe52107'
proposal=json.loads(blob('circuit/routing/issue189/jl117-u8202-via-branch/provisional-joint-proposal.json'));cuts=sorted(proposal['removed_uuids']);assert len(cuts)==3 and len(proposal['copper'])==186
spec=importlib.util.spec_from_file_location('guard',Path.cwd()/'circuit/routing/issue189/core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
archive=Path('/tmp/issue189-u8202-full.zip');digest='4c09d2684114b9ca8bb39694406ccbf1bfc55d03b6570142e4b49892029d3f3f';assert sha(archive.read_bytes())==digest
with zipfile.ZipFile(archive) as z:
 def path(s):
  names=[n for n in z.namelist() if n.endswith(s)];assert len(names)==1,(s,names);return names[0]
 def read(s):return json.loads(z.read(path(s)))
 receipt=read('shards-issue189-u8202-via-branch.json');assert not receipt['adopted'] and receipt['copper_added']==receipt['copper_removed']==0
 assert receipt['native_warning_evidence_error']=='actual removals differ from reviewed cuts' and 'complete_native_warning_evidence' not in receipt
 stages={};summaries={};base=collections.Counter(v for rows in copper_block_groups(board.decode()).values() for v in rows);assert sum(base.values())==33425
 for key in ('start','merge-rejected-1','merge-rejected-2','merge','fresh'):
  folder=bid+'-grid-shards-'+key;raw=z.read(path(folder+'/'+bid+'.kicad_pcb'));dump=read(folder+'/dump.json');drc=read(folder+'/drc.json');assert sha(raw)==dump['board_sha256'];assert drc['kicad_version']=='10.0.6'
  for suffix in ('.kicad_pro','.kicad_dru'):assert z.read(path(folder+'/'+bid+suffix))==blob(f'boards/{bid}/{bid}'+suffix)
  if key=='start':assert raw==board;before=dump;before_drc=drc
  for field in ('pads','edges','keepouts','layers'):assert dump[field]==before[field]
  assert zone_metadata(raw.decode())==zone_metadata(board.decode())
  change=delta(board.decode(),raw.decode());removed=sorted(x['uuid'] for x in change['removed']);expected_cuts=cuts if key=='merge-rejected-1' else []
  assert removed==expected_cuts;assert unchanged_nonrouting(board.decode(),raw.decode(),expected_cuts)==1111
  expected=proposal['copper'] if key=='merge-rejected-1' else [x for x in proposal['copper'] if x['net']=='AGND'] if key=='merge-rejected-2' else []
  assert len(change['added'])==len(expected);assert {r['uuid'] for r in change['added']}=={r['uuid'] for r in expected};guard.require_known_geometry(change['added'],expected)
  if key in ('start','merge','fresh'):assert raw==board and dump['open_edges']==117
  counts=collections.Counter(v for rows in copper_block_groups(raw.decode()).values() for v in rows);assert sum((base-counts).values())==len(expected_cuts)
  gate=promotion_gate(before,dump,before_drc,drc);pads={p['uuid']:p['ref']+'.'+p['pad'] for p in dump['pads']}
  summaries[key]={'board_sha256':sha(raw),'open_edges':dump['open_edges'],'agnd_open_edges':len(dump['islands'].get('AGND',[None]))-1,'minus12_pad_groups':[[pads[u] for u in g if u in pads] for g in dump['islands'].get('-12V',[])],'drc_errors':sum(v['severity']=='error' for v in drc['violations']),'error_types':dict(collections.Counter(v['type'] for v in drc['violations'] if v['severity']=='error')),'parity':len(drc['schematic_parity']),'warnings':sum(v['severity']=='warning' for v in drc['violations']),'retained_copper':sum((base&counts).values()),'added':len(change['added']),'removed':len(removed),'unchanged_nonrouting':1111,'gate':gate};stages[key]=dump
 assert summaries['merge-rejected-1']['drc_errors']==0 and any(x['net']=='-12V' for x in summaries['merge-rejected-1']['gate']['split_pad_groups'])
 assert summaries['merge-rejected-2']['drc_errors']>0
 assert connectivity_signature(stages['merge'])==connectivity_signature(stages['fresh'])==connectivity_signature(before)
 replay=read('shards-issue189-u8202-via-branch-copper.json');assert not replay['added'] and not replay['removed'];assert sha(z.read(path('shards-issue189-u8202-via-branch-copper.json')))==receipt['copper_replay']['sha256']
 log=z.read(path('adoption.log'));settled=[]
 for step,count in re.findall(r'refill pass (\d+): (\d+) open edges',log.decode()):
  step,count=int(step),int(count)
  if step==1:settled.append([])
  assert step==len(settled[-1])+1;settled[-1].append(count)
 assert settled==[[117]*3,[117]*3,[116]*3,[117]*3,[117]*3]
 result={'status':'REJECTED JOINT TRANSACTION AND EXACT ROLLBACK INDEPENDENTLY RECONCILED; NOT ADOPTED','source_commit':source,'run':38041226566,'artifact':11666153064,'artifact_sha256':digest,'native_log_sha256':sha(log),'settled_native_passes':settled,'stages':summaries,'final_board_byte_identical_to_source':True,'final_fresh_agrees':True,'complete_warning_audits':'NOT RUN: strict reviewed-cut scope rejected after full rollback','receipt':receipt}
 Path('/tmp/issue189-u8202-full-rejection-proof.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('stages','receipt')},indent=2))
