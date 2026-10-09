#!/usr/bin/env python3
"""Replay one eligible #189 benchmark candidate through fresh native gates.

No rerouting and no non-copper geometry replacement. Canonical files are changed
only with --promote, after hash checks, settled checks and an independent reload.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen import route_jack_grid as driver
from scripts.pcbgen.route_shards import delta,merge_text,copper_block_groups
from scripts.pcbgen.zone_cache import without_zone_cache
from scripts.pcbgen.copper_identity import retention


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_inputs(report,folder,root=ROOT):
    if report.get('status')!='COMPLETE':raise ValueError('benchmark is incomplete')
    board_id=report['board']
    if board_id not in ('osc-jack-left','osc-jack-right','osc-core'):raise ValueError('unknown board')
    new=report['variants']['new']
    if not new.get('eligible_for_promotion'):raise ValueError('benchmark candidate is not eligible')
    board=root/'boards'/board_id/f'{board_id}.kicad_pcb'
    if str(board.relative_to(root)) not in report['input_hashes']:raise ValueError('missing canonical input hash')
    for name,expected in report['input_hashes'].items():
        path=(root/name).resolve()
        if not path.is_relative_to(root.resolve()):raise ValueError('input path outside checkout')
        if sha(path)!=expected:raise ValueError('stale input: '+name)
    saved=folder/'input'/board.name;candidate=folder/'new'/'native'/board.name
    if sha(saved)!=report['saved_input_sha256']:raise ValueError('saved input hash mismatch')
    if sha(candidate)!=new['candidate_sha256']:raise ValueError('candidate hash mismatch')
    return board_id,board,candidate


def checked_copy(board_id,source,label):
    target=driver.workspace(board_id,label)/source.name
    shutil.copyfile(source,target)
    drc,dump=driver.check(target)
    if any(v['severity']=='error' for v in drc['violations']) or drc['schematic_parity']:
        raise driver.StageRejected(label+': native DRC/parity error')
    return target,drc,dump


def publication_copy(board_id,checked,drc,dump,limit=95*1024*1024):
    """Keep large derived fills out of Git only after native refill equivalence."""
    if checked.stat().st_size<limit:return checked,{}
    text,count=without_zone_cache(checked.read_text())
    compact=driver.workspace(board_id,'189-compact')/checked.name;compact.write_text(text)
    if not count or compact.stat().st_size>=limit:raise ValueError('board remains too large after derived cache removal')
    filled,refilled_drc,refilled=checked_copy(board_id,compact,'189-compact-refill')
    if driver.connectivity_signature(refilled)!=driver.connectivity_signature(dump):
        raise driver.StageRejected('cache-free saved board changed native connectivity after refill')
    if driver.warning_identities(refilled_drc)!=driver.warning_identities(drc):
        raise driver.StageRejected('cache-free saved board changed native warnings after refill')
    for kind in ('pads','tracks','vias'):
        if sorted(json.dumps(x,sort_keys=True) for x in refilled[kind])!=sorted(json.dumps(x,sort_keys=True) for x in dump[kind]):
            raise driver.StageRejected('cache-free saved board changed native '+kind)
    return compact,{'derived_zone_cache_fields_removed':count,'filled_bytes':checked.stat().st_size,
                    'published_bytes':compact.stat().st_size,'refilled_board_sha256':sha(filled),
                    'status':'Native settled refill matches accepted connectivity, warnings and pad/copper geometry'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('benchmark_dir',type=Path);p.add_argument('--promote',action='store_true')
    a=p.parse_args();report_path=a.benchmark_dir/'result.json'
    report=json.loads(report_path.read_text())
    board_id,board,candidate=validate_inputs(report,a.benchmark_dir)
    original=board.read_text();replay=delta(original,candidate.read_text())
    replayed=driver.workspace(board_id,'189-replay')/board.name
    replayed.write_text(merge_text(original,[replay]))
    # A delta must reproduce all candidate copper without changing panel/parts/zones.
    def complete_copper(text):return {u:sorted(x[2] for x in items) for u,items in copper_block_groups(text).items()}
    if complete_copper(replayed.read_text())!=complete_copper(candidate.read_text()):
        raise ValueError('copper replay differs from benchmark candidate')
    _,before_drc,before=checked_copy(board_id,board,'189-adopt-base')
    baseline_dump=json.loads((a.benchmark_dir/'input'/'dump.json').read_text())
    if driver.connectivity_signature(before)!=driver.connectivity_signature(baseline_dump):
        raise driver.StageRejected('current settled baseline differs from benchmark')
    checked,after_drc,after=checked_copy(board_id,replayed,'189-adopt-check')
    fresh,fresh_drc,fresh_dump=checked_copy(board_id,checked,'189-adopt-fresh')
    if driver.connectivity_signature(after)!=driver.connectivity_signature(fresh_dump):
        raise driver.StageRejected('independent replay connectivity differs')
    gate=driver.promotion_gate(before,fresh_dump,before_drc,fresh_drc)
    publication,cache_receipt=publication_copy(board_id,fresh,fresh_drc,fresh_dump) if gate['adopted'] else (fresh,{})
    receipt={'schema':'obstacle-benchmark-adoption-1','benchmark_sha256':sha(report_path),
             'benchmark_source':report['new_ref'],'input_board_sha256':sha(board),
             'candidate_board_sha256':sha(publication),'native_filled_board_sha256':sha(fresh),
             'publication_cache':cache_receipt,'open_edges_before':before['open_edges'],
             'open_edges_after':fresh_dump['open_edges'],'open_by_net_after':{n:len(g)-1 for n,g in fresh_dump['islands'].items()},
             'drc_errors':0,'parity':0,'warning_identities':driver.warning_identities(fresh_drc),
             'retained_copper':retention(before,fresh_dump),**gate}
    receipt['status']='NATIVE CHECKED UNVALIDATED DRAFT'
    output=ROOT/'.circuit-cache'/f'{board_id}-189-adoption.json'
    output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    if not gate['adopted']:raise driver.StageRejected('replay failed promotion gate: '+str(output))
    if a.promote:
        # Recheck the canonical SHA immediately before the write; do not overwrite
        # copper another process adopted while these lengthy native checks ran.
        if sha(board)!=replay['base_sha256']:raise ValueError('canonical board changed during native checks')
        reports=board.parent/'reports'/'grid-routing';reports.mkdir(exist_ok=True)
        replay_path=reports/'issue189-benchmark-copper.json'
        replay_path.write_text(json.dumps(replay,sort_keys=True)+'\n')
        receipt['copper_replay']={'path':driver.rel(replay_path),'sha256':sha(replay_path),'base_sha256':replay['base_sha256']}
        (reports/'issue189-benchmark.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
        shutil.copyfile(publication,board)
    print(json.dumps({'promoted':a.promote,'board':board_id,'before':before['open_edges'],'after':fresh_dump['open_edges']}))


if __name__=='__main__':main()
