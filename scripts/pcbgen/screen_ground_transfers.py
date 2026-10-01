"""All-contact transfer interval screen with an explicit aggregate current class.

Role caps are optional supplied conditions, never inferred from planning
worksheets or passive pin types. This is a numerical diagnostic, not physical
contact, current, manufacturing or K-allocation acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def bounded_absolute_current(coefficients,caps,total):
    """Maximum linear absolute-current envelope; all signs remain admissible."""
    coefficients=np.asarray(coefficients,dtype=float);caps=np.asarray(caps,dtype=float)
    if coefficients.shape!=caps.shape or coefficients.ndim!=1 or not np.isfinite(coefficients).all() or not np.isfinite(caps).all() or not np.isfinite(total):
        raise ValueError('finite matching current-bound vectors required')
    if np.any(caps<0) or np.any(coefficients<0) or total<0:raise ValueError('negative current bound')
    order=np.argsort(-np.asarray(coefficients));remaining=total;value=0.;allocation=[]
    for index in order:
        current=min(float(caps[index]),remaining)
        if current:
            value+=float(coefficients[index])*current
            allocation.append((int(index),current));remaining-=current
        if remaining<=0:break
    return value,allocation


def screen(receipt,ledger,role_caps=None):
    if receipt['board_sha256']!=ledger['board_sha256']:
        raise ValueError('matrix and current-role ledger have different board identities')
    if not ledger.get('native_export_sha256') or receipt['native_export_sha256']!=ledger['native_export_sha256']:
        raise ValueError('matrix and current-role ledger have different native export identities')
    U=np.asarray(receipt['matrices_ohm']['upper'],dtype=float);L=np.asarray(receipt['matrices_ohm']['lower'],dtype=float)
    ports=receipt['ports'];roles={(p['ref'],p['pad']):p['category'] for p in ledger['pads']}
    if len(roles)!=len(ledger['pads']):raise ValueError('duplicate ground ledger contact')
    expected={(p['ref'],p['pad']):p for p in ledger['pads']}
    reference=[key for key in expected if key[0]==receipt['reference_main']]
    if len(reference)!=1 or expected[reference[0]]['category']!='main_wire_boundary':
        raise ValueError('exact reference main contact is absent or ambiguous')
    actual={(p['ref'],p['pad']):p for p in ports}
    if len(actual)!=len(ports) or set(actual)!=set(expected)-set(reference):
        raise ValueError('matrix does not cover every exact ground contact once')
    for key,port in actual.items():
        row=expected[key]
        kind=('load' if row['possible_normal_return_basis'] else
              'GH' if row['category']=='GH_return_observation' else 'main')
        if port['kind']!=kind:raise ValueError('matrix current/observation role differs from source ledger')
    represented={(p['ref'],p['pad']):p['uuid'] for p in receipt['all_native_AGND_pad_component_mapping']}
    if len(represented)!=len(receipt['all_native_AGND_pad_component_mapping']) or represented!={key:p['uuid'] for key,p in expected.items()}:
        raise ValueError('matrix native contact UUID inventory differs from ledger')
    if U.shape!=(len(ports),len(ports)) or L.shape!=U.shape or not np.isfinite(U).all() or not np.isfinite(L).all():
        raise ValueError('finite matrix dimensions must match exact ground contacts')
    if not np.allclose(U,U.T,rtol=1e-10,atol=1e-12) or not np.allclose(L,L.T,rtol=1e-10,atol=1e-12):
        raise ValueError('ground transfer matrices must be reciprocal')
    gh=np.array([i for i,p in enumerate(ports) if p['kind']=='GH'])
    loads=np.array([i for i,p in enumerate(ports) if p['kind']=='load'])
    if not len(gh) or not len(loads):raise ValueError('all GH observations and actual load basis are required')
    references=[(receipt['reference_main'],None)]+[(p['ref'],i) for i,p in enumerate(ports) if p['kind']=='main']
    aggregate=float(ledger['normal_transfer_envelope']['aggregate_absolute_current_A'])
    if not np.isfinite(aggregate) or aggregate<=0:raise ValueError('positive finite aggregate current required')
    caps=np.array([float((role_caps or {}).get(roles[ports[i]['ref'],ports[i]['pad']],aggregate)) for i in loads])
    result=[]
    for reference,index in references:
        def rebase(M):
            return M if index is None else M-M[:,index,None]-M[index,None,:]+M[index,index]
        u,l=rebase(U),rebase(L);gap=u-l;centre=(u+l)/2
        diagonal=np.diag(gap)
        if diagonal.min()<-1e-10:raise ValueError('negative variational diagonal gap')
        widths=.5*np.sqrt(np.maximum(diagonal[gh,None],0)*np.maximum(diagonal[loads][None,:],0))
        coefficients=abs(centre[np.ix_(gh,loads)])+widths
        observations=[]
        for row,g in enumerate(gh):
            voltage,allocation=bounded_absolute_current(coefficients[row],caps,aggregate)
            observations.append({'GH_ref':ports[g]['ref'],'GH_pad':ports[g]['pad'],
                'absolute_voltage_upper_V':voltage,'equivalent_transfer_upper_ohm':voltage/aggregate,
                'extreme_current_allocation':[{'ref':ports[loads[j]]['ref'],'pad':ports[loads[j]]['pad'],
                    'role':roles[ports[loads[j]]['ref'],ports[loads[j]]['pad']],'absolute_current_A':current,
                    'centre_ohm':float(centre[g,loads[j]]),'interval_halfwidth_ohm':float(widths[row,j])}
                    for j,current in allocation]})
        result.append({'reference_main':reference,'worst':max(observations,key=lambda r:r['absolute_voltage_upper_V']),
            'observations':observations})
    return {'status':'NOT ACCEPTED: numerical profiles and supplied current conditions only',
        'screen_algorithm_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_receipts':{'matrix_content_sha256':content_hash(receipt),'ledger_content_sha256':content_hash(ledger),
            'native_export_sha256':receipt['native_export_sha256'],'model_source_sha256':receipt['model_source_sha256'],
            'phase_provenance':receipt.get('phase_provenance',{}),'supplied_role_caps_content_sha256':content_hash(role_caps or {})},
        'board_sha256':receipt['board_sha256'],'aggregate_absolute_current_A':aggregate,
        'role_caps_A':role_caps or {},'source_conditions':ledger['normal_transfer_envelope'],
        'method':'For each compatible Loewner bracket, |Z_ab| <= |(U+L)_ab/2| + sqrt((U-L)_aa*(U-L)_bb)/2. Maximize its conservative weighted absolute-current bound under one aggregate sum and the explicitly supplied role caps.',
        'references':result}


def content_hash(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def bind_artifacts(result,matrix_path,ledger_path,role_caps_path=None):
    for name,path in (('matrix',matrix_path),('ledger',ledger_path)):
        raw=Path(path).read_bytes()
        if content_hash(json.loads(raw))!=result['input_receipts'][name+'_content_sha256']:
            raise ValueError('ground screen input changed: '+name)
        result.setdefault('input_artifacts',{})[name]={'path':str(Path(path).resolve()),'sha256':hashlib.sha256(raw).hexdigest()}
    matrix=json.loads(Path(matrix_path).read_bytes())
    stored=matrix.get('profile_receipt')
    if stored:
        path=Path(stored['path']);expected=stored['sha256']
    else:
        # Reviewed potential-only reuse retains the exact original profile
        # digest and copies those identical bytes to its own sidecar.
        path=Path(matrix_path).with_name(Path(matrix_path).stem+'-profiles.json')
        expected=matrix.get('phase_provenance',{}).get('potential',{}).get('exact_original_profile_sha256')
    if not expected or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        raise ValueError('ground finite-profile receipt differs from its matrix binding')
    result['input_artifacts']['profiles']={'path':str(path.resolve()),'sha256':expected}
    if role_caps_path is not None:
        raw=Path(role_caps_path).read_bytes()
        if content_hash(json.loads(raw))!=result['input_receipts']['supplied_role_caps_content_sha256']:
            raise ValueError('supplied current conditions changed')
        result['input_artifacts']['role_caps']={'path':str(Path(role_caps_path).resolve()),'sha256':hashlib.sha256(raw).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('matrix',type=Path);p.add_argument('ledger',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--role-caps',type=Path);a=p.parse_args()
    result=screen(json.loads(a.matrix.read_text()),json.loads(a.ledger.read_text()),json.loads(a.role_caps.read_text()) if a.role_caps else None)
    bind_artifacts(result,a.matrix,a.ledger,a.role_caps)
    a.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps([{'reference_main':r['reference_main'],**r['worst']} for r in result['references']],indent=2))
