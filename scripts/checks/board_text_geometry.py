#!/usr/bin/env python3
"""Read KiCad 10 .kicad_pcb geometry and copper connectivity from the file text.

Host-only and read-only: no pcbnew, no refill, no DRC. Footprints, pads,
courtyards, tracks, vias, zones (with their stored fills) and Edge.Cuts are
parsed from the S-expression text. Connectivity is an approximation of the
native ratsnest (anchor-in-shape tests on pads, tracks, vias and stored zone
fills); callers compare it with the native counts in the receipts and report
any difference instead of trusting it blindly.
"""
from __future__ import annotations
import collections,hashlib,math,re
from pathlib import Path

TOKEN=re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()"]+')


def sexpr(text):
    stack=[[]]
    for m in TOKEN.finditer(text):
        tok=m.group(0)
        if tok=='(':stack.append([])
        elif tok==')':
            done=stack.pop();stack[-1].append(done)
        else:stack[-1].append(tok[1:-1] if tok[0]=='"' else tok)
    return stack[0]


def top_blocks(text):
    """Yield (head, block_text) for every top-level child of kicad_pcb."""
    starts=[m.start()+2 for m in re.finditer(r'\n\t\(',text)]
    for i,s in enumerate(starts):
        e=starts[i+1]-2 if i+1<len(starts) else len(text)
        head=re.match(r'\(([\w]+)',text[s:s+40]).group(1)
        yield head,text[s:e]


def child(node,name):
    for c in node:
        if isinstance(c,list) and c and c[0]==name:return c
    return None


def children(node,name):
    return [c for c in node if isinstance(c,list) and c and c[0]==name]


def rot(lx,ly,deg):
    """KiCad local-to-board rotation (y down, positive angle counter-clockwise on screen)."""
    r=math.radians(deg);c,s=math.cos(r),math.sin(r)
    return lx*c+ly*s,-lx*s+ly*c


class Footprint:
    __slots__=('ref','value','lib','x','y','angle','side','locked','pads','courtyard_local','uuid')

    def board_points(self,pts,x=None,y=None,angle=None):
        x=self.x if x is None else x;y=self.y if y is None else y;angle=self.angle if angle is None else angle
        return [(x+dx,y+dy) for dx,dy in (rot(px,py,angle) for px,py in pts)]

    def courtyard_bbox(self,x=None,y=None,angle=None):
        if not self.courtyard_local:return None
        pts=self.board_points(self.courtyard_local,x,y,angle)
        xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        return (min(xs),min(ys),max(xs),max(ys))

    def pad_shapes(self,x=None,y=None,angle=None):
        """Board-frame pad rectangles (x0,y0,x1,y1) per pad, as axis-aligned bounds."""
        x=self.x if x is None else x;y=self.y if y is None else y;angle=self.angle if angle is None else angle
        out=[]
        for p in self.pads:
            cx,cy=rot(p['lx'],p['ly'],angle);cx+=x;cy+=y
            a=p['abs_angle']-self.angle+angle
            w,h=p['w'],p['h']
            pts=[rot(dx,dy,a) for dx,dy in ((-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2))]
            xs=[cx+q[0] for q in pts];ys=[cy+q[1] for q in pts]
            out.append(dict(p,x=cx,y=cy,bbox=(min(xs),min(ys),max(xs),max(ys))))
        return out


def parse_footprint(block):
    n=sexpr(block)[0]
    f=Footprint();f.lib=n[1];f.locked=child(n,'locked') is not None and child(n,'locked')[1]=='yes'
    f.side=child(n,'layer')[1];f.uuid=(child(n,'uuid') or [None,None])[1]
    at=child(n,'at');f.x,f.y=float(at[1]),float(at[2]);f.angle=float(at[3]) if len(at)>3 else 0.0
    f.ref=f.value=''
    for p in children(n,'property'):
        if p[1]=='Reference':f.ref=p[2]
        elif p[1]=='Value':f.value=p[2]
    f.pads=[]
    for p in children(n,'pad'):
        pat=child(p,'at');size=child(p,'size');layers=child(p,'layers')[1:];net=child(p,'net')
        drill=child(p,'drill');pu=child(p,'uuid')
        f.pads.append({'num':p[1],'kind':p[2],'shape':p[3],'lx':float(pat[1]),'ly':float(pat[2]),
                       'abs_angle':float(pat[3]) if len(pat)>3 else 0.0,'w':float(size[1]),'h':float(size[2]),
                       'layers':layers,'net':net[-1] if net else '','uuid':pu[1] if pu else None,'drill':float(drill[-1]) if drill and drill[-1].replace('.','',1).isdigit() else 0.0})
    pts=[]
    for kind in ('fp_line','fp_rect','fp_poly','fp_circle','fp_arc'):
        for g in children(n,kind):
            lay=child(g,'layer')
            if not lay or not lay[1].endswith('CrtYd'):continue
            if kind=='fp_poly':
                for xy in children(child(g,'pts'),'xy'):pts.append((float(xy[1]),float(xy[2])))
            elif kind=='fp_circle':
                c=child(g,'center');e=child(g,'end');r=math.dist((float(c[1]),float(c[2])),(float(e[1]),float(e[2])))
                pts+= [(float(c[1])-r,float(c[2])-r),(float(c[1])+r,float(c[2])+r)]
            else:
                for key in ('start','end','mid'):
                    q=child(g,key)
                    if q:pts.append((float(q[1]),float(q[2])))
    if pts:
        xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        f.courtyard_local=[(min(xs),min(ys)),(max(xs),min(ys)),(max(xs),max(ys)),(min(xs),max(ys))]
    else:f.courtyard_local=None
    return f


SEG=re.compile(r'\(segment\s+\(start ([\d.\-]+) ([\d.\-]+)\)\s+\(end ([\d.\-]+) ([\d.\-]+)\)\s+\(width ([\d.]+)\)\s+\(layer "([^"]+)"\)\s+(?:\(locked [^)]*\)\s+)?\(net "([^"]*)"\)\s+\(uuid "([^"]+)"\)')
VIA=re.compile(r'\(via\s+(?:\(\w+[^()]*\)\s+)*?\(at ([\d.\-]+) ([\d.\-]+)\)\s+\(size ([\d.]+)\)\s+\(drill ([\d.]+)\)\s+\(layers ((?:"[^"]+"\s*)+)\)(.*?)\(net "([^"]*)"\)\s+\(uuid "([^"]+)"\)',re.S)


class Board:
    def __init__(self,path):
        self.path=Path(path);raw=self.path.read_bytes();self.sha256=hashlib.sha256(raw).hexdigest()
        text=raw.decode();self.footprints={};self.segments=[];self.vias=[];self.zones=[];self.edges=[]
        self.copper_layers=[]
        for head,block in top_blocks(text):
            if head=='footprint':
                f=parse_footprint(block);self.footprints[f.ref]=f
            elif head=='segment':
                m=SEG.search(block)
                if m:
                    a,b,c,d,w,l,net,u=m.groups()
                    self.segments.append({'a':(float(a),float(b)),'b':(float(c),float(d)),'w':float(w),'layer':l,'net':net,'uuid':u})
            elif head=='via':
                m=VIA.search(block)
                if m:
                    x,y,s,dr,lay,_,net,u=m.groups()
                    self.vias.append({'xy':(float(x),float(y)),'size':float(s),'drill':float(dr),'layers':re.findall(r'"([^"]+)"',lay),'net':net,'uuid':u})
            elif head=='zone':
                self.zones.append(parse_zone(block))
            elif head in ('gr_line','gr_rect','gr_arc','gr_poly') and '"Edge.Cuts"' in block:
                n=sexpr(block)[0];pts=[(float(q[1]),float(q[2])) for k in ('start','end','mid') for q in [child(n,k)] if q]
                self.edges.append((head,pts))
            elif head=='layers':
                for m in re.finditer(r'\(\d+ "([^"]+\.Cu)"',block):self.copper_layers.append(m.group(1))
        if not self.copper_layers:self.copper_layers=['F.Cu','B.Cu']
        self.unknown_tracks=text.count('\n\t(arc')

    def outline_bbox(self):
        pts=[p for _,ps in self.edges for p in ps]
        return (min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)) if pts else None


def parse_zone(block):
    n=sexpr(block)[0];net=child(n,'net');name=child(n,'name')
    layers=child(n,'layers') or child(n,'layer');layers=layers[1:] if layers else []
    keep=child(n,'keepout')
    outline=[(float(q[1]),float(q[2])) for q in children(child(child(n,'polygon'),'pts'),'xy')] if child(n,'polygon') else []
    fills=[]
    for fp in children(n,'filled_polygon'):
        lay=child(fp,'layer')[1];pts=[(float(q[1]),float(q[2])) for q in children(child(fp,'pts'),'xy')]
        fills.append((lay,pts))
    rules={}
    if keep:
        for k in keep[1:]:
            if isinstance(k,list):rules[k[0]]=k[1]
    return {'net':net[-1] if net else '','name':name[1] if name else '','layers':layers,'keepout':rules if keep else None,
            'outline':outline,'fills':fills}


def point_in_poly(x,y,pts):
    inside=False;j=len(pts)-1
    for i in range(len(pts)):
        xi,yi=pts[i];xj,yj=pts[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi+1e-300)+xi:inside=not inside
        j=i
    return inside


def seg_point_dist(p,a,b):
    ax,ay=a;bx,by=b;px,py=p;dx,dy=bx-ax,by-ay;L=dx*dx+dy*dy
    t=0 if L==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L))
    return math.hypot(px-ax-t*dx,py-ay-t*dy)


def seg_bbox(s,pad=0.0):
    (ax,ay),(bx,by)=s['a'],s['b'];h=s['w']/2+pad
    return (min(ax,bx)-h,min(ay,by)-h,max(ax,bx)+h,max(ay,by)+h)


def bbox_overlap(a,b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]


def seg_rect_dist(s,r):
    """Distance from a segment centreline to an axis-aligned rectangle (0 when crossing)."""
    x0,y0,x1,y1=r
    for p in (s['a'],s['b']):
        if x0<=p[0]<=x1 and y0<=p[1]<=y1:return 0.0
    corners=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
    d=min(seg_point_dist(c,s['a'],s['b']) for c in corners)
    for i in range(4):
        d=min(d,seg_seg_dist(s['a'],s['b'],corners[i],corners[(i+1)%4]))
    return d


def seg_seg_dist(a,b,c,d):
    def ccw(p,q,r):return (r[1]-p[1])*(q[0]-p[0])-(q[1]-p[1])*(r[0]-p[0])
    if (ccw(a,c,d)>0)!=(ccw(b,c,d)>0) and (ccw(a,b,c)>0)!=(ccw(a,b,d)>0):return 0.0
    return min(seg_point_dist(a,c,d),seg_point_dist(b,c,d),seg_point_dist(c,a,b),seg_point_dist(d,a,b))


class Grid:
    def __init__(self,cell=2.0):self.cell=cell;self.cells=collections.defaultdict(list)

    def keys(self,bb):
        c=self.cell
        for i in range(int(math.floor(bb[0]/c)),int(math.floor(bb[2]/c))+1):
            for j in range(int(math.floor(bb[1]/c)),int(math.floor(bb[3]/c))+1):yield (i,j)

    def add(self,bb,item):
        for k in self.keys(bb):self.cells[k].append(item)

    def query(self,bb):
        seen=set();out=[]
        for k in self.keys(bb):
            for it in self.cells.get(k,()):
                if id(it) not in seen:seen.add(id(it));out.append(it)
        return out


def pad_on_layer(pad,layer):
    return any(l==layer or l=='*.Cu' or (l.endswith('.Cu') and l.startswith('*')) for l in pad['layers'])


def connectivity(board,nets=None):
    """Approximate native islands per net from the board text.

    Items: pads (on their copper layers), segment endpoints, vias and stored zone
    fills. Returns {net: [island,...]} where each island is a list of item labels
    ('pad:REF.N', 'seg:uuid', 'via:uuid', 'zone:name@layer#i').
    """
    parent={}
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb:parent[ra]=rb
    items=collections.defaultdict(list)
    pad_index=collections.defaultdict(lambda:Grid(2.0));seg_index=collections.defaultdict(lambda:Grid(2.0))
    pads={};vias={};segs={};fills={}
    for f in board.footprints.values():
        for p in f.pad_shapes():
            if not p['net'] or (nets and p['net'] not in nets):continue
            lab=f'pad:{f.ref}.{p["num"]}';parent[lab]=lab;pads[lab]=p;items[p['net']].append(lab)
            for layer in board.copper_layers:
                if pad_on_layer(p,layer):pad_index[(p['net'],layer)].add(p['bbox'],lab)
    for s in board.segments:
        if nets and s['net'] not in nets:continue
        lab='seg:'+s['uuid'];parent[lab]=lab;segs[lab]=s;items[s['net']].append(lab)
        seg_index[(s['net'],s['layer'])].add(seg_bbox(s),lab)
    for v in board.vias:
        if nets and v['net'] not in nets:continue
        lab='via:'+v['uuid'];parent[lab]=lab;vias[lab]=v;items[v['net']].append(lab)
    for z in board.zones:
        if z['keepout'] is not None or not z['net'] or (nets and z['net'] not in nets):continue
        for i,(layer,pts) in enumerate(z['fills']):
            lab=f'zone:{z["name"]}@{layer}#{i}';parent[lab]=lab;fills[lab]=(z['net'],layer,pts);items[z['net']].append(lab)
    def via_layers(v):
        ls=v['layers']
        if len(ls)==2 and ls[0] in board.copper_layers and ls[1] in board.copper_layers:
            i,j=sorted((board.copper_layers.index(ls[0]),board.copper_layers.index(ls[1])))
            return board.copper_layers[i:j+1]
        return board.copper_layers
    for lab,s in segs.items():
        for pt in (s['a'],s['b']):
            q=(pt[0]-1e-3,pt[1]-1e-3,pt[0]+1e-3,pt[1]+1e-3)
            for other in seg_index[(s['net'],s['layer'])].query(q):
                if other==lab:continue
                o=segs[other]
                if seg_point_dist(pt,o['a'],o['b'])<=o['w']/2+1e-4:union(lab,other)

    for lab,s in segs.items():
        for pl in pad_index[(s['net'],s['layer'])].query(seg_bbox(s)):
            if seg_rect_dist(s,pads[pl]['bbox'])<=s['w']/2+1e-4:union(lab,pl)
    for pl,p in pads.items():
        q=(p['x']-1e-3,p['y']-1e-3,p['x']+1e-3,p['y']+1e-3)
        for layer in board.copper_layers:
            if not pad_on_layer(p,layer):continue
            for other in seg_index[(p['net'],layer)].query(q):
                o=segs[other]
                if seg_point_dist((p['x'],p['y']),o['a'],o['b'])<=o['w']/2+1e-4:union(pl,other)
    for lab,v in vias.items():
        r=v['size']/2;q=(v['xy'][0]-r,v['xy'][1]-r,v['xy'][0]+r,v['xy'][1]+r)
        for layer in via_layers(v):
            for other in seg_index[(v['net'],layer)].query(q):
                o=segs[other]
                if seg_point_dist(v['xy'],o['a'],o['b'])<=o['w']/2+r+1e-4:union(lab,other)
            for pl in pad_index[(v['net'],layer)].query(q):
                x0,y0,x1,y1=pads[pl]['bbox']
                if math.hypot(max(x0-v['xy'][0],0,v['xy'][0]-x1),max(y0-v['xy'][1],0,v['xy'][1]-y1))<=r+1e-4:union(lab,pl)
    fill_bbox={lab:(min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)) for lab,(_,_,pts) in fills.items()}
    for lab,(net,layer,pts) in fills.items():
        bb=fill_bbox[lab]
        for pl in pad_index[(net,layer)].query(bb):
            p=pads[pl];x0,y0,x1,y1=p['bbox']
            if point_in_poly(p['x'],p['y'],pts) or any(point_in_poly(cx,cy,pts) for cx,cy in ((x0,y0),(x1,y0),(x1,y1),(x0,y1))) \
               or any(x0<=vx<=x1 and y0<=vy<=y1 for vx,vy in pts):union(lab,pl)
        for sl in seg_index[(net,layer)].query(bb):
            s=segs[sl]
            if point_in_poly(*s['a'],pts) or point_in_poly(*s['b'],pts):union(lab,sl)
        for vl,v in vias.items():
            if v['net']==net and layer in via_layers(v) and bb[0]<=v['xy'][0]<=bb[2] and bb[1]<=v['xy'][1]<=bb[3] and point_in_poly(*v['xy'],pts):union(lab,vl)
    out={}
    for net,labs in items.items():
        groups=collections.defaultdict(list)
        for l in labs:groups[find(l)].append(l)
        out[net]=list(groups.values())
    return out,pads,segs,vias


def island_pads(island):
    return sorted(l[4:] for l in island if l.startswith('pad:'))


def island_points(island,pads,segs,vias):
    pts=[]
    for l in island:
        if l.startswith('pad:'):pts.append((pads[l]['x'],pads[l]['y'],l))
        elif l.startswith('via:'):v=vias[l];pts.append((v['xy'][0],v['xy'][1],l))
        elif l.startswith('seg:'):
            s=segs[l];pts+=[(s['a'][0],s['a'][1],l),(s['b'][0],s['b'][1],l)]
    return pts


def open_edges(islands,pads,segs,vias):
    """Minimum spanning set of island-to-island gaps, named by their nearest pad or copper item."""
    if len(islands)<2:return []
    P=[island_points(i,pads,segs,vias) for i in islands]
    def gap(a,b):
        best=None
        for x1,y1,l1 in P[a]:
            for x2,y2,l2 in P[b]:
                d=math.hypot(x1-x2,y1-y2)
                if best is None or d<best[0]:best=(d,l1,l2,(x1,y1),(x2,y2))
        return best
    inside={0};edges=[];cand={j:gap(0,j) for j in range(1,len(islands))}
    while cand:
        j=min(cand,key=lambda k:cand[k][0]);d,l1,l2,p1,p2=cand.pop(j)
        edges.append({'gap_mm':round(d,3),'from':l1,'to':l2,'from_xy':[round(p1[0],3),round(p1[1],3)],'to_xy':[round(p2[0],3),round(p2[1],3)],
                      'to_island':j})
        inside.add(j)
        for k in list(cand):
            g=gap(j,k)
            if g[0]<cand[k][0]:cand[k]=g
    return edges
