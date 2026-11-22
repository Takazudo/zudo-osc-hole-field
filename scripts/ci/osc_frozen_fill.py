"""One disposable fill baseline; Linux container payload, never original writes."""
import collections
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

import osc_frozen_topology as topology

PINS = {
    'osc-core.kicad_pcb': topology.BOARD_HASH,
    'osc-core.kicad_pro': '118d3a49c306babe3ec88c0fb2906cbc29792164c76a677f47c670ba9c0136fe',
    'osc-core.kicad_dru': '14989a90b6d8bec5967487b7bbc915f4382bab17e7759a30517a00e6c11c27ac',
}
VIAS = {
    '124a4a80-065e-5fc9-8a64-4c25e5f56be2': '+12V',
    'b8ef9367-a253-51bc-a1c6-081b159913b4': '+12V',
    'd061a0b1-f9a5-50dc-80b9-4fa3b9b91b59': '+12V',
    '4eb15aa5-9666-5496-87ed-11a7491196b2': '+12V',
    '32dc2066-3f13-5af7-b3e3-07494e0bb60a': 'AGND',
    '38240157-5f63-590a-86c4-6e665aff0b8a': 'AGND',
}
REPORT_LIMIT = 16 * 1024 * 1024
LOG_LIMIT = 64 * 1024
OUTPUT_LIMIT = 900000
PCB_LIMIT = 64 * 1024 * 1024
MEMBER_LIMIT = 100000
MEMORY_CAP = 2147483648
PAYLOAD_SECONDS = 420
PHASE_CAPS = {'normalize':45,'drc-before':100,'fill':300,'drc-after':100}
FILL_RESERVE = 115
SUBSTAGE_LIMIT = 65536
SUBSTAGES = {'normalize':('load','save','reload','metadata','connectivity','zone-metadata','snapshot-save'),
             'fill':('load','fill','save','reload','metadata','connectivity','zone-metadata','snapshot-save')}
CGROUP = Path('/sys/fs/cgroup')
PHASES = ('preflight','normalize','drc-before','fill','drc-after','summarize')
STATUS = 'FILL_BASELINE_OBSERVATIONS_NOT_ACCEPTANCE'


class SubstageLog:
    def __init__(self,path,phase):
        if phase not in SUBSTAGES: raise ValueError('substage phase')
        self.phase=phase;self.seq=0;self.size=0;self.last=-math.inf
        self.stream=path.open('xb')

    def write(self,stage,event):
        stamp=time.monotonic()
        if not math.isfinite(stamp) or stamp<self.last: raise ValueError('substage clock')
        row={'seq':self.seq+1,'phase':self.phase,'stage':stage,'event':event,'monotonic_seconds':stamp}
        data=(json.dumps(row,sort_keys=True)+'\n').encode()
        if self.size+len(data)>SUBSTAGE_LIMIT: raise ValueError('substage log bound')
        if self.stream.write(data)!=len(data): raise OSError('substage short write')
        self.stream.flush();os.fsync(self.stream.fileno())
        self.seq+=1;self.size+=len(data);self.last=stamp

    @contextmanager
    def stage(self,name):
        self.write(name,'start')
        yield
        # Exceptions leave a durable start without a fabricated completion.
        self.write(name,'complete')

    def close(self): self.stream.close()


def parse_substages(data,phase):
    if phase not in SUBSTAGES or len(data)>SUBSTAGE_LIMIT: raise ValueError('substage bound/phase')
    rows=[];previous=-math.inf
    expected=[(stage,event) for stage in SUBSTAGES[phase] for event in ('start','complete')]
    for line in data.splitlines(keepends=True):
        if not line.endswith(b'\n'): raise ValueError('incomplete substage record')
        row=json.loads(line)
        if not isinstance(row,dict) or set(row)!={'seq','phase','stage','event','monotonic_seconds'}: raise ValueError('substage schema')
        i=len(rows);stamp=row['monotonic_seconds']
        if type(row['seq']) is not int or row['seq']!=i+1 or row['phase']!=phase or i>=len(expected) or (row['stage'],row['event'])!=expected[i]: raise ValueError('substage order')
        if type(stamp) not in (int,float) or not math.isfinite(stamp) or stamp<previous: raise ValueError('substage time')
        rows.append(row);previous=stamp
    return {'rows':rows,'complete':len(rows)==len(expected)}


def capture_substages(result,scratch,phase,require_complete=False):
    target=result.setdefault('worker_substages',{})
    path=scratch/(phase+'-substages.jsonl')
    try:
        with path.open('rb') as stream:data=stream.read(SUBSTAGE_LIMIT+1)
        observation={'log_sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),**parse_substages(data,phase)}
        target[phase]=observation
        if require_complete and not observation['complete']: raise ValueError('worker substage incomplete')
    except Exception as exc:
        target.setdefault(phase,{'rows':[],'complete':False})['error']=type(exc).__name__+': '+str(exc)[:240]
        if 'data' in locals():
            prefix=b'';valid={'rows':[],'complete':False}
            for line in data.splitlines(keepends=True):
                try: candidate=parse_substages(prefix+line,phase)
                except Exception: break
                prefix+=line;valid=candidate
            target[phase].update(rows=valid['rows'],complete=False,valid_prefix_bytes=len(prefix),
                captured_bytes=len(data),captured_sha256=hashlib.sha256(data).hexdigest(),
                unparsed_tail=data[len(prefix):len(prefix)+512].decode('utf-8',errors='replace'),
                capture_truncated=len(data)>SUBSTAGE_LIMIT)
        raise


def memory_snapshot():
    """Read only this owned container's unified cgroup, never host discovery."""
    values={}
    for name in ('memory.current','memory.peak','memory.events','memory.max','memory.swap.max'):
        with (CGROUP/name).open(encoding='ascii') as stream: text=stream.read(4097)
        if len(text)>4096: raise ValueError('cgroup telemetry bound')
        if name=='memory.events':
            events={}
            for line in text.splitlines():
                fields=line.split()
                if len(fields)!=2 or not re.fullmatch('[a-z_]{1,32}',fields[0]) or not re.fullmatch('[0-9]{1,20}',fields[1]) or fields[0] in events: raise ValueError('unsupported memory.events')
                events[fields[0]]=int(fields[1])
            if not 1<=len(events)<=16 or not {'low','high','max','oom','oom_kill'}<=set(events): raise ValueError('unsupported memory.events')
            values[name]=events
        else:
            if not re.fullmatch('[0-9]{1,20}',text.strip()): raise ValueError('unsupported '+name)
            values[name]=int(text.strip())
    if values['memory.max']!=MEMORY_CAP: raise ValueError('owned cgroup memory.max mismatch')
    if values['memory.swap.max']!=0: raise ValueError('owned cgroup swap limit mismatch')
    return values


def record_memory(result, phase, point):
    rows=result.setdefault('memory_telemetry',[])
    if len(rows)>=16: raise ValueError('telemetry row bound')
    # Keep failed telemetry explicit without overwriting the primary failure.
    row={'phase':phase,'point':point,'monotonic_seconds':time.monotonic()};rows.append(row)
    try:
        row['values']=memory_snapshot()
        row['peak_semantics']='memory.peak is cumulative for this cgroup, not a phase peak'
        baseline=next((r['values']['memory.events'] for r in rows if 'values' in r),row['values']['memory.events'])
        current=row['values']['memory.events']
        if set(current)!=set(baseline) or any(current[k]<baseline[k] for k in current): raise ValueError('memory.events baseline discontinuity')
        row['events_since_baseline']={k:current[k]-baseline[k] for k in current}
        if any(row['events_since_baseline'].get(k,0)>0 for k in ('oom','oom_kill')):
            raise ValueError('owned cgroup OOM event during run')
    except Exception as exc:
        row['error']=type(exc).__name__+': '+str(exc)[:160]
        raise


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def bounded_members(items):
    ids=set()
    for index,item in enumerate(items):
        if index>=MEMBER_LIMIT: raise ValueError('membership bound')
        ids.add(topology.uid(item))
    return sorted(ids)


def semantic_hash(path):
    """Streaming token hash: ignore ONLY direct zone filled_polygon subtrees.

    Preserve atom spelling, node order and every other node. Require equality
    across the original input, normalized-before and filled-after snapshots.
    """
    token = re.compile(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+')
    stack = []
    pending = False
    skip = None
    h = hashlib.sha256()
    def emit(t):
        data=t.encode(); h.update(len(data).to_bytes(8,'big')); h.update(data)
    # KiCad serialization uses single-line quoted strings; reject unsupported
    # multiline quoted atoms instead of changing their interpretation.
    with path.open(encoding='utf-8') as stream:
        for line in stream:
            if len(re.findall(r'(?<!\\)"', line)) % 2: raise ValueError('multiline quoted atom unsupported')
            for t in token.findall(line):
                if t == '(':
                    if pending: raise ValueError('missing node tag')
                    pending = True; stack.append(None)
                elif t == ')':
                    if pending or not stack: raise ValueError('malformed close')
                    if skip is None: emit(t)
                    if skip == len(stack): skip=None
                    stack.pop()
                elif pending:
                    parent=stack[-2] if len(stack)>1 else None
                    stack[-1]=t; pending=False
                    if skip is None and parent=='zone' and t=='filled_polygon': skip=len(stack)
                    if skip is None: emit('('); emit(t)
                elif skip is None: emit(t)
    if stack or pending: raise ValueError('incomplete sexpression')
    return h.hexdigest()


def verify_inputs(root):
    result={}
    for name, expected in PINS.items():
        p=root/name
        if p.is_symlink() or not p.is_file() or sha(p)!=expected: raise ValueError('input identity: '+name)
        result[name]=expected
    return result


def native_snapshot(board, pcb, stages):
    with stages.stage('metadata'):
        selected={}
        for f in board.GetFootprints():
            for p in f.Pads():
                name=f.GetReference()+'.'+p.GetNumber()
                if name in topology.EXPECTED:
                    wanted=topology.EXPECTED[name]
                    if name in selected or topology.uid(p)!=wanted['uuid'] or p.GetNetname()!=wanted['net']:
                        raise ValueError('pad identity')
                    selected[name]=p
        if set(selected)!=set(topology.EXPECTED): raise ValueError('missing pad')
        for t in board.GetTracks():
            key=topology.uid(t)
            if key in VIAS:
                if key in selected or t.GetNetname()!=VIAS[key]: raise ValueError('via identity')
                selected[key]=t
        if not set(VIAS)<=set(selected): raise ValueError('missing via')
    with stages.stage('connectivity'):
        board.GetConnectivity().RecalculateRatsnest()
        ids={name:topology.uid(item) for name,item in selected.items()}
        rows={}
        for name,item in selected.items():
            members=bounded_members(board.GetConnectivity().GetConnectedItems(item))
            rows[name]={'count':len(members),'uuid_sha256':digest(members),
                        'selected_members':sorted(n for n,u in ids.items() if u in members)}
    with stages.stage('zone-metadata'):
        zones=[]
        for z in board.Zones():
            counts={}
            for name in topology.COPPER_LAYERS:
                layer=getattr(pcb,name.replace('.','_'))
                if z.IsOnLayer(layer): counts[name]=z.GetFilledPolysList(layer).OutlineCount()
            zones.append({'uuid':topology.uid(z),'net':z.GetNetname(),'rule_area':z.GetIsRuleArea(),'counts':counts})
        if len(zones)>1000: raise ValueError('zone bound')
    return {'membership':rows,'zones':zones,'entry_terminal':None,
            'entry_terminal_status':'UNRESOLVED: no source-proven power-entry terminal selected',
            'meaning':'Native membership, not direct-contact adjacency or hardware acceptance'}


def worker(phase, scratch):
    stages=SubstageLog(scratch/(phase+'-substages.jsonl'),phase)
    try:
        import pcbnew
        if pcbnew.GetBuildVersion()!='10.0.6': raise ValueError('pcbnew version')
        path=scratch/'before'/'osc-core.kicad_pcb'
        with stages.stage('load'):
            source=scratch/'input'/'osc-core.kicad_pcb' if phase=='normalize' else path
            board=pcbnew.LoadBoard(str(source))
            if not board: raise ValueError('load failed')
        if phase=='fill':
            with stages.stage('fill'):
                if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()): raise ValueError('fill failed')
            path=scratch/'after'/'osc-core.kicad_pcb'
        with stages.stage('save'):
            pcbnew.SaveBoard(str(path),board)
            if not path.is_file(): raise ValueError('save failed')
        with stages.stage('reload'):
            board=pcbnew.LoadBoard(str(path))
            if not board: raise ValueError('reload failed')
        snapshot=native_snapshot(board,pcbnew,stages)
        with stages.stage('snapshot-save'):
            (scratch/(phase+'.json')).write_text(json.dumps(snapshot),encoding='utf-8')
    finally: stages.close()


def bounded(argv, cwd, deadline, log, watched=(), record=None):
    remaining=deadline-time.monotonic()
    if remaining<=0: raise TimeoutError('total deadline exhausted')
    start=time.monotonic()
    outcome={} if record is None else record
    outcome.update(argv=argv,status='STARTED',start_monotonic_seconds=start,deadline_monotonic_seconds=deadline,exit_code=None)
    proc=None
    try:
        with log.open('xb') as output:
            proc=subprocess.Popen(argv,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
            while proc.poll() is None:
                if time.monotonic()>=deadline: raise TimeoutError('total deadline')
                if log.stat().st_size>LOG_LIMIT: raise ValueError('log bound')
                if any(p.exists() and p.stat().st_size>limit for p,limit in watched): raise ValueError('file size bound')
                time.sleep(.05)
        if log.stat().st_size>LOG_LIMIT: raise ValueError('log bound')
        if any(p.exists() and p.stat().st_size>limit for p,limit in watched): raise ValueError('file size bound')
        if proc.returncode!=0: raise ValueError('command exit '+str(proc.returncode))
        outcome['status']='COMPLETE'
    except BaseException as exc:
        outcome['status']='FAILED';outcome['error']=type(exc).__name__+': '+str(exc)[:500]
        if proc is not None and proc.poll() is None:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait(timeout=2)
        raise
    finally:
        outcome['end_monotonic_seconds']=time.monotonic()
        outcome['elapsed_seconds']=outcome['end_monotonic_seconds']-start
        outcome['exit_code']=proc.returncode if proc is not None else None
        if log.is_file(): outcome['log_sha256']=sha(log)
    return outcome


def drc_summary(path):
    if path.stat().st_size>REPORT_LIMIT: raise ValueError('report bound')
    d=json.loads(path.read_text())
    if d.get('kicad_version')!='10.0.6': raise ValueError('DRC version')
    counts=collections.Counter()
    identities=collections.Counter()
    for category in ('violations','unconnected_items','schematic_parity'):
        if not isinstance(d.get(category),list): raise ValueError('missing DRC category')
        for row in d[category]:
            if not isinstance(row,dict) or not isinstance(row.get('items'),list): raise ValueError('malformed DRC row')
            ids=[]
            for item in row['items']:
                if not isinstance(item.get('uuid'),str) or not item['uuid']: raise ValueError('missing DRC UUID')
                ids.append(item['uuid'])
            key=json.dumps([category,row.get('type'),row.get('severity'),row.get('description'),sorted(ids)],separators=(',',':'))
            identities[key]+=1; counts[category+':'+str(row.get('type'))]+=1
    if sum(identities.values())>100000: raise ValueError('DRC item bound')
    return dict(counts),identities


def delta(before, after):
    def summarize(counter):
        rows=sorted(counter.items())
        return {'count':sum(counter.values()),'identity_sha256':digest(rows),'sample':rows[:32], 'sample_complete':len(rows)<=32}
    return {'added':summarize(after-before),'removed':summarize(before-after)}


def drc_checkpoint(result, phase, path):
    counts,identities=drc_summary(path)
    result.setdefault('drc_checkpoints',{})[phase]={
        'report_sha256':sha(path),'report_bytes':path.stat().st_size,
        'counts':counts,'identities':delta(collections.Counter(),identities)['added']}
    result.setdefault('drc_counts',{})[phase.removeprefix('drc-')]=counts
    return counts,identities


def phase_deadline(total, phase, now):
    if phase not in PHASE_CAPS: raise ValueError('unknown bounded phase')
    if now>=total: raise TimeoutError('total deadline exhausted')
    limit=min(total-FILL_RESERVE,now+PHASE_CAPS[phase]) if phase=='fill' else min(total,now+PHASE_CAPS[phase])
    if limit<=now: raise TimeoutError('fill post-DRC/summarize reserve exhausted')
    return limit


def phase_start(result,phase):
    row={'phase':phase,'status':'STARTED','start_monotonic_seconds':time.monotonic()}
    result.setdefault('phase_results',[]).append(row)
    return row


def phase_end(row,status,deadline):
    row.update(status=status,end_monotonic_seconds=time.monotonic())
    row['elapsed_seconds']=row['end_monotonic_seconds']-row['start_monotonic_seconds']
    if status=='COMPLETE' and row['end_monotonic_seconds']>deadline:
        row['status']='FAILED';raise TimeoutError('phase deadline exhausted')


def main():
    start=time.monotonic(); deadline=start+PAYLOAD_SECONDS
    root=Path('/work/boards/osc-core'); scratch=Path('/scratch/osc-fill')
    result={'status':'FAILED','board_acceptance':False,'entry_terminal':None,'commands':[],
            'limits':'One fill; 420s payload; caps45/100/300/100; fill reserves115s for post-DRC+summary; no route edits'}
    phase='preflight'
    phase_row=phase_start(result,phase)
    drc_data={}
    try:
        record_memory(result,phase,'before')
        result['input_before']=verify_inputs(root)
        result['nonfill_input']=semantic_hash(root/'osc-core.kicad_pcb')
        scratch.mkdir(exist_ok=False)
        for kind in ('input','before','after'):
            dest=scratch/kind; dest.mkdir()
            for name in PINS:
                if kind=='input' or not name.endswith('.kicad_pcb'): shutil.copyfile(root/name,dest/name)
        record_memory(result,phase,'after')
        phase_end(phase_row,'COMPLETE',deadline)
        for phase in ('normalize','drc-before','fill','drc-after'):
            phase_row=phase_start(result,phase)
            local_deadline=phase_deadline(deadline,phase,phase_row['start_monotonic_seconds'])
            record_memory(result,phase,'before')
            if phase.startswith('drc-'):
                kind=phase[4:]; report=scratch/(phase+'.json')
                argv=['kicad-cli','pcb','drc','--format','json','--severity-all','--output',str(report),str(scratch/kind/'osc-core.kicad_pcb')]
                watched=((report,REPORT_LIMIT),)
            else:
                argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker',phase,str(scratch)]
                target='before' if phase=='normalize' else 'after'
                watched=((scratch/(phase+'.json'),REPORT_LIMIT),(scratch/target/'osc-core.kicad_pcb',PCB_LIMIT),(scratch/(phase+'-substages.jsonl'),SUBSTAGE_LIMIT))
            command={'phase':phase};result['commands'].append(command)
            bounded(argv,scratch,local_deadline,scratch/(phase+'.log'),watched,command)
            if phase in SUBSTAGES: capture_substages(result,scratch,phase,require_complete=True)
            if phase.startswith('drc-'):
                drc_data[phase]=drc_checkpoint(result,phase,report)
            if phase=='normalize':
                result['native_before']=json.loads((scratch/'normalize.json').read_text())
                result['nonfill_before']=semantic_hash(scratch/'before/osc-core.kicad_pcb')
                if result['nonfill_input']!=result['nonfill_before']: raise ValueError('normalization changed non-fill semantics')
            if phase=='fill':
                result['native_after']=json.loads((scratch/'fill.json').read_text())
                result['nonfill_before']=semantic_hash(scratch/'before/osc-core.kicad_pcb')
                result['nonfill_after']=semantic_hash(scratch/'after/osc-core.kicad_pcb')
                if result['nonfill_input']!=result['nonfill_after']: raise ValueError('non-fill semantic change')
            record_memory(result,phase,'after')
            phase_end(phase_row,'COMPLETE',local_deadline)
        phase='summarize'
        phase_row=phase_start(result,phase)
        record_memory(result,phase,'before')
        bc,bi=drc_data['drc-before']; ac,ai=drc_data['drc-after']
        result['drc']={'before':bc,'after':ac,'delta':delta(bi,ai),'before_identity_sha256':digest(sorted(bi.items())), 'after_identity_sha256':digest(sorted(ai.items()))}
        result['scratch_hashes']={kind:sha(scratch/kind/'osc-core.kicad_pcb') for kind in ('input','before','after')}
        result['input_after']=verify_inputs(root)
        for kind in ('before','after'):
            for name in PINS:
                if not name.endswith('.kicad_pcb') and sha(scratch/kind/name)!=PINS[name]: raise ValueError('project/rules changed')
        record_memory(result,phase,'after')
        phase_end(phase_row,'COMPLETE',deadline)
        if time.monotonic()>deadline: raise TimeoutError('total deadline')
        result['status']=STATUS
    except Exception as exc:
        phase_end(phase_row,'FAILED',deadline)
        result['failure']={'phase':phase,'type':type(exc).__name__,'message':str(exc)[:500]}
        if phase in SUBSTAGES:
            try: capture_substages(result,scratch,phase)
            except Exception as check: result['substage_capture_failure']=type(check).__name__+': '+str(check)[:240]
        try: record_memory(result,phase,'failed')
        except Exception as check: result['telemetry_failure']=type(check).__name__+': '+str(check)[:160]
        log=scratch/(phase+'.log')
        if log.is_file():
            result['failure']['log_sha256']=sha(log)
            with log.open('rb') as stream:
                stream.seek(max(0,log.stat().st_size-4096))
                result['failure']['log_tail']=stream.read(4096).decode('utf-8',errors='replace')
        try: result['input_after']=verify_inputs(root)
        except Exception as check: result['input_recheck_failure']=str(check)[:500]
    result['elapsed_seconds']=time.monotonic()-start
    result['source_hashes']={'before':result.get('input_before'), 'after':result.get('input_after')}
    data=json.dumps(result,sort_keys=True)
    if len(data.encode())>OUTPUT_LIMIT:
        data=json.dumps({'status':'FAILED','board_acceptance':False,'failure':{'phase':'serialization','message':'output bound'},'elapsed_seconds':time.monotonic()-start})
        print(data); return 1
    print(data)
    return 0 if result['status']==STATUS else 1


def validate_result(result):
    def hash_ok(value): return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
    def count_ok(value): return type(value) is int and value>=0
    def native(value):
        names=set(topology.EXPECTED)|set(VIAS)
        if not isinstance(value,dict) or value.get('entry_terminal') is not None or not isinstance(value.get('entry_terminal_status'),str): raise ValueError('native evidence')
        members=value.get('membership')
        if not isinstance(members,dict) or set(members)!=names: raise ValueError('native endpoint coverage')
        for row in members.values():
            if not isinstance(row,dict) or not count_ok(row.get('count')) or row['count']>MEMBER_LIMIT or not hash_ok(row.get('uuid_sha256')): raise ValueError('native membership')
            ids=row.get('selected_members')
            if not isinstance(ids,list) or any(not isinstance(x,str) for x in ids) or len(ids)!=len(set(ids)) or not set(ids)<=names or len(ids)>row['count']: raise ValueError('selected membership')
        zones=value.get('zones')
        if not isinstance(zones,list) or not 1<=len(zones)<=1000: raise ValueError('native zones')
        seen=set()
        for z in zones:
            if not isinstance(z,dict) or not isinstance(z.get('uuid'),str) or not z['uuid'] or z['uuid'] in seen or not isinstance(z.get('net'),str) or type(z.get('rule_area')) is not bool: raise ValueError('zone identity')
            seen.add(z['uuid']); counts=z.get('counts')
            if not isinstance(counts,dict) or not counts or not set(counts)<=set(topology.COPPER_LAYERS) or not all(count_ok(n) for n in counts.values()): raise ValueError('zone counts')
        if not set(topology.ZONES)<=seen: raise ValueError('zone coverage')
    if result.get('status')!=STATUS or result.get('board_acceptance') is not False: raise ValueError('fill unsuccessful')
    worker_rows=result.get('worker_substages')
    if not isinstance(worker_rows,dict) or set(worker_rows)!=set(SUBSTAGES): raise ValueError('worker substage coverage')
    for phase,entry in worker_rows.items():
        if not isinstance(entry,dict) or entry.get('complete') is not True or 'error' in entry or not hash_ok(entry.get('log_sha256')) or not count_ok(entry.get('bytes')) or not 0<entry['bytes']<=SUBSTAGE_LIMIT: raise ValueError('worker substage evidence')
        data=b''.join((json.dumps(row)+'\n').encode() for row in entry.get('rows',[]))
        if not parse_substages(data,phase)['complete']: raise ValueError('worker substage incomplete')
    if result.get('source_hashes')!={'before':PINS,'after':PINS}: raise ValueError('source hashes')
    if not hash_ok(result.get('nonfill_input')) or result['nonfill_input']!=result.get('nonfill_before') or result['nonfill_input']!=result.get('nonfill_after'): raise ValueError('non-fill semantics')
    if len(result.get('commands',[]))!=4 or any(x.get('exit_code')!=0 for x in result['commands']): raise ValueError('command outcomes')
    phase_rows=result.get('phase_results')
    if not isinstance(phase_rows,list) or [p.get('phase') for p in phase_rows]!=list(PHASES): raise ValueError('phase coverage')
    for p in phase_rows:
        a=p.get('start_monotonic_seconds');b=p.get('end_monotonic_seconds');elapsed=p.get('elapsed_seconds')
        if p.get('status')!='COMPLETE' or any(type(v) not in (int,float) or not math.isfinite(v) for v in (a,b,elapsed)) or b<a or elapsed!=b-a or elapsed>PHASE_CAPS.get(p['phase'],PAYLOAD_SECONDS): raise ValueError('phase outcome')
    checkpoints=result.get('drc_checkpoints')
    if not isinstance(checkpoints,dict) or set(checkpoints)!={'drc-before','drc-after'}: raise ValueError('DRC checkpoint coverage')
    for name,row in checkpoints.items():
        if not isinstance(row,dict) or not hash_ok(row.get('report_sha256')) or not count_ok(row.get('report_bytes')) or not 0<row['report_bytes']<=REPORT_LIMIT or not isinstance(row.get('counts'),dict) or not isinstance(row.get('identities'),dict): raise ValueError('DRC checkpoint')
        if result.get('drc_counts',{}).get(name[4:])!=row['counts']: raise ValueError('DRC checkpoint counts')
    if not isinstance(result.get('elapsed_seconds'),(int,float)) or not 0<=result['elapsed_seconds']<=PAYLOAD_SECONDS: raise ValueError('deadline')
    if 'failure' in result or 'input_recheck_failure' in result: raise ValueError('failure present')
    frames=result.get('memory_telemetry')
    if not isinstance(frames,list) or [(x.get('phase'),x.get('point')) for x in frames]!=[(p,q) for p in PHASES for q in ('before','after')]: raise ValueError('telemetry coverage')
    previous=-math.inf
    for frame in frames:
        stamp=frame.get('monotonic_seconds')
        if type(stamp) not in (int,float) or not math.isfinite(stamp) or stamp<previous: raise ValueError('telemetry timestamp')
        previous=stamp
        v=frame.get('values')
        if 'error' in frame or not isinstance(v,dict) or set(v)!={'memory.current','memory.peak','memory.events','memory.max','memory.swap.max'} or v['memory.max']!=MEMORY_CAP or v['memory.swap.max']!=0: raise ValueError('telemetry values')
        if any(not count_ok(v[k]) for k in ('memory.current','memory.peak','memory.max','memory.swap.max')): raise ValueError('telemetry counts')
        events=v['memory.events']
        if not isinstance(events,dict) or not 1<=len(events)<=16 or not {'low','high','max','oom','oom_kill'}<=set(events) or any(not isinstance(k,str) or not count_ok(n) for k,n in events.items()): raise ValueError('telemetry events')
        baseline=frames[0]['values']['memory.events']
        if set(events)!=set(baseline) or any(events[k]<baseline[k] for k in events) or frame.get('events_since_baseline')!={k:events[k]-baseline[k] for k in events}: raise ValueError('telemetry delta')
        if any(frame['events_since_baseline'].get(k,0)>0 for k in ('oom','oom_kill')): raise ValueError('OOM event prevents success')
    if not all(k in result for k in ('native_before','native_after','drc','scratch_hashes')): raise ValueError('missing evidence')
    native(result['native_before']);native(result['native_after'])
    hashes=result['scratch_hashes']
    if not isinstance(hashes,dict) or set(hashes)!={'input','before','after'} or not all(hash_ok(h) for h in hashes.values()) or hashes['input']!=PINS['osc-core.kicad_pcb']: raise ValueError('scratch evidence')
    drc=result['drc']
    if not isinstance(drc,dict): raise ValueError('DRC evidence')
    for phase in ('before','after'):
        counts=drc.get(phase)
        if not isinstance(counts,dict) or any(not isinstance(k,str) or not count_ok(v) for k,v in counts.items()) or not hash_ok(drc.get(phase+'_identity_sha256')): raise ValueError('DRC summary')
        checkpoint=checkpoints['drc-'+phase]
        if counts!=checkpoint['counts'] or drc[phase+'_identity_sha256']!=checkpoint['identities'].get('identity_sha256') or sum(counts.values())!=checkpoint['identities'].get('count'): raise ValueError('DRC checkpoint consistency')
    changes=drc.get('delta')
    if not isinstance(changes,dict) or set(changes)!={'added','removed'}: raise ValueError('DRC delta')
    for row in list(changes.values())+[c['identities'] for c in checkpoints.values()]:
        if not isinstance(row,dict) or not count_ok(row.get('count')) or not hash_ok(row.get('identity_sha256')) or type(row.get('sample_complete')) is not bool or not isinstance(row.get('sample'),list) or len(row['sample'])>32: raise ValueError('DRC identities')
        for pair in row['sample']:
            if not isinstance(pair,(list,tuple)) or len(pair)!=2 or not isinstance(pair[0],str) or not count_ok(pair[1]) or pair[1]==0: raise ValueError('DRC sample')
        total=sum(p[1] for p in row['sample'])
        if total>row['count'] or (row['sample_complete'] and total!=row['count']): raise ValueError('DRC count mismatch')


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--worker': worker(sys.argv[2],Path(sys.argv[3]))
    elif len(sys.argv)==1: sys.exit(main())
    else: raise SystemExit('invalid arguments')
