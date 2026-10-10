"""Select one complete saved JR131 In2 path; native acceptance remains mandatory."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups
HERE=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb'
assert sha(board)=='7bb70ac47e12c8bb2e2362d78f7602bdf99c2a69214c68aebeef273b0ce11965'
assert sum(map(len,copper_block_groups(board.read_text()).values()))==51402
screen=HERE/'screen.json'
assert sha(screen)=='6eebc55ae83d70ea6b34711f31781fafdfd5c2087de53fd73d3f6bc84d14298b'
s=json.loads(screen.read_text());assert len(s['cases'])==8 and s['board_sha256']==sha(board)
assert s['router_sha256']==sha(ROOT/'scripts/pcbgen/grid_router.py')
case=next(c for c in s['cases'] if c['net']=='XE8DD7DCFD030742EDE49' and c['domain']=='in2')
assert case['complete'] and all(r['path'] for r in case['routes'])
p=case['proposal'];rows=p['copper'];assert p['board_sha256']==sha(board) and not p['removed_uuids']
assert len(rows)==len({r['uuid'] for r in rows})==119 and sum(r['kind']=='via' for r in rows)==3
assert all(r['kind']=='via' or r['layer'] in ('F.Cu','In2.Cu','B.Cu') for r in rows)
proposal=HERE/'proposal.json';proposal.write_text(json.dumps(p,indent=2)+'\n')
plan=dict(board='osc-jack-right',input_board_sha256=sha(board),name='189-jr131-d7411-in2',proposal=str(proposal.relative_to(ROOT)),proposal_sha256=sha(proposal),rail_method='rail-links',restore_connectivity=False,scope='One whole D7411.1-U7409.6 signal obligation,116segments/3vias,0cuts/moves. Preserve all51402accepted copper objects and all original pad groups. Full settled/fresh native DRC/parity and capped-warning audits remain required before adoption.')
(HERE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(ROOT/'circuit/routing/issue189/jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps(dict(screen_sha256=sha(screen),selected_net=case['net'],domain='in2',proposal_sha256=sha(proposal),reason='Whole path uses3vias and no In3segments; alternative four-layer path uses4vias. Native plane preservation remains unproven.',removed_copper=0,retained_copper=51402),indent=2)+'\n')
print('Prepared116segments/3vias; native NOT RUN')
