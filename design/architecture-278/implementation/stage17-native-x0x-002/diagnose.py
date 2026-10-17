import sys,json,hashlib
from pathlib import Path
base=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3')
repo=base/'osc-validation-run002'; out=base/'osc-stage17-x0x-002'
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage17_native_parity as c
expected,p=c.expected_from_source(repo)
tree=p.parse((out/'retained/netlist.net').read_text())
refs={p.one(n,'ref')[1] for n in p.children(p.one(tree,'components'),'comp')}
missing=sorted(set(expected)-refs)
report={'status':'DIAGNOSTIC ONLY; full parity remains FAIL','missing_references':missing,'missing_source_details':{r:expected[r] for r in missing}}
try:
 report['present_component_comparison']=c.compare(tree,{r:e for r,e in expected.items() if r in refs},p)
except (ValueError,KeyError,IndexError) as exc:
 report['present_component_comparison']={'status':'FAIL','error':str(exc)}
report['netlist_sha256']=hashlib.sha256((out/'retained/netlist.net').read_bytes()).hexdigest()
(out/'diagnostic-present-components.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report['present_component_comparison'],indent=2))
