#!/usr/bin/env python3
"""Bounded old/new native benchmark for #189; never promotes canonical boards.

Both variants start from the same settled, independently rechecked board bytes.
Artifacts retain context, proposals, identities, logs, timings and negative results.
"""
from __future__ import annotations
import argparse,collections,hashlib,importlib.util,json,resource,shutil,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen import route_jack_grid as driver
from scripts.pcbgen import grid_router


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def endpoints(dump):
    """Pad-component membership, including nets absent from the open-island table."""
    pads={p['uuid']:p for p in dump['pads'] if p['net']}
    by_net=collections.defaultdict(list)
    for uid,p in pads.items():by_net[p['net']].append(uid)
    return {n:[sorted(u for u in g if u in pads) for g in dump['islands'].get(n,[ids])]
            for n,ids in sorted(by_net.items())}


def splits(before,after):
    old,new=endpoints(before),endpoints(after);bad=[]
    for net,groups in old.items():
        labels={u:i for i,g in enumerate(new.get(net,[])) for u in g}
        for g in groups:
            if any(u not in labels for u in g) or len({labels[u] for u in g if u in labels})>1:
                bad.append({'net':net,'previously_connected_pads':g})
    return bad


def warning_ids(drc):
    return sorted((v['type'],tuple(sorted(i.get('uuid','') for i in v.get('items',[]))))
                  for v in drc['violations'] if v['severity']=='warning')


def select(dump,count):
    ordered=driver.signal_chunk(dump,None)
    # Include stranded neighbours and long header-to-IC obligations, then fill in
    # stable order. UUID/ref/pad/net identities are saved, never list indices.
    selected=list(dict.fromkeys(ordered[:3]+ordered[-3:]+sorted(ordered,key=lambda n:(-len(dump['islands'][n]),n))[:2]+ordered))[:count]
    pads={p['uuid']:p for p in dump['pads']}
    return [{'net':n,'islands':[[{k:pads[u][k] for k in ('uuid','ref','pad','xy','layers')}
                    for u in g if u in pads] for g in dump['islands'][n]]} for n in selected]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('board',choices=['osc-jack-left','osc-jack-right','osc-core'])
    p.add_argument('--old-ref',default='1fe06ad50248d6434876fbf2bd6e32e1bfbb13bb');p.add_argument('--count',type=int,default=10)
    a=p.parse_args();out=ROOT/'.circuit-cache'/f'issue189-{a.board}';out.mkdir(exist_ok=True)
    report={'schema':'obstacle-benchmark-1','board':a.board,'old_ref':a.old_ref,
            'new_ref':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            'budget':{'connections':a.count,'rrr_rounds':1,'max_victims':4,'max_expansions':100000,'res_mm':.1,
                      'minimum_useful_progress':'at least one native open edge closed without any pad-component split or warning regression'},
            'variants':{},'status':'RUNNING'}
    def save(): (out/'result.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    save();t=time.monotonic()
    try:
        work=driver.workspace(a.board,'189-frozen');board=work/f'{a.board}.kicad_pcb'
        source=ROOT/'boards'/a.board/board.name;shutil.copyfile(source,board)
        report['input_hashes']={str(f.relative_to(ROOT)):sha(f) for f in sorted(source.parent.rglob('*'))
            if f.is_file() and (f.suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru','.kicad_sch') or f.name in ('fp-lib-table','sym-lib-table'))}
        report['router_hashes']={n:sha(ROOT/'scripts/pcbgen'/n) for n in ('grid_router.py','grid_astar.c','route_jack_grid.py')}
        report['kicad_version']=driver.run('bash','scripts/kicad/run.sh','kicad-cli','version').strip()
        drc,before=driver.check(board)
        verify=driver.workspace(a.board,'189-frozen-verify')/board.name;shutil.copyfile(board,verify)
        drc2,before2=driver.check(verify)
        if endpoints(before)!=endpoints(before2) or before['open_edges']!=before2['open_edges']:
            raise RuntimeError('independent baseline differs after settled refill')
        if any(v['severity']=='error' for v in drc2['violations']) or drc2['schematic_parity']:
            raise RuntimeError('baseline native DRC/parity errors')
        board,before,drc=verify,before2,drc2
        report['baseline_seconds']=time.monotonic()-t
        report['saved_input_sha256']=sha(board);report['open_edges_before']=before['open_edges']
        report['baseline_warnings']=warning_ids(drc);report['selected']=select(before,a.count)
        report['before_components']=endpoints(before)
        shutil.copytree(board.parent,out/'input',dirs_exist_ok=True)
        old_path=ROOT/'.circuit-cache'/'old-grid'/'grid_router.py';old_path.parent.mkdir(exist_ok=True)
        old_path.write_bytes(subprocess.check_output(['git','show',f'{a.old_ref}:scripts/pcbgen/grid_router.py']))
        spec=importlib.util.spec_from_file_location('issue189_old_grid',old_path);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        report['old_router_sha256']=sha(old_path);save()
        for label,router in [('old',old.route),('new',grid_router.route)]:
            events=[];routing_seconds=0;logs=[];start=time.monotonic()
            def timed(*args,**kw):
                nonlocal routing_seconds
                if label=='new':kw['diagnostics']=events
                began=time.monotonic()
                try:return router(*args,**kw)
                finally:routing_seconds+=time.monotonic()-began
            driver.route=timed
            stage=dict(name=f'189-{label}',nets=[x['net'] for x in report['selected']],rrr_rounds=1,
                clearance=.2,signal_width=.2,signal_via_diameter=.6,res=.1,max_expansions=100000,
                grow={n:.05 for n in [*driver.RAILS,'AGND']})
            candidate,receipt=driver.run_stage(a.board,board,stage,json.loads((ROOT/'design/boards'/f'{a.board}.json').read_text()),
                                             lambda line:(logs.append(line),print(line,flush=True)))
            result={'receipt':receipt,'diagnostics':events,'routing_seconds':routing_seconds,'elapsed_seconds':time.monotonic()-start,
                    'native_status':'REJECTED' if candidate is None else 'CHECKED','candidate_sha256':sha(candidate) if candidate else None}
            if candidate:
                after=json.loads(candidate.with_name('dump.json').read_text());after_drc=json.loads(candidate.with_name('drc.json').read_text())
                result['after_components']=endpoints(after);result['splits']=splits(before,after)
                result['new_warning_identities']=[w for w in warning_ids(after_drc) if w not in warning_ids(drc)]
                result['native_gain']=before['open_edges']-after['open_edges']
                result['eligible_for_promotion']=result['native_gain']>0 and not result['splits'] and not result['new_warning_identities']
                original={i['uuid']:i for k in ('tracks','vias') for i in before[k]};remaining={i['uuid']:i for k in ('tracks','vias') for i in after[k]}
                result['retained_copper']={'before':len(original),'after':len(remaining),'identical':sum(remaining.get(u)==i for u,i in original.items()),
                    'removed_uuids':sorted(set(original)-set(remaining)),'added_uuids':sorted(set(remaining)-set(original)),
                    'changed_existing_uuids':sorted(u for u in set(original)&set(remaining) if original[u]!=remaining[u])}
                shutil.copytree(candidate.parent,out/label/'native',dirs_exist_ok=True)
            else:result['eligible_for_promotion']=False
            result['accepted_progress_per_hour']=(result.get('native_gain',0)*3600/result['elapsed_seconds']) if result['eligible_for_promotion'] else 0
            report['variants'][label]=result
            (out/label).mkdir(exist_ok=True);(out/label/'route.log').write_text('\n'.join(logs)+'\n')
            for suffix in ('', '-verify'):
                folder=ROOT/'.circuit-cache'/f'{a.board}-grid-189-{label}{suffix}'
                if folder.exists():shutil.copytree(folder,out/label/('proposal' if not suffix else 'verify'),dirs_exist_ok=True)
            save()
        report['status']='COMPLETE'
    except Exception as error:
        report.update(status='ERROR',error=repr(error));raise
    finally:
        report['elapsed_seconds']=time.monotonic()-t;report['peak_host_rss_kb']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;save()

if __name__=='__main__':main()
