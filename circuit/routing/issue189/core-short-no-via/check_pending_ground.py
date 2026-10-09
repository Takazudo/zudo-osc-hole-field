"""Static proposal comparison only; never treats pending ground copper as accepted."""
import json,importlib.util,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('ground_rebase',HERE.parent/'core-finer-ground-batch/rebase_proposal.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
signal=json.loads((HERE/'proposal-original.json').read_text());ground=json.loads((HERE.parent/'core-finer-ground-batch/proposal.json').read_text());assert signal['board_sha256']==ground['board_sha256'];cases=[]
for net in sorted({r['net'] for r in signal['copper']}):
 rows=[r for r in signal['copper'] if r['net']==net];gap=min(module.gap(a,b) for a in rows for b in ground['copper']);cases.append({'net':net,'objects':len(rows),'minimum_gap_mm':gap if math.isfinite(gap) else None,'static_clearance_pass':gap>=.25})
(HERE/'pending-ground-gaps.json').write_text(json.dumps({'status':'PROPOSAL/PROPOSAL ONLY; CORE37950004600 STILL MUST BE RECONCILED; NOT AN ACCEPTED REBASE','cases':cases,'all_static_clearance_pass':all(x['static_clearance_pass'] for x in cases)},indent=2)+'\n');print(cases)
