import sys,json,collections
from pathlib import Path
base=Path('/mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3'); repo=base/'osc-validation-run002'; out=base/'osc-stage17-x0x-002'
sys.path.insert(0,str(repo/'scripts/architecture278/implementation')); import stage17_native_parity as c
expected,p=c.expected_from_source(repo); t=p.parse((out/'retained/netlist.net').read_text())
obs={}; duplicated=[]; names=collections.Counter()
for net in p.children(p.one(t,'nets'),'net'):
 name=p.one(net,'name')[1]; nodes=p.children(net,'node'); names[name]+=len(nodes)
 for n in nodes:
  key=(p.one(n,'ref')[1],p.one(n,'pin')[1])
  if key in obs: duplicated.append(key)
  obs[key]=name
rows=[]
for r,e in expected.items():
 for pin,wanted in e['pins'].items():
  raw=obs.get((r,pin)); decoded=raw.replace('{slash}','/') if raw else raw
  if wanted is None: status='NC_OMITTED' if raw is None else ('NC_SINGLETON' if raw.startswith('unconnected-') and names[raw]==1 else 'NC_CONNECTED_MISMATCH')
  else: status='EXACT' if raw==wanted else ('SLASH_ENCODING_ONLY' if decoded==wanted else ('ABSENT' if raw is None else 'NET_MISMATCH'))
  rows.append({'reference':r,'pin':pin,'expected':wanted,'native_raw':raw,'native_slash_decoded':decoded,'classification':status})
report={'status':'OBSERVATION ONLY; full strict parity FAIL','normalization':'Only literal {slash} -> / is applied for the conditional encoding column; raw names preserved.','counts':dict(collections.Counter(x['classification'] for x in rows)),'duplicates':duplicated,'unexpected_endpoints':[list(k) for k in obs if k[0] not in expected or k[1] not in expected[k[0]]['pins']],'pins':rows}
(out/'pin-classification.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report['counts']))
