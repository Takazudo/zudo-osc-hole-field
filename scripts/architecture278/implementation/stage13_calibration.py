"""Existing A01 control feasibility, not a new calibration system or simulation."""
import argparse,hashlib,json,math
from pathlib import Path
import stage12_budget as prior
ROOT=prior.ROOT;OUT=prior.old.prior.a.OUT/'stage13';need=prior.need

def observe(params,a,x):
 b=prior.transfer(0,0,a,x,**params)['out_V']
 return {'IN_gain':prior.transfer(1,0,a,x,**params)['out_V']-b,'CV_gain':prior.transfer(0,1,a,x,**params)['out_V']-b,'offset_V':b}
def control_sensitivity(params,a,x):
 ra=params.get('ra',10000);rp=params.get('rp',100000);series=params.get('rseries',1000);load=params.get('rload',1e7)
 ga=params.get('ga',1);gm=params.get('gm',1);gr=params.get('gr',1);ka=params.get('ka',1);kn=params.get('kn',1);errors=params.get('errors',{})
 D=load+series+ra*a*(1-a);dbeta=load*(D-a*ra*(1-2*a))/D**2
 high=params.get('ref',5)+errors.get('REF_positive',0);low=-kn*high+(1+kn)*errors.get('REF_negative',0)
 M=load+series+rp*x*(1-x);dmanual=load*((high-low)*M-(low+(high-low)*x)*rp*(1-2*x))/M**2
 return [[gr*ga*(1+ka)*dbeta,0],[0,0],[gr*ga*(1+ka)*dbeta*(errors.get('IN_buffer',0)+errors.get('remote_buffer',0)),gr*gm*dmanual]]

def bounded_setting(fn,target):
 lo,hi=fn(0),fn(1);need(math.isfinite(target)and math.isfinite(lo)and math.isfinite(hi)and hi>lo,'finite monotone setting')
 if target<lo:return {'setting':0.,'reachable':False,'target':target,'achieved':lo,'interval':[lo,hi]}
 if target>hi:return {'setting':1.,'reachable':False,'target':target,'achieved':hi,'interval':[lo,hi]}
 left,right=0.,1.
 for _ in range(60):
  middle=(left+right)/2
  if fn(middle)<target:left=middle
  else:right=middle
 x=(left+right)/2
 return {'setting':x,'reachable':True,'target':target,'achieved':fn(x),'interval':[lo,hi]}
def fit_only(params,a,x,target_gain):
 obs=observe(params,a,x)
 return {'fitted_IN_gain':obs['IN_gain'],'fitted_CV_gain':obs['CV_gain'],'fitted_offset_V':obs['offset_V'],'fitted_correction':'y_corrected=y−(G_IN−target_gain)*VIN−(G_CV−1)*CV−B','mathematical_model_residual_V':0.,'realized_in_hardware':False,'scope':'Three-parameter characterization from independent IN/CV/zero observations; correction requires unavailable independent input corrections. Perfect fitted algebra is not calibration hardware or measured residual.'}
def check_case(params,gain):
 aset=bounded_setting(lambda a:observe(params,a,.5)['IN_gain'],gain)
 xset=bounded_setting(lambda x:observe(params,aset['setting'],x)['offset_V'],0)
 a,x=aset['setting'],xset['setting'];obs=observe(params,a,x);rows=[]
 for vin in (-5,0,5):
  for cv in (-5,0,5):
   tr=prior.transfer(vin,cv,a,x,**params);ideal=gain*vin+cv
   rows.append({'vin_V':vin,'CV_V':cv,'actual_loaded_model_V':tr['out_V'],'target_V':ideal,'residual_V':tr['out_V']-ideal,'ideal_within_supply_rails':abs(tr['internal_V'])<12,'actual_headroom_proven':False,'output_load_change_V':None})
 return {'requested_gain':gain,'atten_setting':aset,'offset_setting':xset,'observed_coefficients':obs,'actual_control_jacobian':control_sensitivity(params,a,x),'residuals':rows,'maximum_abs_DC_model_residual_V':max(abs(r['residual_V'])for r in rows),'CV_only_residual_at5V':5*(obs['CV_gain']-1),'mathematical_fit':fit_only(params,a,x,gain),'load_criterion_met':None,'complete_static_criterion_met':None,'scope':'Existing knobs set a temporary operating point only; not retained correction when user changes either control. Bounds include nominal potloading and selected physicalresistor corners, not taper/contact/setting-resolution guarantees.'}
def parameter_cases(report):
 cases={'nominal':{}};refs=['R7117','R7118','R7121','R7122','R7123','R7124','R7125','R7126','R7101','R7102']
 for i,row in enumerate(report['coherent_physical_resistor_corners']):
  for label in ('minimum_error','maximum_error'):
   fractions=row[label]['physical_resistor_fraction'];need(set(fractions)==set(refs)and all(abs(v)==.001 for v in fractions.values()),'retained physical corner')
   R={r:1+fractions[r]for r in refs}
   cases[f'stage12_case{i}_{label}']={'ka':R['R7118']/R['R7117'],'ga':R['R7124']/R['R7121'],'gm':R['R7124']/R['R7122'],'gcv':R['R7124']/R['R7123'],'gr':R['R7126']/R['R7125'],'kn':R['R7102']/R['R7101']}
 return cases

def analyze(inp,report,inv):
 need(inp['instance']=='A01'and inp['new_hardware'] is False and inp['fitted_correction_is_hardware'] is False,'no invented calibration hardware')
 need(inp['actual_controls']=={'ATTEN':'RV1307','OFFSET':'RV1308'}and inp['physical_setting_interval']==[0,1],'only existing bounded controls')
 need(inv['packages']['RV1307']['unit_records'][0]['value']=='PTV09A-4020F-B103'and inv['packages']['RV1308']['unit_records'][0]['value']=='PTV09A-4020F-B104','exact captured controls')
 need(inp['requested_gains']==[-1,0,1],'retained endpoint/centre observations')
 need(report['criteria']['static']['target_V']==.002 and report['criteria']['output_load_change']['target_V']==.001,'distinct retained criteria')
 cases=[]
 for name,params in parameter_cases(report).items():
  observations=[{'a':a,'x':x,**observe(params,a,x)}for a in (0,.5,1)for x in (0,.5,1)]
  cases.append({'name':name,'params':params,'unadjusted_control_observations':observations,'bounded_presets':[check_case(params,g)for g in inp['requested_gains']]})
 saturation=[]
 for gain in (-1,1):
  for sign in (-1,1):
   tr=prior.transfer(sign*5,sign*5,(gain+1)/2,1 if sign==1 else 0)
   saturation.append({'gain_setting':gain,'vin_V':sign*5,'CV_V':sign*5,'manual_pot_setting':1 if sign==1 else 0,'mathematical_output_V':tr['out_V'],'over_supply_rail':abs(tr['out_V'])>=12,'hardware_output_V':None,'scope':'No saturation model; any overrail demand is excluded from linear correction/acceptance. Actual clipping threshold/recovery remains unknown.'})
 return {'status':'A01 EXISTING-CONTROL FEASIBILITY; NOT CALIBRATION ACCEPTANCE','existing_controls':inp['actual_controls'],'case_coverage':'Nominal plus ten retained Stage12 extremizing physicalresistor witnesses; not an exhaustive all-error tolerance envelope. The knobs are modeled electricalfractions, not measured shaftangles or markings. Track/taper/contactresolution and mechanicalrepeatability remain unqualified.','observability':{'observed_parameters':['IN_gain','CV_gain','offset_V'],'control_jacobian_structure':[['dG_IN/da',0],[0,0],['dB/da','dB/dx']],'generic_control_rank':2,'single_zero_input_observation_rank':1,'unadjustable_mode':'CV_gain=gr*gcv independent of both knob settings','mathematical_identification_rank':3,'scope':'Independent VIN,CV and zero observations identify three affine parameters; two knobs cannot independently set all three. This is algebraic rank, not metrological conditioning or potresolution proof.'},'documented_observation_map':{'ATTEN_centre_and_endpoints':{'model':'Unadjusted9controlposition observations plus boundedrequestedgain−1/0/+1 presets','adjustment':'ATTEN changes operatinggain; cannot independently trim both physicalendpoints andcentre'},'OFFSET_CV_unity':{'model':'CV_gain=gr*gcv independently observable','adjustment':'NONE; bothcontrol derivatives exactlyzero'},'manual_midpoint_endpoints':{'model':'Offset coefficient atx0/.5/1 captured for eachcorner','adjustment':'OFFSET changes operatingintercept; no independent mid/span/endpointtrims'},'output_DC':{'model':'B(x) can be nulled atonezero-input state ifrange permits','adjustment':'TemporaryOFFSETsetting only, not correctionofgain/load/drift'},'output_load_and_drift':{'model':'UNKNOWN; no outputload/temperaturebehavior in retainedDCmodel','adjustment':'NONE independent; no 1mVload or2mVstatic acceptance'},'clip_thresholds':{'model':'Nominal±10V internalhalf-output comparators; actual reference/offset/hysteresis/timing UNKNOWN','adjustment':'NONE; usercontrols change signal, not comparatorreference or threshold calibration'}},'cases':cases,'offset_coupling_examples':[{'scope':'Conditional100uV illustrative input/remote/manual/output offsets, not actual guaranteedcell bound','params':{'errors':{'IN_buffer':.0001,'remote_buffer':.0001,'manual_amp':.0001,'output':.0001}},'preset':check_case({'errors':{'IN_buffer':.0001,'remote_buffer':.0001,'manual_amp':.0001,'output':.0001}},0)},{'scope':'Deliberate out-of-range6V intercept stress to exercise boundedcontrol logic; not a normal deviceoffset prediction','params':{'errors':{'output':6}},'preset':check_case({'errors':{'output':6}},0)}],'saturation_cases':saturation,'criteria':{'static_target_V':.002,'load_induced_target_V':.001,'source':'Stage12 retained criteria; A01 ownerdefined calibration acceptance still unresolved','load_test':'Same preset, −5/0/+5V output open versus10k; Stage12 algebra has no finite outputgain/load/ground model, so load error is UNKNOWN, not zero.','endpoint_target_distinction':'Unreachable exact±1 is not automatically a violation of the retained0.5% endpoint gain target; complete source/setting/error conditions still unqualified.','static_comparison':'Residual numbers may exceed retained2mV target but full tolerance/temperature/protection/headroom and calibration protocol not established. No hardware PASS/FAIL inferred.'},'removable_modes':{'temporary_operating_preset':['IN gain if within actual modeled control range','zero-input intercept if within actual manual range'],'not_permanent_calibration':['moving either userpot changes the calibrated operating function','no endpoint/centre scale remapping is implemented','no separately adjustable OFFSET CV gain','no independent load/drift/noise/return correction'],'unknown':['pot taper/contact/setting resolution and reproducibility','input protection/source and opamp bias/offset/load dependence','actual output swing, load error and clip thresholds','temperature/drift and reference accuracy']},'complete_static_criterion_met':None,'load_criterion_met':None,'hardware_acceptance':False,'native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}
def build():
 paths=[OUT/'calibration-input.json',prior.OUT/'budget-report.json',prior.old.prior.OUT/'inventory-report.json']
 report=analyze(*[json.loads(p.read_text())for p in paths])
 paths += [Path(__file__),Path(__file__).with_name('test_stage13_calibration.py'),Path(prior.__file__),ROOT/'doc/src/content/docs/architecture/osc-block-ao.mdx',ROOT/'design/spec/modules/offset.py',ROOT/'design/standard/electrical-standard.json']
 report['source_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in paths};return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();text=json.dumps(build(),sort_keys=True,indent=2,allow_nan=False)+'\n';path=OUT/'calibration-report.json'
 if args.check:need(path.read_text()==text,'stale calibration report')
 else:path.write_text(text)
 print('PASS existing-control source study; calibration/load acceptance OPEN')
if __name__=='__main__':main()
