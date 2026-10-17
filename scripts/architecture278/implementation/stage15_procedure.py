"""Propose real-control verification after owner intended-use decision; preserve historical evidence."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
import stage15_interpretation as previous
import stage15_electrical as electrical
import stage11_assessment as common
ROOT=common.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage15-procedure'
BASE='c6a62d3c820fdbd7dfe0efe160e0758bb4942687'
need=common.need

def preserve():
    scope=json.loads((OUT/'scope.json').read_text())
    names=set(subprocess.check_output(['git','ls-tree','-r','--name-only',BASE,*common.PREFIXES],cwd=ROOT,text=True).splitlines())-common.MUTABLE
    need(scope['baseline_commit']==BASE and set(scope['preserved_prior_source_sha256'])==names,'historical inventory')
    for name,sha in scope['preserved_prior_source_sha256'].items():
        need(common.digest(ROOT/name)==sha==hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest(),'preserved '+name)
    return len(names)

def predecessor():
    preserve()
    need((previous.OUT/'interpretation-report.json').read_text()==json.dumps(previous.build(),sort_keys=True,indent=2,allow_nan=False)+'\n','historical interpretation report')
    for role in ('root','code','electrical'):
        r=json.loads((previous.OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'historical review authorship')
        for name,sha in r['source_sha256'].items():
            actual=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest() if name in common.MUTABLE else common.digest(ROOT/name)
            need(actual==sha,'historical review binding '+name)

def analyze(standard,allocation,decision):
    need(decision['manual_offset_use']=='continuous musical control set by ear or meter','owner decision')
    need(decision['prescribed_voltage_at_knob_positions'] is False,'no knob-position accuracy promise')
    need(decision['criteria_unchanged'] is True,'criteria retained')
    need(all(decision[k] is False for k in ('factory_protocol_approved','component_implementation_authorized','physical_execution_authorized')),'no unapproved procedure or implementation')
    need(decision['precision_priorities']==['accurate external-CV transfer','stability after adjustment'],'owner precision priorities')
    need(standard['calibration']['static_precision_error_V']==.002 and standard['calibration']['precision_output_load_error_V']==.001,'canonical criteria')
    cases=list(electrical.all_cases(.0001,.001))
    gains=[p['gr']*p['gcv'] for p,*_ in cases]
    gmin,gmax=min(gains),max(gains)
    gainerr=5*max(abs(gmin-1),abs(gmax-1))
    initial=allocation['scenarios'][0]
    manual={r['state']:r for r in initial['state_rows'] if r['state'] in ('manual_low','manual_high','zero')}
    # This is a necessary headroom in the error budget, NOT assumed calibration performance.
    allowance=.002-gainerr
    return {'owner_decision':decision,'static_target_V':.002,'load_change_target_V':.001,
        'existing_model_support':{'initial25C_CV_gain_interval':[gmin,gmax],
            'CV_gain_only_max_abs_error_at5V_V':gainerr,'remaining_for_actual_baseline_and_all_other_static_terms_V':allowance,
            'CV_gain_10V_span_error_interval_V':[10*(gmin-1),10*(gmax-1)],
            'condition':'Coherent initial25C network matching sensitivity only; no actual-condition whole-cell bound or calibrated result.',
            'manual_endpoint_and_midpoint_characterization':{n:{'nominal_out_V':r['nominal']['out_V'],'fixed_setting_error_interval_V':r['with_reference_initial_signed_interval_V']} for n,r in manual.items()},
            'manual_scope':'Historical nominal fractions/reference sensitivity characterize range and centre; these are not prescribed-voltage accuracy limits at knob positions.'},
        'absolute_acceptance_equation':'r(V)=OUT(V)−[Btarget+Gdesired*INmeasured+CVmeasured]; Btarget selected BEFORE adjustment. Do not substitute measuredOUT0 for Btarget.',
        'paired_gain_equation':'Gcv=[OUT(CVhi)−OUT(CVlo)]/[CVhi−CVlo], unchanged other stimuli/controls/load. Diagnostic intercept cancellation only.',
        'remaining_budget_equation':'|achieved baseline error| + uncertainty contribution + input/protection/nonlinearity/drift/output/return terms <= remaining budget, without duplicate terms.0.99995mV is an algebraic necessary allowance, not a new setup tolerance or simultaneous allocation per term.',
        'physical_actuators':{'OFFSET':'Adjust reachable Btarget with IN=CV=0 by observing independent meter; real front control, no added trim. Factory setup is temporary control positioning.',
            'ATTEN':'Select IN gain with independent source/meter; cannot independently change externalCVgain. Lock before OFFSET baseline adjustment; reverify baseline after any ATTEN change.',
            'external_CV_gain':'No independent fitted actuator; gr*gcv remains set by approved network ratios. Screen as built, do not claim calibration-corrected gain.',
            'stored_correction':'None; no mathematical subtraction or software correction applied.'},
        'persistence':{'controls_held':'Only measured same-setting performance persists over verified conditions/time; stability not proven by one zero reading.',
            'OFFSET_moved':'Previous Btarget setting/zero is no longer retained. User may choose another reachable offset by ear/meter; this does not invalidate intended use. Reset a declared Btarget physically for absolute verification.',
            'ATTEN_moved':'INgain and possibly offset change; factory INgain/baseline settings do not persist. Re-establish intended gain/baseline for verification.',
            'CV_gain_after_control_moves':'Idealmodel gr*gcv independent ofbothcontrols; physical invariance must be verified, not assumed from ratios.',
            'power_or_environment_change':'No persistence guarantee without measurement at specified conditions.'},
        'finite_procedure':[
            {'step':1,'action':'Record DUT identity,actual rails/reference,source/receiver grounds,source impedance,meteruncertainty andload. Warmup20min perstandard. Propose25C initialtest; final temperature/time envelope remainsunadopted.'},
            {'step':2,'action':'IN=CV=0; chooseATTEN centre and declaredBtarget=0V. Physically setOFFSET usingmeter, thenfreezecontrols. Record achievedbaseline error,not silentlyzeroed readings. If targetunreachable,failsetup; no mathcorrection.'},
            {'step':3,'action':'With10kohm proposedstaticload andallcontrolsheld, apply externalCV−5,−2.5,0,+2.5,+5V inbothdirections, measuringatinputjack. Reportraw absolute residual againstBtarget+CV andpairedgain/intercept separately. No adjustmentbetweensamples. Includeuncertainty whenassessingunchanged2mVtarget.'},
            {'step':4,'action':'HoldCV=0,controlsunchanged; sampleOUT at0,1,5,15,30min(proposedwindow). Record drift frominitial andabsolute deviationfromBtarget; recheck±5Vgain atwindowend. Noautozero. Thiswindowis notadoptedservicequalification.'},
            {'step':5,'action':'MoveOFFSET throughcentre/endpoints andback; characterizeactualrange,centrenonzero,approachdirection/repeatability andsettling withoutinventedvoltage tolerances. Then physicallysetBtarget−2/0/+2V andrepeatCVsweep atATTEN0/.5/1 selectedsettings. Only useunclippedverifiedheadroom; ±7Vsum notguaranteed byanalysis. Invalidheadroom meansNOTRUN,notpass. Re-establishbaselineafterATTENchange.'},
            {'step':6,'action':'INpath verification remainsseparate: CV=0; physically selectdesiredINgain−1/0/+1 whereattainable,thenadjustmanualBtarget0 andholdboth. SweepIN−5/0/+5 againstBtarget+Gdesired*IN. If endpointgain unreachable,recordspecificINadjustmentgap,notexternalCVfailure. Frontcontrolmovement doesnotpreservegainsetting.'},
            {'step':7,'action':'EstablishnominalOUT−5/0/+5V withdeclaredsources/controls; alternateinstrument-open and10kohm whileallsettingsheld. MeasureOUT10k−OUTopen againstdistinct1mVcriterion; no rezeroing, inputchange orcontroladjustmentwithinpair. Recordsettling andactualinstrumentloading.'},
            {'step':8,'action':'Repeatbaseline/gains aftercontrolmovement andpowercycle asproposedpersistencecharacterization. Do notclaimlifetime/tempqualification. Record pass/fail/NOTRUN perlane andactualconditions; no aggregate acceptancewithoutapprovedfactoryprotocol.'}],
        'minimum_gap_and_remedy':{'current_gap':'No accepted executablefactoryprocedure,actual-condition errorbound or physicalverification. MissingCVgaintrim alone does notprovehardwarefailure; as-builtCVgain may meetbudget.',
            'if_CV_gain_fails':'First isolatepairedCVslope frombaseline/input/loading/drift. If repeatableCVgain alone exceedsthe approvedstaticallocation, existingcontrols cannot correctit. Minimumproposedfunctionalremedy is ONE independent stableCVpathgain-adjustment degreeoffreedom inlocalCVsummerbranch, preservingotherpath gains; exactimplementation would requireseparateapproval andanalysis. No partsearch ortrimdesign here.',
            'if_baseline_or_drift_fails':'UseexistingOFFSET forreachablebaseline; do nottreat initialrezero asdriftrepair. Identifymeasuredsource(input,reference,return,amplifier) beforeproposingits specificremedy; no blanketredesign.',
            'next_step':'Review/adopt proposedfactorymeasurementcontract and authorize a separatebenchverification task on anavailableprototype, with declaredenvironment/uncertainty. No componentimplementation is presentlyjustified orauthorized.'},
        'protocol_status':'PROPOSED_UNADOPTED','factory_calibration_performed':False,'hardware_acceptance':False,'component_geometry_changed':False,
        'native':'NOT RUN','CAD':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}

def build():
    count=preserve()
    files=[ROOT/'design/standard/electrical-standard.json',ROOT/'design/architecture-278/implementation/stage15-completion/allocation-report.json',OUT/'owner-decision.json']
    r=analyze(*[json.loads(p.read_text()) for p in files])
    files += [OUT/'scope.json',ROOT/'design/spec/modules/offset.py',ROOT/'doc/src/content/docs/architecture/osc-block-ao.mdx',Path(electrical.__file__),Path(__file__),Path(__file__).with_name('test_stage15_procedure.py'),ROOT/'design/architecture-278/implementation/STAGE15-PROCEDURE.md']
    r.update(baseline_commit=BASE,preserved_predecessor_files=count,source_sha256={str(p.relative_to(ROOT)):common.digest(p) for p in files})
    return r

def reviews():
    for role in ('code','electrical'):
        r=json.loads((OUT/('review-'+role+'.json')).read_text())
        need(r.get('independent_review') and r.get('authorship_exclusion'),'review authorship')
        common.bindings(r)
        need({'scripts/architecture278/implementation/stage15_procedure.py','design/architecture-278/implementation/STAGE15-PROCEDURE.md'}<=set(r['source_sha256']),'review coverage')

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-predecessor',action='store_true');args=p.parse_args()
    if args.check_predecessor:predecessor();print('PASS frozen interpretation evidence; owner intended use recorded separately');return
    r=build();common.finite(r);common.acceptance(r);text=json.dumps(r,indent=2,sort_keys=True,allow_nan=False)+'\n';dest=OUT/'procedure-report.json'
    if args.check:need(dest.read_text()==text,'stale procedure');reviews()
    else:dest.write_text(text)
    print('PASS proposed physical procedure; no factory gain trim or hardware acceptance')
if __name__=='__main__':main()
