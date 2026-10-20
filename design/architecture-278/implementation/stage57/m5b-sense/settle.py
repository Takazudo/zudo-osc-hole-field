"""Bind two independently built Stage57 reroute copies (Stage53 settle rule, Stage57 gate)."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from accept import read,sha,signature,evaluate

def settle(baseline,first,fresh,proposal,output,check=False):
 snapshots=[read(p/f'connectivity-{label}.json') for p,label in [(first,'pass1'),(fresh,'passfresh')]]
 accepts=[read(p/f'acceptance-{label}.json') for p,label in [(first,'pass1'),(fresh,'passfresh')]]
 for folder,label,accepted in [(first,'pass1',accepts[0]),(fresh,'passfresh',accepts[1])]:
  if evaluate(baseline,folder,proposal,label)!=accepted:raise ValueError('stored acceptance does not replay')
 boards=[p/'osc-jack-left.kicad_pcb' for p in [first,fresh]]
 hashes=[sha(p) for p in boards]
 if hashes[0]!=hashes[1] or any(s['board_sha256']!=hashes[0] for s in snapshots):raise ValueError('fresh board bytes differ')
 if snapshots[0]!=snapshots[1]:raise ValueError('fresh full native snapshot differs')
 if any(not a['accepted_bounded_native_repair'] or a['candidate_sha256']!=hashes[0] or a['proposal_sha256']!=sha(proposal) for a in accepts):raise ValueError('acceptance binding')
 if accepts[0]!=accepts[1]:raise ValueError('fresh acceptance differs')
 bindings={}
 for folder,label in [(first,'pass1'),(fresh,'passfresh')]:
  for name in ['osc-jack-left.kicad_pcb',f'drc-{label}.json',f'drc-{label}.json.execution.json',f'connectivity-{label}.json',f'acceptance-{label}.json']:
   p=folder/name;bindings[str(p)]=sha(p)
 for p in [baseline/'osc-jack-left.kicad_pcb',baseline/'connectivity-passfresh.json',baseline/'drc-passfresh.json',baseline/'drc-passfresh.json.execution.json',proposal]:bindings[str(p)]=sha(p)
 result=dict(accepted_bounded_native_repair=True,candidate_sha256=hashes[0],baseline_sha256=sha(baseline/'osc-jack-left.kicad_pcb'),proposal_sha256=sha(proposal),independent_native_builds=2,complete_snapshot_sha256=sha(first/'connectivity-pass1.json'),native_object_count=len(snapshots[0]['objects']),identity=accepts[0]['identity'],connectivity=accepts[0]['connectivity'],drc=accepts[0]['drc'],warning_comparison=accepts[0]['warning_comparison'],evidence_sha256=bindings,limits='114 opens remain. Capped silkscreen warning identity nonregression remains unresolved. Disposable design study only; no canonical adoption, manufacturing or physical/electrical qualification.')
 text=json.dumps(result,indent=2,sort_keys=True)+'\n'
 if check:
  if output.read_text()!=text:raise ValueError('settlement replay drift')
 else:
  if output.exists():raise ValueError('do not overwrite settlement')
  output.write_text(text)
 print(json.dumps({'accepted':True,'candidate_sha256':hashes[0],'independent_native_builds':2,'read_only_check':check}))
if __name__=='__main__':settle(*(Path(p) for p in sys.argv[1:] if p!='--check'),check='--check' in sys.argv)
