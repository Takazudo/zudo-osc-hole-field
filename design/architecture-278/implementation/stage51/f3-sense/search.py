"""Bounded additive search for one F3 sense-net island; no rip-up."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
BASE='05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441'
NET='XED7C19D453619667580D';SOURCE='3921a7e7-bdde-5afd-9636-95804e2a2928'
def run(dump_path,output,mode):
 d=json.loads(dump_path.read_text())
 if d['board_sha256']!=BASE or d['open_edges']!=116 or sorted(map(len,d['islands'][NET]))!=[1,50] or [SOURCE] not in d['islands'][NET]:raise ValueError('baseline/partition')
 layers=['B.Cu'] if mode=='back' else ['F.Cu','In2.Cu','In3.Cu','B.Cu']
 params=dict(res=.1,clearance=.2,signal_width=.2,via_diameter=.6,via_drill=.3,hole_clearance=.25,edge_clearance=.5,grow={'AGND':.05,'+12V':.05,'-12V':.05,'+5V':.05},allowed_layers=layers,max_expansions=1000000,bounds_mm=[222,90,244,118],window_mm=25,via_cost=60)
 if mode in ('wide','fine'):
  params['bounds_mm']=[205,72,246,120]
 if mode=='fine':params['res']=.05
 diagnostics=[]
 results,removed=route(d,[NET],diagnostics=diagnostics,**params)
 if removed:raise ValueError('unexpected retirement')
 rows,links=copper_rows(results,'osc-jack-left','stage51-f3-'+mode)
 evidence=dict(mode=mode,parameters=params,dump_sha256=hashlib.sha256(dump_path.read_bytes()).hexdigest(),results=results,links=links,diagnostics=diagnostics,failed_links=sum(not x['path'] for x in results))
 output.with_suffix('.search.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
 output.write_text(json.dumps(dict(board_sha256=BASE,removed_uuids=[],copper=rows),indent=2,sort_keys=True)+'\n')
 print(json.dumps({'mode':mode,'objects':len(rows),'failed_links':evidence['failed_links']}))
 return evidence['failed_links']
if __name__=='__main__':sys.exit(run(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3]))
