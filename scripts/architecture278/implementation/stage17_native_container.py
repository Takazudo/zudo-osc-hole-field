"""Future exact admitted native supervisor. Never run without a fresh review."""
import hashlib,json,os,pathlib,resource,subprocess,sys,time,traceback

SOURCE='5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b'
out=pathlib.Path('/output'); control=pathlib.Path('/control')
started=time.monotonic(); records=[]; status='SUPERVISOR_FAILURE'
sys.stdout=(out/'supervisor.stdout').open('w',buffering=1)
sys.stderr=(out/'supervisor.stderr').open('w',buffering=1)
def save(name,value): (out/name).write_text(json.dumps(value,indent=2)+'\n')
def main():
    global status
    for folder in ('home','config','cache','tmp'): (out/folder).mkdir()
    cg=pathlib.Path('/sys/fs/cgroup')
    limits={k:(cg/k).read_text().strip() for k in ('cpu.max','memory.max','memory.swap.max','pids.max')}
    fs=os.statvfs(out)
    proof={'limits':limits,'output_capacity_bytes':fs.f_blocks*fs.f_frsize,'mountinfo':pathlib.Path('/proc/self/mountinfo').read_text(),'interfaces':os.listdir('/sys/class/net'),'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),'other_path_writable':{p:os.access(p,os.W_OK) for p in ('/dev','/dev/mqueue','/etc/hosts','/etc/hostname','/etc/resolv.conf')}}
    save('capability.json',proof)
    assert limits=={'cpu.max':'200000 100000','memory.max':'4294967296','memory.swap.max':'0','pids.max':'128'}
    assert proof['output_capacity_bytes']==262144000 and proof['interfaces']==['lo']
    assert os.getuid()!=0 and os.getgid()!=0 and 0 not in os.getgroups()
    assert all(not x for x in proof['other_path_writable'].values())
    assert all(os.statvfs(p).f_flag & os.ST_RDONLY for p in ('/','/inputs','/control'))
    assert not os.path.exists('/dev/shm') or os.statvfs('/dev/shm').f_flag & os.ST_RDONLY
    (out/'ready').write_text('capabilities asserted\n')
    while not (control/'admit.json').exists():
        if time.monotonic()-started>300: raise TimeoutError('admission expired; native NOT RUN')
        time.sleep(.2)
    admission=json.loads((control/'admit.json').read_text())
    assert admission['approved'] and admission['source_commit']==SOURCE
    required={'stage17_native_container.py','stage17_native_host.py','stage17_retain.py','capability.json','docker-argv.json','input-binding.json','proposal.json'}
    assert set(admission['reviewed_sha256'])==required
    for name,digest in admission['reviewed_sha256'].items():
        assert hashlib.sha256((control/name).read_bytes()).hexdigest()==digest,name
    binding=json.loads((control/'input-binding.json').read_text())
    assert {str(p.relative_to('/inputs')) for p in pathlib.Path('/inputs').rglob('*') if p.is_file()}==set(binding['generated_sha256'])
    for name,digest in binding['generated_sha256'].items():
        assert hashlib.sha256((pathlib.Path('/inputs')/name).read_bytes()).hexdigest()==digest,name
    commands=[['kicad-cli','version'],['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o','/output/netlist.net','/inputs/a01.kicad_sch']]
    status='NATIVE_FAILURE'
    for index,argv in enumerate(commands):
        record={'argv':argv,'started_elapsed_seconds':time.monotonic()-started,'exit':None}
        records.append(record);save('commands.json',records)
        with (out/f'command-{index}.stdout').open('wb') as stdout,(out/f'command-{index}.stderr').open('wb') as stderr:
            result=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=max(1,500-(time.monotonic()-started)))
        record.update(exit=result.returncode,elapsed_seconds=time.monotonic()-started-record['started_elapsed_seconds'])
        save('commands.json',records)
        if result.returncode: return
        if index==0 and (out/'command-0.stdout').read_text().strip()!='10.0.6':
            status='VERSION_MISMATCH';return
    assert (out/'netlist.net').is_file() and (out/'netlist.net').stat().st_size>0
    status='NATIVE_SUCCESS'
try:
    main()
except BaseException:
    traceback.print_exc()
finally:
    cg=pathlib.Path('/sys/fs/cgroup')
    save('resource.json',{'elapsed_seconds':time.monotonic()-started,'rusage_children':list(resource.getrusage(resource.RUSAGE_CHILDREN)),'cgroup':{k:(cg/k).read_text() for k in ('memory.peak','memory.events','cpu.stat')}})
    sys.stdout.flush();sys.stderr.flush()
    save('done.json',{'status':status,'commands_attempted':len(records),'native_success':status=='NATIVE_SUCCESS'})
    # All producer files are now quiescent; host verifies inventory twice.
    while time.monotonic()-started<595: time.sleep(.25)
