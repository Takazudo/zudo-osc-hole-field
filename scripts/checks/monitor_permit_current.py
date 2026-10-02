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
FACTS={
 'U101':('component-monitor-permit-candidates','monitor-tps37044mjofddfrq1',1),
 'U102':('component-monitor-permit-candidates','monitor-tlv9022dr',2),
 'U103':('component-monitor-permit-candidates','monitor-ref3433tidbvr',1),
 'U104':('component-monitor-permit-candidates','monitor-sn74lvc1g17dbvr',1),
 'U105':('component-monitor-permit-candidates','monitor-sn74lvc1g74dctr',1),
 'U106':('component-monitor-permit-candidates','monitor-sn74lvc1g17dbvr',1),
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
    def minimum(ref):
        p=parts[ref]; e=exact[p['mpn']]
        if p['value']!=e['resistance_ohm']:
            raise ValueError('resistance and MPN disagree')
        # Analysis reference 25C and -40..125C envelope, not a manufacturer
        # nominal-resistance reference-temperature qualification.
        tolerance=e['tolerance_fraction']; drift=100*e['tcr_abs_per_C']
        if (not math.isfinite(tolerance) or not math.isfinite(drift)
                or not 0 <= tolerance < 1 or not 0 <= drift < 1):
            raise ValueError('invalid independent resistor condition')
        factor=(1-tolerance)*(1-drift)
        if not 0 < factor <= 1:
            raise ValueError('invalid resistor condition')
        return p['value']*factor
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
          'U106 input settles near4.545V at5V supply through the bleed divider: its sustained HIGH is not the ICC rail-level test condition. Additional steady input-stage current is unbounded; the DeltaICC row atVCC-0.6V is not extrapolated.',
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
