"""Rebind two saved additive paths to the accepted JR145 board; never replace copper."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta
cache=ROOT/'.circuit-cache/issue189-downloaded/jr-bounded-one/.circuit-cache'
a=(cache/'osc-jack-right-grid-shards-start/osc-jack-right.kicad_pcb').read_text()
b=(ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_text()
old='f08bc0fd04a23a66471a7e563f0661f6313ded52db11a51b857eff49af1c5d05';new='7e548f08e57c5b982c707583b537c7364939f4e336c1f2e8cfc2b2b7bf0253b6'
assert hashlib.sha256(a.encode()).hexdigest()==old and hashlib.sha256(b.encode()).hexdigest()==new
change=delta(a,b);assert not change['removed'] and len(change['added'])==22
before,current=copper_block_groups(a),copper_block_groups(b);assert all(rows==current[u] for u,rows in before.items())
source=ROOT/'circuit/routing/issue189/jr146-bounded-screen/result.json';screen=json.loads(source.read_text())
nets={'X3307A17C148FAA8F7A4D','X31F914D5C9FE2488242A'}
selected=[t for t in screen['transactions'] if t['net'] in nets];assert len(selected)==2
rows=[]
for t in selected:
 p=t['proposal'];assert p['board_sha256']==old and not p['removed_uuids'];rows.extend(p['copper'])
assert len(rows)==31 and len({r['uuid'] for r in rows})==31 and all(r['uuid'] not in current for r in rows)
proposal={'board_sha256':new,'removed_uuids':[],'copper':rows};p=HERE/'proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
(HERE/'plan.json').write_text(json.dumps({'base_sha256':new,'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'D7504.1 and R7626.1 additive paths;31objects,zero removals,all prior50821objects retained. Native combined gate NOT RUN.'},indent=2)+'\n')
(HERE/'rebase.json').write_text(json.dumps({'status':'REVIEWED REBASE; NATIVE COMBINED GATE NOT RUN','screen_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'old_board_sha256':old,'new_board_sha256':new,'selected_nets':sorted(nets),'prior_added_objects_preserved':22,'retained_current_objects':sum(map(len,current.values())),'added_objects':31,'removed_objects':0,'new_uuid_collisions':0},indent=2)+'\n')
print('Prepared31additions on JR145; all',sum(map(len,current.values())),'current objects retained; native NOT RUN')
