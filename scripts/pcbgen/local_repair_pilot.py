#!/usr/bin/env python3
"""Read-only native JR local-repair pilot for #189; never promotes a board."""
import hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen import route_jack_grid as driver
from scripts.pcbgen.route_shards import delta
from scripts.pcbgen.copper_identity import retention


def main():
    plan_path=ROOT/'circuit/routing/issue189/jr-local-plan.json'
    plan=json.loads(plan_path.read_text());board_id=plan['board']
    source=ROOT/'boards'/board_id/f'{board_id}.kicad_pcb'
    source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
    if source_hash!=plan['input_board_sha256']:raise ValueError('stale local-repair input')
    out=ROOT/'.circuit-cache/issue189-jr-local';out.mkdir(exist_ok=True)
    receipt={'status':'RUNNING','adopted':False,'input_board_sha256':source_hash,
             'plan_sha256':hashlib.sha256(plan_path.read_bytes()).hexdigest()}
    def save(): (out/'result.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    save()
    try:
        base=driver.workspace(board_id,'189-local-base')/source.name;shutil.copyfile(source,base)
        before_drc,before=driver.check(base)
        if any(v['severity']=='error' for v in before_drc['violations']) or before_drc['schematic_parity']:
            raise driver.StageRejected('native baseline is not clean')
        spec=plan['stage'];definition=json.loads((ROOT/'design/boards'/f'{board_id}.json').read_text())
        candidate,stage=driver.run_stage(board_id,base,spec,definition,print)
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
    except Exception as error:
        receipt.update(status='ERROR; NOT ADOPTED',error=repr(error));raise
    finally:
        save()
        if hashlib.sha256(source.read_bytes()).hexdigest()!=source_hash:
            raise RuntimeError('canonical board changed during read-only pilot')


if __name__=='__main__':main()
