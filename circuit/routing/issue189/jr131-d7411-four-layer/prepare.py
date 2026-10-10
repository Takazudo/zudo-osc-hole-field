"""Select one complete saved JR131 four-layer path; native acceptance remains mandatory."""
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
screen=HERE.parent/'jr131-d7411-in2/screen.json'
assert sha(screen)=='6eebc55ae83d70ea6b34711f31781fafdfd5c2087de53fd73d3f6bc84d14298b'
s=json.loads(screen.read_text());assert len(s['cases'])==8 and s['board_sha256']==sha(board)
assert s['router_sha256']==sha(ROOT/'scripts/pcbgen/grid_router.py')
case=next(c for c in s['cases'] if c['net']=='XE8DD7DCFD030742EDE49' and c['domain']=='four-layer')
assert case['complete'] and all(r['path'] for r in case['routes'])
p=case['proposal'];rows=p['copper'];assert p['board_sha256']==sha(board) and not p['removed_uuids']
assert len(rows)==len({r['uuid'] for r in rows})==96 and sum(r['kind']=='via' for r in rows)==4
assert all(r['kind']=='via' or r['layer'] in ('F.Cu','In2.Cu','In3.Cu','B.Cu') for r in rows)
proposal=HERE/'proposal.json';proposal.write_text(json.dumps(p,indent=2)+'\n')
plan=dict(board='osc-jack-right',input_board_sha256=sha(board),name='189-jr131-d7411-four-layer',proposal=str(proposal.relative_to(ROOT)),proposal_sha256=sha(proposal),rail_method='rail-links',restore_connectivity=False,scope='One whole D7411.1-U7409.6 signal obligation,92segments/4vias,0cuts/moves. Preserve all51402accepted copper objects and all original pad groups. Full settled/fresh native DRC/parity and capped-warning audits remain required before adoption.')
(HERE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(ROOT/'circuit/routing/issue189/jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps(dict(screen_sha256=sha(screen),selected_net=case['net'],domain='four-layer',proposal_sha256=sha(proposal),reason='Distinct saved four-layer path after In2 native rejection split C7523.2/R7331.2. Native preservation is unproven; no original group split is allowed.',removed_copper=0,retained_copper=51402),indent=2)+'\n')
print('Prepared92segments/4vias; native NOT RUN')
