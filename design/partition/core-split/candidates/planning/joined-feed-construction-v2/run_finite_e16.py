#!/usr/bin/env python3
"""Serialized, hash-ledgered E16 finite coverage on one replayed round (source-only; no native call).

Each unit runs through replay_steps.Ledger: its own process under `timeout 180s`,
finite_units.py's 2 GiB address-space limit, a step ledger binding input/method/output
SHA-256, and content-bound --resume. Units run one at a time.
"""
import argparse,json,time
from pathlib import Path
import replay_steps as rs
HERE=Path(__file__).resolve().parent
NETS=['+12V','-12V','+5V','AGND']
UNIT_METHODS=['finite_units.py','finite_adapter.py','selective_annulus.py','fragments.py','connectivity.py','staged_caps.py']
def main():
 p=argparse.ArgumentParser();p.add_argument('--python',required=True);p.add_argument('--run',type=Path,required=True,help='replay OUTDIR holding K?-eval-ROUND')
 p.add_argument('--round',default='t2');p.add_argument('--output',type=Path,required=True);p.add_argument('--board',choices=['KA','KB'],action='append');p.add_argument('--net',choices=NETS,action='append')
 p.add_argument('--pitch',type=float,default=1.);p.add_argument('--face-pitch',type=float,default=.25);p.add_argument('--tile-mm',type=float,default=24.);p.add_argument('--origin',type=float,nargs=2,default=(0.,0.))
 p.add_argument('--resume',action='store_true');a=p.parse_args()
 out=a.output;rs.need(out.is_absolute() and not out.is_relative_to(rs.ROOT),'absolute OUTDIR outside the repository required')
 rs.need(a.resume or not out.exists(),'fresh OUTDIR required (or --resume)');out.mkdir(parents=True,exist_ok=True)
 L=rs.Ledger(out,a.resume,a.python);started=time.strftime('%Y-%m-%dT%H:%M:%S%z');geom=['--pitch',str(a.pitch),'--face-pitch',str(a.face_pitch),'--tile-mm',str(a.tile_mm),'--origin',str(a.origin[0]),str(a.origin[1])]
 for b in a.board or ['KA','KB']:
  ev=a.run/f'{b}-eval-{a.round}';d=out/b;d.mkdir(exist_ok=True)
  planes=[d/f'planes-{n}.json.gz' for n in NETS]
  L.run(f'{b}-split',['finite_units.py','split','--planes',ev/'clipped-sheets.json','--outdir',d],[ev/'clipped-sheets.json'],['finite_units.py'],planes)
  for net in a.net or NETS:
   tag=f'{b}-{net}';desc=d/f'desc-{net}.json.gz';plan=d/f'plan-{net}.json'
   L.run(f'{tag}-describe',['finite_units.py','describe','--source',ev/'normalized-caps.json','--planes',d/f'planes-{net}.json.gz','--graph',ev/'port-graph.json','--census',ev/'port-obligations.json',f'--net={net}','--output',desc],
         [ev/'normalized-caps.json',d/f'planes-{net}.json.gz',ev/'port-graph.json',ev/'port-obligations.json'],UNIT_METHODS,[desc])
   L.run(f'{tag}-plan',['finite_units.py','plan','--desc',desc,*geom,'--output',plan],[desc],UNIT_METHODS,[plan])
   chunks=json.loads(plan.read_text())['chunks'];meshes=[d/f'mesh-{net}-{k:03d}.pkl.gz' for k in range(len(chunks))]
   for k,m in enumerate(meshes):
    L.run(f'{tag}-mesh-{k:03d}',['finite_units.py','mesh','--desc',desc,*geom,'--chunk',str(k),'--output',m],[desc,plan],UNIT_METHODS,[m])
   op,cov=d/f'operator-{net}.pkl.gz',d/f'coverage-{net}.json.gz'
   L.run(f'{tag}-assemble',['finite_units.py','assemble','--desc',desc,*geom,'--mesh',*meshes,'--graph',ev/'port-graph.json','--census',ev/'port-obligations.json','--operator',op,'--output',cov],
         [desc,plan,*meshes,ev/'port-graph.json',ev/'port-obligations.json'],UNIT_METHODS,[op,cov])
 log=out/'finite-log.json';prior=json.loads(log.read_text()) if log.exists() else {'invocations':[]}
 prior['invocations'].append({'started':started,'run':str(a.run),'round':a.round,'boards':a.board or ['KA','KB'],'nets':a.net or NETS,'geometry':geom,'resume':a.resume,'log':L.log})
 log.write_text(json.dumps(prior,indent=1)+'\n')
if __name__=='__main__':main()
