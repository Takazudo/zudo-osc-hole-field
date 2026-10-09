import hashlib,importlib.util,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
p=Path('circuit/routing/issue189/jr-three-remaining/rebase_proposal.py');spec=importlib.util.spec_from_file_location('gap_helper',p);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
root=Path('circuit/routing/issue189');source=json.loads((root/'jr140-next-no-via/result.json').read_text());yes=[t for t in source['transactions'] if t['proposal']['copper'] and not any(r['kind']=='via' for r in t['proposal']['copper'])];assert len(yes)==2;rows=[r for t in yes for r in t['proposal']['copper']];assert len(rows)==72
minimum=min(helper.gap(a,b) for i,a in enumerate(rows) for b in rows[:i]);assert minimum>=.25
board=Path('boards/osc-jack-right/osc-jack-right.kicad_pcb');sha=hashlib.sha256(board.read_bytes()).hexdigest();assert sha=='c2e6f8896869213293239912fefa64915da41fcdfa2094f082d017a88803a087';assert all(t['proposal']['board_sha256']==sha for t in yes)
p=root/'jr-two-no-via';proposal=p/'proposal.json';proposal.write_text(json.dumps({'board_sha256':sha,'removed_uuids':[],'copper':rows},indent=2)+'\n');(p/'plan.json').write_text(json.dumps({'base_sha256':sha,'proposal_sha256':hashlib.sha256(proposal.read_bytes()).hexdigest(),'scope':'Two transactions72 B.Cu segments; zero vias/cuts; native gates mandatory','nets':[t['net'] for t in yes],'minimum_new_cross_net_gap_mm':minimum},indent=2)+'\n');print(len(rows),minimum)
