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
    result=run(command,check=False)
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

def router(dsn,ses,work,threads,heap_mb,timeout_sec,image,fanout=True):
    name=f'osc-route-{os.getpid()}'
    command=['docker','run','--rm','--name',name,'--network','none','--hostname','router','--cpus',str(threads),'--memory',f'{max(heap_mb+512,1024)}m','--user',f'{os.getuid()}:{os.getgid()}','-e','HOME=/tmp','-v',f'{work.resolve()}:/work','-w','/work','--entrypoint','java',image,f'-Xmx{heap_mb}m','-jar','/app/freerouting-executable.jar','--gui.enabled=false','--api_server.enabled=false','--user_data_path=/tmp','-de','/work/'+dsn.name,'-do','/work/'+ses.name,'-mt',str(threads),'-mp','20','--router.optimizer.enabled=false']
    if not fanout:command.append('--router.fanout.enabled=false')
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

def main():
    parser=argparse.ArgumentParser();parser.add_argument('board_id');parser.add_argument('--board',type=Path);parser.add_argument('--report',type=Path);parser.add_argument('--timeout-sec',type=int);parser.add_argument('--threads',type=int);parser.add_argument('--heap-mb',type=int);parser.add_argument('--no-fanout',action='store_true')
    args=parser.parse_args()
    definition=load_definition(ROOT/'design/boards'/f'{args.board_id}.json')
    if not definition.routing:raise ValueError(f'{args.board_id}: routing definition missing')
    board=(args.board or ROOT/'boards'/args.board_id/f'{args.board_id}.kicad_pcb').resolve()
    board.relative_to(ROOT)
    if not board.exists():raise FileNotFoundError(board)
    report=(args.report or board.parent/'reports/routing.json').resolve();report.relative_to(ROOT);report.parent.mkdir(parents=True,exist_ok=True)
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
            result['status']='UPDATED DRAFT' if not (result['after']['rule_errors'] or result['after']['unconnected_items'] or result['after']['schematic_parity_issues']) else 'INCOMPLETE DRAFT'
            exit_code=0 if result['status']=='UPDATED DRAFT' else 2
        elif complete:
            stats_path=work/'stats.json'
            run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','inspect',args.board_id,'--board',repo_relative(board),'--stats',repo_relative(stats_path)])
            stats=json.loads(stats_path.read_text())
            result['via_count']=stats['via_count'];result['via_nets']=stats['via_nets'];result['total_track_length_mm']=stats['total_track_length_mm']
            result['preexisting_tracks_preserved']=len(stats['track_uuids'])
            result['preexisting_zones_preserved']=stats['zone_count']
            result['status']='UNCHANGED DRAFT';result['after']=result['before'];exit_code=0
        else:
            project_settings(board,definition.routing)
            dsn=work/'input.dsn';ses=work/'output.ses';ses.unlink(missing_ok=True)
            run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/route_kicad.py','prepare',args.board_id,'--board',repo_relative(board),'--dsn',repo_relative(dsn)])
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
                result['status']='ROUTED DRAFT' if not (result['after']['rule_errors'] or result['after']['unconnected_items'] or result['after']['schematic_parity_issues']) else 'INCOMPLETE DRAFT'
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
        report.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        print(f"{args.board_id}: {result['status']}; report {repo_relative(report)}")
        if result.get('error'):print(result['error'],file=sys.stderr)
    return exit_code
if __name__=='__main__':raise SystemExit(main())
