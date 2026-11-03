"""Future run orchestrator. Requires separate owner approval and live admission."""
import argparse,hashlib,json,os,pathlib,shutil,subprocess,time
import stage17_retain
from stage17_retain import retain

SOURCE='5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b'
IMAGE='kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repo',type=pathlib.Path,required=True)
    parser.add_argument('--run',type=pathlib.Path,required=True)
    parser.add_argument('--verification-commit',required=True)
    args=parser.parse_args();repo=args.repo.resolve();base=args.run.resolve()
    assert not base.exists(),'unique fresh output/control directory required'
    assert os.environ.get('HEAVY_GUARD_HELD')=='1'
    assert subprocess.run(['flock','-n',str(pathlib.Path.home()/'.agent-guard/heavy/slot-0.lock'),'true']).returncode!=0
    assert int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))>4*1024*1024
    def cmd(argv,timeout=20):return subprocess.check_output(argv,text=True,timeout=timeout)
    assert cmd(['git','-C',str(repo),'rev-parse','HEAD']).strip()==args.verification_commit
    script_dir=repo/'scripts/architecture278/implementation'
    assert pathlib.Path(__file__).resolve().parent==script_dir
    assert pathlib.Path(stage17_retain.__file__).resolve()==script_dir/'stage17_retain.py'
    for script in ('stage17_native_host.py','stage17_native_container.py','stage17_retain.py'):
        pinned=subprocess.check_output(['git','-C',str(repo),'show',args.verification_commit+':scripts/architecture278/implementation/'+script])
        assert (script_dir/script).read_bytes()==pinned,('verification script drift',script)
    path='design/architecture-278/implementation/stage17/schematic-report.json'
    raw=subprocess.check_output(['git','-C',str(repo),'show',SOURCE+':'+path])
    assert (repo/path).read_bytes()==raw
    report=json.loads(raw);inputs=repo/'design/architecture-278/implementation/stage17/generated'
    for group,root in [('generated_sha256',inputs),('source_sha256',repo)]:
        for name,digest in report[group].items():assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
    base.mkdir();(base/'empty').mkdir()
    for name in ('stage17_native_host.py','stage17_native_container.py','stage17_retain.py'):
        shutil.copyfile(pathlib.Path(__file__).parent/name,base/name)
    def save(name,value):
        payload=json.dumps(value,indent=2)+'\n'
        assert sum(p.stat().st_size for p in base.iterdir() if p.is_file())+len(payload.encode())<12*1024*1024
        (base/name).write_text(payload)
    save('input-binding.json',{'source_commit':SOURCE,'generated_sha256':report['generated_sha256'],'source_sha256':report['source_sha256']})
    save('proposal.json',{'status':'WAITING_FRESH_OWNER_AUTHORIZATION_AND_REVIEW','source_commit':SOURCE,'verification_commit':args.verification_commit,'run':str(base),'quota':'250MiB live+250MiB retained+12MiB metadata <=512MiB','timeout_seconds':600,'native_attempts':1})
    name=base.name
    assert name=='osc-stage17-x0x-002','this proposal admits only the new unique run002'
    argv=['docker','run','--detach','--pull=never','--name',name,'--platform','linux/amd64','--network','none','--read-only','--cpus','2','--memory','4g','--memory-swap','4g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--ipc','none','--log-driver','none','--tmpfs','/output:rw,noexec,nosuid,nodev,size=262144000,mode=1777','--mount',f'type=bind,src={inputs},dst=/inputs,readonly','--mount',f'type=bind,src={base},dst=/control,readonly','--mount',f'type=bind,src={base}/empty,dst=/dev/mqueue,readonly','--workdir','/output','--env','HOME=/output/home','--env','XDG_CONFIG_HOME=/output/config','--env','XDG_CACHE_HOME=/output/cache','--env','TMPDIR=/output/tmp','--entrypoint','/usr/bin/timeout',IMAGE,'-s','KILL','600','python3','/control/stage17_native_container.py']
    save('docker-argv.json',argv)
    start=time.monotonic();verified=False;cid=None
    try:
        cid=cmd(argv).strip();save('docker-inspect.json',json.loads(cmd(['docker','inspect',cid])))
        proof_saved=False
        while time.monotonic()-start<520:
            if not proof_saved and subprocess.run(['docker','exec',name,'test','-f','/output/ready'],capture_output=True,timeout=10).returncode==0:
                save('capability.json',json.loads(cmd(['docker','exec',name,'cat','/output/capability.json'])))
                print('WAITING: independently review actual capabilities and create bound admit.json',flush=True);proof_saved=True
            if subprocess.run(['docker','exec',name,'test','-f','/output/done.json'],capture_output=True,timeout=10).returncode==0:
                receipt=retain(name,base/'retained',{'supervisor.stdout','supervisor.stderr','done.json','resource.json'},seconds=min(60,580-(time.monotonic()-start)))
                save('retention.json',receipt)
                done=json.loads((base/'retained/done.json').read_text())
                names={r['path'] for r in receipt['files']}
                commands=json.loads((base/'retained/commands.json').read_text()) if 'commands.json' in names else []
                assert done['commands_attempted']==len(commands)
                for index,record in enumerate(commands):
                    assert {f'command-{index}.stdout',f'command-{index}.stderr'}<=names
                if done['native_success']:
                    required={'commands.json','command-0.stdout','command-0.stderr','command-1.stdout','command-1.stderr','netlist.net'}
                    assert required <= {r['path'] for r in receipt['files']}
                    assert (base/'retained/command-0.stdout').read_text().strip()=='10.0.6'
                    assert (base/'retained/netlist.net').stat().st_size>0
                    assert [r['argv'] for r in commands]==[['kicad-cli','version'],['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o','/output/netlist.net','/inputs/a01.kicad_sch']]
                    assert all(r['exit']==0 for r in commands)
                verified=receipt['cleanup_permitted']
                save('assessment.json',{'native':done,'retention':receipt['status'],'parity':'NOT RUN until independent comparator','elapsed_seconds':time.monotonic()-start})
                print(json.dumps(done),flush=True)
                return 0 if done['native_success'] else 1
            time.sleep(.2)
        raise TimeoutError('native supervisor completion deadline')
    except BaseException as error:
        save('host-failure.json',{'error':str(error),'verified_copy':verified,'native_result':'UNKNOWN unless retained records establish it'})
        raise
    finally:
        if cid:
            if not verified:
                print('RETENTION FAILED: holding source until hard600s deadline; no retry',flush=True)
                while time.monotonic()-start<600: time.sleep(.5)
            subprocess.run(['docker','kill',name],capture_output=True,timeout=10)
            save('docker-final.json',json.loads(cmd(['docker','inspect',name])))
            cmd(['docker','rm',name])

if __name__=='__main__': raise SystemExit(main())
