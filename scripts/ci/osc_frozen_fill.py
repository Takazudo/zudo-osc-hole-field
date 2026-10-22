"""One disposable fill baseline; Linux container payload, never original writes."""
import collections
import hashlib
import json
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
STATUS = 'FILL_BASELINE_OBSERVATIONS_NOT_ACCEPTANCE'


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

    Preserve atom spelling, node order and every other node. Compare normalized
    SaveBoard snapshots, not writer formatting against the original producer.
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


def native_snapshot(board, pcb):
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
    board.GetConnectivity().RecalculateRatsnest()
    ids={name:topology.uid(item) for name,item in selected.items()}
    rows={}
    for name,item in selected.items():
        members=bounded_members(board.GetConnectivity().GetConnectedItems(item))
        rows[name]={'count':len(members),'uuid_sha256':digest(members),
                    'selected_members':sorted(n for n,u in ids.items() if u in members)}
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
    import pcbnew
    if pcbnew.GetBuildVersion()!='10.0.6': raise ValueError('pcbnew version')
    path=scratch/'before'/'osc-core.kicad_pcb'
    if phase=='normalize':
        board=pcbnew.LoadBoard(str(scratch/'input'/'osc-core.kicad_pcb'))
        if not board: raise ValueError('load failed')
        pcbnew.SaveBoard(str(path),board)
        board=pcbnew.LoadBoard(str(path))
    elif phase=='fill':
        board=pcbnew.LoadBoard(str(path))
        if not board: raise ValueError('load failed')
        if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()): raise ValueError('fill failed')
        path=scratch/'after'/'osc-core.kicad_pcb'
        pcbnew.SaveBoard(str(path),board)
        board=pcbnew.LoadBoard(str(path))
    else: raise ValueError('unknown phase')
    if not path.is_file() or not board: raise ValueError('save/load failure')
    (scratch/(phase+'.json')).write_text(json.dumps(native_snapshot(board,pcbnew)),encoding='utf-8')


def bounded(argv, cwd, deadline, log, watched=()):
    remaining=deadline-time.monotonic()
    if remaining<=0: raise TimeoutError('total deadline exhausted')
    start=time.monotonic()
    with log.open('xb') as output:
        proc=subprocess.Popen(argv,cwd=cwd,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
        try:
            while proc.poll() is None:
                if time.monotonic()>=deadline: raise TimeoutError('total deadline')
                if log.stat().st_size>LOG_LIMIT: raise ValueError('log bound')
                if any(p.exists() and p.stat().st_size>limit for p,limit in watched): raise ValueError('file size bound')
                time.sleep(.05)
        except BaseException:
            os.killpg(proc.pid,signal.SIGKILL)
            proc.wait(timeout=2)
            raise
    if log.stat().st_size>LOG_LIMIT: raise ValueError('log bound')
    if any(p.exists() and p.stat().st_size>limit for p,limit in watched): raise ValueError('file size bound')
    if proc.returncode!=0: raise ValueError('command exit '+str(proc.returncode))
    return {'argv':argv,'exit_code':proc.returncode,'elapsed_seconds':time.monotonic()-start,'log_sha256':sha(log)}


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


def main():
    start=time.monotonic(); deadline=start+100
    root=Path('/work/boards/osc-core'); scratch=Path('/scratch/osc-fill')
    result={'status':'FAILED','board_acceptance':False,'entry_terminal':None,'commands':[],
            'limits':'One fill; 100s total; no link/route edits; outer owned container cleanup required'}
    phase='preflight'
    try:
        result['input_before']=verify_inputs(root)
        result['nonfill_input']=semantic_hash(root/'osc-core.kicad_pcb')
        scratch.mkdir(exist_ok=False)
        for kind in ('input','before','after'):
            dest=scratch/kind; dest.mkdir()
            for name in PINS:
                if kind=='input' or not name.endswith('.kicad_pcb'): shutil.copyfile(root/name,dest/name)
        for phase in ('normalize','drc-before','fill','drc-after'):
            if phase.startswith('drc-'):
                kind=phase[4:]; report=scratch/(phase+'.json')
                argv=['kicad-cli','pcb','drc','--format','json','--severity-all','--output',str(report),str(scratch/kind/'osc-core.kicad_pcb')]
                watched=((report,REPORT_LIMIT),)
            else:
                argv=[sys.executable,'-B',str(Path(__file__).resolve()),'--worker',phase,str(scratch)]
                target='before' if phase=='normalize' else 'after'
                watched=((scratch/(phase+'.json'),REPORT_LIMIT),(scratch/target/'osc-core.kicad_pcb',PCB_LIMIT))
            result['commands'].append(bounded(argv,scratch,deadline,scratch/(phase+'.log'),watched))
            if phase=='normalize':
                result['native_before']=json.loads((scratch/'normalize.json').read_text())
                result['nonfill_before']=semantic_hash(scratch/'before/osc-core.kicad_pcb')
                if result['nonfill_input']!=result['nonfill_before']: raise ValueError('normalization changed non-fill semantics')
            if phase=='fill':
                result['native_after']=json.loads((scratch/'fill.json').read_text())
                result['nonfill_before']=semantic_hash(scratch/'before/osc-core.kicad_pcb')
                result['nonfill_after']=semantic_hash(scratch/'after/osc-core.kicad_pcb')
                if result['nonfill_input']!=result['nonfill_after']: raise ValueError('non-fill semantic change')
        phase='summarize'
        bc,bi=drc_summary(scratch/'drc-before.json'); ac,ai=drc_summary(scratch/'drc-after.json')
        result['drc']={'before':bc,'after':ac,'delta':delta(bi,ai),'before_identity_sha256':digest(sorted(bi.items())), 'after_identity_sha256':digest(sorted(ai.items()))}
        result['scratch_hashes']={kind:sha(scratch/kind/'osc-core.kicad_pcb') for kind in ('input','before','after')}
        result['input_after']=verify_inputs(root)
        for kind in ('before','after'):
            for name in PINS:
                if not name.endswith('.kicad_pcb') and sha(scratch/kind/name)!=PINS[name]: raise ValueError('project/rules changed')
        if time.monotonic()>deadline: raise TimeoutError('total deadline')
        result['status']=STATUS
    except Exception as exc:
        result['failure']={'phase':phase,'type':type(exc).__name__,'message':str(exc)[:500]}
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
    if result.get('source_hashes')!={'before':PINS,'after':PINS}: raise ValueError('source hashes')
    if not hash_ok(result.get('nonfill_input')) or result['nonfill_input']!=result.get('nonfill_before') or result['nonfill_input']!=result.get('nonfill_after'): raise ValueError('non-fill semantics')
    if len(result.get('commands',[]))!=4 or any(x.get('exit_code')!=0 for x in result['commands']): raise ValueError('command outcomes')
    if not isinstance(result.get('elapsed_seconds'),(int,float)) or not 0<=result['elapsed_seconds']<=100: raise ValueError('deadline')
    if 'failure' in result or 'input_recheck_failure' in result: raise ValueError('failure present')
    if not all(k in result for k in ('native_before','native_after','drc','scratch_hashes')): raise ValueError('missing evidence')
    native(result['native_before']);native(result['native_after'])
    hashes=result['scratch_hashes']
    if not isinstance(hashes,dict) or set(hashes)!={'input','before','after'} or not all(hash_ok(h) for h in hashes.values()) or hashes['input']!=PINS['osc-core.kicad_pcb']: raise ValueError('scratch evidence')
    drc=result['drc']
    if not isinstance(drc,dict): raise ValueError('DRC evidence')
    for phase in ('before','after'):
        counts=drc.get(phase)
        if not isinstance(counts,dict) or any(not isinstance(k,str) or not count_ok(v) for k,v in counts.items()) or not hash_ok(drc.get(phase+'_identity_sha256')): raise ValueError('DRC summary')
    changes=drc.get('delta')
    if not isinstance(changes,dict) or set(changes)!={'added','removed'}: raise ValueError('DRC delta')
    for row in changes.values():
        if not isinstance(row,dict) or not count_ok(row.get('count')) or not hash_ok(row.get('identity_sha256')) or type(row.get('sample_complete')) is not bool or not isinstance(row.get('sample'),list) or len(row['sample'])>32: raise ValueError('DRC identities')
        for pair in row['sample']:
            if not isinstance(pair,(list,tuple)) or len(pair)!=2 or not isinstance(pair[0],str) or not count_ok(pair[1]) or pair[1]==0: raise ValueError('DRC sample')
        total=sum(p[1] for p in row['sample'])
        if total>row['count'] or (row['sample_complete'] and total!=row['count']): raise ValueError('DRC count mismatch')


if __name__=='__main__':
    if len(sys.argv)==4 and sys.argv[1]=='--worker': worker(sys.argv[2],Path(sys.argv[3]))
    elif len(sys.argv)==1: sys.exit(main())
    else: raise SystemExit('invalid arguments')
