"""Counterfactual recommended-land registration intervals; no CAD transform."""
from collections import Counter
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
EVIDENCE=Path(__file__).with_name('evidence.json')
GATE='design/stack/geometry/links/link-gate.json'
OPTIONS='design/stack/geometry/links/link-gate-options.json'
PDF='.circuit-cache/sources/manufacturer-transfer-20261117/hirose-EDC3-150229-11.pdf'
PDF_SHA='c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07'


def decimal(text):
    if not isinstance(text,str):raise ValueError('decimal string required')
    try:out=Decimal(text)
    except InvalidOperation as exc:raise ValueError('invalid decimal') from exc
    if not out.is_finite():raise ValueError('finite decimal required')
    return out


def limits(dimension):
    if dimension['unit']!='mm':raise ValueError('explicit mm unit required')
    n,t=decimal(dimension['nominal']),decimal(dimension['tolerance'])
    if t<0 or n<t:raise ValueError('invalid dimension interval')
    return n-t,n+t


def land_y(dimensions):
    pad=dimensions['signal_pad_length'];gap=dimensions['pad_to_tab_gap'];tab=dimensions['tab_length']
    pmax=limits(pad)[1];gmax=limits(gap)[1];tmax=limits(tab)[1]
    pn,gn,tn=(decimal(x['nominal']) for x in (pad,gap,tab))
    return {'nominal':[str(-pn/2),str(pn/2+gn+tn)],
            'outer_interval':[str(-pmax/2),str(pmax/2+gmax+tmax)],
            'derivation':'lower=-signal_pad_max/2; upper=signal_pad_max/2+gap_max+tab_max',
            'scope':'Independent endpoint extrema in a reviewer-defined row-midpoint frame; no physical field registration'}


def registration_interval(field_size,feature_min,feature_max,clearance):
    field,lo,hi,margin=map(decimal,(field_size,feature_min,feature_max,clearance))
    if field<=0 or hi<lo or margin<0:raise ValueError('invalid registration interval input')
    lower=-field/2+margin-lo
    upper=field/2-margin-hi
    return {'lower_mm':str(lower),'upper_mm':str(upper),
            'status':'NONEMPTY_CONDITIONAL_INTERVAL' if lower<=upper else 'EMPTY_CONDITIONAL_INTERVAL'}


def validate(evidence):
    if evidence['drawing']['sha256']!=PDF_SHA or evidence['drawing']['document']!='EDC3-150229-11':
        raise ValueError('reviewed primary source identity changed')
    expected={'signal_pad_length':('1.3','0.1'),'pad_to_tab_gap':('1.5','0.1'),
              'tab_length':('2.2','0.1')}
    for name,(nominal,tolerance) in expected.items():
        if evidence['dimensions'][name]!={'unit':'mm','nominal':nominal,'tolerance':tolerance}:
            raise ValueError('reviewed PCB mounting pattern dimension changed')
    if evidence['land_G_mm']!={'8':'9.1','14':'12.1','26':'18.1','40':'25.1'} or evidence['land_G_tolerance_mm']!='0.1':
        raise ValueError('reviewed G table or tolerance changed')
    pad=evidence['signal_pad_x_bound']
    if (pad['pad_width_nominal_mm'],pad['pad_width_tolerance_mm'],pad['conservative_per_axis_position_mm'])!=('0.3','0.03','0.05'):
        raise ValueError('reviewed conservative signal pad bound changed')
    if evidence['actual_registration'] is not None or evidence['full_body_terminal_union_established'] is not False:
        raise ValueError('actual registration/full union not established')


def extract(evidence,gate,options):
    validate(evidence)
    if options['field']['depth']['value']!=6.1 or options['field']['growth_mm']['value']!=.25:
        raise ValueError('retained field changed')
    links=[r for r in gate['links'] if not r.get('gone')]
    if len(links)!=61 or len({r['id'] for r in links})!=61 or not all(r.get('placed') for r in links):
        raise ValueError('exact61 virtual link inventory required')
    counts=Counter(r['circuits'] for r in links)
    if set(counts)!={8,14,26,40}:raise ValueError('selected contact-count set changed')
    exact={x['circuits']:x['connector'] for x in options['sizes']}
    if any(r['connector']!=exact[r['circuits']] for r in links):raise ValueError('selected connector identity mismatch')
    y=land_y(evidence['dimensions']);rows=[]
    for n in sorted(counts):
        A=Decimal('.5')*(n-1);G=A+Decimal('5.6')
        if G!=decimal(evidence['land_G_mm'][str(n)]):raise ValueError('G formula/table mismatch')
        maxG=G+decimal(evidence['land_G_tolerance_mm'])
        pad=evidence['signal_pad_x_bound']
        signal_span=A+2*decimal(pad['conservative_per_axis_position_mm'])+decimal(pad['pad_width_nominal_mm'])+decimal(pad['pad_width_tolerance_mm'])
        if signal_span>maxG:raise ValueError('tab G no longer dominates conservative signal pad span')
        field_width=Decimal('.5')*n+Decimal('5.6')
        scenarios=[]
        for margin in ('0','0.25'):
            dx=registration_interval(str(field_width),str(-maxG/2),str(maxG/2),margin)
            dy=registration_interval(str(options['field']['depth']['value']),*y['outer_interval'],margin)
            scenarios.append({'additional_per_side_clearance_mm':margin,'delta_x':dx,'delta_y':dy,
                'joint_interval_status':'EMPTY_CONDITIONAL_RECTANGLE' if any(d['status'].startswith('EMPTY') for d in (dx,dy)) else 'NONEMPTY_CONDITIONAL_RECTANGLE',
                'interpretation':'COUNTERFACTUAL LAND-ONLY interval arithmetic; not an adopted registration or physical containment result'})
        rows.append({'contacts':n,'connector':exact[n],'links':counts[n],'endpoints':2*counts[n],
            'field_width_mm':str(field_width),'field_depth_mm':str(options['field']['depth']['value']),
            'land_G_nominal_mm':str(G),'land_G_maximum_mm':str(maxG),
            'conservative_signal_pad_span_mm':str(signal_span),'signal_pad_span_scope':pad['scope'],
            'tab_G_dominates_signal_pad_span':True,'land_y':y,'scenarios':scenarios,
            'actual_registration':None,'adopted_registration':None,'physical_containment':'NOT_ESTABLISHED'})
    return {'source_commit':evidence['source_commit'],'engineering_commit':evidence['engineering_commit'],
            'inputs_sha256':evidence['sha256'],'drawing':evidence['drawing'],'coordinate_convention':evidence['coordinate_convention'],
            'variants':rows,'virtual_links':61,'virtual_endpoints':122,'full_body_terminal_union_established':False,
            'scope':'Recommended PCB land-only counterfactual arithmetic. Actual field-to-pad-row registration, body/terminal union, mounted geometry and access remain unestablished. No geometry, native, placement, routing, DRC/fill, adoption or manufacturing action.'}


def run(root=ROOT):
    evidence=json.loads(EVIDENCE.read_text())
    if evidence['sha256'].get(PDF)!=PDF_SHA:raise ValueError('missing primary PDF pin')
    for path,pin in evidence['sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=pin:raise ValueError('source pin changed: '+path)
    return extract(evidence,json.loads((root/GATE).read_text()),json.loads((root/OPTIONS).read_text()))


if __name__=='__main__':print(json.dumps(run(),indent=2))
