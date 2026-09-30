#!/usr/bin/env python3
"""Bounded, offline Freerouting DSN/SES round trip for unvalidated PCB drafts."""
from __future__ import annotations
import argparse,copy,hashlib,json,os,re,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.definition import load_definition

SIZE_RE=re.compile(r'([\d.]+)\s*(B|KiB|MiB|GiB|TiB)')

def read_env():
    text=(ROOT/'scripts/pcbgen/router.env').read_text()
    values=dict(line.split('=',1) for line in text.splitlines() if line and not line.startswith('#'))
    image=values['ROUTER_IMAGE']
    if not re.fullmatch(r'ghcr\.io/freerouting/freerouting@sha256:[0-9a-f]{64}',image):raise ValueError('router image must be digest-pinned')
    return image,int(values['ROUTER_HEAP_MB']),int(values['ROUTER_TIMEOUT_SEC'])

def repo_relative(path):
    return str(path.resolve().relative_to(ROOT))

def run(command,log=None,check=True):
    done=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if log:Path(log).write_text(done.stdout)
    if done.stdout:print(done.stdout[-2000:],end='')
    if check and done.returncode:raise RuntimeError(f'command failed ({done.returncode}): {command[0]} {command[1]}')
    return done

def drc(board,path):
    command=['bash','scripts/kicad/run.sh','kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',repo_relative(path),repo_relative(board)]
    # A failed invocation must never reuse an earlier successful oracle report.
    path.unlink(missing_ok=True)
    result=run(command,check=False)
    if result.returncode:raise RuntimeError(f'KiCad DRC failed (exit {result.returncode})')
    if not path.exists():raise RuntimeError(f'KiCad DRC report missing (exit {result.returncode})')
    data=json.loads(path.read_text())
    if data.get('kicad_version')!='10.0.6':raise RuntimeError('wrong KiCad oracle version')
    return data

def unrouted_names(data):
    names=set()
    for item in data.get('unconnected_items',[]):
        for part in item.get('items',[]):
            match=re.search(r'\[([^]]+)\]',part.get('description',''))
            if match:names.add(match[1])
    return sorted(names)

def drc_summary(data):
    return {'rule_errors':sum(x.get('severity')=='error' for x in data.get('violations',[])),
            'rule_warnings':sum(x.get('severity')=='warning' for x in data.get('violations',[])),
            'unconnected_items':len(data.get('unconnected_items',[])),
            'unrouted_nets':unrouted_names(data),
            'schematic_parity_issues':len(data.get('schematic_parity',[]))}

def drc_passes(summary):
    """Connectivity alone cannot establish the routing gate."""
    return all(summary[key] == 0 for key in ('rule_errors', 'unconnected_items', 'schematic_parity_issues'))

def project_settings(board,routing):
    project=board.with_suffix('.kicad_pro')
    if not project.exists():raise RuntimeError(f'KiCad project missing: {project}')
    data=json.loads(project.read_text())
    design=data.setdefault('board',{}).setdefault('design_settings',{})
    design.setdefault('rules',{})['min_track_width']=routing['min_track_width_mm']
    settings=data.setdefault('net_settings',{})
    classes=settings.get('classes',[])
    default=next((c for c in classes if c.get('name')=='Default'),None)
    if default is None:raise RuntimeError('KiCad project has no Default net class')
    by_name={c['name']:c for c in classes}
    for spec in routing['net_classes']:
        c=by_name.get(spec['name'])
        if c is None:c=copy.deepcopy(default);c['name']=spec['name'];by_name[spec['name']]=c
        for target,key in (('track_width','track_width_mm'),('clearance','clearance_mm'),('via_diameter','via_diameter_mm'),('via_drill','via_drill_mm')):c[target]=spec[key]
    settings['classes']=sorted(by_name.values(),key=lambda c:(c['name']!='Default',c['name']))
    chosen={c['name'] for c in routing['net_classes']}
    patterns=[p for p in settings.get('netclass_patterns',[]) if p.get('netclass') not in chosen]
    for spec in routing['net_classes']:
        if spec['name']!='Default':patterns.extend({'netclass':spec['name'],'pattern':n} for n in spec['nets'])
    settings['netclass_patterns']=patterns
    output=json.dumps(data,indent=2,sort_keys=True)+'\n'
    if project.read_text()!=output:project.write_text(output)

def memory_mb(raw):
    match=SIZE_RE.search(raw)
    if not match:return 0.0
    amount=float(match[1]);unit=match[2]
    return amount*{'B':1/1048576,'KiB':1/1024,'MiB':1,'GiB':1024,'TiB':1048576}[unit]

def router(dsn,ses,work,threads,heap_mb,timeout_sec,image,fanout=True,ignored_classes=()):
    name=f'osc-route-{os.getpid()}'
    command=['docker','run','--rm','--name',name,'--network','none','--hostname','router','--cpus',str(threads),'--memory',f'{max(heap_mb+512,1024)}m','--user',f'{os.getuid()}:{os.getgid()}','-e','HOME=/tmp','-v',f'{work.resolve()}:/work','-w','/work','--entrypoint','java',image,f'-Xmx{heap_mb}m','-jar','/app/freerouting-executable.jar','--gui.enabled=false','--api_server.enabled=false','--user_data_path=/tmp','-de','/work/'+dsn.name,'-do','/work/'+ses.name,'-mt',str(threads),'-mp','20','--router.optimizer.enabled=false']
    if not fanout:command.append('--router.fanout.enabled=false')
    if ignored_classes:command.extend(('-inc',','.join(ignored_classes)))
    started=time.monotonic();peak=0.0;timed_out=False;log_path=work/'freerouting-live.log'
    with log_path.open('w') as output:
        proc=subprocess.Popen(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT)
        try:
            while proc.poll() is None:
                if time.monotonic()-started>=timeout_sec:
                    subprocess.run(['docker','kill',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    try:proc.wait(timeout=10)
                    except subprocess.TimeoutExpired:proc.kill();proc.wait()
                    timed_out=True;break
                try:
                    sample=subprocess.run(['docker','stats','--no-stream','--format','{{.MemUsage}}',name],text=True,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=3)
                    peak=max(peak,memory_mb(sample.stdout))
                except subprocess.TimeoutExpired:pass
                time.sleep(.25)
        finally:
            if proc.poll() is None:proc.kill();proc.wait()
    return (124 if timed_out else proc.returncode),time.monotonic()-started,peak,log_path.read_text()

def attach_native_ratsnest(board,report,result):
    native=report.parent/'ratsnest.json'
    sample=result.get('drc_unrouted_net_name_sample',result.get('unrouted_net_names',[]))
    # Match DRC's fail-closed receipt policy: never reuse a previous native result.
    for key in ('native_ratsnest_error','native_unconnected_edge_count','native_board_sha256',
                'native_ratsnest_report','multi_pad_candidate_net_count','native_gate_status',
                'drc_unrouted_name_sample_count','drc_unrouted_name_sample_truncated',
                'native_open_edges_by_net','unrouted_net_names','unrouted_net_count',
                'unrouted_name_basis','drc_unrouted_net_name_sample'):
        result.pop(key,None)
    result['drc_unrouted_net_name_sample']=sample
    native.unlink(missing_ok=True)
    board_hash=hashlib.sha256(board.read_bytes()).hexdigest()
    run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/ratsnest.py',repo_relative(board),repo_relative(native)])
    detail=json.loads(native.read_text())
    if not isinstance(detail,dict):raise ValueError('native ratsnest report must be an object')
    for key in ('native_unconnected_edges','multi_pad_candidate_net_count'):
        if type(detail.get(key)) is not int or detail[key]<0:
            raise ValueError(f'invalid native ratsnest count: {key}')
    source=detail.get('board')
    if not isinstance(source,str) or (ROOT/Path(source)).resolve()!=board.resolve():
        raise ValueError('native ratsnest report describes a different board')
    if hashlib.sha256(board.read_bytes()).hexdigest()!=board_hash:
        raise RuntimeError('board changed while collecting native ratsnest')
    if detail.get('board_sha256')!=board_hash:
        raise ValueError('native ratsnest board hash differs from inspected board')
    edges=detail.get('native_open_edges_by_net')
    if (not isinstance(edges,dict) or any(not isinstance(name,str) or not name or
            type(count) is not int or count<=0 for name,count in edges.items())):
        raise ValueError('invalid native per-net edge counts')
    for key,expected in (('native_open_net_count',len(edges)),
                         ('named_edge_count_sum',sum(edges.values()))):
        if type(detail.get(key)) is not int or detail[key]!=expected:
            raise ValueError('inconsistent native per-net count: '+key)
    if sum(edges.values())!=detail['native_unconnected_edges']:
        raise ValueError('native per-net edges do not sum to total')
    if not isinstance(detail.get('named_edge_basis'),str) or not detail['named_edge_basis']:
        raise ValueError('native per-net edge basis missing')
    result['native_board_sha256']=board_hash
    result['native_unconnected_edge_count']=detail['native_unconnected_edges']
    result['native_ratsnest_report']=repo_relative(native)
    result['multi_pad_candidate_net_count']=detail['multi_pad_candidate_net_count']
    result['drc_unrouted_name_sample_count']=len(sample)
    phase=result.get('after') or result.get('prepared') or result.get('before') or {}
    result['drc_unrouted_name_sample_truncated']=detail['native_unconnected_edges']>phase.get('unconnected_items',0)
    result['unrouted_net_names']=sorted(detail['native_open_edges_by_net'])
    result['unrouted_net_count']=detail['native_open_net_count']
    result['native_open_edges_by_net']=detail['native_open_edges_by_net']
    result['unrouted_name_basis']=detail['named_edge_basis']

SUCCESS_STATUSES={'ROUTED DRAFT','UPDATED DRAFT','UNCHANGED DRAFT'}

def finalize_native_gate(board,report,result,exit_code):
    """Native connectivity is a mandatory gate, never a best-effort statistic.

    Preserve prior failures (including timeout exit 3); a native result cannot
    promote a failed route. A ratsnest-only refresh does not recheck DRC/parity.
    """
    try:
        attach_native_ratsnest(board,report,result)
    except Exception as exc:
        result['native_ratsnest_error']=str(exc)
        result['native_gate_status']='NOT RUN'
        if exit_code==0 or result.get('status') in SUCCESS_STATUSES:
            result['status']='PIPELINE FAILED DRAFT'
            return 2
        return exit_code
    if result['native_unconnected_edge_count']:
        result['native_gate_status']='OPEN EDGES'
        if exit_code==0 or result.get('status') in SUCCESS_STATUSES:
            result['status']='INCOMPLETE DRAFT'
            return 2
    else:
        result['native_gate_status']='ZERO OPEN EDGES'
    return exit_code

def main():
    parser=argparse.ArgumentParser();parser.add_argument('board_id');parser.add_argument('--board',type=Path);parser.add_argument('--report',type=Path);parser.add_argument('--timeout-sec',type=int);parser.add_argument('--threads',type=int);parser.add_argument('--heap-mb',type=int);parser.add_argument('--no-fanout',action='store_true');parser.add_argument('--refresh-ratsnest-only',action='store_true')
    args=parser.parse_args()
    definition=load_definition(ROOT/'design/boards'/f'{args.board_id}.json')
    if not definition.routing:raise ValueError(f'{args.board_id}: routing definition missing')
    board=(args.board or ROOT/'boards'/args.board_id/f'{args.board_id}.kicad_pcb').resolve()
    board.relative_to(ROOT)
    if not board.exists():raise FileNotFoundError(board)
    report=(args.report or board.parent/'reports/routing.json').resolve();report.relative_to(ROOT);report.parent.mkdir(parents=True,exist_ok=True)
    if args.refresh_ratsnest_only:
        if not report.exists():raise FileNotFoundError(report)
        result=json.loads(report.read_text())
        # Do not attach fresh counts to an old successful routing badge.
        if result.get('status')!='RATSNEST ONLY DRAFT':
            result['prior_routing_status']=result.get('status','UNKNOWN')
        result['status']='RATSNEST ONLY DRAFT'
        result['routing_gate_scope']='Ratsnest refresh only; DRC and parity NOT RUN'
        exit_code=finalize_native_gate(board,report,result,0)
        report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        return exit_code
    work=board.parent/'routing-work';work.mkdir(exist_ok=True)
    image,env_heap,env_timeout=read_env()
    threads=args.threads or max(1,min((os.cpu_count() or 2)//2,6))
    heap=args.heap_mb or env_heap;timeout=args.timeout_sec or env_timeout
    if threads<1 or threads>max(1,(os.cpu_count() or 1)//2) or heap<256 or heap>4096 or timeout<1:raise ValueError('invalid resource bounds')
    routing_hash=hashlib.sha256(json.dumps({'routing':definition.routing,'outline':definition.outline,'layers':definition.layers},sort_keys=True,separators=(',',':')).encode()).hexdigest()
    previous=json.loads(report.read_text()) if report.exists() else {}
    started=time.monotonic()
    result={'routing_spec_sha256':routing_hash,'schema_version':1,'board_id':args.board_id,'status':'NOT RUN','draft':True,'router_image':image,'thread_limit':threads,'heap_mb':heap,'fanout_enabled':not args.no_fanout,'time_limit_sec':timeout,'board':repo_relative(board),'routed_net_count':0,'unrouted_net_count':0,'unrouted_net_names':[],'via_count':0,'total_track_length_mm':0.0,'runtime_sec':0.0,'sampled_peak_memory_mb':0.0,'preexisting_tracks_preserved':0,'preexisting_zones_preserved':0}
    exit_code=1
    try:
        pre=drc(board,work/'pre-drc.json');result['before']=drc_summary(pre)
        complete=not result['before']['unrouted_nets'] and result['before']['unconnected_items']==0
        if complete and previous.get('routing_spec_sha256')!=routing_hash:
            project_settings(board,definition.routing)
            dsn=work/'input.dsn'
            run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','prepare',args.board_id,'--board',repo_relative(board),'--dsn',repo_relative(dsn)])
            after=drc(board,work/'post-drc.json');result['after']=drc_summary(after)
            stats_path=work/'stats.json'
            run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','inspect',args.board_id,'--board',repo_relative(board),'--stats',repo_relative(stats_path)])
            stats=json.loads(stats_path.read_text())
            result['via_count']=stats['via_count'];result['via_nets']=stats['via_nets'];result['total_track_length_mm']=stats['total_track_length_mm']
            result['preexisting_tracks_preserved']=len(stats['track_uuids']);result['preexisting_zones_preserved']=stats['zone_count']
            result['status']='UPDATED DRAFT' if drc_passes(result['after']) else 'INCOMPLETE DRAFT'
            exit_code=0 if result['status']=='UPDATED DRAFT' else 2
        elif complete:
            stats_path=work/'stats.json'
            run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','inspect',args.board_id,'--board',repo_relative(board),'--stats',repo_relative(stats_path)])
            stats=json.loads(stats_path.read_text())
            result['via_count']=stats['via_count'];result['via_nets']=stats['via_nets'];result['total_track_length_mm']=stats['total_track_length_mm']
            result['preexisting_tracks_preserved']=len(stats['track_uuids'])
            result['preexisting_zones_preserved']=stats['zone_count']
            result['after']=result['before']
            result['status']='UNCHANGED DRAFT' if drc_passes(result['after']) else 'INCOMPLETE DRAFT'
            exit_code=0 if drc_passes(result['after']) else 2
        else:
            project_settings(board,definition.routing)
            dsn=work/'input.dsn';ses=work/'output.ses';ses.unlink(missing_ok=True)
            run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','prepare',args.board_id,'--board',repo_relative(board),'--dsn',repo_relative(dsn)])
            prepared=drc(board,work/'prepared-drc.json')
            result['prepared']=drc_summary(prepared)
            if result['prepared']['rule_errors'] or result['prepared']['schematic_parity_issues']:
                result['router_skipped']='Prepared DRC has rule or schematic-parity errors'
                raise RuntimeError(result['router_skipped'])
            if drc_passes(result['prepared']):
                stats_path=work/'stats.json'
                run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','inspect',args.board_id,'--board',repo_relative(board),'--stats',repo_relative(stats_path)])
                stats=json.loads(stats_path.read_text())
                result.update({k:stats[k] for k in ('via_count','via_nets','total_track_length_mm')})
                result['preexisting_tracks_preserved']=len(stats['track_uuids'])
                result['preexisting_zones_preserved']=stats['zone_count']
                result['after']=result['prepared']
                result['routed_net_count']=len(result['before']['unrouted_nets'])
                result['status']='ROUTED DRAFT'
                result['router_skipped']='Prepared copper and refilled zones satisfy the complete gate'
                exit_code=0
            else:
                code,seconds,peak,log=router(dsn,ses,work,threads,heap,timeout,image,not args.no_fanout)
                (work/'freerouting.log').write_text(log)
                result['router_runtime_sec']=round(seconds,3);result['sampled_peak_memory_mb']=round(peak,2)
                if code==124:
                    matched=sorted(set(re.findall(r"Net '([^']+)' \(\d+ unrouted connection",log)))
                    result['unrouted_net_names']=matched or result['before']['unrouted_nets']
                    result['unrouted_name_basis']='router final log' if matched else 'pre-route DRC snapshot; no imported session'
                    result['unrouted_net_count']=len(result['unrouted_net_names'])
                    result['routed_net_count']=None
                    result['status']='TIMEOUT DRAFT';exit_code=3
                elif code or not ses.exists():
                    result['status']='ROUTER FAILED DRAFT';result['router_exit_code']=code
                    result['unrouted_net_names']=result['before']['unrouted_nets'];result['unrouted_net_count']=len(result['unrouted_net_names'])
                    result['unrouted_name_basis']='pre-route DRC snapshot; no imported session'
                    result['routed_net_count']=None;exit_code=2
                else:
                    stats_path=work/'stats.json'
                    run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','finish',args.board_id,'--board',repo_relative(board),'--ses',repo_relative(ses),'--stats',repo_relative(stats_path)])
                    stats=json.loads(stats_path.read_text())
                    result.update({k:stats[k] for k in ('via_count','via_nets','total_track_length_mm','preexisting_tracks_preserved','preexisting_zones_preserved')})
                    after=drc(board,work/'post-drc.json');result['after']=drc_summary(after)
                    before_names=set(result['before']['unrouted_nets']);after_names=set(result['after']['unrouted_nets'])
                    result['routed_net_count']=len(before_names-after_names)
                    result['unrouted_net_count']=len(after_names);result['unrouted_net_names']=sorted(after_names)
                    result['status']='ROUTED DRAFT' if drc_passes(result['after']) else 'INCOMPLETE DRAFT'
                    exit_code=0 if result['status']=='ROUTED DRAFT' else 2
    except Exception as exc:
        result['status']='PIPELINE FAILED DRAFT';result['error']=str(exc);exit_code=2
    finally:
        if result['status'] in ('TIMEOUT DRAFT','ROUTER FAILED DRAFT','PIPELINE FAILED DRAFT'):
            try:
                stats_path=work/'failure-stats.json'
                run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','inspect',args.board_id,'--board',repo_relative(board),'--stats',repo_relative(stats_path)])
                stats=json.loads(stats_path.read_text())
                result['via_count']=stats['via_count'];result['via_nets']=stats['via_nets'];result['total_track_length_mm']=stats['total_track_length_mm']
                result['preexisting_tracks_preserved']=len(stats['track_uuids']);result['preexisting_zones_preserved']=stats['zone_count']
            except Exception as metrics_error:
                result['metrics_error']=str(metrics_error)
        result['runtime_sec']=round(time.monotonic()-started,3)
        exit_code=finalize_native_gate(board,report,result,exit_code)
        report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(f"{args.board_id}: {result['status']}; report {repo_relative(report)}")
        if result.get('error'):print(result['error'],file=sys.stderr)
    return exit_code
if __name__=='__main__':raise SystemExit(main())
