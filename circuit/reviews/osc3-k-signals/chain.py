#!/usr/bin/env python3
"""OSC3: chain several route_jack_grid stages on the adopted K board and gate the result once.

The complete-warning audit on K takes most of a day, so a per-stage audit is not
practical. Each named stage of scripts/pcbgen/route_jack_grid.py (unchanged) runs on
the previous kept candidate and is kept only when its raw gate passes against its own
input; the last kept candidate is then gated once against the adopted board with
complete native warning evidence and only then copied over boards/osc-core (--promote).
Draft only: qualification NOT RUN; no fabrication output.
"""
from __future__ import annotations
import argparse,datetime,hashlib,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import scripts.pcbgen.route_jack_grid as driver
from scripts.pcbgen.route_shards import delta

HERE=Path(__file__).resolve().parent
BOARD_ID='osc-core'


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p,n):return json.loads(Path(p).with_name(n).read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('label');p.add_argument('stages',nargs='+');p.add_argument('--promote',action='store_true')
    p.add_argument('--max-minutes',type=float,help='stop starting new stages after this; the gate still runs')
    p.add_argument('--resume-from',metavar='STAGE',help='continue after an interrupted chain from STAGE\'s fresh-copy verified candidate (re-gated raw against the start)')
    a=p.parse_args();log=lambda m:print(m,flush=True)
    names={s['name']:s for s in driver.STAGES}
    specs=[names[n] for n in a.stages]
    board=ROOT/'boards'/BOARD_ID/f'{BOARD_ID}.kicad_pcb';base_sha=sha(board)
    definition=json.loads((ROOT/'design/boards'/f'{BOARD_ID}.json').read_text())
    t0=time.time();deadline=t0+a.max_minutes*60 if a.max_minutes else None;steps=[]
    if a.resume_from:
        # The interrupted run's settled start copy must still hold the adopted bytes.
        start=ROOT/'.circuit-cache'/f'{BOARD_ID}-grid-osc3-{a.label}-start'/board.name
        if sha(start)!=base_sha:raise RuntimeError('retained start copy is not the adopted board')
        dump0=load(start,'dump.json')
        current=ROOT/'.circuit-cache'/f'{BOARD_ID}-grid-{a.resume_from}-verify'/board.name
        gate=driver.promotion_gate(dump0,load(current,'dump.json'),load(start,'drc.json'),load(current,'drc.json'))
        if not gate['adopted']:raise RuntimeError('resumed candidate fails the raw gate against the start')
        steps.append({'step':'resumed:'+','.join(a.stages[:a.stages.index(a.resume_from)+1]),'open_edges_before':dump0['open_edges'],
                      'open_edges_after':load(current,'dump.json')['open_edges'],'raw_gate_adopted':True,'input_sha256':base_sha,'candidate_sha256':sha(current)})
        specs=specs[a.stages.index(a.resume_from)+1:]
    else:
        work=driver.workspace(BOARD_ID,f'osc3-{a.label}-start');start=work/board.name;shutil.copyfile(board,start)
        drc0,dump0=driver.check(start)
        if any(v['severity']=='error' for v in drc0['violations']) or drc0['schematic_parity']:raise RuntimeError('start board not clean')
        current=start
    for spec in specs:
        if deadline and time.time()>deadline:steps.append({'step':spec['name'],'result':'not started: time budget'});continue
        before=load(current,'dump.json');before_drc=load(current,'drc.json')
        candidate,receipt=driver.run_stage(BOARD_ID,current,spec,definition,log)
        if receipt=='resume':steps.append({'step':spec['name'],'result':'time budget used inside stage'});continue
        if candidate is None:steps.append({'step':spec['name'],'result':'nothing to do' if not receipt else {k:receipt.get(k) for k in ('rejection_reason','open_edges_before','open_edges_after')}});continue
        if receipt['open_edges_after']>=receipt['open_edges_before'] or driver.split_pad_groups(before,load(candidate,'dump.json')):
            candidate,receipt=driver.stitched(BOARD_ID,current,candidate,receipt,spec,definition,log)
        gate=driver.promotion_gate(before,load(candidate,'dump.json'),before_drc,load(candidate,'drc.json'))
        kept=bool(gate['adopted'])
        steps.append({'step':spec['name'],'open_edges_before':receipt['open_edges_before'],'open_edges_after':receipt['open_edges_after'],
                      'links_added':receipt.get('links_added'),'ripped':receipt.get('ripped'),'links_dropped_for_agnd_split':receipt.get('links_dropped_for_agnd_split'),
                      'raw_gate_adopted':kept,'split_pad_groups':len(gate['split_pad_groups']),'new_warning_identities':gate['new_warning_identities'],
                      'input_sha256':sha(current),'candidate_sha256':sha(candidate)})
        log(f"{spec['name']}: {receipt['open_edges_before']} -> {receipt['open_edges_after']} raw gate {'pass' if kept else 'FAIL'}")
        if kept:current=candidate
        (HERE/f'{a.label}-progress.json').write_text(json.dumps({'steps':steps,'current':str(current.relative_to(ROOT))},indent=1)+'\n')
    out={'schema':'osc3-k-chain-1','label':a.label,'status':'NATIVE CHECKED DRAFT STAGE','qualification':'NOT RUN: electrical, thermal and physical qualification',
         'fabrication_outputs':'NOT CREATED','input_board_sha256':base_sha,'stages':a.stages,'steps':steps,
         'tool':{'kicad_cli_version':driver.run('bash','scripts/kicad/run.sh','kicad-cli','version').strip(),'wrapper':'scripts/kicad/run.sh'},
         'started_utc':datetime.datetime.fromtimestamp(t0,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'adopted':False,'promoted':False}
    if current is start:out['rejection_reason']='no step passed its raw gate'
    else:
        receipt={'stage':f'osc3-{a.label}','open_edges_before':dump0['open_edges'],'open_edges_after':load(current,'dump.json')['open_edges']}
        receipt=driver.complete_gate(BOARD_ID,start,current,receipt,{'name':f'osc3-{a.label}'})
        receipt['input_board_sha256']=sha(start);receipt['candidate_board_sha256']=sha(current)
        receipt=driver.enforce_warning_completeness(receipt,load(start,'drc.json'),load(current,'drc.json'),receipt['input_board_sha256'],receipt['candidate_board_sha256'])
        receipt['split_pad_groups']=[{'net':s['net'],'pads':len(s['previously_connected_pads'])} for s in receipt['split_pad_groups']]
        receipt.pop('raw_promotion_gate',None)
        out.update(final_gate=receipt,adopted=bool(receipt['adopted']),open_edges_before=dump0['open_edges'],open_edges_after=load(current,'dump.json')['open_edges'])
        if receipt['adopted']:
            if sha(board)!=base_sha:raise RuntimeError('adopted K board changed during the chain')
            replay=delta(board.read_text(),current.read_text())
            rp=HERE/f'{a.label}-copper.json';rp.write_text(json.dumps(replay,sort_keys=True)+'\n')
            out['copper_replay']={'path':str(rp.relative_to(ROOT)),'sha256':sha(rp),'base_sha256':replay['base_sha256']}
            if a.promote:shutil.copyfile(current,board);out['promoted']=True;log('promoted '+str(board.relative_to(ROOT)))
    out['wall_seconds']=round(time.time()-t0)
    (HERE/f'{a.label}.json').write_text(json.dumps(out,indent=1,sort_keys=True)+'\n')
    log(f"osc3-{a.label}: adopted={out['adopted']} {dump0['open_edges']} -> {out.get('open_edges_after')}")


if __name__=='__main__':main()
