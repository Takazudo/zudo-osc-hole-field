"""Source-only operation description and fail-closed production request sealing.

Description is not a production request. Sealing requires a separately signed
combined-resource qualification, a clean immutable checkout and the owner-delegated
E16-only trust store. This module never signs, approves, reserves or executes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
import attribution_admission as A

TOOLS=('bash','timeout','systemd-run','systemctl','unshare','mount','umount','ssh-keygen','flock','setsid',
       'awk','cat','date','mkdir','rm','sed','sleep','tr','git','ldd')


def source_paths():
    paths=list(HERE.glob('*.py'))
    # Imported namespace-package initializers or sourceless modules cannot hide
    # outside the sealed import roots, even when gitignored.
    for root in (HERE,A.ROOT/'scripts',A.ROOT/'scripts/pcbgen'):
        for pattern in ('*.pyc','*.so','*.pyd'):
            for p in root.glob(pattern):
                A.need(False,'unbound repository import override: '+str(p))
    for root in (A.ROOT/'scripts',A.ROOT/'scripts/pcbgen'):
        if (root/'__init__.py').exists():paths.append(root/'__init__.py')
    for child in HERE.iterdir():
        if child.is_dir() and (child/'__init__.py').exists():
            paths.extend(p for p in child.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths += [A.ROOT/'scripts/pcbgen/sheet_mesh.py',A.ROOT/'scripts/pcbgen/shared_interface.py']
    return sorted(paths)


def linked_paths(output,bound):
    """Resolve standalone wheel-library dependencies without changing loader env.

    A bundled leaf can omit RPATH because its importing extension preloads its
    wheel dependencies. Such a soname must resolve uniquely inside the already
    bound environment. This binds bytes; actual loading remains an in-run gate.
    """
    result=set()
    for line in output.splitlines():
        tokens=line.split()
        if 'not found' in line:
            matches={p for p in bound if p.name==tokens[0]}
            A.need(len(matches)==1,'unresolved/ambiguous bundled library: '+tokens[0])
            result.update(matches)
        else:
            for token in tokens:
                if token.startswith('/'):
                    lib=Path(token)
                    A.need(lib.is_file(),'missing linked library');result.add(lib.resolve())
    return result


def toolchain_paths(python=None):
    python=Path(python or A.python_path())
    # Exact installed numerical environment; no numerical imports/execution.
    site=python.parent.parent/'lib/python3.12/site-packages'
    stdlib=Path('/usr/lib/python3.12')
    paths={python.resolve(),python.parent.parent/'pyvenv.cfg'}
    for directory in (site,stdlib):
        A.need(directory.is_dir(),'missing pinned Python environment')
        for p in directory.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                paths.add(p.resolve())
    for tool in TOOLS:
        p=Path('/usr/bin')/tool
        A.need(p.exists(),'missing tool: '+tool);paths.add(p.resolve())
    # Dynamic loader/system shared libraries are code too. Bind the libraries
    # used by every ELF executable/extension via local ldd (read-only loader trace).
    # No real numerical artifact, field or operator is opened.
    elf=[]
    for p in sorted(paths):
        with p.open('rb') as stream:
            if stream.read(4)==b'\x7fELF':elf.append(p)
    for p in elf:
        result=subprocess.run(['/usr/bin/ldd',str(p)],capture_output=True,text=True,timeout=5)
        A.need(result.returncode==0,'cannot bind shared libraries: '+str(p))
        paths.update(linked_paths(result.stdout,paths))
    return sorted(paths)


def file_manifest(paths):
    return {'files':{str(p):A.sha(p) for p in paths}}


def packet_from_inventory(sources):
    inventory=A.independent_inventory()
    def find(name,board=None):
        matches=[r for p,r in inventory.items() if Path(p).name==name and (board is None or Path(p).parent.name==board)]
        A.need(len(matches)==1,'ambiguous/missing independent input: '+name)
        r=matches[0]
        return {'path':r['path'],'sha256':r['expected_sha256'],'bytes':r['observed_bytes'],
                'format':'pickle' if name.endswith('.pkl.gz') else 'json',
                'gzip':name.endswith('.gz'),'decoded_limit':512*1024**2}
    packet={'original_request_identity':{'compressed_sha256':'3ac6356762419c653c8949adb1c2d12db58e109408d52246ef482e9a398adc54','decompressed_sha256':'ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6'},
            'config':find('coupled-network-config.json'),'cases':find('process-cases.json'),
            'solver_sha256':sources['finite_solve.py'],'source_bindings':sources,
            'certificate_method':'original-operator-symmetric-part-coercivity-v1',
            'certificate_storage':'lazy-frontier-interval-LDL-v1',
            'certificate_ordering':'rcm-original-structural-union-v1',
            'certificate_limits':{'max_entries':4_000_000,'max_updates':20_000_000,'max_input_nnz':16_000_000},
            'comparison':find('coupled-+12V-nominal-average-uniform-dielectric.json.gz'),'boards':{}}
    for board in ('KA','KB'):
        packet['boards'][board]={'operator':find('operator-+12V.pkl.gz',board),
            'desc':find('desc-+12V.json.gz',board),'plan':find('plan-+12V.json',board),
            'reduction':find(board+'-red-+12V-nominal-average-uniform-dielectric.pkl.gz'),
            'mesh':[find(f'mesh-+12V-{i:03}.pkl.gz',board) for i in range(11)]}
    return packet


def describe():
    from attribution_host import HOST_LIMITS
    A.verify_policy({'authorization_policy':A.AUTHORIZATION_POLICY})
    sources=A.source_bindings()
    operation={'authorization_policy':dict(A.AUTHORIZATION_POLICY),'operation':A.OPERATION,'limits':A.LIMITS,'environment_policy':A.ENVIRONMENT_POLICY,'source_bindings':sources,
               'source_tree':file_manifest(source_paths()),'toolchain':file_manifest(toolchain_paths()),
               'packet':packet_from_inventory(sources),'host_limits':HOST_LIMITS,
               'guard_sha256':A.sha(A.account_home()/'.codex/scripts/heavy-guard.sh')}
    return {'schema':'e16-attribution-operation-description-v1','production_request_sha256':None,
            'execution':'NOT_RUN','resource_status':'NOT_QUALIFIED',
            'operation_sha256':A.operation_digest(operation),'operation':operation,
            'notice':'Source/toolchain/index metadata only. This is not a production request or qualification.'}


def seal(description,qualification_path,output,*,qualification_only=False):
    """Only seal after actual independently signed combined-resource evidence exists."""
    A.need(description['schema']=='e16-attribution-operation-description-v1','not an operation description')
    operation=description['operation']
    A.need(A.operation_digest(operation)==description['operation_sha256'],'stale operation description')
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=A.ROOT,text=True).strip()
    A.need(not subprocess.check_output(['git','status','--porcelain'],cwd=A.ROOT,text=True).strip(),'immutable clean checkout required')
    run_id=uuid.uuid4().hex
    request=operation|{'schema':'e16-attribution-request-v1','run_id':run_id,'attempt':1,
                       'request_kind':'resource-qualification' if qualification_only else 'production-attribution',
                       'source_sha':head,'checkout':str(A.ROOT),'python':str(A.python_path()),
                       'output':str(A.output_root()/('attribution-'+run_id)),'host':A.host_identity(),
                       'trust_sha256':A.sha(A.trust_path()),
                       'ledger':{'path':str(A.ledger_path()),'sha256':A.sha(A.ledger_path())},
                       'qualification':None if qualification_only else {'path':str(Path(qualification_path).resolve()),'sha256':A.sha(qualification_path)}}
    if not qualification_only:A.verify_qualification(request)
    digest=hashlib.sha256(A.canon(request)).hexdigest()
    # Preparing a request never revalidates original artifact bytes outside guard.
    A.validate_metadata(request,digest,revalidate_inputs=False)
    A.need(not Path(request['output']).exists(),'execution output already exists')
    A.write_new(output,A.canon(request))
    return {'qualification_request_sha256':digest if qualification_only else None,
            'production_request_sha256':None if qualification_only else digest,'request_path':str(Path(output).resolve()),
            'admission_status':'NOT_ADMITTED','execution_status':'NOT_RUN',
            'next_action':'Locally delegated operator authorization and controller reservation signatures for this exact digest.'}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    x=s.add_parser('describe');x.add_argument('--output',required=True)
    x=s.add_parser('seal');x.add_argument('--description',required=True);x.add_argument('--qualification',required=True);x.add_argument('--output',required=True)
    x=s.add_parser('seal-qualification');x.add_argument('--description',required=True);x.add_argument('--output',required=True)
    args=p.parse_args(argv)
    if args.command=='describe':
        result=describe();A.write_new(args.output,A.canon(result));print(json.dumps({'operation_sha256':result['operation_sha256'],'production_request_sha256':None}))
    else:print(json.dumps(seal(A.read_json(args.description,8*1024**2),getattr(args,'qualification',None),args.output,qualification_only=args.command=='seal-qualification')))


if __name__=='__main__':main()
