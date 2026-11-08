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

Receipt lifecycle (lifecycle.py, issue #308): the receipt is written atomically
before every native call, the driver's own SIGINT/SIGTERM handler forwards the
signal to the children it started and finalises `INTERRUPTED; NOT ADOPTED`, a
--max-minutes deadline finalises `TIMED OUT; NOT ADOPTED`, and --reconcile lets
the collector finish a receipt from the process exit status it saw. The only
change to the imported driver is at run time: its run() subprocess helper is
replaced by lifecycle.owned_run so the children are reachable.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts/checks'));sys.path.insert(0,str(HERE))
import lifecycle
RAILS=('+12V','-12V','+5V')
# Wall-clock budgets in minutes, one source for the driver and the workflow (budgets.json beside this
# script). K needs more native checks than a jack (README 2026-11-08); the plan's limits.wall_minutes=60
# stays as the 2026-11-07 record. An explicit --max-minutes wins.
BUDGETS=HERE/'budgets.json'
def default_minutes(board_id):return json.loads(BUDGETS.read_text())['minutes'][board_id]


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


def run(board_id,driver=None,delta=None,retention=None,out_dir=HERE,invocation=None,max_minutes=None,budget_source=None,cid_dir=None):
    """One native transaction. driver/delta/retention default to the real modules; tests inject stubs."""
    lifecycle.reset()
    plan=load(board_id);spec=plan['transaction']['spec']
    source=ROOT/plan['input_board'];source_hash=sha(source)
    if source_hash!=plan['input_board_sha256']:raise SystemExit('accepted board changed; replan before running')
    invocation=invocation or lifecycle.new_invocation()
    out=Path(out_dir)/f'{spec["name"]}.json'
    if out.exists():
        # A receipt from another invocation (a committed historical one, or a run that was cut off) is never overwritten.
        try:prior=json.loads(out.read_text()).get('invocation')
        except (ValueError,AttributeError):prior='<unreadable>'
        if prior!=invocation:
            raise lifecycle.StaleReceipt(f'{out} exists from invocation {prior!r}, not {invocation!r}; move or delete it before this run '
                                         '(the workflow run step does that). Nothing was started.')
    # The RUNNING receipt exists before anything slow (plan validation, driver imports, the git call): a signal in
    # that window then still ends in a finalised receipt and a cleaned cid directory.
    receipt={'schema':lifecycle.SCHEMA,'status':'RUNNING','terminal':False,'terminal_outcome':None,'adopted':False,'raw_gate_passed':False,
             'board':board_id,'input_board':plan['input_board'],'input_board_sha256':source_hash,'plan_sha256':sha(HERE/'transactions.json'),
             'spec':spec,'spec_name':spec['name'],'started_utc':lifecycle.utc(),'invocation':invocation,'source_revision':None,'environment':None,
             'driver':{'pid':os.getpid(),'pgid':os.getpgid(0),'python':sys.version.split()[0],'argv':sys.argv,'signal_handlers':lifecycle.STATE.installed},
             'max_minutes':max_minutes,'budget_source':budget_source,'grace_seconds':lifecycle.STATE.grace,
             'oracle_cid_dir':None,'phases':[],'native_calls':[],'current_child':None,'signals':[]}
    rec=lifecycle.Receipt(out,receipt);save=rec.save;t0=time.time()
    try:
        lifecycle.STATE.cwd=ROOT
        lifecycle.STATE.cid_dir=Path(cid_dir) if cid_dir else ROOT/'.circuit-cache'/f'osc4-oracle-cids-{invocation}'
        lifecycle.STATE.cid_dir.mkdir(parents=True,exist_ok=True);receipt['oracle_cid_dir']=str(lifecycle.STATE.cid_dir)
        lifecycle.STATE.receipt=rec;rec.checkpoint('preflight')
        # The host-side plan checks (unique in-frame cuts, target pad in the frame, target net open) gate the native run.
        checked=validate(board_id)
        if checked['errors']:raise SystemExit('plan invalid: '+'; '.join(checked['errors']))
        if driver is None:import scripts.pcbgen.route_jack_grid as driver
        if delta is None:from scripts.pcbgen.route_shards import delta
        if retention is None:from scripts.pcbgen.copper_identity import retention
        # Make the native children owned: the driver's run() helper spawns `bash scripts/kicad/run.sh ...` through its RUNNER hook.
        if hasattr(driver,'RUNNER'):driver.RUNNER=lifecycle.owned_run
        elif hasattr(driver,'run'):driver.run=lifecycle.owned_run
        receipt.update(source_revision=lifecycle.source_revision(ROOT),environment=lifecycle.environment())
        rec.checkpoint('base_check')
        base=driver.workspace(board_id,spec['name']+'-base')/source.name;shutil.copyfile(source,base)
        before_drc,before=driver.check(base)
        if any(v['severity']=='error' for v in before_drc['violations']) or before_drc['schematic_parity']:
            raise driver.StageRejected('native baseline is not clean')
        definition=json.loads((ROOT/'design/boards'/f'{board_id}.json').read_text())
        # run_stage() owns the cut/apply, the candidate check and the driver's own verify check; each native call is logged.
        rec.checkpoint('stage',open_edges_before=before['open_edges'])
        candidate,stage=driver.run_stage(board_id,base,spec,definition,print)
        receipt.update(stage=stage,open_edges_before=before['open_edges'])
        if candidate is not None and stage and not stage.get('rejected'):
            after=json.loads(candidate.with_name('dump.json').read_text())
            if after['open_edges']>=before['open_edges'] or driver.split_pad_groups(before,after):
                rec.checkpoint('stitch',open_edges_after_stage=after['open_edges'])
                candidate,stage=driver.stitched(board_id,base,candidate,stage,spec,definition,print)
                receipt['stage']=stage  # carries stage.agnd_stitch when the board-wide stitch was used
                after=json.loads(candidate.with_name('dump.json').read_text())
            rec.checkpoint('fresh_check',open_edges_candidate=after['open_edges'])
            fresh=driver.workspace(board_id,spec['name']+'-fresh')/source.name;shutil.copyfile(candidate,fresh)
            fresh_drc,verified=driver.check(fresh)
            if driver.connectivity_signature(after)!=driver.connectivity_signature(verified):
                raise driver.StageRejected('fresh-copy connectivity differs from the candidate')
            rec.checkpoint('final_gate')
            gate=driver.promotion_gate(before,verified,before_drc,fresh_drc)
            replay=delta(source.read_text(),fresh.read_text())
            lifecycle.write_atomic(Path(out_dir)/f'{spec["name"]}-copper.json',json.dumps(replay,sort_keys=True)+'\n')
            # 'adopted' stays False: this driver never promotes, and adoption also needs the complete-warning audit.
            receipt.update(raw_gate=gate,raw_gate_passed=bool(gate['adopted']),open_edges_after=verified['open_edges'],
                           open_by_net_after={n:len(g)-1 for n,g in verified['islands'].items()},
                           retained_copper=retention(before,verified),candidate_sha256=sha(fresh),
                           complete_native_warning_evidence='NOT RUN: raw gate only; adoption needs the complete-warning audit',
                           terminal_outcome='COMPLETED',
                           status=('NATIVE CHECKED; RAW GATE PASSED; NOT PROMOTED' if gate['adopted']
                                   else 'NATIVE CHECKED; RAW GATE FAILED; NOT ADOPTED'))
        else:receipt.update(status='REJECTED OR NOTHING TO DO; NOT ADOPTED',terminal_outcome='REJECTED')
    except (Exception,SystemExit) as error:
        receipt.update(status='ERROR; NOT ADOPTED',terminal_outcome='ERROR',error=repr(error));raise
    except BaseException as error:
        # The lifecycle handler already named the signal; a bare KeyboardInterrupt/SystemExit is recorded here. Never left RUNNING.
        if receipt.get('terminal_outcome') not in ('INTERRUPTED','TIMED_OUT'):receipt.update(status='INTERRUPTED; NOT ADOPTED',terminal_outcome='INTERRUPTED')
        receipt['error']=repr(error);raise
    finally:
        lifecycle.settle()  # the result is decided: cancel the deadline, later signals are only recorded
        rec.end_phase();receipt['wall_seconds']=round(time.time()-t0,1);receipt['ended_utc']=lifecycle.utc()
        if sha(source)!=source_hash:receipt.update(status='ERROR: accepted board bytes changed during the run',terminal_outcome='ERROR')
        receipt['signals']=list(lifecycle.STATE.signals)
        # Only a completed gate may carry raw_gate_passed; nothing may carry adopted.
        if receipt['terminal_outcome']!='COMPLETED':receipt['raw_gate_passed']=False
        receipt['adopted']=False;receipt['terminal']=True
        save();lifecycle.sweep_containers(rec);lifecycle.cleanup_cid_dir()
        # A signal that arrived while finalising was only recorded in STATE (the handler does not write then).
        receipt['signals']=list(lifecycle.STATE.signals);save();lifecycle.STATE.receipt=None


def parse_exit_status(text):
    if text is None or text.strip().lower() in ('','unknown','none'):return None
    return int(text)


def main(argv=None,**injected):
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('board',choices=('osc-core','osc-jack-left','osc-jack-right'))
    p.add_argument('--validate',action='store_true',help='host-only plan check; no KiCad, no routing')
    p.add_argument('--max-minutes',type=float,default=None,help='wall-clock budget; the driver stops itself and finalises TIMED OUT (default per board in budgets.json)')
    p.add_argument('--print-budget',action='store_true',help='print the default budget in minutes for the board and exit')
    p.add_argument('--invocation',default=None,help='invocation id stamped into the receipt (default: generated; the workflow passes its run id)')
    p.add_argument('--grace-seconds',type=float,default=None,help='time an interrupted native child gets before SIGKILL (default %s or $OSC4_GRACE_SECONDS)'%lifecycle.DEFAULT_GRACE_SECONDS)
    p.add_argument('--out-dir',default=str(HERE),help=argparse.SUPPRESS)
    p.add_argument('--cid-dir',default=None,help=argparse.SUPPRESS)
    p.add_argument('--reconcile',action='store_true',help='collector mode: finish a receipt the driver left nonterminal from --exit-status; host-only')
    p.add_argument('--exit-status',default=None,help="with --reconcile: the driver's exit status as the shell saw it, or 'unknown'")
    p.add_argument('--force-reconcile-corrupt',action='store_true',help='with --reconcile: also finish an unreadable receipt (its bytes go to <spec>.raw-events.jsonl)')
    a=p.parse_args(argv)
    if a.validate:
        r=validate(a.board);print(json.dumps(r,sort_keys=True));return 1 if r['errors'] else 0
    if a.print_budget:print(default_minutes(a.board));return 0
    spec_name=load(a.board)['transaction']['spec']['name']
    if a.reconcile:
        r=lifecycle.reconcile(Path(a.out_dir)/f'{spec_name}.json',parse_exit_status(a.exit_status),invocation=a.invocation,board=a.board,spec_name=spec_name,
                              force_corrupt=a.force_reconcile_corrupt)
        print(json.dumps(r,sort_keys=True));return r['exit_code']
    max_minutes=a.max_minutes if a.max_minutes is not None else default_minutes(a.board)
    budget_source='--max-minutes' if a.max_minutes is not None else f'driver default for {a.board} (budgets.json)'
    lifecycle.install(deadline_seconds=max_minutes*60,grace=a.grace_seconds)
    try:run(a.board,invocation=a.invocation,max_minutes=max_minutes,budget_source=budget_source,out_dir=a.out_dir,cid_dir=a.cid_dir,**injected)
    except lifecycle.Interrupted as e:
        print(f'transaction stopped: {e.reason}; receipt finalised (exit {e.exit_code})',file=sys.stderr);return e.exit_code
    except lifecycle.StaleReceipt as e:
        print(f'refusing to start: {e}',file=sys.stderr);return 3
    return 0


if __name__=='__main__':sys.exit(main())
