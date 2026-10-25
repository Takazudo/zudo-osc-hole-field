#!/usr/bin/env python3
"""Joined scalar design alternatives, never geometry or PCB connectivity credit."""
import argparse,json,hashlib,math
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[5]
def load(p):return json.loads(p.read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def drop(rail_current,return_current,main_mm,feed_mm,hot,contact,rail_copper,return_copper,parallel_returns):
 if parallel_returns not in (1,2,3) or any(not math.isfinite(v) or v<0 for v in (rail_current,return_current,main_mm,feed_mm,hot,contact,rail_copper,return_copper)):raise ValueError('invalid alternative')
 wire=(main_mm+feed_mm)*hot/1000+2*contact
 return 1000*(rail_current*(wire+rail_copper)+return_current*(wire/parallel_returns+return_copper))
def calculate():
 p=R/'design/partition/partition-input.json';d=load(p)['load_distribution'];curvepath=R/'circuit/routing/epic-242/decision-pilots/feed-arrangement/robust-curve.json';curve=load(curvepath)
 main=max(curve['cut_and_preparation']['main_cut_range_mm']);feed=max(curve['cut_and_preparation']['new_cut_range_mm']);assert (main,feed)==(104,85)
 assert d['net_order']==['+12V','-12V','+5V','AGND','AGND','AGND']
 result=[]
 for label,m,f,rc,gc,n in [('historical-110-plus-110',110,110,.001,.0005,1),('latest-short-cuts-original-copper',main,feed,.001,.0005,1),('latest-short-cuts-tight-copper',main,feed,.0001,.0001,1),('matched-three-return-subnetwork',main,feed,.001,.0005,3),('matched-two-return-subnetwork',main,feed,.001,.0005,2)]:
  drops={net:drop(amps,d['single_return_max_A'],m,f,d['hot_resistance_requirement_ohm_per_m'],d['combined_termination_resistance_ohm'],rc,gc,n) for net,amps in d['rail_max_A'].items()}
  result.append({'id':label,'main_cut_ceiling_mm':m,'new_cut_ceiling_mm':f,'global_rail_copper_ohm':rc,'global_common_return_copper_ohm':gc,'parallel_return_paths_per_section':n,'drops_mV':drops,'minimum_margin_mV':20-max(drops.values()),'scalar_20mV_screen':all(v<=20 for v in drops.values()),'physical_candidate_ready':False,'scope':'Whole-source concentration through one rail path. Parallel case requires actual same-endpoint accessible returns and matched source/load current functionals; no equal sharing or arbitrary signed GH injection credit.'})
 tight=result[2];margin=tight['minimum_margin_mV'];maxrail=max(d['rail_max_A'].values());ret=d['single_return_max_A'];allowedcombined=(.020-maxrail*.001-ret*.0005-(maxrail+ret)*2*d['combined_termination_resistance_ohm'])/((maxrail+ret)*d['hot_resistance_requirement_ohm_per_m'])*1000
 return {'status':'CONDITIONAL_DESIGN_COMPARISON_NOT_SOURCE_REALIZATION','source_hashes':{str(p.relative_to(R)):digest(p),str(curvepath.relative_to(R)):digest(curvepath),'compare-budgets.py':digest(Path(__file__))},'alternatives':result,'tight_copper_headroom':{'mV':margin,'additional_common_rail_and_return_cut_each_section_sum_mm':margin/(maxrail+ret)/d['hot_resistance_requirement_ohm_per_m'],'additional_return_mohm_if_rail_unchanged':margin/ret},'original_copper_one_return':{'combined_cut_limit_mm':allowedcombined,'new_cut_limit_with104mm_main_mm':allowedcombined-main,'shortfall_against85mm_feed_mm':feed-(allowedcombined-main)},'parallel_derivation':'For a genuine two-port return subnetwork, three separate conductors each <=Rs give Reff<=Rs/3 by conductance sum and Rayleigh monotonicity. Equal currents are not asserted. Access and shared necks must be charged once in the expanded graph. Additional externally injected ports require their own joined solution.','not_credited':['Actual source-to-load board copper and via/spreading resistance','Finite contact/source functionals for new CS247 ends','Complete 380-GH-return signed network and peripheral port bounds','Any measured thermal/process capability or physical fit','Fault/partial-power qualification','Native validation or architecture adoption']}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();out=json.dumps(calculate(),indent=2,sort_keys=True)+'\n';p=H/'budget-comparison.json'
 if a.check:assert p.read_text()==out,'source budget evidence drift'
 else:p.write_text(out)
 print('PASS conditional joined alternatives; physical candidate remains unestablished')
if __name__=='__main__':main()
