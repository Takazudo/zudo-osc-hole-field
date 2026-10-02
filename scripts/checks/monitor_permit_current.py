#!/usr/bin/env python3
"""Conditional monitor allocation screen with explicit source-condition gaps."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks import monitor_permit_behavior as behavior
SPEC=ROOT/'design/power/monitor-permit-draft.json'
CATALOG=ROOT/'design/power/monitor-permit-parts.json'
SUPPLY=ROOT/'design/power/supply-architecture-input.json'
REPORT=ROOT/'design/power/monitor-permit-current-report.json'
# Transcribed from SCES351Y printed p6, not a general VI=VCC condition.
# Require the retained owner row to keep this comparison tied to that source.
LVC_ICC_CONDITIONS='VCC1.65..5.5V, VI5.5V orGND, IO0, TA-40..125C. Loaded, slow-input and switching current remain separate.'
FACTS={
 'U101':('component-monitor-permit-candidates','monitor-tps37044mjofddfrq1',1),
 'U102':('component-monitor-permit-candidates','monitor-tlv9022dr',2),
 'U103':('component-monitor-permit-candidates','monitor-ref3433tidbvr',1),
 'U104':('component-monitor-permit-candidates','monitor-sn74lvc1g17dbvr',1),
 'U105':('component-monitor-permit-candidates','monitor-sn74lvc1g74dctr',1),
 'U106':('component-monitor-permit-candidates','monitor-sn74lvc1g17dbvr',1),
}


def high_input_applicability(supply_bounds, r120_bounds, r125_bounds, current):
    """Compare ideal steady HIGH voltages with the exact retained ICC test point."""
    for ref in ('U104','U106'):
        row=current[ref]
        if (row['fact_id']!='fact-monitor-sn74lvc1g17dbvr-quiescent-table-max'
                or row['conditions']!=LVC_ICC_CONDITIONS):
            raise ValueError('LVC ICC source condition changed: '+ref)
    if (len(supply_bounds)!=2
            or any(isinstance(v,bool) or not isinstance(v,(int,float))
                   or not math.isfinite(v) for v in supply_bounds)
            or not 0 < supply_bounds[0] <= supply_bounds[1]):
        raise ValueError('invalid normal supply bounds')
    low,high=supply_bounds
    r1_low,r1_high=r120_bounds; rb_low,rb_high=r125_bounds
    gain_low=rb_low/(r1_high+rb_low)
    gain_high=rb_high/(r1_low+rb_high)
    inputs={'U104':[low,high], 'U106':[low*gain_low,high*gain_high]}
    return {
        'status':'CONDITIONAL INPUT VOLTAGES; ACTUAL ICC APPLICATION UNRESOLVED',
        'source_fact_id':current['U104']['fact_id'],
        'source_locator':current['U104']['locator'],
        'source_conditions':LVC_ICC_CONDITIONS,
        'source_high_input_test_V':5.5,
        'conditional_supply_V':list(supply_bounds),
        'resistance_bounds_ohm':{'R120':list(r120_bounds),'R125':list(r125_bounds)},
        'U106_divider_gain_bounds':[gain_low,gain_high],
        'U106_input_deficit_below_supply_V':[low*(1-gain_high),high*(1-gain_low)],
        'buffers':{ref:{'conditional_steady_high_input_V':bounds,
                        'icc_high_test_point_matches_entire_conditional_interval':bounds==[5.5,5.5],
                        'application_qualified':False}
                   for ref,bounds in inputs.items()},
        'actual_extra_supply_current_A':None,
        'assumptions':[
            'U104 input FAULT_N and its HIGH output GOOD_FAST are ideal and equal to the normal +5V source; actual output droop and loading remain unresolved.',
            'Zero U106 input current and other leakage; R121 therefore has no steady voltage drop.',
            'Independent resistor tolerance/TCR corners use the existing 25C reference and -40..125C analysis envelope.',
            'U106 input equals GOOD_FAST*R125/(R120+R125); these conditional intervals are not physical input-voltage guarantees.',
            'Even a modeled test-point match does not establish actual input/output conditions or current qualification.',
            'The separate 3.6V ICC row and VCC-0.6V DeltaICC point do not establish a voltage-wide bound for either buffer.'],
    }


def load_current_facts():
    results={}; paths=set()
    for ref,(bundle,name,count) in FACTS.items():
        directory=ROOT/'.claude/skills'/bundle
        paths.update(directory/file for file in ('facts.json','sources.json','manifest.json'))
        facts=json.loads((directory/'facts.json').read_text())['facts']
        fact=next(f for f in facts if f['fact_id']=='fact-'+name+'-quiescent-table-max')
        source=next(s for s in json.loads((directory/'sources.json').read_text())['sources']
                    if s['source_id']==fact['source_id'])
        record=next(r for r in json.loads((directory/'manifest.json').read_text())['records']
                    if r['record_id']==fact['record_id'])
        if (fact['verdict']!='PASS - primary-source confirmed' or fact['unit']!='A'
                or fact['class']!='GUARANTEED_ELECTRICAL' or isinstance(fact['value'],bool)
                or not math.isfinite(fact['value']) or fact['value']<=0
                or source['availability']!='AVAILABLE' or source['authority_class']!='MANUFACTURER_PRIMARY'
                or fact['fact_id'] not in record['fact_ids'] or source['record_id']!=record['record_id']
                or source['source_id'] not in record['source_ids']):
            raise ValueError('current fact source closure failed: '+ref)
        results[ref]={'mpn':record['mpn'],'fact_id':fact['fact_id'],
                      'table_max_A':fact['value'],'units_per_package':count,
                      'package_table_sum_A':fact['value']*count,
                      'conditions':fact['conditions'],'locator':fact['locator'],
                      'application_qualified':False}
    return results,paths


def build(spec, catalog, supply, current):
    # Reuse the independently tested topology guard; no equation follows a
    # rewired capture silently. Values remain available for sensitivity tests.
    behavior.build(spec)
    parts={p['ref']:p for p in spec['components']}
    for ref,row in current.items():
        if row['mpn']!=parts[ref]['mpn']:
            raise ValueError('current evidence MPN differs: '+ref)
    exact={p['mpn']:p for p in catalog['parts']}
    def resistance_bounds(ref):
        p=parts[ref]; e=exact[p['mpn']]
        if p['value']!=e['resistance_ohm']:
            raise ValueError('resistance and MPN disagree')
        if (isinstance(p['value'],bool) or not math.isfinite(p['value'])
                or p['value']<=0):
            raise ValueError('invalid resistance')
        # Analysis reference 25C and -40..125C envelope, not a manufacturer
        # nominal-resistance reference-temperature qualification.
        tolerance=e['tolerance_fraction']; drift=100*e['tcr_abs_per_C']
        if (isinstance(tolerance,bool) or isinstance(e['tcr_abs_per_C'],bool)
                or not math.isfinite(tolerance) or not math.isfinite(drift)
                or not 0 <= tolerance < 1 or not 0 <= drift < 1):
            raise ValueError('invalid independent resistor condition')
        factor=(1-tolerance)*(1-drift)
        if not 0 < factor <= 1:
            raise ValueError('invalid resistor condition')
        return p['value']*factor,p['value']*(1+tolerance)*(1+drift)
    def minimum(ref):
        return resistance_bounds(ref)[0]
    applicability=high_input_applicability(
        supply['source_requirement']['required_load_voltage_magnitude_V']['+5V'],
        resistance_bounds('R120'),resistance_bounds('R125'),current)
    upper={rail:values[1] for rail,values in supply['source_requirement']['required_load_voltage_magnitude_V'].items()}
    reference=3.31  # Explicit conditional assumption; coarse REF-good is insufficient.
    # Passive maximum principle: with zero sense leakage every resistor-only
    # internal node lies between VN and REF. Bounding each source branch
    # independently is deliberately loose; it avoids a nominal-only budget.
    ref_branches={
        'R102':(reference+upper['-12V'])/minimum('R102'),
        'R104':reference/minimum('R104'),
        'R105_R106':reference/(minimum('R105')+minimum('R106')),
        'R107_R108':reference/(minimum('R107')+minimum('R108')),
        # A negative fault clamps REF_SENSE: R113 no longer limits the feed.
        'R109_to_R112_clamped':reference/sum(minimum('R'+str(i)) for i in range(109,113)),
    }
    ref_output=sum(ref_branches.values())
    iq=sum(row['package_table_sum_A'] for row in current.values())
    base=upper['+5V']/minimum('R122')
    pullup=upper['+5V']/minimum('R119')
    bleed=upper['+5V']/(minimum('R120')+minimum('R125'))
    p5_div=upper['+5V']/sum(minimum('R'+str(i)) for i in range(116,119))
    p12_div=upper['+12V']/(minimum('R114')+minimum('R115'))
    dummy=upper['+12V']/minimum('R124')
    vn=(reference+upper['-12V'])/minimum('R101')
    states={}
    for state,base_on,fault_low,dummy_on in (
            ('fault_asserted',False,True,False),('permit_enabled',True,False,True),
            ('both_paths_conservative_dc_screen',True,True,True)):
        rows={'+5V':ref_output+iq+p5_div+base*base_on+pullup*fault_low+bleed*base_on,
              '+12V':p12_div+dummy*dummy_on,'-12V':vn}
        states[state]={'conditional_dc_A':rows,
            'unallocated_auxiliary_A':{rail:supply['load_envelope']['auxiliary_allowance_mA'][rail]/1000-value
                                      for rail,value in rows.items()}}
    return {'status':'CONDITIONAL DC ALLOCATION SCREEN; NO COMPLETE CURRENT ACCEPTANCE',
        'qualification_accepted':False,'total_dynamic_current_A':None,
        'reference_assumed_max_V':reference,
        'reference_output_branch_bounds_A':ref_branches,
        'reference_output_total_A':ref_output,
        'reference_load_charged_to_5V_once':True,
        'active_device_source_rows':current,
        'conditional_active_quiescent_sum_A':iq,
        'steady_high_icc_applicability':applicability,
        'timing_bleed_conditional_dc_A':bleed,
        'states':states,
        'original_auxiliary_allowance_mA':supply['load_envelope']['auxiliary_allowance_mA'],
        'original_supply_requirements_changed':False,
        'conditions_and_open_gates':[
          'Adopt the listed source-table currents outside their full source conditions only as explicit assumptions, not guarantees.',
          'Reference-divider load uses the top-only path when either TLV output clamps REF_SENSE to ground; this loose bound is retained in every screened state.',
          'Reference <=3.31V, negative rail nonpositive and normal rail bounds; coarse reference monitor does not establish this precision window.',
          'Zero capacitor leakage and zero input/output/off-state semiconductor leakage, ideal logic voltages within supply rails, passive resistor network and zero semiconductor drops for load-current bounds.',
          '25C resistance reference and -40..125C resistor/TCR envelope are analysis conditions, not installed thermal qualification.',
          'Source input current equals reference output demand plus reference IQ; no separate free reference supply.',
          'The SN74LVC1G17 ICC row specifies VI=5.5 V or GND, IO=0, VCC=1.65..5.5 V. Neither U104 nor U106 actual HIGH input is directly covered. U106 additionally retains a divided HIGH (nominal 4.545 V at 5 V). Additional steady input-stage current is unbounded; the separate 3.6 V ICC row and VCC-0.6 V DeltaICC point are not extrapolated.',
          'Both-path DC screen is not a transient maximum: LVC slow-input/switching current, cap charging and retained-charge return paths remain unbounded.',
          'Actual isolation loads, discharge circuits and remaining protection auxiliaries must share the original 20mA per-rail allowance.',
          'Ground-loss, partial-power/backfeed, startup, thermal and physical qualification remain open.'],
    }


def run(check=False):
    current,paths=load_current_facts()
    data=build(json.loads(SPEC.read_text()),json.loads(CATALOG.read_text()),json.loads(SUPPLY.read_text()),current)
    paths.update((SPEC,CATALOG,SUPPLY,Path(__file__).resolve(),Path(behavior.__file__).resolve()))
    data['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
    text=json.dumps(data,indent=2)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text: raise ValueError('current report drift')
    else: REPORT.write_text(text)
    print('PASS: conditional DC allocation reproduced; dynamic and physical current acceptance OPEN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
