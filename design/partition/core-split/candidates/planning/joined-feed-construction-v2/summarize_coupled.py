#!/usr/bin/env python3
"""Index the coupled KA-KB results as the declared process-case x return-state matrix (source-only).

Rails do not depend on the AGND return state, so each matrix entry combines the rail
solutions of its process case with the AGND solution of its state. Per entry: pad
potentials, local-ground displacement, rail-minus-local-ground error of every rail pad
that belongs to a referenced part (loaded or not; the loaded subset is reported separately), wire/source currents, residuals, conductor-class energy, and the 20 mV /
1 mOhm / 0.5 mOhm requirements applied once over the modelled path. Neutral field
names; the 2026-10-13 partial-model fields stay in finite-network-t2.json as history.
"""
import argparse,gzip,json,math
from collections import defaultdict
from pathlib import Path
import numpy as np
import shapely
HERE=Path(__file__).resolve().parent
RAILS=['+12V','-12V','+5V']
def jl(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def local_ground(finite,boards=('KA','KB')):
 """ref -> AGND pad ids on its own footprint; pad -> centroid, for the nearest-AGND fallback."""
 own=defaultdict(list);centre={};refs={}
 for b in boards:
  g=jl(HERE/f'evidence/e16/{b}-t2-port-graph.json.gz')
  for p in g['physical_ports']:refs[p['id']]=(b,p.get('ref'),p['net'])
  for net in RAILS+['AGND']:
   desc=jl(Path(finite)/b/f'desc-{net}.json.gz')
   for pid,frs in desc['supports'].items():
    if frs:centre[pid]=shapely.union_all([shapely.from_wkb(f['wkb']) for f in frs]).centroid
 for pid,(b,ref,net) in refs.items():
  if net=='AGND' and ref:own[(b,ref)].append(pid)
 return own,centre,refs
def external_boundary(cov_rows):
 """Every inherited legacy harness / main conductor with a KA or KB end on a rail net, reconciled to the t2 census."""
 iface=jl(HERE.parents[2]/'power/joined/interfaces.json')['two'];by={}
 for b in ('KA','KB'):
  for q in jl(HERE/f'evidence/e16/{b}-t2-port-graph.json.gz')['physical_ports']:by[(b,q.get('ref'),q.get('pad'))]=q['id']
 covered={r['pad_id']:r for r in cov_rows};out=[]
 for kind,rows in (('legacy_harness',iface['legacy_conductors']),('existing_main',iface['existing_main_conductors'])):
  for c in rows:
   if c['net'] not in RAILS+['AGND']:continue
   for e in c['ends']:
    if e['board'] not in ('KA','KB'):continue
    pid=by.get((e['board'],e['ref'],e['pin']));r=covered.get(pid)
    out.append({'conductor':c['id'],'kind':kind,'net':c['net'],'board':e['board'],'ref':e['ref'],'pin':e['pin'],'pad_id':pid,
                'in_t2_census':pid is not None,'finite_path_to_feed':bool(r and r['finite_path_to_feed']),'structurally_unresolved':bool(r and r['structurally_unresolved'])})
 from collections import Counter
 summary=Counter((x['kind'],x['net'],x['board'],'in_census' if x['in_t2_census'] else 'NOT_IN_CENSUS','finite' if x['finite_path_to_feed'] else ('unresolved' if x['structurally_unresolved'] else 'no_path')) for x in out)
 return {'treatment':'No supported current operator exists for these conductors (GH returns, EL rail harnesses, JL/JR/P main branches). They are external boundaries of the KA-KB subnetwork: their current is not injected, and the 0.5 A GH conductor condition is NOT EVALUATED here. Patch sleeves are not counted as returns.',
         'counts':{'|'.join(k):v for k,v in sorted(summary.items())},'ends':out}
def main():
 p=argparse.ArgumentParser();p.add_argument('--coupled',type=Path,required=True);p.add_argument('--finite',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--config',type=Path,default=HERE/'evidence/e16/coupled-network-config.json');a=p.parse_args()
 cfg=jl(a.config);cases=list(jl(HERE/'evidence/e16/process-cases.json')['cases']);depth=cfg['default_depth_case'];B=cfg['budgets']
 own,centre,refs=local_ground(a.finite)
 res={};missing=[];trunk={}
 for net in RAILS+['AGND']:
  for c in cases:
   f=a.coupled/f'coupled-{net}-{c}-{depth}.json.gz'
   if f.exists():res[net,c]=jl(f)
   else:missing.append(f.name)
   ra=a.coupled/f'KA-red-{net}-{c}-{depth}.pkl.gz'
   if ra.exists():
    # KA copper from the held source lands to each feed terminal's support: driving point at the
    # terminal node with KB detached, minus the KA-side termination (ka_red S is the Schur complement there).
    import finite_units as U
    r=U.pload(ra);Sinv=np.linalg.inv(r['S']);Rt=cfg['wires']['termination_per_end_ohm']
    trunk[net,c]={t.rsplit('-',1)[1]:float(Sinv[i,i]-Rt) for i,t in enumerate(r['terms'])}
 states=['all-present']+['remove-'+'-'.join(f'W{w}' for w in r) for grp in ('single','double') for r in cfg['return_states'][grp]]
 matrix=[];
 for c in cases:
  for st in states:
   entry={'case':c,'depth':depth,'return_state':st,'scenario':cfg['scenario']['id']}
   if any((n,c) not in res for n in RAILS+['AGND']):entry['status']='NOT RUN';entry['reason']='coupled result missing: '+','.join(n for n in RAILS+['AGND'] if (n,c) not in res);matrix.append(entry);continue
   g=res['AGND',c]['states'][st]['boards'];agnd={b:g[b]['pad_potential_V'] for b in g}
   agnd_pads={b:[(pid,centre[pid]) for pid in agnd[b] if pid in centre] for b in agnd}
   errs=[];per_net={}
   for net in RAILS+['AGND']:
    r=res[net,c]['states']['all-present' if net!='AGND' else st];bd=r['boards']
    allv=[(b,pid,v) for b in bd for pid,v in bd[b]['pad_potential_V'].items()]
    worst=max(allv,key=lambda x:abs(x[2]))
    dp={b:r['driving_point'].get(b,{}) for b in bd}
    lim=B['agnd_copper_ohm'] if net=='AGND' else B['rail_copper_ohm']
    rcu=[(b,pid,x) for b in dp for pid,x in zip(dp[b].get('pads',[]),dp[b].get('R_copper_ohm',[]))]
    over=[(b,pid,x) for b,pid,x in rcu if x>lim]
    per_net[net]={'model_pad_potential_extreme_V':{'board':worst[0],'pad_id':worst[1],'value':worst[2]},'wire_current_A':r['wire_current_A'],
                  'source_current_A':bd['KA']['source_injection_A'],'checks':r['checks'],'energy_W':{**{f'{b}.{k}':v for b in bd for k,v in bd[b]['energy_W'].items()},**r['energy_W']},
                  'copper_resistance_requirement_ohm':lim,'max_model_copper_resistance_ohm':max((x for *_,x in rcu),default=None),
                  'min_model_copper_resistance_ohm':min((x for *_,x in rcu),default=None),'median_model_copper_resistance_ohm':float(np.median([x for *_,x in rcu])) if rcu else None,
                  'ka_trunk_copper_to_terminal_ohm':trunk.get((net,c)),
                  'pads_over_copper_requirement':len(over),'pads_evaluated':len(rcu)}
    if net in RAILS:
     for b in bd:
      for pid,v in bd[b]['pad_potential_V'].items():
       bb,ref,_=refs[pid]
       if not ref:continue
       gp=[q for q in own.get((b,ref),[]) if q in agnd[b]]
       if gp:vg=sum(agnd[b][q] for q in gp)/len(gp);basis='own AGND pad'
       elif agnd_pads[b] and pid in centre:
        q,_=min(agnd_pads[b],key=lambda t:t[1].distance(centre[pid]));vg=agnd[b][q];basis='nearest fed AGND pad '+q
       else:continue
       errs.append({'board':b,'pad_id':pid,'ref':ref,'net':net,'rail_V':v,'local_ground_V':vg,'error_V':v-vg,'additive_screen_V':abs(v)+abs(vg),'local_ground_basis':basis,
                    'loaded':pid in res[net,c]['loaded_pads']})
   worst=max(errs,key=lambda e:abs(e['error_V'])) if errs else None;ld=[e for e in errs if e['loaded']]
   entry.update(status='EXECUTED',nets=per_net,max_abs_rail_minus_local_ground_V=worst and abs(worst['error_V']),worst_pad=worst,
                pads_over_path_error_requirement=sum(abs(e['error_V'])>B['path_error_V'] for e in errs),pads_evaluated_for_path_error=len(errs),
                max_abs_error_loaded_pads_V=max((abs(e['error_V']) for e in ld),default=None),loaded_pads_evaluated=len(ld),
                max_additive_screen_V=max((e['additive_screen_V'] for e in errs),default=None),error_convention=cfg['error_convention'],
                gh_conductor_condition='NOT EVALUATED: no GH conductor or GH return current is in this KA-KB model')
   matrix.append(entry)
  matrix.append({'case':c,'depth':depth,'return_state':'all-three-open','status':'CLASSIFIED, NOT SOLVED',
                 'classification':'KB AGND has no conductor to the source: the KB AGND network floats and every KB load return is a fault path outside this model (external obligations: GH/harness returns, patch sleeves, earth).',
                 'external_fault_obligations':'#59 fault survival and the inherited 380 GH-return analysis remain separate obligations.'})
 cov_rows=jl(HERE/'evidence/e16/finite-coverage-t2-rows.json.gz')
 out={'schema':'e16-coupled-matrix-v1','external_boundary':external_boundary(cov_rows),'scope':'KA-KB subnetwork only: KA and KB core copper, CS247 W1-W6 bulk once, each termination once, conditional KA main-land source support. Excludes inlet/star/protection copper, JL/JR/P/EL branches, GH/harness and patch returns.',
      'scenario':cfg['scenario'],'process_cases':cases,'depth_case':depth,'return_states':states+['all-three-open'],'entries':matrix,'missing_results':missing,
      'budgets':B,'unserved_loads':{f'{n}|{c}':r['unserved_loads'] for (n,c),r in res.items()},
      'limits':['Conditional: process (foil, plating, rho), stack depths, wire/termination requirement values and the source support are declared assumptions, not qualified values.',
                'Loads: only datasheet-supported op-amp quiescent and conditional logic supply currents are injected; most fitted-IC supply current, all output/signal current and the EL demand are unmapped and not injected, so voltages are a lower-load study, not a worst case.',
                'A modelled value within a requirement is necessary, not sufficient: the unmodelled inlet/star/branch copper shares the same global allowance.',
                'P1 finite elements on the exact clipped copper; conforming discretisation tends to underestimate resistance; refinement and shifted-origin changes are reported separately.']}
 a.output.write_text(json.dumps(out,indent=1)+'\n')
 print(json.dumps({'entries':len(matrix),'executed':sum(e['status']=='EXECUTED' for e in matrix),'missing':len(missing)}))
if __name__=='__main__':main()
