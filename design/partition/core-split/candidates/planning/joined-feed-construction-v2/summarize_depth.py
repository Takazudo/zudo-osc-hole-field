#!/usr/bin/env python3
"""Stack-depth sensitivity of the coupled reduced study (nominal-average, all returns present)."""
import argparse,gzip,hashlib,json
from pathlib import Path
import numpy as np
import finite_units as U
HERE=Path(__file__).resolve().parent
DEPTHS=['uniform-dielectric','staged-caps-bands','barrel-upper-1p6-per-interval']
def main():
 p=argparse.ArgumentParser();p.add_argument('--coupled',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 cfg=U.jload(HERE/'evidence/e16/coupled-network-config.json');Rt=cfg['wires']['termination_per_end_ohm'];sha=lambda q:hashlib.sha256(Path(q).read_bytes()).hexdigest()
 out={'schema':'e16-coupled-depth-sensitivity-v1','case':'nominal-average','scenario':cfg['scenario']['id'],'depth_cases':{},
      'note':'uniform-dielectric is the matrix default; staged-caps-bands is the rejected staged-model stack; barrel-upper-1p6-per-interval charges every tap-to-tap interval the full board thickness (an upper bound on each interval).',
      'bindings':{'config':sha(HERE/'evidence/e16/coupled-network-config.json'),'method':{m:sha(HERE/m) for m in ['summarize_depth.py','finite_solve.py']},'run_directory':str(a.coupled)}}
 for depth in DEPTHS:
  row={}
  for net in ['+12V','-12V','+5V','AGND']:
   f=a.coupled/f'coupled-{net}-nominal-average-{depth}.json.gz';rf=a.coupled/f'KA-red-{net}-nominal-average-{depth}.pkl.gz'
   d=json.loads(gzip.decompress(f.read_bytes()));st=d['states']['all-present'];r=U.pload(rf);Sinv=np.linalg.inv(r['S'])
   rcu=[x for b in st['driving_point'].values() for x in b['R_copper_ohm']];pv=[abs(v) for b in st['boards'].values() for v in b['pad_potential_V'].values()]
   tot=st['energy_W']['total'];bar=sum(b['energy_W']['barrels'] for b in st['boards'].values())
   row[net]={'ka_trunk_copper_to_terminal_ohm':{t.rsplit('-',1)[1]:float(Sinv[i,i]-Rt) for i,t in enumerate(r['terms'])},
             'copper_resistance_ohm':{'min':min(rcu),'median':float(np.median(rcu)),'max':max(rcu)},'max_abs_pad_potential_V':max(pv),'barrel_energy_share':bar/tot if tot else None,
             'source':{f.name:sha(f),rf.name:sha(rf)}}
  out['depth_cases'][depth]=row
 a.output.write_text(json.dumps(out,indent=1)+'\n');print(json.dumps({k:{n:round(v['ka_trunk_copper_to_terminal_ohm'][next(iter(v['ka_trunk_copper_to_terminal_ohm']))]*1e3,3) for n,v in r.items()} for k,r in out['depth_cases'].items()}))
if __name__=='__main__':main()
