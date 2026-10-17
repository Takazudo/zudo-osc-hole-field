"""Source-bound candidate passive identities; no canonical assignment or native calls."""
import argparse,hashlib,json,math,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'design/architecture-278/implementation/stage11'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def analyze(spec,inventory):
 selected=spec['selections'];need(set(selected)==set(inventory['unselected_MPN_refs'])and len(selected)==20,'all20 unspecified source identities')
 rows={};refs_by_mpn={}
 for ref,choice in selected.items():
  source=inventory['packages'][ref];need(not source['attributes']['MPN'],'source identity already assigned')
  need(choice['role']==source['attributes']['Role'],'source role drift '+ref)
  need(choice['captured_pins']==source['pins']and choice['captured_footprint']==source['footprint']and choice['captured_value']==source['unit_records'][0]['value'],'source value/pin/footprint drift '+ref)
  mpn=choice['candidate_MPN'];part=spec['parts'][mpn];evidence=spec['sources'][part['source_id']]
  need(part['source_id']==mpn and evidence['url']=='https://www.yageogroup.com/component-documentation/download/specsheet/'+mpn,'exact source identity URL')
  need(evidence['physical_pdf_page_index']==0 and evidence['printed_page_label']=='unlabelled','exact specsheet locator')
  need(re.fullmatch('[0-9a-f]{64}',evidence['sha256'])and evidence['sha256']!='0'*64 and evidence['availability']=='AVAILABLE','retained primary digest')
  need(part['candidate_only']is True and part['supplier_order_code']is None,'candidate/sourcing boundary')
  value=float(choice['captured_value'].split()[0]);tol=part['tolerance_fraction']
  need(part['kind']==ref[0]and math.isclose(value,part['value_SI'],rel_tol=1e-12,abs_tol=0),'candidate changed nominal value')
  need(math.isfinite(tol)and 0<tol<1,'finite nonzero tolerance')
  row={'ref':ref,'candidate_MPN':mpn,'captured_value':choice['captured_value'],'pins':source['pins'],'role':choice['role'],'footprint':source['footprint'],'candidate_ratings':part,'component_nominal_tolerance_interval_SI':[value*(1-tol),value*(1+tol)],'source_id':part['source_id'],'identity_status':'Exact primary-document candidate identified; not adopted or procured','fit_status':'Existing0603 footprint preserved; package dimensions are evidence, not qualified landpattern/assembly'}
  if part['kind']=='R':
   power=part['power_W_at_70C'];voltage=part['maximum_continuous_voltage_V'];need(power==.1 and voltage==75,'reviewed resistor rating conditions')
   row['conditional_70C_limits']={'power_W':power,'resistive_working_voltage_bound_V':min(voltage,math.sqrt(power*value*(1-tol))),'formula':'min(75V,sqrt(P70*Rminimum)); not permission to apply this voltage in circuit','hotter_than_70C_power_W':None}
  else:
   need(part['rated_voltage_V']>0 and part['effective_capacitance_at_bias_F']is None and part['ESR_ohm']is None,'capacitor application unknowns cannot become guarantee')
  rows[ref]=row;refs_by_mpn.setdefault(mpn,[]).append(ref)
 need(sum(r['candidate_ratings']['kind']=='R'for r in rows.values())==17,'17 resistor roles')
 cap=rows['C7102'];app=spec['REF5050_application'];need(app['device']=='REF5050AIDR'and app['source_id']=='REF50-app','exact reference application')
 need(app['output_cap_range_F']==[1e-6,50e-6]and app['stability_ESR_max_ohm']==1.5,'reviewed AI-grade output capacitor conditions')
 need(cap['candidate_ratings']['dielectric']=='X7R'and rows['C7104']['candidate_ratings']['dielectric']=='C0G','reviewed capacitor dielectric')
 tolerance_min=cap['component_nominal_tolerance_interval_SI'][0]
 reference={'C7102_candidate_MPN':cap['candidate_MPN'],'nominal_F':cap['candidate_ratings']['value_SI'],'tolerance_only_min_F':tolerance_min,'application_output_min_F':app['output_cap_range_F'][0],'tolerance_only_establishes_application_min':tolerance_min>=app['output_cap_range_F'][0],'effective_C_at_5V_temperature_aging_F':None,'ESR_ohm':None,'verdict':'NEEDS BENCH / DESIGN GAP: identity resolved, output-cap application not established','noise_ESR_recommendation_distinct_from_stability_limit':True,'next_bounded_recommendation':'Evaluate a larger nominal output capacitor with exact manufacturer effective-C/ESR data and source-stage value-change review; do not silently replace captured1uF.'}
 input_caps=[]
 for ref in ('C7101','C7107'):
  p=inventory['packages'][ref];need(p['pins']=={'1':'+12V','2':'AGND'},'reference input bypass topology');v,unit=p['unit_records'][0]['value'].split();need(unit in ('F','nF','µF'),'known capacitor value unit');input_caps.append(float(v)*{'F':1,'nF':1e-9,'µF':1e-6}[unit])
 reference['input_bypass_nominal_F']=sum(input_caps);reference['recommended_input_bypass_F']=app['recommended_input_bypass_F'];reference['input_bypass_recommendation_established']=sum(input_caps)>=app['recommended_input_bypass_F'][0]
 need(inventory['packages']['RV1308']['attributes']['MPN']=='PTV09A-4020F-B104','captured RV1308 identity drift')
 history=spec['RV1308_history'];need(len(history)==3 and all(h['commit']and h['blob_sha256']and h['excerpt']for h in history),'bounded history evidence')
 return {'status':'20 EXACT PASSIVE CANDIDATES; APPLICATION AND HARDWARE ACCEPTANCE OPEN','candidate_assignments':rows,'references_by_candidate_MPN':refs_by_mpn,'counts':{'source_refs':20,'resistors':17,'capacitors':3,'distinct_candidate_MPNs':len(refs_by_mpn)},'reference_capacitor_application':reference,'RV1308_history':history,'RV1308_conclusion':spec['RV1308_conclusion'],'sources':spec['sources'],'retrieval_failures':spec['retrieval_failures'],'remaining_unknowns':spec['global_unknowns'],'source_values_changed':False,'canonical_BOM_changed':False,'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
def build():
 files=[OUT/'identity-input.json',OUT.parent/'stage10/inventory-report.json'];spec,inventory=[json.loads(p.read_text())for p in files];result=analyze(spec,inventory)
 files += [Path(__file__),Path(__file__).with_name('test_stage11_identity.py')]
 result['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();body=json.dumps(build(),sort_keys=True,indent=2)+'\n';dest=OUT/'identity-report.json'
 if args.check:need(dest.read_text()==body,'stale Stage11 identity report')
 else:dest.write_text(body)
 print('20exact candidate identities; REF5050 output/input capacitance application gaps retained')
if __name__=='__main__':main()
