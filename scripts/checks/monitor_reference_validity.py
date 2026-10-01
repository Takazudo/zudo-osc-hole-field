#!/usr/bin/env python3
"""Integrate the coarse REF window without promoting it to precision validity."""
import argparse
import copy
import hashlib
import json
import math
import re
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks import monitor_permit_behavior as behavior
from scripts.checks import negative_monitor_network as negative
from scripts.checks import rail_monitor_candidate as rail
SPEC=ROOT/'design/power/monitor-permit-draft.json'
CATALOG=ROOT/'design/power/monitor-permit-parts.json'
OWNER=ROOT/'.claude/skills/component-monitor-permit-candidates'
REPORT=ROOT/'design/power/monitor-reference-validity-report.json'
FACT_SUFFIXES=('programmed-window','accuracy','hysteresis')


def source_facts():
    facts=json.loads((OWNER/'facts.json').read_text())['facts']
    manifest=json.loads((OWNER/'manifest.json').read_text())['records']
    sources=json.loads((OWNER/'sources.json').read_text())['sources']
    record=next(r for r in manifest if r['record_id']=='rec-monitor-tps37044mjofddfrq1')
    result={}
    for suffix in FACT_SUFFIXES:
        fact=next(f for f in facts if f['fact_id']=='fact-monitor-tps37044mjofddfrq1-'+suffix)
        source=next(s for s in sources if s['source_id']==fact['source_id'])
        if (fact['record_id']!=record['record_id'] or fact['fact_id'] not in record['fact_ids']
                or source['source_id'] not in record['source_ids']
                or source['record_id']!=record['record_id']
                or fact['verdict']!='PASS - primary-source confirmed'
                or fact['class']!='GUARANTEED_ELECTRICAL' or fact['provenance']!='PRIMARY-SPEC'
                or not re.fullmatch('[0-9a-f]{64}',source['sha256']) or set(source['sha256'])=={'0'}
                or source['authority_class']!='MANUFACTURER_PRIMARY' or source['availability']!='AVAILABLE'):
            raise ValueError('coarse monitor source closure failed')
        result[suffix]=fact
    return result,record['mpn']


def enclosing_decimal(value, upper):
    """A 12-place decimal enclosure consumable by the existing numeric API."""
    scale=10**12
    integer=math.ceil(value*scale) if upper else math.floor(value*scale)
    out=float(F(integer,scale))
    parsed=rail.number(out)
    if (parsed < value if upper else parsed > value):
        raise ValueError('decimal conversion narrowed the reference interval')
    return out


def calculate(spec,catalog,old,negative_spec,facts,mpn):
    behavior.build(spec)  # Explicit captured-topology and duplicate-ref guard.
    parts={p['ref']:p for p in spec['components']}
    if parts['U101']['mpn']!=mpn:
        raise ValueError('coarse monitor exact identity differs')
    entries={p['mpn']:p for p in catalog['parts']}
    condition=old['resistor_condition']
    # This divider uses one exact RT family envelope. Reject substitution
    # rather than silently applying its precision/TCR to another family.
    for ref in ('R109','R110','R111','R112','R113'):
        p=parts[ref];e=entries[p['mpn']]
        if (p['value']!=e['resistance_ohm'] or e['kind']!='resistor'
                or e['tolerance_fraction']!=condition['tolerance_fraction']
                or e['tcr_abs_per_C']!=condition['tcr_abs_per_C']):
            raise ValueError('reference divider evidence differs')
    mapping=dict(zip(('RN','RR','RG','RB','RU','RUG','RO','ROG'),range(101,109)))
    for p in negative_spec['resistors']:
        captured=parts['R'+str(mapping[p['ref']])]
        if (captured['mpn']!=p['mpn'] or captured['value']!=p['ohm']
                or [captured['pins']['1'],captured['pins']['2']]!=p['nodes']):
            raise ValueError('negative study differs from captured resistor network')
    for ref,key in (('U102','comparator'),('U103','reference')):
        if parts[ref]['mpn']!=negative_spec[key]['mpn']:
            raise ValueError('negative study device differs')
    window=facts['programmed-window']['value']
    if window['sense1_2_nominal_V'] != 0.4:
        raise ValueError('0.4V source accuracy/hysteresis applicability changed')
    device={
        'nominal_threshold_V':window['sense1_2_nominal_V'],
        'window_fraction':window['window_fraction'],
        'absolute_threshold_accuracy_fraction':facts['accuracy']['value']['at_0p4V_fraction'],
        'hysteresis_fraction_of_trip':[facts['hysteresis']['value']['at_0p4V_min'],facts['hysteresis']['value']['at_0p4V_max']],
        'adjustable_input_current_table_max_A':0,
    }
    divider={'top':[{'ohm':parts['R'+str(i)]['value']} for i in range(109,113)],
             'bottom':[{'ohm':parts['R113']['value']}],'sense_inputs':1}
    studies={}
    for label,bias in [('zero_sense_current',0),('assumed_source_table_current',old['supervisor']['adjustable_input_current_table_max_A'])]:
        device['adjustable_input_current_table_max_A']=bias
        limits=rail.divider_bounds(divider,device,condition)
        extent=(limits['UV_trip'][0],limits['OV_trip'][1])
        recovery=(limits['UV_recover'][1],limits['OV_recover'][0])
        evaluated=copy.deepcopy(negative_spec)
        evaluated['reference']['normal_target_V']=[enclosing_decimal(v,i==1) for i,v in enumerate(extent)]
        result=negative.calculate(evaluated)
        studies[label]={
            'sense_current_absolute_assumption_A':bias,
            'events_V':{name:[rail.display(v,i==1) for i,v in enumerate(pair)] for name,pair in limits.items()},
            'possible_settled_retained_good_reference_extent_V':[rail.display(v,i==1) for i,v in enumerate(extent)],
            'common_static_recovery_interval_V':[rail.display(recovery[0],True),rail.display(recovery[1],False)],
            'propagated_reference_enclosure_V':evaluated['reference']['normal_target_V'],
            'negative_trip_magnitude_V':result['conditional_trip_magnitude_V'],
            'negative_normal_UV_margin_V':result['normal_UV_margin_V'],
            'negative_normal_OV_margin_V':result['normal_OV_margin_V'],
            'negative_normal_band_guaranteed':result['conditional_static_normal_band_accepted'],
            'coarse_enclosure_within_narrow_reference':(
                extent[0]>=rail.number(negative_spec['reference']['normal_target_V'][0])
                and extent[1]<=rail.number(negative_spec['reference']['normal_target_V'][1])),
        }
    # Explicit forced DC counterexample, not an asserted reachable transient.
    ref=F('3.14');vn=F('-10.9')
    resistances={p['ref']:rail.number(p['ohm']) for p in negative_spec['resistors']}
    nodes,_,_=negative.nodal(negative_spec,resistances,{'AGND':F(),'VN':vn,'REF':ref})
    top=sum((rail.number(p['ohm']) for p in divider['top']),F())
    bottom=rail.number(divider['bottom'][0]['ohm'])
    sense=ref*bottom/(top+bottom)
    nominal=rail.number(device['nominal_threshold_V']);w=rail.number(device['window_fraction'])
    hmax=rail.number(device['hysteresis_fraction_of_trip'][1])
    # Nominal threshold accuracy, source maximum hysteresis; no sense current.
    uv_recover=nominal*(1-w)*(1+hmax);ov_recover=nominal*(1+w)*(1-hmax)
    return {
        'status':'CONDITIONAL REFERENCE VALIDITY INTEGRATION; NO QUALIFICATION',
        'qualification_accepted':False,'canonical_protection_implemented':False,
        'original_narrow_reference_assumption_V':negative_spec['reference']['normal_target_V'],
        'narrow_reference_proved_by_coarse_enclosure':all(row['coarse_enclosure_within_narrow_reference'] for row in studies.values()),
        'source_facts':facts,'resistor_condition':condition,
        'studies':studies,
        'forced_nominal_counterexample':{
            'reference_V':float(ref),'negative_rail_V':float(vn),'positive_rails_V':[12,5],
            'reference_sense_V':float(sense),'nominal_coarse_recovery_V':[float(uv_recover),float(ov_recover)],
            'coarse_monitor_ideal_released':uv_recover<sense<ov_recover,
            'negative_nodes_V':{n:float(nodes[n]) for n in ('SENSE','UV','OV')},
            'negative_comparators_ideal_released':nodes['OV']<nodes['SENSE']<nodes['UV'],
            'negative_rail_inside_required_band':rail.number(result['normal_magnitude_V'][0]) <= -vn <= rail.number(result['normal_magnitude_V'][1]),
            'scope':'Forced DC values, nominal resistor/threshold accuracy, zero leakage/offset; not proof of a reachable physical trajectory.'},
        'remaining_conditions':[
            'All threshold intervals are settled/static; common recovery means its strict interior with valid supply, other paired sense inputs healthy or correctly unused, and sufficient settling, not a time bound.',
            'Source-table 350nA condition is VSENSE=5.5V; its use near0.4V is an assumption, not a source guarantee.',
            'Negative comparator error/input-current envelopes retain all conditions of the separate network study.',
            'The broad interval is an enclosure across independent corners; it is not one device\'s exact acceptance interval.',
            'Reference startup, slow-slew, effective bypass, actual output-current/line conditions and independent validity remain unqualified.',
            'REF34 box temperature coefficient is not a local slope; separate line/load cross-sections do not bound their interaction.',
            'No physical dynamic, bench or installed protection acceptance; do not replace the narrow study with a claimed wider passing result.'],
    }


def run(check=False):
    spec=json.loads(SPEC.read_text());catalog=json.loads(CATALOG.read_text())
    old=json.loads(rail.SPEC.read_text());negative_spec=json.loads(negative.SPEC.read_text())
    rail.validate_sources(old);negative.validate(negative_spec)
    facts,mpn=source_facts()
    data=calculate(spec,catalog,old,negative_spec,facts,mpn)
    paths={SPEC,CATALOG,rail.SPEC,rail.SOURCES,negative.SPEC,negative.SOURCES,
           ROOT/negative_spec['normal_voltage_source'],Path(__file__).resolve(),
           Path(behavior.__file__).resolve(),Path(rail.__file__).resolve(),Path(negative.__file__).resolve()}
    paths.update(OWNER/name for name in ('facts.json','sources.json','manifest.json'))
    data['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    text=json.dumps(data,indent=2)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text:raise ValueError('reference integration report drift')
    else: REPORT.write_text(text)
    print('PASS: reference integration report reproduced; physical qualification OPEN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
