"""Route at most12 bounded paired proposals on the unchanged saved JR input."""
import argparse,copy,hashlib,itertools,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args();screen=json.loads((HERE/'screen.json').read_text());d=json.loads(a.dump.read_text())
assert sha(a.dump)==screen['dump_sha256']=='f885375bc4a8ac5cc0ca879f841a4d3768a560876e43c023e2abe14e38a86c8a'
board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(board)==screen['board_sha256']==d['board_sha256']
for path,key in [('floorplan-candidate.json','floorplan_sha256'),('partition-input.json','source_sha256'),('connector-packing-candidate.json','headers_sha256')]:assert sha(ROOT/'design/partition'/path)==screen[key]
groups={}
for c in screen['static_candidates']:groups.setdefault((c['target'],c['peer']),[]).append(c)
for values in groups.values():values.sort(key=lambda c:(sum(x*x for move in c['delta_mm'].values() for x in move),json.dumps(c['delta_mm'],sort_keys=True)))
chosen=[]
for index in range(max(map(len,groups.values()),default=0)):
 for key in sorted(groups):
  if index<len(groups[key]):chosen.append(groups[key][index])
chosen=chosen[:12]
controls={}
for target in sorted({c['target'] for c in chosen}):
 path=HERE.parent/'jr134-movable-ground-connectors'/target/'route-result.json'
 if not path.exists():path=HERE.parent/'jr134-movable-ground'/target/'route-result.json'
 old=json.loads(path.read_text());assert old['input_dump_sha256']==screen['dump_sha256'] and old['board_sha256']==screen['board_sha256']
 control=[r for r in old['transactions'] if r['delta_mm']==[0,0]]
 assert {r['mode'] for r in control}=={'direct','plane'} and all(not r['complete_raster_transaction'] for r in control)
 controls[target]=dict(path=str(path.relative_to(ROOT)),sha256=sha(path),unmoved_direct_complete=False,unmoved_plane_complete=False)
started=time.monotonic();rows=[];positive=False
output=dict(status='RUNNING READ-ONLY VIRTUAL COMPARISON; NATIVE NOT RUN',board_sha256=sha(board),dump_sha256=sha(a.dump),screen_sha256=sha(HERE/'screen.json'),selected_candidates=len(chosen),compatible_static_candidates=screen['candidate_count'],saved_controls=controls,transactions=rows)
def save():
 output['elapsed_seconds']=time.monotonic()-started;(HERE/'route-result.json').write_text(json.dumps(output,indent=2)+'\n')
save()
for index,c in enumerate(chosen):
 ref=c['target'];original=next(p for p in d['pads'] if p['ref']==ref and p['net']=='AGND');group=next(g for g in d['islands']['AGND'] if original['uuid'] in g);assert group==[original['uuid']]
 main=max(d['islands']['AGND'],key=len);x,y=[v/1e6 for v in original['xy']];bounds=[x-8,y-8,x+8,y+8]
 for mode in ('direct','plane'):
  current=copy.deepcopy(d)
  for pad in current['pads']:
   if pad['ref'] not in c['delta_mm']:continue
   shift=[round(x*1e6) for x in c['delta_mm'][pad['ref']]]
   pad['xy']=[v+s for v,s in zip(pad['xy'],shift)];pad['poly']=[[v+s for v,s in zip(point,shift)] for point in pad['poly']]
  for b in c['bridges']:current['tracks'].append(dict(uuid=b['uuid'],net=b['net'],layer=b['layer'],a=b['start_nm'],b=b['end_nm'],width=b['width_nm']))
  current['islands']['AGND']=[group,main] if mode=='direct' else [group];events=[]
  result,removed=route(current,['AGND'],planes={'AGND':'In1.Cu'} if mode=='plane' else None,allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.0125,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=bounds,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-right'))
  assert not removed
  copper,_=copper_rows(result,'osc-jack-right','issue189-jr-paired-'+str(index)+'-'+mode);complete=bool(copper) and bool(result) and all(r['path'] for r in result)
  item=dict(candidate_index=index,target=ref,peer=c['peer'],delta_mm=c['delta_mm'],mode=mode,complete_raster_transaction=complete,bounds_mm=bounds,results=result,diagnostics=events,virtual_proposal=dict(board_sha256=d['board_sha256'],source_translations=c['source_translations'],removed_uuids=[],copper=c['bridges']+copper))
  rows.append(item);save();print(index,ref,c['peer'],mode,'complete',complete,'objects',len(copper)+len(c['bridges']),flush=True)
  if complete:positive=True;break
 if positive:break
assert sha(board)==screen['board_sha256']
output.update(status='VIRTUAL COMPARISON COMPLETE; NO BOARD CHANGE; NATIVE SOURCE/DRC/PARITY/TOPOLOGY/WARNING/RETENTION NOT RUN',positive_virtual_transaction=positive,completed_trials=len(rows),untested_selected_candidates=len(chosen)-len({r['candidate_index'] for r in rows}));save()
