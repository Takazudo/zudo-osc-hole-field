import hashlib,json,os,pathlib,subprocess,time,resource,sys,traceback
out=pathlib.Path('/output')
started=time.monotonic()
sys.stdout=(out/'supervisor.stdout').open('w',buffering=1)
sys.stderr=(out/'supervisor.stderr').open('w',buffering=1)
def main():
    def save(name,data):
        (out/name).write_text(json.dumps(data,indent=2)+'\n')
    for name in ('home','config','cache','tmp'): (out/name).mkdir()
    cg=pathlib.Path('/sys/fs/cgroup')
    limits={k:(cg/k).read_text().strip() for k in ('cpu.max','memory.max','memory.swap.max','pids.max')}
    fs=os.statvfs(out)
    proof={'limits':limits,'output_capacity_bytes':fs.f_blocks*fs.f_frsize,'mountinfo':pathlib.Path('/proc/self/mountinfo').read_text(),'interfaces':os.listdir('/sys/class/net'),'uid':os.getuid(),'gid':os.getgid(),'groups':os.getgroups(),'other_path_writable':{p:os.access(p,os.W_OK) for p in ('/dev','/dev/mqueue','/etc/hosts','/etc/hostname','/etc/resolv.conf')}}
    save('capability.json',proof)
    assert limits['cpu.max']=='200000 100000'
    assert limits['memory.max']=='4294967296' and limits['memory.swap.max']=='0'
    assert limits['pids.max']=='128' and proof['output_capacity_bytes']==262144000
    assert proof['interfaces']==['lo'] and proof['uid']!=0
    assert os.statvfs('/').f_flag & os.ST_RDONLY
    assert os.statvfs('/inputs').f_flag & os.ST_RDONLY
    assert not os.path.exists('/dev/shm') or os.statvfs('/dev/shm').f_flag & os.ST_RDONLY
    for path in ('/dev','/dev/mqueue','/etc/hosts','/etc/hostname','/etc/resolv.conf'):
        assert not os.access(path,os.W_OK),('unexpected writable path',path)
    assert os.getgid()!=0 and 0 not in os.getgroups()
    (out/'ready').write_text('capabilities asserted\n')
    while not pathlib.Path('/control/admit.json').exists():
        if time.monotonic()-started>300: raise RuntimeError('admission timeout; no native command run')
        time.sleep(.2)
    admission=json.loads(pathlib.Path('/control/admit.json').read_text())
    assert admission['approved'] and admission['source_commit']=='5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b'
    assert set(admission['reviewed_sha256'])=={'container_runner.py','host_runner.py','capability.json','docker-argv.json','input-binding.json','proposal.json'}
    for name,digest in admission['reviewed_sha256'].items():
        assert hashlib.sha256((pathlib.Path('/control')/name).read_bytes()).hexdigest()==digest,name
    binding=json.loads(pathlib.Path('/control/input-binding.json').read_text())
    for name,digest in binding['generated_sha256'].items():
        assert hashlib.sha256((pathlib.Path('/inputs')/name).read_bytes()).hexdigest()==digest,name
    assert hashlib.sha256(pathlib.Path('/inputs/a01.kicad_sch').read_bytes()).hexdigest()=='2d7530895ab55e5b7dd1e41d416f1cb9b295fd716b3b07aa83c83e6dbf195538'
    commands=[['kicad-cli','version'],['kicad-cli','sch','export','netlist','--format','kicadsexpr','-o','/output/netlist.net','/inputs/a01.kicad_sch']]
    records=[]
    for i,argv in enumerate(commands):
        before=time.monotonic()
        with (out/f'command-{i}.stdout').open('wb') as stdout,(out/f'command-{i}.stderr').open('wb') as stderr:
            p=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=max(1,550-(time.monotonic()-started)))
        records.append({'argv':argv,'exit':p.returncode,'elapsed_seconds':time.monotonic()-before})
        save('commands.json',records)
        if p.returncode: break
        if i==0 and (out/'command-0.stdout').read_text().strip()!='10.0.6': break
    save('resource.json',{'elapsed_seconds':time.monotonic()-started,'rusage_children':list(resource.getrusage(resource.RUSAGE_CHILDREN)),'cgroup':{k:(cg/k).read_text() for k in ('memory.peak','memory.events','cpu.stat')}})
    save('output-sha256.json',{str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in out.rglob('*') if p.is_file()})
    (out/'done').write_text('native commands finished; no retry\n')
try:
    main()
except BaseException:
    traceback.print_exc()
    (out/'done').write_text('supervisor failure; inspect stderr; no retry\n')
finally:
    while time.monotonic()-started<580: time.sleep(.25)
