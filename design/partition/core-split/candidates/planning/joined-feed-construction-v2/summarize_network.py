#!/usr/bin/env python3
"""Compact, hash-bound summary of run_finite_network.sh outputs for evidence/e16."""
import argparse,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
LIMIT_OHM={'+12V':1e-3,'-12V':1e-3,'+5V':1e-3,'AGND':5e-4}   # power/joined/budget.json limits, charged once globally
DROP_LIMIT_V=.020
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--runs',type=Path,required=True);p.add_argument('--round',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 rows=[];ports={};files={}
 for f in sorted(a.runs.glob('*.json')):
  d=json.loads(f.read_text());files[f.name]=sha(f)
  for r in d['results']:
   row={'board':d['board'],'net':d['net'],'case':r['case'],'pitch_mm':r['pitch_mm'],'removed_wires':r['removed_wires'],
        'ports_solved':r['ports_solved'],'ports_without_finite_path':len(r['ports_without_finite_path']),
        'structurally_unresolved_excluded':len(d['coverage']['structurally_unresolved_excluded']),'rail_pads':d['coverage']['rail_pads'],
        'max_port_R_mOhm':None if r['max_port_resistance_ohm'] is None else round(r['max_port_resistance_ohm']*1e3,4),
        'max_port_onboard_R_mOhm':None if r['max_port_onboard_resistance_ohm'] is None else round(r['max_port_onboard_resistance_ohm']*1e3,4),
        'worst_port':r['worst_port'],'max_wire_current_fraction':{k:round(v,4) for k,v in r['max_wire_current_fraction'].items()},
        'model_drop_figure_mV':None if r['distribution_free_drop_bound_V'] is None else round(r['distribution_free_drop_bound_V']*1e3,3),
        'model':{k:r['model'][k] for k in ['sheet_cells','sheet_pieces','segments','barrel_legs','pads','face_joins','barrels_without_sheet_cell']},
        'input_sha256':d['input_sha256']}
   row['model_drop_figure_within_20mV']=None if row['model_drop_figure_mV'] is None else row['model_drop_figure_mV']<=DROP_LIMIT_V*1e3
   if row['max_port_onboard_R_mOhm'] is not None:row['onboard_R_over_global_copper_budget']=round(row['max_port_onboard_R_mOhm']/(LIMIT_OHM[d['net']]*1e3),3)
   rows.append(row)
   if r['case']=='nominal-average' and r['pitch_mm']==.5:ports[f"{d['board']}|{d['net']}|{'-'.join(map(str,r['removed_wires'])) or 'all'}"]=r['ports']
 out={'schema':'e16-finite-network-summary-v1','round':a.round,'status':'CONDITIONAL_PARTIAL_NETWORK; NOT ELECTRICAL COMPLIANCE; ACCEPTANCE UNRESOLVED',
      'budgets':{'distribution_mV':20,'rail_copper_mOhm':1,'return_copper_mOhm':.5,'note':'Global budgets are charged once across the whole joined network. A model port resistance above a budget means only that the budget is not shown met: the model overcharges barrels and idealizes joins, so it is not a lower bound. The actual drop depends on per-pad currents, which are not established.'},
      'rows':rows,'run_files_sha256':files,'native_calls':0,'accepted':False}
 a.output.write_text(json.dumps(out,indent=1)+'\n')
 a.output.with_name(a.output.stem+'-ports.json.gz').write_bytes(gzip.compress(json.dumps(ports,sort_keys=True,separators=(',',':')).encode(),mtime=0))
 for r in rows:print(r['board'],r['net'],r['case'][:12],r['pitch_mm'],r['removed_wires'],r['ports_solved'],r['ports_without_finite_path'],r['max_port_R_mOhm'],r['max_port_onboard_R_mOhm'],r['max_wire_current_fraction'],r['model_drop_figure_mV'])
if __name__=='__main__':main()
