"""Bounded same-input search exclusions at shared vias of two native-rejected paths."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import RAILS,LAYER_COST,neck_kwargs
HERE=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();parser=argparse.ArgumentParser();parser.add_argument('dump',type=Path);dump=parser.parse_args().dump;assert sha(dump)=='a9f1b738f0e541ca5f01d7057f7bb002289e0bf43b90cb223253287f4e5abd84'
d=json.loads(dump.read_text());board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(board)==d['board_sha256']=='7bb70ac47e12c8bb2e2362d78f7602bdf99c2a69214c68aebeef273b0ce11965'
screen=ROOT/'circuit/routing/issue189/jr131-d7411-in2/screen.json';s=json.loads(screen.read_text());assert s['router_sha256']==sha(ROOT/'scripts/pcbgen/grid_router.py')
case=next(c for c in s['cases'] if c['net']=='XE8DD7DCFD030742EDE49' and c['domain']=='in2')['historical']
result=dict(status='BOUNDED SEARCH ONLY; NATIVE NOT RUN',board_sha256=sha(board),dump_sha256=sha(dump),router_sha256=s['router_sha256'],baseline_screen_sha256=sha(screen),method='Only search-time via exclusions at shared first/last via locations of native-rejected In2/four-layer paths. No physical keepout, pad, trace or rule changes.',cases=[])
for label,centres in [('first',[(382.7,191.7)]),('last',[(392.375,192.65)]),('both',[(382.7,191.7),(392.375,192.65)])]:
 for domain,layers in [('in2',['F.Cu','In2.Cu','B.Cu']),('four-layer',['F.Cu','In2.Cu','In3.Cu','B.Cu'])]:
  trial=copy.deepcopy(d);trial['islands'][case['net']]=case['native_groups'];new=[]
  for x,y in centres:
   h=.15;new.append(dict(name='search-only-native-rejection-via-exclusion',layers=layers,poly=[[round((x-h)*1e6),round((y-h)*1e6)],[round((x+h)*1e6),round((y-h)*1e6)],[round((x+h)*1e6),round((y+h)*1e6)],[round((x-h)*1e6),round((y+h)*1e6)]],tracks=False,vias=True))
  trial['keepouts']+=new;events=[];start=time.monotonic()
  paths,removed=route(trial,[case['net']],allowed_layers=layers,layer_cost=LAYER_COST,rail_nets=RAILS,clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=case['bounds_mm'],fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs('osc-jack-right'))
  assert not removed
  rows,_=copper_rows(paths,'osc-jack-right','issue189-jr-shared-via-'+label+'-'+domain);complete=bool(rows) and bool(paths) and all(r['path'] for r in paths)
  result['cases'].append(dict(exclusion=label,domain=domain,search_only_keepouts=new,elapsed_seconds=time.monotonic()-start,complete=complete,diagnostics=events,routes=paths,proposal=dict(board_sha256=sha(board),removed_uuids=[],copper=rows)))
  (HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(label,domain,complete,len(rows),flush=True)
assert sha(board)==d['board_sha256']
result['status']='COMPLETE BOUNDED SEARCH; NATIVE NOT RUN';(HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
