"""A01 resistance-domain reconciliation and coherent conditional DC/CV budget.
No solver, simulator, native tool, altered circuit or new acceptance authority.
"""
import argparse,hashlib,json,math,itertools
from pathlib import Path
import stage11_electrical as old
ROOT=old.ROOT;OUT=old.prior.a.OUT/'stage12'
need=old.need
DOMAIN={
'local_source_copper':['PCB_spreading_necks_vias'],
'local_return_join':['PCB_spreading_necks_vias'],
'local_transport_branch':['PCB_spreading_necks_vias'],
'middle_copper':['PCB_spreading_necks_vias'],
'middle_power_copper':['PCB_spreading_necks_vias'],
'middle_AGND_copper':['PCB_spreading_necks_vias'],
'LED_local_copper':['PCB_spreading_necks_vias'],
'GH_harness':['wire','crimp_termination','GH_mated_contact','GH_header_pin_termination'],
'DIN_mated_pair':['DIN_mated_contact','DIN_pin_termination'],
'permanent_terminal_wire':['wire','permanent_termination']}
def transfer(vin,cv,a,x,*,rp=100000,ra=10000,rseries=1000,rload=1e7,ref=5,kn=1,ka=1,ga=1,gm=1,gcv=1,gr=1,errors=None):
 errors=errors or {};get=lambda k:errors.get(k,0)
 need(all(math.isfinite(v)for v in [vin,cv,a,x,rp,ra,rseries,rload,ref,kn,ka,ga,gm,gcv,gr,*errors.values()])and 0<=a<=1 and 0<=x<=1,'finite transfer state')
 b=vin+get('IN_buffer');remote=b+get('remote_buffer')
 attenw=old.wiper(a,ra,0,remote,rseries,rload)['sense_V']
 atten=(1+ka)*(attenw+get('atten_amp'))-ka*b
 high=ref+get('REF_positive');low=-kn*high+(1+kn)*get('REF_negative')
 manual=old.wiper(x,rp,low,high,rseries,rload)['sense_V']+get('manual_amp')
 c=cv+get('CV_buffer');summer=-(ga*atten+gm*manual+gcv*c)+(1+ga+gm+gcv)*get('summer')
 internal=-gr*summer+(1+gr)*get('restore');output=internal+get('output')
 return {'out_V':output,'internal_V':internal,'reference_high_V':high,'reference_low_V':low,'atten_V':atten,'manual_V':manual,'ideal_control_law_V':(2*a-1)*vin+(2*x-1)*5+cv}
def coefficients(a,x):
 beta=old.wiper(a,10000,0,1)['sense_V'];damp=1e7/(1e7+1000+100000*x*(1-x))
 return {'IN_buffer':2*beta-1,'remote_buffer':2*beta,'atten_amp':2,'manual_amp':1,'CV_buffer':1,'summer':-4,'restore':2,'output':1,'REF_positive':damp*(2*x-1),'REF_negative':damp*2*(1-x)}
def resistor_corner_cases(inv):
 refs=['R7117','R7118','R7121','R7122','R7123','R7124','R7125','R7126','R7101','R7102']
 facts=json.loads((ROOT/'.claude/skills/component-passives-family/facts.json').read_text())['facts']
 fact=next(f for f in facts if f['fact_id']=='fact-r-precision-resistance')
 need(fact['value']=={'nominal':100000,'tolerance_percent':.1}and fact['verdict']=='PASS - primary-source confirmed','exact100k tolerance evidence')
 candidate=json.loads((old.OUT/'identity-report.json').read_text())['candidate_assignments']
 for r in refs[:8]:
  need(inv['packages'][r]['attributes']['MPN']=='RT0603BRD07100KL','exact precision resistor '+r)
  value=inv['packages'][r]['unit_records'][0]['value'];need(value in ('100000 Ω','100 kΩ'),'actual100k source '+r)
 for r in refs[8:]:
  q=candidate[r];need(q['candidate_ratings']['value_SI']==10000 and q['candidate_ratings']['tolerance_fraction']==.001 and q['pins']==inv['packages'][r]['pins'],'candidate10k source '+r)
  need(inv['packages'][r]['unit_records'][0]['value']=='10000 Ω','actual10k source '+r)
 states=[(5,0,1,.5),(5,0,0,.5),(0,0,.5,0),(0,0,.5,1),(1,1,.75,.75)]
 result=[]
 for vin,cv,a,x in states:
  values=[]
  for signs in itertools.product((-1,1),repeat=10):
   R=dict(zip(refs,[1+.001*k for k in signs]))
   # One physical feedback resistor R7124 is shared by all three summer ratios.
   params={'ka':R['R7118']/R['R7117'],'ga':R['R7124']/R['R7121'],'gm':R['R7124']/R['R7122'],'gcv':R['R7124']/R['R7123'],'gr':R['R7126']/R['R7125'],'kn':R['R7102']/R['R7101']}
   r=transfer(vin,cv,a,x,**params);values.append({'out_V':r['out_V'],'error_V':r['out_V']-r['ideal_control_law_V'],'physical_resistor_fraction':dict(zip(refs,[.001*k for k in signs]))})
  result.append({'vin_V':vin,'offset_CV_V':cv,'atten_position':a,'offset_position':x,'physical_corner_count':1024,'minimum_error':min(values,key=lambda r:r['error_V']),'maximum_error':max(values,key=lambda r:r['error_V']),'scope':'Coherent ten-physical-resistor tolerance corners, not independent summer-ratio extrema. Nominal pots/1k/10M; reference source and opamp errors excluded. Candidate R7101/2 evidence fromStage11; retained100k0.1% exactprimary. No calibration removal assumed.'})
 return result

def bias_terms(a,x):
 za=1/(1/(1000+10000*a*(1-a))+1/1e7)
 zm=1/(1/(1000+100000*x*(1-x))+1/1e7)
 damp=1e7/(1e7+1000+100000*x*(1-x))
 return {'conditional_input_current_A':15e-9,'conditions':'Retained OPA4197 PW full-temperature inputbias specification at stated midsupply testconditions. These are current-to-error sensitivities, not guaranteed assembled errors for every ±5V commonmode.','known_linear_coefficients_V_per_A':{'atten_noninverting_bias':-2*za,'manual_noninverting_bias':-zm,'atten_inverting_bias':100000,'summer_inverting_bias':-100000,'restore_inverting_bias':100000,'remote_inverting_bias':2*old.wiper(a,10000,0,1)['sense_V']*10000,'REF_negative_inverting_bias':damp*(1-x)*10000,'output_inverting_bias':100},'unknown_coefficients':['IN_buffer positive:10k plus external/protection source impedance','CV_buffer positive:10k plus external/protection source impedance','REF_positive positive:REF5050 dynamic/DC output impedance','remote/restore/output/reference ground and feedback-source impedances','follower feedback input currents through actual output/return impedance'],'rule':'Each coefficient multiplies its actual pin current once, signed for coherent state or absolute for independently bounded pin currents. Do not add as voltageoffset again; no unqualified allpin15nA wholecell guarantee.'}

def edge_domains(kind):
 need(kind in DOMAIN,'unclassified resistance edge '+kind);return DOMAIN[kind]
def mapping(graph,previous,inv):
 expected={f'{ref}:{pin}':net for ref,p in inv['packages'].items()for pin,net in p['pins'].items()if net in ('AGND','+12V','-12V','+5V')}
 rows=previous['power_and_return_endpoint_paths'];need(len(rows)==106 and {r['to']:r['net']for r in rows}==expected,'all106 actual source endpoints')
 usage={}
 for row in rows:
  for i in row['edge_indices']:usage[i]=usage.get(i,0)+1
 out=[]
 for row in rows:
  here=row['source_boundary'];terms=[]
  for i in row['edge_indices']:
   e=graph['edges'][i];need(e['net']==row['net']and here in (e['from'],e['to']),'continuous actual path')
   here=e['to']if here==e['from']else e['from']
   terms.append({'edge_index':i,'kind':e['kind'],'domains':edge_domains(e['kind']),'from':e['from'],'to':e['to'],'allocated_mm':e['allocated_developed_mm'],'wire_max_mm':e['wire_cut_max_mm'],'GH_contacts':e['mated_GH_contacts'],'DIN_contacts':int(e['kind']=='DIN_mated_pair'),'endpoint_walk_use_count':usage[i],'resistance_ohm':None,'shared_current_A':None})
  need(here==row['to']and graph['nodes'][here]['net']==row['net'],'actual endpoint net')
  out.append({'to':row['to'],'net':row['net'],'source_boundary':row['source_boundary'],'source_pad_xyz_mm':graph['nodes'][here]['pad_xyz_mm'],'edge_terms':terms,'upstream_source_feed':{'domain':'upstream_source_feed','resistance_ohm':None,'regulation_error_V':None},'original_plane_requirement':{'limit_ohm':.0005 if row['net']=='AGND'else .001,'applies_to':'Combined applicable PCB spreading/necks/vias domain across boards, not each edge and not contacts/wires','applicability':'Mapping to split A01 boards requires review; source value preserved'},'expanded_architecture_comparison':{'limit_ohm':.0005 if row['net']=='AGND'else .001,'applies_to':'Broader complete branch/common or rail transfer wording; unresolved conflict of domains','accepted_redefinition':False},'complete_transfer_error_V':None})
 return out

def criteria(standard,partition,inp):
 cal=standard['calibration'];dist=partition['load_distribution']
 cells={c['id']:c for c in standard['cells']}
 need(cal['warmup_minutes']==20,'retained warmup changed')
 need(standard['signals']['minimum_output_load_ohm']==10000 and standard['signals']['clip_internal_threshold_V']==[-10,10],'retained load/clip criteria changed')
 need(any('endpoint/centre gain tolerance target 0.5%'in n for n in cells['bipolar_attenuverter']['notes']),'atten criterion source changed')
 need(any('10 nF wiper filter' in n and '0.26 ms' in n for n in cells['dc_control_source']['notes']),'manual timing source changed')
 need((dist['return_plane_resistance_ceiling_ohm'],dist['rail_plane_resistance_ceiling_ohm'])==(.0005,.001),'original plane limits changed')
 need(cal['static_precision_error_V']==.002 and cal['precision_output_load_error_V']==.001 and cal['pitch_tracking_target_cents']==5,'retained error criteria changed')
 return {'original_plane':{'return_ohm':.0005,'rail_ohm':.001,'source':'design/partition/partition-input.json#/load_distribution','producer':'scripts/checks/partition35.py rwire/rp/rg and alternative-return formulas','original_commit':'ffe487d7','domain':'PCB only; producer adds wire and termination separately; no GH resistance waiver or artificial per-board reset'},'distribution':{'hot_distribution_V':.020,'complete_path_V':.20,'GH_contact_A':.5,'source':'design/architecture-278/GATE.md; partition35.py','scope':'Separate voltage/current constraints, not resistance or precision error synonyms'},'static':{'target_V':.002,'source':'design/standard/electrical-standard.json#/calibration/static_precision_error_V','status':'Retained project PROPOSAL/NEEDS BENCH','scope':'Calibrated static precision target; exact A01 calibration state/grid and included terms remain unresolved'},'output_load_change':{'target_V':.001,'source':'design/standard/electrical-standard.json#/calibration/precision_output_load_error_V','scope':'Output change open-to10k at -5/0/+5V; not total control-law or reference error'},'attenuverter':{'endpoint_centre_gain_target_fraction':.005,'source':'electrical-standard.json cells[id=bipolar_attenuverter].notes','scope':'Endpoint/centre target; centre trimmed by knob; not full-position calibrated absolute accuracy'},'pitch':{'cents':5,'voltage_equivalent_V':5/1200,'warmup_minutes':20,'scope':cal['pitch_tracking_scope'],'source':'electrical-standard.json#/calibration','A01_pitch_acceptance':'NOT ESTABLISHED; owner-defined cents tolerance still required for A01 pitch-CV service'},'ideal_AO_runner':{'criterion_V':.001,'source':'design/spec/modules/run_offset_spice.py run_case assertion','scope':'Seven ideal unlimited-rail wiring algebra cases, not complete A01 or physical acceptance','executed':False},'clip_indication':{'nominal_internal_threshold_V':standard['signals']['clip_internal_threshold_V'],'source':'electrical-standard.json#/signals/clip_internal_threshold_V','scope':'Comparator/half-output threshold; actual reference/offset/slew/noise/propagation limits remain unknown. Not a pitch-CV error target.'},'timing':{'A01_settling_target_s':None,'source':'dc_control_source notes: existing variable10nF filter; run_offset_spice onlyDC','scope':'No A01-specific accepted numerical settling/noise bandwidth recovered. X1 400us criterion is not imported.'},'new_proposals':inp['proposals'],'recommended_domain_mapping':{'status':'PROPOSED/UNAPPROVED; no existing check changed','mapping':'Retain0.5mohm combined PCB return-spreading/necks/vias and1mohm combined PCB rail-transfer domain. Add connector/crimp/wire/source terms separately for20mV distribution and0.20V fullpath; retain0.5A actualGHcontactcurrent. Evaluate DC/CV accuracy from actual source/receiver ground differences and circuit gain, not by assigning entire2mV/5cents toAGND.','architecture_resolution':'Recommend explicit owner-reviewed clarification of expanded wholebranch wording; until adopted preserve both historical checks and report applicability unresolved, not a pass or silent waiver.'}}
def build_report(inp,inv,graph,previous,standard,partition):
 need(inp['instance']=='A01'and inp['new_criteria_approved']is False,'bounded unapproved criteria')
 need(inv['packages']==json.loads((old.prior.OUT/'inventory-report.json').read_text())['packages'],'live retained inventory')
 captured=json.loads((old.OUT/'electrical-input.json').read_text())
 for ref,pins in captured['source_pin_bindings'].items():need(inv['packages'][ref]['pins']==pins,'retained fullpin topology '+ref)
 for ref,value in captured['source_value_bindings'].items():need(inv['packages'][ref]['unit_records'][0]['value']==value,'retained scalar source '+ref)
 rows=[]
 for vin in (-5,0,5):
  for cv in (-5,0,5):
   for a in (0,.25,.5,.75,1):
    for x in (0,.25,.5,.75,1):
     r=transfer(vin,cv,a,x);coef=coefficients(a,x)
     rows.append({'vin_V':vin,'offset_CV_V':cv,'atten_position':a,'offset_position':x,**r,'control_law_error_V':r['out_V']-r['ideal_control_law_V'],'offset_coefficients':coef,'bias_current_terms':bias_terms(a,x),'conditional_100uV_each_offset_envelope_V':sum(abs(c)for c in coef.values())*.0001,'all_input_errors_sum_method':'Signed coefficients for correlated scenarios; independent bounded terms use sum of absolute contributions. Raw-reference error enters REF_positive coefficient once; do not count same source again at REFN5.','headroom_established':False})
 return {'status':'A01 SOURCE BUDGET; ACCEPTANCE UNRESOLVED','criteria':criteria(standard,partition,inp),'resistance_endpoint_mapping':mapping(graph,previous,inv),'resistance_accounting':{'expression':'DeltaVhot=sum(Iedge*Redge); DeltaVreturn=sum(signed Ireturn_edge*Redge), worst-case from declared state envelopes without cancellation credit; source regulation plus hotloss plus returnshift plus transient separately','catalog_contact_scope':'Retained GH catalog contact measurement does not automatically include installedcrimp,wire or board solderjoint. Exact measurementplanes required before adding/subtracting terms; avoid doublecounting internal conductor portions.', 'complete_loop':'Per-endpoint source-to-pad reachability is not a closed supply/return qualification. Complete upstream hotfeed and returnfeed, sharedreturn topology and source regulation must all be supplied.', 'shared_edges':'Edge identity reused in multiple endpoint walks is one physical conductor. endpoint_walk_use_count is not current multiplicity; add actual downstream load once.','original_checks_preserved':True,'equal_sharing_credit':False,'stage11_strap_option':'Frozen comparison only; no new geometry/material/contact elaboration and no substitution into baseline graph.'},'coherent_DC_cases':rows,'coherent_physical_resistor_corners':resistor_corner_cases(inv),'calibration_accounting':{'actual_actuators':'Two fixed user pots; no added calibration trimmers or per-instance digital correction.','potentially_adjustable':'User knob can null one observed output state if within range; repeatability and reference/load changes unqualified. This is not factory multi-point correction.','not_removed_by_assumption':['gain-ratio errors across IN/CV paths','position-dependent wiper loading and track law','reference drift/noise','load/return/state-dependent errors','output clipping and recovery'],'unresolved':'No accepted A01 calibration algorithm, trim authority, testgrid/temperature/load, or postcal residual bound recovered.2mV target does not prove those facilities exist.'},'input_boundaries':{'vin_definition':'Coherent algebra starts at ideal buffered IN/OFFSET stimulus; raw source and front protection errors are additional explicit terms, not silently zero.','physical_chain':'External source impedance→jack tip/factorytail→ADG5412F protected switch→IN_PROTECTED/OFFSET_PROTECTED;100k pulldown R7107/R7111,10k sense R7108/R7112→OPA4197 follower→IN_BUFFER/OFFSET_BUFFER.','unknown_terms':['external source impedance and cable leakage/capacitance','ADG on-resistance/nonlinearity/leakage and powered/off fault-state protection','100k pulldown loading against external source impedance','10k sense resistor times actual input bias plus protection/switch/external source impedance','input commonmode/offset/load dependence and startup/clamp injection'],'gain_to_output':'IN_BUFFER error times(2*loaded_beta−1), OFFSET_BUFFER error times1 atnominalratios; use actual correlated transfer for ratio corners.','nominal_input_range_V':[-5,5],'survival_not_linear_range_V':[-12,12]},'budget_terms':{'modeled_control_law':'Exact nominal loadedwiper/reference inversion/attenuator/summer/restore DC algebra, conditioned on linear amplifiers and exactratios','opamp_offset':'All ten used precision-stage coefficients included.100uV is retained±18V25C evidence sensitivity, not±12V wholecell guarantee. Input bias, referenceaccuracy, noise, drift, gain ratios and return errors remain distinct unknown terms.','reference_ratio':'Stage11 candidate R7101/R7102 independent0.1% corner error adds to manualpath using actual lowreference coefficient; not blindly added to unrelated CVinput.','gain_ratios':'Individual precision100k resistors (not guaranteed matched networks) and actualcandidate resistor correlations/TCR require exactcomponent evidence; no invented universal ratio bound.','output_load':'Compare same setting open-to10k; subtracting cancels common static terms only when their load/state dependence is demonstrated.998ohm feedforward drop is feedback-corrected while linear, so not itself residualerror.','return':'Source/receiver reference node difference propagates through actual gain coefficient; no single current or universal coefficient for all AGND paths.','timing':'10nF existingmanualfilter and variableTheveninR give nominalsimpletau up to259.326us; settlingthreshold andfullmultilooptransfer unknown.'},'complete_error_bound_V':None,'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
def build():
 paths=[OUT/'budget-input.json',old.prior.OUT/'inventory-report.json',old.prior.OUT/'interfaces-report.json',old.prior.OUT/'electrical-report.json',ROOT/'design/standard/electrical-standard.json',ROOT/'design/partition/partition-input.json']
 result=build_report(*[json.loads(p.read_text())for p in paths])
 paths += [Path(__file__),Path(__file__).with_name('test_stage12_budget.py'),ROOT/'scripts/checks/partition35.py',ROOT/'design/architecture-278/GATE.md',ROOT/'design/architecture-278/electrical.md',ROOT/'design/spec/modules/offset.py',ROOT/'design/spec/modules/run_offset_spice.py',ROOT/'design/standard/offset-model-source-work-note.md',ROOT/'doc/src/content/docs/architecture/osc-block-ao.mdx',ROOT/'.claude/skills/component-ti-opa4197ipwr/facts.json',ROOT/'.claude/skills/component-ti-opa4197ipwr/sources.json',ROOT/'.claude/skills/component-passives-family/facts.json',ROOT/'.claude/skills/component-passives-family/sources.json',old.OUT/'identity-report.json',OUT/'criteria-history.json',old.OUT/'electrical-report.json',old.OUT/'electrical-input.json']
 result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';out=OUT/'budget-report.json'
 if args.check:need(out.read_text()==text,'stale Stage12 budget')
 else:out.write_text(text)
 print('PASS Stage12 source budget; complete electrical acceptance UNKNOWN')
if __name__=='__main__':main()
