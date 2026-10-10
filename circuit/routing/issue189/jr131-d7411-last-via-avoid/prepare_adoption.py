"""Serialize the independently checked joint proposal; full native gates still required."""
import hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import delta
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 proof=json.loads((HERE/'native-pilot.json').read_text())
 assert proof['run']==38031328950 and proof['artifact_sha256']=='3115f9948613136ad4f6c6ef134a60a42a09e579d5c55c844bf2279a1eaeaf6c'
 assert proof['native_pilot_eligible'] and proof['fresh_agrees'] and not proof['adopted']
 plan=json.loads((HERE/'plan.json').read_text());proposal=HERE/'proposal.json';board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb'
 assert sha(board)==plan['input_board_sha256']==proof['stages']['base']['board_sha256']
 assert sha(proposal)==plan['proposal_sha256'];rows=json.loads(proposal.read_text());assert not rows['removed_uuids'] and len(rows['copper'])==172
 work=ROOT/'.circuit-cache/issue189-jr-d7411-last-via-avoid';work.mkdir(parents=True,exist_ok=True);candidate=work/board.name
 for suffix in ('.kicad_pro','.kicad_dru'):candidate.with_suffix(suffix).write_bytes(board.with_suffix(suffix).read_bytes())
 subprocess.run(['bash','scripts/kicad/run.sh','python3','scripts/pcbgen/grid_apply.py',str(board.relative_to(ROOT)),str(proposal.relative_to(ROOT)),'--output',str(candidate.relative_to(ROOT))],cwd=ROOT,check=True)
 replay=delta(board.read_text(),candidate.read_text());assert not replay['removed']
 assert {r['uuid'] for r in replay['added']}=={r['uuid'] for r in rows['copper']}
 spec=importlib.util.spec_from_file_location('guard',HERE.parent/'core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard);guard.require_known_geometry(replay['added'],rows['copper'])
 (work/'copper.json').write_text(json.dumps(replay,sort_keys=True)+'\n')
 print('Native serialized 172 additions/zero removals; full fresh and complete-warning adoption gates NOT RUN')
if __name__=='__main__':main()
