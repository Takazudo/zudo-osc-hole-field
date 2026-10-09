import json,hashlib,sys,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import Raster,FillGuard
cases=[('jr-d7504-outer-avoid','osc-jack-right',False),('jr-two-after-protected','osc-jack-right',True),('jr-two-without-d7504','osc-jack-right',True),('jl-u106-outer','osc-jack-left',True),('jl-u2119-ground-corridor','osc-jack-left',False)]
out=[]
for name,board,accepted in cases:
 root=Path('.circuit-cache/issue189-downloaded')/name/'.circuit-cache';p=root/(board+'-grid-shards-start')/'dump.json';d=json.loads(p.read_text());proposal=json.loads((Path('circuit/routing/issue189')/name/'proposal.json').read_text());assert proposal['board_sha256']==d['board_sha256']
 rows=proposal['copper'];pts=[v for row in rows for k,v in row.items() if k in ('start_nm','end_nm','at_nm')];bounds=[min(v[0] for v in pts)/1e6-6,min(v[1] for v in pts)/1e6-6,max(v[0] for v in pts)/1e6+6,max(v[1] for v in pts)/1e6+6];begin=time.monotonic();r=Raster(d,.025,bounds_mm=bounds);checks=[]
 for layer in ['F.Cu','B.Cu','In1.Cu']:
  fg=FillGuard(r.label[r.layers.index(layer)],r.net_id['AGND'],.45,.025,domain=r.d_edge>0);pieces=[]
  for row in rows:
   if row['kind']=='via':pieces.append(r.disc(row['at_nm'],row['diameter_nm']/2))
   elif row['layer']==layer:pieces.append(r.segment_mask(row['start_nm'],row['end_nm'],row['width_nm']+2*r.step))
  checks.append({'layer':layer,'keeps_ground_partition':bool(fg.keeps(fg.shrunk(pieces)))})
 out.append({'case':name,'native_accepted':accepted,'board_sha256':d['board_sha256'],'dump_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bounds_mm':bounds,'objects':len(rows),'elapsed_seconds':time.monotonic()-begin,'checks':checks});print(name,checks,flush=True)
Path('circuit/routing/issue189/jr-ground-screen/crosscheck.json').write_text(json.dumps({'status':'APPROXIMATE OFFLINE SCREEN AGAINST PREVIOUS NATIVE OUTCOMES; NOT NEW NATIVE VALIDATION','cases':out},indent=2)+'\n')
