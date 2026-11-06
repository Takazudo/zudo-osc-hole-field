#!/usr/bin/env python3
"""OSC4: run one planned bounded local transaction on an accepted board, never promoting it.

The plan is transactions.json in this folder (select_transactions.py). The spec
is handed unchanged to scripts/pcbgen/route_jack_grid.py run_stage() (explicit
repair mode), with that driver imported, not edited. The accepted board is copied
into a disposable .circuit-cache workspace; boards/ is never written, and the
source hash is re-checked at the end. The receipt and the copper delta are
written next to this script. --validate checks the plan against the board text
on the host without KiCad (no pcbnew, no routing). Draft only: electrical,
thermal and physical qualification remain NOT RUN; no fabrication output.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts/checks'))
RAILS=('+12V','-12V','+5V')


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(board_id):
    plan=json.loads((HERE/'transactions.json').read_text())['transactions'][board_id]
    if plan['transaction'] is None:raise SystemExit(f'{board_id}: no transaction planned')
    return plan


def validate(board_id):
    """Host-only plan check against the accepted board text; mirrors repair_selection()/repair_bounds() limits."""
    import board_text_geometry as g
    plan=load(board_id);t=plan['transaction'];spec=t['spec']
    board=g.Board(ROOT/plan['input_board'])
    errors=[]
    if board.sha256!=plan['input_board_sha256']:errors.append('board bytes differ from the plan input')
    objs={}
    for s in board.segments:objs.setdefault(s['uuid'],[]).append(s)
    for v in board.vias:objs.setdefault(v['uuid'],[]).append(v)
    x0,y0,x1,y1=spec['repair_bounds_mm']
    if not (0<x1-x0<=50 and 0<y1-y0<=50):errors.append('frame is not within 50 mm')
    cuts=spec['repair_source_uuids']
    if not 1<=len(cuts)<=12:errors.append('explicit cuts must number 1..12')
    victims=set()
    for u in cuts:
        if len(objs.get(u,[]))!=1:errors.append(f'cut {u} is not unique');continue
        o=objs[u][0];victims.add(o['net'])
        if o['net'] in (*RAILS,'AGND'):errors.append(f'cut {u} is supply/ground copper')
        pts=[o['a'],o['b']] if 'a' in o else [o['xy']];r=o.get('w',o.get('size',0))/2
        if not all(x0<=x-r and x+r<=x1 and y0<=y-r and y+r<=y1 for x,y in pts):errors.append(f'cut {u} leaves the frame')
    targets=spec['repair_targets']
    if len(victims-set(targets))>2:errors.append('more than two victim nets')
    pads={p['uuid']:(f.ref,p) for f in board.footprints.values() for p in f.pad_shapes()}
    if targets==['AGND']:
        gp=spec.get('repair_ground_pad_uuids',[])
        if not 1<=len(gp)<=4 or any(pads.get(u,(0,{'net':None}))[1]['net']!='AGND' for u in gp):errors.append('ground pads must be 1..4 AGND pads')
    elif any(n in (*RAILS,'AGND') for n in targets) or len(targets)!=1:errors.append('signal repair needs exactly one signal target')
    if not any(p['net'] in targets and x0<=p['x']<=x1 and y0<=p['y']<=y1 for _,p in pads.values()):errors.append('no target pad in the frame')
    isl,*_=g.connectivity(board,nets=set(targets))
    if all(len(isl.get(n,[]))<2 for n in targets):errors.append('target net is not open on this board')
    return {'board':board_id,'input_board_sha256':board.sha256,'spec_name':spec['name'],'cuts':len(cuts),
            'victim_nets':sorted(victims-set(targets)),'frame_mm':spec['repair_bounds_mm'],'errors':errors,
            'status':'PLAN VALID FOR NATIVE RUN' if not errors else 'PLAN INVALID'}


def run(board_id):
    import scripts.pcbgen.route_jack_grid as driver
    from scripts.pcbgen.route_shards import delta
    from scripts.pcbgen.copper_identity import retention
    plan=load(board_id);spec=plan['transaction']['spec']
    source=ROOT/plan['input_board'];source_hash=sha(source)
    if source_hash!=plan['input_board_sha256']:raise SystemExit('accepted board changed; replan before running')
    receipt={'schema':'osc4-transaction-receipt-1','status':'RUNNING','adopted':False,'board':board_id,
             'input_board_sha256':source_hash,'plan_sha256':sha(HERE/'transactions.json'),'spec':spec,
             'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    out=HERE/f'{spec["name"]}.json'
    def save():out.write_text(json.dumps(receipt,indent=1,sort_keys=True)+'\n')
    save();t0=time.time()
    try:
        base=driver.workspace(board_id,spec['name']+'-base')/source.name;shutil.copyfile(source,base)
        before_drc,before=driver.check(base)
        if any(v['severity']=='error' for v in before_drc['violations']) or before_drc['schematic_parity']:
            raise driver.StageRejected('native baseline is not clean')
        definition=json.loads((ROOT/'design/boards'/f'{board_id}.json').read_text())
        candidate,stage=driver.run_stage(board_id,base,spec,definition,print)
        receipt.update(stage=stage,open_edges_before=before['open_edges'])
        if candidate is not None and stage and not stage.get('rejected'):
            after=json.loads(candidate.with_name('dump.json').read_text())
            if after['open_edges']>=before['open_edges'] or driver.split_pad_groups(before,after):
                candidate,stage=driver.stitched(board_id,base,candidate,stage,spec,definition,print)
                after=json.loads(candidate.with_name('dump.json').read_text())
            fresh=driver.workspace(board_id,spec['name']+'-fresh')/source.name;shutil.copyfile(candidate,fresh)
            fresh_drc,verified=driver.check(fresh)
            if driver.connectivity_signature(after)!=driver.connectivity_signature(verified):
                raise driver.StageRejected('fresh-copy connectivity differs from the candidate')
            gate=driver.promotion_gate(before,verified,before_drc,fresh_drc)
            replay=delta(source.read_text(),fresh.read_text())
            (HERE/f'{spec["name"]}-copper.json').write_text(json.dumps(replay,sort_keys=True)+'\n')
            receipt.update(raw_gate=gate,open_edges_after=verified['open_edges'],
                           open_by_net_after={n:len(g)-1 for n,g in verified['islands'].items()},
                           retained_copper=retention(before,verified),candidate_sha256=sha(fresh),
                           complete_native_warning_evidence='NOT RUN: raw gate only; adoption needs the complete-warning audit',
                           status='NATIVE CHECKED DISPOSABLE TRANSACTION; NOT PROMOTED')
        else:receipt['status']='REJECTED OR NOTHING TO DO; NOT ADOPTED'
    except Exception as error:
        receipt.update(status='ERROR; NOT ADOPTED',error=repr(error));raise
    finally:
        receipt['wall_seconds']=round(time.time()-t0,1)
        if sha(source)!=source_hash:receipt['status']='ERROR: accepted board bytes changed during the run'
        save()


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('board',choices=('osc-core','osc-jack-left','osc-jack-right'))
    p.add_argument('--validate',action='store_true',help='host-only plan check; no KiCad, no routing')
    a=p.parse_args()
    if a.validate:
        r=validate(a.board);print(json.dumps(r,sort_keys=True));return 1 if r['errors'] else 0
    run(a.board)


if __name__=='__main__':sys.exit(main())
