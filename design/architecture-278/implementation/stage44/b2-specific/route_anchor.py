"""Route the actual B2 +5V feed to its retained via on B.Cu.

Restrict only the destination subset of an existing native component; keep every
obstacle. Full native connectivity remains mandatory after applying the proposal.
"""
from pathlib import Path
import copy,json,sys
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
ANCHOR='06b2530e-ef31-5ad6-b94a-011fdc6dd3ee'
SOURCE='2b3a893d-37c2-5814-a10c-1bdaa3a4a2e7'

def propose(dump_path,output):
    original=json.loads(dump_path.read_text());d=copy.deepcopy(original)
    groups=d['islands'].get('+5V',[])
    if len(groups)!=2 or not any(ANCHOR in g for g in groups) or not any(g==[SOURCE] for g in groups):raise ValueError('unexpected native +5V partition')
    anchor=next(v for v in d['vias'] if v['uuid']==ANCHOR)
    if anchor['net']!='+5V' or anchor['xy']!=[157000000,205000000]:raise ValueError('anchor binding')
    d['islands']['+5V']=[[ANCHOR] if ANCHOR in g else g for g in groups]
    results,removed=route(d,['+5V'],res=.05,signal_width=.2,clearance=.25,allowed_layers=['B.Cu'],rail_nets=['+5V'],grow={'+12V':.05,'-12V':.05,'+5V':.05},via_diameter=.7,via_drill=.3,max_expansions=1000000,bounds_mm=[140.5,168,173,213.5],window_mm=12,log=lambda s:print(s,flush=True))
    if removed:raise ValueError('unexpected removal')
    rows,links=copper_rows(results,'osc-jack-left','stage44-real-anchor-feed')
    output.write_text(json.dumps({'board_sha256':d['board_sha256'],'removed_uuids':[],'copper':rows},indent=2)+'\n')
    output.with_name('anchor-search.json').write_text(json.dumps({'source_dump':str(dump_path),'baseline_islands':original['islands']['+5V'],'restricted_destination':[ANCHOR],'results':results,'links':links,'failed_links':sum(not r['path'] for r in results),'limits':'Destination subset restriction only; obstacles unchanged. Full native closure and retained partitions required.'},indent=2)+'\n')
    if any(not r['path'] for r in results):raise SystemExit(1)
if __name__=='__main__':propose(Path(sys.argv[1]),Path(sys.argv[2]))
