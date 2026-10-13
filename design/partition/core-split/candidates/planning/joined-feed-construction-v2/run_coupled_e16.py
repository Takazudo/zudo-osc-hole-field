#!/usr/bin/env python3
"""Serialized coupled KA-KB solves over the finite operators of run_finite_e16.py (source-only).

Per net, process case and declared stack depth: reduce KA, reduce KB, driving-point
chunks, then couple. Each unit is a separate hash-ledgered process (replay_steps.Ledger):
timeout 180 s, a 2 GiB no-swap memory scope (finite_solve.enter_memory_scope), content-bound --resume. One unit at a time.
"""
import argparse,json,time
from pathlib import Path
import replay_steps as rs
HERE=Path(__file__).resolve().parent
NETS=['+12V','-12V','+5V','AGND']
METHODS=['finite_solve.py','finite_adapter.py','finite_units.py','load_ledger.py']
DP_CHUNK=96         # pads per driving-point unit: 4 refined solves per 16-pad batch must fit 180 s on 1.9 M nodes
def main():
 p=argparse.ArgumentParser();p.add_argument('--python',required=True);p.add_argument('--finite',type=Path,required=True,help='run_finite_e16.py OUTDIR')
 p.add_argument('--output',type=Path,required=True);p.add_argument('--net',choices=NETS,action='append');p.add_argument('--case',action='append');p.add_argument('--depth',action='append')
 p.add_argument('--config',type=Path,default=HERE/'evidence/e16/continuation-20261013b/coupled-network-config.json');p.add_argument('--cases',type=Path,default=HERE/'evidence/e16/process-cases.json')
 p.add_argument('--resume',action='store_true');a=p.parse_args()
 out=a.output;rs.need(out.is_absolute() and not out.is_relative_to(rs.ROOT),'absolute OUTDIR outside the repository required')
 rs.need(a.resume or not out.exists(),'fresh OUTDIR required (or --resume)');out.mkdir(parents=True,exist_ok=True)
 cfg=json.loads(a.config.read_text());ledger=HERE/cfg['scenario']['ledger'];L=rs.Ledger(out,a.resume,a.python);started=time.strftime('%Y-%m-%dT%H:%M:%S%z')
 cases=a.case or list(json.loads(a.cases.read_text())['cases']);depths=a.depth or [cfg['default_depth_case']]
 coverage=[a.finite/b/f'coverage-{net}.json.gz' for b in ('KA','KB') for net in NETS]
 service=out/f'device-service-{cfg["scenario"]["id"]}.json'
 L.run('device-service-'+cfg['scenario']['id'],['finite_solve.py','service','--config',a.config,'--ledger',ledger,'--coverage',*coverage,'--output',service],
       [a.config,ledger,*coverage],METHODS,[service])
 common=['--config',a.config,'--cases',a.cases]
 for net in a.net or NETS:
  for case in cases:
   for depth in depths:
    tag=f'{net}-{case}-{depth}';red={};dps={};ops={}
    for b in ('KA','KB'):
     op=a.finite/b/f'operator-{net}.pkl.gz';cov=a.finite/b/f'coverage-{net}.json.gz';ops[b]=op;r=out/f'{b}-red-{tag}.pkl.gz';red[b]=r
     args=['--operator',op,'--coverage',cov,*common,'--case',case,'--depth',depth,'--board',b,f'--net={net}']
     L.run(f'{b}-reduce-{tag}',['finite_solve.py','reduce',*args,'--ledger',ledger,'--service',service,'--output',r],[op,cov,a.config,a.cases,ledger,service,*coverage],METHODS,[r])
     n=json.loads((out/'steps'/f'{b}-reduce-{tag}.json').read_text())['stdout_tail'];pads=json.loads(n.strip().splitlines()[-1])['pads'];dps[b]=[]
     for k,lo in enumerate(range(0,pads,DP_CHUNK)):
      f=out/f'{b}-dp-{tag}-{k:03d}.pkl.gz';dps[b].append(f)
      L.run(f'{b}-dpoint-{tag}-{k:03d}',['finite_solve.py','dpoint',*args,'--start',str(lo),'--stop',str(lo+DP_CHUNK),'--output',f],[op,cov,a.config,a.cases],METHODS,[f])
    res=out/f'coupled-{tag}.json.gz'
    L.run(f'couple-{tag}',['finite_solve.py','couple','--ka-red',red['KA'],'--kb-red',red['KB'],'--ka-op',ops['KA'],'--kb-op',ops['KB'],'--ka-dp',*dps['KA'],'--kb-dp',*dps['KB'],
          *common,'--case',case,'--depth',depth,f'--net={net}','--output',res],[red['KA'],red['KB'],ops['KA'],ops['KB'],*dps['KA'],*dps['KB'],a.config,a.cases],METHODS,[res])
 log=out/'coupled-log.json';prior=json.loads(log.read_text()) if log.exists() else {'invocations':[]}
 prior['invocations'].append({'started':started,'finite':str(a.finite),'nets':a.net or NETS,'cases':cases,'depths':depths,'resume':a.resume,'device_service':str(service),'log':L.log})
 log.write_text(json.dumps(prior,indent=1)+'\n')
if __name__=='__main__':main()
