"""Current A01-A06 owner scope and source-only exact-part inventory.
Historical checks run at their immutable checkpoint, never with rewritten failures.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage26'
BASE='f30d653e733a85fe00b1c187a5f571a983a3b47a'
OWNER_QUOTE='それなら適当で良さそう\nオシレーターのピッチについても、もし厳密に音階を指定したいなら別途クオンタイザーを使うので、こちらの楽器的には1V/octに追従できていること以上は必要ない\n\natten offsetは特に、雑にCVをいじるものだから求められる条件は緩い'
REMOVED_OBLIGATIONS=['close_2mV_complete_static_budget', 'precision_baseline_factory_protocol', 'precision_reference_replacement', 'spare_matched_inverter_rewire', 'lower_pot_impedance_for_precision', 'pitch_grade_AO_temperature_time_guarantee', 'precision_audio_center_null', 'independent_CV_gain_trim_for_2mV']
OSCILLATOR_GAPS=['HF_TRIM RVO1109 has required20kohm source value but blank exact MPN/supplier; existing10kohm TC33X catalog identity is not a20kohm substitute.', 'As-built base/scale/HF adjustment reach, interaction and temperature/nonlinearity qualification unavailable; no proven actuator shortage from source alone.']
MODULES=['A01','A02','A03','A04','A05','A06']
CHECKS=['electrical_safety','stable_operation','useful_control_range','noise_and_control_artifacts',
        'clipping_headroom_and_recovery','sensible_loading','practical_settling','manufacturing_and_assembly']
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}


def need(ok,message):
    if not ok:raise ValueError(message)


def read(path):return json.loads(path.read_text())
def dump(x):return json.dumps(x,indent=2,sort_keys=True,ensure_ascii=False,allow_nan=False)+'\n'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_scope(scope,checks):
    need(scope['authority']=='OWNER_APPROVED_CURRENT_AO_ACCEPTANCE_SCOPE' and scope['baseline_commit']==BASE,'authority/baseline')
    need(scope['effective_UTC']=='2026-10-17T04:03:00Z' and scope['owner_quote_ja']==OWNER_QUOTE,'dated owner evidence')
    need(scope['removed_obligations']==REMOVED_OBLIGATIONS,'reviewed obligation retirement only')
    need(scope['scope_modules']==MODULES,'only A01-A06')
    need(scope['scope_paths']==['IN through ATTEN to OUT','OFFSET CV jack to OUT','manual OFFSET to OUT'],'complete utility path scope')
    need(scope['current_use']=='COARSE_MUSICAL_CV_MANIPULATION','owner functional use')
    expected={'static_precision_error_V':.002,'precision_output_load_error_V':.001}
    need(set(scope['retired_criteria'])==set(expected),'scoped criterion set')
    for key,value in expected.items():
        row=scope['retired_criteria'][key]
        need(row['historical_value']==value and row['current_limit'] is None and row['disposition']=='NOT_APPLICABLE_CURRENT_AO_SCOPE','retired not passed or loosened numerical criterion')
    for key in ('precision_factory_calibration_required','prescribed_voltage_at_knob_positions','precision_pitch_cv_service_claim','hardware_acceptance'):
        need(scope[key] is False,'unapproved precision or physical claim')
    need(scope['new_numeric_accuracy_limit'] is None,'no invented accuracy threshold')
    need(scope['retained_nominal_function']=={'equation':'OUT = gain * IN + manual_offset + OFFSET_CV','gain_range':[-1,1],
        'input_V':[-5,5],'manual_offset_V':[-5,5],'offset_cv_V':[-5,5],'internal_clip_indication_nominal_V':[-10,10],
        'sum_extreme_V':[-15,15],'sum_extreme_is_linear_output_promise':False},'range/headroom contract')
    need(scope['implementation_scope']=={'implemented_instance':'A01','A02_A06_replication_authorized':False,
        'production_CAD_changed':False,'architecture_adopted':False,'native_request':'NONE'},'bounded implementation')
    pot=scope['pot_disposition']
    need(pot['ref']=='RV1308' and pot['selected_mpn']=='PTV09A-4020F-B104' and pot['nominal_ohm']==100000
         and pot['stage25_B103_status']=='SUPERSEDED_AS_UNNECESSARY_FOR_CURRENT_USE','retain B104')
    ex=scope['filter_exception']
    need(ex=={'ref':'C7105','module':'A01','role':'manual OFFSET smoothing, not pitch reference or storage',
        'mpn':'C0603C103J5RACTU','dielectric':'X7R','nominal_F':1e-8,'disposition':'SELECT_FOR_SOURCE_CANDIDATE_ONLY',
        'global_c_small_policy_changed':False,'other_compensation_storage_timing_policy_changed':False},'local filter classification only')
    need(scope['retained_checks']==CHECKS and set(checks)==set(CHECKS),'no functional/safety check omitted')
    for key,row in checks.items():
        need(all(isinstance(row[k],str) and row[k].strip() for k in ('requirement','method','source')),'complete check '+key)
        need(row['physical_status']=='NOT_RUN' and row['accepted'] is False and row['numeric_accuracy_limit'] is None,'no manufactured functional pass '+key)


def resolve(module,scope,standard):
    # Exact module match, never prefix matching or changing the global shared cell.
    if module in scope['scope_modules']:
        return {'basis':'stage26/acceptance.json','static_limit_V':None,'load_precision_limit_V':None,
                'precision_disposition':'NOT_APPLICABLE_CURRENT_AO_SCOPE','functional_checks':CHECKS}
    return {'basis':'unchanged global OSC-ES-1','static_limit_V':standard['calibration']['static_precision_error_V'],
            'load_precision_limit_V':standard['calibration']['precision_output_load_error_V'],
            'precision_disposition':'UNCHANGED','calibration':copy.deepcopy(standard['calibration'])}


def summarize_units(units):
    need(len(units)==154,'complete 154 units')
    packages={};uuids=set();pin_ids=set()
    for key,row in units.items():
        need(key==f"{row['ref']}.{row['unit']}" and row['uuid'] not in uuids,'unit key/UUID identity')
        uuids.add(row['uuid']);p=packages.setdefault(row['ref'],{'pins':{},'units':[]})
        p['units'].append(row['unit'])
        for pin,net in row['pins'].items():
            need(pin not in p['pins'] or p['pins'][pin]==net,'unit pin conflict')
            p['pins'][pin]=net
        for pin,uid in row['pin_uuids'].items():
            need(uid not in pin_ids,'duplicate source pin UUID');pin_ids.add(uid)
    need(len(packages)==118 and sum(len(p['pins']) for p in packages.values())==561,'complete 118 references/561 pins')
    return packages


def materialize(units,packages,patch,scope):
    need(len(patch['operations'])==19 and len({o['ref'] for o in patch['operations']})==19,'19 unique source selections')
    before=summarize_units(units);after=copy.deepcopy(units);selections={}
    for op in patch['operations']:
        ref=op['ref'];p=packages[ref];chosen=op['proposed'];mpn=chosen['selected_mpn'];candidate=patch['candidates'][mpn]
        need(hashlib.sha256((json.dumps(p,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()).hexdigest()==op['source_package_sha256'],'exact source package '+ref)
        need(op['unchanged_pins']==p['pins'] and op['unchanged_unit_records']==p['unit_records'],'source pin/unit metadata '+ref)
        need(all(p[k] is None for k in ('selected_manufacturer','selected_mpn','supplier_order_code')),'source selection baseline')
        need(chosen['supplier_order_code']==candidate['code'] and candidate['observation']['componentModelEn']==mpn
             and chosen['selected_manufacturer']==candidate['observation']['componentBrandEn'],'exact supplier identity')
        need(candidate['observation']['assemblyMode']=='smtWeld' and candidate['observation']['visible_service']=={'Assembly Type':'SMT Assembly','PCBA Type':'Economic and Standard'},'catalog assembly')
        if ref=='C7105':need(mpn==scope['filter_exception']['mpn'] and candidate['ratings']['dielectric']=='X7R','local filter candidate')
        if ref=='C7104':need(candidate['ratings']['dielectric']=='C0G','compensation dielectric preserved')
        keys=[k for k,row in after.items() if row['ref']==ref]
        need(keys,'selected package present')
        for key in keys:
            props=after[key]['properties']
            need(props['MPN']==props['Manufacturer']==props['LCSC']=='','blank source unit selection')
            props.update(MPN=mpn,Manufacturer=chosen['selected_manufacturer'],LCSC=chosen['supplier_order_code'],IdentityStatus='EXACT_SOURCE_CANDIDATE_NOT_RELEASED')
        selections[ref]={'before':op['test'],'selected_source_candidate':chosen,
                         'source_package_sha256':op['source_package_sha256'], 'ratings':candidate['ratings'],
                         'sourcing':op['sourcing'],'historical_requirements':op['unresolved'],
                         'current_requirement_basis':'stage26/acceptance.json and functional-checks.json',
                         'CAD_applied':False,'order_ready':False}
    need(summarize_units(after)==before,'no electrical inventory change')
    validate_materialization(units,after,selections)
    return {'status':'EXACT_PARTS_SELECTED_IN_SOURCE_CANDIDATE_ONLY','source_units':after,'packages':before,
            'selections':selections,'counts':{'references':118,'pins':561,'unit_UUIDs':154,'selected_passives':19},
            'annotations_exclusion_flags_preserved':True,'production_CAD_applied':False,'native_packet_materialized':False}


def validate_materialization(before,after,selections):
    need(before.keys()==after.keys(),'omitted or additional unit')
    for key,old in before.items():
        row=after[key];expected=copy.deepcopy(old)
        if old['ref'] in selections:
            sel=selections[old['ref']]['selected_source_candidate']
            expected['properties'].update(MPN=sel['selected_mpn'],Manufacturer=sel['selected_manufacturer'],
                                          LCSC=sel['supplier_order_code'],IdentityStatus='EXACT_SOURCE_CANDIDATE_NOT_RELEASED')
        need(row==expected,'unauthorized metadata/pin/flag change '+key)


def validate_oscillator(record,netlist):
    need(record['authority']=='OWNER_CLARIFICATION_RECORDED_WITHOUT_CIRCUIT_CHANGE','oscillator authority')
    for key in ('base_pitch_trim_fixes_scale','upstream_quantizer_fixes_downstream_tracking',
                'global_tracking_numeric_targets_changed','new_controls_required_by_source_review'):
        need(record[key] is False,'oscillator role/requirement confusion '+key)
    need(record['VCO_1V_per_oct_requirement_preserved'] is True and record['new_controls_added']==0,'existing tracking architecture')
    need(record['actual_range_qualification'] is None and record['native']==record['physical_calibration']=='NOT_RUN','unqualified calibration')
    packages={p['ref']:p for p in netlist['packages']}
    roles={'BASE_TRIM':'RVO1106','RZ_TRIM':'RVO1107','SCALE_TRIM':'RVO1108','HF_TRIM':'RVO1109',
           'SINE_SYMMETRY':'RVO1110','SINE_LEVEL':'RVO1111'}
    need(set(record['inspected_trim_packages'])==set(roles),'complete existing trim roles')
    for role,ref in roles.items():
        need(record['inspected_trim_packages'][role]==packages[ref],'exact source trim '+role)
    need(record['front_tuning_packages']=={ref:packages[ref] for ref in ('RV104','RV105')},'front tuning preserved')
    need(record['shared_octave_span']==packages['RV1601'],'shared octave trim')
    need(packages['RVO1109']['attributes']['MPN']=='' and record['actual_missing_items']==OSCILLATOR_GAPS,'HF identity gap retained')
    return record


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'protected historical/canonical bytes changed')
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    allowed={'scripts/architecture278/implementation/'+n for n in ('stage26_acceptance.py','test_stage26_acceptance.py')}
    need(all(p.startswith(REL+'stage26/') or p in allowed for p in new),'out-of-scope new file')
    return {'baseline':BASE,'mutable_entrypoints_only':sorted(MUTABLE)}


def build(check_cache=False):
    paths=[OUT/'acceptance.json',OUT/'functional-checks.json',ROOT/'design/standard/electrical-standard.json',
           ROOT/REL/'stage18/compatibility-report.json',ROOT/REL/'stage16/inputs-report.json',
           ROOT/REL/'stage23/candidate-selection.patch.json']
    scope,checks,standard,historical,inputs,patch=map(read,paths)
    validate_scope(scope,checks)
    need(standard['calibration']['static_precision_error_V']==.002 and standard['calibration']['precision_output_load_error_V']==.001
         and standard['calibration']['octave_step_error_V']==.002 and standard['calibration']['pitch_tracking_target_cents']==5,'global precision unchanged')
    oscillator=validate_oscillator(read(OUT/'oscillator-calibration.json'),read(ROOT/REL/'candidate-netlist.json'))
    inventory=materialize(historical['unit_metadata'],inputs['packages'],patch,scope)
    if check_cache:
        receipts=read(ROOT/REL/'stage23/retrieval.json')
        for candidate in patch['candidates'].values():
            row=receipts[candidate['code']];p=ROOT/row['raw_cache']
            need(sha(p)==row['sha256']==candidate['supplier_sha256'],'dated supplier receipt')
    report={'status':'CURRENT_OWNER_AO_SCOPE_IMPLEMENTED_SOURCE_ONLY','effective_UTC':scope['effective_UTC'],
            'module_resolution':{m:resolve(m,scope,standard) for m in MODULES+['O1','O2','O3','O4','O5','MULT','S&H','MASTER_REFERENCE']},
            'retired_as_not_applicable':scope['retired_criteria'],'removed_precision_obligations':scope['removed_obligations'],
            'oscillator_calibration':oscillator,'retained_checks':checks,'pot_disposition':scope['pot_disposition'],
            'manual_filter_diagnostic':{'nominal_center_1percent_settling_s':math.log(100)*1e-8*26000*1e7/(26000+1e7),
                                        'acceptance_threshold_s':None,'purpose':'Retained RC diagnostic, not a precision timing gate'},
            'source_inventory_sha256':hashlib.sha256(dump(inventory).encode()).hexdigest(),
            'counts':inventory['counts'],'current_exact_candidate_identity_gaps_for_19_passives':0,
            'physical_and_order_readiness':'OPEN; exact identity closure is not rating/process/assembly qualification',
            'next_bounded_step':'Resolve the retained DIN fabrication position/fixing/process and externally assembled wiring/strain-relief definition before physical binding; no precision-only redesign.',
            'native_request':'NONE','architecture_adopted':False,'hardware_acceptance':False,'preservation':protected()}
    paths += [OUT/'oscillator-calibration.json',ROOT/REL/'candidate-netlist.json',ROOT/'design/spec/modules/oscillator.py',ROOT/'doc/src/content/docs/architecture/osc-block-osc.mdx',OUT/'README.md',ROOT/REL/'README.md',ROOT/REL/'stage24/definitions.json',ROOT/REL/'stage25/fabrication-request.md',
              ROOT/REL/'stage23/retrieval.json',Path(__file__),Path(__file__).with_name('test_stage26_acceptance.py'),
              Path(__file__).with_name('check_source.py')]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in paths}
    return inventory,report


def history_check():
    protected()
    # A detached disposable checkout gives old strict guards their real old files AND git history.
    # No dependency install, native executable or production artifact is invoked.
    with tempfile.TemporaryDirectory(prefix='osc-stage26-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            subprocess.run([sys.executable,'scripts/architecture278/implementation/check_source.py'],cwd=checkout,check=True)
            subprocess.run([sys.executable,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage2[0-5]*.py'],cwd=checkout,check=True)
        finally:
            subprocess.run(['git','worktree','remove',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage25 checkpoint reproduction and 180 historical regressions; historical failures remain historical')


def reviews():
    review=read(OUT/'independent-review.json')
    need(review['status']=='PASS_SOURCE_REVIEW_ONLY','independent review')
    for name,wanted in review['reviewed_sha256'].items():need(sha(ROOT/name)==wanted,'review binding '+name)


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-cache',action='store_true')
    p.add_argument('--check-history',action='store_true');p.add_argument('--check-review',action='store_true');args=p.parse_args()
    if args.check_history:history_check()
    inventory,report=build(args.check_cache)
    for name,data in [('candidate-inventory.json',inventory),('acceptance-report.json',report)]:
        dest=OUT/name;body=dump(data)
        if args.check:need(dest.read_text()==body,'deterministic drift '+name)
        else:dest.write_text(body)
    if args.check_review:reviews()
    print('PASS current A01-A06 scope; 19 source selections; 118 refs/561 pins/154 units; physical/native NOT RUN')


if __name__=='__main__':main()
