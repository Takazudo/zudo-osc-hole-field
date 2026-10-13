#!/usr/bin/env python3
"""Post-hoc node-level KCL audit of the reductions and of every published coupled state (source-only).

For each board/net/case reduction: the load-solve residual r = A u0 - f at every free node,
reported three ways: relative to the largest injected node current (the declared 1e-9
criterion), relative to each row's own current magnitude sum_j |A_ij u0_j| + |f_i|, and as
the normwise backward error ||r|| / (||A|| ||u0|| + ||f||). The per-row roundoff floor
eps * sum_j |A_ij u0_j| is reported so a residual at that floor is distinguishable from
an inaccurate solve.
"""
import argparse,glob,hashlib,json,os,sys
from pathlib import Path
import numpy as np
import finite_solve as S,finite_units as U
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--coupled',type=Path,required=True);p.add_argument('--finite',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if os.environ.get('E16_VERIFY_SCOPE')!='1':
  os.environ['E16_VERIFY_SCOPE']='1'
  os.execvp('systemd-run',['systemd-run','--user','--scope','-q','-p',f'MemoryMax={U.LIMIT}','-p','MemorySwapMax=0',sys.executable,os.path.abspath(__file__)]+sys.argv[1:])
 here=Path(__file__).resolve().parent;cfg=U.jload(here/'evidence/e16/coupled-network-config.json');cases=U.jload(here/'evidence/e16/process-cases.json')['cases'];rows=[]
 for f in sorted(glob.glob(str(a.coupled/'K?-red-*.pkl.gz'))):
  r=U.pload(f);ops=U.pload(a.finite/r['board']/f"operator-{r['net']}.pkl.gz")
  Af,_,_,free,pos,fixed,terms,src,_,_=S.board_parts(ops,cases[r['case']],cfg['depth_cases'][r['depth']],cfg,r['board'],r['net'],release=True)
  b=np.zeros(ops['N'])
  for pid,(I,_) in r['loads'].items():
   if pid in {u['pad_id'] for u in r['unserved_loads']}:continue
   n,w=ops['supports'][pid];b[n]-=I*w
  b=b[free];u=r['u0'];res=Af@u-b;row=abs(Af)@abs(u)+abs(b);eps=np.finfo(float).eps
  rows.append({'board':r['board'],'net':r['net'],'case':r['case'],'depth':r['depth'],
   'residual_rel_max_load':float(np.max(abs(res))/max(np.max(abs(b)),1e-300)),
   'residual_rel_row_magnitude':float(np.max(abs(res)/np.maximum(row,1e-300))),
   'normwise_backward_error':float(np.max(abs(res))/(float(np.max(abs(Af).sum(axis=1)))*float(np.max(abs(u)))+float(np.max(abs(b))))),
   'max_row_current_magnitude_A':float(np.max(row)),'roundoff_floor_rel_max_load':float(eps*np.max(row)/max(np.max(abs(b)),1e-300)),
   'max_abs_matrix_entry_S':float(abs(Af).max())})
  del ops,Af
 # Published coupled states: rebuild v = u0 - Y v_t from the reductions and the interface solve, then the
 # full board residual (copper + termination stamps) and its evaluation floor, for every return state.
 states=[];eps=np.finfo(float).eps;Rt=cfg['wires']['termination_per_end_ohm'];Rw=cfg['wires']['bulk_ohm']
 for f in sorted(glob.glob(str(a.coupled/'coupled-*.json.gz'))):
  res=U.jload(f);net,case,depth=res['net'],res['case'],res['depth'];tag=f'{net}-{case}-{depth}'
  rA,rB=U.pload(a.coupled/f'KA-red-{tag}.pkl.gz'),U.pload(a.coupled/f'KB-red-{tag}.pkl.gz')
  sols={}
  for name,st in res['states'].items():
   removed={int(w[1:]) for w in st['removed_wires']};G,wires=S.small_system(rA,rB,cfg,removed);k=len(wires)
   sols[name]=np.linalg.solve(G,np.concatenate([-rA['g'],-rB['g']]))
  for blk,(tagb,red) in enumerate((('KA',rA),('KB',rB))):
   ops=U.pload(a.finite/tagb/f'operator-{net}.pkl.gz');K,_,_=S.A.laplacian(ops['Kg_face'],ops['Kg_inner'],ops['barrels'],ops['rings'],cases[case],cfg['depth_cases'][depth])
   terms,_,sup=S.terminal_stamps(ops,cfg);N=red['N'];fvec=np.zeros(N);served=set(red['loads'])-{u['pad_id'] for u in red['unserved_loads']}
   for pid in served:n,w=ops['supports'][pid];fvec[n]-=red['loads'][pid][0]*w
   absK=abs(K)
   for name,vt in sols.items():
    k=len(terms);v_t=vt[:k] if blk==0 else vt[k:];vm=S.reconstruct_potential(red,v_t)
    inj,_=S.apply_board(K,sup,Rt,vm,v_t);r=(inj-fvec)[red['free']];mag=(absK@abs(vm))
    for n,w in sup:mag[n]+=abs(w)*abs(w@vm[n])/Rt
    mag=mag[red['free']]+abs(fvec[red['free']]);scale=max(float(np.max(abs(fvec))),1e-300)
    states.append({'net':net,'case':case,'depth':depth,'state':name,'board':tagb,'residual_rel_max_load':float(np.max(abs(r)))/scale,
                   'residual_rel_row_magnitude':float(np.max(abs(r)/np.maximum(mag,1e-300))),'roundoff_floor_rel_max_load':float(eps*np.max(mag))/scale,
                   'rows_above_10x_floor':int(np.sum(abs(r)>10*eps*np.maximum(mag,1e-300)))})
   del ops,K,absK
 bind={'reductions':{Path(f).name:sha(f) for f in sorted(glob.glob(str(a.coupled/'K?-red-*.pkl.gz')))},'coupled':{Path(f).name:sha(f) for f in sorted(glob.glob(str(a.coupled/'coupled-*.json.gz')))},
       'operators':{f'{b}/{Path(f).name}':sha(f) for b in ('KA','KB') for f in sorted(glob.glob(str(a.finite/b/'operator-*.pkl.gz')))},'method':{m:sha(here/m) for m in ['verify_kcl.py','finite_solve.py','finite_adapter.py']}}
 a.output.write_text(json.dumps({'schema':'e16-node-kcl-audit-v2','declared_tolerance':cfg['numerical_tolerances']['kcl_relative'],'reductions':rows,'coupled_states':states,'bindings':bind},indent=1)+'\n')
 print(json.dumps({'reductions':len(rows),'coupled_states':len(states),'max_coupled_rel_max_load':max(x['residual_rel_max_load'] for x in states),'rows_above_10x_floor':sum(x['rows_above_10x_floor'] for x in states)}))
if __name__=='__main__':main()
