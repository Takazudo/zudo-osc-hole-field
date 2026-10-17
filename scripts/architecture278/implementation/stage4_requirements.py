"""Candidate-only requirements rationale audit; no canonical rule mutation."""
import argparse
from collections import Counter
import hashlib
import json
import subprocess
from pathlib import Path
import stage3_crossing_audit as audit

ROOT,OUT=audit.ROOT,audit.OUT
INITIAL='f0c8eaa0d16a0ab59427bef8d2e2fb5f9cf9c336'
STANDARD='design/standard/electrical-standard.json'

def classify(row):
    net=row['actual_identity']['actual_net'].split('/')[-1];uid=row['actual_identity']['actual_panel_uid']
    if net.startswith('OSC_OCT') or net in ('OCT_SELECTED','1V_BUFFER','RANGE_CV','LFO_REF') or uid.endswith(('.TUNE','.FINE')):return 'pitch_DC_and_dynamic'
    if net=='OSC_GATE_REF':return 'gate_threshold_reference_DC'
    if net in ('SYNC_GATE','SOFT_DRIVE','HARD_DRIVE'):return 'conditioned_logic_and_sync_command'
    if net=='SYNC_BUFFER':return 'buffered_analog_gate_input'
    if net.endswith('_SCALED'):return 'buffered_audio_waveform'
    if 'REF' in net:return 'buffered_reference_DC_and_load_transients'
    if net.endswith('_W'):return 'raw_wiper_modulation_or_PW'
    if net in ('FM_BUFFER','FM_REMOTE','PWM_BUFFER','PWM_REMOTE'):return 'buffered_FM_PWM_modulation'
    raise ValueError('unclassified crossing signal '+net)

METRICS={
'pitch_DC_and_dynamic':['absolute pitch error/offset, ground shift and loading','temperature drift and calibration span','modulation bandwidth, settling and coupling; no blanket DC-only assumption'],
'gate_threshold_reference_DC':['threshold reference DC error and drift','shared-source loading and return error','threshold modulation/noise under five receivers'],
'conditioned_logic_and_sync_command':['guaranteed high/low margin at actual receiver and ground','ringing/overshoot/undershoot and false edges','minimum pulse width, pulse loss and timing; AC-coupled core sync response'],
'buffered_analog_gate_input':['comparator threshold window and hysteresis','noise/ringing threshold recrossings','input slew, narrow-pulse propagation and false/missed edges'],
'buffered_audio_waveform':['amplitude error, bandwidth/phase and distortion','capacitive-load stability and crosstalk','fault/return behavior at local output buffer'],
'buffered_reference_DC_and_load_transients':['DC offset/loading/return and temperature drift','five-instance source stability and aggregate admittance','switch/pot load transients and settling'],
'raw_wiper_modulation_or_PW':['position-dependent Thevenin resistance and input bias error','RC bandwidth/slew, noise pickup and source return','PW/FM/PWM command accuracy over full pot travel'],
'buffered_FM_PWM_modulation':['DC command error and AC modulation bandwidth','driver isolation/feedback and capacitive-load stability','source/receiver loading, crosstalk and return shift']}

def build():
    standard=json.loads((ROOT/STANDARD).read_text());oldbytes=subprocess.check_output(['git','show',INITIAL+':'+STANDARD],cwd=ROOT);old=json.loads(oldbytes)
    source=json.loads((OUT/'direct-study-report.json').read_text())['best']['paths'];ctx=audit.context();rows=[]
    for row in source:
        ident=row['actual_identity'];kind=classify(row);nodes=[]
        for endpoint in sorted(set(ident['canonical_source_nodes']+[ident[k]['ref']+':'+ident[k]['pin'] for k in ('front','other')])):
            ref,pin=endpoint.split(':');part,net=ctx['bypin'][ref,pin]
            if net!=ident['actual_net']:raise ValueError('source endpoint net mismatch')
            nodes.append({'endpoint':endpoint,'net':net,'source_instance':part['instance'],'unit':part['unit'],'source_key':part['key'],'symbol':part['symbol'],'pin_type':part['pin_types'].get(pin),'attributes':part['attributes'],'is_canonical_crossing_source':endpoint in ident['canonical_source_nodes']})
        rows.append({'actual_identity':ident,'signal_class':kind,'live_endpoint_evidence':nodes,'required_characterization':METRICS[kind],'physical_result':'NOT RUN','strict300_comparison_mm':row['total_mm'],'strict300_over':row['total_mm']>300,'classification':'source-backed topology; proposed characterization, not measured performance'})
    paths=[Path(__file__),Path(audit.__file__),Path(__file__).with_name('test_stage4_requirements.py'),ROOT/STANDARD,ROOT/'design/spec/modules/oscillator.py',ROOT/'design/spec/modules/oscillator-reference.json',ROOT/'design/spec/cells/run_spice.py',ROOT/'design/architecture-278/electrical.md',OUT/'direct-study-report.json',OUT/'stage3-crossing-audit.json']
    cells={c['id']:c for c in standard['cells']}
    return {'status':'CANDIDATE REQUIREMENTS CORRECTION PROPOSAL; canonical limits unchanged; native NOT RUN',
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
            'initial_source':{'commit':INITIAL,'path':STANDARD,'sha256':hashlib.sha256(oldbytes).hexdigest(),'authority':old['authority'],'status':old['status'],'remote_controls':old['remote_controls']},
            'current_remote_controls':standard['remote_controls'],'relevant_cells':{k:{field:cells[k][field] for field in ('authority','verification_status','connections','notes')} for k in ('remote_buffer','high_impedance_input','gate_trigger_input')},
            'calibration_targets':standard['calibration'],'row_count':len(rows),'class_counts':dict(sorted(Counter(r['signal_class'] for r in rows).items())),'rows':rows,
            'requirement_definition_reconciliation':[
                {'claim':'0.3m harness and1nF harness envelope','classification':'PROJECT-CHOICE planning envelope; unvalidated NEEDS BENCH','evidence':'initial/current OSC-ES-1 remote_controls and remote_buffer notes','not_proven':'measured failure boundary, universal stability threshold, or universal complete pad-to-pad conductor limit'},
                {'claim':'300mm complete path including connectors/traces/test equipment','classification':'later architecture278 planning interpretation','evidence':'design/architecture-278/electrical.md complete-path paragraph','not_proven':'equivalence to original harness-only wording or independent electrical derivation'},
                {'claim':'1nF aggregate shared direct load','classification':'architecture278 conservative allocation for shared driver; not measured','evidence':'electrical.md900pF allocation and separate five1k/100nF receiver dynamics','not_proven':'actual capacitance, phase margin, transient recovery or source current'},
                {'claim':'334mm unsafe or300mm safe','classification':'UNSUPPORTED inference','evidence':'none; length-only scalar has no actual parasitic/driver/load dynamics','not_proven':'any physical safety or stability conclusion'}],
            'proposed_candidate_reporting_correction':['Keep historical strict300 developed-path comparisons as sensitivity results, not proof that rewiring or a second connector is electrically required.','Record harness length and complete developed length separately; independently account direct capacitance once over actual electrical segment union.','Use signal-class driver/receiver error and transient requirements with actual parasitics, ground and temperature; retain canonical envelope until a separately reviewed requirement change.','Do not infer internal copper is superior to a protected/buffered external patch; compare actual source impedance, protection, termination, return, load and spectrum.','Do not add topology solely to satisfy an unvalidated scalar cutoff. Optimize joint mechanical/electrical behavior after definition review.'],
            'pitch_conversion':{'relationship':'At1V/oct, cents=1200*deltaV;5cents=4.166666667mV','status':'algebraic conversion only; total core/calibration/temperature errors share budget'},
            'gate_scope':'SYNC_BUFFER is analog before comparator, SYNC_GATE is conditioned HC output, SOFT/HARD_DRIVE follow switch into100k pulldown/10k series/1nF AC core sync network. OSC_GATE_REF is a DC threshold reference, not a logic pulse. They must not share a single logic-level characterization.',
            'remaining':['No new bench/SPICE/native run.','Actual capacitance/inductance/contact resistance, driver stability and receiver margin unextracted.','Canonical limit changes and architecture adoption not performed.','Local sensitive timing/summing/feedback/storage nodes remain local; this review is not permission to route them remotely.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();data=json.dumps(r,indent=2,sort_keys=True)+'\n';dest=OUT/'stage4-requirements-report.json'
    if args.check:
        if dest.read_text()!=data:raise ValueError('stale requirement audit')
    else:dest.write_text(data)
    print('requirements audit',r['row_count'],r['class_counts'],'canonical unchanged')
if __name__=='__main__':main()
