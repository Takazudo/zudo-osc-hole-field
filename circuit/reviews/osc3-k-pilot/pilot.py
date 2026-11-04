#!/usr/bin/env python3
"""OSC3: the sequenced K power/return pilot (OSC2 H1 -> H2 -> H3) with one complete-warning audit at the end.

Uses the OSC2 hypothesis specs from circuit/reviews/osc2-k-power-return/trial.py and the
shared driver scripts/pcbgen/route_jack_grid.py unchanged (run_stage, stitched,
promotion_gate, complete_gate, enforce_warning_completeness). Each step runs on the
previous step's checked candidate and must pass the raw gate against its own input;
a failing step is skipped so earlier gains are kept. The final candidate is gated once
against the adopted K board with complete native warning evidence, and only then
copied over boards/osc-core/osc-core.kicad_pcb (--promote). Draft only: electrical,
thermal and physical qualification remain NOT RUN; no fabrication output is created.
"""
from __future__ import annotations
import argparse,datetime,hashlib,importlib.util,json,shutil,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
import scripts.pcbgen.route_jack_grid as driver
from scripts.pcbgen.route_shards import delta

HERE=Path(__file__).resolve().parent
BOARD_ID='osc-core'
K3409_SHA='dda33a25479c9993f71e33d49129cf16414828b3dd2083b6d4f91a65421c728c'
spec_=importlib.util.spec_from_file_location('osc2_trial',ROOT/'circuit/reviews/osc2-k-power-return/trial.py')
osc2=importlib.util.module_from_spec(spec_);spec_.loader.exec_module(osc2)
SEQUENCE=['h1-plane-escapes','h2-5v-trunks','h3-escapes-split-repair']


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p,n):return json.loads(Path(p).with_name(n).read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('--promote',action='store_true')
    p.add_argument('--resume-gate',action='store_true',help='skip routing: gate the retained final candidate of the previous receipt (hashes must match)')
    a=p.parse_args();log=lambda m:print(m,flush=True)
    board=ROOT/'boards'/BOARD_ID/f'{BOARD_ID}.kicad_pcb'
    if sha(board)!=K3409_SHA:raise RuntimeError('adopted K board is not K3409')
    definition=json.loads((ROOT/'design/boards'/f'{BOARD_ID}.json').read_text())
    t0=time.time();steps=[]
    if a.resume_gate:
        # An earlier run's settled start copy and checked final candidate, bound by their recorded hashes.
        prev=json.loads((HERE/'osc3-k-pilot.json').read_text());steps=prev['steps']
        start=ROOT/'.circuit-cache'/f'{BOARD_ID}-grid-osc3-pilot-start'/board.name
        kept=[s for s in steps if s.get('raw_gate_adopted')]
        current=ROOT/'.circuit-cache'/f"{BOARD_ID}-grid-osc3-pilot-{kept[-1]['step']}-verify"/board.name
        if sha(start)!=K3409_SHA or sha(current)!=kept[-1]['candidate_sha256']:raise RuntimeError('retained pilot workspaces do not match the receipt')
        dump0=load(start,'dump.json')
    else:
        work=driver.workspace(BOARD_ID,'osc3-pilot-start');start=work/board.name;shutil.copyfile(board,start)
        drc0,dump0=driver.check(start)
        if any(v['severity']=='error' for v in drc0['violations']) or drc0['schematic_parity']:raise RuntimeError('start board not clean')
        current=start
    for key in ([] if a.resume_gate else SEQUENCE):
        spec={**osc2.HYPOTHESES[key]['spec'],'name':'osc3-pilot-'+key}
        before=load(current,'dump.json');before_drc=load(current,'drc.json')
        candidate,receipt=driver.run_stage(BOARD_ID,current,spec,definition,log)
        if candidate is None:steps.append({'step':key,'result':'nothing to do' if not receipt else receipt});continue
        if receipt['open_edges_after']>=receipt['open_edges_before'] or driver.split_pad_groups(before,load(candidate,'dump.json')):
            candidate,receipt=driver.stitched(BOARD_ID,current,candidate,receipt,spec,definition,log)
        gate=driver.promotion_gate(before,load(candidate,'dump.json'),before_drc,load(candidate,'drc.json'))
        kept=bool(gate['adopted'])
        steps.append({'step':key,'spec':spec,'open_edges_before':receipt['open_edges_before'],'open_edges_after':receipt['open_edges_after'],
                      'links_added':receipt.get('links_added'),'links_dropped_for_agnd_split':receipt.get('links_dropped_for_agnd_split'),
                      'raw_gate_adopted':kept,'split_pad_groups':len(gate['split_pad_groups']),'new_warning_identities':gate['new_warning_identities'],
                      'input_sha256':sha(current),'candidate_sha256':sha(candidate)})
        log(f"{key}: {receipt['open_edges_before']} -> {receipt['open_edges_after']} raw gate {'pass' if kept else 'FAIL'}")
        if kept:current=candidate
    out={'schema':'osc3-k-pilot-1','resumed_gate':a.resume_gate,'status':'NATIVE CHECKED DRAFT STAGE','qualification':'NOT RUN: electrical, thermal and physical qualification',
         'fabrication_outputs':'NOT CREATED','input_board_sha256':K3409_SHA,'sequence':SEQUENCE,'steps':steps,
         'tool':{'kicad_cli_version':driver.run('bash','scripts/kicad/run.sh','kicad-cli','version').strip(),'wrapper':'scripts/kicad/run.sh'},
         'started_utc':datetime.datetime.fromtimestamp(t0,datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),'adopted':False,'promoted':False}
    if current is start:
        out['rejection_reason']='no step passed its raw gate'
    else:
        final_spec={'name':'osc3-k-pilot'}
        receipt={'stage':'osc3-k-pilot','open_edges_before':dump0['open_edges'],'open_edges_after':load(current,'dump.json')['open_edges']}
        receipt=driver.complete_gate(BOARD_ID,start,current,receipt,final_spec)
        receipt['input_board_sha256']=sha(start);receipt['candidate_board_sha256']=sha(current)
        receipt=driver.enforce_warning_completeness(receipt,load(start,'drc.json'),load(current,'drc.json'),receipt['input_board_sha256'],receipt['candidate_board_sha256'])
        receipt['split_pad_groups']=[{'net':s['net'],'pads':len(s['previously_connected_pads'])} for s in receipt['split_pad_groups']]
        receipt.pop('raw_promotion_gate',None)
        after=load(current,'dump.json')
        out.update(final_gate=receipt,adopted=bool(receipt['adopted']),before=osc2.rail_summary(dump0),after=osc2.rail_summary(after),
                   precision_returns=osc2.precision_returns(dump0,after))
        if receipt['adopted']:
            replay=delta(board.read_text(),current.read_text())
            rp=HERE/'osc3-k-pilot-copper.json';rp.write_text(json.dumps(replay,sort_keys=True)+'\n')
            out['copper_replay']={'path':str(rp.relative_to(ROOT)),'sha256':sha(rp),'base_sha256':replay['base_sha256']}
            if a.promote:shutil.copyfile(current,board);out['promoted']=True;log('promoted '+str(board.relative_to(ROOT)))
    out['wall_seconds']=round(time.time()-t0)
    (HERE/'osc3-k-pilot.json').write_text(json.dumps(out,indent=1,sort_keys=True)+'\n')
    log(f"osc3-k-pilot: adopted={out['adopted']} {dump0['open_edges']} -> {out.get('after',{}).get('open_edges')}")


if __name__=='__main__':main()
