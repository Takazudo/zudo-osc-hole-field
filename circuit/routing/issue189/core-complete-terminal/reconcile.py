"""Reconcile rejected core evidence; extract completed audit sections, never adopt."""
import collections,hashlib,json,sys,zipfile
from pathlib import Path,PurePosixPath
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.audit_added_mask import unchanged_nonrouting,new_silk_identities
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata,zone_fixture_parts,zone_fixture_text
from scripts.pcbgen.zone_batch_evidence import artwork_ids
archive=Path(sys.argv[1]);destination=Path(sys.argv[2]);output=Path(sys.argv[3]);sha=lambda b:hashlib.sha256(b).hexdigest()
with archive.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()=='b5c112a5c9336a27cb08369ec42a11b7cc51a39bb569215d24075ccd3ab11567'
with zipfile.ZipFile(archive) as z:
 root='.circuit-cache/';audit=root+'osc-core-grid-shards-complete-warnings/native-audits/';read=lambda n:json.loads(z.read(n))
 receipt_name=next(n for n in z.namelist() if n.endswith('/shards-issue189-finer-ground-complete-warnings.json'));receipt=read(receipt_name)
 assert not receipt['adopted'] and receipt['rejection_reason']=='incomplete_native_warning_evidence'
 assert 'exit status 137' in receipt['native_warning_evidence_error']
 replay=next(n for n in z.namelist() if n.endswith('/shards-issue189-finer-ground-complete-warnings-copper.json'))
 assert sha(z.read(replay))=='25a3de5583c9bb61611a4e46d9463a581a09cba43c1dc23bf2d45c5203a3b08c'
 paths={s:root+f'osc-core-grid-shards-{s}/' for s in ('start','merge','fresh')}
 dumps={s:read(p+'dump.json') for s,p in paths.items()};reports={s:read(p+'drc.json') for s,p in paths.items()}
 texts={s:z.read(p+'osc-core.kicad_pcb').decode() for s,p in paths.items()};hashes={s:sha(t.encode()) for s,t in texts.items()}
 assert hashes['start']=='95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5'
 assert hashes['merge']==hashes['fresh']==receipt['candidate_board_sha256']=='b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'
 context={s:z.read(paths['start']+'osc-core'+s) for s in ('.kicad_pro','.kicad_dru')}
 for stage,p in paths.items():
  assert dumps[stage]['board_sha256']==hashes[stage]
  assert reports[stage]['kicad_version']=='10.0.6' and not reports[stage]['schematic_parity']
  assert not any(v['severity']=='error' for v in reports[stage]['violations'])
  for suffix,data in context.items():assert z.read(p+'osc-core'+suffix)==data
  for key in ('pads','edges','keepouts','layers'):assert dumps[stage][key]==dumps['start'][key]
 assert dumps['start']['open_edges']==1441 and dumps['fresh']['open_edges']==1402
 assert connectivity_signature(dumps['merge'])==connectivity_signature(dumps['fresh'])
 gate=json.loads(json.dumps(promotion_gate(dumps['start'],dumps['fresh'],reports['start'],reports['fresh'])))
 assert gate==receipt['raw_promotion_gate'] and not gate['adopted'] and not gate['split_pad_groups']
 copper={s:collections.Counter(b for group in copper_block_groups(texts[s]).values() for b in group) for s in ('start','fresh')}
 assert sum(copper['start'].values())==133169 and not copper['start']-copper['fresh']
 additions=copper['fresh']-copper['start'];assert sum(additions.values())==382
 assert sum(n for b,n in additions.items() if b[2].startswith('(segment'))==344
 assert sum(n for b,n in additions.items() if b[2].startswith('(via'))==38
 assert unchanged_nonrouting(texts['start'],texts['fresh'])==3807
 assert zone_metadata(texts['start'])==zone_metadata(texts['fresh'])
 zone=read(audit+'zones/result.json');assert zone['status']=='STARTED; NO COMPLETE ZONE EVIDENCE' and not zone.get('zone_silk_scope_complete')
 uid='601e02b2-8ccb-5c28-83e5-03789d47fbbd';zr=audit+'zones/'
 selected=read(zr+f'zone-{uid}-scope.json')['selected_item_uuids'];assert len(selected)==144
 progress=[json.loads(line) for line in z.read(zr+f'zone-{uid}-progress.jsonl').decode().splitlines()];assert len(progress)==217
 parts={stage:zone_fixture_parts(texts[name],uid,artwork_ids(texts[name])) for stage,name in [(0,'start'),(1,'fresh')]}
 completed=collections.Counter();seen=set()
 for row in progress:
  stage=row['stage'];item=row['item_uuid'];assert (stage,item) not in seen;seen.add((stage,item));completed[stage]+=1
  folder=zr+f'zone-{uid}/{stage}-{selected.index(item):04d}/'
  board=z.read(folder+'osc-core.kicad_pcb');report=z.read(folder+'drc.json')
  assert sha(board)==row['fixture_sha256'] and board==zone_fixture_text(parts[stage],item).encode()
  assert sha(report)==row['report_sha256'];raw=json.loads(report);assert raw['kicad_version']=='10.0.6'
  actual={(r['type'],r['severity'],tuple(sorted(i['uuid'] for i in r['items']))) for r in new_silk_identities(raw,uid)}
  assert actual=={(a,b,tuple(ids)) for a,b,ids in row['identities']}==set()
  for suffix,data in context.items():assert z.read(folder+'osc-core'+suffix)==data
 assert completed=={0:144,1:73}
 destination.mkdir(parents=True,exist_ok=False);extracted=[]
 for info in z.infolist():
  name=info.filename
  keep=any(name.startswith(audit+section+'/') for section in ('holes-before','holes-after','silk'))
  keep=keep or any(name==p+f for p in paths.values() for f in ('drc.json','dump.json','osc-core.kicad_pro','osc-core.kicad_dru'))
  if not keep or name.endswith('/'):continue
  rel=PurePosixPath(name);assert not rel.is_absolute() and '..' not in rel.parts and (info.external_attr>>16)&0o170000!=0o120000
  data=z.read(name);target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  extracted.append(dict(path=name,size=len(data),sha256=sha(data)))
 result=dict(status='REJECTED CORE ARTIFACT RECONCILED; NOT ADOPTED',run=37984573591,
  source_commit='a89ff33adc26675b7cdf2f22616dcb1a9826cb59',bot_commit='ff6faebab30c5fbb97682ce0cd62569d3b1d9843',
  artifact=11650664778,artifact_sha256='b5c112a5c9336a27cb08369ec42a11b7cc51a39bb569215d24075ccd3ab11567',
  board_sha256=hashes,open_edges_before=1441,open_edges_candidate=1402,drc_errors=0,parity=0,
  raw_gate=gate,retained_prior_copper=133169,added_segments=344,added_vias=38,removed_copper=0,
  fresh_agreement=True,unchanged_nonrouting_objects=3807,completed_zone_fixtures=dict(completed),
  full_zone_coverage=False,zone_exit_status=137,exit137_cause='NOT ESTABLISHED',adopted=False,
  complete_audit_sections_extracted_to=str(destination),extracted_files=extracted)
 output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='extracted_files'},indent=2))
