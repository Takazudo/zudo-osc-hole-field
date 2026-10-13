#!/usr/bin/env python3
"""Coupled KA-KB finite network of one net: sequential board reduction, interface solve, back-substitution.

  reduce  one board/net/process case: factor the board alone (sources held, terminals
          as interface nodes behind their finite termination supports), eliminate the
          copper onto the terminal nodes (Schur complement S, load term g) and keep
          what back-substitution needs; also unit-current driving-point data per pad.
  couple  join KA and KB through each live wire's bulk once; solve every declared
          return state on the small interface system; back-substitute pad potentials,
          wire/source currents, conductor-class Joule energy and KCL residuals.

Each wire's bulk is charged once and each end's termination once, on its own board.
Only the KA source supports are held; KB floats on its wires. No ideal edge is added.
"""
import argparse,gc,gzip,hashlib,json,os,pickle,resource,sys,time
for _v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ.setdefault(_v,'1')
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
HERE=Path(__file__).resolve().parent
import finite_adapter as A
from finite_units import jload,psave,pload,sha,need,LIMIT
BATCH=16
def wire_of(t):return int(t.rsplit('-W',1)[1])
def injected(cfg,ledger,board,net,service):
 """Signed pad currents of the declared scenario that the solver injects; everything else is reported, not injected."""
 need(service is not None and service.get('scenario_id')==cfg['scenario']['id'],'explicit scenario device service is required')
 eligible=set(service['device_service']['eligible_pad_ids'])
 sc=cfg['scenario']['id'];out={};skipped=[]
 for r in ledger['records']:
  if r['scenario_id']!=sc or r['board']!=board or r['net']!=net:continue
  if r['pad_id'] in eligible and r['provenance'] in ('supported_pin_current','conditional_assumption') and r['current_A'] is not None:
   need(r['pad_id'] not in out,'duplicate ledger current on one pad: '+r['pad_id']);out[r['pad_id']]=(float(r['current_A']),r['provenance'])
  elif r['current_A'] not in (None,0,0.):skipped.append(r['pad_id'])
 return out,skipped
def ledger_binding(cfg,ledger):
 content=hashlib.sha256(json.dumps({k:ledger[k] for k in ('records','interface_demands','allowances')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 need(content==ledger['ledger_sha256']==cfg['scenario']['ledger_sha256'],'ledger content hash differs from its declared or configured hash')
def service_manifest(config,ledger_path,coverage_paths):
 """Content-bound all-board/all-net coverage and complete-device load eligibility."""
 import load_ledger as LL
 cfg=jload(config);ledger=jload(ledger_path);ledger_binding(cfg,ledger)
 expected={(b,n) for b in LL.BOARDS for n in LL.NETS};bindings={};served=set()
 scenario=cfg['scenario']['id'];rows=[r for r in ledger['records'] if r['scenario_id']==scenario]
 by_id={r['pad_id']:r for r in rows};known=set(by_id);seen=set()
 need(len(by_id)==len(rows),'duplicate ledger pad records in service scenario')
 need(len(coverage_paths)==len(expected),'service requires all eight KA/KB board/net coverage files')
 for path in coverage_paths:
  cov=jload(path);key=(cov['board'],cov['net']);need(key in expected and key not in seen,'duplicate or unknown board/net coverage')
  seen.add(key);ids=[r['pad_id'] for r in cov['rows']]
  need(cov['ports']==len(ids) and len(ids)==len(set(ids)),'coverage pad census differs or duplicates')
  need(cov['terminals_covered'] is True and cov['obligated_without_finite_path']==[] and cov['floating_finite_components']==[],'finite coverage is incomplete')
  local={r['pad_id']:r for r in cov['rows']}
  need(all(r['pad_id'] in local for r in rows if (r['board'],r['net'])==key),'coverage omits a ledger pad')
  for row in cov['rows']:
   need(isinstance(row['finite_path_to_feed'],bool),'coverage path flag must be boolean')
   need(not row['obligated'] or row['finite_path_to_feed'],'obligated pad has no finite path')
   need(not row['finite_path_to_feed'] or row['support_nodes']>0,'served pad has no finite support')
   if row['pad_id'] in known:
    record=by_id[row['pad_id']]
    need((record['board'],record['net'])==key,'coverage assigns a ledger pad to another board/net')
    if row['finite_path_to_feed']:served.add(row['pad_id'])
  bindings[key[0]+'|'+key[1]]={'path':str(Path(path).resolve()),'sha256':sha(path),'desc_sha256':cov['desc_sha256']}
 need(seen==expected,'service requires all eight KA/KB board/net coverages')
 service=LL.device_service(ledger,scenario,served)
 need(abs(service['included_global_residual_A'])<=LL.TOL,'complete-device service has nonzero signed current residual')
 out={'schema':'e16-device-service-v1','scenario_id':scenario,'ledger_sha256':ledger['ledger_sha256'],
  'bindings':{'config':sha(config),'ledger':sha(ledger_path),'coverage':bindings,
   'methods':{m:sha(HERE/m) for m in ('finite_solve.py','load_ledger.py')}},'device_service':service}
 out['service_sha256']=hashlib.sha256(LL.canon(out).encode()).hexdigest()
 return out
def create_service(a):
 manifest=service_manifest(a.config,a.ledger,a.coverage)
 Path(a.output).write_text(json.dumps(manifest,sort_keys=True,indent=1)+'\n')
 return {'scenario_id':manifest['scenario_id'],'service_sha256':manifest['service_sha256'],'summary':manifest['device_service']['summary'],
  'eligible_pads':len(manifest['device_service']['eligible_pad_ids']),'included_global_residual_A':manifest['device_service']['included_global_residual_A']}
def validate_service(service_path,config,ledger_path,coverage,board,net,operator):
 """Recompute eligibility from the eight bound coverage files; local coverage cannot drift."""
 manifest=jload(service_path)
 need(manifest.get('schema')=='e16-device-service-v1','missing complete-device service manifest')
 paths=[b['path'] for b in manifest['bindings']['coverage'].values()]
 expected=service_manifest(config,ledger_path,paths)
 need(manifest==expected,'service manifest differs from bound ledger, coverage, configuration or methods')
 local=manifest['bindings']['coverage'][board+'|'+net]
 need(local['sha256']==sha(coverage),'local coverage differs from complete-device service')
 need(local['desc_sha256']==operator['desc_sha256'],'operator differs from complete-device service')
 return manifest

REFINE_STEPS=3
def _extended_residual(Af,x,b):
 """Evaluate b-Ax with extended products/sums, using bounded sparse-entry scratch.

 Keep the original matrix and float64 solution: no coefficient, topology, load or
 tolerance changes. One long-double node vector is used per RHS; no full extended
 copy of the matrix or of a multi-RHS solution is allocated.
 """
 if np.finfo(np.longdouble).eps>=np.finfo(np.float64).eps:
  raise RuntimeError('extended-precision residual requires wider-than-float64 longdouble')
 if Af.format not in ('csr','csc'):
  raise ValueError('refinement requires CSR or CSC sparse storage')
 xx=np.asarray(x);bb=np.asarray(b);vector=bb.ndim==1
 if vector:xx=xx[:,None];bb=bb[:,None]
 residual=np.empty(bb.shape,dtype=np.float64)
 for j in range(bb.shape[1]):
  rr=bb[:,j].astype(np.longdouble)
  for lo in range(0,len(Af.data),65536):
   hi=min(lo+65536,len(Af.data))
   major=np.searchsorted(Af.indptr,np.arange(lo,hi),side='right')-1
   minor=Af.indices[lo:hi]
   row,col=(minor,major) if Af.format=='csc' else (major,minor)
   product=Af.data[lo:hi].astype(np.longdouble)*xx[col,j].astype(np.longdouble)
   np.add.at(rr,row,-product)
  residual[:,j]=rr
 return residual[:,0] if vector else residual

def refined_solve(lu,Af,b):
 """Bounded mixed-precision refinement with the unchanged load-relative criterion.

 Float64 sparse residuals can lose small injection currents to cancellation in
 conductive rows. Evaluate them in extended precision, solve each correction with
 the existing LU, and retain the best of the initial plus three corrected iterates.
 A reported residual above the declared threshold remains a failure. This helper
 does not replace the independent full coupled node-KCL and energy audits.
 """
 x=lu.solve(b);scale=max(float(np.max(abs(b))),1e-300)
 r=_extended_residual(Af,x,b);best=x.copy();worst=float(np.max(abs(r)))/scale
 for _ in range(REFINE_STEPS):
  x=x+lu.solve(r);r=_extended_residual(Af,x,b)
  score=float(np.max(abs(r)))/scale
  if score<worst:best=x.copy();worst=score
 return best,worst
def terminal_stamps(ops,cfg):
 """Each feed termination: rank-1 distributed conductance w w'/Rt between its pad support and its terminal node."""
 terms=sorted(ops['terminals'],key=wire_of);Rt=cfg['wires']['termination_per_end_ohm']
 return terms,Rt,[ops['supports'][t] for t in terms]
def held_nodes(ops,cfg,board,net):
 fixed=np.zeros(ops['N'],bool);src=[]
 if board==cfg['source_support']['board']:
  for p in cfg['source_support']['pads'][net]:
   need(p['pad_id'] in ops['supports'],'source support pad has no finite support: '+p['ref'])
   n=ops['supports'][p['pad_id']][0][ops['support_inside'][p['pad_id']]];need(len(n)>=3,'source land has no interior mesh nodes: '+p['ref'])
   fixed[n]=True;src.append(p['pad_id'])
 return fixed,src
def board_parts(ops,case,depth,cfg,board,net,release=False):
 """Factor block A over free mesh nodes, dense coupling B (free x terminals), D (terminals), without forming M.

 With release=True the operator's class matrices are dropped once K is built (peak memory before factorisation)."""
 K,Kb,records=A.laplacian(ops['Kg_face'],ops['Kg_inner'],ops['barrels'],ops['rings'],case,depth)
 if release:ops.pop('Kg_face');ops.pop('Kg_inner');del Kb;gc.collect();Kb=None
 N=ops['N'];terms,Rt,sup=terminal_stamps(ops,cfg);T=len(terms);fixed,src=held_nodes(ops,cfg,board,net)
 free=np.flatnonzero(~fixed);pos=-np.ones(N,np.int64);pos[free]=np.arange(len(free))
 coo=K.tocoo();del K;gc.collect()
 keep=(pos[coo.row]>=0)&(pos[coo.col]>=0)
 rows=[pos[coo.row[keep]]];cols=[pos[coo.col[keep]]];vals=[coo.data[keep]];del coo,keep
 B=np.zeros((len(free),T));D=np.zeros((T,T))
 for k,(n,w) in enumerate(sup):
  m=pos[n]>=0;nn,ww=pos[n[m]],w[m]
  rows.append(np.repeat(nn,len(nn)));cols.append(np.tile(nn,len(nn)));vals.append(np.outer(ww,ww).ravel()/Rt)
  B[nn,k]-=ww/Rt;D[k,k]+=1/Rt
 Af=sp.csc_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(len(free),len(free)));del rows,cols,vals;gc.collect()
 return Af,B,D,free,pos,fixed,terms,src,records,Kb
def apply_board(K,sup,Rt,vm,vt):
 """(mesh injection, terminal injection) = M [vm; vt] for one board, by operator application."""
 inj=K@vm;tin=np.zeros(len(sup))
 for k,(n,w) in enumerate(sup):
  d=(w@vm[n]-vt[k])/Rt;inj[n]+=w*d;tin[k]=-d
 return inj,tin
def full_matrix(ops,case,depth,cfg,board,net):
 """Explicit [mesh | terminal] matrix and held mask; for small reference problems only."""
 K,_,_=A.laplacian(ops['Kg_face'],ops['Kg_inner'],ops['barrels'],ops['rings'],case,depth);N=ops['N'];terms,Rt,sup=terminal_stamps(ops,cfg);T=len(terms)
 M=sp.lil_matrix(sp.bmat([[K,None],[None,sp.csr_matrix((T,T))]]))
 for k,(n,w) in enumerate(sup):
  for i,wi in zip(n,w):
   for j,wj in zip(n,w):M[i,j]+=wi*wj/Rt
   M[i,N+k]-=wi/Rt;M[N+k,i]-=wi/Rt
  M[N+k,N+k]+=1/Rt
 return M.tocsr(),held_nodes(ops,cfg,board,net)[0],terms
def factor_board(a):
 cfg=jload(a.config);case=jload(a.cases)['cases'][a.case];depth=cfg['depth_cases'][a.depth];ops=pload(a.operator);cov=jload(a.coverage)
 need(cov['desc_sha256']==ops['desc_sha256'],'coverage and operator from different descriptions')
 Af,Bf,D,free,pos,fixed,terms,src,records,_=board_parts(ops,case,depth,cfg,a.board,a.net,release=True)
 covered={r['pad_id'] for r in cov['rows'] if r['finite_path_to_feed']}
 pads=sorted(p for p in covered if p in ops['supports'] and p not in terms and p not in src)
 lu=spla.splu(Af,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0.,options=dict(SymmetricMode=True))
 return ops,free,pos,Bf,pads,lu,Af
def dpoint(a):
 """Unit-current driving-point data e_p = w_p' A^-1 w_p and q_p = B' A^-1 w_p for pads[start:stop]."""
 ops,free,pos,Bf,pads,lu,Af=factor_board(a);sel=pads[a.start:a.stop];e=np.zeros(len(sel));q=np.zeros((Bf.shape[1],len(sel)));worst=0.
 for k in range(0,len(sel),BATCH):
  chunk=sel[k:k+BATCH];Wb=np.zeros((len(free),len(chunk)))
  for j,p in enumerate(chunk):
   n,w=ops['supports'][p];need((pos[n]>=0).all(),'pad support touches a held source node: '+p);Wb[pos[n],j]=w
  U,res=refined_solve(lu,Af,Wb);worst=max(worst,res);e[k:k+len(chunk)]=np.sum(Wb*U,axis=0);q[:,k:k+len(chunk)]=Bf.T@U
 psave(a.output,{'board':a.board,'net':a.net,'case':a.case,'depth':a.depth,'pads':sel,'e':e,'q':q,'operator':sha(a.operator),'bindings':{'config':sha(a.config),'cases':sha(a.cases),'method':sha(Path(__file__))},'solve_residual_relative':worst})
 return {'board':a.board,'net':a.net,'pads':len(sel),'solve_residual_relative':worst}
def reduce(a):
 cfg=jload(a.config);case=jload(a.cases)['cases'][a.case];depth=cfg['depth_cases'][a.depth];ops=pload(a.operator);cov=jload(a.coverage);ledger=jload(a.ledger)
 need(cov['desc_sha256']==ops['desc_sha256'],'coverage and operator from different descriptions')
 ledger_binding(cfg,ledger)
 service=validate_service(a.service,a.config,a.ledger,a.coverage,a.board,a.net,ops)
 Af,Bf,D,free,pos,fixed,terms,src,records,_=board_parts(ops,case,depth,cfg,a.board,a.net,release=True);N=ops['N'];T=len(terms)
 covered={r['pad_id'] for r in cov['rows'] if r['finite_path_to_feed']}
 loads,skipped=injected(cfg,ledger,a.board,a.net,service);f=np.zeros(N);unserved=[]
 for pid,(I,prov) in sorted(loads.items()):
  need(pid in covered and pid in ops['supports'],'eligible complete-device load has no local finite support: '+pid)
  n,w=ops['supports'][pid];need(not fixed[n].any(),'load on a held source support: '+pid);f[n]-=I*w
 t0=time.monotonic();lu=spla.splu(Af,permc_spec='MMD_AT_PLUS_A',diag_pivot_thresh=0.,options=dict(SymmetricMode=True));tf=time.monotonic()-t0
 Y,resY=refined_solve(lu,Af,Bf) if T else (np.zeros((len(free),0)),0.);S=D-Bf.T@Y
 u0,res=refined_solve(lu,Af,f[free]) if f.any() else (np.zeros(len(free)),0.);g=Bf.T@u0
 pads=sorted(p for p in covered if p in ops['supports'] and p not in terms and p not in src)
 Wr,Wc,Wv=[],[],[]
 for j,p in enumerate(pads):
  n,w=ops['supports'][p];keep=pos[n]>=0;need(keep.all(),'pad support touches a held source node: '+p);Wr+=list(pos[n]);Wc+=[j]*len(n);Wv+=list(w)
 W=sp.csc_matrix((Wv,(Wr,Wc)),shape=(len(free),len(pads)))
 P0=W.T@u0;PY=(W.T@Y) if T else np.zeros((len(pads),0))
 Wb=W[:,:BATCH].toarray();U,_=refined_solve(lu,Af,Wb);E=Wb.T@U;recip=float(np.max(abs(E-E.T))/max(np.max(abs(E)),1e-30)) if len(pads) else 0.
 out={'board':a.board,'net':a.net,'case':a.case,'depth':a.depth,'N':N,'free':free,'terms':terms,'S':S,'g':g,'Y':Y,'u0':u0,'pads':pads,'P0':P0,'PY':PY,
      'loads':{p:v for p,v in loads.items()},'device_service_summary':service['device_service']['summary'],'service_excluded_pad_ids':service['device_service']['excluded_pad_ids'],'unserved_loads':unserved,'nonzero_not_injected':skipped,'source_pads':src,
      'checks':{'reciprocity_relative':recip,'load_solve_residual_relative':res,'interface_solve_residual_relative':resY,'refinement_steps':REFINE_STEPS,'factor_seconds':round(tf,2),'L_U_nnz':int(lu.L.nnz+lu.U.nnz)},
      'barrel_intervals':len(records),'bindings':{'operator':sha(a.operator),'coverage':sha(a.coverage),'ledger':sha(a.ledger),'service':sha(a.service),'config':sha(a.config),'cases':sha(a.cases),'method':sha(Path(__file__))}}
 psave(a.output,out)
 return {k:out[k] for k in ['board','net','case','depth','N']}|{'pads':len(pads),'loads':len(loads),'unserved':len(unserved),'checks':out['checks']}
def small_system(rA,rB,cfg,removed,bulk=None):
 """Interface matrix over [KA terminals | KB terminals] with each live wire bulk once."""
 tA,tB=[wire_of(t) for t in rA['terms']],[wire_of(t) for t in rB['terms']];need(tA==tB,'KA/KB terminal identities differ')
 k=len(tA);G=np.zeros((2*k,2*k));G[:k,:k]=rA['S'];G[k:,k:]=rB['S']
 for i,w in enumerate(tA):
  if w in removed:continue
  gw=1/(bulk or cfg['wires']['bulk_ohm']);G[i,i]+=gw;G[k+i,k+i]+=gw;G[i,k+i]-=gw;G[k+i,i]-=gw
 return G,tA
def couple(a):
 cfg=jload(a.config);case=jload(a.cases)['cases'][a.case];depth=cfg['depth_cases'][a.depth]
 rA,rB=pload(a.ka_red),pload(a.kb_red)
 need(rA['net']==rB['net']==a.net and rA['case']==rB['case']==a.case and rA['depth']==rB['depth']==a.depth,'reductions of one net/case/depth')
 need(rA['bindings']['operator']==sha(a.ka_op) and rB['bindings']['operator']==sha(a.kb_op),'operators differ from the reduced ones')
 need(rA['bindings'].get('service') and rA['bindings']['service']==rB['bindings'].get('service'),'board reductions use different or missing complete-device service')
 need(all(red['bindings']['config']==sha(a.config) and red['bindings']['cases']==sha(a.cases) and red['bindings']['method']==sha(Path(__file__)) for red in (rA,rB)),'reduction configuration, cases or method differs from coupled inputs')
 Rt=cfg['wires']['termination_per_end_ohm'];Rw=cfg['wires']['bulk_ohm'];rs=cfg['return_states']
 states={'all-present':[]}
 if a.net=='AGND':
  for grp in ('single','double'):
   for r in rs[grp]:states['remove-'+'-'.join(f'W{w}' for w in r)]=r
 def gather(files,red,opfile):
  parts=[pload(f) for f in files];pads=[p for x in parts for p in x['pads']]
  need(all(x['operator']==sha(opfile) and x['case']==a.case and x['depth']==a.depth for x in parts),'driving-point chunk from another operator/case/depth')
  need(all(x.get('bindings',{}).get('config')==sha(a.config) and x.get('bindings',{}).get('cases')==sha(a.cases) and x.get('bindings',{}).get('method')==sha(Path(__file__)) for x in parts),'driving-point chunk configuration, cases or method differs from coupled inputs')
  need(pads==red['pads'],'driving-point chunks must cover every reduced pad exactly once, in order')
  return {'pads':pads,'e':np.concatenate([x['e'] for x in parts]) if parts else np.zeros(0),'q':np.concatenate([x['q'] for x in parts],axis=1) if parts else np.zeros((len(red['terms']),0)),
          'residual':max((x['solve_residual_relative'] for x in parts),default=0.)}
 dpA,dpB=gather(a.ka_dp,rA,a.ka_op),gather(a.kb_dp,rB,a.kb_op)
 # Interface solves for every state first (small), then each board once for all states.
 small={}
 for name,removed in states.items():
  G,wires=small_system(rA,rB,cfg,set(removed));k=len(wires);vt=np.linalg.solve(G,np.concatenate([-rA['g'],-rB['g']]))
  live=np.array([w not in removed for w in wires]);small[name]=(G,wires,k,vt,live,np.where(live,(vt[:k]-vt[k:])/Rw,0.))
 per={name:{} for name in states}
 for tag,red,opfile,blk in (('KA',rA,a.ka_op,0),('KB',rB,a.kb_op,1)):
  op=pload(opfile);K,Kb,_=A.laplacian(op['Kg_face'],op['Kg_inner'],op['barrels'],op['rings'],case,depth)
  terms,_,sup=terminal_stamps(op,cfg);fixed,_=held_nodes(op,cfg,tag,a.net);N=red['N']
  f=np.zeros(N);served=set(red['loads'])-{u['pad_id'] for u in red['unserved_loads']}
  for pid in served:n,w=op['supports'][pid];f[n]-=red['loads'][pid][0]*w
  rho=case['rho_ohm_mm'];cf,ci=case['outer_copper_mm']/rho,case['inner_copper_mm']/rho
  for name in states:
   G,wires,k,vt,live,iw=small[name];v_t=vt[:k] if blk==0 else vt[k:]
   vm=np.zeros(N);vm[red['free']]=red['u0']-red['Y']@v_t
   inj,tin=apply_board(K,sup,Rt,vm,v_t);res=inj-f
   freeres=float(np.max(abs(res[red['free']])))/max(float(np.max(abs(f))),1e-30) if f.any() else float(np.max(abs(res[red['free']])))
   E_term=float(sum((w@vm[n]-v_t[kk])**2/Rt for kk,(n,w) in enumerate(sup)))
   pv=red['P0']-red['PY']@v_t
   per[name][tag]={'pad_potential_V':dict(zip(red['pads'],map(float,pv))),'source_injection_A':float(res[fixed].sum()),'terminal_injection_A':list(map(float,tin)),
                   'load_injection_A':float(f.sum()),'kcl_free_relative':freeres,
                   'energy_W':{'face_copper':float(vm@(op['Kg_face']@vm))*cf,'inner_copper':float(vm@(op['Kg_inner']@vm))*ci,'barrels':float(vm@(Kb@vm)),'terminations':E_term},
                   'work_W':float(f@vm)}
  del op,K,Kb;gc.collect()
 results={}
 for name,removed in states.items():
  G,wires,k,vt,live,iw=small[name];boards=per[name]
  out={'removed_wires':[f'W{w}' for w in removed],'wire_current_A':{f'W{w}':float(i) for w,i in zip(wires,iw)}}
  E_wire=float(np.sum(iw**2)*Rw)
  # Global KCL: held source injection + every load injection = 0; wire current leaves KA and enters KB once.
  total_inj=boards['KA']['source_injection_A']+boards['KA']['load_injection_A']+boards['KB']['load_injection_A']
  scale=max(abs(boards['KA']['load_injection_A'])+abs(boards['KB']['load_injection_A']),1e-30)
  wire_balance=float(max(np.max(abs(np.asarray(boards['KA']['terminal_injection_A'])+iw)),np.max(abs(np.asarray(boards['KB']['terminal_injection_A'])-iw)))) if k else 0.
  E=sum(sum(b['energy_W'].values()) for b in boards.values())+E_wire;work=boards['KA']['work_W']+boards['KB']['work_W']
  out.update(boards=boards,energy_W=dict(wires_bulk=E_wire,total=E),checks={'global_kcl_relative':abs(total_inj)/scale,'wire_terminal_balance_A':wire_balance,
             'energy_minus_load_work_relative':abs(E-work)/max(abs(work),1e-30) if work else abs(E),'nonnegative_energy':all(x>=-1e-18 for b in boards.values() for x in b['energy_W'].values()) and E_wire>=0,
             'max_free_node_kcl_relative':max(b['kcl_free_relative'] for b in boards.values()),'driving_point_solve_residual':max(dpA['residual'],dpB['residual'])})
  # Unit-current driving point per pad (source to pad), and its copper share after removing wire and termination energy.
  dp={}
  for tag,red,blk,parts in (('KA',rA,slice(0,k),dpA),('KB',rB,slice(k,2*k),dpB)):
   if not parts['pads']:continue
   R=np.zeros((2*k,len(parts['pads'])));R[blk]=parts['q'];V=np.linalg.solve(G,R)
   rdp=parts['e']+np.sum(parts['q']*V[blk],axis=0);iwp=np.where(live[:,None],(V[:k]-V[k:])/Rw,0.)
   rcu=rdp-np.sum(iwp**2,axis=0)*(Rw+2*Rt)
   dp[tag]={'pads':parts['pads'],'R_driving_point_ohm':rdp.tolist(),'R_copper_ohm':rcu.tolist()}
  out['driving_point']=dp;results[name]=out
 # Sensitivity: all returns present with every wire at the 110 mm maximum cut.
 Rmax=cfg['wires']['bulk_ohm_max_cut'];G,wires=small_system(rA,rB,cfg,set(),Rmax);k=len(wires)
 vt=np.linalg.solve(G,np.concatenate([-rA['g'],-rB['g']]));sens={'bulk_ohm':Rmax,'wire_current_A':{f'W{w}':float(i) for w,i in zip(wires,(vt[:k]-vt[k:])/Rmax)}}
 for tag,red,v_t in (('KA',rA,vt[:k]),('KB',rB,vt[k:])):
  pv=red['P0']-red['PY']@v_t;j=int(np.argmax(abs(pv))) if len(pv) else None
  sens[tag]={'pad_id':red['pads'][j],'model_pad_potential_V':float(pv[j])} if j is not None else None
 served=lambda r:sorted(set(r['loads'])-{u['pad_id'] for u in r['unserved_loads']})
 res={'schema':'e16-coupled-net-result-v1','net':a.net,'wire_length_sensitivity_all_present':sens,'loaded_pads':served(rA)+served(rB),'case':a.case,'depth':a.depth,'states':results,
      'not_solved':{'all-three-open':'KB AGND has no conductor to the source: a floating network, no finite result'} if a.net=='AGND' else {},
      'bindings':{'ka_reduction':sha(a.ka_red),'kb_reduction':sha(a.kb_red),'ka_operator':sha(a.ka_op),'kb_operator':sha(a.kb_op),'config':sha(a.config),'service':rA['bindings']['service'],'method':sha(Path(__file__))},
      'unserved_loads':{'KA':rA['unserved_loads'],'KB':rB['unserved_loads']},'reduction_checks':{'KA':rA['checks'],'KB':rB['checks']}}
 Path(a.output).write_bytes(gzip.compress(json.dumps(res,sort_keys=True).encode(),mtime=0))
 return {'net':a.net,'case':a.case,'states':len(results),'checks':{n:r['checks'] for n,r in results.items()}}
SCOPE_ENV='E16_SOLVE_SCOPE'
def enter_memory_scope():
 """Run this CLI unit inside a 2 GiB, no-swap cgroup scope and prove the limits apply.

 SuperLU reserves address space by a fill-factor guess (zero-filled, mostly untouched),
 so an address-space rlimit rejects factorisations whose resident memory is ~1.2 GiB.
 The unit bound is therefore enforced on resident memory by the kernel instead."""
 if os.environ.get(SCOPE_ENV)!='1':
  os.environ[SCOPE_ENV]='1'
  os.execvp('systemd-run',['systemd-run','--user','--scope','-q','-p',f'MemoryMax={LIMIT}','-p','MemorySwapMax=0',sys.executable,os.path.abspath(__file__)]+sys.argv[1:])
 rel=Path('/proc/self/cgroup').read_text().strip().split('::',1)[1];cg=Path('/sys/fs/cgroup'+rel)
 need((cg/'memory.max').read_text().strip()==str(LIMIT) and (cg/'memory.swap.max').read_text().strip()=='0','not inside the 2 GiB no-swap memory scope: '+rel)
def main(argv=None):
 if argv is None:enter_memory_scope()
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='cmd',required=True)
 x=s.add_parser('service')
 for k in ['ledger','config','output']:x.add_argument('--'+k,required=True)
 x.add_argument('--coverage',nargs='+',required=True)
 x=s.add_parser('reduce')
 for k in ['operator','coverage','ledger','service','config','cases','case','depth','board','net','output']:x.add_argument('--'+k,required=True)
 x=s.add_parser('dpoint')
 for k in ['operator','coverage','config','cases','case','depth','board','net','output']:x.add_argument('--'+k,required=True)
 x.add_argument('--start',type=int,required=True);x.add_argument('--stop',type=int,required=True)
 x=s.add_parser('couple')
 for k in ['ka-red','kb-red','ka-op','kb-op','config','cases','case','depth','net','output']:x.add_argument('--'+k,required=True)
 x.add_argument('--ka-dp',nargs='*',default=[]);x.add_argument('--kb-dp',nargs='*',default=[])
 a=p.parse_args(argv);start=time.monotonic();r={'service':create_service,'reduce':reduce,'dpoint':dpoint,'couple':couple}[a.cmd](a)
 r.update(elapsed_seconds=round(time.monotonic()-start,2),peak_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss);print(json.dumps(r))
if __name__=='__main__':main()
