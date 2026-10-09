import json,hashlib,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import connectivity_signature,promotion_gate
root=Path('.circuit-cache/issue189-downloaded/jr-c7413-endpoints');board='osc-jack-right';name='osc-jack-right-grid-189-jr135-c7413-endpoints';out=Path('circuit/routing/issue189/jr-c7413-endpoints')
before=root/(board+'-grid-189-local-base');candidate=root/name
r=json.loads((root/('issue189-local-'+board)/'result.json').read_text());d=json.loads((candidate/'dump.json').read_text());a=json.loads((before/'dump.json').read_text());f=json.loads((root/(name+'-fresh')/'dump.json').read_text());assert connectivity_signature(d)==connectivity_signature(f)
x=Counter(v for vs in copper_block_groups((before/(board+'.kicad_pcb')).read_text()).values() for v in vs);y=Counter(v for vs in copper_block_groups((candidate/(board+'.kicad_pcb')).read_text()).values() for v in vs)
assert sum((x-y).values())==r['retained_copper']['removed_objects'];assert sum((y-x).values())==r['retained_copper']['added_objects'];assert not r['retained_copper']['changed_existing_uuids'];assert hashlib.sha256((candidate/(board+'.kicad_pcb')).read_bytes()).hexdigest()==r['candidate_sha256']
assert json.loads(json.dumps(promotion_gate(a,d,json.loads((before/'drc.json').read_text()),json.loads((candidate/'drc.json').read_text()))))==r['gate']
summary=dict(r['gate'],before_objects=sum(x.values()),after_objects=sum(y.values()),identical_objects=sum((x&y).values()),added_objects=sum((y-x).values()),removed_objects=sum((x-y).values()),native_edges_before=a['open_edges'],native_edges_after=d['open_edges'],AGND_edges_before_after=[len(v['islands']['AGND'])-1 for v in (a,d)],drc_errors=sum(v['severity']=='error' for v in json.loads((candidate/'drc.json').read_text())['violations']),parity=len(json.loads((candidate/'drc.json').read_text())['schematic_parity']),warnings=sum(v['severity']=='warning' for v in json.loads((candidate/'drc.json').read_text())['violations']),fresh_agrees=True)
(out/'pilot.json').write_text(json.dumps(r,indent=2)+'\n');(out/'retention.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
(out/'artifact.json').write_text(json.dumps(dict(run_id=37965489217,source_commit='61dcf368f6d29f32b33f5d6b0baa4aacb162e419',artifact_id=11633417223,artifact_sha256='c9691383c024c5e0fcfb2d3694e637c0c4d0080cf464752e8ac9d85b463f12f1',candidate_sha256=r['candidate_sha256'],replay_sha256=r['replay_sha256'],adopted=False),indent=2)+'\n')

for key in ('pads','edges','keepouts','layers'):
 assert a[key]==d[key]==f[key],key
for suffix in ('kicad_pro','kicad_dru'):
 assert (before/(board+'.'+suffix)).read_bytes()==(candidate/(board+'.'+suffix)).read_bytes()
assert r['gate']['adopted'] and r['open_edges_after']==134
