"""Select three mutually separated whole additive transactions on exact JR145.

The .25mm precheck covers proposed copper against other proposals and the22new
accepted objects only. It is not a native DRC, zone or connectivity certificate.
"""
import hashlib,json,sys
from pathlib import Path
from shapely.geometry import Point,LineString
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS
old='f08bc0fd04a23a66471a7e563f0661f6313ded52db11a51b857eff49af1c5d05';new='7e548f08e57c5b982c707583b537c7364939f4e336c1f2e8cfc2b2b7bf0253b6'
base=(ROOT/'.circuit-cache/issue189-downloaded/jr-bounded-one/.circuit-cache/osc-jack-right-grid-shards-start/osc-jack-right.kicad_pcb').read_text();current=(ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_text();assert hashlib.sha256(base.encode()).hexdigest()==old and hashlib.sha256(current.encode()).hexdigest()==new
change=delta(base,current);assert not change['removed'] and len(change['added'])==22
before,existing=copper_block_groups(base),copper_block_groups(current);assert all(v==existing[u] for u,v in before.items())
fixed=json.loads((HERE.parent/'jr-bounded-one/proposal.json').read_text())['copper'];assert {r['uuid'] for r in fixed}=={r['uuid'] for r in change['added']}
source=HERE.parent/'jr146-bounded-screen/result.json';screen=json.loads(source.read_text());excluded={'XA722A4EC7F452FB17AC1':'already accepted','XFA0270EBB537DA86D487':'deferred: earlier native split on this net; revised path not independently validated'}
transactions=[t for t in screen['transactions'] if t.get('proposal',{}).get('copper') and t['net'] not in excluded]
def gap(a,b):
 if a['net']==b['net'] or (a['kind']==b['kind']=='segment' and a['layer']!=b['layer']):return float('inf')
 def shape(r):
  if r['kind']=='via':return Point(r['at_nm']),r['diameter_nm']/2
  assert r['kind']=='segment';return LineString([r['start_nm'],r['end_nm']]),r['width_nm']/2
 x,r=shape(a);y,s=shape(b);return (x.distance(y)-r-s)/1e6
# The known failed pair must be rejected by the precheck.
failed=json.loads((HERE.parent/'jr-bounded-two/proposal.json').read_text())['copper'];assert min(gap(a,b) for i,a in enumerate(failed) for b in failed[:i])<0
selected=[];deferred=[]
for t in sorted(transactions,key=lambda t:(len(t['proposal']['copper']),t['net'])):
 p=t['proposal'];assert p['board_sha256']==old and not p['removed_uuids'];rows=p['copper']
 assert all(r['kind']=='via' or r['layer'] in SIGNAL_LAYERS for r in rows)
 fixed_gap=min(gap(a,b) for a in rows for b in fixed);conflicts=[]
 for prev in selected:
  nearest=min(gap(a,b) for a in rows for b in prev['proposal']['copper'])
  if nearest<.25:conflicts.append({'net':prev['net'],'copper_gap_mm':nearest})
 if fixed_gap<.25 or conflicts:deferred.append({'net':t['net'],'reason':'proposed cross-net clearance','fixed_gap_mm':fixed_gap,'conflicts':conflicts})
 elif len(selected)>=3:deferred.append({'net':t['net'],'reason':'three-transaction batch limit'})
 else:selected.append(t)
rows=[r for t in selected for r in t['proposal']['copper']];assert len(selected)==3 and len(rows)==108
assert len({r['uuid'] for r in rows})==108 and all(r['uuid'] not in existing for r in rows)
minimum=min(gap(a,b) for i,a in enumerate(rows) for b in rows[:i]);assert minimum>=.25
p=HERE/'proposal.json';p.write_text(json.dumps({'board_sha256':new,'removed_uuids':[],'copper':rows},indent=2)+'\n')
(HERE/'plan.json').write_text(json.dumps({'base_sha256':new,'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'scope':'Three whole signal transactions,108additions,zero removals. All50821current objects retained. Conservative new/new and prior22-object gap precheck only; full native gates mandatory.'},indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps({'status':'SELECTED AND REBASED; NATIVE NOT RUN','input_board_sha256':new,'source_board_sha256':old,'screen_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'selected_nets':[t['net'] for t in selected],'added_objects':108,'retained_current_objects':sum(map(len,existing.values())),'removed_objects':0,'minimum_new_cross_net_copper_gap_mm':minimum,'excluded':excluded,'deferred':deferred},indent=2)+'\n');print('Selected3transactions108objects; minimum new cross-net gap',minimum,'mm; native NOT RUN')
