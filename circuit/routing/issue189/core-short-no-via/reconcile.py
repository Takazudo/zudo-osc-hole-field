"""Reconcile rejected19-segment native core trial without publishing copper."""
import collections,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import promotion_gate,connectivity_signature
root=Path('.circuit-cache/issue189-downloaded/core-short19/.circuit-cache');out=Path(__file__).parent
stages={s:root/('osc-core-grid-shards-'+s) for s in ['start','merge','fresh']}
read=lambda p:json.loads(p.read_text())
d={s:read(p/'dump.json') for s,p in stages.items()};reports={s:read(p/'drc.json') for s,p in stages.items()}
boards={s:(p/'osc-core.kicad_pcb').read_text() for s,p in stages.items()};counts={s:collections.Counter(v for vs in copper_block_groups(text).values() for v in vs) for s,text in boards.items()}
a,b=counts['start'],counts['merge'];assert not a-b and sum(a.values())==133169 and sum((b-a).values())==19
assert counts['fresh']==b and connectivity_signature(d['merge'])==connectivity_signature(d['fresh'])
gate=promotion_gate(d['start'],d['merge'],reports['start'],reports['merge']);assert not gate['adopted'] and gate['split_pad_groups'] and not gate['native_errors'] and not gate['new_warning_identities'];assert promotion_gate(d['start'],d['fresh'],reports['start'],reports['fresh'])==gate
for key in ['pads','edges','keepouts','layers']:assert d['start'][key]==d['merge'][key]==d['fresh'][key]
for suffix in ['.kicad_pro','.kicad_dru']:assert len({(p/('osc-core'+suffix)).read_bytes() for p in stages.values()})==1
pads={p['uuid']:p['ref']+'.'+p['pad'] for p in d['start']['pads']};split=[]
for item in gate['split_pad_groups']:
 original=set(item['previously_connected_pads']);parts=[original.intersection(g) for g in d['merge']['islands'][item['net']]];parts=[g for g in parts if g];parts.sort(key=len)
 split.append(dict(net=item['net'],original_pad_count=len(original),part_sizes=list(map(len,parts)),smaller_parts=[[pads[u] for u in sorted(g)] for g in parts[:-1]]))
proof=dict(status='REJECTED; CANONICAL CORE UNCHANGED',run_id=37965185751,gate=gate,split_attribution=split,before_objects=sum(a.values()),after_objects=sum(b.values()),identical_objects=sum((a&b).values()),added_objects=19,removed_objects=0,native_edges_before=d['start']['open_edges'],native_edges_after=d['merge']['open_edges'],AGND_edges_before_after=[len(d[s]['islands']['AGND'])-1 for s in ['start','merge']],fresh_agrees=True,physical_geometry_and_project_rules_unchanged=True,board_sha256={s:hashlib.sha256(t.encode()).hexdigest() for s,t in boards.items()},drc_errors={s:sum(v['severity']=='error' for v in r['violations']) for s,r in reports.items()},parity={s:len(r['schematic_parity']) for s,r in reports.items()},warnings={s:sum(v['severity']=='warning' for v in r['violations']) for s,r in reports.items()})
(out/'retention.json').write_text(json.dumps(proof,indent=2)+'\n');print({k:v for k,v in proof.items() if k!='gate'})
(out/'artifact.json').write_text(json.dumps(dict(run_id=37965185751,source_commit='08aec29e83d24d291f4d41a7bb10300e072a7260',artifact_id=11638511202,zip_sha256='60524fca152e069c17d8880e0a740df9b6a082273f7a879a88764d17f509e414',candidate_sha256=proof['board_sha256']['merge'],replay_sha256='da1d5262b945e51aa45eb500e1296efd2324d515b164132c4da9e36cec67cf49',adopted=False),indent=2)+'\n')
