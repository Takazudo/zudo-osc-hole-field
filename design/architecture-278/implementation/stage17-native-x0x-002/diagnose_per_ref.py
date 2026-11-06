import sys,json,copy
from pathlib import Path
base=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3'); repo=base/'osc-validation-run002'; out=base/'osc-stage17-x0x-002'
sys.path.insert(0,str(repo/'scripts/architecture278/implementation'))
import stage17_native_parity as c
expected,p=c.expected_from_source(repo); original=p.parse((out/'retained/netlist.net').read_text())
comps=p.children(p.one(original,'components'),'comp'); results={}
for component in comps:
 ref=p.one(component,'ref')[1]; tree=copy.deepcopy(original)
 group=p.one(tree,'components'); group[:]=['components',component]
 for net in p.children(p.one(tree,'nets'),'net'):
  name=p.one(net,'name'); name[1]=name[1].replace('{slash}','/')
  net[:]=[x for x in net if not(isinstance(x,list) and x and x[0]=='node' and p.one(x,'ref')[1]!=ref)]
 try: results[ref]=c.compare(tree,{ref:expected[ref]},p)
 except (ValueError,KeyError,IndexError) as exc: results[ref]={'status':'FAIL','error':str(exc)}
report={'status':'CONDITIONAL DIAGNOSTIC ONLY; full parity FAIL','assumption':'Decode only native {slash} tokens to /; isolate components to enumerate first mismatch per reference. Not aggregate connectivity proof.','results':results}
(out/'diagnostic-per-reference.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({r:v for r,v in results.items() if v['status']=='FAIL'},indent=2)); print('pass component count',sum(v['status'].startswith('PASS') for v in results.values()))
