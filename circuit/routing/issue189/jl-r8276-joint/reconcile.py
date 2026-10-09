"""Independently verify the eligible joint pilot; no canonical publication."""
import collections,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
root=Path('.circuit-cache/issue189-downloaded/jl-r8276-joint');out=Path(__file__).parent;name='osc-jack-left-grid-189-jl119-r8276-joint'
stages={'start':root/'osc-jack-left-grid-189-local-base','merge':root/name,'fresh':root/(name+'-fresh')};read=lambda p:json.loads(p.read_text());r=read(root/'issue189-local-osc-jack-left/result.json');d={s:read(p/'dump.json') for s,p in stages.items()};reports={s:read(p/'drc.json') for s,p in stages.items()};board='osc-jack-left.kicad_pcb';counts={s:collections.Counter(v for vs in copper_block_groups((p/board).read_text()).values() for v in vs) for s,p in stages.items()};a,b=counts['start'],counts['merge'];assert sum((a-b).values())==2 and sum((b-a).values())==75 and sum((a&b).values())==33346;assert counts['fresh']==b;assert connectivity_signature(d['merge'])==connectivity_signature(d['fresh'])
for s in ['merge','fresh']:assert json.loads(json.dumps(promotion_gate(d['start'],d[s],reports['start'],reports[s])))==r['gate'] and r['gate']['adopted']
for key in ['pads','edges','keepouts','layers']:assert d['start'][key]==d['merge'][key]==d['fresh'][key]
for suffix in ['.kicad_pro','.kicad_dru']:assert len({(p/('osc-jack-left'+suffix)).read_bytes() for p in stages.values()})==1
assert hashlib.sha256((stages['fresh']/board).read_bytes()).hexdigest()==r['candidate_sha256'];assert hashlib.sha256((root/'issue189-local-osc-jack-left/copper.json').read_bytes()).hexdigest()==r['replay_sha256']
proof=dict(status='ELIGIBLE PILOT; NOT CANONICAL ADOPTION',before_objects=sum(a.values()),after_objects=sum(b.values()),identical_objects=sum((a&b).values()),added_objects=75,removed_objects=2,gate=r['gate'],native_edges_before=d['start']['open_edges'],native_edges_after=d['fresh']['open_edges'],fresh_agrees=True,physical_geometry_and_project_rules_unchanged=True,drc_errors={s:sum(v['severity']=='error' for v in drc['violations']) for s,drc in reports.items()},parity={s:len(drc['schematic_parity']) for s,drc in reports.items()},warnings={s:sum(v['severity']=='warning' for v in drc['violations']) for s,drc in reports.items()},candidate_sha256=r['candidate_sha256'],replay_sha256=r['replay_sha256'])
(out/'retention.json').write_text(json.dumps(proof,indent=2)+'\n');(out/'pilot.json').write_text(json.dumps(r,indent=2)+'\n');print(proof)
(out/'artifact.json').write_text(json.dumps(dict(run_id=37976521780,source_commit='d1dd53fea72278434ae40e6ef4c4d02ac2c54afd',artifact_id=11639497498,zip_sha256='0d643e9bfa906f9f45f2daa8ec87835a64ca2ec8c05bbc9ad2d3071fb5fd12b6'),indent=2)+'\n')
