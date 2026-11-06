"""Conditional demand comparisons; unknowns and source requirements never auto-reduced."""
from pathlib import Path
from collections import Counter
from unittest.mock import patch
import json,sys
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from proposal import ROOT,prepare,require,sha,write
from design.spec.instrument import specification
from scripts.schgen.core import designator
from scripts.schgen.build_master_budget import build as master_build
from scripts.schgen.build_rail_ledger import build as ledger_build
from design.spec.modules import build_sample_hold_current as sh
from design.spec.modules.check_oscillator_reference import build as fanout_build
RAILS=('+12V','-12V','+5V')
RESERVES={'Internal resistive/reference/shaper load reserve','Shared reference and distribution reserve','Reference/control/expo/feedback reserve','Reference, rates, clamp and control reserve','reference, signal pots, summer feedback, servo and trims'}
def read(p):return json.loads((ROOT/p).read_text())
def build():
 fs,ins=specification();new,proposal=prepare(fs,ins);f=next(f for f in new if f.name=='sample_hold')
 baseline=sh.build();require(baseline==read('design/reports/current/sample_hold.json'),'SH worksheet drift')
 with patch.object(sh,'family',return_value=f):candidate=sh.build()
 master=master_build();ledger=ledger_build();fanout=fanout_build();supply=read('design/power/supply-architecture.json')
 require(master==read('design/power/rail-budget.json') and ledger==read('design/power/rail-ledger.json') and fanout==read('design/reports/oscillator-reference-fanout.json'),'source report drift')
 savings={kind:{r:round(sum(b[field][r]-n[field][r] for b,n in zip(baseline['instances'],candidate['instances'])),6) for r in RAILS} for kind,field in [('typical','known_typical_mA'),('planning_Iq','known_planning_upper_mA')]}
 require(savings=={'typical':{'+12V':27.36,'-12V':27.36,'+5V':0},'planning_Iq':{'+12V':42,'-12V':42,'+5V':0}},'IQ arithmetic')
 packages=ledger['physical_ic_packages'];clips=[p for p in packages if p['symbol']=='LM393BIDR' and p['supply_pins']=={'8':'+12V','4':'-12V'}]
 require(len(clips)==20,'clip comparator topology count')
 correction=0;cliprows=[]
 for inst in sorted({p['instance'] for p in clips}):
  rows=[l for l in ledger['worksheet_loads'] if l['instance']==inst and l['label']=='LM393BIDR'];require(len(rows)==1,'clip row')
  row=rows[0];qty=sum(p['instance']==inst for p in clips)
  require(qty==row['count'] and row['reported_assumed_typical_mA']=={'+12V':qty*.6,'-12V':qty*.1,'+5V':0} and row['planning_allowance_mA']=={'+12V':qty,'-12V':qty,'+5V':0},'clip accounting source')
  delta=round(row['reported_assumed_typical_mA']['+12V']-row['reported_assumed_typical_mA']['-12V'],6);correction+=delta
  cliprows.append({'load_id':row['id'],'refs':[p['ref'] for p in clips if p['instance']==inst],'negative_typical_correction_mA':delta})
 require(abs(correction-10)<1e-9,'typical correction')
 reserves=[r for r in ledger['worksheet_loads'] if r['label'] in RESERVES]
 require(len(reserves)==19 and all(sum(r['planning_allowance_mA'][rail] for r in reserves)==233 for rail in RAILS[:2]),'reserve pool')
 branch=[];unused=[];trim=[]
 for inst in ins:
  family=next(f for f in fs if f.name==inst.family)
  if inst.family not in ('filter','envelope','mix4_vca'):continue
  for p in family.parts:
   if p.prefix=='RV' and p.value=='10 kΩ' and p.pins.get('1')=='REFN5' and p.pins.get('3')=='REF5':trim.append({'instance':inst.name,'ref':designator(p,inst),'key':p.key,'pins':p.pins,'value':p.value,'nominal_through_mA':1,'included_in_reserve_not_extra':True})
   if p.prefix in ('R','RB') and any(n and 'IABC' in n for n in p.pins.values()):
    target=unused if 'UNUSED_BIAS_OFF' in p.key else branch
    target.append({'instance':inst.name,'ref':designator(p,inst),'key':p.key,'value':p.value,'pins':p.pins,'allocation':'Part of live OTA bias/servo branch; overlap magnitude unallocated; no rebate'})
 require(len(trim)==26,'real trim track inventory')
 require(Counter(x['instance'] for x in branch)==Counter({**{f'F{i}':4 for i in range(1,4)},**{f'E{i}':2 for i in range(1,7)},'M4A':1,'M4B':1}),'complete main OTA feed inventory')
 require(len(unused)==2,'unused OTA bias-off inventory')
 ext=supply['selected_requirement'];normal=ext['normal_with_allowances_mA'];planning={r:round(normal[r]-savings['planning_Iq'][r],6) for r in RAILS}
 corrected={r:round(master['reported_assumed_typical_subtotal_mA'][r]-savings['typical'][r]+(correction if r=='-12V' else 0),6) for r in RAILS}
 refinement={r:round(5*(5-fanout['per_rail_output_current_bound_mA_per_oscillator'][r]),9) for r in RAILS[:2]}
 unknown={r:None for r in RAILS}
 result={'status':'UNADOPTED conditional accounting proposal, not a maximum or measured demand','removed_Iq_mA':savings,'removed_counts_by_mpn':dict(Counter(p['mpn'] for p in proposal['packages'])),'physical_IC_count_before':len(packages),'physical_IC_count_proposed':len(packages)-12,
 'master_reported_typical_before_mA':master['reported_assumed_typical_subtotal_mA'],'master_reported_typical_after_Iq_and_clip_accounting_mA':corrected,'master_planning_before_mA':master['reported_planning_upper_subtotal_mA'],'master_planning_after_Iq_mA':{r:round(master['reported_planning_upper_subtotal_mA'][r]-savings['planning_Iq'][r],6) for r in RAILS},
 'EXT_normal_with_allowances_before_mA':normal,'EXT_normal_with_allowances_after_Iq_mA':planning,'source_minimum_continuous_mA_UNCHANGED':ext['minimum_continuous_mA'],'source_minimum_transient_mA_UNCHANGED':ext['minimum_transient_mA'],
 'historical_zudo_pd_unmeasured_target_mA':{r:master['rails'][r]['supply_design_target'] for r in RAILS},'planning_after_Iq_minus_historical_target_mA':{r:round(planning[r]-master['rails'][r]['supply_design_target'],6) for r in RAILS},
 'clip_comparator_accounting':{'packages':clips,'worksheet_rows':cliprows,'negative_typical_correction_mA':round(correction,6),'planning_correction_mA':0,'qualification':'Symmetry correction under existing0.6mA/package model; not a new measured or guaranteed LM393B rating; LED/pullup current separate'},
 'reserve_pools':reserves,'coarse_reserve_mA_per_analog_rail':233,'reserve_rebate_booked_mA':0,'verified_nominal_trim_branches':trim,'nominal_trim_current_contained_in_reserves_mA_per_analog_rail':26,'OTA_bias_overlap_branches':branch,'OTA_unused_bias_off_branches':unused,
 'optional_reference_refinement_NOT_BOOKED':{'current_explicit_increment_mA_per_analog_rail':25,'conditional_5_oscillator_allowance_reduction_mA':refinement,'same_conditions':fanout['conditions'],'reason':'Tightens only explicit5mA per-oscillator increment; no assumed credit from original12mA reserve; no physical saving'},
 'simultaneity':{'Iq_allowance_power_reduction_at_nominal_plusminus12_W':1.008,'typical_Iq_model_power_reduction_at_nominal_plusminus12_W':.65664,'aggregate_rail_maxima_are_not_simultaneous_power':True,'rule':'Quiescent and rail-to-rail resistor currents genuinely load both rails. Bipolar signal/indicator extrema may be opposite states. Keep independent rail requirements; no blanket halving.'},
 'guaranteed_whole_instrument_maximum_mA':unknown,'complete_typical_mA':unknown,'measured_source_capacity_mA':unknown,'unknown_reasons_preserved':ledger['unknown_maximum_reasons'],'source_not_proven_preserved':supply['not_proven'],'ADG5412F_package_count_existing':sum(p['symbol']=='ADG5412FBRUZ' for p in packages),'grouped_input_protection_savings_booked_mA':0}
 return result,candidate
if __name__=='__main__':
 result,candidate=build()
 for name,data in [('accounting.json',result),('sample-hold-proposed.json',candidate)]:
  p=HERE/name
  if '--check' in sys.argv:require(json.loads(p.read_text())==data,name+' drift')
  else:write(p,data)
 print('PASS conditional42mA/rail IQ proposal;10mA negative typical correction;233mA reserve retained')
