"""Reuse only byte-identical completed native batches; incomplete output never passes."""
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.audit_added_mask import new_silk_identities

sha=lambda b:hashlib.sha256(b).hexdigest()


def validate_source(root,before,after,batch_size,output):
    root=Path(root)
    if type(batch_size) is not int or batch_size not in (4,16):raise ValueError('resume requires explicit native batch size4or16')
    if output.exists():raise ValueError('resume output must be a new directory')
    result=json.loads((root/'result.json').read_text())
    if (result['version']!='10.0.6' or result['before_sha256']!=sha(before.read_bytes())
            or result['after_sha256']!=sha(after.read_bytes())):raise ValueError('resume native source mismatch')
    return root


def completed_prefix(root,uid,scope,batches):
    if root is None:return {}
    path=root/f'zone-{uid}-scope.json';progress=root/f'zone-{uid}-progress.jsonl'
    if not path.exists():
        if progress.exists():raise ValueError('resume progress without native scope')
        return {}
    if json.loads(path.read_text())!=scope:raise ValueError('resume native scope changed')
    rows=[json.loads(line) for line in progress.read_text().splitlines()] if progress.exists() else []
    expected=[(stage,index,ids) for stage in (0,1) for index,ids in enumerate(batches)]
    actual=[(r['stage'],r['batch_index'],r['item_uuids']) for r in rows]
    if (any(type(r['stage']) is not int or type(r['batch_index']) is not int for r in rows)
            or actual!=expected[:len(rows)]):raise ValueError('resume progress is not an exact ordered prefix')
    return {(r['stage'],r['batch_index']):r for r in rows}


def verified_report(root,uid,label,fixture,row,geometry):
    """Freshly reconstructed/native-checked fixture must equal the saved fixture."""
    folder=root/f'zone-{uid}'/label
    saved=(folder/fixture.name).read_bytes();current=fixture.read_bytes()
    if saved!=current or sha(saved)!=row['fixture_sha256']:raise ValueError('resume fixture bytes changed')
    if row['native_geometry_sha256']!=geometry:raise ValueError('resume native geometry changed')
    for suffix in ('.kicad_pro','.kicad_dru'):
        if (folder/fixture.with_suffix(suffix).name).read_bytes()!=fixture.with_suffix(suffix).read_bytes():
            raise ValueError('resume native context changed')
    data=(folder/'drc.json').read_bytes()
    if sha(data)!=row['report_sha256']:raise ValueError('resume raw report changed')
    report=json.loads(data)
    if report.get('kicad_version')!='10.0.6' or set(report.get('included_severities',[]))!={'error','warning','exclusion'}:
        raise ValueError('resume native report scope changed')
    identities={(v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in new_silk_identities(report,uid)}
    expected={(a,b,tuple(ids)) for a,b,ids in row['identities']}
    if identities!=expected or len(expected)!=len(row['identities']):raise ValueError('resume receipt differs from native report')
    return data
