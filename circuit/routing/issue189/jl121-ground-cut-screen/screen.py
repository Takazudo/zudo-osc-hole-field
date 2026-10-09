"""Raster-only cut prefilter; native cut topology and victim restoration still mandatory."""
import json,time,hashlib,sys
from pathlib import Path
from shapely.geometry import Point,LineString
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import SIGNAL_LAYERS,LAYER_COST,RAILS,neck_kwargs,repair_selection,repair_bounds
p=Path('.circuit-cache/issue189-downloaded/jl-three-finer-ground/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json');d=json.loads(p.read_text());sha=d['board_sha256'];assert sha==hashlib.sha256(Path('boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()
main=max(d['islands']['AGND'],key=len);targets=[]
for group in d['islands']['AGND']:
 if group==main:continue
 for pad in d['pads']:
  if pad['uuid'] not in group:continue
  cut=[]
  for t in d['tracks']:
   if t['net'] in RAILS+['AGND'] or t['layer'] not in pad['layers']:continue
   distance=Point(pad['xy']).distance(LineString([t['a'],t['b']]))/1e6-t['width']/2e6
   if distance<1.2:cut.append(t)
  if not 1<=len(cut)<=12 or len({t['net'] for t in cut})>2:continue
  xs=[pad['xy'][0]/1e6]+[q[0]/1e6 for t in cut for q in [t['a'],t['b']]];ys=[pad['xy'][1]/1e6]+[q[1]/1e6 for t in cut for q in [t['a'],t['b']]];bounds=[min(xs)-6,min(ys)-6,max(xs)+6,max(ys)+6]
  if max(bounds[2]-bounds[0],bounds[3]-bounds[1])>50:continue
  targets.append((len(cut),pad['ref'],pad['pad'],pad,group,cut,bounds))
out=[];start=time.monotonic()
for _,_,_,pad,group,cut,bounds in sorted(targets,key=lambda t:t[:3]):
 if time.monotonic()-start>600:break
 ids={t['uuid'] for t in cut};spec={'repair_targets':['AGND'],'repair_ground_pad_uuids':[pad['uuid']],'repair_source_uuids':sorted(ids),'repair_bounds_mm':bounds};repair_selection(d,spec);repair_bounds(d,spec,['AGND'],ids)
 search={**d,'tracks':[t for t in d['tracks'] if t['uuid'] not in ids],'islands':{'AGND':[group,main]}};events=[];t=time.monotonic()
 results,removed=route(search,['AGND'],res=.025,clearance=.25,rail_width=.3,via_diameter=.6,allowed_layers=SIGNAL_LAYERS,layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],fill_guards={'-12V':'In3.Cu'},window_mm=6,max_expansions=300000,bounds_mm=bounds,diagnostics=events,**neck_kwargs('osc-jack-left'))
 rows,_=copper_rows(results,'osc-jack-left','issue189-jl121-cut-prefilter-'+pad['ref']);assert not removed
 out.append({'pad':pad['ref']+'.'+pad['pad'],'spec':spec,'selected_objects':cut,'victim_nets':sorted({t['net'] for t in cut}),'elapsed_seconds':time.monotonic()-t,'results':results,'diagnostics':events,'ground_copper':rows});print(out[-1]['pad'],'cuts',len(ids),'ground objects',len(rows),flush=True)
 Path('circuit/routing/issue189/jl121-ground-cut-screen/result.json').write_text(json.dumps({'status':'RASTER ONLY; SIGNAL CUT TOPOLOGY/Victim restoration NOT CHECKED; NOT A COMPLETE PROPOSAL','input_dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'board_sha256':sha,'elapsed_seconds':time.monotonic()-start,'transactions':out},indent=2)+'\n')
