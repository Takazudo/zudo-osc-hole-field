import json,sys,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.grid_router import Raster,FillGuard
source=Path('.circuit-cache/issue189-downloaded/jr-local/osc-jack-right-grid-189-jr-local-cut/dump.json')
dump=json.loads(source.read_text());proposal=json.load(open('circuit/routing/issue189/jr-coupled-proposal.json'));start=time.monotonic()
r=Raster(dump,.05,grow={n:.05 for n in ['+12V','-12V','+5V','AGND']});li=r.layers.index('In3.Cu');g=FillGuard(r.label[li],r.net_id['-12V'],.45,.05)
rows=[x for x in proposal['copper'] if x['kind']=='via' or x.get('layer')=='In3.Cu']
def pieces(xs):
 return [r.disc(x['at_nm'],x['diameter_nm']/2) if x['kind']=='via' else r.segment_mask(x['start_nm'],x['end_nm'],x['width_nm']+2*r.step) for x in xs]
out={'status':'APPROXIMATE RASTER ATTRIBUTION ONLY; NOT A NATIVE RESULT','input_dump_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'all_keeps':g.keeps(g.shrunk(pieces(rows))),'individual':[]}
for row in rows:
 out['individual'].append({'uuid':row['uuid'],'net':row['net'],'kind':row['kind'],'single_keeps':g.keeps(g.shrunk(pieces([row]))),'all_except_this_keeps':g.keeps(g.shrunk(pieces([x for x in rows if x!=row])))})
out['elapsed_seconds']=time.monotonic()-start
Path('.circuit-cache/issue189-jr-fill-attribution.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
