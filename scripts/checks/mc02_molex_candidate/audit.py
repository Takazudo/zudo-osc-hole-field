"""Exact unadopted Molex150200075 source comparison; no model execution."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
GATE = 'design/stack/geometry/links/link-gate.json'
BINDING = {'mpn': '150200075', 'document': 'SD-15020-001', 'revision': 'F',
           'sheet': 1, 'contacts': 8, 'type': 'A', 'contact_side': 'same-side',
           'length_nominal_mm': '51', 'length_tolerance_mm': '2',
           'locator': 'sheet1 N8 row / 51 +/-2mm column / type A; type diagrams lower left'}
# Nominal/tolerance pairs transcribed from the reviewed drawing, never scaled from a render.
DIMENSIONS = {'tail_thickness': ('0.30','0.05'), 'total_width': ('4.50','0.10'),
              'exposed_length': ('4.00','0.80'), 'support_length': ('6.00','2.00'),
              'conductor_width': ('0.30','0.03'), 'length': ('51','2')}
PRIOR_SHA = '8768bb1cb657069d9d136a5ee1f555f8d1ffcffe6a184602c60b2107859e9472'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def interval(record):
    if record['unit'] != 'mm' or record['basis'] != 'explicit_plus_minus':
        raise ValueError('explicit mm tolerance required')
    n,t = (Decimal(record[k]) for k in ('nominal','tolerance'))
    if not n.is_finite() or not t.is_finite() or n<0 or t<0 or n<t:
        raise ValueError('invalid interval')
    return n-t,n+t


def compare(record, target):
    low,high=interval(record);lo=Decimal(target['lower']);hi=target['upper']
    if target['unit']!='mm': raise ValueError('comparator units')
    short=max(Decimal(0),lo-low);excess=max(Decimal(0),high-Decimal(hi)) if hi is not None else Decimal(0)
    return {'declared_interval_mm':[str(low),str(high)],
            'relation':'NOT_CONTAINED' if short or excess else 'CONTAINED',
            'lower_shortfall_mm':str(short),'upper_excess_mm':str(excess)}


def validate(evidence, links):
    if evidence['binding'] != BINDING: raise ValueError('exact order-code/table binding drift')
    if set(evidence['dimensions']) != set(DIMENSIONS): raise ValueError('dimension set drift')
    for field,(n,t) in DIMENSIONS.items():
        row=evidence['dimensions'][field]
        interval(row)
        if (row['nominal'],row['tolerance']) != (n,t): raise ValueError('dimension semantic drift: '+field)
    if evidence['nominal_layers'] != {'copper_mm':'0.10','polyester_adhesive_each_mm':'0.086','stiffener_polyester_mm':'0.155','tolerance':None}:
        raise ValueError('nominal-only layers promoted or changed')
    if evidence['prior_51mm_result_sha256'] != PRIOR_SHA: raise ValueError('historical receipt changed')
    selected=[r for r in links if not r.get('gone') and r['cable']=='C29534']
    ids=[r['id'] for r in selected]
    if len(ids)!=28 or len(set(ids))!=28 or sorted(ids)!=evidence['candidate_link_ids']:
        raise ValueError('exact28 candidate link set drift')
    if any(r['circuits']!=8 or r['cable_length_mm']!=50 for r in selected):
        raise ValueError('existing engineering link properties changed')
    return ids


def audit(root=ROOT):
    e=json.loads((HERE/'evidence.json').read_text())
    for path,sha in e['sha256'].items():
        if digest(root/path)!=sha: raise ValueError('source pin changed: '+path)
    ids=validate(e,json.loads((root/GATE).read_text())['links'])
    connector=json.loads((root/'scripts/checks/mc02_cable_contract/evidence.json').read_text())['connector']
    if connector['source']['sha256']!='9f056f58ff000739633cc3cb7697ba185967083dcf1429b7ab10783b3f55bac5':
        raise ValueError('FH12 comparator source changed')
    rows=[]
    for field in ('tail_thickness','total_width','exposed_length','support_length'):
        c=connector['criteria'][field];target=c.get('by_contacts',{}).get('8',c.get('value'))
        result=compare(e['dimensions'][field],target)
        rows.append({'field':field,'source':e['dimensions'][field], 'comparator':target,
            'comparator_class':c['class'],'connector_locator':c['locator'],
            'comparison_scope':'CONDITIONAL_DATUM_MAPPING' if field=='support_length' else 'DECLARED_DIMENSIONS_ONLY',
            'actual_datum_mapping':None if field=='support_length' else 'named dimension comparison',**result})
    material=json.loads((root/'design/stack/link-electrical/inputs.json').read_text())['cable']
    return {'status':'SOURCE_COMPARISON_ONLY; NO_ADOPTION', 'source_commit':e['source_commit'],
        'engineering_commit':e['engineering_commit'],'binding':BINDING,'sha256':e['sha256'],
        'candidate_link_ids':sorted(ids),'comparisons':rows,
        'stiffener':{'nominal_mm':'0.155','guaranteed_interval_mm':None,'recommended_minimum_mm':'0.188',
            'nominal_relation':'BELOW_RECOMMENDATION','interval_verdict':'UNSOURCED_TOLERANCE',
            'locator':'sheet2 cross-section 0.155mm polyester; FH12 catalog printedp11 upper stiffener0.188MIN'},
        'finish':{'drawing_label':'Au plating','category_relation':'GOLD_NAME_AGREEMENT_ONLY','plating_qualification':'NOT_ESTABLISHED'},
        'material_comparison':{'candidate_copper_nominal_mm':'0.10','existing_model_copper_mm':material['pitch_0_5']['conductor_thickness_mm'],
            'candidate_conductor_width_interval_mm':[str(v) for v in interval(e['dimensions']['conductor_width'])],
            'missing_candidate_bounds':['copper thickness tolerance','rho(T)','effective dielectric/finite-thickness model','end/contact resistance and coupling'],
            'candidate_material_parameters_bound':False,'model_applicability':'NOT_ESTABLISHED',
            'finite_thickness_caution':'Retained capacitance kernel is coplanar zero-thickness; eps_eff sweep does not establish applicability to0.10mm copper','existing_assumed_eps_eff':material['eps_eff'],
            'existing_assumed_end_equivalent_mm':material['end_equivalent_mm']},
        'length':{'candidate_interval_mm':[str(v) for v in interval(e['dimensions']['length'])],
            'prior_51mm_result_sha256':PRIOR_SHA,'prior_scope':'51mm nominal only; unchanged LX-based material inputs',
            'tolerance_or_exact_product_qualification':'NOT_ESTABLISHED'},
        'terminal_positional_datum_conformity':{'status':'NOT_ASSESSED',
            'reason':'EDC sheet3 basic boxed0.5 pitch and nX true-position0.05 datumZ are not equivalent to Molex0.50+/-0.05 pitch and0.5(N-1)+/-0.10 span; no scalar GD&T conformity inferred'},
        'physical_compatibility':'NOT_ESTABLISHED','native':'NOT_RUN','electrical_model_run':'NOT_RUN',
        'holds':['DRC','fill','hardware adoption','manufacturing']}


if __name__=='__main__': print(json.dumps(audit(),indent=2))
