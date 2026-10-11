"""Select one whole bounded route; preserve all accepted copper and native obligations."""
import hashlib,importlib.util,itertools,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups
spec=importlib.util.spec_from_file_location('geometry_guard',HERE.parent/'core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();board=ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb';assert sha(board)=='a01df89dcab3d4fab8eb0ae80195b2825d2d47adc517cd73452d9b9aa6ea079a'
assert sum(map(len,copper_block_groups(board.read_text()).values()))==33421
s=json.loads((HERE/'weighted-5m-result.json').read_text());assert len(s['cases'])==10 and s['maximum_expansions']==5000000 and s['astar_weight']==2.5
assert s['board_sha256']==sha(board) and s['router_sha256']==sha(ROOT/'scripts/pcbgen/grid_router.py')
positive=[c for c in s['cases'] if c['complete']];assert len(positive)==4
comparisons=[]
for a,b in itertools.combinations(positive,2):
 if a['net']==b['net']:continue
 gap=min(guard.gap(x,y) for x in a['proposal']['copper'] for y in b['proposal']['copper']);comparisons.append({'a':[a['net'],a['domain']],'b':[b['net'],b['domain']],'minimum_gap_mm':gap});assert gap<.25
selected=min(positive,key=lambda c:len(c['proposal']['copper']));assert selected['net']=='XB8780C34DCDC50D9A9BA' and selected['domain']=='in3'
rows=selected['proposal']['copper'];assert len(rows)==len({r['uuid'] for r in rows})==99 and not selected['proposal']['removed_uuids'];assert all(r['kind']=='via' or r['layer'] in ('F.Cu','In3.Cu','B.Cu') for r in rows)
proposal=HERE/'proposal.json';proposal.write_text(json.dumps(selected['proposal'],indent=2)+'\n')
plan=dict(board='osc-jack-left',input_board_sha256=sha(board),name='189-jl118-u8215-bounded',proposal=str(proposal.relative_to(ROOT)),proposal_sha256=sha(proposal),rail_method='rail-links',restore_connectivity=False,scope='One whole saved U8215.5-U8216.12 In3 route,99objects,zero cuts/moves. Other positive routes conflict and are excluded whole. Preserve all33421old copper and all original native pad groups; full native/fresh/complete-warning gates mandatory before adoption.')
(HERE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(ROOT/'circuit/routing/issue189/jl-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps({'input_board_sha256':sha(board),'screen_sha256':sha(HERE/'weighted-5m-result.json'),'proposal_sha256':sha(proposal),'selected_net':selected['net'],'domain':selected['domain'],'segments':sum(r['kind']=='segment' for r in rows),'vias':sum(r['kind']=='via' for r in rows),'whole_case_comparisons':comparisons,'retained_copper':33421,'removed_copper':0},indent=2)+'\n')
print('Selected',len(rows),'objects;',sum(r['kind']=='via' for r in rows),'vias; native NOT RUN')
