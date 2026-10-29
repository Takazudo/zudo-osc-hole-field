import argparse,csv,json,hashlib,re
from pathlib import Path
from collections import Counter,defaultdict
from decimal import Decimal
ap=argparse.ArgumentParser();ap.add_argument('parts',type=Path);ap.add_argument('accounting',type=Path);ap.add_argument('variants',type=Path);args=ap.parse_args()
parts=json.loads(args.parts.read_text());prior=json.loads(args.accounting.read_text())
def ohms(s):
 s=s.replace(' ','');m=re.fullmatch(r'([0-9.]+)([kM]?)Ω',s);assert m,s
 return Decimal(m[1])*{'':1,'k':1000,'M':1000000}[m[2]]
result={}
for v,old in prior['variant_comparison'].items():
 base=args.variants/v/'candidate/source-records';bp=base/'candidate-bom.csv';pp=base/'candidate-pin-map.csv'
 rows={r['ref']:r for r in csv.DictReader(bp.open())};pins=defaultdict(list)
 for r in csv.DictReader(pp.open()): pins[r['ref']].append(r)
 additions=old['candidate_physical_not_assigned'];missing=old['assigned_not_in_candidate_physical'];groups=defaultdict(list)
 for ref in additions:
  r=rows[ref];role=r['roles'].split(':',1)[1];assert '/series_' in role
  groups[(r['instance'],role.split('/series_')[0])].append(ref)
 chains=[];used=[]
 for ref in missing:
  if not ref.startswith('R'): continue
  src=parts[ref][0];legs=groups.pop((src['instance'],src['role']));used+=legs
  total=sum(ohms(rows[x]['value']) for x in legs);assert total==ohms(src['value'])
  degrees=Counter();adj=defaultdict(set)
  for leg in legs:
   pr=pins[leg];assert len(pr)==2 and all(x['state']=='NET' for x in pr)
   ns=[(x['net_scope'],x['resolved_label']) for x in pr]
   for n in ns: degrees[n]+=1
   adj[ns[0]].add(ns[1]);adj[ns[1]].add(ns[0])
  ends=[n for n,d in degrees.items() if d==1];assert len(ends)==2 and all(d in (1,2) for d in degrees.values())
  assert sorted(n[1] for n in ends)==sorted(src['pins'].values())
  reached={ends[0]}; todo=[ends[0]]
  while todo:
   for n in adj[todo.pop()]-reached:reached.add(n);todo.append(n)
  assert reached==set(degrees)
  chains.append({'original_ref':ref,'instance':src['instance'],'role':src['role'],'original_value':src['value'],'legs':[{'ref':x,'value':rows[x]['value'],'mpn':rows[x]['mpn']} for x in legs],'nominal_ohms':str(total),'candidate_scoped_endpoints':ends,'status':'nominal sum and connected series endpoints match; tolerance/performance not tested'})
 assert not groups and set(used)==set(additions)
 residual=[r for r in missing if not r.startswith('R')];assert len(residual)==36
 physical=[r for r in rows.values() if r['footprint'] and r['on_board']=='yes' and r['population'] in ('FITTED','DNP')]
 h=[{k:r[k] for k in ['instance','ref','value','roles']} for r in rows.values() if r['instance'] in ('H1','H2') and r['ref'].startswith('U')]
 result[v]={'replaced_resistors':len(chains),'series_legs':len(used),'series_function_counts':dict(Counter(c['role'] for c in chains)),'chains':chains,'remaining_absent_packages':[{ 'ref':r,'repository_source':parts[r]} for r in residual],'candidate_H1_H2_IC_roles':h,'candidate_physical_count':len(physical),'candidate_fitted_physical':sum(r['population']=='FITTED' for r in physical),'candidate_DNP_physical':sum(r['population']=='DNP' for r in physical),'identity_balance':f"5904 - {len(missing)} + {len(additions)} = {len(physical)}",'source_hashes':{bp.name:hashlib.sha256(bp.read_bytes()).hexdigest(),pp.name:hashlib.sha256(pp.read_bytes()).hexdigest()}}
print(json.dumps(result,indent=2))
