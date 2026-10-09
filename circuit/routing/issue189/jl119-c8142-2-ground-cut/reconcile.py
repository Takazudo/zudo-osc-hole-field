import json,hashlib,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import connectivity_signature,promotion_gate
root=Path('.circuit-cache/issue189-downloaded/jl-c8142-ground');board='osc-jack-left';name='osc-jack-left-grid-189-jl119-c8142-2-ground-cut';out=Path('circuit/routing/issue189/jl119-c8142-2-ground-cut')
before=root/(board+'-grid-189-local-base');candidate=root/name
r=json.loads((root/('issue189-local-'+board)/'result.json').read_text());d=json.loads((candidate/'dump.json').read_text());a=json.loads((before/'dump.json').read_text());f=json.loads((root/(name+'-verify')/'dump.json').read_text());cut=json.loads((root/(name+'-cut')/'dump.json').read_text());assert connectivity_signature(d)==connectivity_signature(f)
x=Counter(v for vs in copper_block_groups((before/(board+'.kicad_pcb')).read_text()).values() for v in vs);y=Counter(v for vs in copper_block_groups((candidate/(board+'.kicad_pcb')).read_text()).values() for v in vs)
assert sum((x-y).values())==r['retained_copper']['removed_objects'];assert sum((y-x).values())==r['retained_copper']['added_objects'];assert not r['retained_copper']['changed_existing_uuids'];assert hashlib.sha256((candidate/(board+'.kicad_pcb')).read_bytes()).hexdigest()==r['candidate_sha256']
assert json.loads(json.dumps(promotion_gate(a,d,json.loads((before/'drc.json').read_text()),json.loads((candidate/'drc.json').read_text()))))==r['gate']
summary=dict(r['gate'],before_objects=sum(x.values()),after_objects=sum(y.values()),identical_objects=sum((x&y).values()),added_objects=sum((y-x).values()),removed_objects=sum((x-y).values()),native_edges_before=a['open_edges'],native_edges_after=d['open_edges'],AGND_edges_before_cut_after=[len(v['islands']['AGND'])-1 for v in (a,cut,d)],drc_errors=r['stage']['drc_errors'],parity=r['stage']['parity'],warnings=r['stage']['drc_warnings'],fresh_agrees=True)
(out/'rejection.json').write_text(json.dumps(r,indent=2)+'\n');(out/'retention.json').write_text(json.dumps(summary,indent=2)+'\n');print(summary)
(out/'artifact.json').write_text(json.dumps(dict(run_id=37967648679,source_commit='6d76d17712c63c3ec72c910211dfa2322c45a924',artifact_id=11634289502,artifact_sha256='a5697c04b3510063c1b0ea3198951f01debaa42a6f128e12faca021066606c2d',candidate_sha256=r['candidate_sha256'],replay_sha256=r['replay_sha256'],adopted=False),indent=2)+'\n')
