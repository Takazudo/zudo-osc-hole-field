"""Fixed admitted E16 worker. Authentication and kernel proofs precede NumPy.

Invoke only through attribution_host. There is no fixture/authority bypass flag.
The fixture suites use bounded in-memory/test-root adapters separately.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

HERE=Path(__file__).resolve().parent
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
import attribution_admission as A


def prove_worker(request):
    from numerical_unit_guard import UnitGuard
    from attribution_host import HOST_LIMITS,prove_reservation_owner
    UnitGuard(request['guard_sha256']).prove_owner(inherited_fd=int(os.environ['E16_GUARD_FD']))
    prove_reservation_owner()
    A.check_environment(os.environ)
    cg=Path('/sys/fs/cgroup')
    actual=cg/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    worker=Path(os.environ['E16_CGROUP_WORKER'])
    parent=Path(os.environ['E16_CGROUP_PARENT'])
    A.need(worker.resolve()==worker and parent.resolve()==parent and actual==worker and worker.parent==parent,
           'worker containment identity differs')
    A.need(worker.name=='worker' and (worker/'memory.max').read_text().strip()==str(HOST_LIMITS['worker_bytes'])
           and (worker/'memory.swap.max').read_text().strip()=='0','worker memory/no-swap boundary absent')
    A.need(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode,'isolated source-only Python import mode required')
    work=Path(request['output'])/'staging/.work.partial'
    result=Path(os.environ['E16_SUPERVISOR_RESULT'])
    A.need(result==work/'result' and not result.exists(),'worker output identity/freshness differs')
    A.need(sys.pycache_prefix=='/dev/null','unbound bytecode cache refused')
    deadline=float(os.environ['E16_WORK_DEADLINE']);started=float(os.environ['E16_GUARD_ENTRY_AT'])
    A.need(started<=time.monotonic()<deadline<=started+180,'invalid actual guarded interval')
    limit=int(os.environ['E16_OUTPUT_LIMIT'])
    A.need(65536<limit<=64*1024**2,'invalid aggregate worker output budget')
    return result,deadline,limit


def run(request_path,digest,authority,reservation):
    # Read only bounded request before proving its requested actual containment.
    metadata=A.read_json(request_path,8*1024**2)
    result,deadline,limit=prove_worker(metadata)
    request=A.verify_for_host(request_path,digest,authority,reservation,deadline=deadline)
    claim_bytes=A.claim_worker(request,digest,deadline)
    # -S prevented site/.pth/sitecustomize code before authentication. Add only
    # the exact hash-bound numerical environment after successful verification.
    site=A.python_path().parent.parent/'lib/python3.12/site-packages'
    sys.path.insert(1,str(site))
    import attribution_transport as T
    import attribution_executor as E
    budget=T.Budget(seconds=max(.001,deadline-time.monotonic()),output_bytes=limit)
    budget.deadline=deadline
    budget.started=float(os.environ['E16_GUARD_ENTRY_AT'])
    budget.charge(claim_bytes)
    outcome=E.run_pipeline(request['packet'],result,budget)
    A.need(outcome['status']=='COMPLETE','incomplete attribution worker')
    # Parent supervisor/host still must reconcile output, resources, cleanup and
    # final shared-guard receipt. A worker success alone is never acceptance.
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('request','digest','authority','reservation'):p.add_argument('--'+name,required=True)
    args=p.parse_args(argv)
    return run(args.request,args.digest,args.authority,args.reservation)


if __name__=='__main__':
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError) as exc:
        print('E16 worker refused: '+str(exc),file=sys.stderr)
        raise SystemExit(2)
