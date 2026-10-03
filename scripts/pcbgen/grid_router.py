#!/usr/bin/env python3
"""Four-layer grid A* router for the last open pad islands of a draft board.

Input is a grid_dump.py JSON. Each open island of a requested net is joined to
the net's largest island with a grid path over the board's copper layers and
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
import argparse,collections,heapq,json,math,sys
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
    def __init__(self,dump,res=0.1,skip=(),grow=None):
        self.layers=tuple(dump.get('layers',LAYERS));n=len(self.layers)
        xs=[v for e in dump['edges'] for v in (e[0],e[2])];ys=[v for e in dump['edges'] for v in (e[1],e[3])]
        if not xs:raise ValueError('board outline missing')
        self.res=res;self.step=res*1e6
        self.x0=min(xs)-self.step;self.y0=min(ys)-self.step
        self.w=int((max(xs)-self.x0)/self.step)+3;self.h=int((max(ys)-self.y0)/self.step)+3
        nets=sorted({i['net'] for k in ('pads','tracks','vias') for i in dump[k] if i['net']})
        self.net_id={n:i+1 for i,n in enumerate(nets)}
        self.label=np.zeros((n,self.h,self.w),np.int32)
        self.hole=np.zeros((self.h,self.w),bool);self.smd=np.zeros((self.h,self.w),bool)
        grow=grow or {}
        for p in dump['pads']:
            value=self.net_id.get(p['net'],-1) if p['net'] else -1
            if p['poly']:
                m,sl=self.polygon(p['poly'],grow.get(p['net'],0)*1e6)
                for name in p['layers']:self.label[self.layers.index(name)][sl][m]=value
                if not p['drill']:self.smd[sl]|=m
            if p['drill']:
                m,sl=self.disc(p['xy'],p['drill']/2);self.hole[sl]|=m
                if p['npth']:
                    for li in range(n):self.label[li][sl][m]=-1
        for t in dump['tracks']:
            if t['uuid'] in skip:continue
            self.segment(self.layers.index(t['layer']),t['a'],t['b'],t['width']+2e6*grow.get(t['net'],0),self.net_id[t['net']])
        for v in dump['vias']:
            if v['uuid'] in skip:continue
            self.via(v['xy'],v['diameter']+2e6*grow.get(v['net'],0),v['drill'],self.net_id[v['net']])
        gx,gy=self.centres()
        ring=shapely.polygonize([shapely.LineString([e[:2],e[2:]]) for e in dump['edges']])
        inside=shapely.contains_xy(shapely.union_all(ring),gx,gy) if not ring.is_empty else np.zeros_like(gx,bool)
        self.d_edge=ndimage.distance_transform_edt(inside)*res
        self.keep_track=np.zeros((n,self.h,self.w),bool);self.keep_via=np.zeros((self.h,self.w),bool)
        for k in dump['keepouts']:
            if len(k['poly'])<3:continue
            m,sl=self.polygon(k['poly'])
            for name in k['layers']:
                if k['tracks']:self.keep_track[self.layers.index(name)][sl]|=m
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

    def polygon(self,poly,grow=0.0,conservative=True):
        # Any cell touched by copper counts: buffering by the half-diagonal makes EDT distances lower bounds.
        shape=shapely.Polygon(np.array(poly,float))
        if grow or conservative:shape=shape.buffer(grow+(self.step/SQRT2 if conservative else 0),quad_segs=4)
        lo,hi=np.array(shape.bounds[:2]),np.array(shape.bounds[2:]);sl=self.window(lo,hi);gx,gy=self.centres(sl)
        return shapely.contains_xy(shape,gx,gy)|shapely.intersects_xy(shape.exterior,gx,gy),sl

    def disc(self,xy,radius):
        radius+=self.step/SQRT2
        sl=self.window((xy[0]-radius,xy[1]-radius),(xy[0]+radius,xy[1]+radius));gx,gy=self.centres(sl)
        return (gx-xy[0])**2+(gy-xy[1])**2<=radius*radius,sl

    def segment_mask(self,a,b,width):
        r=width/2+self.step/SQRT2;sl=self.window((min(a[0],b[0])-r,min(a[1],b[1])-r),(max(a[0],b[0])+r,max(a[1],b[1])+r));gx,gy=self.centres(sl)
        dx,dy=b[0]-a[0],b[1]-a[1];length=dx*dx+dy*dy or 1.0
        u=np.clip(((gx-a[0])*dx+(gy-a[1])*dy)/length,0,1)
        return (gx-a[0]-u*dx)**2+(gy-a[1]-u*dy)**2<=r*r,sl

    def segment(self,li,a,b,width,value):
        m,sl=self.segment_mask(a,b,width)
        self.label[li][sl][m]=value
        return m,sl

    def via(self,xy,diameter,drill,value):
        m,sl=self.disc(xy,diameter/2)
        for li in range(len(self.layers)):self.label[li][sl][m]=value
        h,hs=self.disc(xy,drill/2);self.hole[hs]|=h

    def cell(self,x,y):
        return int(round((y-self.y0)/self.step)),int(round((x-self.x0)/self.step))

    def point(self,j,i):
        return int(round(self.x0+i*self.step)),int(round(self.y0+j*self.step))


def island_mask(raster,dump,members):
    ids=set(members);mask=np.zeros((len(raster.layers),raster.h,raster.w),bool)
    for p in dump['pads']:
        if p['uuid'] in ids and p['poly']:
            m,sl=raster.polygon(p['poly'],conservative=False)
            for name in p['layers']:mask[raster.layers.index(name)][sl]|=m
    for t in dump['tracks']:
        if t['uuid'] in ids:
            li=raster.layers.index(t['layer']);sl=raster.window(np.minimum(t['a'],t['b']),np.maximum(t['a'],t['b']))
            gx,gy=raster.centres(sl);a,b=t['a'],t['b'];dx,dy=b[0]-a[0],b[1]-a[1];length=dx*dx+dy*dy or 1.0
            u=np.clip(((gx-a[0])*dx+(gy-a[1])*dy)/length,0,1)
            mask[li][sl]|=(gx-a[0]-u*dx)**2+(gy-a[1]-u*dy)**2<=(raster.step*0.75)**2
    for v in dump['vias']:
        if v['uuid'] in ids:
            j,i=raster.cell(*v['xy']);mask[:,j,i]=True
    return mask


def astar(free,via_ok,src,goal,layer_cost,via_cost,max_expansions,weight=1.0,penalty=None):
    """Multi-source A*; through-copper (all layers own copper) switches layer without a via.

    weight>1 inflates the heuristic: faster, at most weight times the optimal cost.
    """
    layers,h,w=free.shape
    hdist=ndimage.distance_transform_edt(~goal.any(0))*weight
    passable=free|src|goal
    through=src.all(0)|goal.all(0)
    best={};prev={};heap=[]
    for l,y,x in np.argwhere(src):
        best[(l,y,x)]=0.0;heapq.heappush(heap,(hdist[y,x],0.0,int(l),int(y),int(x)))
    steps=((-1,0,1.0),(1,0,1.0),(0,-1,1.0),(0,1,1.0),(-1,-1,SQRT2),(-1,1,SQRT2),(1,-1,SQRT2),(1,1,SQRT2))
    expansions=0;get=best.get;inf=math.inf
    while heap:
        _,g,l,y,x=heapq.heappop(heap)
        if get((l,y,x),inf)<g:continue
        expansions+=1
        if expansions>max_expansions:return None,expansions
        if goal[l,y,x]:
            path=[(l,y,x)]
            while path[-1] in prev:path.append(prev[path[-1]])
            return path[::-1],expansions
        row=passable[l];cost_l=layer_cost[l]
        for dy,dx,cost in steps:
            ny,nx=y+dy,x+dx
            if not(0<=ny<h and 0<=nx<w) or not row[ny,nx]:continue
            if dy and dx and not(row[y,nx] and row[ny,x]):continue
            ng=g+cost*(cost_l if penalty is None else cost_l*penalty[l][ny,nx]);key=(l,ny,nx)
            if ng<get(key,inf):
                best[key]=ng;prev[key]=(l,y,x);heapq.heappush(heap,(ng+hdist[ny,nx],ng,l,ny,nx))
        thr=through[y,x]
        if thr or via_ok[y,x]:
            for l2 in range(layers):
                if l2==l or not passable[l2,y,x]:continue
                ng=g+(0.5 if thr else via_cost);key=(l2,y,x)
                if ng<get(key,inf):
                    best[key]=ng;prev[key]=(l,y,x);heapq.heappush(heap,(ng+hdist[y,x],ng,l2,y,x))
    return None,expansions


def fill_partition(label,plane_id,clearance,res):
    """Map each blob of the plane net's own copper on one layer to its plane-fill region."""
    region=ndimage.distance_transform_edt(~((label!=0)&(label!=plane_id)))*res>=clearance
    comp,_=ndimage.label(region);blobs,n=ndimage.label(label==plane_id)
    found=ndimage.maximum(comp,blobs,range(1,n+1)) if n else []
    return [int(c) for c in np.atleast_1d(found)]


def fill_region_count(label,plane_id,clearance,res):
    """Connected plane-fill regions on one layer that hold the plane net's own copper."""
    return len({c for c in fill_partition(label,plane_id,clearance,res) if c})


def splits(before,after):
    """True if two copper blobs sharing a fill region before are separated after."""
    joined={}
    for b,a in zip(before,after):
        if b and joined.setdefault(b,a)!=a:return True
    return False


def route(dump,nets=(),rip=(),rip_first=False,res=0.1,layer_cost=None,via_cost=30.0,
          clearance=0.25,rail_nets=(),rail_width=0.4,signal_width=0.3,via_diameter=0.7,via_drill=0.3,
          hole_clearance=0.25,edge_clearance=0.5,max_expansions=4_000_000,allowed_layers=None,log=print,
          planes=None,signal_via_diameter=None,grow=None,window_mm=12.0,weight=1.0,full_board=False,
          escape_halo_mm=0.0,escape_halo_cost=4.0,fill_guards=None,fill_clearance=0.33,
          rrr_rounds=0,rrr_max_rip=4,rrr_soft_cost=12.0):
    """Return (results, removed_uuids). Each result has net, island pad names and a [layer,x,y,through] path or None.

    planes maps a net to its plane layer: every island of that net gets a short
    fanout ending in a through via inside the plane instead of a link to another island.
    grow adds clearance (mm) around existing copper of the named nets, e.g. rails
    whose net-class clearance exceeds the routed class.
    """
    rip=list(rip);planes=planes or {}
    removed={i['uuid'] for k in ('tracks','vias') for i in dump[k] if i['net'] in rip}
    raster=Raster(dump,res,removed,grow or {});L=len(raster.layers)
    # Outer layers cost more: new copper there cuts the surface pours.
    layer_cost=list(layer_cost) if layer_cost else [3.0 if name in ('F.Cu','B.Cu') else 1.0 for name in raster.layers]
    if len(layer_cost)!=L:raise ValueError('one layer cost per copper layer required')
    margin=res/SQRT2+0.01
    islands={n:[list(g) for g in groups] for n,groups in dump['islands'].items()}
    pads_by_uuid={p['uuid']:p for p in dump['pads']}
    for n in rip:islands[n]=[[p['uuid']] for p in dump['pads'] if p['net']==n]
    for n in planes:
        if n not in islands:islands[n]=[[p['uuid']] for p in dump['pads'] if p['net']==n]
    order=[n for n in (list(nets) or sorted(islands)) if n not in rip]
    order=rip+order if rip_first else order+rip
    allowed=[raster.layers.index(n) for n in (allowed_layers or raster.layers)]
    results=[]

    def search(N,w,vd,src,goal,goal_is_via,pad_window,exclude=(),soft=None):
        """soft: net ids whose copper is passable at a cost; returns (path, expanded) or, with soft, (path, blockers)."""
        extra=int(round(pad_window/res));guard=int(round(1.5/res))
        boxes=[np.argwhere(src.any(0))]
        if not goal_is_via:boxes.append(np.argwhere(src.any(0)|goal.any(0)))
        # A net's own bounding box plus margin almost always holds its route; a
        # whole-board retry rarely succeeds and dominates failure cost, so it is opt-in.
        windows=[(b.min(0),b.max(0)) for b in boxes]+([None] if full_board and not goal_is_via else [])
        for k,attempt in enumerate(windows):
            if attempt is None:y0,y1,x0,x1=0,raster.h,0,raster.w
            else:
                lo,hi=attempt;y0,y1=max(0,lo[0]-extra),min(raster.h,hi[0]+extra+1);x0,x1=max(0,lo[1]-extra),min(raster.w,hi[1]+extra+1)
            g0,g1,h0,h1=max(0,y0-guard),min(raster.h,y1+guard),max(0,x0-guard),min(raster.w,x1+guard)
            inner=(slice(y0-g0,y1-g0),slice(x0-h0,x1-h0));win=(slice(y0,y1),slice(x0,x1))
            free=np.zeros((L,y1-y0,x1-x0),bool);foreign_any=np.zeros((g1-g0,h1-h0),bool)
            soft_near=[None]*L;soft_any=np.zeros((g1-g0,h1-h0),bool)
            for li in range(L):
                lab=raster.label[li][g0:g1,h0:h1];foreign=(lab!=0)&(lab!=N)
                if soft is not None:
                    sm=np.isin(lab,soft)&foreign;foreign&=~sm;soft_any|=sm
                    if li in allowed and li not in exclude and sm.any():
                        dsoft,idx=ndimage.distance_transform_edt(~sm,return_indices=True)
                        near=(dsoft[inner]*res<clearance+w/2+margin)
                        soft_near[li]=np.where(near,lab[idx[0],idx[1]][inner],0)
                foreign_any|=foreign
                if li in allowed and li not in exclude:
                    dist=ndimage.distance_transform_edt(~foreign)[inner]*res
                    free[li]=(dist>=clearance+w/2+margin)&(raster.d_edge[win]>=edge_clearance+w/2+margin)&(raster.d_keep_track[li][win]>=w/2+margin)
            vr=vd/2
            dist_any=ndimage.distance_transform_edt(~foreign_any)[inner]*res
            d_hole=ndimage.distance_transform_edt(~raster.hole[g0:g1,h0:h1])[inner]*res
            via_ok=((dist_any>=clearance+vr+margin)&(raster.d_edge[win]>=edge_clearance+vr+margin)&(raster.d_keep_via[win]>=vr+margin)
                    &(d_hole>=vr+hole_clearance+margin)&(raster.d_smd[win]>=vr+margin))
            s=src[:,y0:y1,x0:x1]
            gl=(np.broadcast_to(via_ok,s.shape)&~s&free) if goal_is_via else goal[:,y0:y1,x0:x1]
            if not s.any() or not gl.any():continue
            penalty=None
            if escape_halo_mm:
                # Keep inner-layer copper off the via-escape ring around other SMD pads.
                halo=raster.d_smd[win]<=escape_halo_mm
                penalty=[np.where(halo,escape_halo_cost,1.0) if raster.layers[li] not in ('F.Cu','B.Cu') else None for li in range(L)]
                penalty=[pp if pp is not None else np.ones(halo.shape) for pp in penalty]
            if soft is not None:
                # Rip-up probe: copper of soft nets costs extra instead of blocking.
                base=penalty or [np.ones(s.shape[1:]) for _ in range(L)]
                penalty=[np.where(soft_near[li]>0,base[li]*rrr_soft_cost,base[li]) if soft_near[li] is not None else base[li] for li in range(L)]
                if soft_any.any():
                    dvia,vidx=ndimage.distance_transform_edt(~soft_any,return_indices=True)
            path,expanded=astar(free,via_ok,s,gl,layer_cost,via_cost,max_expansions if k else min(max_expansions,300_000),weight,penalty)
            if path is not None and soft is not None:
                blockers=set()
                for i,(l,y,x) in enumerate(path):
                    if soft_near[l] is not None and soft_near[l][y,x]:blockers.add(int(soft_near[l][y,x]))
                    if i and path[i-1][0]!=l and soft_any.any() and dvia[inner][y,x]*res<clearance+vd/2+margin:
                        yy,xx=vidx[0][inner][y,x],vidx[1][inner][y,x]
                        for li in range(L):
                            v=raster.label[li][g0+yy,h0+xx]
                            if v in soft:blockers.add(int(v))
                return [(l,y+y0,x+x0) for l,y,x in path],blockers
            if path is not None:return [(l,y+y0,x+x0) for l,y,x in path],expanded
            if goal_is_via:break
        return None,0

    def commit(net,N,w,vd,names,path,src,goal,end_via):
        out=[]
        for l,y,x in path:
            px,py=raster.point(y,x);through=bool(src[:,y,x].all() or (goal is not None and goal[:,y,x].all()))
            out.append([raster.layers[l],px,py,int(through)])
        if end_via:out.append([raster.layers[(path[-1][0]+1)%L],out[-1][1],out[-1][2],0])
        vias=sum(1 for p,q in zip(out,out[1:]) if p[0]!=q[0] and not q[3])
        log(f'PATH {net} {names} cells {len(path)} vias {vias}')
        results.append({'net':net,'island':names,'path':out,'width_nm':int(round(w*1e6)),'via_diameter_nm':int(round(vd*1e6))})
        for i,(l,y,x) in enumerate(path):
            px,py=raster.point(y,x)
            raster.segment(l,(px,py),(px,py),w*1e6+2*raster.step,N)
            if i and path[i-1][0]!=l and not out[i][3]:raster.via((px,py),vd*1e6,via_drill*1e6,N)
        if end_via:
            px,py=raster.point(path[-1][1],path[-1][2]);raster.via((px,py),vd*1e6,via_drill*1e6,N)

    # Fill guards: a signal path may share a plane-fill layer only if the fill keeps
    # every plane via/pad in as few connected regions as before.
    guards={raster.layers.index(layer):raster.net_id[n] for n,layer in (fill_guards or {}).items() if n in raster.net_id}
    # Zone clearance plus half the minimum fill width approximates where the native fill can pass.
    fill_regions=lambda li,lab:fill_partition(lab,guards[li],fill_clearance,res)
    fill_count={li:fill_regions(li,raster.label[li]) for li in guards}
    def fill_ok(path,w,vd,src,goal):
        # Vias pierce every layer, so any layer change can also cut a fill.
        vias=any(path[i][0]!=path[i-1][0] for i in range(1,len(path)))
        used=[li for li in guards if vias or any(l==li for l,_,_ in path)]
        if not used:return True
        for li in used:
            lab=raster.label[li].copy()
            for i,(l,y,x) in enumerate(path):
                px,py=raster.point(y,x)
                if l==li:
                    m,sl=raster.segment_mask((px,py),(px,py),w*1e6+2*raster.step);lab[sl][m]=-1
                elif i and path[i-1][0]!=l:
                    m,sl=raster.disc((px,py),vd*1e6/2);lab[sl][m]=-1
            if splits(fill_count[li],fill_regions(li,lab)):return False
        return True

    name=lambda g:[pads_by_uuid[u]['ref']+'.'+pads_by_uuid[u]['pad'] for u in g if u in pads_by_uuid]
    def net_params(net):
        rail=net in rail_nets or net in planes
        return (rail_width if rail else signal_width),(via_diameter if rail or not signal_via_diameter else signal_via_diameter)
    failed=[]

    def route_one(net,src,reached,names):
        N=raster.net_id[net];w,vd=net_params(net)
        path,_=search(N,w,vd,src,reached,False,window_mm)
        if path is not None and guards and not fill_ok(path,w,vd,src,reached):
            path,_=search(N,w,vd,src,reached,False,window_mm,exclude=tuple(guards))
            if path is not None and not fill_ok(path,w,vd,src,reached):path=None
        if path is None:return False
        i0=max(i for i,(l,y,x) in enumerate(path) if src[l,y,x])
        i1=min(i for i,(l,y,x) in enumerate(path) if reached[l,y,x] and i>=i0)
        path=path[i0:i1+1]
        commit(net,N,w,vd,names,path,src,reached,False)
        if guards:fill_count.update({li:fill_regions(li,raster.label[li]) for li in guards})
        for l,y,x in path:reached[l,y,x]=True
        return True

    def route_groups(net,groups,record=True):
        main=max(range(len(groups)),key=lambda i:len(groups[i]))
        reached=island_mask(raster,dump,groups[main]);ok=True
        for gi,g in enumerate(groups):
            if gi==main:continue
            src=island_mask(raster,dump,g)
            if route_one(net,src,reached,name(g)):reached|=src;continue
            ok=False
            if record:
                log(f'NOPATH {net} {name(g)}');results.append({'net':net,'island':name(g),'path':None});failed.append((net,g,groups[main]))
        return ok

    rippable={raster.net_id[n] for n in raster.net_id if n not in rail_nets and n not in planes and n not in (fill_guards or {}) and n!='AGND'}
    pads_by_net=collections.defaultdict(list)
    for p in dump['pads']:pads_by_net[p['net']].append(p)

    def rip_up_and_reroute():
        """Rip a few blocking signal nets, route the failed island, then reroute the ripped nets."""
        nonlocal results,removed
        id_net={v:k for k,v in raster.net_id.items()}
        for rnd in range(rrr_rounds):
            pending=[f for f in failed];failed.clear();fixed=0
            for net,g,main_group in pending:
                N=raster.net_id[net];w,vd=net_params(net)
                src=island_mask(raster,dump,g);reached=island_mask(raster,dump,main_group)
                for r in results:
                    if r['net']==net and r['path']:
                        for lay,x,y,_ in r['path']:
                            j,i=raster.cell(x,y);reached[raster.layers.index(lay),j,i]=True
                if route_one(net,src,reached,name(g)):
                    results[:]=[r for r in results if not (r['net']==net and r['path'] is None and r['island']==name(g))];fixed+=1;continue
                probe,blockers=search(N,w,vd,src,reached,False,window_mm,soft=sorted(rippable-{N}))
                if probe is None or not blockers or len(blockers)>rrr_max_rip:
                    failed.append((net,g,main_group));continue
                snapshot=(raster.label.copy(),raster.hole.copy(),[dict(r) for r in results],set(removed),dict(fill_count))
                victims=[id_net[b] for b in blockers]
                for b in blockers:
                    raster.label[raster.label==b]=0
                    for pad in pads_by_net[id_net[b]]:
                        if pad['poly']:
                            m,sl=raster.polygon(pad['poly'])
                            for lay in pad['layers']:raster.label[raster.layers.index(lay)][sl][m]=b
                results[:]=[r for r in results if r['net'] not in victims]
                removed|={i['uuid'] for k in ('tracks','vias') for i in dump[k] if i['net'] in victims}
                if guards:fill_count.update({li:fill_regions(li,raster.label[li]) for li in guards})
                ok=route_one(net,src,reached,name(g))
                for v in victims:
                    if not ok:break
                    ok=route_groups(v,[[p['uuid']] for p in pads_by_net[v]],record=False)
                if ok:
                    results[:]=[r for r in results if not (r['net']==net and r['path'] is None and r['island']==name(g))]
                    fixed+=1;log(f'RRR {net} {name(g)} ripped {victims}')
                else:
                    raster.label[...]=snapshot[0];raster.hole[...]=snapshot[1];results[:]=snapshot[2];removed.clear();removed|=snapshot[3];fill_count.clear();fill_count.update(snapshot[4])
                    failed.append((net,g,main_group))
            log(f'RRR round {rnd+1}: fixed {fixed}, still failing {len(failed)}')
            if not fixed:break

    for net in order:
        if net not in islands or net not in raster.net_id:continue
        N=raster.net_id[net];rail=net in rail_nets or net in planes
        w=rail_width if rail else signal_width;vd=via_diameter if rail or not signal_via_diameter else signal_via_diameter
        groups=islands[net]
        name=lambda g:[pads_by_uuid[u]['ref']+'.'+pads_by_uuid[u]['pad'] for u in g if u in pads_by_uuid]
        if net in planes:
            for g in groups:
                src=island_mask(raster,dump,g)
                if src.all(0).any():continue  # through-hole copper already reaches every layer
                path,expanded=search(N,w,vd,src,None,True,3.0)
                if path is None:
                    log(f'NOPATH {net} {name(g)} plane fanout');results.append({'net':net,'island':name(g),'path':None});continue
                i0=max(i for i,(l,y,x) in enumerate(path) if src[l,y,x]);path=path[i0:]
                commit(net,N,w,vd,name(g),path,src,None,True)
            continue
        route_groups(net,groups)

    if rrr_rounds:
        rip_up_and_reroute()
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
                rows.append({'kind':'via','uuid':uid,'net':r['net'],'at_nm':q[1:3],'diameter_nm':r.get('via_diameter_nm',int(round(via_diameter*1e6))),
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
    p.add_argument('--via-cost',type=float,default=30.0);p.add_argument('--layer-cost',default='',help='one cost per copper layer; default 3 outer, 1 inner')
    p.add_argument('--planes',default='',help='NET:LAYER pairs whose islands fan out to a via into that plane')
    p.add_argument('--grow',default='',help='NET:mm pairs of extra clearance around existing copper')
    p.add_argument('--signal-via-diameter',type=float);p.add_argument('--window-mm',type=float,default=12.0)
    p.add_argument('--weight',type=float,default=1.0,help='heuristic inflation (>1 is faster, bounded suboptimal)')
    p.add_argument('--full-board',action='store_true',help='retry failed islands on the whole board')
    p.add_argument('--escape-halo-mm',type=float,default=0.0,help='inner-layer cost penalty radius around SMD pads')
    p.add_argument('--fill-guards',default='',help='NET:LAYER plane fills that signal paths must not split')
    p.add_argument('--layers',default='',help='allowed routing layers (default: all)');p.add_argument('--max-expansions',type=int,default=4_000_000)
    a=p.parse_args()
    dump=json.loads(a.dump.read_text())
    split=lambda s:[x for x in s.split(',') if x]
    results,removed=route(dump,split(a.nets),split(a.rip),a.rip_first,a.res,[float(x) for x in split(a.layer_cost)] or None,a.via_cost,
                          a.clearance,split(a.rail_nets),a.rail_width,a.signal_width,max_expansions=a.max_expansions,
                          allowed_layers=split(a.layers) or None,log=lambda m:print(m,flush=True),
                          planes=dict(x.rsplit(':',1) for x in split(a.planes)),signal_via_diameter=a.signal_via_diameter,
                          grow={k:float(v) for k,v in (x.rsplit(':',1) for x in split(a.grow))},window_mm=a.window_mm,weight=a.weight,full_board=a.full_board,escape_halo_mm=a.escape_halo_mm,
                          fill_guards=dict(x.rsplit(':',1) for x in split(a.fill_guards)))
    rows,links=copper_rows(results,a.board_id,a.tag)
    a.output.write_text(json.dumps({'status':'UNCHECKED PROPOSAL; native DRC/parity/ground gates required','board_sha256':dump['board_sha256'],
                                    'removed_uuids':removed,'copper':rows,'links':links,
                                    'unrouted':[{'net':r['net'],'island':r['island']} for r in results if not r['path']]},indent=1)+'\n')
    print(f'{len(links)} links, {len(rows)} copper rows, {len(removed)} ripped objects, {sum(1 for r in results if not r["path"])} unrouted')
if __name__=='__main__':main()
