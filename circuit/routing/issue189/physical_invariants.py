"""Audit native-exported pad/net, outline, keepout and layer invariance for accepted stages."""
import collections,hashlib,json
from pathlib import Path
out={'scope':'Native-exported non-route geometry for latest accepted additive stages; not hardware qualification','boards':{}}
for board,artifact,end in [('osc-jack-left','jl-u106-outer','osc-jack-left-grid-shards-fresh'),('osc-jack-right','jr-two-after-protected','osc-jack-right-grid-shards-fresh'),('osc-core','core-filtered','osc-core-grid-189-compact-refill')]:
 root=Path('.circuit-cache/issue189-downloaded')/artifact/'.circuit-cache';pa=root/(board+'-grid-shards-start')/'dump.json';pb=root/end/'dump.json';a=json.loads(pa.read_text());b=json.loads(pb.read_text());rows={}
 for key in ('pads','edges','keepouts'):
  def normalized(xs):return collections.Counter(json.dumps(x,sort_keys=True,separators=(',',':')) for x in xs)
  assert normalized(a[key])==normalized(b[key]),(board,key)
  rows[key]={'unchanged':True,'count':len(a[key])}
 assert a['layers']==b['layers'];rows['layers']={'unchanged':True,'layers':a['layers']}
 out['boards'][board]={'before_dump_sha256':hashlib.sha256(pa.read_bytes()).hexdigest(),'after_dump_sha256':hashlib.sha256(pb.read_bytes()).hexdigest(),'before_board_sha256':a['board_sha256'],'after_native_filled_board_sha256':b['board_sha256'],'geometry':rows};print(board,rows,flush=True)
Path('circuit/routing/issue189/physical-invariants.json').write_text(json.dumps(out,indent=2)+'\n')
