"""Widen the escape to two verified existing main-ground vias; preserve obstacles."""
from pathlib import Path
import copy,json,sys
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
BASE_HASH='d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'
SOURCE='b9d402b4-b8c4-5ab2-a8c0-3fd450c4809c'
DESTINATIONS=['a6b5c1e1-3b03-53c1-aff3-69160966559d','763aee4d-42eb-57c6-b00b-a5415564f1de']

def propose(dump_path,output):
 d=json.loads(dump_path.read_text());groups=d['islands']['AGND']
 if d['board_sha256']!=BASE_HASH or not any(g==[SOURCE] for g in groups):raise ValueError('baseline/source')
 if not any(all(v in g for v in DESTINATIONS) for g in groups):raise ValueError('destinations not same ground component')
 d=copy.deepcopy(d);d['islands']['AGND']=[[SOURCE],DESTINATIONS]
 results,removed=route(d,['AGND'],res=.05,clearance=.25,rail_nets=['AGND'],rail_width=.4,signal_width=.2,via_diameter=.7,via_drill=.3,allowed_layers=['F.Cu','In2.Cu','B.Cu'],max_expansions=1000000,bounds_mm=[263,125,276,139],window_mm=15,log=lambda s:print(s,flush=True))
 if removed:raise ValueError('unexpected retirement')
 rows,links=copper_rows(results,'osc-jack-left','stage46-ground-corridor')
 output.write_text(json.dumps({'board_sha256':BASE_HASH,'removed_uuids':[],'copper':rows},indent=2)+'\n')
 output.with_name('corridor-search.json').write_text(json.dumps({'source':SOURCE,'destinations':DESTINATIONS,'bounds_native_mm':[263,125,276,139],'results':results,'links':links,'failed_links':sum(not r['path'] for r in results)},indent=2)+'\n')
 if any(not r['path'] for r in results):raise SystemExit(1)
if __name__=='__main__':propose(Path(sys.argv[1]),Path(sys.argv[2]))
