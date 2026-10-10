"""Select a complete saved alternative; never modify a board or physical keepout."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(board)=='7bb70ac47e12c8bb2e2362d78f7602bdf99c2a69214c68aebeef273b0ce11965'
assert sum(map(len,copper_block_groups(board.read_text()).values()))==51402
s=json.loads((HERE/'screen.json').read_text());assert len(s['cases'])==6 and s['board_sha256']==sha(board) and s['router_sha256']==sha(ROOT/'scripts/pcbgen/grid_router.py')
positive=[c for c in s['cases'] if c['complete']];assert len(positive)==2 and all(c['exclusion']=='last' for c in positive)
a=next(c for c in positive if c['domain']=='in2');b=next(c for c in positive if c['domain']=='four-layer');assert a['routes']==b['routes']
assert [{k:v for k,v in r.items() if k!='uuid'} for r in a['proposal']['copper']]==[{k:v for k,v in r.items() if k!='uuid'} for r in b['proposal']['copper']]
rows=a['proposal']['copper'];assert len(rows)==len({r['uuid'] for r in rows})==172 and sum(r['kind']=='via' for r in rows)==5
assert not a['proposal']['removed_uuids'];assert all(r['kind']=='via' or r['layer'] in ('F.Cu','In2.Cu','B.Cu') for r in rows)
proposal=HERE/'proposal.json';proposal.write_text(json.dumps(a['proposal'],indent=2)+'\n')
plan=dict(board='osc-jack-right',input_board_sha256=sha(board),name='189-jr131-d7411-last-via-avoid',proposal=str(proposal.relative_to(ROOT)),proposal_sha256=sha(proposal),rail_method='rail-links',restore_connectivity=False,scope='Whole saved signal alternative avoiding the shared last via:167segments/5vias,0cuts/moves. Search-only exclusion is not a physical keepout. Preserve all51402accepted copper and all original native groups; zero DRC/parity and complete warnings/fresh replay remain mandatory before adoption.')
(HERE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(ROOT/'circuit/routing/issue189/jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps(dict(screen_sha256=sha(HERE/'screen.json'),proposal_sha256=sha(proposal),domain='in2',exclusion='last',positive_domains_geometry_identical=True,physical_keepouts_added=0,retained_copper=51402,removed_copper=0),indent=2)+'\n')
print('Prepared167segments/5vias; proposal',sha(proposal),'; native NOT RUN')
