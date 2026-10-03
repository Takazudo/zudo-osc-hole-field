#!/usr/bin/env python3
"""Four-layer grid A* router for the last open pad islands of a draft board.

Input is a grid_dump.py JSON. Each open island of a requested net is joined to
the net's largest island with a grid path over F.Cu/In1.Cu/In2.Cu/B.Cu and
through vias; routed copper becomes an obstacle for later nets. Optional
rip-up removes all copper of named signal nets and reroutes them afterwards.

The raster is conservative, not exact: obstacles come from foreign copper,
drills, keepouts and the board edge, inflated by clearance plus half the new
width plus one cell half-diagonal. Zone pours are ignored because they refill.
Every result is only a proposal: build it into a candidate board and accept
it only after native KiCad DRC/parity, refill, ratsnest and ground checks.
A candidate board must sit two directories below the repository root
(for example .circuit-cache/<name>/) so its fp-lib-table ${KIPRJMOD}/../../
path resolves; elsewhere DRC reports spurious lib_footprint_issues.
"""
from __future__ import annotations
import argparse,heapq,json,math,sys
from pathlib import Path
import numpy as np
from scipy import ndimage
import shapely

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid

LAYERS=('F.Cu','In1.Cu','In2.Cu','B.Cu')
SQRT2=math.sqrt(2)


class Raster:
    """Integer net labels per layer on a res-mm grid; 0 is empty, -1 foreign to every net."""
    def __init__(self,dump,res=0.1,skip=()):
        xs=[v for e in dump['edges'] for v in (e[0],e[2])];ys=[v for e in dump['edges'] for v in (e[1],e[3])]
        if not xs:raise ValueError('board outline missing')
        self.res=res;self.step=res*1e6
        self.x0=min(xs)-self.step;self.y0=min(ys)-self.step
        self.w=int((max(xs)-self.x0)/self.step)+3;self.h=int((max(ys)-self.y0)/self.step)+3
        nets=sorted({i['net'] for k in ('pads','tracks','vias') for i in dump[k] if i['net']})
        self.net_id={n:i+1 for i,n in enumerate(nets)}
        self.label=np.zeros((4,self.h,self.w),np.int32)
        self.hole=np.zeros((self.h,self.w),bool);self.smd=np.zeros((self.h,self.w),bool)
        for p in dump['pads']:
            value=self.net_id.get(p['net'],-1) if p['net'] else -1
            if p['poly']:
                m,sl=self.polygon(p['poly'])
                for name in p['layers']:self.label[LAYERS.index(name)][sl][m]=value
                if not p['drill']:self.smd[sl]|=m
            if p['drill']:
                m,sl=self.disc(p['xy'],p['drill']/2);self.hole[sl]|=m
                if p['npth']:
                    for li in range(4):self.label[li][sl][m]=-1
        for t in dump['tracks']:
            if t['uuid'] in skip:continue
            self.segment(LAYERS.index(t['layer']),t['a'],t['b'],t['width'],self.net_id[t['net']])
        for v in dump['vias']:
            if v['uuid'] in skip:continue
            self.via(v['xy'],v['diameter'],v['drill'],self.net_id[v['net']])
        gx,gy=self.centres()
        ring=shapely.polygonize([shapely.LineString([e[:2],e[2:]]) for e in dump['edges']])
        inside=shapely.contains_xy(shapely.union_all(ring),gx,gy) if not ring.is_empty else np.zeros_like(gx,bool)
        self.d_edge=ndimage.distance_transform_edt(inside)*res
        self.keep_track=np.zeros((4,self.h,self.w),bool);self.keep_via=np.zeros((self.h,self.w),bool)
        for k in dump['keepouts']:
            if len(k['poly'])<3:continue
            m,sl=self.polygon(k['poly'])
            for name in k['layers']:
                if k['tracks']:self.keep_track[LAYERS.index(name)][sl]|=m
            if k['vias']:self.keep_via[sl]|=m
        self.d_keep_track=[ndimage.distance_transform_edt(~m)*res for m in self.keep_track]
        self.d_keep_via=ndimage.distance_transform_edt(~self.keep_via)*res
        self.d_smd=ndimage.distance_transform_edt(~self.smd)*res

    def centres(self,sl=(slice(None),slice(None))):
        ys=np.arange(self.h)[sl[0]];xs=np.arange(self.w)[sl[1]]
        gx,gy=np.meshgrid(self.x0+xs*self.step,self.y0+ys*self.step)
        return gx,gy

    def window(self,lo,hi):
        i0=max(0,int((lo[0]-self.x0)/self.step)-1);i1=min(self.w,int((hi[0]-self.x0)/self.step)+2)
        j0=max(0,int((lo[1]-self.y0)/self.step)-1);j1=min(self.h,int((hi[1]-self.y0)/self.step)+2)
        return (slice(j0,j1),slice(i0,i1))

    def polygon(self,poly):
        arr=np.array(poly,float);sl=self.window(arr.min(0),arr.max(0));gx,gy=self.centres(sl)
        return shapely.contains_xy(shapely.Polygon(arr),gx,gy)|shapely.intersects_xy(shapely.Polygon(arr).exterior,gx,gy),sl

    def disc(self,xy,radius):
        sl=self.window((xy[0]-radius,xy[1]-radius),(xy[0]+radius,xy[1]+radius));gx,gy=self.centres(sl)
        return (gx-xy[0])**2+(gy-xy[1])**2<=radius*radius,sl

    def segment(self,li,a,b,width,value):
        r=width/2;sl=self.window((min(a[0],b[0])-r,min(a[1],b[1])-r),(max(a[0],b[0])+r,max(a[1],b[1])+r));gx,gy=self.centres(sl)
        dx,dy=b[0]-a[0],b[1]-a[1];length=dx*dx+dy*dy or 1.0
        u=np.clip(((gx-a[0])*dx+(gy-a[1])*dy)/length,0,1)
        m=(gx-a[0]-u*dx)**2+(gy-a[1]-u*dy)**2<=r*r
        self.label[li][sl][m]=value
        return m,sl

    def via(self,xy,diameter,drill,value):
        m,sl=self.disc(xy,diameter/2)
        for li in range(4):self.label[li][sl][m]=value
        h,hs=self.disc(xy,drill/2);self.hole[hs]|=h

    def cell(self,x,y):
        return int(round((y-self.y0)/self.step)),int(round((x-self.x0)/self.step))

    def point(self,j,i):
        return int(round(self.x0+i*self.step)),int(round(self.y0+j*self.step))


def island_mask(raster,dump,members):
    ids=set(members);mask=np.zeros((4,raster.h,raster.w),bool)
    for p in dump['pads']:
        if p['uuid'] in ids and p['poly']:
            m,sl=raster.polygon(p['poly'])
            for name in p['layers']:mask[LAYERS.index(name)][sl]|=m
    for t in dump['tracks']:
        if t['uuid'] in ids:
            li=LAYERS.index(t['layer']);sl=raster.window(np.minimum(t['a'],t['b']),np.maximum(t['a'],t['b']))
            gx,gy=raster.centres(sl);a,b=t['a'],t['b'];dx,dy=b[0]-a[0],b[1]-a[1];length=dx*dx+dy*dy or 1.0
            u=np.clip(((gx-a[0])*dx+(gy-a[1])*dy)/length,0,1)
            mask[li][sl]|=(gx-a[0]-u*dx)**2+(gy-a[1]-u*dy)**2<=(raster.step*0.75)**2
    for v in dump['vias']:
        if v['uuid'] in ids:
            j,i=raster.cell(*v['xy']);mask[:,j,i]=True
    return mask


def astar(free,via_ok,src,goal,layer_cost,via_cost,max_expansions):
    """Multi-source A*; through-copper (all four layers own copper) switches layer without a via."""
    h,w=free.shape[1:]
    hdist=ndimage.distance_transform_edt(~goal.any(0))
    best={};prev={};heap=[]
    through_src=src.all(0);through_goal=goal.all(0)
    for l,y,x in np.argwhere(src):
        best[(l,y,x)]=0.0;heapq.heappush(heap,(hdist[y,x],0.0,int(l),int(y),int(x)))
    ok=lambda l,y,x:free[l,y,x] or src[l,y,x] or goal[l,y,x]
    steps=((-1,0,1.0),(1,0,1.0),(0,-1,1.0),(0,1,1.0),(-1,-1,SQRT2),(-1,1,SQRT2),(1,-1,SQRT2),(1,1,SQRT2))
    expansions=0
    while heap:
        _,g,l,y,x=heapq.heappop(heap)
        if best.get((l,y,x),math.inf)<g:continue
        expansions+=1
        if expansions>max_expansions:return None,expansions
        if goal[l,y,x]:
            path=[(l,y,x)]
            while path[-1] in prev:path.append(prev[path[-1]])
            return path[::-1],expansions
        for dy,dx,cost in steps:
            ny,nx=y+dy,x+dx
            if not(0<=ny<h and 0<=nx<w) or not ok(l,ny,nx):continue
            if dy and dx and not(ok(l,y,nx) and ok(l,ny,x)):continue
            ng=g+cost*layer_cost[l];key=(l,ny,nx)
            if ng<best.get(key,math.inf):
                best[key]=ng;prev[key]=(l,y,x);heapq.heappush(heap,(ng+hdist[ny,nx],ng,l,ny,nx))
        through=through_src[y,x] or through_goal[y,x]
        if via_ok[y,x] or through:
            for l2 in range(4):
                if l2==l or not ok(l2,y,x):continue
                ng=g+(0.5 if through else via_cost);key=(l2,y,x)
                if ng<best.get(key,math.inf):
                    best[key]=ng;prev[key]=(l,y,x);heapq.heappush(heap,(ng+hdist[y,x],ng,l2,y,x))
    return None,expansions


def route(dump,nets=(),rip=(),rip_first=False,res=0.1,layer_cost=(3,1,1.3,3),via_cost=30.0,
          clearance=0.25,rail_nets=(),rail_width=0.4,signal_width=0.3,via_diameter=0.7,via_drill=0.3,
          hole_clearance=0.25,edge_clearance=0.5,max_expansions=4_000_000,allowed_layers=LAYERS,log=print):
    """Return (results, removed_uuids). Each result has net, island pad names and a [layer,x,y,through] path or None."""
    rip=list(rip)
    removed={i['uuid'] for k in ('tracks','vias') for i in dump[k] if i['net'] in rip}
    raster=Raster(dump,res,removed)
    margin=res/SQRT2+0.01
    islands={n:[list(g) for g in groups] for n,groups in dump['islands'].items()}
    pads_by_uuid={p['uuid']:p for p in dump['pads']}
    for n in rip:islands[n]=[[p['uuid']] for p in dump['pads'] if p['net']==n]
    order=[n for n in (list(nets) or sorted(islands)) if n not in rip]
    order=rip+order if rip_first else order+rip
    allowed=[LAYERS.index(n) for n in allowed_layers]
    results=[]
    for net in order:
        if net not in islands or net not in raster.net_id:continue
        N=raster.net_id[net];w=rail_width if net in rail_nets else signal_width
        free=np.zeros((4,raster.h,raster.w),bool);foreign_any=np.zeros((raster.h,raster.w),bool)
        for li in range(4):
            foreign=(raster.label[li]!=0)&(raster.label[li]!=N);foreign_any|=foreign
            if li in allowed:
                dist=ndimage.distance_transform_edt(~foreign)*res
                free[li]=(dist>=clearance+w/2+margin)&(raster.d_edge>=edge_clearance+w/2+margin)&(raster.d_keep_track[li]>=w/2+margin)
        vr=via_diameter/2
        dist_any=ndimage.distance_transform_edt(~foreign_any)*res
        d_hole=ndimage.distance_transform_edt(~raster.hole)*res
        via_ok=((dist_any>=clearance+vr+margin)&(raster.d_edge>=edge_clearance+vr+margin)&(raster.d_keep_via>=vr+margin)
                &(d_hole>=vr+hole_clearance+margin)&(raster.d_smd>=vr+margin))
        groups=islands[net]
        main=max(range(len(groups)),key=lambda i:len(groups[i]))
        reached=island_mask(raster,dump,groups[main])
        for gi,g in enumerate(groups):
            if gi==main:continue
            names=[pads_by_uuid[u]['ref']+'.'+pads_by_uuid[u]['pad'] for u in g if u in pads_by_uuid]
            src=island_mask(raster,dump,g)
            path,expanded=astar(free,via_ok,src,reached,layer_cost,via_cost,max_expansions)
            if path is None:
                log(f'NOPATH {net} {names} expanded {expanded}');results.append({'net':net,'island':names,'path':None});continue
            i0=max(i for i,(l,y,x) in enumerate(path) if src[l,y,x])
            i1=min(i for i,(l,y,x) in enumerate(path) if reached[l,y,x] and i>=i0)
            path=path[i0:i1+1]
            out=[]
            for l,y,x in path:
                px,py=raster.point(y,x);through=bool(src[:,y,x].all() or reached[:,y,x].all())
                out.append([LAYERS[l],px,py,int(through)])
            vias=sum(1 for p,q in zip(out,out[1:]) if p[0]!=q[0] and not q[3])
            log(f'PATH {net} {names} cells {len(path)} expanded {expanded} vias {vias}')
            results.append({'net':net,'island':names,'path':out,'width_nm':int(round(w*1e6))})
            for i,(l,y,x) in enumerate(path):
                px,py=raster.point(y,x)
                raster.segment(l,(px,py),(px,py),w*1e6+2*raster.step,N)
                if i and path[i-1][0]!=l and not out[i][3]:raster.via((px,py),via_diameter*1e6,via_drill*1e6,N)
            for l,y,x in path:reached[l,y,x]=True
            reached|=src
    return results,sorted(removed)


def simplify(points):
    """Drop interior points of straight runs on one layer."""
    out=[points[0]]
    for i in range(1,len(points)-1):
        p,q,r=out[-1],points[i],points[i+1]
        if p[0]==q[0]==r[0]:
            d1=(q[1]-p[1],q[2]-p[2]);d2=(r[1]-q[1],r[2]-q[2])
            if d1[0]*d2[1]-d1[1]*d2[0]==0 and d1[0]*d2[0]+d1[1]*d2[1]>0:continue
        out.append(q)
    out.append(points[-1]);return out


def copper_rows(results,board_id,tag,via_diameter=0.7,via_drill=0.3):
    """Source copper rows (segments and through vias) with stable UUIDs, plus per-link UUID lists."""
    rows=[];links=[];seen=set()
    for k,r in enumerate(results):
        if not r['path']:continue
        pts=simplify(r['path']);key=f"{tag}:{r['net']}:{k}";ids=[]
        for i,(p,q) in enumerate(zip(pts,pts[1:])):
            if p[0]==q[0]:
                if p[1:3]==q[1:3]:continue
                uid=stable_uuid(board_id,tag,f'{key}:track:{i}')
                rows.append({'kind':'segment','uuid':uid,'net':r['net'],'start_nm':p[1:3],'end_nm':q[1:3],'width_nm':r['width_nm'],'layer':p[0]})
            else:
                if q[3] or (r['net'],q[1],q[2]) in seen:continue
                seen.add((r['net'],q[1],q[2]))
                uid=stable_uuid(board_id,tag,f'{key}:via:{i}')
                rows.append({'kind':'via','uuid':uid,'net':r['net'],'at_nm':q[1:3],'diameter_nm':int(round(via_diameter*1e6)),
                             'drill_nm':int(round(via_drill*1e6)),'layers':['F.Cu','B.Cu'],'locked':False})
            ids.append(uid)
        links.append({'net':r['net'],'island':r['island'],'copper_uuids':ids})
    return rows,links


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('dump',type=Path);p.add_argument('output',type=Path);p.add_argument('--board-id',required=True)
    p.add_argument('--tag',required=True,help='UUID namespace for this batch')
    p.add_argument('--nets',default='',help='comma-separated nets (default: every open net)')
    p.add_argument('--rip',default='',help='comma-separated signal nets to remove and reroute')
    p.add_argument('--rip-first',action='store_true')
    p.add_argument('--rail-nets',default='+12V,-12V,+5V')
    p.add_argument('--res',type=float,default=0.1);p.add_argument('--clearance',type=float,default=0.25)
    p.add_argument('--signal-width',type=float,default=0.3);p.add_argument('--rail-width',type=float,default=0.4)
    p.add_argument('--via-cost',type=float,default=30.0);p.add_argument('--layer-cost',default='3,1,1.3,3')
    p.add_argument('--layers',default=','.join(LAYERS));p.add_argument('--max-expansions',type=int,default=4_000_000)
    a=p.parse_args()
    dump=json.loads(a.dump.read_text())
    split=lambda s:[x for x in s.split(',') if x]
    results,removed=route(dump,split(a.nets),split(a.rip),a.rip_first,a.res,[float(x) for x in a.layer_cost.split(',')],a.via_cost,
                          a.clearance,split(a.rail_nets),a.rail_width,a.signal_width,max_expansions=a.max_expansions,
                          allowed_layers=split(a.layers),log=lambda m:print(m,flush=True))
    rows,links=copper_rows(results,a.board_id,a.tag)
    a.output.write_text(json.dumps({'status':'UNCHECKED PROPOSAL; native DRC/parity/ground gates required','board_sha256':dump['board_sha256'],
                                    'removed_uuids':removed,'copper':rows,'links':links,
                                    'unrouted':[{'net':r['net'],'island':r['island']} for r in results if not r['path']]},indent=1)+'\n')
    print(f'{len(links)} links, {len(rows)} copper rows, {len(removed)} ripped objects, {sum(1 for r in results if not r["path"])} unrouted')
if __name__=='__main__':main()
