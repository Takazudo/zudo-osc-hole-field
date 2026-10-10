import collections,hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.audit_added_mask import new_silk_identities
p=Path(sys.argv[1]);z=zipfile.ZipFile(p);names=z.namelist()
def find(t):
 x=[n for n in names if n.endswith(t)];assert len(x)==1,(t,x);return x[0]
def read(t):return json.loads(z.read(find(t)))
def sha(t):return hashlib.sha256(z.read(find(t))).hexdigest()
m=read('manifest.json');out=read('comparison.json');proof={'artifact_sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'artifact_bytes':p.stat().st_size,'comparison':out,'manifest_sha256':sha('manifest.json'),'native_version':'10.0.6','adopted':False}
assert proof['artifact_sha256']=='c695ea8f653546e443daa8aba67811441b31787684e162f2583465f2dfd11601'
assert proof['manifest_sha256']=='52a0024b423e2ba1f4764f72074181efe078ac884ac9082d2ccef6c36cf1757a'
assert len(m['cases'])==18
assert sha('inputs/start/osc-core.kicad_pcb')==m['before_sha256'];assert sha('inputs/fresh/osc-core.kicad_pcb')==m['after_sha256'];assert sha('original-inline.py')==m['baseline_file_sha256']
proof['source_board_hashes']={'before':m['before_sha256'],'after':m['after_sha256']};proof['baseline_sha256']=m['baseline_file_sha256'];proof['case_counts']={};proof['reports']=[]
def rows(report):return sorted((v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in report['violations'])
def scoped(report,c):
 assert report['kicad_version']=='10.0.6';assert set(report['included_severities'])=={'error','warning','exclusion'}
 return sorted((v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in new_silk_identities(report,c['zone_uuid']))
for i,c in enumerate(m['cases']):
 assert sha(f'inputs/case-{i:02d}/osc-core.kicad_pcb')==c['fixture_sha256']
 if c['saved_report_sha256']:assert sha(f'inputs/case-{i:02d}/saved-drc.json')==c['saved_report_sha256']
for mode in ('original','isolated'):
 partial=[n for n in names if n.endswith(f'{mode}/partial.json')];complete=[n for n in names if n.endswith(f'{mode}/complete.json')]
 receipts=read(f'{mode}/partial.json') if partial else [];proof['case_counts'][mode]=len(receipts)
 if complete:assert read(f'{mode}/complete.json')['cases']==receipts
 for r in receipts:
  c=m['cases'][r['case']];i=r['case'];assert r['version']=='10.0.6';assert r['fixture_sha256']==c['fixture_sha256'];assert r['native_geometry_sha256']==c['native_geometry_sha256'];assert sha(f'{mode}/case-{i:02d}/osc-core.kicad_pcb')==c['fixture_sha256']
  for suffix in ('.kicad_pro','.kicad_dru'):assert z.read(find(f'{mode}/case-{i:02d}/osc-core{suffix}'))==z.read(find(f'inputs/start/osc-core{suffix}'))
  if mode=='isolated':
   worker=read(f'{mode}/case-{i:02d}/native-validation.json');assert worker['fixture_sha256']==c['fixture_sha256'];assert worker['native_geometry_sha256']==c['native_geometry_sha256'];assert worker['version']=='10.0.6'
  if c['layer']=='B.Cu':
   raw=read(f'{mode}/case-{i:02d}/new-drc.json');assert sha(f'{mode}/case-{i:02d}/new-drc.json')==r['report_sha256'];assert json.loads(json.dumps(scoped(raw,c)))==r['zone_silk_identities'];assert json.loads(json.dumps(rows(raw)))==r['reported_native_identities'];assert r['other_warning_domains_complete'] is False
   if c['saved_report_sha256']:
    saved=read(f'inputs/case-{i:02d}/saved-drc.json');assert rows(raw)==rows(saved);assert scoped(raw,c)==scoped(saved,c)
   proof['reports'].append({'mode':mode,'case':i,'batch_index':c['batch_index'],'sha256':r['report_sha256'],'scoped_identities':len(scoped(raw,c)),'raw_warning_counts':dict(collections.Counter(v['type'] for v in raw['violations'] if v['severity']=='warning')),'raw_error_count':sum(v['severity']=='error' for v in raw['violations'])})
 if complete:assert len(receipts)==18
if out['status'].startswith('18CONTROLS_EQUIVALENT'):
 a=read('original/complete.json')['cases'];b=read('isolated/complete.json')['cases'];assert len(a)==len(b)==18
 for x,y in zip(a,b):assert {k:v for k,v in x.items() if k!='report_sha256'}=={k:v for k,v in y.items() if k!='report_sha256'}
 assert len(proof['reports'])==4
telemetry=[json.loads(l) for l in z.read(find('telemetry.jsonl')).decode().splitlines()];proof['telemetry']={}
for mode in ('original','isolated'):
 samples=[s for s in telemetry if s['mode']==mode and 'phase' not in s];after=[s for s in telemetry if s['mode']==mode and s.get('phase')=='after_cleanup']
 if not samples:continue
 assert len(after)==1;assert after[0]['owned_containers_remaining']==[];assert after[0]['tree_rss_kib']=={}
 proof['telemetry'][mode]={'samples':len(samples),'peak_tree_rss_kib':max(s['total_rss_kib'] for s in samples),'minimum_available_kib':min(s['available_kib'] for s in samples),'elapsed_sample_seconds':after[0]['epoch']-samples[0]['epoch'],'cleanup':after[0]}
proof['reconciliation']='PASS; exact archived inputs, frozen baseline, completed receipt/report/context checks and owned cleanup verified';proof['full_warning_coverage']=False;proof['full_stability_established']=False
print(json.dumps(proof,indent=2))
