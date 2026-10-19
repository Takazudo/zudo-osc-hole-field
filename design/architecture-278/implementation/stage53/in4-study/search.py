"""Explicit continuous-screen escape plus bounded raster onward route; disposable."""
from pathlib import Path
import copy,hashlib,json,sys,uuid
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
BASE='05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441'
NET='XED7C19D453619667580D';SOURCE='3921a7e7-bdde-5afd-9636-95804e2a2928'
def uid(n):return str(uuid.uuid5(uuid.NAMESPACE_URL,'stage53-in4-seed/'+n))
def seed():
 via=[227980882,113013236]
 return [dict(kind='segment',uuid=uid('seed-track'),net=NET,layer='B.Cu',start_nm=[229010000,113390000],end_nm=via,width_nm=200000),dict(kind='via',uuid=uid('seed-via'),net=NET,at_nm=via,diameter_nm=600000,drill_nm=300000)]
def run(path,output,mode="coarse"):
 import importlib.util
 spec=importlib.util.spec_from_file_location('stage53_preflight',Path(__file__).with_name('preflight.py'));pf=importlib.util.module_from_spec(spec);spec.loader.exec_module(pf)
 if pf.run()!=json.loads(Path(__file__).with_name('preflight.json').read_text()):raise ValueError('preflight drift')
 if output.exists() or output.with_suffix('.search.json').exists():raise ValueError('refuse overwrite search')
 d=json.loads(path.read_text())
 if d['board_sha256']!=BASE or sorted(map(len,d['islands'][NET]))!=[1,50] or [SOURCE] not in d['islands'][NET]:raise ValueError('baseline')
 d=copy.deepcopy(d);rows=seed();t,v=rows
 d['tracks'].append(dict(uuid=t['uuid'],net=NET,a=t['start_nm'],b=t['end_nm'],width=t['width_nm'],layer=t['layer']))
 d['vias'].append(dict(uuid=v['uuid'],net=NET,xy=v['at_nm'],diameter=v['diameter_nm'],drill=v['drill_nm']))
 d['islands'][NET]=[g+[t['uuid'],v['uuid']] if g==[SOURCE] else g for g in d['islands'][NET]]
 params=dict(res=.1,clearance=.2,signal_width=.2,via_diameter=.6,via_drill=.3,hole_clearance=.25,edge_clearance=.5,grow={'AGND':.05,'+12V':.05,'-12V':.05,'+5V':.05},allowed_layers=['F.Cu','In2.Cu','In3.Cu','B.Cu'],max_expansions=1500000,bounds_mm=[205,72,246,120],window_mm=30,via_cost=60)
 params['allowed_layers']=['In4.Cu']
 if mode=='fine':params['res']=.05
 if mode not in ('coarse','fine'):raise ValueError('bounded mode')
 diagnostics=[];results,removed=route(d,[NET],diagnostics=diagnostics,**params)
 if removed:raise ValueError('retirement')
 additional,links=copper_rows(results,'osc-jack-left','stage53-in4-onward-'+mode)
 output.with_suffix('.search.json').write_text(json.dumps(dict(parameters=params,seed=rows,results=results,links=links,diagnostics=diagnostics,dump_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),synthetic_seed_membership='proposal only; requires native confirmation'),indent=2,sort_keys=True)+'\n')
 output.write_text(json.dumps(dict(board_sha256=BASE,removed_uuids=[],copper=rows+additional),indent=2,sort_keys=True)+'\n')
 failed=sum(not r['path'] for r in results);print(json.dumps({'objects':len(rows+additional),'failed_links':failed}));return failed
if __name__=='__main__':sys.exit(run(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3] if len(sys.argv)>3 else "coarse"))
