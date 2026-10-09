"""Prepare whole saved supply cases after reconciliation; never remove accepted copper."""
import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location('signal_rebase', HERE.parent / 'core-short-no-via/rebase_proposal.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def retained_known_additions(added, batches):
    actual = {row['uuid'] for row in added}
    assert len(actual) == len(added), 'duplicate new UUID'
    known = []
    for batch in batches:
        ids = {row['uuid'] for row in batch}
        overlap = actual & ids
        assert not overlap or overlap == ids, 'partial known addition: reconcile explicitly'
        if overlap:
            known.extend(batch)
    assert actual == {row['uuid'] for row in known}, 'unknown accepted additions'
    guard.require_known_geometry(added, known)
    return known


def select_whole_cases(proposal, selection, fixed):
    by_id = {row['uuid']: row for row in proposal['copper']}
    claimed = [u for case in selection for u in case['uuids']]
    assert len(claimed) == len(set(claimed)) == len(by_id)
    assert set(claimed) == set(by_id)
    rows, kept, excluded = [], [], []
    for case in selection:
        copper = [by_id[u] for u in case['uuids']]
        minimum = min((guard.gap(a, b) for a in copper for b in fixed), default=math.inf)
        receipt = {**case, 'minimum_gap_to_accepted_additions_mm': minimum if math.isfinite(minimum) else None}
        if minimum < .25:
            excluded.append(receipt)
        else:
            kept.append(receipt)
            rows.extend(copper)
    return rows, kept, excluded


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--accepted-sha256', required=True)
    args = parser.parse_args()
    board = 'boards/osc-core/osc-core.kicad_pcb'
    source_commit = '4580536e8edd0bb9216c02d6b01aec00189da20e'
    old = subprocess.check_output(['git', 'show', f'{source_commit}:{board}'], cwd=ROOT).decode()
    current = (ROOT / board).read_text()
    sha = hashlib.sha256(current.encode()).hexdigest()
    assert sha == args.accepted_sha256, 'accepted core hash differs'
    proposal_path = HERE / 'proposal-original.json'
    proposal = json.loads(proposal_path.read_text())
    selection = json.loads((HERE / 'selection.json').read_text())
    assert hashlib.sha256(old.encode()).hexdigest() == proposal['board_sha256']
    assert hashlib.sha256(proposal_path.read_bytes()).hexdigest() == selection['proposal_sha256']
    assert not proposal['removed_uuids'] and len(proposal['copper']) == 120 and len(selection['selected']) == 94
    before, after = guard.copper_block_groups(old), guard.copper_block_groups(current)
    assert all(blocks == after.get(u) for u, blocks in before.items()), 'accepted original copper changed'
    change = guard.delta(old, current)
    assert not change['removed']
    batches = [json.loads((HERE.parent / path).read_text())['copper'] for path in (
        'core-finer-ground-batch/proposal.json', 'core-short-no-via/proposal-original.json')]
    fixed = retained_known_additions(change['added'], batches)
    rows, kept, excluded = select_whole_cases(proposal, selection['selected'], fixed)
    assert rows and all(r['kind'] == 'segment' and r['net'] in ['+12V', '-12V'] and r['width_nm'] == 250000 and r['layer'] in ['F.Cu', 'B.Cu'] for r in rows)
    assert all(r['uuid'] not in after for r in rows)
    minimum = min(guard.gap(a, b) for i, a in enumerate(rows) for b in rows[:i])
    assert minimum >= .25, 'saved supply cases conflict with each other'
    output = HERE / 'proposal.json'
    output.write_text(json.dumps({**proposal, 'board_sha256': sha, 'copper': rows}, indent=2) + '\n')
    (HERE / 'plan.json').write_text(json.dumps({'base_sha256': sha, 'proposal_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'scope': f'{len(kept)} whole supply cases, {len(rows)} full-width outer segments, zero vias/cuts; heuristic only, native gates mandatory'}, indent=2) + '\n')
    (HERE / 'rebase.json').write_text(json.dumps({'status': 'REBASED; NATIVE NOT RUN', 'source_commit': source_commit, 'source_board_sha256': proposal['board_sha256'], 'accepted_board_sha256': sha, 'retained_objects': sum(map(len, after.values())), 'retained_new_objects': len(fixed), 'added_objects': len(rows), 'removed_objects': 0, 'minimum_new_cross_net_gap_mm': minimum if math.isfinite(minimum) else None, 'selected': kept, 'excluded_for_accepted_copper': excluded}, indent=2) + '\n')
    print('Prepared', len(kept), 'whole supply cases;', len(excluded), 'omitted; native NOT RUN')


if __name__ == '__main__':
    main()
