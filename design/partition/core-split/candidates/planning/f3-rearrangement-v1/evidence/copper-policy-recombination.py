import json,gzip,hashlib,time
from pathlib import Path
from collections import defaultdict
import shapely
from shapely.geometry import shape,mapping
from shapely.ops import unary_union
root=Path('/workspace/zudo-osc-hole-field');p=Path('/tmp/f3-rearrange-pad-regions-1');reg=root/'design/partition/core-split/candidates/planning/f3-rearrangement-v1/evidence/regions/A24-N-result.json'
paths=[reg,p/'A24-N-result.json',p/'A24-N-constraints.json.gz',root/'design/partition/core-split/candidates/copper-index.jsonl.gz',root/'design/reports/board-net-tokens.json']
seals={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in paths};start=time.monotonic();assert shapely.__version__=='2.1.2'
rows={':'.join(map(str,x['source_span']))+':'+x['sha256']:x for x in map(json.loads,gzip.open(paths[-2],'rt'))};tokens=json.loads(paths[-1].read_text());cs=json.loads(gzip.decompress(paths[2].read_bytes()));available=shape(json.loads(reg.read_text())['robust_external_free']);groups=defaultdict(list)
for i,c in enumerate(cs):
 r=rows.get(c['fixed_id']);net=tokens[r['net_token']] if r else c['kind'];c['net_family']=net;c['source_object']=r;c['index']=i;c['lo']=shape(c['lower']);c['hi']=shape(c['upper']);groups[net].append(c)
def coverage(sub):
 lo=unary_union([c['lo'] for c in sub]);hi=unary_union([c['hi'] for c in sub]);free=available.difference(hi.buffer(.001,quad_segs=32));uncovered=available.difference(lo)
 return {'constraints':len(sub),'unique_fixed_objects':len({c['fixed_id'] for c in sub}),'lower_covers_available':lo.covers(available) and uncovered.is_empty,'lower_uncovered_area_mm2':uncovered.area,'guarded_remaining_area_mm2':free.area,'guarded_remaining_region':mapping(free)}
family=[]
for n,sub in sorted(groups.items()):
 alone=coverage(sub);released=coverage([c for c in cs if c['net_family']!=n]);family.append({'family':n,'alone':alone,'after_release_this_family':released,'objects':[rows[k]|{'object_key':k} if k in rows else {'fixed_pad_uuid':k} for k in sorted({c['fixed_id'] for c in sub})],'moving_pad_refs':sorted({c['ref'] for c in sub})})
rails={'+12V','-12V','+5V','AGND'};policies={
 'release_shared_rail_objects_only':rails,
 'release_nonrail_copper_objects_only':set(groups)-rails-{'FOREIGN_PAD'},
 'release_all_copper_objects_keep_fixed_pad':set(groups)-{'FOREIGN_PAD'},
 'release_rails_and_F3_only_keep_foreign_signals':rails|{n for n in groups if n.startswith('/F3/')},
}
pol=[{'policy':k,'release_net_families':sorted(v),'remaining':coverage([c for c in cs if c['net_family'] not in v])} for k,v in policies.items()]
out={'status':'SAVED_CONSTRAINT_RECOMBINATION_ONLY_NO_POSE_OR_RECONSTRUCTION','source_sha256':seals,'available_area_mm2':available.area,'full':coverage(cs),'families':family,'policies':pol,'scope':'Recombines already constructed exclusion polygons. Releasing a family means ignoring its existing pad-conflict constraints hypothetically, not deleting copper, proving reconstruction, or establishing full eligibility. No new placement/pad/copper geometry generated.','elapsed_seconds':time.monotonic()-start,'shapely':shapely.__version__,'geos':shapely.geos_version_string}
for x in paths:assert hashlib.sha256(x.read_bytes()).hexdigest()==seals[str(x)]
path=Path('/tmp/f3-rearrangement-copper-policy-review.json');path.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
print('available',available.area)
for r in family:print(r['family'],r['alone']['constraints'],r['alone']['unique_fixed_objects'],'alone covers',r['alone']['lower_covers_available'],'release free',r['after_release_this_family']['guarded_remaining_area_mm2'],'remaining covers',r['after_release_this_family']['lower_covers_available'])
for x in pol:print(x['policy'],x['remaining']['guarded_remaining_area_mm2'],x['remaining']['lower_covers_available'])
print('elapsed',out['elapsed_seconds'],'output',path)
