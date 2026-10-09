"""Make the native ground-corridor victim junctions explicit and trim unused tails."""
import hashlib,json,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
cache=ROOT/'.circuit-cache/issue189-downloaded/jl-ground-corridor'
b=json.loads((cache/'osc-jack-left-grid-189-local-base/dump.json').read_text())
d=json.loads((cache/'osc-jack-left-grid-189-jl-ground-corridor-verify/dump.json').read_text())
sha='3d40f1db27f350ce063bf601cab2eeb9f6394b47da9930fca21b6bc0258d2352'
assert b['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()
assert d['board_sha256']=='52ccc61d654358e065e965a8017480c3d5f916a7a11def61f4bdca5e913e47d3'
r=json.loads((HERE/'jl-ground-corridor-result.json').read_text());assert not r['gate']['split_pad_groups'] and not r['gate']['native_errors']
assert {u for _,ids in r['gate']['new_warning_identities'] for u in ids}=={'314bbbeb-a6d9-58dc-8d13-9539dd4a935d','8594279c-ab8c-5519-991c-1428359db0fe','e715f264-d849-58bf-b75f-f6b35aba63b8'}
replay=HERE/'jl-ground-corridor-copper.json';assert hashlib.sha256(replay.read_bytes()).hexdigest()==r['replay_sha256'];delta=json.loads(replay.read_text())
original={t['uuid']:t for t in b['tracks']};current={t['uuid']:t for t in d['tracks']}
screen=json.loads((HERE/'jl-ground-inner-tail-screen.json').read_text());assert len(screen['removed_tracks'])==18 and screen['length_mm']<4
assert screen['input_dump_sha256']==hashlib.sha256((cache/'osc-jack-left-grid-189-jl-ground-corridor-verify/dump.json').read_bytes()).hexdigest()
for t in screen['removed_tracks']:assert t==original[t['uuid']]==current[t['uuid']]
net='XB64017DF2FF0BC77988E';tail=current['e715f264-d849-58bf-b75f-f6b35aba63b8'];branch=current['36b24407-7b1f-5c21-8639-5276799d066a'];long=current['9f7c1a32-43a8-5388-aedb-ea218917c455']
for t in (tail,branch,long):assert t==original[t['uuid']] and t['net']==net
assert tail['a']==[143500000,122700000] and tail['b']==[143500000,122500000]
assert branch['a']==tail['b'] and branch['b']==[142900000,121900000]
assert long['a']==[159800000,123600000] and long['b']==[146800000,123600000]
added={x['uuid'] for x in delta['added']};rows=[]
for t in d['tracks']:
 if t['uuid'] not in added:continue
 row={'kind':'segment','uuid':t['uuid'],'net':t['net'],'start_nm':t['a'],'end_nm':t['b'],'width_nm':t['width'],'layer':t['layer']}
 if t['uuid']=='8594279c-ab8c-5519-991c-1428359db0fe':
  assert t['a']==[143200000,122150000] and t['b']==[143200000,122100000]
  row['start_nm']=[143200000,122200000]
 elif t['uuid']=='b0909c66-abc4-5a27-9a80-71d0df973609':
  assert t['a']==[146800000,123450000] and t['b']==[146750000,123500000]
  row['end_nm']=long['b']
 else:rows.append(row);continue
 del row['uuid'];row['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-ground-junction/'+json.dumps(row,sort_keys=True)));rows.append(row)
for v in d['vias']:
 if v['uuid'] in added:rows.append({'kind':'via','uuid':v['uuid'],'net':v['net'],'at_nm':v['xy'],'diameter_nm':v['diameter'],'drill_nm':v['drill']})
assert len(rows)==27
replacement={'kind':'segment','net':net,'start_nm':[143200000,122200000],'end_nm':branch['b'],'width_nm':branch['width'],'layer':branch['layer']}
assert branch['width']==200000 and branch['layer']=='F.Cu'
replacement['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-ground-trim/'+json.dumps(replacement,sort_keys=True)));rows.append(replacement)
removed={x['uuid'] for x in delta['removed']}|{t['uuid'] for t in screen['removed_tracks']}|{tail['uuid'],branch['uuid']}
assert len(removed)==21
assert all(sum(o['uuid']==u for kind in ('tracks','vias') for o in b[kind])==1 for u in removed)
proposal={'board_sha256':sha,'removed_uuids':sorted(removed),'copper':rows};p=HERE/'jl-ground-junction-proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
plan={'board':'osc-jack-left','input_board_sha256':sha,'name':'189-jl-ground-junction','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'Native ground corridor closes135 to134 with no original group splits but three dangling warnings. Make both new victim endpoints meet retained centerlines, remove newly redundant terminal branches (3.673mm In2 plus0.624mm F), preserve the long13mm original branch and all other copper. Full native original membership/warning/DRC/parity/fresh gates mandatory.'}
(HERE/'jl-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n');print('Prepared28 additions/21 removals; native NOT RUN')
