import sys, math
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from lib import *
from shapely.geometry import LineString, Point, box
from shapely import affinity
from shapely.ops import unary_union
txt=open(REPO+'/boards/osc-core/osc-core.kicad_pcb').read()
b=sexp(txt)
import json
tok=json.loads(gshow('HEAD','design/reports/board-net-tokens.json'))
layers_cu=[l[1] for l in child(b,'layers')[1:] if isinstance(l,list) and l[1].endswith('.Cu')]
print('copper layers',layers_cu)
for net in ['/W1/F2_SUM','/W1/F2_OUT']:
    tk=[k for k,v in tok.items() if v==net][0]
    shapes=[]  # (geom, layers set, label)
    for f in children(b,'footprint'):
        at=child(f,'at'); x,y=float(at[1]),float(at[2]); rot=float(at[3]) if len(at)>3 else 0.0
        ref=[p[2] for p in children(f,'property') if p[1]=='Reference'][0]
        for p in children(f,'pad'):
            n=child(p,'net')
            if not n or n[-1]!=tk: continue
            pa=child(p,'at'); px,py=float(pa[1]),float(pa[2]); prot=float(pa[3]) if len(pa)>3 else 0.0
            sz=child(p,'size'); w,h=float(sz[1]),float(sz[2])
            a=math.radians(rot)
            gx=x+px*math.cos(a)+py*math.sin(a); gy=y-px*math.sin(a)+py*math.cos(a)
            g=affinity.rotate(box(gx-w/2,gy-h/2,gx+w/2,gy+h/2),-prot,origin=(gx,gy))
            ls=[l for l in child(p,'layers')[1:]]
            L=set(layers_cu) if '*.Cu' in ls else {l for l in ls if l.endswith('.Cu')}
            shapes.append((g,L,f'PAD {ref}.{p[1]}'))
            print(net,'pad',ref,p[1],p[2],p[3],'size',w,h,'padrot',prot,'at',(round(gx-100,3),round(gy-50,3)),sorted(L))
    for s in children(b,'segment'):
        if child(s,'net')[-1]!=tk: continue
        st=child(s,'start');en=child(s,'end');w=float(child(s,'width')[1])
        g=LineString([(float(st[1]),float(st[2])),(float(en[1]),float(en[2]))]).buffer(w/2)
        shapes.append((g,{child(s,'layer')[1]},'SEG'))
    for v in children(b,'via'):
        if child(v,'net')[-1]!=tk: continue
        at=child(v,'at'); sz=float(child(v,'size')[1]); ls=child(v,'layers')[1:]
        i0,i1=layers_cu.index(ls[0]),layers_cu.index(ls[1])
        shapes.append((Point(float(at[1]),float(at[2])).buffer(sz/2),set(layers_cu[min(i0,i1):max(i0,i1)+1]),f'VIA {round(float(at[1])-100,3)},{round(float(at[2])-50,3)}'))
    par=list(range(len(shapes)))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    for i in range(len(shapes)):
        for j in range(i):
            if shapes[i][1]&shapes[j][1] and shapes[i][0].intersects(shapes[j][0]): par[f(i)]=f(j)
    comps={}
    for i,s in enumerate(shapes): comps.setdefault(f(i),[]).append(s[2])
    for c,m in comps.items():
        print('  component:',[x for x in m if x!='SEG'],'segments',m.count('SEG'))
    # distance from U5210 pad to nearest other copper on same layer
    for g,L,lab in shapes:
        if lab.startswith('PAD U5210'):
            d=min(g.distance(g2) for g2,L2,l2 in shapes if l2!=lab and L&L2)
            print('  ',lab,'gap to nearest same-layer copper of the net mm',round(d,4))
print('--- endpoints near U5210 pads')
for s in children(b,'segment'):
    n=tok.get(child(s,'net')[-1])
    if n not in('/W1/F2_SUM','/W1/F2_OUT'): continue
    st=child(s,'start');en=child(s,'end')
    for p in (st,en):
        x,y=float(p[1])-100,float(p[2])-50
        if 181<x<186 and 206<y<210: print(n,child(s,'layer')[1],'w',child(s,'width')[1],'start',(float(st[1])-100,float(st[2])-50),'end',(float(en[1])-100,float(en[2])-50))
