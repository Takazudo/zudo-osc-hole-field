"""Select bounded additive supply paths; native validation and any rebase remain mandatory."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups
source=HERE.parent/'core1441-rail-screen';paths=[source/'first24.json',source/'rest.json'];data=[json.loads(p.read_text()) for p in paths]
sha='a0e3cff1ebc211564b8be10f6a993d50fb6d4372edde86a056ebc8dda3ea5932'
assert all(d['published_board_sha256']==sha for d in data)
assert len({d['input_native_dump_sha256'] for d in data})==1 and len({d['router_sha256'] for d in data})==1
rows=[];selected=[]
for t in [t for d in data for t in d['transactions']]:
 p=t['proposal'];assert p['board_sha256']==sha and not p['removed_uuids'];c=p['copper']
 if not 1<=len(c)<=2 or not all(x['kind']=='segment' and x['width_nm']==250000 for x in c):continue
 length=sum(math.dist(x['start_nm'],x['end_nm'])/1e6 for x in c)
 if length>2:continue
 rows.extend(c);selected.append({'net':t['net'],'pads':t['pads'],'objects':len(c),'total_length_mm':length})
assert len(selected)==109 and len(rows)==135 and len({r['uuid'] for r in rows})==135
board=ROOT/'boards/osc-core/osc-core.kicad_pcb';assert hashlib.sha256(board.read_bytes()).hexdigest()==sha,'Core changed; rebase with retention proof, never overwrite it'
existing=copper_block_groups(board.read_text());assert all(r['uuid'] not in existing for r in rows)
proposal={'board_sha256':sha,'removed_uuids':[],'copper':rows};out=HERE/'proposal-original.json';out.write_text(json.dumps(proposal,indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps({'status':'SELECTED ONLY; NATIVE NOT RUN; REBASE AFTER SOLE CORE WRITER FINISHES','source_result_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},'source_board_sha256':sha,'input_native_dump_sha256':data[0]['input_native_dump_sha256'],'router_sha256':data[0]['router_sha256'],'selection_rule':'1or2segments only;250000nm wide;total length<=2mm;no vias or removals','selected_targets':selected,'added_segments':135,'retained_input_objects':sum(map(len,existing.values())),'proposal_sha256':hashlib.sha256(out.read_bytes()).hexdigest()},indent=2)+'\n')
print('Selected109targets/135segments; all',sum(map(len,existing.values())),'existing objects retained; native NOT RUN')
