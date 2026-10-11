"""Pin the sole whole JL layer-domain candidate for a read-only native pilot."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
screen=json.loads((HERE/'result.json').read_text());success=[c for c in screen['cases'] if c['complete']]
assert len(screen['cases'])==8 and len(success)==1
case=success[0];assert case['net']=='X632AF8DD6216ED26A96D' and case['inner_layer']=='In2.Cu'
proposal=case['proposal'];assert not proposal['removed_uuids']
rows=proposal['copper'];assert len(rows)==115 and len({r['uuid'] for r in rows})==115
assert sum(r['kind']=='via' for r in rows)==4
assert all(r['net']==case['net'] and (r['kind']=='via' or r['layer'] in ('F.Cu','In2.Cu','B.Cu')) for r in rows)
source=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';assert sha(source)==proposal['board_sha256']==screen['board_sha256']
path=HERE/'proposal.json';path.write_text(json.dumps(proposal,indent=2)+'\n')
plan=dict(board='osc-jack-left',input_board_sha256=sha(source),name='189-jl118-u2119-in2-only',proposal=str(path.relative_to(ROOT)),proposal_sha256=sha(path),rail_method='rail-links',restore_connectivity=False,scope='One complete U2119.12-U2117.13 signal obligation:111segments/4vias on F/In2/B,0cuts/moves, same0.025mm/300000budget as failed four-layer saved trial. Native original groups, retained copper, DRC/parity, warnings and settled/fresh mandatory; no automatic restoration or publication. Full capped-warning evidence still mandatory before any later adoption.')
(HERE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(ROOT/'circuit/routing/issue189/jl-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared111segments/4vias,0cuts/moves; native NOT RUN')
