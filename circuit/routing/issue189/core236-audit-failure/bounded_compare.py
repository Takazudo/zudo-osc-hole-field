"""One serial, artifact-bound native comparison; never audit-resume or adopt."""
import ast,collections,hashlib,json,os,re,shutil,signal,subprocess,sys,textwrap,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
ROOT=Path('.circuit-cache/core236-18compare')
SHA=lambda b:hashlib.sha256(b).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def validate_manifest(m):
    cases=m['cases'];keys=[(c['zone_uuid'],c['stage'],c['batch_index']) for c in cases]
    if len(cases)!=18 or len(set(keys))!=18:raise ValueError('exact18distinct cases required')
    f=[c for c in cases if c['layer']=='F.Cu'];b=[c for c in cases if c['layer']=='B.Cu']
    if len(f)!=16 or {(c['stage'],c['batch_index']) for c in b}!={(0,0),(0,1)}:raise ValueError('matched F and two B cases required')
    if any({c['stage'] for c in f if c['batch_index']==i}!={0,1} for i in {c['batch_index'] for c in f}):raise ValueError('F cases must be matched pairs')
    if m['budget']['total_seconds']!=900 or m['budget']['job_minutes']!=20:raise ValueError('total diagnostic budget changed')
    return m
def original_code(source,expected):
    if SHA(source.encode())!=expected:raise ValueError('original inline source changed')
    tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='classify_zone')
    nested=next(n for n in fn.body if isinstance(n,ast.FunctionDef) and n.name=='text_rows')
    lines=source.splitlines();start=next(i for i,l in enumerate(lines) if 'loaded=pcbnew.LoadBoard(str(fixture))' in l)
    end=next(i for i in range(start,len(lines)) if "report=folder/'drc.json'" in lines[i])
    signature=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='native_zone_signature')
    helper='\n'.join(lines[signature.lineno-1:signature.end_lineno])+'\n'+textwrap.dedent('\n'.join(lines[nested.lineno-1:nested.end_lineno]))
    return compile(textwrap.dedent('\n'.join(lines[start:end])),'EXACT617INLINE','exec'),helper
def prepare(manifest):
    m=validate_manifest(read(manifest));ROOT.mkdir(parents=True,exist_ok=False)
    archives=[('original.zip','d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5'),('failure.zip','2cd2463554fdd63a672bf3b59dae5e3473a960017f51c142f9fc0fd7e4ebeaf4')]
    for name,expected in archives:
        with Path('.circuit-cache/'+name).open('rb') as f:
            if hashlib.file_digest(f,'sha256').hexdigest()!=expected:raise ValueError('immutable archive digest mismatch')
    with zipfile.ZipFile('.circuit-cache/original.zip') as z:
        for stage,expected in [('start',m['before_sha256']),('fresh',m['after_sha256'])]:
            folder=ROOT/'inputs'/stage;folder.mkdir(parents=True)
            for suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru'):
                names=[n for n in z.namelist() if n.endswith('osc-core-grid-shards-'+stage+'/osc-core'+suffix)];assert len(names)==1
                data=z.read(names[0]);(folder/('osc-core'+suffix)).write_bytes(data)
            assert SHA((folder/'osc-core.kicad_pcb').read_bytes())==expected
    assert all((ROOT/'inputs/start'/('osc-core'+s)).read_bytes()==(ROOT/'inputs/fresh'/('osc-core'+s)).read_bytes() for s in ('.kicad_pro','.kicad_dru'))
    with zipfile.ZipFile('.circuit-cache/failure.zip') as z:
        for i,c in enumerate(m['cases']):
            folder=ROOT/'inputs'/f'case-{i:02d}';folder.mkdir()
            for suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru'):
                data=z.read(c['archive_folder']+'osc-core'+suffix);(folder/('osc-core'+suffix)).write_bytes(data)
            assert SHA((folder/'osc-core.kicad_pcb').read_bytes())==c['fixture_sha256']
            for s in ('.kicad_pro','.kicad_dru'):assert (folder/('osc-core'+s)).read_bytes()==(ROOT/'inputs/start'/('osc-core'+s)).read_bytes()
            if c['saved_report_sha256']:
                raw=z.read(c['archive_folder']+'drc.json');assert SHA(raw)==c['saved_report_sha256'];identities(json.loads(raw),c['zone_uuid']);(folder/'saved-drc.json').write_bytes(raw)
            else:assert c['archive_folder']+'drc.json' not in z.namelist()
    source=Path(__file__).with_name('baseline-original.py.txt').read_text()
    original_code(source,m['baseline_file_sha256']);(ROOT/'original-inline.py').write_text(source)
    (ROOT/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
def reported_identities(report):
    return sorted((v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in report['violations'])
def identities(report,zone_uuid):
    if report['kicad_version']!='10.0.6' or set(report['included_severities'])!={'error','warning','exclusion'}:raise ValueError('native report incomplete')
    # This is the ORIGINAL zone-fixture verifier, not the full-board cap gate.
    # Pad-free zone fixtures have artificial capped isolated-copper reports;
    # their raw findings are retained but never certified as complete evidence.
    from scripts.pcbgen.audit_added_mask import new_silk_identities
    rows=new_silk_identities(report,zone_uuid)
    return sorted((v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in rows)
def leg(mode):
    import pcbnew
    from scripts.pcbgen.zone_fixture_validation import isolated_fixture_check
    m=validate_manifest(read(ROOT/'manifest.json'));version=subprocess.check_output(['kicad-cli','version'],text=True).strip();assert version=='10.0.6'
    code,helper=original_code((ROOT/'original-inline.py').read_text(),m['baseline_file_sha256']);state={'hashlib':hashlib,'pcbnew':pcbnew};exec(helper,state,state)
    boards=[pcbnew.LoadBoard(str(ROOT/'inputs'/s/'osc-core.kicad_pcb')) for s in ('start','fresh')]
    texts=[state['text_rows'](b) for b in boards];output=ROOT/mode;output.mkdir()
    receipts=[]
    for i,c in enumerate(m['cases']):
        folder=output/f'case-{i:02d}';shutil.copytree(ROOT/'inputs'/f'case-{i:02d}',folder);fixture=folder/'osc-core.kicad_pcb'
        layer=pcbnew.F_Cu if c['layer']=='F.Cu' else pcbnew.B_Cu
        actual_zone=next(z for z in boards[c['stage']].Zones() if z.m_Uuid.AsString()==c['zone_uuid'])
        assert state['native_zone_signature'](actual_zone.GetFilledPolysList(layer))==c['native_geometry_sha256']
        if c['saved_report_sha256']:identities(read(folder/'saved-drc.json'),c['zone_uuid'])
        if mode=='original':
            # Execute exact original statement bytes in one persistent loop
            # namespace: never substitute refactored flag-off validation.
            state.update(fixture=fixture,uid=c['zone_uuid'],layer=layer,item_uids=c['item_uuids'],texts=texts[c['stage']],stage=c['stage'],source_signatures={str(c['stage']):c['native_geometry_sha256']})
            exec(code,state,state);geometry=state['geometry_signature']
        elif mode=='isolated':geometry=isolated_fixture_check(fixture,c['zone_uuid'],layer,c['item_uuids'],texts[c['stage']],c['native_geometry_sha256'])
        else:raise ValueError('unknown mode')
        receipt=dict(case=i,fixture_sha256=SHA(fixture.read_bytes()),native_geometry_sha256=geometry,version=version)
        assert receipt['fixture_sha256']==c['fixture_sha256']
        if c['layer']=='B.Cu':
            report=folder/'new-drc.json';subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--output',str(report),str(fixture)],check=True)
            raw=read(report);actual=identities(raw,c['zone_uuid']);receipt['zone_silk_identities']=actual;receipt['report_sha256']=SHA(report.read_bytes())
            receipt['reported_native_identities']=reported_identities(raw)
            receipt['raw_warning_counts']=dict(collections.Counter(v['type'] for v in raw['violations'] if v['severity']=='warning'))
            receipt['other_warning_domains_complete']=False
            if c['saved_report_sha256']:
                saved=read(folder/'saved-drc.json');assert actual==identities(saved,c['zone_uuid'])
                assert reported_identities(raw)==reported_identities(saved)
        for suffix in ('.kicad_pro','.kicad_dru'):assert fixture.with_suffix(suffix).read_bytes()==(ROOT/'inputs'/('start' if c['stage']==0 else 'fresh')/('osc-core'+suffix)).read_bytes()
        receipts.append(receipt);(output/'partial.json').write_text(json.dumps(receipts)+'\n');print(json.dumps(receipt),flush=True)
    (output/'complete.json').write_text(json.dumps(dict(mode=mode,cases=receipts,status='18CONTROLS COMPLETE; NO FULL AUDIT/ADOPTION'))+'\n')
def containers(mode):
    result=[]
    ids=subprocess.run(['docker','ps','-q'],capture_output=True,text=True,check=True,timeout=5).stdout.split()
    for cid in ids:
        item=json.loads(subprocess.check_output(['docker','inspect',cid],text=True,timeout=5))[0]
        cmd=item['Config'].get('Cmd',[])
        if 'bounded_compare.py' in ' '.join(cmd) and 'leg' in cmd and mode in cmd and item['State']['Pid']>0:result.append((cid,item['State']['Pid']))
    return result
def process_tree(roots):
    allrows={}
    for p in Path('/proc').glob('[0-9]*/status'):
        try:
            s=p.read_text();allrows[int(p.parent.name)]=(int(re.search(r'PPid:\s+(\d+)',s)[1]),int(re.search(r'VmRSS:\s+(\d+)',s)[1]) if 'VmRSS:' in s else 0)
        except (OSError,TypeError):continue
    ids=set(roots)
    while True:
        more={pid for pid,(ppid,rss) in allrows.items() if ppid in ids}
        if more<=ids:break
        ids|=more
    return {pid:allrows[pid][1] for pid in ids if pid in allrows}
def cleanup(proc,owned):
    for cid,pid in owned:
        try:subprocess.run(['docker','kill',cid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
        except (OSError,subprocess.TimeoutExpired):pass
    if proc.poll() is None:
        try:os.killpg(proc.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
            proc.wait(timeout=5)
def stop_reason(sample,now,deadline,budget):
    if now>=deadline:return 'INCONCLUSIVE_TOTAL_BUDGET'
    if sample['available_kib']<budget['minimum_available_kib'] or sample['total_rss_kib']>budget['maximum_process_tree_rss_kib']:return 'INCONCLUSIVE_EARLY_MEMORY_STOP'
    return None
def controller():
    m=validate_manifest(read(ROOT/'manifest.json'));deadline=time.monotonic()+m['budget']['total_seconds'];out=dict(status='INCOMPLETE',adopted=False,modes=[])
    try:
        for mode in ('original','isolated'):
            if time.monotonic()>=deadline:out['status']='INCONCLUSIVE_TOTAL_BUDGET';return
            with (ROOT/(mode+'.stdout')).open('w') as stdout,(ROOT/(mode+'.stderr')).open('w') as stderr:
                script=str(Path(__file__).resolve().relative_to(Path.cwd().resolve()))
                proc=subprocess.Popen(['bash','scripts/kicad/run.sh','python3',script, 'leg',mode],stdout=stdout,stderr=stderr,start_new_session=True);owned=[];reason=None
                try:
                    while proc.poll() is None:
                        owned=containers(mode);tree=process_tree([proc.pid,*[pid for cid,pid in owned]])
                        available=int(re.search(r'MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text())[1]);sample=dict(epoch=time.time(),mode=mode,tree_rss_kib=tree,total_rss_kib=sum(tree.values()),available_kib=available)
                        with (ROOT/'telemetry.jsonl').open('a') as f:f.write(json.dumps(sample)+'\n')
                        reason=stop_reason(sample,time.monotonic(),deadline,m['budget'])
                        if reason:break
                        time.sleep(2)
                finally:
                    cleanup(proc,owned)
                    remaining=containers(mode)
                    after=dict(epoch=time.time(),mode=mode,phase='after_cleanup',tree_rss_kib=process_tree([proc.pid,*[pid for cid,pid in owned]]),owned_containers_remaining=remaining,available_kib=int(re.search(r'MemAvailable:\s+(\d+)',Path('/proc/meminfo').read_text())[1]))
                    with (ROOT/'telemetry.jsonl').open('a') as f:f.write(json.dumps(after)+'\n')
                    if remaining:reason='FAILED_DESCENDANT_CLEANUP'
                out['modes'].append(dict(mode=mode,exit_status=proc.returncode,reason=reason))
                if reason or proc.returncode!=0:out['status']=reason or 'FAILED_NATIVE_LEG';return
        a=read(ROOT/'original/complete.json')['cases'];b=read(ROOT/'isolated/complete.json')['cases'];assert len(a)==len(b)==18
        for x,y in zip(a,b):assert {k:v for k,v in x.items() if k!='report_sha256'}=={k:v for k,v in y.items() if k!='report_sha256'}
        out['status']='18CONTROLS_EQUIVALENT; FULL STABILITY/WARNING COVERAGE NOT ESTABLISHED'
    finally:(ROOT/'comparison.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':
    if sys.argv[1]=='prepare':
        try:prepare(Path(sys.argv[2]))
        except Exception as failure:
            if ROOT.exists():
                with (ROOT/'preflight-failure.json').open('x') as f:f.write(json.dumps(dict(status='INCOMPLETE_PREFLIGHT',adopted=False,error_type=type(failure).__name__,error=str(failure),native_legs_started=0,native_DRC_invocations=0))+'\n')
            raise
    elif sys.argv[1]=='leg':leg(sys.argv[2])
    elif sys.argv[1]=='controller':
        def stop(signum,frame):raise KeyboardInterrupt('external diagnostic stop')
        signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop);controller()
        if not read(ROOT/'comparison.json')['status'].startswith('18CONTROLS_EQUIVALENT'):sys.exit(2)
