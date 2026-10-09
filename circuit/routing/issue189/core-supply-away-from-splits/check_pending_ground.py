"""Compare saved complete supply cases against pending ground copper, without rebasing."""
import json,hashlib,importlib.util,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ground_rebase',HERE.parent/'core-finer-ground-batch/rebase_proposal.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
p=HERE/'proposal-original.json';g=HERE.parent/'core-finer-ground-batch/proposal.json';proposal=json.loads(p.read_text());ground=json.loads(g.read_text());selection=json.loads((HERE/'selection.json').read_text());assert proposal['board_sha256']==ground['board_sha256'];by_id={r['uuid']:r for r in proposal['copper']};cases=[]
for case in selection['selected']:
 rows=[by_id[u] for u in case['uuids']];gap=min(module.gap(a,b) for a in rows for b in ground['copper']);cases.append({'net':case['net'],'pads':case['pads'],'objects':len(rows),'uuids':case['uuids'],'minimum_gap_mm':gap if math.isfinite(gap) else None,'static_clearance_pass':gap>=.25})
result={'status':'PROPOSAL/PROPOSAL ONLY; WAIT FOR CORE37950004600; NOT AN ACCEPTED REBASE','source_proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'pending_ground_proposal_sha256':hashlib.sha256(g.read_bytes()).hexdigest(),'cases':cases,'all_static_clearance_pass':all(c['static_clearance_pass'] for c in cases)};(HERE/'pending-ground-gaps.json').write_text(json.dumps(result,indent=2)+'\n');print('cases',len(cases),'conflicts',[c for c in cases if not c['static_clearance_pass']],'minimum gap',min(c['minimum_gap_mm'] for c in cases))
