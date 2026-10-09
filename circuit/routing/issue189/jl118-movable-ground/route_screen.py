"""Bounded same-input virtual movement/control comparison; native placement not run."""
import argparse,copy,hashlib,json,sys,time,uuid
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import LAYER_COST,RAILS,neck_kwargs
parser=argparse.ArgumentParser();parser.add_argument('ref',choices=['R8107','R8270','R8273','RB2214','RB2315']);args=parser.parse_args();ref=args.ref
here=Path(__file__).parent/ref;p=Path('.circuit-cache/issue189-downloaded/jl-r8276-adoption/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');d=json.loads(p.read_text());screen=json.loads((here/'result.json').read_text());side=screen['part']['side']
assert d['board_sha256']==screen['board_sha256']==hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()
original=next(p for p in d['pads'] if p['ref']==ref and p['net']=='AGND');group=next(g for g in d['islands']['AGND'] if original['uuid'] in g);assert group==[original['uuid']];main=max(d['islands']['AGND'],key=len)
out=[];started=time.monotonic();positive=False
moves=sorted([c['delta_mm'] for c in screen['static_candidates']],key=lambda v:(sum(x*x for x in v),v))
for mode in ['direct','plane']:
 for delta in [[0,0]]+moves:
  current=copy.deepcopy(d);shift=[round(x*1e6) for x in delta]
  for pad in current['pads']:
   if pad['ref']==ref:
    pad['xy']=[a+b for a,b in zip(pad['xy'],shift)];pad['poly']=[[a+b for a,b in zip(v,shift)] for v in pad['poly']]
  signal=next(p for p in d['pads'] if p['ref']==ref and p['net']!='AGND');bridge=[]
  if any(shift):
   row=dict(kind='segment',uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-jl118-move-bridge-'+ref+str(delta))),net=signal['net'],layer=side,start_nm=signal['xy'],end_nm=[a+b for a,b in zip(signal['xy'],shift)],width_nm=200000);bridge=[row]
   current['tracks'].append(dict(uuid=row['uuid'],net=row['net'],layer=row['layer'],a=row['start_nm'],b=row['end_nm'],width=row['width_nm']))
  current['islands']['AGND']=[group,main] if mode=='direct' else [group];events=[];x,y=[v/1e6 for v in original['xy']];bounds=[x-8,y-8,x+8,y+8]
  results,removed=route(current,['AGND'],planes={'AGND':'In1.Cu'} if mode=='plane' else None,allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.0125,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=bounds,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-left'));assert not removed
  rows,_=copper_rows(results,'osc-jack-left','issue189-jl118-move-'+ref+mode+str(delta));complete=bool(rows) and all(r['path'] for r in results)
  item=dict(mode=mode,delta_mm=delta,complete_raster_transaction=complete,results=results,diagnostics=events,bounds_mm=bounds,virtual_proposal=dict(board_sha256=d['board_sha256'],required_placement_translation={'ref':ref,'delta_nm':shift,'side':side,'rotation_deg':screen['part']['rotation_deg']},removed_uuids=[],copper=bridge+rows));out.append(item)
  print(ref,mode,delta,'complete',complete,'objects',len(rows)+len(bridge),flush=True)
  if complete:positive=True;break
 if positive:break
(here/'route-result.json').write_text(json.dumps(dict(status='VIRTUAL PLACEMENT ONLY; NATIVE SOURCE REGENERATION/DRC/PARITY/TOPOLOGY/RETENTION NOT RUN',input_dump_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),screen_sha256=hashlib.sha256((here/'result.json').read_bytes()).hexdigest(),board_sha256=d['board_sha256'],elapsed_seconds=time.monotonic()-started,transactions=out),indent=2)+'\n')
