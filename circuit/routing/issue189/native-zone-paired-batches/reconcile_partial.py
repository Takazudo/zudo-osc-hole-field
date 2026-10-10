"""Preserve verified partial native batches; never certify full coverage."""
import hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.zone_batch_evidence import BEFORE,AFTER,artwork_ids
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts,zone_fixture_batch_text,artwork_batches
from scripts.pcbgen.audit_added_mask import new_silk_identities
archive,before,after,output=map(Path,sys.argv[1:]);sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(archive.read_bytes())=='30bbbe4e71ba6c7e82fb4d88e135b2d30fba554c9c03ce5dfae1e6cd02bc608f'
assert [sha(p.read_bytes()) for p in (before,after)]==[BEFORE,AFTER]
texts=[p.read_text() for p in (before,after)];art=artwork_ids(texts[0]);assert art==artwork_ids(texts[1])
context={s:before.with_suffix(s).read_bytes() for s in ('.kicad_pro','.kicad_dru')};rows=[]
with zipfile.ZipFile(archive) as z:
 name=next(n for n in z.namelist() if n.endswith('/result.json') and 'paired-zone-batches/' in n);prefix=name[:-len('result.json')]
 result=json.loads(z.read(name));assert result['version']=='10.0.6' and [result['before_sha256'],result['after_sha256']]==[BEFORE,AFTER] and not result.get('zone_silk_scope_complete')
 for uid,counts in [('601e02b2-8ccb-5c28-83e5-03789d47fbbd',[9,9]),('e389d344-872d-538e-9bfc-39577adb1686',[12,5])]:
  scope=json.loads(z.read(prefix+f'zone-{uid}-scope.json'));selected=scope['selected_item_uuids'];assert set(selected)<=art
  batches=artwork_batches(selected,16);progress=[json.loads(line) for line in z.read(prefix+f'zone-{uid}-progress.jsonl').decode().splitlines()]
  expected=[(s,i,ids) for s in (0,1) for i,ids in enumerate(batches)]
  assert [(r['stage'],r['batch_index'],r['item_uuids']) for r in progress]==expected[:sum(counts)]
  assert [sum(r['stage']==s for r in progress) for s in (0,1)]==counts
  parts=[zone_fixture_parts(t,uid,art) for t in texts]
  for r in progress:
   folder=prefix+f"zone-{uid}/{r['stage']}-batch-{r['batch_index']:04d}/"
   board=z.read(folder+before.name);raw=z.read(folder+'drc.json');report=json.loads(raw)
   assert board==zone_fixture_batch_text(parts[r['stage']],r['item_uuids']).encode() and sha(board)==r['fixture_sha256']
   assert sha(raw)==r['report_sha256'] and report['kicad_version']=='10.0.6' and set(report['included_severities'])=={'error','warning','exclusion'}
   assert not new_silk_identities(report,uid) and not r['identities']
   for s,data in context.items():assert z.read(folder+before.stem+s)==data==after.with_suffix(s).read_bytes()
  rows.append(dict(uuid=uid,selected_items=len(selected),completed_per_stage=counts,required_per_stage=[len(batches)]*2,fixtures=[{k:v for k,v in r.items() if k!='fixture'} for r in progress]))
receipt=dict(status='35 OF 42 PAIRED BATCHES RECONCILED; INCOMPLETE; NOT ADOPTED',run=38005209241,source_commit='d727b49d25b4c1005b7333542e6e1b19eb247ad8',artifact=11652255919,artifact_sha256=sha(archive.read_bytes()),before_sha256=BEFORE,after_sha256=AFTER,exit_code=124,full_paired_zone_coverage=False,adopted=False,zones=rows)
output.write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status'])
