"""E16 single-unit lifecycle facade and bounded fixture adapter.

The production path delegates to the source-owned authenticated host/worker
adapter. Readiness never grants qualification, authority or reservation.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import time

import attribution_admission as A
need=A.need

LIMITS = {'diagnostics':1,'units':1,'rhs':1,'attempts':1,'seconds':180,
          'memory_bytes':2*1024**3,'swap_bytes':0,'output_bytes':64*1024**2}
HERE=Path(__file__).resolve().parent
SOURCE_FILES=A.SOURCE_NAMES


def source_bindings():
    return A.source_bindings()


def artifact_bindings(packet):
    yield packet['config'];yield packet['cases']
    for board in ('KA','KB'):
        data=packet['boards'][board]
        for key in ('operator','reduction','desc','plan'):
            yield data[key]
        yield from data['mesh']
    if 'comparison' in packet:
        yield packet['comparison']


def validate_request(request, digest, original_index, budget):
    """No input decode here. Caller authenticates digest/index independently.

    Independent expected artifact hashes must come from the original request or
    retained index, never from this operation's own freshly computed hashes.
    """
    import attribution_transport as T
    budget.check()
    need(hashlib.sha256(T.canonical(request)).hexdigest()==digest,'stale request digest')
    need(request['limits']==LIMITS and request['operation']=='e16-selected-attribution-v1','changed operation/caps')
    need(bool(re.fullmatch(r'[0-9a-f]{32}',request['run_id'])) and request['attempt']==1,'invalid single-use identity')
    need(request['source_bindings']==source_bindings(),'source binding drift')
    need(request['packet']['source_bindings']==request['source_bindings'],'packet source binding drift')
    need(request['packet']['solver_sha256']==request['source_bindings']['finite_solve.py'],'solver binding drift')
    need(request['packet']['certificate_limits']['max_entries'] <= 4_000_000 and
         request['packet']['certificate_limits']['max_updates'] <= 20_000_000 and
         request['packet']['certificate_limits'].get('max_input_nnz',16_000_000) <= 16_000_000,'unreviewed certificate cap')
    seen=set()
    for b in artifact_bindings(request['packet']):
        budget.check()
        path=str(Path(b['path']).resolve())
        need(path not in seen,'duplicate artifact path')
        seen.add(path)
        need(original_index.get(path)==b['sha256'],'artifact not independently bound')
        need(0 < b['bytes'] <= 512*1024**2 and 0 < b['decoded_limit'] <= 512*1024**2,'artifact limits invalid')
    need(request['output'] not in seen and not Path(request['output']).exists(),'output must be fresh')


def _once(request,digest,index,claim_directory,authority,reservation,budget):
    """Shared fixture/admitted lifecycle core. Evidence objects are NOT grants.

    This internal function accepts already independently authenticated authority
    and reservation observations; production entry below does not fabricate them.
    A fixture invocation is restricted before this function, including file paths,
    real decoded dimensions and immutable low ceilings.
    """
    import attribution_executor as E
    import attribution_transport as T
    budget.phase='admission'
    validate_request(request,digest,index,budget)
    for evidence,name in ((authority,'authority'),(reservation,'reservation')):
        need(evidence is not None,'missing '+name)
        need(evidence['request_sha256']==digest and evidence['run_id']==request['run_id'] and
             evidence['limits']==LIMITS and evidence['expires_unix'] > time.time(), 'stale/inapplicable '+name)
    need(reservation['exclusive'] is True,'missing exclusive reservation')
    claims=Path(claim_directory);claims.mkdir(exist_ok=True)
    # Same persistent O_EXCL convention as local_native_admission.claim, owned
    # by E16. A failed execution remains consumed; never resume/remove the claim.
    claim=claims/(request['run_id']+'.json')
    data=T.canonical({'request_sha256':digest,'run_id':request['run_id'],'attempt':1,
                      'source_bindings':request['source_bindings'],'claimed_at_unix':time.time()})
    budget.charge(len(data))
    with claim.open('xb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    return E.run_pipeline(request['packet'],request['output'],budget)


def run_fixture(request, root, authority=None, reservation=None, budget=None):
    """Bounded fixture-only transport; no real retained path can enter it.

    All input files must be directly under a fresh test root; format/payload
    bounds are checked before any numerical work. This does not raise or reuse
    fixture_report's ceilings, and it is not a production execution transport.
    """
    import attribution_reconstruction as C
    import attribution_transport as T
    root=Path(root).resolve()
    need(request.get('fixture_only') is True,'fixture marker required')
    need(root.name.startswith('e16-fixture-') and root.parent == Path('/tmp'), 'fixture root must be /tmp/e16-fixture-*')
    budget=budget or T.Budget()
    index={}
    for b in artifact_bindings(request['packet']):
        path=Path(b['path'])
        need(path.parent.resolve()==root and not path.is_symlink(),'fixture path outside test root')
        need(b['bytes'] <= 4*1024**2 and b['decoded_limit'] <= 4*1024**2,'fixture byte ceiling exceeded')
        index[str(path.resolve())]=b['sha256']
        obj=T.decode(b,budget)
        C.check_fixture_payload(obj)
        del obj
    need(Path(request['output']).parent.resolve()==root,'fixture output outside test root')
    operators={b:T.decode(request['packet']['boards'][b]['operator'],budget) for b in ('KA','KB')}
    C.check_fixture_size(operators)
    del operators
    digest=hashlib.sha256(T.canonical(request)).hexdigest()
    return _once(request,digest,index,root/'claims',authority,reservation,budget)


def readiness():
    return {'schema':'e16-executor-readiness-v1','source_status':'SOURCE_COMPLETE',
            'resource_status':'NOT_QUALIFIED','request_status':'NOT_PREPARED',
            'admission_status':'NOT_ADMITTED','execution_status':'NOT_RUN',
            'production_request_sha256':None,'production_execute_command':None,
            'source_bindings':source_bindings(),'limits':LIMITS,
            'implemented':['interval sparse LDL / exact bordered Schur checker',
                           'hash-bound streaming decoder and exhaustive original chunk replay',
                           'selected RHS and serial original Assembly mapping/accounting',
                           'quota-reserved atomic terminal transport','single-use lifecycle core and bounded fixtures',
                           'bounded subprocess supervisor with guard/cgroup/quota proof primitives',
                           'interval forward-error bounds and resolved Stage C screen',
                           'exact operation compiler and separate resource-qualification request kind',
                           'independent signature/trust-root admission and exclusive one-unit accounting',
                           'fixed isolated worker and source-owned cgroup/tmpfs host lifecycle',
                           'immutable output journal plus durable shared-guard acceptance'],
            'remaining_source_gaps':[],
            'remaining':['separately admitted combined real-data resource qualification, including exact certificate fill/work and nine mesh passes per board',
                         'independently provisioned signer trust store and reviewed qualification evidence',
                         'sealed exact production request, applicable signed authorization and current exclusive reservation'],
            'real_artifact_decoded':False,'numerical_units_executed':0,
            'electrical_acceptance':False,'whole_board_acceptance':False,'adopted':False}


def execute_production(request_path,digest,authority_path,reservation_path):
    # Host reads only bounded metadata before shared guard entry. It authenticates
    # exact evidence and enforces all kernel/budget gates before numerical work.
    from attribution_host import launch
    return launch(request_path,digest,authority_path,reservation_path)



if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readiness',action='store_true',required=True)
    parser.parse_args()
    print(json.dumps(readiness(),sort_keys=True,indent=2))
    raise SystemExit(2)
