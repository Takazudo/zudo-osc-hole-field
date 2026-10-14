"""Exact E16 request authentication, immutable bindings and one-unit accounting.

No approval/signing command exists here. Production trusts only an independently
provisioned account signer file and detached OpenSSH signatures in three separate
namespaces. Tests use throwaway keys under temporary fixture roots; those keys
never enter the fixed production trust store. Resource qualification is distinct
from exact-request authorization and a current exclusive reservation.
"""
import base64
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import pwd
import re
import stat
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
LIMITS={'diagnostics':1,'units':1,'rhs':1,'attempts':1,'seconds':180,
        'memory_bytes':2*1024**3,'swap_bytes':0,'output_bytes':64*1024**2}
INVENTORY=HERE/'evidence/e16/attribution-reconstruction-wsl-20261014/resource-inventory.json'
INVENTORY_SHA='8cfcf5fac5bd749dcd58313b4df8eb1a9080723a5c5d34d80c548098c2d60b18'
OPERATION='e16-selected-attribution-v1'
SOURCE_NAMES=('attribution_admission.py','attribution_host.py','attribution_worker.py',
 'attribution_request.py','attribution_supervisor.py','attribution_resolution.py',
 'attribution_executor.py','attribution_transport.py','attribution_uniqueness.py',
 'attribution_lifecycle.py','attribution_reconstruction.py','finite_adapter.py',
 'finite_solve.py','finite_units.py','resistance_attribution.py','numerical_unit_guard.py')

ENVIRONMENT_POLICY={'python_flags':['-I','-S','-B','-X','pycache_prefix=/dev/null'],
                    'path':'/usr/bin:/bin','locale':'C.UTF-8','numerical_threads':1,
                    'loader_overrides':False,'inherited_credentials':False}
INTERNAL_ENV={'HEAVY_GUARD_HELD','E16_PARENT_MOUNT_NS','E16_CLAIM_BYTES','E16_CLAIM_PATH',
 'E16_HOST_CONTROLLER_PID','E16_HOST_LOCK_FD','E16_CGROUP_PARENT','E16_CGROUP_WORKER',
 'E16_GUARD_ENTRY_AT','E16_SUPERVISOR_WORK','E16_SUPERVISOR_RESULT','E16_WORK_DEADLINE','E16_OUTPUT_LIMIT','TMPDIR'}


def check_environment(env,inside=False):
    need(not any(k.startswith(('LD_','DYLD_','PYTHON')) for k in env),'unbound loader/Python environment override')


def clean_environment(env,inside=False):
    check_environment(env)
    account=pwd.getpwuid(os.getuid());runtime='/run/user/'+str(os.getuid())
    out={'HOME':account.pw_dir,'USER':account.pw_name,'LOGNAME':account.pw_name,
         'PATH':'/usr/bin:/bin','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
         'XDG_RUNTIME_DIR':runtime,'DBUS_SESSION_BUS_ADDRESS':'unix:path='+runtime+'/bus',
         'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    if inside:out.update({k:v for k,v in env.items() if k in INTERNAL_ENV})
    else:need(not any(k.startswith(('E16_','HEAVY_GUARD_')) for k in env),'inherited execution/guard identity')
    return out


def need(ok,message):
    if not ok:raise ValueError(message)


def canon(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()


def check_time(deadline):
    if deadline is not None:need(time.monotonic()<deadline,'admission deadline exhausted')


def remaining(deadline,maximum=5.):
    check_time(deadline)
    return maximum if deadline is None else max(.001,min(maximum,deadline-time.monotonic()))


def account_home():
    return Path(pwd.getpwuid(os.getuid()).pw_dir)


def trust_path():
    return account_home()/'.config/zudo-e16/attribution.allowed_signers'


def state_directory():
    return account_home()/'.local/state/zudo-e16-attribution'


def ledger_path():
    return account_home()/'.cache/zudo-e16-runs/campaign-20261014/campaign-note.json'


def output_root():
    return account_home()/'.cache/zudo-e16-runs'


def python_path():
    return account_home()/'.cache/zudo-e16-numerical-venv/bin/python'


def sha(path,deadline=None):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while True:
            check_time(deadline)
            chunk=stream.read(65536)
            if not chunk:return h.hexdigest()
            h.update(chunk)


def read_bytes(path,limit=1024*1024):
    path=Path(path)
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'rb') as stream:
        info=os.fstat(stream.fileno())
        need(stat.S_ISREG(info.st_mode) and info.st_size<=limit,'nonregular/oversized admission file')
        raw=stream.read(limit+1)
        need(len(raw)<=limit,'oversized admission file')
        return raw


def parse_json(raw):
    def unique(pairs):
        out={}
        for k,v in pairs:
            need(k not in out,'duplicate JSON field');out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=unique,parse_constant=lambda x:need(False,'nonfinite JSON value'))


def read_json(path,limit=1024*1024):
    return parse_json(read_bytes(path,limit))


def source_bindings():
    result={};total=0
    for name in SOURCE_NAMES:
        raw=read_bytes(HERE/name,1024**2);total+=len(raw)
        need(total<=8*1024**2,'source bootstrap metadata cap exceeded')
        result[name]=hashlib.sha256(raw).hexdigest()
    return result


def host_identity():
    return {'uid':os.getuid(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
            'machine_id':Path('/etc/machine-id').read_text().strip()}


def artifacts(packet):
    yield packet['config'];yield packet['cases']
    for board in ('KA','KB'):
        for key in ('operator','reduction','desc','plan'):
            yield packet['boards'][board][key]
        yield from packet['boards'][board]['mesh']
    yield packet['comparison']


def independent_inventory():
    need(sha(INVENTORY)==INVENTORY_SHA,'independent original inventory changed')
    d=read_json(INVENTORY)
    out={row['path']:row for name in ('solver_artifacts','bound_plus12_inputs') for row in d[name]}
    spec=HERE/'evidence/e16/resistance-attribution-wsl-20261014/transfer-experiment.json'
    need(sha(spec)=='a755d4558260f5e9e669855d6464a8d3f54c64cbae44a90ea9bed211aadf7383','original experiment bindings changed')
    for row in read_json(spec)['bindings']:
        if Path(row['path']).name in ('coupled-network-config.json','process-cases.json'):
            path=str(HERE/row['path'])
            out[path]={'path':path,'expected_sha256':row['sha256'],'observed_bytes':row['bytes']}
    # The original unit-current projection was independently identified in the
    # predecessor handoff. Bind its original compressed artifact, never loaded watts.
    path=str(account_home()/'.cache/zudo-e16-runs/coupled-approved-852ffac-8262c033/coupled-+12V-nominal-average-uniform-dielectric.json.gz')
    out[path]={'path':path,'expected_sha256':'b6b6b8928fe77619202f9d323d44b5f04a784435134be8ebb152b24d68e7b96d','observed_bytes':39146}
    return out


def operation_digest(request):
    # Qualification binds exact code/toolchain/data/algorithm/caps. Fresh execution
    # identity/output and its own qualification/signature cannot be circular inputs.
    keys=('operation','limits','environment_policy','source_bindings','source_tree','toolchain','packet','host_limits','guard_sha256')
    return hashlib.sha256(canon({k:request[k] for k in keys})).hexdigest()


def verify_signature(path,namespace,identity,trust_sha,deadline=None):
    """The trust root is fixed outside both request and checkout; never supplied by packet."""
    trust=trust_path()
    info=trust.lstat()
    need(stat.S_ISREG(info.st_mode) and info.st_uid==os.getuid() and not info.st_mode&0o022 and info.st_size<=65536,
         'untrusted signer store ownership/mode')
    need(sha(trust,deadline)==trust_sha,'signer store binding changed')
    raw=read_bytes(path,65536)
    signature=Path(str(path)+'.sig')
    read_bytes(signature,16384)  # bounded regular/no-follow file before external verifier
    result=subprocess.run(['/usr/bin/ssh-keygen','-Y','verify','-f',str(trust),'-I',identity,
                           '-n',namespace,'-s',str(signature)],input=raw,
                          stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                          timeout=remaining(deadline),check=False)
    need(result.returncode==0,'missing/invalid independently signed '+namespace)
    need(read_bytes(path,65536)==raw,'signed evidence changed during verification')
    return parse_json(raw)


def verify_qualification(request,deadline=None,*,metadata_only=False):
    binding=request['qualification']
    need(hashlib.sha256(read_bytes(binding['path'],65536)).hexdigest()==binding['sha256'],'qualification bytes changed')
    q=verify_signature(binding['path'],'e16-attribution-resource-v1','e16-resource-reviewer',request['trust_sha256'],deadline)
    need(q['schema']=='e16-attribution-resource-v1' and q['status']=='RESOURCE_QUALIFIED', 'resource qualification absent')
    need(q['operation_sha256']==operation_digest(request) and q['limits']==LIMITS,'qualification scope differs')
    need(q['combined_operation'] is True and q['evidence_kind']=='admitted_combined_operation', 'individual/tiny timings are not qualification')
    need(type(q['expires_unix']) in (int,float) and math.isfinite(q['expires_unix']) and q['expires_unix']>time.time(),'qualification expired')
    measures=q['measured']
    for name,maximum in (('elapsed_seconds',180),('memory_peak_bytes',2*1024**3),('output_peak_bytes',64*1024**2)):
        value=measures[name]
        need(type(value) in (int,float) and math.isfinite(value) and 0<value<=maximum,'qualification exceeds '+name)
    need(measures['swap_bytes']==0 and measures['max_concurrency']==1 and measures['attempts']==1,'qualification caps differ')
    allowance=q['production_admission_allowance_seconds_upper']
    need(type(allowance) in (int,float) and math.isfinite(allowance) and allowance>=10 and measures['elapsed_seconds']+allowance<=180,'production-only admission overhead not qualified')
    need(q['cleanup_complete'] is True and q['all_required_phases'] is True,'incomplete qualification')
    # Signed verdict is tied to retained, independently reviewable receipts too.
    need(isinstance(q['evidence'],list) and 0<len(q['evidence'])<=16,'qualification receipts absent/oversized')
    if metadata_only:return q
    total=0
    for binding in q['evidence']:
        total+=Path(binding['path']).stat().st_size
        need(total<=1024**2,'qualification compact receipt size exceeded')
        need(sha(binding['path'],deadline)==binding['sha256'],'qualification receipt drift')
    return q


def validate_identity(request,digest):
    need(isinstance(digest,str) and re.fullmatch('[0-9a-f]{64}',digest) is not None,'invalid request digest')
    need(isinstance(request.get('run_id'),str) and re.fullmatch('[0-9a-f]{32}',request['run_id']) is not None
         and type(request.get('attempt')) is int and request['attempt']==1,'invalid single-use identity')


def validate_structure(request,digest,deadline=None):
    """Bounded pre-claim checks; no selected artifact or numerical import."""
    check_time(deadline);validate_identity(request,digest)
    check_environment(os.environ)
    need(request['schema']=='e16-attribution-request-v1' and request['operation']==OPERATION and canon(request['limits'])==canon(LIMITS),'request operation/caps differ')
    need(request['request_kind'] in ('production-attribution','resource-qualification'),'invalid request kind')
    need(request['host']==host_identity() and request['environment_policy']==ENVIRONMENT_POLICY,'host/environment changed')
    need(request['checkout']==str(ROOT) and request['python']==str(python_path()),'checkout/interpreter differs')
    need(request['output']==str(output_root()/('attribution-'+request['run_id'])) and request['ledger']['path']==str(ledger_path()),'output/ledger differs')
    need(request['source_bindings']==source_bindings(),'source binding changed')
    from attribution_host import HOST_LIMITS
    need(request['host_limits']==HOST_LIMITS,'host reservation/caps changed')
    result=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,timeout=remaining(deadline))
    need(result.returncode==0 and result.stdout.strip()==request['source_sha'],'immutable checkout head differs')
    if Path(request['output']).exists():
        journal=read_json(state_directory()/(request['run_id']+'.json'),65536)
        need(journal['request_sha256']==digest and journal['status']=='CONSUMED_NO_RETRY','output is not owned by consumed identity')


def validate_metadata(request,digest,deadline=None,*,revalidate_inputs=True):
    check_time(deadline)
    need(hashlib.sha256(canon(request)).hexdigest()==digest,'stale request digest')
    check_environment(os.environ)
    need(request['environment_policy']==ENVIRONMENT_POLICY,'environment policy changed')
    need(request['schema']=='e16-attribution-request-v1' and request['operation']==OPERATION and canon(request['limits'])==canon(LIMITS),'operation/caps differ')
    need(request['request_kind'] in ('production-attribution','resource-qualification'),'invalid request kind')
    validate_identity(request,digest)
    need(request['host']==host_identity(),'host/boot/UID changed')
    need(request['checkout']==str(ROOT) and request['python']==str(python_path()),'checkout/interpreter differs')
    need(request['output']==str(output_root()/('attribution-'+request['run_id'])),'output identity differs')
    need(request['ledger']['path']==str(ledger_path()),'noncanonical campaign ledger')
    need(request['source_bindings']==source_bindings(),'source binding changed')
    need(request['packet']['source_bindings']==request['source_bindings'],'packet source differs')
    need(request['packet']['solver_sha256']==request['source_bindings']['finite_solve.py'],'solver binding changed')
    need(not any(k in request['packet'] for k in ('fixture_only','fixture_removed')),'fixture scope in production request')
    need(set(request['packet']['boards'])=={'KA','KB'},'incomplete board scope')
    from attribution_host import HOST_LIMITS
    need(request['host_limits']==HOST_LIMITS,'host reservation/caps changed')
    caps=request['packet']['certificate_limits']
    need(set(caps)=={'max_entries','max_updates','max_input_nnz'} and
         all(type(caps[k]) is int and 0<caps[k]<=v for k,v in
             {'max_entries':4_000_000,'max_updates':20_000_000,'max_input_nnz':16_000_000}.items()),'certificate cap differs')
    result=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,timeout=remaining(deadline))
    need(result.returncode==0 and result.stdout.strip()==request['source_sha'],'immutable checkout head differs')
    result=subprocess.run(['git','status','--porcelain'],cwd=ROOT,capture_output=True,text=True,timeout=remaining(deadline))
    need(result.returncode==0 and not result.stdout.strip(),'tracked checkout is not clean')
    from attribution_request import packet_from_inventory
    need(request['packet']==packet_from_inventory(request['source_bindings']),'production packet differs from fixed original experiment')
    inventory=independent_inventory();seen=set()
    for binding in artifacts(request['packet']):
        path=binding['path']
        need(path not in seen and path in inventory,'duplicate/nonoriginal artifact')
        seen.add(path);original=inventory[path]
        need(binding['sha256']==original['expected_sha256'] and binding['bytes']==original['observed_bytes'],'original artifact binding differs')
        need(type(binding['decoded_limit']) is int and 0<binding['decoded_limit']<=512*1024**2,'decoded bound invalid')
    for board in ('KA','KB'):
        b=request['packet']['boards'][board]
        need(Path(b['desc']['path']).name=='desc-+12V.json.gz' and Path(b['operator']['path']).name=='operator-+12V.pkl.gz','board/net artifact scope differs')
        need(Path(b['operator']['path']).parent.name==board and Path(b['desc']['path']).parent.name==board,'board artifact switched')
        need(Path(b['reduction']['path']).name==board+'-red-+12V-nominal-average-uniform-dielectric.pkl.gz','case/depth reduction differs')
        need([Path(m['path']).name for m in b['mesh']]==[f'mesh-+12V-{i:03}.pkl.gz' for i in range(11)],'original chunk scope/order differs')
        need(all(Path(m['path']).parent.name==board for m in b['mesh']),'wrong board chunks')
    need(Path(request['packet']['comparison']['path']).name=='coupled-+12V-nominal-average-uniform-dielectric.json.gz','comparison scope differs')
    need(sha(account_home()/'.codex/scripts/heavy-guard.sh',deadline)==request['guard_sha256'],'guard changed')
    # Every requested source/toolchain file is checked inside guard, as are all
    # selected artifact bytes. Streaming decode repeats descriptor-bound checks.
    verify_manifests(request,deadline)
    if revalidate_inputs:
        for binding in artifacts(request['packet']):
            need(Path(binding['path']).stat().st_size==binding['bytes'] and sha(binding['path'],deadline)==binding['sha256'],'stale selected input')


def verify_manifests(request,deadline=None):
    from attribution_request import source_paths,toolchain_paths
    expected={'source_tree':source_paths(),'toolchain':toolchain_paths()}
    for group,paths in expected.items():
        need(set(request[group]['files'])==set(map(str,paths)),'incomplete '+group+' manifest')
        for path,value in request[group]['files'].items():
            need(sha(path,deadline)==value,group+' file drift: '+path)


def verify_for_host(request_path,digest,authority_path,reservation_path,*,deadline=None,metadata_only=False):
    """Authenticate before expensive input reads; no boolean or old campaign delegation."""
    r=read_json(request_path,8*1024**2)
    need(hashlib.sha256(canon(r)).hexdigest()==digest,'stale request digest')
    validate_identity(r,digest)
    need(r.get('request_kind') in ('production-attribution','resource-qualification'),'invalid request kind')
    prefix='e16-attribution' if r['request_kind']=='production-attribution' else 'e16-attribution-qualification'
    authority=verify_signature(authority_path,prefix+'-authorization-v1','e16-operator',r['trust_sha256'],deadline)
    reservation=verify_signature(reservation_path,prefix+'-reservation-v1','e16-controller',r['trust_sha256'],deadline)
    now=time.time()
    for grant,kind in ((authority,'authorization'),(reservation,'reservation')):
        need(grant['schema']==prefix+'-'+kind+'-v1' and grant['request_kind']==r['request_kind'] and grant['request_sha256']==digest and
             grant['run_id']==r['run_id'] and canon(grant['limits'])==canon(LIMITS) and grant['operation']==OPERATION,'inapplicable '+kind)
        need(all(type(grant[k]) in (int,float) and math.isfinite(grant[k]) for k in ('issued_unix','expires_unix')),'invalid grant time')
        need(grant['issued_unix']<=now and grant['expires_unix']>=now+(180 if deadline is None else max(0,deadline-time.monotonic())), 'expired/too-short '+kind)
    need(authority['approved'] is True and reservation['exclusive'] is True,'missing authority/reservation')
    need(reservation['host']==host_identity() and reservation['ledger_sha256']==r['ledger']['sha256'],'reservation host/ledger differs')
    if r['request_kind']=='production-attribution':verify_qualification(r,deadline,metadata_only=metadata_only)
    else:need(r.get('qualification') is None,'qualification request must not pretend prior qualification')
    if metadata_only:
        validate_structure(r,digest,deadline)
        need(len(read_bytes(ledger_path(),65536))<=65536,'ledger receipt cap')
    else:validate_metadata(r,digest,deadline)
    current=hashlib.sha256(read_bytes(ledger_path(),65536)).hexdigest()
    if current!=r['ledger']['sha256']:
        receipt=read_json(state_directory()/(r['run_id']+'.json'))
        need(receipt['request_sha256']==digest and receipt['before_ledger_sha256']==r['ledger']['sha256'] and
             receipt['after_ledger_sha256']==current,'campaign accounting changed')
    return r


def write_new(path,data):
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def claim(request,digest,deadline=None):
    """Consume exactly one diagnostic; failed launch stays charged and unrepeatable.

    Caller holds the shared heavy slot AND the E16 exclusive reservation flock.
    The immutable O_EXCL journal preserves every original ledger byte. Ledger
    replacement is atomic. A crash between journal and ledger leaves a consumed
    identity and blocks execution until external reconciliation, never retry.
    """
    check_time(deadline);validate_identity(request,digest)
    state=state_directory();state.mkdir(parents=True,exist_ok=True)
    old=read_bytes(ledger_path());before=hashlib.sha256(old).hexdigest()
    need(before==request['ledger']['sha256'],'campaign changed before consumption')
    data=json.loads(old);budget=data['execution_budget']
    need(data['live_owned_work'] is False and budget['production_diagnostic_used']<budget['production_diagnostic_limit'],'campaign unavailable/exhausted')
    need(all(r.get('state','').startswith('terminal') for r in data['runs']),'prior campaign is not terminal')
    data=copy.deepcopy(data);data['execution_budget']['production_diagnostic_used']+=1
    data['live_owned_work']=True
    data['activity']='ACTIVE: admitted selected-attribution diagnostic; attempt5 remains terminal'
    data.setdefault('attribution_charges',[]).append({'request_sha256':digest,'run_id':request['run_id'],'diagnostic_charge':1,
                                                    'full_baseline_charge':0,'attempt':1,'state':'ACTIVE','terminal_receipt':str(Path(request['output'])/'terminal.json')})
    new=canon(data)
    receipt={'request_sha256':digest,'run_id':request['run_id'],'attempt':1,'source_sha':request['source_sha'],
             'before_ledger_sha256':before,'after_ledger_sha256':hashlib.sha256(new).hexdigest(),
             'original_ledger_base64':base64.b64encode(old).decode(),'claimed_at_unix':time.time(),
             'diagnostic_charge':1,'full_baseline_charge':0,'status':'CONSUMED_NO_RETRY'}
    claimpath=state/(request['run_id']+'.json');encoded=canon(receipt)
    need(len(encoded)+2*len(new)+4096<65536,'accounting receipt reserve exceeded')
    write_new(claimpath,encoded)
    check_time(deadline)
    temp=ledger_path().with_name('.attribution-'+request['run_id']+'.pending')
    write_new(temp,new)
    need(sha(ledger_path(),deadline)==before,'campaign race during consumption')
    os.replace(temp,ledger_path())
    fd=os.open(ledger_path().parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return claimpath,len(encoded)+len(new)


def claim_worker(request,digest,deadline=None):
    check_time(deadline)
    receipt=read_json(state_directory()/(request['run_id']+'.json'))
    need(receipt['request_sha256']==digest and receipt['after_ledger_sha256']==sha(ledger_path(),deadline),'worker lacks consumed reservation')
    path=state_directory()/(request['run_id']+'.worker-started')
    raw=canon({'request_sha256':digest,'started_unix':time.time()})
    write_new(path,raw)
    return len(raw)


def finish_accounting(request,digest,terminal,deadline=None):
    """Finish only this consumed diagnostic; preserve all historical run records."""
    check_time(deadline)
    claimpath=state_directory()/(request['run_id']+'.json')
    journal=read_json(claimpath)
    need(journal['request_sha256']==digest,'terminal claim differs')
    current=read_bytes(ledger_path())
    need(hashlib.sha256(current).hexdigest()==journal['after_ledger_sha256'],'accounting changed before terminal')
    ledger=parse_json(current)
    charges=[x for x in ledger['attribution_charges'] if x['run_id']==request['run_id']]
    need(len(charges)==1 and charges[0]['state']=='ACTIVE','identity already terminal/unknown')
    charges[0]['state']='TERMINAL'
    charges[0]['status']=terminal['status']
    charges[0]['cleanup_complete']=terminal['cleanup_complete']
    ledger['live_owned_work']=not terminal['cleanup_complete']
    ledger['activity']='TERMINAL: selected attribution diagnostic; original baseline attempt5 remains terminal' if terminal['cleanup_complete'] else 'BLOCKED: attribution cleanup incomplete'
    raw=canon(ledger)
    receipt=canon({'request_sha256':digest,'run_id':request['run_id'],'request_kind':request['request_kind'],
                   'output_manifest_sha256':hashlib.sha256(canon(terminal['files'])).hexdigest(),'terminal_status':terminal['status'],
                   'cleanup_complete':terminal['cleanup_complete'],'ledger_sha256':hashlib.sha256(raw).hexdigest()})
    destination=state_directory()/(request['run_id']+'.terminal.json')
    write_new(destination,receipt)
    temp=ledger_path().with_name('.attribution-'+request['run_id']+'.terminal-pending')
    write_new(temp,raw);os.replace(temp,ledger_path())
    fd=os.open(ledger_path().parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return len(receipt)+len(raw)
