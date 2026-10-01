#!/usr/bin/env python3
"""Source-bound screen of the negative-fault veto; no device timing guarantee."""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks import monitor_permit_behavior as behavior
SPEC=ROOT/'design/power/monitor-permit-draft.json'
OWNER=ROOT/'.claude/skills/component-monitor-permit-candidates'
REPORT=ROOT/'design/power/monitor-fault-retiming-report.json'
REQUIRED={
    'tps37044mjofddfrq1': ('programmed-window','accuracy','reset-delay','detect-delay','glitch-immunity-nominal'),
    'tlv9022dr': ('output-low-table-max','output-leakage-typical'),
}


def source_paths():
    return [SPEC,Path(__file__).resolve(),Path(behavior.__file__).resolve()] + [
        OWNER/name for name in ('facts.json','sources.json','manifest.json')]


def snapshot_sources():
    return {p:p.read_bytes() for p in source_paths()}


def verify_unchanged(snapshot):
    if any(p.read_bytes()!=data for p,data in snapshot.items()):
        raise ValueError('retiming inputs changed during calculation')


def source_facts(snapshot=None):
    if snapshot is None: snapshot=snapshot_sources()
    facts=json.loads(snapshot[OWNER/'facts.json'])['facts']
    sources=json.loads(snapshot[OWNER/'sources.json'])['sources']
    records=json.loads(snapshot[OWNER/'manifest.json'])['records']
    result={}; identities={}
    for device,suffixes in REQUIRED.items():
        record=next(r for r in records if r['record_id']=='rec-monitor-'+device)
        identities[device]=record['mpn']
        for suffix in suffixes:
            fact=next(f for f in facts if f['fact_id']=='fact-monitor-'+device+'-'+suffix)
            source=next(s for s in sources if s['source_id']==fact['source_id'])
            if (fact['record_id']!=record['record_id'] or fact['fact_id'] not in record['fact_ids']
                    or source['source_id'] not in record['source_ids'] or source['record_id']!=record['record_id']
                    or fact['verdict']!='PASS - primary-source confirmed' or fact['provenance']!='PRIMARY-SPEC'
                    or source['authority_class']!='MANUFACTURER_PRIMARY' or source['availability']!='AVAILABLE'
                    or not re.fullmatch('[0-9a-f]{64}',source['sha256']) or set(source['sha256'])=={'0'}):
                raise ValueError('retiming source closure failed')
            result[suffix]=fact
    return result,identities


def calculate(spec,facts,identities):
    behavior.build(spec)
    parts={p['ref']:p for p in spec['components']}
    if (parts['U101']['mpn']!=identities['tps37044mjofddfrq1']
            or parts['U102']['mpn']!=identities['tlv9022dr']):
        raise ValueError('retiming exact identity differs')
    for ref in ('R109','R110','R111','R112','R113'):
        value=parts[ref]['value']
        if isinstance(value,bool) or not math.isfinite(value) or value<=0:
            raise ValueError('invalid divider resistance')
    if not (parts['U102']['pins']['1']==parts['U102']['pins']['7']==parts['U101']['pins']['2']=='REF_SENSE'
            and parts['U101']['pins']['8']=='FAULT_N'):
        raise ValueError('negative-fault route differs')
    top=sum(parts['R'+str(i)]['value'] for i in range(109,113))
    bottom=parts['R113']['value']
    window=facts['programmed-window']['value']
    nominal=window['sense1_2_nominal_V']
    if nominal!=0.4 or facts['output-low-table-max']['unit']!='V':
        raise ValueError('retiming source applicability differs')
    uv=nominal*(1-window['window_fraction'])
    uv_min=uv*(1-facts['accuracy']['value']['at_0p4V_fraction'])
    clamp=facts['output-low-table-max']['value']
    ref=3.3  # Forced nominal illustration; no reference accuracy claim.
    healthy=ref*bottom/(top+bottom)
    top_current=(ref-clamp)/top
    bottom_current=clamp/bottom
    reset=facts['reset-delay']['value']
    if reset['nominal_s']!=spec['model_conditions']['supervisor_reset_s']:
        raise ValueError('programmed reset time differs')
    overdrive=(healthy-uv)/uv
    return {
        'status':'CONDITIONAL NEGATIVE-FAULT VETO; PHYSICAL TIMING UNPROVED',
        'qualification_accepted':False,'canonical_protection_implemented':False,
        'source_facts':facts,
        'route':'U102 outputs1/7 -> REF_SENSE -> U101 SENSE1 / RESET1 -> FAULT_N',
        'forced_nominal_reference_V':ref,
        'released_reference_sense_V':healthy,
        'nominal_UV_trip_V':uv,'lowest_source_UV_trip_V':uv_min,
        'assumed_clamp_V':clamp,
        'conditional_clamp_below_lowest_UV_trip':clamp<uv_min,
        'nominal_clamped_top_current_A':top_current,
        'nominal_clamped_bottom_current_A':bottom_current,
        'nominal_required_total_comparator_sink_A':top_current-bottom_current,
        'assumed_clamp_point_requires_sourcing':top_current<bottom_current,
        'nominal_zero_clamp_reference_current_A':ref/top,
        'nominal_released_divider_current_A':ref/(top+bottom),
        'reference_equivalent_shift_V_per_total_leakage_A':top,
        'total_leakage_scope':'TPS SENSE1 input plus both released TLV output drains; no full-temperature total bound',
        'nominal_recovery_overdrive_fraction':overdrive,
        'nominal_node_above_UV_trip':healthy>uv,
        'source_reset_table_overdrive_fraction':reset['test_overdrive_fraction'],
        'nominal_recovery_at_least_table_overdrive':overdrive>=reset['test_overdrive_fraction'],
        'programmed_reset_nominal_s':reset['nominal_s'],
        'physical_assertion_bound_s':None,'physical_recovery_bounds_s':None,
        'guaranteed_minimum_detectable_negative_fault_s':None,
        'remaining_conditions':[
            'VOL source limit is at 4mA, 5V, VCM=V-, -40..125C; adopting it at the actual lower sink current, supply and common mode remains conditional.',
            'Released output leakage is only a typical source row at 25C and VPULLUP=V+; neither its maximum nor application at REF_SENSE is established.',
            'At-least-table overdrive is arithmetic only, not a full condition match or proof of monotonic timing versus overdrive.',
            'Reset tolerance requires 10% overdrive and 10kohm/10pF RESET loading; Check the reported signed recovery margin against that condition; passing that arithmetic alone does not establish applicability. Do not infer a 7ms minimum or 7..13ms actual interval.',
            'Glitch immunity is nominal, not a guaranteed short-pulse detection limit. Comparator maximum propagation is also unestablished.',
            'The reroute adds a supervisor detection stage to negative-fault assertion; complete cold-collapse release timing remains unbounded.',
            'Raw GOOD_FAST pulse diagnostics bypass the monitor and do not map external fault durations to reset pulse widths.',
            'Fault-dependent REF load can feed back through reference impedance/settling into negative comparator thresholds; chatter and coupled dynamics remain unmodeled.',
            'The coarse reference precision gap persists. Partial-power, leakage, retained charge, ground integrity and installed qualification remain open.'],
    }


def run(check=False):
    snapshot=snapshot_sources()
    facts,identities=source_facts(snapshot)
    report=calculate(json.loads(snapshot[SPEC]),facts,identities)
    report['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(snapshot[p]).hexdigest() for p in sorted(snapshot)}
    verify_unchanged(snapshot)
    text=json.dumps(report,indent=2)+'\n'
    if check:
        if REPORT.read_text()!=text: raise ValueError('retiming report drift')
    else: REPORT.write_text(text)
    print('PASS: negative-fault route and conditional load/timing screen; physical timing OPEN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
