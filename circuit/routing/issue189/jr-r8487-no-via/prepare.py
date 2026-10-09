"""Serialize the pinned additive signal proposal with the native oracle.

This writes a disposable candidate and delta only. route_shards.merge must still
run all original-baseline gates before any canonical adoption.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.route_shards import delta


def main():
    board = ROOT / 'boards/osc-jack-right/osc-jack-right.kicad_pcb'
    proposal = HERE / 'proposal.json'
    plan = json.loads((HERE / 'plan.json').read_text())
    if hashlib.sha256(board.read_bytes()).hexdigest() != plan['base_sha256']:
        raise ValueError('JR changed: recompute the bounded proposal; never overwrite accepted copper')
    if hashlib.sha256(proposal.read_bytes()).hexdigest() != plan['proposal_sha256']:
        raise ValueError('Bounded proposal differs from the reviewed plan')
    work = ROOT / '.circuit-cache/issue189-jr-r8487-no-via'
    work.mkdir(parents=True, exist_ok=True)
    candidate = work / board.name
    subprocess.run(['bash', 'scripts/kicad/run.sh', 'python3',
                    'scripts/pcbgen/grid_apply.py', str(board.relative_to(ROOT)),
                    str(proposal.relative_to(ROOT)), '--output',
                    str(candidate.relative_to(ROOT))], cwd=ROOT, check=True)
    replay = delta(board.read_text(), candidate.read_text())
    if replay['removed']:
        raise ValueError('Additive signal escape unexpectedly removed existing copper')
    (work / 'copper.json').write_text(json.dumps(replay) + '\n')
    print('Prepared native-serialized delta; connectivity/DRC gate NOT RUN')


if __name__ == '__main__':
    main()
