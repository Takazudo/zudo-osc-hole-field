import hashlib,json,os,pathlib,subprocess,sys,time
base=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(base.parent/'osc-validation/scripts/architecture278/implementation'))
from stage17_retain import retain
image='kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec'
name='osc-retention-synthetic-20261016-001'
assert os.environ.get('HEAVY_GUARD_HELD')=='1'
assert subprocess.run(['flock','-n',str(pathlib.Path.home()/'.agent-guard/heavy/slot-0.lock'),'true']).returncode!=0
def cmd(argv):return subprocess.check_output(argv,text=True,timeout=20)
def save(name,value):(base/name).write_text(json.dumps(value,indent=2)+'\n')
code="""import pathlib,time,json,os
p=pathlib.Path('/output');(p/'nested').mkdir()
(p/'nested/binary.bin').write_bytes(bytes(range(256))*16384)
(p/'empty.log').write_bytes(b'')
(p/'synthetic.net').write_text('SYNTHETIC ONLY; NOT A KICAD NETLIST\\n')
(p/'manifest-ready.json').write_text(json.dumps({'synthetic':True,'native_commands':0,'cpu.max':pathlib.Path('/sys/fs/cgroup/cpu.max').read_text(),'memory.max':pathlib.Path('/sys/fs/cgroup/memory.max').read_text(),'output_capacity':os.statvfs(p).f_blocks*os.statvfs(p).f_frsize}))
time.sleep(100)
"""
argv=['docker','run','--detach','--pull=never','--name',name,'--platform','linux/amd64','--network','none','--read-only','--cpus','2','--memory','4g','--memory-swap','4g','--pids-limit','128','--cap-drop','ALL','--security-opt','no-new-privileges','--ipc','none','--log-driver','none','--tmpfs','/output:rw,noexec,nosuid,nodev,size=262144000,mode=1777','--mount',f'type=bind,src={base.parent}/native-run-001/empty,dst=/dev/mqueue,readonly','--entrypoint','/usr/bin/timeout',image,'-s','KILL','110','python3','-c',code]
save('argv.json',argv)
start=time.monotonic();results={}
try:
    cid=cmd(argv).strip()
    save('inspect.json',json.loads(cmd(['docker','inspect',cid])))
    for _ in range(30):
        if subprocess.run(['docker','exec',name,'test','-f','/output/manifest-ready.json'],capture_output=True).returncode==0:break
        time.sleep(.1)
    required={'nested/binary.bin','empty.log','synthetic.net','manifest-ready.json'}
    try:
        retain(name,base/'missing',required|{'missing-required.log'},seconds=15)
        raise AssertionError('missing required accepted')
    except ValueError as e:results['missing_required_rejected']=str(e)
    results['container_alive_after_rejection']=cmd(['docker','inspect','--format','{{.State.Running}}',name]).strip()=='true'
    assert results['container_alive_after_rejection']
    receipt=retain(name,base/'retained',required,seconds=45)
    assert receipt['cleanup_permitted']
    assert (base/'retained/nested/binary.bin').read_bytes()==bytes(range(256))*16384
    assert (base/'retained/empty.log').stat().st_size==0
    results.update({'status':'PASS SYNTHETIC RETENTION ONLY','receipt':receipt,'native_commands':0,'elapsed_seconds':time.monotonic()-start})
    save('result.json',results)
finally:
    subprocess.run(['docker','kill',name],capture_output=True,timeout=10)
    save('final-inspect.json',json.loads(cmd(['docker','inspect',name])))
    cmd(['docker','rm',name])
print(json.dumps(results,indent=2))
