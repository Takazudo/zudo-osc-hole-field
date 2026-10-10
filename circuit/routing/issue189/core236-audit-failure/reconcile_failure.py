"""Read-only failed audit diagnosis: exact raw reports/fixtures and telemetry."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.audit_zone_silk_scope import artwork_batches,zone_fixture_parts,zone_fixture_batch_text
from scripts.pcbgen.zone_batch_evidence import artwork_ids
from scripts.pcbgen.audit_added_mask import new_silk_identities
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads(Path('/tmp/issue189-core236-failure-failure-inventory.json').read_text());inventory={r['path']:r for r in manifest['inventory']}
assert manifest['archive_sha256']=='2cd2463554fdd63a672bf3b59dae5e3473a960017f51c142f9fc0fd7e4ebeaf4' and manifest['archive_bytes']==630799591
diagnostics=Path('/tmp/issue189-core236-failure-diagnostics.zip');assert sha(diagnostics.read_bytes())==manifest['diagnostics_sha256']
sources=[];context=[]
with zipfile.ZipFile('/tmp/issue189-core236-reconciliation-inputs.zip') as z:
 for stage,digest in [('start','b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'),('fresh','f27efe521f4ed4f6c0ceb53f45f58a82a824c05475ef012a2034a0d1d2a154d1')]:
  suffix='osc-core-grid-shards-'+stage+'/osc-core';names={s:next(n for n in z.namelist() if n.endswith(suffix+s)) for s in ('.kicad_pcb','.kicad_pro','.kicad_dru')};raw=z.read(names['.kicad_pcb']);assert sha(raw)==digest;sources.append(raw.decode());context.append({s:sha(z.read(names[s])) for s in ('.kicad_pro','.kicad_dru')})
assert context[0]==context[1]
with zipfile.ZipFile(diagnostics) as z:
 for n in z.namelist():assert len(z.read(n))==inventory[n]['bytes'] and sha(z.read(n))==inventory[n]['sha256']
 find=lambda suffix:next(n for n in z.namelist() if n.endswith(suffix))
 result=json.loads(z.read(find('core236-zone-recovery/result.json')));assert result['status']=='STARTED; NO COMPLETE ZONE EVIDENCE' and result['version']=='10.0.6'
 assert result['before_sha256']=='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66' and result['after_sha256']=='f27efe521f4ed4f6c0ceb53f45f58a82a824c05475ef012a2034a0d1d2a154d1'
 summaries=[]
 for scope_name in sorted(n for n in z.namelist() if n.endswith('-scope.json')):
  scope=json.loads(z.read(scope_name));uid=scope['zone_uuid'];batches=artwork_batches(scope['selected_item_uuids'],16)
  rows=[json.loads(l) for l in z.read(find('zone-'+uid+'-progress.jsonl')).decode().splitlines()];expected=[(s,i,b) for s in (0,1) for i,b in enumerate(batches)]
  assert [(r['stage'],r['batch_index'],r['item_uuids']) for r in rows]==expected[:len(rows)]
  parts=[zone_fixture_parts(t,uid,artwork_ids(t)) for t in sources]
  for row in rows:
   folder=f"core236-zone-recovery/zone-{uid}/{row['stage']}-batch-{row['batch_index']:04d}/";fixture=zone_fixture_batch_text(parts[row['stage']],row['item_uuids']).encode()
   assert sha(fixture)==row['fixture_sha256']==inventory[folder+'osc-core.kicad_pcb']['sha256']
   report_raw=z.read(folder+'drc.json');assert sha(report_raw)==row['report_sha256'];report=json.loads(report_raw)
   assert report['kicad_version']=='10.0.6' and set(report['included_severities'])=={'error','warning','exclusion'}
   for s,digest in context[row['stage']].items():assert inventory[folder+'osc-core'+s]['sha256']==digest
   actual={(v['type'],v['severity'],tuple(sorted(i['uuid'] for i in v['items']))) for v in new_silk_identities(report,uid)};assert actual=={(a,b,tuple(ids)) for a,b,ids in row['identities']}
  entry=dict(zone_uuid=uid,layer=scope['layer'],selected_artwork=len(scope['selected_item_uuids']),planned_paired_batches=len(expected),verified_prefix=len(rows),missing=len(expected)-len(rows))
  if len(rows)<len(expected):
   stage,index,items=expected[len(rows)];folder=f'core236-zone-recovery/zone-{uid}/{stage}-batch-{index:04d}/';fixture=zone_fixture_batch_text(parts[stage],items).encode()
   assert sha(fixture)==inventory[folder+'osc-core.kicad_pcb']['sha256'];assert folder+'drc.json' not in inventory
   entry['stopped_operation']=dict(stage=stage,batch_index=index,fixture_path=folder+'osc-core.kicad_pcb',fixture_sha256=sha(fixture),fixture_bytes=len(fixture),item_uuids=items,native_DRC_report='ABSENT; NO COMPLETED RECEIPT')
  summaries.append(entry)
 rows=[json.loads(l) for l in z.read(find('resource.jsonl')).decode().splitlines()];samples=[]
 for r in rows:
  mem={k:int(v) for k,v in re.findall(r'^(\w+):\s+(\d+)',r['/proc/meminfo'],re.M)}
  for line in r['largest_processes'][1:]:
   fields=line.split()
   if len(fields)==5 and fields[0]=='2709':samples.append(dict(epoch=r['utc_epoch'],rss_kib=int(fields[3]),vsz_kib=int(fields[4]),mem_available_kib=mem['MemAvailable'],swap_free_kib=mem['SwapFree']))
 min_available=min(int(re.search(r'MemAvailable:\s+(\d+)',r['/proc/meminfo'])[1]) for r in rows)
 proof=dict(status='FAILED AUDIT EVIDENCE RECONCILED; NO RETRY OR ADOPTION',source='617082dc9b7a7f457fd3363b6999d6bb2f341dc5',run=38058774479,artifact=11673646039,archive_sha256=manifest['archive_sha256'],inspection_run=38062381542,export_artifact=11673986827,export_sha256='c6ae91f2848f6a164983847e8ba78c0729238968cd905caa759eda25efc28e7e',before_sha256=result['before_sha256'],after_sha256=result['after_sha256'],zones=summaries,telemetry=dict(samples=len(rows),native_auditor_pid=2709,first_auditor=samples[0],peak_auditor=max(samples,key=lambda s:s['rss_kib']),last_auditor=samples[-1],min_mem_available_kib=min_available,minimum_disk_free_bytes=min(r['disk']['free'] for r in rows),cgroup_events='NOT CAPTURED; NO CGROUP FIELDS AVAILABLE',wall_time='42:04.96',wrapper_maxRSS_kib=30256,wrapper_RSS_is_not_native_auditor_RSS=True),diagnosis='Severe memory pressure and growth in long-lived native auditor observed; exact allocation defect and kernel OOM decision unproven',remaining_native_gates='Full zone/warning/promotion/publication INCOMPLETE; later coverage unknown; no copper adopted')
 Path('/tmp/issue189-core236-audit-failure-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps(proof,indent=2))
