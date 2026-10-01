#!/usr/bin/env python3
"""Invert conditional negative-monitor normal-band margins; not fault acceptance."""
import argparse
import hashlib
import json
import math
from fractions import Fraction as F
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks import negative_monitor_network as negative
from scripts.checks import rail_monitor_candidate as rail
REPORT=ROOT/'design/power/monitor-reference-compatibility-report.json'


def fraction(value):
    return {'numerator':value.numerator,'denominator':value.denominator}


def inward(value,lower):
    """Decimal usable endpoint strictly inside the exact mathematical boundary."""
    scale=10**12
    integer=math.floor(value*scale)+1 if lower else math.ceil(value*scale)-1
    out=float(F(integer,scale));parsed=rail.number(out)
    if (parsed<=value if lower else parsed>=value):
        raise ValueError('display conversion did not remain strictly inside boundary')
    return out


def corner_equations(spec):
    conditions=spec['conditions']
    bias=rail.number(conditions['powered_input_bias_per_pin_A'])
    error=rail.number(conditions['powered_comparator_error_V'])
    if min(bias,error)<0:raise ValueError('negative comparator error envelope')
    result=[]
    for resistance in negative.resistor_corners(spec):
        rn,rr,rg=(resistance[n] for n in ('RN','RR','RG'))
        if min(resistance.values())<=0:raise ValueError('positive resistor values required')
        conductance=1/rn+1/rr+1/rg
        equations={}
        for event,top,bottom in (('UV','RU','RUG'),('OV','RO','ROG')):
            rt,rb=resistance[top],resistance[bottom]
            slope=rn*(1/rr-conductance*rb/(rt+rb))
            spread=rn*(conductance*(error+bias*rt*rb/(rt+rb))+2*bias)
            if slope<=0:raise ValueError('nonpositive reference sensitivity requires different inequalities')
            equations[event]=(slope,spread)
        result.append((resistance,equations))
    return result


def calculate(spec,bands):
    if len(bands)!=2 or not 0<rail.number(bands[0])<rail.number(bands[1]):
        raise ValueError('ordered positive normal band required')
    low,high=map(rail.number,bands)
    corners=corner_equations(spec)
    bounds={'lower_OV':None,'upper_UV':None}
    for resistance,equations in corners:
        for label,event,rail_limit,direction in (('lower_OV','OV',high,1),('upper_UV','UV',low,-1)):
            slope,spread=equations[event]
            boundary=(rail_limit+direction*spread)/slope
            old=bounds[label]
            if old is None or (boundary>old['boundary'] if direction==1 else boundary<old['boundary']):
                bounds[label]={'boundary':boundary,'slope':slope,'spread':spread,'resistors':resistance}
    lower,upper=(bounds[key]['boundary'] for key in ('lower_OV','upper_UV'))
    if lower>=upper:raise ValueError('empty strict common compatibility interval')
    trips={event:[min(eq[event][0]*lower-eq[event][1] for _,eq in corners),
                  max(eq[event][0]*upper+eq[event][1] for _,eq in corners)] for event in ('UV','OV')}
    nominal={p['ref']:rail.number(p['ohm']) for p in spec['resistors']}
    ref=F('3.2');vn=F('-10.9')
    nodes,_,_=negative.nodal(spec,nominal,{'AGND':F(),'REF':ref,'VN':vn})
    narrow=list(map(rail.number,spec['reference']['normal_target_V']))
    return {
        'status':'CONDITIONAL NORMAL-BAND COMPATIBILITY ONLY; NOT REFERENCE VALIDITY OR FAULT ACCEPTANCE',
        'qualification_accepted':False,'canonical_protection_implemented':False,
        'reference_requirement_changed':False,'fault_rejection_accepted':False,
        'normal_negative_rail_magnitude_V':bands,'original_reference_assumption_V':spec['reference']['normal_target_V'],
        'original_assumption_strictly_inside':lower<narrow[0]<=narrow[1]<upper,
        'resistor_corner_count':len(corners),
        'strict_reference_boundaries_exact':{'lower':fraction(lower),'upper':fraction(upper)},
        'inward_display_reference_interval_V':[inward(lower,True),inward(upper,False)],
        'limiting_corner_witnesses':{label:{'boundary_V':fraction(row['boundary']),
            'trip_slope_V_per_V':fraction(row['slope']),'trip_error_spread_V':fraction(row['spread']),
            'resistance_ohm':{ref:fraction(value) for ref,value in row['resistors'].items()}}
            for label,row in bounds.items()},
        'trip_magnitude_enclosure_over_interval_closure_V':{event:[rail.display(a,False),rail.display(b,True)] for event,(a,b) in trips.items()},
        'forced_nominal_counterexample':{'reference_V':float(ref),'negative_rail_V':float(vn),
            'reference_inside_compatibility_interval':lower<ref<upper,
            'sense_nodes_V':{n:float(nodes[n]) for n in ('SENSE','UV','OV')},
            'comparators_ideal_released':nodes['OV']<nodes['SENSE']<nodes['UV'],
            'negative_rail_inside_normal_band':low<=-vn<=high,
            'scope':'Prescribed DC, nominal resistors, zero comparator/input-current error; not a claimed reachable trajectory.'},
        'conditions':spec['conditions'],
        'limits':[
            'Strict inequalities preserve positive normal-band margins; equality at a limiting witness loses acceptance.',
            'The displayed usable interval is rounded inward; exact fractional boundaries and witness equations are authoritative.',
            'Trip envelopes use the closure of the reference interval and independent resistor/error corners; no one device is claimed to span the whole envelope.',
            'This calculation prevents false rejection of normal rails under assumptions. It does not ensure rejection of every unsafe rail.',
            'Comparator error, input-current/TCR applicability, independent reference validity, dynamic response and ground integrity retain their existing open source/physical conditions.',
            'Do not replace the historical reference range or dependent current/pin screens without separate fault-rejection and source qualification.',
            'No protection hardware implementation, installed or bench qualification is inferred.'],
    }


def run(check=False):
    paths={negative.SPEC,negative.SOURCES,Path(negative.__file__),Path(rail.__file__),Path(__file__)}
    snapshot={p:p.read_bytes() for p in paths}
    spec=json.loads(snapshot[negative.SPEC])
    supply=ROOT/spec['normal_voltage_source'];snapshot[supply]=supply.read_bytes()
    negative.validate(spec)
    bands=json.loads(snapshot[supply])['source_requirement']['required_load_voltage_magnitude_V']['-12V']
    report=calculate(spec,bands)
    if any(p.read_bytes()!=data for p,data in snapshot.items()):
        raise ValueError('reference compatibility inputs changed during calculation')
    report['input_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(data).hexdigest() for p,data in sorted(snapshot.items())}
    text=json.dumps(report,indent=2,allow_nan=False)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text:raise ValueError('reference compatibility report drift')
    else:REPORT.write_text(text)
    print('PASS: conditional inverse normal-band diagnostic; reference/fault acceptance OPEN')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    run(parser.parse_args().check)
