import hashlib,json,os,pathlib,subprocess,time,sys
base=pathlib.Path(__file__).resolve().parent
repo=base.parent/'osc-validation'
image='kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
name='osc-stage17-x0x-20261016-001'
def command(args,**kw):return subprocess.run(args,check=True,capture_output=True,text=True,timeout=30,**kw).stdout
def save(name,data):
    payload=json.dumps(data,indent=2)+'\n'
    assert len(payload.encode())<2*1024*1024
    assert sum(p.stat().st_size for p in base.iterdir() if p.is_file())+len(payload.encode())<12*1024*1024
    (base/name).write_text(payload)
assert not (base/'admit.json').exists(),'stale admission forbidden'
assert os.environ.get('HEAVY_GUARD_HELD')=='1'
assert subprocess.run(['flock','-n',str(pathlib.Path.home()/'.agent-guard/heavy/slot-0.lock'),'true']).returncode!=0
assert int(next(x.split()[1] for x in pathlib.Path('/proc/meminfo').read_text().splitlines() if x.startswith('MemAvailable:')))>4*1024*1024
assert command(['git','-C',str(repo),'rev-parse','HEAD']).strip()=='5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b'
report=json.loads((repo/'design/architecture-278/implementation/stage17/schematic-report.json').read_text())
inputs=repo/'design/architecture-278/implementation/stage17/generated'
for group,root in [('generated_sha256',inputs),('source_sha256',repo)]:
    for path,digest in report[group].items():assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,path
assert {str(p.relative_to(inputs)) for p in inputs.rglob('*') if p.is_file()}==set(report['generated_sha256'])
save('input-binding.json',{'source_commit':'5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b','generated_sha256':report['generated_sha256'],'source_sha256':report['source_sha256']})
argv=['docker','run','--detach','--pull=never','--name',name,'--platform','linux/amd64','--network','none','--read-only','--cpus','2','--memory','4g','--memory-swap','4g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--ipc','none','--log-driver','none','--tmpfs','/output:rw,noexec,nosuid,nodev,size=262144000,mode=1777','--mount',f'type=bind,src={inputs},dst=/inputs,readonly','--mount',f'type=bind,src={base},dst=/control,readonly','--mount',f'type=bind,src={base}/empty,dst=/dev/mqueue,readonly','--workdir','/output','--env','HOME=/output/home','--env','XDG_CONFIG_HOME=/output/config','--env','XDG_CACHE_HOME=/output/cache','--env','TMPDIR=/output/tmp','--entrypoint','/usr/bin/timeout',image,'-s','KILL','600','python3','/control/container_runner.py']
save('docker-argv.json',argv)
start=time.monotonic()
try:
    cid=command(argv).strip()
    save('docker-inspect.json',json.loads(command(['docker','inspect',cid])))
    while time.monotonic()-start<580:
        ready=subprocess.run(['docker','exec',name,'test','-f','/output/ready'],capture_output=True,timeout=10)
        if ready.returncode:
            failed=subprocess.run(['docker','exec',name,'test','-f','/output/done'],capture_output=True,timeout=10)
            if failed.returncode==0:
                target=base/'preflight-failure';target.mkdir()
                command(['docker','cp',name+':/output/.',str(target)])
                raise RuntimeError('capability preflight failed; native NOT RUN; logs retained')
            time.sleep(.5)
            continue
        proof=subprocess.run(['docker','exec',name,'cat','/output/capability.json'],capture_output=True,text=True,timeout=10)
        if proof.returncode==0:
            save('capability.json',json.loads(proof.stdout));break
        time.sleep(.5)
    print('ACTUAL CAPABILITIES RETAINED; waiting for independently reviewed admit.json',flush=True)
    while time.monotonic()-start<580:
        done=subprocess.run(['docker','exec',name,'test','-f','/output/done'],capture_output=True,timeout=10)
        if done.returncode==0:
            target=base/'retained';target.mkdir()
            manifest=json.loads(command(['docker','exec',name,'python3','-c',"import pathlib,json; p=pathlib.Path('/output'); files=list(p.rglob('*')); assert not any(x.is_symlink() for x in files); print(json.dumps({'bytes':sum(x.stat().st_size for x in files if x.is_file())}))"]))
            assert manifest['bytes']<=262144000
            command(['docker','cp',name+':/output/.',str(target)])
            save('result.json',{'elapsed_seconds':time.monotonic()-start,'native_done':True,'retained_bytes':sum(p.stat().st_size for p in target.rglob('*') if p.is_file())})
            print('OUTPUT RETAINED',flush=True);break
        state=command(['docker','inspect','--format','{{.State.Running}}',name]).strip()
        if state!='true':raise RuntimeError('container stopped before completion; native status unknown')
        time.sleep(.5)
    else:raise RuntimeError('host timeout before completion')
finally:
    subprocess.run(['docker','kill',name],capture_output=True,timeout=10)
    save('docker-final.json',json.loads(command(['docker','inspect',name])))
    command(['docker','rm',name])
