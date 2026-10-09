import collections,json,subprocess,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.route_shards import copper_block_groups
source='1fe06ad5';out={'comparison':'Original issue baseline to current branch; full serialized copper block multisets, not a waiver for removed copper','source_commit':subprocess.check_output(['git','rev-parse',source]).decode().strip(),'current_commit':subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),'boards':{}}
for name in ['osc-jack-left','osc-jack-right','osc-core']:
 path=f'boards/{name}/{name}.kicad_pcb';a=subprocess.check_output(['git','show',f'{source}:{path}']).decode();b=Path(path).read_text();x=copper_block_groups(a);y=copper_block_groups(b);ca=collections.Counter(z for v in x.values() for z in v);cb=collections.Counter(z for v in y.values() for z in v)
 r={'before_sha256':hashlib.sha256(a.encode()).hexdigest(),'after_sha256':hashlib.sha256(b.encode()).hexdigest(),'before_objects':sum(ca.values()),'after_objects':sum(cb.values()),'identical_objects':sum((ca&cb).values()),'removed_or_changed_objects':sum((ca-cb).values()),'new_or_changed_objects':sum((cb-ca).values())};out['boards'][name]=r;print(name,r,flush=True)
for name,r in out['boards'].items():
 r['accepted_reroutes']=[]
 for receipt in sorted((Path('boards')/name/'reports/grid-routing').glob('*issue189*.json')):
  v=json.loads(receipt.read_text())
  if not v.get('adopted'):continue
  count=v.get('copper_removed',0)
  if receipt.name=='issue189-benchmark.json':count=len(json.loads(receipt.with_name('issue189-benchmark-copper.json').read_text())['removed'])
  if count:r['accepted_reroutes'].append({'receipt':str(receipt),'removed_objects':count,'before_open_edges':v['open_edges_before'],'after_open_edges':v['open_edges_after'],'native_errors':v.get('native_errors'),'drc_errors':v['drc_errors'],'parity':v['parity'],'split_pad_groups':v['split_pad_groups'],'new_warning_identities':v['new_warning_identities']})
Path('circuit/routing/issue189/current-retention-ledger.json').write_text(json.dumps(out,indent=2)+'\n')
