#!/usr/bin/env python3
"""Read-only native jack local-repair pilot for #189; never promotes a board."""
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen import route_jack_grid as driver
from scripts.pcbgen.route_shards import delta
from scripts.pcbgen.copper_identity import retention


def coupled_candidate(board_id,base,before,plan,definition):
    """Check one fixed signal replay, then restore supply/return membership.

    This disposable transaction does not weaken the ordinary router's fill
    guard. Its intermediate signal topology is never eligible for promotion.
    """
    rail_method=plan.get('rail_method','rail-fanout')
    if rail_method not in ('rail-fanout','rail-links'):
        raise ValueError('unsupported coupled rail method')
    proposal=ROOT/plan['signal_proposal']
    if hashlib.sha256(proposal.read_bytes()).hexdigest()!=plan['signal_proposal_sha256']:
        raise ValueError('coupled proposal changed')
    if hashlib.sha256(base.read_bytes()).hexdigest()!=plan['input_board_sha256']:
        raise ValueError('native baseline bytes differ from coupled proposal input')
    candidate=driver.workspace(board_id,plan['name'])/base.name
    driver.run('bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_apply.py',
               driver.rel(base),driver.rel(proposal),'--output',driver.rel(candidate))
    drc,after=driver.check(candidate)
    if any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:
        raise driver.StageRejected('coupled signal proposal has native DRC/parity errors')
    phases={'signal_open_edges':after['open_edges']}
    splits=driver.split_pad_groups(before,after)
    prior_minus=len(before['islands'].get('-12V',[None]))-1
    needs_rail=any(s['net']=='-12V' for s in splits) or len(after['islands'].get('-12V',[None]))-1>prior_minus
    if needs_rail:
        rail={**next(s for s in driver.STAGES if s['name']==rail_method),
              'name':plan['name']+'-rail','nets':['-12V'],'res':.05,'window_mm':6}
        if rail_method=='rail-fanout':rail['planes']={'-12V':'In3.Cu'}
        restored,receipt=driver.run_stage(board_id,candidate,rail,definition,print)
        phases['rail']=receipt
        if restored is None:raise driver.StageRejected('bounded -12V restoration failed')
        candidate=restored;after=json.loads(candidate.with_name('dump.json').read_text())
    if any(s['net']=='-12V' for s in driver.split_pad_groups(before,after)) or len(after['islands'].get('-12V',[None]))-1>prior_minus:
        raise driver.StageRejected('coupled transaction did not restore original -12V connectivity')
    if any(s['net']=='AGND' for s in driver.split_pad_groups(before,after)):
        initial={'open_edges_before':before['open_edges'],'open_edges_after':after['open_edges'],
                 'open_by_net_after':{n:len(g)-1 for n,g in after['islands'].items()}}
        candidate,phases['ground']=driver.stitched(board_id,base,candidate,initial,{'name':plan['name']},definition,print)
        after=json.loads(candidate.with_name('dump.json').read_text())
    # Independent reload after the complete transaction, even if a substage
    # already checked its own copy. The caller applies the original-baseline gate.
    fresh=driver.workspace(board_id,plan['name']+'-fresh')/base.name;shutil.copyfile(candidate,fresh)
    drc,verified=driver.check(fresh)
    if driver.connectivity_signature(after)!=driver.connectivity_signature(verified):
        raise driver.StageRejected('coupled transaction fresh-copy connectivity differs')
    if any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:
        raise driver.StageRejected('coupled fresh copy has native DRC/parity errors')
    return fresh,{'status':'NATIVE CHECKED DISPOSABLE COUPLED TRANSACTION','phases':phases}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',choices=('osc-jack-left','osc-jack-right'),default='osc-jack-right')
    parser.add_argument('--coupled',action='store_true',help='fixed jack signal replay with mandatory native supply restoration')
    args=parser.parse_args();short='jl' if args.board=='osc-jack-left' else 'jr'
    mode='coupled' if args.coupled else 'local'
    plan_path=ROOT/f'circuit/routing/issue189/{short}-{mode}-plan.json'
    plan=json.loads(plan_path.read_text());board_id=plan['board']
    if board_id!=args.board:raise ValueError('plan board differs from requested board')
    source=ROOT/'boards'/board_id/f'{board_id}.kicad_pcb'
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash!=plan['input_board_sha256']:raise ValueError('stale local-repair input')
    out=ROOT/f'.circuit-cache/issue189-local-{board_id}';out.mkdir(exist_ok=True)
    receipt={'status':'RUNNING','adopted':False,'input_board_sha256':source_hash,
             'plan_sha256':hashlib.sha256(plan_path.read_bytes()).hexdigest()}
    def save(): (out/'result.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    save()
    try:
        base=driver.workspace(board_id,'189-local-base')/source.name;shutil.copyfile(source,base)
        before_drc,before=driver.check(base)
        if any(v['severity']=='error' for v in before_drc['violations']) or before_drc['schematic_parity']:
            raise driver.StageRejected('native baseline is not clean')
        definition=json.loads((ROOT/'design/boards'/f'{board_id}.json').read_text())
        if args.coupled:candidate,stage=coupled_candidate(board_id,base,before,plan,definition)
        else:candidate,stage=driver.run_stage(board_id,base,plan['stage'],definition,print)
        receipt.update(stage=stage,open_edges_before=before['open_edges'])
        if candidate:
            after=json.loads(candidate.with_name('dump.json').read_text())
            after_drc=json.loads(candidate.with_name('drc.json').read_text())
            gate=driver.promotion_gate(before,after,before_drc,after_drc)
            receipt.update(gate=gate,open_edges_after=after['open_edges'],
                           retained_copper=retention(before,after),
                           candidate_sha256=hashlib.sha256(candidate.read_bytes()).hexdigest())
            replay=delta(source.read_text(),candidate.read_text())
            (out/'copper.json').write_text(json.dumps(replay,sort_keys=True)+'\n')
            receipt['replay_sha256']=hashlib.sha256((out/'copper.json').read_bytes()).hexdigest()
        receipt['status']='COMPLETE READ-ONLY PILOT; NO CANONICAL PROMOTION'
    except driver.StageRejected as error:
        receipt.update(status='REJECTED; NOT ADOPTED',error=str(error))
    except Exception as error:
        receipt.update(status='ERROR; NOT ADOPTED',error=repr(error));raise
    finally:
        save()
        if hashlib.sha256(source.read_bytes()).hexdigest()!=source_hash:
            raise RuntimeError('canonical board changed during read-only pilot')


if __name__=='__main__':main()
