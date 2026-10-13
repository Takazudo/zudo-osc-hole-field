#!/usr/bin/env python3
"""Mesh-sensitivity comparison of single-board driving-point resistances (source-only).

For one board net, each variant operator (local refinement, shifted cell origin) is
built from the same verified fragments, pad supports and source lands as the baseline;
only the cell grid differs. e_p is pad p's unit-current potential with the board's
terminal nodes (KB) or held source lands (KA) as reference: dpoint output of finite_solve.
The tolerance was declared before results (coupled-network-config numerical_tolerances);
P1 conforming elements approach the continuum resistance from below, so a refined mesh
is expected to give equal or slightly higher values.
"""
import argparse,json
from pathlib import Path
import numpy as np
from finite_units import pload,jload
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline',required=True);p.add_argument('--variant',action='append',required=True,help='LABEL=dpoint.pkl.gz')
 p.add_argument('--config',default=str(Path(__file__).resolve().parent/'evidence/e16/coupled-network-config.json'));p.add_argument('--output',required=True);a=p.parse_args()
 tol=jload(a.config)['numerical_tolerances'];base=pload(a.baseline);eb=dict(zip(base['pads'],base['e']));out={'board':base['board'],'net':base['net'],'case':base['case'],'pads':len(eb),'variants':{}}
 for spec in a.variant:
  label,f=spec.split('=',1);v=pload(f);ev=dict(zip(v['pads'],v['e']));need=set(eb)==set(ev)
  rel=np.array([(ev[k]-eb[k])/eb[k] for k in eb]) if need else np.zeros(0)
  out['variants'][label]={'same_pads':need,'max_abs_relative_change':float(np.max(abs(rel))) if need else None,'median_relative_change':float(np.median(rel)) if need else None,
                          'mean_relative_change':float(np.mean(rel)) if need else None,'max_baseline_e_ohm':float(max(eb.values())),'max_variant_e_ohm':float(max(ev.values())),
                          'within_declared_report_tolerance':bool(need and np.max(abs(rel))<=tol['refinement_change_relative_report_only'])}
 Path(a.output).write_text(json.dumps(out,indent=1)+'\n');print(json.dumps(out))
if __name__=='__main__':main()
