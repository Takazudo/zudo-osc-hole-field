"""Compare source-defined R8127 translations against an unmoved same-input control."""
import copy,hashlib,json,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).parent;p=Path('.circuit-cache/issue189-downloaded/jl-u1518-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json')
d=json.loads(p.read_text());screen=json.loads((HERE/'result.json').read_text());assert d['board_sha256']==screen['board_sha256']==hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()
original=next(p for p in d['pads'] if p['ref']=='R8127' and p['net']=='AGND');group=next(g for g in d['islands']['AGND'] if original['uuid'] in g);assert group==[original['uuid']]
main=max(d['islands']['AGND'],key=len);out=[];start=time.monotonic()
for delta in [[0,0]]+[c['delta_mm'] for c in screen['static_candidates']]:
 current=copy.deepcopy(d);shift=[round(x*1e6) for x in delta]
 for pad in current['pads']:
  if pad['ref']=='R8127':
   pad['xy']=[a+b for a,b in zip(pad['xy'],shift)];pad['poly']=[[a+b for a,b in zip(v,shift)] for v in pad['poly']]
 signal=next(p for p in d['pads'] if p['ref']=='R8127' and p['net']!='AGND');bridge=[]
 if any(shift):
  row=dict(kind='segment',uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-r8127-bridge-'+str(delta))),net=signal['net'],layer='B.Cu',start_nm=signal['xy'],end_nm=[a+b for a,b in zip(signal['xy'],shift)],width_nm=200000);bridge=[row]
  current['tracks'].append(dict(uuid=row['uuid'],net=row['net'],layer=row['layer'],a=row['start_nm'],b=row['end_nm'],width=row['width_nm']))
 current['islands']['AGND']=[group];events=[]
 x,y=[v/1e6 for v in original['xy']];bounds=[x-6,y-6,x+6.8,y+6.8]
 results,removed=route(current,['AGND'],planes={'AGND':'In1.Cu'},allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.0125,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=bounds,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'));assert not removed
 rows,_=copper_rows(results,'osc-jack-left','issue189-r8127-move-'+str(delta));complete=bool(rows) and all(r['path'] for r in results)
 out.append(dict(delta_mm=delta,complete_raster_transaction=complete,results=results,diagnostics=events,proposal=dict(board_sha256=d['board_sha256'],removed_uuids=[],copper=bridge+rows),bounds_mm=bounds));print(delta,'complete',complete,'objects',len(rows)+len(bridge),flush=True)
(HERE/'route-result.json').write_text(json.dumps(dict(status='VIRTUAL PLACEMENT RASTER COMPARISON ONLY; NATIVE PLACEMENT/REGENERATION NOT RUN',input_dump_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),board_sha256=d['board_sha256'],elapsed_seconds=time.monotonic()-start,transactions=out),indent=2)+'\n')
