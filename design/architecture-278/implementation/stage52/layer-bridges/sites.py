"""Conservative local copper/hole/keepout screen for ordinary through-via bridge sites.
No pour connectivity or physical assembly acceptance; native DRC remains mandatory.
"""
from pathlib import Path
import hashlib,json,math,sys
from shapely.geometry import Point,LineString,Polygon,box
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
BASE='05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441';NET='XED7C19D453619667580D'
WINDOW=box(220,90,244,118)
class Screen:
 def __init__(self,d):
  if d['board_sha256']!=BASE:raise ValueError('baseline')
  self.rows=[];self.own_holes={v['uuid'] for k in ('vias','pads') for v in d[k] if v['net']==NET}
  def add(g,r,layers,net,uid,extra=None):
   if g.distance(WINDOW)<2:self.rows.append((g,r,layers,net,uid,extra))
  for t in d['tracks']:add(LineString([(x/1e6,y/1e6) for x,y in [t['a'],t['b']]]),t['width']/2e6,[t['layer']],t['net'],t['uuid'])
  for v in d['vias']:
   g=Point(*[x/1e6 for x in v['xy']]);add(g,v['diameter']/2e6,d['layers'],v['net'],v['uuid']);add(g,v['drill']/2e6,d['layers'],'HOLE',v['uuid'],.25)
  for p in d['pads']:
   g=Polygon([(x/1e6,y/1e6) for x,y in p['poly']]) if p['poly'] else Point(*[x/1e6 for x in p['xy']])
   if not p['poly'] and g.distance(WINDOW)<2:raise ValueError('unknown pad geometry')
   if p['poly']:add(g,0,p['layers'],p['net'],p['uuid']);add(g,0,d['layers'],'NO_VIA_IN_PAD',p['uuid'],0)
   if p['drill']:add(Point(*[x/1e6 for x in p['xy']]),p['drill']/2e6,d['layers'],'HOLE',p['uuid'],.25)
  for k in d['keepouts']:
   if k['tracks'] or k['vias']:add(Polygon([(x/1e6,y/1e6) for x,y in k['poly']]),0,k['layers'],'KEEPOUT',k['name'],0)
  for i,e in enumerate(d['edges']):add(LineString([(e[0]/1e6,e[1]/1e6),(e[2]/1e6,e[3]/1e6)]),0,d['layers'],'EDGE',str(i),.5)
  self.tree=STRtree([r[0] for r in self.rows]);self.d=d
 def margin(self,g,r,layers,via=False):
  margins=[]
  for i in self.tree.query(g.buffer(r+1)):
   h,hr,ls,n,uid,extra=self.rows[i]
   if n==NET or not set(ls)&set(layers) or (n=='NO_VIA_IN_PAD' and not via) or (n=='HOLE' and uid in self.own_holes and not via):continue
   clearance=extra if extra is not None else (.25 if n in ['AGND','+12V','-12V','+5V'] else .2)
   margins.append((g.distance(h)-r-hr-clearance,uid))
  return min(margins,default=(99,'none'))
def run(d,p):
 screen=Screen(d);sites=[];offset=0
 for index,r in enumerate(p['copper'][2:],2):
  a=[v/1e6 for v in r['start_nm']];b=[v/1e6 for v in r['end_nm']];length=math.dist(a,b)
  for j in range(math.ceil(length/.05)+1):
   f=min(j*.05/length,1);xy=[round(a[k]+f*(b[k]-a[k]),6) for k in range(2)];margin,uid=screen.margin(Point(xy),.3,d['layers'],True)
   if margin>=.005:sites.append({'segment_index':index,'s_mm':offset+length*f,'xy_mm':xy,'clearance_surplus_mm':margin,'nearest':uid})
  offset+=length
 return {'board_sha256':BASE,'via_mm':[.6,.3],'screen_margin_mm':.005,'path_length_mm':offset,'sites':sites,'limits':'Native refill/DRC and exact assembly gates still required; samples do not prove absence of continuous sites.'}
if __name__=='__main__':
 d=json.loads(Path(sys.argv[1]).read_text());p=json.loads(Path(sys.argv[2]).read_text());r=run(d,p);Path(sys.argv[3]).write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps({'sites':len(r['sites']),'segments':sorted({s['segment_index'] for s in r['sites']})}))
