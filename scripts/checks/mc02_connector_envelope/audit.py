"""Conditional FH12 field/dimension arithmetic, never physical containment."""
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


def number(text):
    if not isinstance(text,str):raise ValueError('decimal strings required')
    try:value=Decimal(text)
    except InvalidOperation as exc:raise ValueError('invalid decimal') from exc
    if not value.is_finite() or value<0:raise ValueError('nonfinite or negative dimension')
    return value


def budget(field_depth,nominal,tolerance,growth,registration=None):
    field,nom,tol,gap=map(number,(field_depth,nominal,tolerance,growth))
    if nom<tol:raise ValueError('dimension interval below zero')
    if registration is not None:raise ValueError('no reviewed field-to-physical registration admitted')
    maximum=nom+tol
    return {'unit':'mm','field_depth':str(field),'source_depth_interval':[str(nom-tol),str(maximum)],
        'field_minus_maximum_depth':str(field-maximum),
        'centered_residual_per_side':str((field-maximum)/2),
        'centering_condition':'COUNTERFACTUAL: exact shared center assumed solely for arithmetic; not established',
        'nominal_per_side_growth':str(gap),
        'depth_to_retain_growth_at_maximum':str(maximum+2*gap),
        'required_depth_scope':'COUNTERFACTUAL sizing arithmetic, not a new or adopted connector field',
        'registration':None,'physical_containment':'NOT_ESTABLISHED','adopted_field_depth':None}


def validate_source(evidence):
    source=evidence['drawing']
    if source['sha256']!=PDF_SHA or source['document']!='EDC3-150229-11' or source['bytes']!=1059562:
        raise ValueError('verified primary drawing identity changed')
    if source['depth']!={'unit':'mm','nominal':'5.6','tolerance':'0.3','locator':'printed sheets1/2, physical indices0/1, side view overall 5.6 +/-0.3'}:
        raise ValueError('reviewed depth datum changed')
    if source['closed_height']!={'unit':'mm','nominal':'2.0','tolerance':'0.2','locator':'printed sheets1/2, physical indices0/1, closed side view 2 +/-0.2 relative to b'}:
        raise ValueError('reviewed closed height datum changed')
    if evidence['field_to_physical_registration'] is not None:
        raise ValueError('field registration not established')


def extract(evidence,gate,options):
    validate_source(evidence)
    field=options['field']
    if field['growth_mm']['value']!=.25 or field['depth']['value']!=6.1:
        raise ValueError('retained nominal field changed')
    links=[r for r in gate['links'] if not r.get('gone')]
    if len(links)!=61 or len({r['id'] for r in links})!=61 or not all(r.get('placed') for r in links):
        raise ValueError('61 unique placed virtual links required')
    dimensions=budget(str(field['depth']['value']),'5.6','0.3',str(field['growth_mm']['value']))
    rows=[]
    variants={8:'FH12-8S-0.5SH(55), C597995',14:'FH12-14S-0.5SH(55), C5378715',
              26:'FH12-26S-0.5SH(55), C202113',40:'FH12-40S-0.5SH(55), C202114'}
    for link in links:
        if link['circuits'] not in variants or link['connector']!=variants[link['circuits']]:
            raise ValueError('exact selected connector variant changed')
        if link['direction'] not in ('+x','-x','+y','-y'):raise ValueError('unknown field direction')
        axis=0 if link['direction'].endswith('x') else 1
        for side,board,key in (('front',link['front_board'],'front_connector'),('K','K','K_connector')):
            rect=link['geometry'][key]
            vals=[number(str(v)) for v in rect]
            depth=vals[axis+2]-vals[axis]
            span=vals[3-axis]-vals[1-axis]
            if depth!=Decimal('6.1') or span!=Decimal('.5')*link['circuits']+Decimal('5.6'):
                raise ValueError('retained nominal field span does not reproduce')
            rows.append({'endpoint':link['id']+':'+side,'board':board,'board_face':'B','connector':link['connector'],
                'field_rectangle_panel_mm':rect,'field_depth_mm':str(depth),'field_long_axis_span_mm':str(span),
                'long_axis_scope':'Project nominal field span only; no physical width containment comparison admitted',
                'physical_containment':'NOT_ESTABLISHED'})
    return {'source_commit':evidence['source_commit'],'engineering_commit':evidence['engineering_commit'],
        'drawing':evidence['drawing'],'inputs_sha256':evidence['sha256'],'virtual_links':61,'virtual_endpoints':122,
        'depth_budget':dimensions,'closed_height_interval_mm':['1.8','2.2'],
        'closed_height_scope':'Drawing dimension only, not installed height. XY field growth cannot supply a Z tolerance or actuator-access guarantee.',
        'field_depth_source_status':field['depth']['status'],'endpoints':rows,
        'unresolved':['Body/terminal/land datum registration to the virtual field',
            'Full body, terminal and recommended land union with tolerances',
            'Mounted height/solder/board tolerances and actual access',
            'Guaranteed open swept envelope; parenthesized 4.8 and 90 degrees are reference only'],
        'scope':'SOURCE-ONLY CONDITIONAL ARITHMETIC. Positive total dimensional slack does not prove physical containment. No geometry edits, search, native, routing, DRC/fill, adoption or manufacturing.'}


def run(root=ROOT):
    evidence=json.loads(EVIDENCE.read_text())
    for path,pin in evidence['sha256'].items():
        if hashlib.sha256((root/path).read_bytes()).hexdigest()!=pin:raise ValueError('source pin changed: '+path)
    if evidence['sha256'].get(PDF)!=PDF_SHA:raise ValueError('primary PDF missing from pin closure')
    return extract(evidence,json.loads((root/GATE).read_text()),json.loads((root/OPTIONS).read_text()))


if __name__=='__main__':print(json.dumps(run(),indent=2))
