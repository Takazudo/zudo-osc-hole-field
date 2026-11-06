import sys,json,csv
from pathlib import Path
from collections import Counter,defaultdict
repo=Path(sys.argv[1]);variants=Path(sys.argv[2]);sys.dont_write_bytecode=True;sys.path.insert(0,str(repo))
from design.spec.modules.sample_hold import specification
from scripts.schgen.core import designator
from design.spec.modules.io_partition import AMP_MAPS,region
fs,ins=specification();f=fs[0]
source=[];caps=[];packages={}
for i in ins:
 for p in f.parts:
  ref=designator(p,i)
  if p.prefix=='U':
   packages.setdefault((i.name,ref),{'mpn':p.value,'units':[]})['units'].append({'unit':p.unit,'role':p.attributes.get('Role'),'region':p.attributes.get('BoardRegion'),'pins':p.pins})
  if 'C_DEC_' in p.key: caps.append({'instance':i.name,'ref':ref,'pins':p.pins,'owner':p.attributes.get('Decouples'),'region':p.attributes.get('BoardRegion'),'value':p.value})
  if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')) and p.unit in range(1,5):
   nets=[p.pins[k] for k in AMP_MAPS[p.unit-1]]
   source.append({'instance':i.name,'ref':ref,'unit':p.unit,'device':p.value,'role':p.attributes.get('Role'),'region':p.attributes.get('BoardRegion'),'nets_out_minus_plus':nets,'spare':nets[0]==nets[1] and nets[2]=='AGND'})
results={}
for v in ['UNI_ROYAL/BA1','UNI_ROYAL/RevP','YAGEO/BA1','YAGEO/RevP']:
 base=variants/v/'candidate/source-records';bom={r['ref']:r for r in csv.DictReader((base/'candidate-bom.csv').open()) if r['instance'] in ('H1','H2')};pr=defaultdict(dict);roles={};scopes=defaultdict(dict)
 for r in csv.DictReader((base/'candidate-pin-map.csv').open()):
  if r['instance'] not in ('H1','H2'):continue
  key=(r['instance'],r['ref'],int(r['unit']));pr[key][r['pin']]=r['resolved_label'] if r['state']=='NET' else None;roles[key]=r['role'];scopes[key][r['pin']]=r['net_scope']
 channels=[]
 for (inst,ref,u),pins in pr.items():
  dev=bom[ref]['mpn'] or bom[ref]['value']
  if dev not in ('OPA4196IDR','OPA4197IPWR','TL074HIDR') or u not in range(1,5):continue
  nets=[pins[k] for k in AMP_MAPS[u-1]]
  channels.append({'instance':inst,'ref':ref,'unit':u,'device':dev,'role':roles[inst,ref,u],'nets_out_minus_plus':nets,'net_scopes':[scopes[inst,ref,u][k] for k in AMP_MAPS[u-1]],'spare':nets[0]==nets[1] and nets[2]=='AGND'})
 sig=lambda c:(c['instance'],*c['nets_out_minus_plus'])
 old=defaultdict(list);new=defaultdict(list)
 for c in source:
  if not c['spare']:old[sig(c)].append(c)
 for c in channels:
  if not c['spare']:new[sig(c)].append(c)
 matched=[]
 for k in old.keys()&new.keys():
  assert len(old[k])==len(new[k])==1
  matched.append({'repository':old[k][0],'candidate':new[k][0],'same_device':old[k][0]['device']==new[k][0]['device']})
 supply=[]
 for (inst,ref,u),pins in pr.items():
  if ref.startswith('U') and any(k in pins for k in ('4','11')) and (bom[ref]['mpn'] or bom[ref]['value']) in ('OPA4196IDR','OPA4197IPWR','TL074HIDR') and u==5:supply.append({'instance':inst,'ref':ref,'device':bom[ref]['mpn'],'pins':pins})
 results[v]={'repository_active_channels':sum(not c['spare'] for c in source),'candidate_active_channels':sum(not c['spare'] for c in channels),'matched_net_tuples':matched,'repository_unmatched':[c for k in old.keys()-new.keys() for c in old[k]],'candidate_unmatched':[c for k in new.keys()-old.keys() for c in new[k]],'candidate_channels':channels,'candidate_amp_supplies':supply,'candidate_bypass_rows':[{k:r[k] for k in ('ref','value','roles')} for r in bom.values() if 'C_DEC_' in r['roles']]}
print(json.dumps({'repository_packages':{str(k):v for k,v in packages.items()},'repository_channels':source,'repository_bypasses':caps,'variants':results},indent=2))
