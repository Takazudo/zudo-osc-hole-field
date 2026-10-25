#!/usr/bin/env python3
"""Regression checks of accounting boundaries, never spatial/native execution."""
import copy,gzip,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[5]
def read(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes())
def validate(c):
 seeds=read(H/'evidence/seed-dispositions.json');expected={s['object_key']:s for s in seeds};objects=c['objects']
 assert len(objects)==len(expected)==40 and {s['object_key'] for s in objects}==set(expected),'exact40 inventory'
 for x in objects:
  s=expected[x['object_key']]
  assert all(x[k]==s[k] for k in ('source_span','sha256','uuid','component_id')),'identity or branch drift'
  assert x['net']==s['net_token'] and x['classification']==s['classification'],'source ownership drift'
  assert x['canonical']=='PRESERVE_EXACT_SOURCE' and x['future_A']=='UNRESOLVED_NO_OMISSION_OR_COPY_AUTHORITY' and x['future_B']=='PRESERVE_TERMINAL_OBLIGATION_DISPOSITION_UNRESOLVED','unjustified physical disposition'
 assert c['authority']=={k:False for k in ('canonical_edits','fixture_edits','routing','placement','native','adoption','merge')},'unauthorized or missing execution/adoption authority'
 assert c['fixture_decision']['change'] is False,'historical fixture mutation'
 assert all(c['fixture_decision'][k]==dict.fromkeys(('+12V','-12V','+5V','AGND'),0) for k in ('rail_track_counts','rail_via_counts')),'fixture rail inference'
 branches=c['branch_obligations'];assert len(branches)==8 and {b['component_id'] for b in branches}==set(range(8)),'exact branch inventory'
 for b in branches:
  g=next(x for x in read(H/'evidence/components.json.gz') if x['id']==b['component_id'])
  assert b['net']==g['net_token'] and b['classification']==g['classification'] and b['zone_gate']==g['zone_contact_status'],'branch semantics drift'
  assert b['terminal_counts']==g['terminal_board_counts'] and b['source_object_count']==len(g['object_keys']) and b['seed_count']==len(g['seed_keys']),'component ownership drift'
 plus=next(b for b in branches if b['net']=='+5V')
 assert plus['terminal_counts']=={'two-A':38,'two-B':510} and plus['seed_count']==21 and plus['source_object_count']==5653,'mixed +5V cannot be B-exclusive'
 source_zones={z['uuid']:z for z in read(H/'evidence/zones.json')};assert len(c['zones'])==5 and {z['uuid'] for z in c['zones']}==set(source_zones),'exact zone inventory'
 for z in c['zones']:
  original=source_zones[z['uuid']]
  assert all(z[k]==original[k] for k in ('source_span','sha256','uuid')) and z['net']==original['net_token'] and z['layer']==original['source_layer'],'zone identity drift'
  assert z['canonical']=='PRESERVE_EXACT_SOURCE' and z['historical_fill_count']==original['settled_filled_polygon_count'],'unjustified zone disposition'
 assert all(z['future_A']==z['future_B']=='UNRESOLVED_LOCAL_PLANE_AND_RETURN_DESIGN' for z in c['zones']),'unproved projected plane'
 assert c['zone_evidence']['valid_contact_records']==1 and c['zone_evidence']['unresolved_bbox_records']==19,'bbox contacts promoted'
 f=c['cross_board_feed'];assert f['new_native_terminals']==0 and f['same_net_name_joins_boards'] is False and f['legacy_harness_repacking'] is False,'phantom physical feed'
 assert f['net_order']==['+12V','-12V','+5V','AGND','AGND','AGND']
 assert c['genuine_board_needs']['two-A']['direct_owned_pad_counts']=={'+12V':289,'-12V':220,'+5V':38,'AGND':1015}
 assert c['genuine_board_needs']['two-B']['direct_owned_pad_counts']=={'+12V':292,'-12V':192,'+5V':510,'AGND':1281}
 return True

def main():
 c=read(H/'projection-contract.json');validate(c)
 for p,h in read(H/'input-seals.json').items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 # Bind graph rows back to original source, never UUID alone.
 source=(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text()
 for r in read(H/'evidence/reached-source-objects.json.gz'):
  assert hashlib.sha256(source[slice(*r['source_span'])].encode()).hexdigest()==r['sha256']
 review=read(H/'evidence/physical-fixture-review.json');assert review['physical_PCB_census']['all_14_B_pad_UUIDs_and_parent_refs_absent'] and review['physical_PCB_census']['all_40_source_object_UUIDs_absent']
 assert review['artifact']['board_sha256']==c['fixture_decision']['board_sha256']
 for path,h in review['source_sha256'].items():
  p=Path(path)
  # Transferred evidence remains runnable without local artifact caches.
  if '/generated/' not in path and not path.startswith('/tmp/'):
   assert hashlib.sha256(p.read_bytes()).hexdigest()==h,path
 mutations=[('unjustified A omission',lambda x:x['objects'][0].update(future_A='OMIT')),
  ('UUID-only alias',lambda x:x['objects'][0].update(source_span=[0,1])),
  ('mixed rail B-exclusive',lambda x:next(b for b in x['branch_obligations'] if b['net']=='+5V').update(terminal_counts={'two-B':510})),
  ('invalid bbox as contact',lambda x:x['zone_evidence'].update(valid_contact_records=20,unresolved_bbox_records=0)),
  ('phantom physical feed',lambda x:x['cross_board_feed'].update(new_native_terminals=12)),
  ('fixture rewrite',lambda x:x['fixture_decision'].update(change=True)),
  ('native adoption credit',lambda x:x['authority'].update(adoption=True)),
  ('missing branch hidden by duplicate',lambda x:x['branch_obligations'].__setitem__(6,copy.deepcopy(x['branch_obligations'][0]))),
  ('zone source alias',lambda x:x['zones'][0].update(source_span=[0,1],sha256='bad')),
  ('zone canonical removal',lambda x:x['zones'][0].update(canonical='REMOVE')),
  ('missing authority fields',lambda x:x.update(authority={})),
  ('vacuous rail counts',lambda x:x['fixture_decision'].update(rail_track_counts={},rail_via_counts={})),
  ('zone identity alias',lambda x:x['zones'][0].update(uuid='unknown'))]
 for label,mutate in mutations:
  changed=copy.deepcopy(c);mutate(changed)
  try:validate(changed)
  except AssertionError:pass
  else:raise AssertionError('unsafe mutation accepted: '+label)
 print('PASS: exact40 dispositions/5675 source identities; mixed A/B rail, unresolved plane/feed gates;13 unsafe mutations rejected; no geometry/native/fixture writes')
if __name__=='__main__':main()
