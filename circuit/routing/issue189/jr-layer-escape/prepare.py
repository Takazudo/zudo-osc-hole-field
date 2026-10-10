"""Select whole compatible bounded proposals; never remove accepted copper."""
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location('guard', HERE.parent / 'core-short-no-via/rebase_proposal.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
screen = json.loads((HERE / 'result.json').read_text())
assert len(screen['cases']) == 12 and screen['status'] == 'COMPLETE BOUNDED SEARCH; NO NATIVE ACCEPTANCE'
success = [c for c in screen['cases'] if c['complete']]
assert len(success) == 3 and all(c['domain'] == 'in3' for c in success)
selected = [c for c in success if c['net'] in ('XCD7957368B0652402848', 'X94EA1D24CF22A66FD76B')]
assert len(selected) == 2
gap = min(guard.gap(a, b) for a in selected[0]['proposal']['copper'] for b in selected[1]['proposal']['copper'])
assert gap > .25
conflicts = [{ 'nets': [a['net'], b['net']], 'minimum_gap_mm': min(guard.gap(x, y) for x in a['proposal']['copper'] for y in b['proposal']['copper']) } for a, b in itertools.combinations(success, 2)]
assert any(row['minimum_gap_mm'] < 0 for row in conflicts)
copper = [row for c in selected for row in c['proposal']['copper']]
assert len(copper) == len({r['uuid'] for r in copper}) == 146
assert sum(r['kind'] == 'via' for r in copper) == 3
assert all(not c['proposal']['removed_uuids'] for c in selected)
assert all(r['kind'] == 'via' or r['layer'] in ('F.Cu', 'In3.Cu', 'B.Cu') for r in copper)
board = ROOT / 'boards/osc-jack-right/osc-jack-right.kicad_pcb'
assert sha(board) == screen['board_sha256'] == '22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd'
proposal = HERE / 'proposal.json'
proposal.write_text(json.dumps(dict(board_sha256=sha(board), removed_uuids=[], copper=copper), indent=2) + '\n')
plan = dict(board='osc-jack-right', input_board_sha256=sha(board), name='189-jr133-in3-two-whole',
    proposal=str(proposal.relative_to(ROOT)), proposal_sha256=sha(proposal), rail_method='rail-links',
    restore_connectivity=False, scope='Two complete signal obligations,143segments/3vias on F/In3/B; zero cuts/moves. Preserve all51256prior copper objects, all original pad groups, settled/fresh DRC/parity and warning gates. Full capped-warning audits mandatory before later adoption; pilot never publishes.')
(HERE / 'plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(ROOT / 'circuit/routing/issue189/jr-coupled-plan.json').write_text(json.dumps(plan, indent=2) + '\n')
(HERE / 'selection.json').write_text(json.dumps(dict(selected=[c['net'] for c in selected],
    excluded_whole_case='XD0EC0FB162FC331E3F8D', pairwise_gaps=conflicts,
    reason='Two U7406 alternatives intersect; retain the compatible pair with fewer vias/objects. No accepted copper removed.',
    screen_sha256=sha(HERE / 'result.json'), proposal_sha256=sha(proposal)), indent=2) + '\n')
print('Prepared143segments/3vias; minimum new cross-net gap', gap, '; native NOT RUN')
