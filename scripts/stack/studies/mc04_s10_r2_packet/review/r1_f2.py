import json, math, sys, hashlib
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from lib import *
HEAD='80569b5375087df519b79ead67d1bf56c16301e6'
print('## paper poses')
for sha in ['6093081c','8243acdf','6e5716e7','32580f77',HEAD]:
    for path,key in [('design/partition/adopted-placement-pins.json','pins'),('design/partition/floorplan-candidate.json',None)]:
        try: d=gjson(sha,path)
        except Exception as e: print(sha[:8],path,'ERR'); continue
        if key: rows=d[key]
        else:
            rows=None
            for k,v in d.items():
                if isinstance(v,list) and v and isinstance(v[0],dict) and 'ref' in v[0]: rows=v; kk=k; break
        for r in rows:
            if r.get('ref') in('R5257','U5210','R5259','R5256') and r.get('board','K')=='K':
                print(sha[:8],path.split('/')[-1],r['ref'],r.get('x_mm'),r.get('y_mm'),r.get('rotation_deg'),r.get('side'),r.get('fixed'))
dx=round(100*(180.97-174.66)); dy=round(100*(204.70-199.89))
print('dx,dy',dx,dy,dx*dx+dy*dy,793**2, dx*dx+dy*dy>793**2, math.sqrt(dx*dx+dy*dy)/100, math.hypot(180.97-174.66,204.70-199.89))
print('excess', math.sqrt(dx*dx+dy*dy)/100-7.93, 'round2',round(math.hypot(180.97-174.66,204.70-199.89),2))
print('## nets')
io=gjson(HEAD,'design/reports/io-partition.json')
nets={}
for u in io['package_units']:
    for pin,net in u['pins'].items():
        if net: nets.setdefault(net,[]).append((u['ref'],pin,u.get('role')))
for n in ['/W1/F2_SUM','/W1/F2_OUT','/W1/F2_CLIP','/W1/F1_OUT']:
    print(n,sorted(set(nets[n])))
pk={p['ref']:p for p in io['physical_packages']}
for r in ['U5210','R5257','R5256','R5259','R5255','R5258','D5208','D5209']:
    p=pk[r]; print(r,{k:p.get(k) for k in('mpn','symbol','footprint','family','instance','dnp')})
    print('   units',[(u['unit'],u['role'],u['pins']) for u in io['package_units'] if u['ref']==r])
inv=gjson(HEAD,'.claude/skills/component-spec-audit/references/inventory.json')
s=json.dumps(inv)
import re
def find(o,pat,path=''):
    if isinstance(o,dict):
        if any(isinstance(v,str) and pat in v for v in o.values()): print('  inv',path,json.dumps(o)[:500]); return
        for k,v in o.items(): find(v,pat,path+'/'+k)
    elif isinstance(o,list):
        for i,v in enumerate(o): find(v,pat,path+f'[{i}]')
find(inv,'RT0603BRD07100KL'); find(inv,'OPA4196IDR')
print('## board')
txt=open(REPO+'/boards/osc-core/osc-core.kicad_pcb').read()
print('sha',hashlib.sha256(txt.encode()).hexdigest())
fps,segs,vias,_,zones=board(txt)
tok=gjson(HEAD,'design/reports/board-net-tokens.json'); 
T=lambda n: tok.get(n,n)
for r in ['R5257','U5210','R5256','R5259','R5258','R5255']:
    f=fps[r]; print(r,(round(f['at'][0]-100,4),round(f['at'][1]-50,4)),f['rot'],f['layer'],{k:[(round(x-100,4),round(y-50,4),T(n)) for x,y,n in v] for k,v in f['pads'].items() if r!='U5210' or k in('5','6','7')})
def pad(ref,num):
    x,y,n=fps[ref]['pads'][num][0]; return (x,y),T(n)
for a,b in [(('R5257','2'),('U5210','6')),(('R5257','1'),('U5210','7')),(('R5257','1'),('U5210','6')),(('R5257','2'),('U5210','7')),(('R5256','2'),('U5210','6'))]:
    pa,na=pad(*a); pb,nb=pad(*b); print(a,na,b,nb,round(math.dist(pa,pb),4))
# copper
for net in ['/W1/F2_SUM','/W1/F2_OUT']:
    tk=[k for k,v in tok.items() if v==net][0]
    ss=[s for s in segs if s[0]!='ARC' and s[3]==tk]; vv=[v for v in vias if v[1]==tk]
    arcs=[s for s in segs if s[0]=='ARC' and child(s[1],'net')[-1]==tk]
    L=sum(math.dist(s[0],s[1]) for s in ss)
    print(net,tk,'segments',len(ss),'len',round(L,4),'vias',len(vv),'arcs',len(arcs),'layers',sorted({s[2] for s in ss}))
    zs=[z for z in zones if (child(z,'net') or [None])[-1]==tk or (child(z,'net_name') or [None])[-1]==tk]
    print('   zones on net',len(zs))
    # connectivity: union find over points with tolerance, layer aware
    pts=[]  # (x,y,layerset,label)
    padpts=[]
    for ref,f in fps.items():
        for num,pl in f['pads'].items():
            for x,y,n in pl:
                if n==tk: padpts.append((ref,num,x,y,f['layer']))
    print('   pads on net',[(r,n,round(x-100,3),round(y-50,3),l) for r,n,x,y,l in padpts])
    nodes=[]
    for s in ss: nodes.append(('seg',s))
    parent={}
    def fnd(a):
        while parent.setdefault(a,a)!=a:
            parent[a]=parent[parent[a]]; a=parent[a]
        return a
    def uni(a,b): parent[fnd(a)]=fnd(b)
    def key(p,layer): return (round(p[0],3),round(p[1],3),layer)
    for s in ss: uni(key(s[0],s[2]),key(s[1],s[2]))
    for v in vv:
        for l in ('F.Cu','B.Cu','In1.Cu','In2.Cu'): uni(key(v[0],'F.Cu'),key(v[0],l))
    # point on segment (T junction) and pad proximity
    def near_seg(p,s,tol):
        (x1,y1),(x2,y2)=s[0],s[1]; px,py=p
        dx,dy=x2-x1,y2-y1; L2=dx*dx+dy*dy
        t=0 if L2==0 else max(0,min(1,((px-x1)*dx+(py-y1)*dy)/L2))
        return math.hypot(px-(x1+t*dx),py-(y1+t*dy))<=tol
    for s in ss:
        for s2 in ss:
            if s is s2 or s[2]!=s2[2]: continue
            for p in (s[0],s[1]):
                if near_seg(p,s2,s2[4]/2): uni(key(p,s[2]),key(s2[0],s2[2]))
    for v in vv:
        for s in ss:
            if near_seg(v[0],s,0.3): uni(key(v[0],'F.Cu'),key(s[0],s[2]))
    comp={}
    for r,n,x,y,l in padpts:
        hit=None
        for s in ss:
            if s[2]==l and near_seg((x,y),s,0.45): hit=fnd(key(s[0],s[2])); break
        if hit is None:
            for v in vv:
                if math.dist(v[0],(x,y))<0.5: hit=fnd(key(v[0],'F.Cu'))
        comp[(r,n)]=hit
    ids={}
    print('   pad->component', {k:(ids.setdefault(v,len(ids)) if v else None) for k,v in comp.items()})
    # nearest copper endpoint to U5210 pads
    for r,n,x,y,l in padpts:
        if r=='U5210':
            d=min((min(math.dist((x,y),s[0]),math.dist((x,y),s[1])) for s in ss),default=None)
            print('   U5210 pad',n,'nearest segment end mm',d)
