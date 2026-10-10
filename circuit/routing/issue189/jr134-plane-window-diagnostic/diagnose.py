"""Read-only exact raster via-site counts; no search, cuts or rule relaxation."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
import numpy as np
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import Raster,island_mask,SQRT2
from scripts.pcbgen.route_jack_grid import RAILS
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('dump',type=Path);a=p.parse_args()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.dump)=='f885375bc4a8ac5cc0ca879f841a4d3768a560876e43c023e2abe14e38a86c8a'
router_sha=sha(ROOT/'scripts/pcbgen/grid_router.py')
d=json.loads(a.dump.read_text());board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(board)==d['board_sha256']
saved=HERE.parent/'jr134-paired-movement/route-result.json';prior=json.loads(saved.read_text())
cases=[r for r in prior['transactions'] if r['mode']=='plane' and any(e['reason']=='no_legal_via_site' for e in r['diagnostics'])]
cases=[dict(target=t,candidate_index=None,delta_mm={},virtual_proposal={'copper':[]}) for t in sorted({r['target'] for r in cases})]+cases
rows=[]
for case in cases:
 c=copy.deepcopy(d);ref=case['target'];pad=next(p for p in c['pads'] if p['ref']==ref and p['net']=='AGND');x,y=np.array(pad['xy'])/1e6
 for p in c['pads']:
  if p['ref'] in case['delta_mm']:
   shift=[round(v*1e6) for v in case['delta_mm'][p['ref']]]
   p['xy']=[v+s for v,s in zip(p['xy'],shift)];p['poly']=[[v+s for v,s in zip(pt,shift)] for pt in p['poly']]
 for b in case['virtual_proposal']['copper']:
  assert b['kind']=='segment';c['tracks'].append(dict(uuid=b['uuid'],net=b['net'],layer=b['layer'],a=b['start_nm'],b=b['end_nm'],width=b['width_nm']))
 res=.0125;ras=Raster(c,res,grow={n:.05 for n in RAILS+['AGND']},bounds_mm=[x-8,y-8,x+8,y+8]);src=island_mask(ras,c,[pad['uuid']]);N=ras.net_id['AGND'];margin=res/SQRT2+.01
 lo,hi=np.argwhere(src.any(0)).min(0),np.argwhere(src.any(0)).max(0);windows=[]
 for mm in (3,6):
  extra=round(mm/res);guard=round(1.5/res);y0,x0=np.maximum(0,lo-extra);y1,x1=np.minimum([ras.h,ras.w],hi+extra+1)
  g0,g1=max(0,y0-guard),min(ras.h,y1+guard);h0,h1=max(0,x0-guard),min(ras.w,x1+guard)
  inner=(slice(y0-g0,y1-g0),slice(x0-h0,x1-h0));win=(slice(y0,y1),slice(x0,x1))
  foreign=((ras.label[:,g0:g1,h0:h1]!=0)&(ras.label[:,g0:g1,h0:h1]!=N))|((ras.fixed_label[:,g0:g1,h0:h1]!=0)&(ras.fixed_label[:,g0:g1,h0:h1]!=N))
  tests=dict(copper=ndimage.distance_transform_edt(~foreign.any(0))[inner]*res>=.25+.3+margin,edge=ras.d_edge[win]>=.5+.3+margin,keepout=ras.d_keep_via[win]>=.3+margin,drill=ndimage.distance_transform_edt(~ras.hole[g0:g1,h0:h1])[inner]*res>=.3+.25+margin,smd=ras.d_smd[win]>=.3+margin)
  ok=np.logical_and.reduce(list(tests.values()));goal=np.zeros(ok.shape,bool)
  for lay in ('F.Cu','B.Cu'):
   li=ras.layers.index(lay);free=(ndimage.distance_transform_edt(~foreign[li])[inner]*res>=.25+.15+margin)&(ras.d_edge[win]>=.5+.15+margin)&(ras.d_keep_track[li][win]>=.15+margin)
   goal|=ok&free&~src[li][win]
  windows.append(dict(pad_window_mm=mm,via_sites=int(ok.sum()),goal_sites=int(goal.sum()),passing_individual_constraints={k:int(v.sum()) for k,v in tests.items()},sites_if_one_constraint_ignored_diagnostic_only={k:int(np.logical_and.reduce([v for key,v in tests.items() if key!=k]).sum()) for k in tests}))
 if case['candidate_index'] is not None:assert windows[0]['goal_sites']==0
 rows.append(dict(target=ref,candidate_index=case['candidate_index'],delta_mm=case['delta_mm'],windows=windows));print(ref,case['candidate_index'],[(w['pad_window_mm'],w['goal_sites']) for w in windows],flush=True)
assert sha(board)==d['board_sha256'] and sha(ROOT/'scripts/pcbgen/grid_router.py')==router_sha
(HERE/'result.json').write_text(json.dumps(dict(status='DIAGNOSTIC ONLY; NO RULE CHANGES OR ROUTES; NATIVE NOT RUN',board_sha256=sha(board),dump_sha256=sha(a.dump),saved_trials_sha256=sha(saved),router_sha256=sha(ROOT/'scripts/pcbgen/grid_router.py'),cases=rows),indent=2)+'\n')
