"""Additive ground fanout to In1.Cu, with native fill/partition acceptance required."""
from pathlib import Path
import copy,json,sys,argparse
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from route_corridor import BASE_HASH,SOURCE

def propose(dump_path,output,diameter):
 d=json.loads(dump_path.read_text())
 if d['board_sha256']!=BASE_HASH or not any(g==[SOURCE] for g in d['islands']['AGND']):raise ValueError('baseline/source')
 if diameter not in (.7,.6,.5):raise ValueError('unsupported via size')
 d=copy.deepcopy(d);d['islands']['AGND']=[[SOURCE]]
 results,removed=route(d,['AGND'],res=.05,clearance=.25,rail_nets=['AGND'],rail_width=.4,signal_width=.2,via_diameter=diameter,via_drill=.3,allowed_layers=['F.Cu','In1.Cu','In2.Cu','B.Cu'],planes={'AGND':'In1.Cu'},max_expansions=1000000,bounds_mm=[263,125,276,139],plane_window_mm=7,plane_max_expansions=1000000,log=lambda s:print(s,flush=True))
 if removed:raise ValueError('unexpected retirement')
 rows,links=copper_rows(results,'osc-jack-left','stage46-ground-plane-'+str(diameter),via_diameter=diameter,via_drill=.3)
 output.write_text(json.dumps({'board_sha256':BASE_HASH,'removed_uuids':[],'copper':rows},indent=2)+'\n')
 output.with_name(output.stem+'-search.json').write_text(json.dumps({'source':SOURCE,'via_diameter_mm':diameter,'drill_mm':.3,'clearance_mm':.25,'track_width_mm':.4,'results':results,'links':links,'failed_links':sum(not r['path'] for r in results),'limits':'In1.Cu target is a search goal, not a presumption of filled-plane connection; native validation is mandatory.'},indent=2)+'\n')
 if any(not r['path'] for r in results):raise SystemExit(1)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('dump',type=Path);p.add_argument('output',type=Path);p.add_argument('--diameter',type=float,required=True);a=p.parse_args();propose(a.dump,a.output,a.diameter)
