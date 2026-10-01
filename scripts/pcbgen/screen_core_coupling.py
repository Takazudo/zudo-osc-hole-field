"""Describe K coupling matrices without relabeling access as common budget.

Self, same-header and distinct-header entries are reported separately. None
is silently subtracted or promoted to a common/private allocation. This is a
floating postprocessing diagnostic, not a new outward numerical certificate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scripts.pcbgen.core_model_gate import require_native_prerequisite


def verify_actual_authority(receipt):
    prerequisite=receipt['core_native_prerequisite']
    dependencies=prerequisite['dependency_sha256']
    def unique(suffix,expected_digest=None):
        matches=[Path(p) for p,h in dependencies.items() if p.endswith(suffix) and (expected_digest is None or h==expected_digest)]
        if len(matches)!=1:raise ValueError('K screen needs one exact authority: '+suffix)
        return matches[0]
    native=unique('/ground-feasibility-geometry.json',receipt['native_export_sha256'])
    actual=require_native_prerequisite(native,
        unique('/ground-feasibility-native-receipt.json'),unique('/osc-core.receipt.json'))
    if actual!=prerequisite:raise ValueError('K screen native authority differs from solved prerequisite')
    if dependencies[str(native)]!=receipt['native_export_sha256']:
        raise ValueError('K screen native export hash differs from actual authority')
    data=json.loads(native.read_bytes())
    if data['board_sha256']!=receipt['board_sha256']:
        raise ValueError('K screen board differs from actual authority')


def verify_profile_basis(receipt,profiles):
    for key in ('native_export_sha256','model_source_sha256','core_native_prerequisite'):
        if profiles.get(key)!=receipt.get(key) or key not in profiles:
            raise ValueError('K profile sidecar differs in '+key)
    selected=receipt['core_native_prerequisite']['selected_contacts']
    expected={(p['ref'],p['pad']):p for p in selected}
    if (len(selected)!=215 or len(expected)!=215
            or sum(p['kind']=='GH' for p in selected)!=206
            or sum(p['kind']=='main' for p in selected)!=9
            or len({p['uuid'] for p in selected})!=215):
        raise ValueError('K screen requires complete unique 206 GH and nine main identities')
    refs=[p for p in selected if p['ref']==receipt['reference_main'] and p['kind']=='main']
    if len(refs)!=1:raise ValueError('K screen reference main is absent or ambiguous')
    reference=refs[0]
    matrix_ports=receipt['ports']+[{'ref':reference['ref'],'pad':reference['pad'],'kind':'main','layer':0}]
    ids=lambda rows:[(p['ref'],p['pad'],p['kind'],p['layer']) for p in rows]
    if ids(profiles.get('profiles',[]))!=ids(matrix_ports):
        raise ValueError('ordered K matrix/profile identities or reference differ')
    if len(matrix_ports)!=215 or {(p['ref'],p['pad']) for p in matrix_ports}!=set(expected):
        raise ValueError('K matrix/profile selected basis is incomplete or duplicated')
    mapped=receipt['all_native_AGND_pad_component_mapping']
    native={(p['ref'],p['pad']):p for p in mapped}
    if len(native)!=len(mapped) or len({p['uuid'] for p in mapped})!=len(mapped):
        raise ValueError('K native ground mapping contains duplicate identities or UUIDs')
    for p in matrix_ports:
        key=p['ref'],p['pad'];row=expected[key];physical=native.get(key)
        if (p['layer']!=0 or p['kind']!=row['kind'] or row['native_layer']!='F.Cu'
                or not row['main_connected'] or physical is None
                or physical['uuid']!=row['uuid'] or physical['layers']!=['F.Cu']):
            raise ValueError('K profile including reference has wrong role, physical face or UUID')


def summarize(receipt):
    prerequisite=receipt.get('core_native_prerequisite')
    if not prerequisite:raise ValueError('successful K coupling prerequisite required')
    selected=prerequisite['selected_contacts']
    expected={(p['ref'],p['pad']):p for p in selected}
    ports=receipt['ports'];reference=receipt['reference_main']
    references=[p for p in selected if p['ref']==reference and p['kind']=='main']
    if len(expected)!=len(selected) or len(references)!=1:
        raise ValueError('unique selected K identities and reference main required')
    refkey=(references[0]['ref'],references[0]['pad'])
    actual={(p['ref'],p['pad']):p for p in ports}
    if len(actual)!=len(ports) or set(actual)!=set(expected)-{refkey}:
        raise ValueError('matrix does not contain every selected K functional exactly once')
    for key,p in actual.items():
        if p['layer']!=0 or p['kind']!=expected[key]['kind']:
            raise ValueError('K functional face or role changed')
    upper=np.asarray(receipt['matrices_ohm']['upper'],dtype=float)
    lower=np.asarray(receipt['matrices_ohm']['lower'],dtype=float)
    if upper.shape!=(len(ports),len(ports)) or lower.shape!=upper.shape:
        raise ValueError('K matrix dimensions differ from selected profiles')
    if any(not np.isfinite(m).all() or not np.allclose(m,m.T,rtol=1e-10,atol=1e-12) for m in (upper,lower)):
        raise ValueError('finite reciprocal K matrices required')
    # Match the caller's absolute Ohm sanity tolerance. This eigenvalue test
    # is floating diagnostic validation, not an outward PSD certificate.
    # Do not project a malformed gap to the PSD cone.
    minimum_gap=float(np.linalg.eigvalsh((upper-lower+(upper-lower).T)/2)[0])
    if minimum_gap < -1e-9:raise ValueError('K variational gap is indefinite beyond diagnostic roundoff tolerance')
    gh=np.array([i for i,p in enumerate(ports) if p['kind']=='GH'])
    if not len(gh):raise ValueError('K GH observations required')
    mains=[(reference,None)]+[(p['ref'],i) for i,p in enumerate(ports) if p['kind']=='main']
    rows=[]
    for name,index in mains:
        def rebase(m):return m if index is None else m-m[:,index,None]-m[index,None,:]+m[index,index]
        u,l=rebase(upper),rebase(lower);gap=np.diag(u-l)
        if min(gap)<-1e-10:raise ValueError('K negative variational diagonal gap')
        width=.5*np.sqrt(np.maximum(gap[gh,None],0)*np.maximum(gap[gh][None,:],0))
        centre=((u+l)/2)[np.ix_(gh,gh)]
        absolute=abs(centre)+width
        def worst(mask):
            if not mask.any():return None
            a,b=np.unravel_index(np.argmax(np.where(mask,absolute,-np.inf)),absolute.shape)
            return {'observation':{k:ports[gh[a]][k] for k in ('ref','pad')},
                'injection':{k:ports[gh[b]][k] for k in ('ref','pad')},
                'centre_ohm':float(centre[a,b]),'interval_halfwidth_ohm':float(width[a,b]),
                'absolute_interval_upper_ohm':float(absolute[a,b])}
        same=np.array([[ports[a]['ref']==ports[b]['ref'] for b in gh] for a in gh])
        diagonal=np.eye(len(gh),dtype=bool)
        rows.append({'reference_main':name,'full_self':worst(diagonal),
            'same_header_distinct_contact':worst(same & ~diagonal),
            'distinct_header_transfer':worst(~same),
            'GH_self_upper_ohm':[{'ref':ports[i]['ref'],'pad':ports[i]['pad'],'upper_ohm':float(u[i,i])} for i in gh]})
    return {'status':'NOT ACCEPTED: nominal finite coupling profiles; floating postprocessing only',
        'reference_reports':rows,'profile_count':len(ports),'selected_contact_count':len(selected),
        'gap_PSD_diagnostic':{'minimum_eigenvalue_ohm':minimum_gap,'negative_roundoff_tolerance_ohm':1e-9,'outward_certificate':False},
        'interpretation':'All full self terms include main and GH accesses. Same-header and distinct-header classifications are identities only, not private/common energy partitions. No term is subtracted and no K allocation or own-load bound is inferred.',
        'own_load_scope':prerequisite['own_load_scope'],
        'native_export_sha256':receipt['native_export_sha256'],
        'model_source_sha256':receipt['model_source_sha256']}


def run(matrix_path,output):
    matrix_path=Path(matrix_path);output=Path(output)
    algorithm_path=Path(__file__);algorithm_bytes=algorithm_path.read_bytes()
    if output.exists():raise ValueError('use a fresh diagnostic output')
    raw=matrix_path.read_bytes();receipt=json.loads(raw)
    binding=receipt['profile_receipt'];profile_path=Path(binding['path'])
    expected_path=matrix_path.with_name(matrix_path.stem+'-profiles.json').resolve()
    if profile_path.resolve()!=expected_path:raise ValueError('unexpected profile sidecar path')
    profile_bytes=profile_path.read_bytes()
    if hashlib.sha256(profile_bytes).hexdigest()!=binding['sha256']:
        raise ValueError('K profile bytes differ from solver binding')
    verify_profile_basis(receipt,json.loads(profile_bytes))
    verify_actual_authority(receipt)
    result=summarize(receipt)
    result['input_artifacts']={'matrix':{'path':str(matrix_path.resolve()),'sha256':hashlib.sha256(raw).hexdigest()},
        'profiles':dict(binding),'algorithm_sha256':hashlib.sha256(algorithm_bytes).hexdigest()}
    if matrix_path.read_bytes()!=raw or profile_path.read_bytes()!=profile_bytes:
        raise ValueError('K matrix/profile input changed during diagnostic')
    if algorithm_path.read_bytes()!=algorithm_bytes:
        raise ValueError('K screen algorithm source changed during diagnostic')
    with output.open('x') as f:f.write(json.dumps(result,indent=2,sort_keys=True)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('matrix',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    report=run(a.matrix,a.output)
    print(json.dumps([{k:v for k,v in r.items() if k!='GH_self_upper_ohm'} for r in report['reference_reports']],indent=2))
