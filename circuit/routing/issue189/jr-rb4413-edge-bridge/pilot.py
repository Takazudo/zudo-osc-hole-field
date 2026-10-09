"""Disposable RB4413 movement experiment; never publishes a board or edits source."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_move(source, output):
    import pcbnew
    plan = json.loads((HERE / 'plan.json').read_text())
    if subprocess.check_output(['kicad-cli', 'version'], text=True).strip() != '10.0.6':
        raise ValueError('pinned native oracle required')
    board = pcbnew.LoadBoard(str(source))
    fp = next(f for f in board.GetFootprints() if f.GetReference() == plan['ref'])
    part = plan['source_part']
    expected = [round((part['x_mm'] + 100) * 1e6), round((part['y_mm'] + 50) * 1e6)]
    if fp.IsLocked() or fp.GetLayerName() != part['side']:
        raise ValueError('footprint is locked or side differs from source')
    if [fp.GetPosition().x, fp.GetPosition().y] != expected:
        raise ValueError('footprint origin differs from source')
    if fp.GetOrientationDegrees() % 360 != part['kicad_orientation_deg']:
        raise ValueError('footprint orientation differs from source')
    fp.Move(pcbnew.VECTOR2I(*plan['translation_nm']))
    pcbnew.SaveBoard(str(output), board)


def main():
    from scripts.pcbgen import route_jack_grid as driver
    from scripts.pcbgen.copper_identity import retention
    plan = json.loads((HERE / 'plan.json').read_text())
    board_id = plan['board']
    source = ROOT / 'boards' / board_id / (board_id + '.kicad_pcb')
    floor = ROOT / 'design/partition/floorplan-candidate.json'
    proposal_path = HERE / 'proposal.json'
    assert sha(source) == plan['input_board_sha256']
    assert sha(floor) == plan['floorplan_sha256']
    assert sha(proposal_path) == plan['proposal_sha256']
    part = next(p for p in json.loads(floor.read_text())['placements'] if p['ref'] == plan['ref'])
    assert part == plan['source_part'] and not part['fixed'] and 'bypass_cluster' not in part
    out = ROOT / '.circuit-cache/issue189-rb4413-move'
    out.mkdir(exist_ok=True)
    receipt = dict(status='RUNNING', adopted=False, source_regenerated=False, plan_sha256=sha(HERE / 'plan.json'))
    try:
        base = driver.workspace(board_id, '189-jr-rb4413-base') / source.name
        shutil.copyfile(source, base)
        before_drc, before = driver.check(base)
        if any(v['severity'] == 'error' for v in before_drc['violations']) or before_drc['schematic_parity']:
            raise ValueError('baseline native errors')
        moved = driver.workspace(board_id, '189-jr-rb4413-moved') / source.name
        driver.run('bash', 'scripts/kicad/run.sh', 'python3', driver.rel(Path(__file__)),
                   '--native-move', driver.rel(base), driver.rel(moved))
        proposal = json.loads(proposal_path.read_text())
        assert not proposal['removed_uuids']
        proposal['board_sha256'] = sha(moved)
        replay = out / 'moved-copper.json'
        replay.write_text(json.dumps(proposal, indent=2) + '\n')
        candidate = driver.workspace(board_id, '189-jr-rb4413-candidate') / source.name
        driver.run('bash', 'scripts/kicad/run.sh', 'python3', 'scripts/pcbgen/grid_apply.py',
                   driver.rel(moved), driver.rel(replay), '--output', driver.rel(candidate))
        after_drc, after = driver.check(candidate)
        fresh = driver.workspace(board_id, '189-jr-rb4413-fresh') / source.name
        shutil.copyfile(candidate, fresh)
        fresh_drc, verified = driver.check(fresh)
        receipt.update(status='COMPLETE DISPOSABLE PILOT; SOURCE REGENERATION NOT RUN; NOT ADOPTED',
                       open_edges_before=before['open_edges'], open_edges_after=after['open_edges'],
                       gate=driver.promotion_gate(before, after, before_drc, after_drc),
                       fresh_gate=driver.promotion_gate(before, verified, before_drc, fresh_drc),
                       fresh_agreement=driver.connectivity_signature(after) == driver.connectivity_signature(verified),
                       retained_copper=retention(before, after), candidate_sha256=sha(candidate),
                       fresh_sha256=sha(fresh), proposal_sha256=sha(replay))
    except Exception as error:
        receipt.update(status='ERROR; NOT ADOPTED', error=repr(error))
        raise
    finally:
        (out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
        assert sha(source) == plan['input_board_sha256'] and sha(floor) == plan['floorplan_sha256']


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--native-move':
        native_move(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        main()
