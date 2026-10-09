import collections,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
root=Path('.circuit-cache/issue189-downloaded/jr-two-no-via/.circuit-cache');outdir=Path('circuit/routing/issue189/jr-two-no-via')
a=json.loads((root/'osc-jack-right-grid-shards-start/dump.json').read_text());b=json.loads((root/'osc-jack-right-grid-shards-fresh/dump.json').read_text());pads={p['uuid']:p for p in b['pads']};splits=[]
for net,groups in a['islands'].items():
 after=[set(g) for g in b['islands'].get(net,[])]
 for group in groups:
  parts=[set(group)&g for g in after];parts=[g for g in parts if g]
  if len(parts)>1:
   for g in sorted(parts,key=len)[:-1]:splits.append({'net':net,'pads':[{k:pads[u][k] for k in ['uuid','ref','pad','xy']} for u in sorted(g)]})
x=copper_block_groups((root/'osc-jack-right-grid-shards-start/osc-jack-right.kicad_pcb').read_text());y=copper_block_groups((root/'osc-jack-right-grid-shards-fresh/osc-jack-right.kicad_pcb').read_text());ca=collections.Counter(z for v in x.values() for z in v);cb=collections.Counter(z for v in y.values() for z in v)
r={'before':sum(ca.values()),'after':sum(cb.values()),'identical':sum((ca&cb).values()),'removed':sum((ca-cb).values()),'added':sum((cb-ca).values())};assert r=={'before':50990,'after':51062,'identical':50990,'removed':0,'added':72}
receipt=json.loads(Path('boards/osc-jack-right/reports/grid-routing/shards-issue189-two-no-via.json').read_text());out={k:receipt[k] for k in ['adopted','candidate_board_sha256','input_board_sha256','open_edges_before','open_edges_after','drc_errors','parity','drc_warnings','new_warning_identities','independent_connectivity_agrees','copper_replay']};out.update(run_id=37931910118,artifact_id=11616917678,artifact_sha256='e64934d87fb79fe1dba9764d56306af371733f752b333ce259d591652582d213',retention=r,newly_split_pad_groups=splits)
(outdir/'native-result.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
