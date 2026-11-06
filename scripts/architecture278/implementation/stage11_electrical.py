"""A01 conditional analytical budgets. No simulator, native CAD or acceptance."""
import argparse, hashlib, json, math
from pathlib import Path
import stage10_interfaces as prior
ROOT=prior.ROOT
OUT=prior.a.OUT/'stage11'
N='/A01/'
def need(ok,why):
 if not ok: raise ValueError(why)
def wiper(position, resistance, low, high, series=1000, load=1e7):
 need(0<=position<=1 and resistance>0 and series>=0 and load>0,'wiper parameters')
 v=low+(high-low)*position; r=resistance*position*(1-position)
 sense=v*load/(load+series+r); current=sense/load
 return {'position':position,'ideal_V':v,'sense_V':sense,'error_V':sense-v,'thevenin_ohm':r,'load_A':current,'high_endpoint_A':(high-low)/resistance+position*current,'low_endpoint_sink_A':(high-low)/resistance-(1-position)*current,'bias15nA_error_bound_V':15e-9/((1/(r+series))+(1/load))}
def operating_case(signal, offset, cv, position, resistance_return):
 # Conditional ideal DC state; output load fixed10k, no clipping certification.
 atten=2*wiper(position,1e4,0,signal)['sense_V']-signal
 manual=wiper(offset,1e5,-5,5)['sense_V']; out=atten+manual+cv
 magnitude=sum(abs(v)/5600 for v in (signal,cv,out))
 # Both patch sources supply their input100k pull-downs; their return is included
 # in AGND but is not counted as demand from local +12V regulator.
 external_return=(abs(signal)+abs(cv))/100000+abs(out)/10000
 reference_return=5/122000
 enable=2*5/101000
 clip_upper=12/22100 # Conservative LED-on zero-forward-drop envelope, not actual current.
 total=0.0012+reference_return+enable+magnitude+external_return+clip_upper
 return {'input_V':signal,'offset_position':offset,'offset_CV_V':cv,'atten_position':position,'out_ideal_loaded_V':out,'needs_clipping_analysis':abs(out)>=12,'AGND_magnitude_envelope_subtotal_A':total,'terms_A':{'REF5050_IQ_max_conditional':.0012,'reference_divider':reference_return,'two_enable_pulldowns':enable,'three_magnitude_senses':magnitude,'external_input_and_output_load_returns':external_return,'clip_LED_zero_drop_on_bound':clip_upper},'known_rail_magnitude_subtotals_A':{'+12V':.019+.0012+magnitude+clip_upper+abs(out)/10000,'-12V':.019+magnitude+abs(out)/10000,'+5V':enable},'rail_subtotal_scope':'Quiescent rail pairs plus conservative magnitude allocation of represented loads; same LED/output magnitude deliberately charged independently to either analog rail as an envelope, not a simultaneous KCL solution. Missing reference-buffer,summer,remote-buffer and otherIC currents remain additional.','return_shift_subtotal_V':total*resistance_return,'optional_ideal_1V_oct_pitch_cents':total*resistance_return*1200,'scope':'Magnitude sum without cancellation. Incomplete subtotal, excludes remaining ICground/leakage, inputprotection, transients, output/rail faults. REF5050 maximum conditions require validCL/ESR; clipping cases are mathematical demand only.'}

def analyze(inp,inv,graph,old):
 need(inp['return_limit_ohm']==.0005 and inp['rail_limit_ohm']==.001,'preserved resistance constraints')
 need(inp['equal_sharing_credit'] is False,'no parallel sharing credit')
 for r,pins in inp['source_pin_bindings'].items():need(inv['packages'][r]['pins']==pins,'actual source net binding '+r)
 for r,value in inp['source_value_bindings'].items():need(inv['packages'][r]['unit_records'][0]['value']==value,'source value '+r)
 s=inp['strap'];need(all(math.isfinite(s[k]) and s[k]>0 for k in ('length_mm','width_mm','thickness_mm','rho20_ohm_m','temperature_C','alpha_per_C')),'finite strap parameters')
 need(s['temperature_C']>=20 and s['joint_count']==2,'strap conditions')
 bulk=s['rho20_ohm_m']*(1+s['alpha_per_C']*(s['temperature_C']-20))*s['length_mm']*1e-3/(s['width_mm']*s['thickness_mm']*1e-6)
 paths=[]
 expected={(n,k)for k,v in graph['nodes'].items()if v['kind']=='source'for n in ('+12V','-12V','+5V','AGND')if v['net']==n}
 need(len(old['power_and_return_endpoint_paths'])==106 and {(r['net'],r['to'])for r in old['power_and_return_endpoint_paths']}==expected,'106 exact power endpoints')
 for row in old['power_and_return_endpoint_paths']:
  edges=[graph['edges'][i]for i in row['edge_indices']]
  need(all(e['net']==row['net']for e in edges),'power path nets')
  gh=sum(e['mated_GH_contacts']for e in edges);din=sum(e['kind']=='DIN_mated_pair'for e in edges)
  target=row['to'];iscore=inv['packages'][target.split(':')[0]]['owner']=='rear-core'
  limit=inp['return_limit_ohm']if row['net']=='AGND'else inp['rail_limit_ohm']
  paths.append({'net':row['net'],'source_boundary':row['source_boundary'],'to':target,'edge_indices':row['edge_indices'],'GH_contacts':gh,'DIN_contacts':din,'GH_contact_only_after_test_bound_ohm':gh*.05,'candidate_core_strap_replaces_K_PWR_branch':iscore,'strap_bulk_ohm':bulk if iscore else None,'remaining_whole_path_budget_ohm':limit-bulk if iscore else None,'unknown_terms':['upstream source-to-boundary feed','middle spreading/neck/via','two bolted joints and termination pads'if iscore else 'GH/crimp/wire termination','local copper/spreading/vias to actual target pad','common return current distribution'],'actual_complete_resistance_ohm':None,'scope':'Single complete boundary-to-pad graph walk; upstream source additionally required. Strap replaces K-PWR only, no parallel credit or fictional per-board reset.'})
 grid=[i/1000 for i in range(1001)]
 cases=[operating_case(v,o,cv,x,inp['return_limit_ohm'])for v in (-5,0,5)for o in (0,.5,1)for cv in (-5,0,5)for x in (0,.5,1)]
 offset=[wiper(x,1e5,-5,5)for x in grid];atten=[wiper(x,1e4,0,5)for x in grid]
 def extrema(rows):return {'sample_grid_steps':1000,'sampled_max_abs_error_V':max(abs(r['error_V'])for r in rows),'max_error_row':max(rows,key=lambda r:abs(r['error_V'])),'midpoint':rows[500],'scope':'Finite deterministic position sensitivity, not continuous/tolerance guarantee; actual pot tolerance, track/contact noise and temperature remain unknown.'}
 # Full source branch inventory is retained; ideal virtual grounds are conditional.
 refs={'REF5_nominal_unloaded_source_A':5/10000+5/122000+10/100000,'REFN5_nominal_unloaded_sink_A':5/10000+10/100000,'REF5_with_position_load_max_sampled_A':max(5/10000+5/122000+r['high_endpoint_A']for r in offset),'REFN5_with_position_load_max_sampled_A':max(5/10000+r['low_endpoint_sink_A']for r in offset),'endpoints':{n:inv['net_endpoints'][N+n]for n in ('REF5','REFN5')},'scope':'Ideal ±5V, virtual-ground inversion and unloaded comparator inputs; reference buffers source/sink these loads, REF5050 raw output feeds buffer input. Bias/leakage/transient/stability not zero or qualified.'}
 return {'status':'CONDITIONAL ANALYTICAL SOURCE STUDY; NOT QUALIFIED','reference_load':refs,'normal_state_conditional_subtotals':cases,'state_grid_summary':{'case_count':len(cases),'maximum_demand_subtotal_A':max(c['AGND_magnitude_envelope_subtotal_A']for c in cases),'maximum_with_ideal_output_inside_supply_rails_subtotal_A':max(c['AGND_magnitude_envelope_subtotal_A']for c in cases if not c['needs_clipping_analysis']),'scope':'Grid includes overrail mathematical demands; inside supply rails does not establish actual linear headroom. Neither maximum includes all physical currents.'},'return_sensitivity':[{ 'current_A':i,'at_retained_half_mohm_V':i*.0005,'at_GH_pair_aftertest_bound_V':i*.1,'at_half_mohm_ideal_pitch_cents':1200*i*.0005,'at_GH_pair_ideal_pitch_cents':1200*i*.1}for i in (.0012,max(c['AGND_magnitude_envelope_subtotal_A']for c in cases),.1)],'wiper_models':{'offset':extrema(offset),'atten_at_5V_input':extrema(atten),'atten_sampled_max_output_error_V':2*max(abs(r['error_V'])for r in atten),'atten_sampled_max_gain_error_V_per_V':2*max(abs(r['error_V'])for r in atten)/5,'gain_error_coefficients':{'atten_wiper_error':2,'manual_offset_error':1,'offset_CV_error':1,'reference_high_to_unloaded_manual': 'position','reference_low_to_unloaded_manual':'1-position','return_shift':'Depends location of shift and source/receiver reference; no universal coefficient without actual return graph/current distribution'},'offset_nominal_max_Rth_plus1k_ohm':26000,'offset_nominal_RC_tau_max_s':(26000*1e7/(26000+1e7))*1e-8,'atten_transfer':'2*loaded_wiper-IN_BUFFER; wiper loading error is doubled. Manual offset contributes once. Bias15nA conditioned manufacturer sensitivity is not all-temperature assembled error.'},'transfer_headroom':{'ideal':'OUT_INTERNAL=(2*x-1)*IN+manual_offset+OFFSET_CV, before loading/gain/offset errors','ideal_extreme_V':15,'rails_V':[-12,12],'ideal_sum_exceeds_rail_V':3,'output_drive_for_5V_10k_load_V':5+998*5/10000,'scope':'Output drive includes998ohm isolation at DC with local feedback; actual swing/current/thermal and recovery limits remain unknown. ±15V cannot be a linear output on ±12V rails.'},'rail_return_budget':{'quiescent_between_rails_A':{'K_OPA4197':.012,'JR_OPA4197':.006,'JR_OPA4196':.001},'two_5V_enable_resistors_nominal_A':2*5/101000,'magnitude_LED_sense_nominal_at_5V_A_each':5/5600,'clip_LED_12V_zero_forward_drop_upper_A':12/22100,'scope':'IQ between rails is not AGND current. Three magnitude stages, reference divider, control/load, external patch/sleeve and protection currents can enter AGND. No cancellation or equal sharing; complete state/current maxima including REF5050,LM393B,ADG5412F,faults UNKNOWN.','state_classes':['normal position/input/output grid','clipped output/short','startup/rail order','unpowered external patch injection','service disconnected'],'complete_state_current_bounds_A':None},'power_endpoint_comparison':paths,'lowR_comparison':{'strap':s,'bulk_at_temperature_ohm':bulk,'two_joint_plus_remaining_return_allowance_ohm':inp['return_limit_ohm']-bulk,'two_joint_plus_remaining_rail_allowance_ohm':inp['rail_limit_ohm']-bulk,'GH_two_contacts_initial_ohm':.06,'GH_two_contacts_after_test_ohm':.1,'selected_hardware':False,'scope':'Copper material numbers are declared sensitivity inputs, not purchased alloy guarantee. Two bolted joints, pad necks, common feed and source remain unbounded. GH maxima cannot establish retained lowR compliance; not measured minima or proof all GH contacts fail.'},'requirement_history':inp['requirement_history'],'signal_roles':{'REF5/REFN5/wipers/analog':'DC loading, gain, drift, low-frequency noise and AGND shift; attenuation and reference paths may carry modulation. Preserve actual intentional RC transfer. No universal300mm or short-path stability claim.','GATE_RAW/GATE_REF':'REF5 22k/100k divider nominal4.098V feeds U7104:10; buffered GATE_REF U7104:8/9 has only its own feedback in captured A01, not an external gate output or ADG enable. ADG enables derive +5V through1k/100k. Do not fabricate gate loads.','clip':'OUT_INTERNAL divided by2 is compared to REF5/REFN5: nominal ±10V clip indication threshold. Comparator offset/reference error, input slew, noise and propagation affect crossing time/false indication. No pitch accuracy criterion applies to comparator edges.'},'unknowns':['REF5050 C7102 effective capacitance/ESR and input bypass recommendation; see Stage11 identity report','resistor ratio/tolerance/temp drift correlation and all actual pot parameters','complete assembled parasitic capacitance and amplifier stability','all state currents and upstream supply protection','strap joints/torque/ageing/insulation/material and actual copper routing'],'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN'}
def feed_alternative(result,support,graph,old):
 rows=support['low_R_feed_option']['straps'];need(len(rows)==3 and {r['net']for r in rows}=={'+12V','-12V','AGND'},'three distinct strap feeds')
 bynet={r['net']:r for r in rows};lookup={r['to']:r for r in old['power_and_return_endpoint_paths']};out=[]
 for row in result['power_endpoint_comparison']:
  if not row['candidate_core_strap_replaces_K_PWR_branch']:continue
  strap=bynet[row['net']];need(strap['width_mm']==10 and strap['thickness_mm']==1 and 0<strap['developed_centerline_mm']<=result['lowR_comparison']['strap']['length_mm'],'strap dimension/budget')
  expectedpin={'+12V':'1','-12V':'2','AGND':'3'}[row['net']];anchor='A01:K-PWR:local:'+expectedpin
  need(graph['nodes'][anchor]['net']==row['net'],'actual rear feed anchor')
  oldrow=lookup[row['to']];here=oldrow['source_boundary'];suffix=[];reached=False
  for index in oldrow['edge_indices']:
   edge=graph['edges'][index];need(here in (edge['from'],edge['to'])and edge['net']==row['net'],'baseline path identity')
   if reached:suffix.append(index)
   here=edge['to']if here==edge['from']else edge['from']
   if here==anchor:reached=True
  need(reached and here==row['to'],'rear anchor on complete path')
  start=graph['nodes'][row['source_boundary']]['pad_xyz_mm'];end=graph['nodes'][anchor]['pad_xyz_mm']
  middle=strap['middle_stud_xyz_mm'];rear=strap['rear_stud_xyz_mm']
  need(all(len(x)==3 and all(math.isfinite(v)for v in x)for x in (middle,rear)),'finite stud datums')
  segments=[{'kind':'new_middle_copper_transfer','from_xyz_mm':start,'to_xyz_mm':middle,'allocation_mm':prior.trace_length(start,middle),'resistance_ohm':None},{'kind':'bolted_strap','from_xyz_mm':middle,'to_xyz_mm':rear,'allocation_mm':strap['developed_centerline_mm'],'maximum_material_budget_mm':result['lowR_comparison']['strap']['length_mm'],'joints':2,'resistance_ohm':None},{'kind':'new_rear_copper_transfer','from_xyz_mm':rear,'to_xyz_mm':end,'allocation_mm':prior.trace_length(rear,end),'resistance_ohm':None}]
  length=sum(r['allocation_mm']for r in segments)+sum(graph['edges'][i]['allocated_developed_mm']for i in suffix)
  out.append({'net':row['net'],'source_boundary':row['source_boundary'],'to':row['to'],'new_segments':segments,'retained_suffix_edge_indices':suffix,'complete_boundary_to_pad_allocation_mm':length,'upstream_source_to_boundary_resistance_ohm':None,'complete_source_to_pad_resistance_ohm':None,'scope':'GH K-PWR branch disconnected in this option; its existing local pad used as explicit transfer anchor. Copper transfer routing/width/vias/necks unimplemented. DINjoinedreturn remains present but no parallelcredit. Shared source feed not reset or omitted.'})
 need(len(out)==sum(r['candidate_core_strap_replaces_K_PWR_branch']for r in result['power_endpoint_comparison']),'all affected core endpoints')
 result['lowR_complete_endpoint_paths']=out
 result['lowR_unmodified_front_endpoint_targets']=[r['to']for r in result['power_endpoint_comparison']if not r['candidate_core_strap_replaces_K_PWR_branch']]
 return result

def tolerance_sensitivity(identity):
 assignments=identity['candidate_assignments']; result={}
 ri=assignments['R7101']['candidate_ratings'];rf=assignments['R7102']['candidate_ratings']
 need(ri['value_SI']==rf['value_SI']==10000,'reference inversion resistor values')
 ratio_min=(1-rf['tolerance_fraction'])/(1+ri['tolerance_fraction']);ratio_max=(1+rf['tolerance_fraction'])/(1-ri['tolerance_fraction'])
 result['REFN5_inverting_gain']={'ratio_interval':[ratio_min,ratio_max],'ideal_REF5_5V_output_interval_V':[-5*ratio_max,-5*ratio_min],'max_abs_error_from_minus5_V':5*max(abs(ratio_min-1),abs(ratio_max-1)),'scope':'Independent candidate resistor tolerance corners; no tracking/matching credit. Adds reference source/amplifieroffset,bias andtemperature errors; not included in separately reported ideal±5V wiper sweeps.'}
 for label,nominal,low,high,seriesref,loadref in [('offset',1e5,-5,5,'R7119','R7120'),('atten',1e4,0,5,'R7115','R7116')]:
  sr=assignments[seriesref]['candidate_ratings'];lr=assignments[loadref]['candidate_ratings']
  need(sr['value_SI']==1000 and lr['value_SI']==1e7,'exact wiper resistor values')
  rows=[]
  for rt in (-.2,.2):
   for st in (-sr['tolerance_fraction'],sr['tolerance_fraction']):
    for lt in (-lr['tolerance_fraction'],lr['tolerance_fraction']):
     for i in range(1001):
      row=wiper(i/1000,nominal*(1+rt),low,high,1000*(1+st),1e7*(1+lt));row.update(pot_fraction=rt,series_fraction=st,load_fraction=lt);rows.append(row)
  worst=max(rows,key=lambda x:abs(x['error_V']))
  result[label]={'worst_sampled_row':worst,'output_error_V':abs(worst['error_V'])*(2 if label=='atten'else 1),'scope':'Candidate resistor tolerance corners plus retained Bourns ±20% end-to-end resistance at room temperature; finite position grid. Track linearity, contact resistance/noise, temperature and amplifier errors excluded; not assembled bound.'}
 return result

def build():
 paths=[OUT/'electrical-input.json',prior.OUT/'inventory-report.json',prior.OUT/'interfaces-report.json',prior.OUT/'electrical-report.json']
 data=[json.loads(p.read_text())for p in paths];result=analyze(*data)
 identity_path=OUT/'identity-report.json';identity=json.loads(identity_path.read_text());paths.append(identity_path)
 for report in data[1:]+[identity]:
  for name,digest in report['source_sha256'].items():need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'stale source '+name)
 raw=ROOT/'.circuit-cache/sources/architecture278-stage11-identity/ref50.pdf'
 if raw.exists():need(hashlib.sha256(raw.read_bytes()).hexdigest()==data[0]['REF5050_primary_evidence']['sha256'],'REF5050 inspected bytes')
 result['candidate_tolerance_sensitivity']=tolerance_sensitivity(identity)
 support_path=OUT/'support-report.json';support=json.loads(support_path.read_text());paths.append(support_path)
 for name,digest in support['source_sha256'].items():need(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'stale support '+name)
 feed_alternative(result,support,data[2],data[3])
 for name in ('b103','b104'):
  for file in ('facts.json','sources.json'):paths.append(ROOT/f'.claude/skills/component-bourns-ptv09a-4020f-{name}'/file)
 paths += [Path(__file__),Path(__file__).with_name('test_stage11_electrical.py'),ROOT/'design/spec/modules/offset.py',ROOT/'design/partition/partition-input.json',ROOT/'scripts/checks/partition35.py',ROOT/'design/architecture-278/electrical.md',ROOT/'design/architecture-278/GATE.md',ROOT/'design/architecture-278/intake/revision-2/issue-282.json']
 for name in ('ti-ref5050aidr','ti-opa4197ipwr','ti-opa4196idr','ti-lm393bidr'):
  for filename in ('facts.json','sources.json'):paths.append(ROOT/f'.claude/skills/component-{name}'/filename)
 result['new_REF5050_primary_evidence']=data[0]['REF5050_primary_evidence']
 result['primary_evidence']={p.parent.name:json.loads(p.read_text())for p in paths if p.name=='sources.json'}
 result['primary_facts']=data[3]['conditional_budgets']['primary_facts']
 result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();text=json.dumps(r,indent=2,sort_keys=True)+'\n';path=OUT/'electrical-report.json'
 if args.check:need(path.read_text()==text,'stale electrical report')
 else:path.write_text(text)
 print('Stage11 electrical source arithmetic PASS; hardware UNKNOWN')
if __name__=='__main__':main()
