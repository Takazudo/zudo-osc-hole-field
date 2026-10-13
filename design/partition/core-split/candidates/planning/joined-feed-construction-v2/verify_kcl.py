#!/usr/bin/env python3
"""Post-hoc node-level KCL audit of the coupled reductions (source-only; no result is changed).

For each board/net/case reduction: the load-solve residual r = A u0 - f at every free node,
reported three ways: relative to the largest injected node current (the declared 1e-9
criterion), relative to each row's own current magnitude sum_j |A_ij u0_j| + |f_i|, and as
the normwise backward error ||r|| / (||A|| ||u0|| + ||f||). The per-row roundoff floor
eps * sum_j |A_ij u0_j| is reported so a residual at that floor is distinguishable from
an inaccurate solve.
"""
import argparse,glob,json,os,sys
from pathlib import Path
import numpy as np
import finite_solve as S,finite_units as U
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
 a.output.write_text(json.dumps({'schema':'e16-node-kcl-audit-v1','rows':rows},indent=1)+'\n');print(json.dumps(rows[:2]))
if __name__=='__main__':main()
