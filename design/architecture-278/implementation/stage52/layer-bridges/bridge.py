"""Bounded target-only bridge search between explicit screened candidate sites."""
from pathlib import Path
import copy,json,sys,uuid,hashlib
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).resolve().parent))
from scripts.pcbgen.grid_router import route,copper_rows
from sites import Screen,BASE,NET
from shapely.geometry import Point
SITES={'lower':[[227.948045,109.291186],[234.888909,104.511091]],'upper':[[234.885993,102.753381],[235.3,95.7]],'upper-mid':[[234.885993,102.753381],[235.122861,99.590073]],'upper-short':[[235.122861,99.590073],[235.3,95.7]],'lower-west':[[227.021175,105.635042],[234.888909,104.511091]],'upper-main':[[235.122861,99.590073],[235.3,95.7]],'upper-full-main':[[234.885993,102.753381],[235.3,95.7]]}
def uid(s):return str(uuid.uuid5(uuid.NAMESPACE_URL,'stage52/'+s))
def run(path,output,case,res):
 d=json.loads(path.read_text());screen=Screen(d);via=[];groups=[]
 for i,xy in enumerate(SITES[case]):
  existing=next((v for v in d['vias'] if v['net']==NET and v['xy']==[round(v*1e6) for v in xy]),None)
  if existing:
   groups.append(next(g for g in d['islands'][NET] if existing['uuid'] in g) if case.endswith('main') else [existing['uuid']]);continue
  margin,obstacle=screen.margin(Point(xy),.3,d['layers'],True)
  if margin<.005:raise ValueError('candidate via clearance: '+str((xy,margin,obstacle)))
  row=dict(kind='via',uuid=uid(case+str(i)),net=NET,at_nm=[round(v*1e6) for v in xy],diameter_nm=600000,drill_nm=300000);via.append(row)
  d['vias'].append(dict(uuid=row['uuid'],net=NET,xy=row['at_nm'],diameter=600000,drill=300000));groups.append([row['uuid']])
 d['islands'][NET]=groups
 params=dict(res=res,clearance=.2,signal_width=.2,via_diameter=.6,via_drill=.3,hole_clearance=.25,edge_clearance=.5,grow={'AGND':.05,'+12V':.05,'-12V':.05,'+5V':.05},allowed_layers=['F.Cu','In2.Cu','B.Cu'],max_expansions=1500000,bounds_mm=[222,92,242,114],window_mm=10,via_cost=60)
 diagnostics=[];results,removed=route(d,[NET],diagnostics=diagnostics,**params)
 if removed:raise ValueError('rip-up')
 rows,links=copper_rows(results,'osc-jack-left','stage52-'+case+'-'+str(res));result={'board_sha256':BASE,'removed_uuids':[],'copper':via+rows}
 output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');output.with_suffix('.search.json').write_text(json.dumps({'parameters':params,'sites':SITES[case],'results':results,'diagnostics':diagnostics,'synthetic_membership':'proposal endpoint seeds only, not native confirmation','dump_sha256':hashlib.sha256(path.read_bytes()).hexdigest()},indent=2,sort_keys=True)+'\n')
 failed=sum(not r['path'] for r in results);print(json.dumps({'objects':len(result['copper']),'failed':failed}));return failed
if __name__=='__main__':sys.exit(run(Path(sys.argv[1]),Path(sys.argv[2]),sys.argv[3],float(sys.argv[4])))
