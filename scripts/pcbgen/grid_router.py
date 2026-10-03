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
import argparse,collections,heapq,json,math,os,sys
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


_LIB=None


def native_astar():
    """Compile grid_astar.c once into the repository cache; None if no C compiler is available."""
    global _LIB
    if _LIB is None:
        import ctypes,hashlib,shutil,subprocess
        source=Path(__file__).with_name('grid_astar.c');_LIB=False
        cc=shutil.which('cc') or shutil.which('gcc')
        if cc and source.exists():
            out=ROOT/'.circuit-cache'/f"grid_astar-{hashlib.sha256(source.read_bytes()).hexdigest()[:12]}.so"
            out.parent.mkdir(exist_ok=True)
            if not out.exists():
                done=subprocess.run([cc,'-O2','-shared','-fPIC','-o',str(out),str(source)],capture_output=True)
                if done.returncode:return None
            lib=ctypes.CDLL(str(out));P=ctypes.c_void_p
            lib.grid_astar.restype=ctypes.c_long
            lib.grid_astar.argtypes=[ctypes.c_int]*3+[P]*8+[ctypes.c_long,P,ctypes.c_long,P]
            _LIB=lib
    return _LIB or None


def astar(free,via_ok,src,goal,layer_cost,via_cost,max_expansions,weight=1.0,penalty=None):
    lib=native_astar()
    if lib is not None:
        import ctypes
        L,h,w=free.shape
        passable=np.ascontiguousarray(free|src|goal,dtype=np.uint8)
        cost=np.empty((L,h,w),np.float32)
        for l in range(L):cost[l]=layer_cost[l]*(penalty[l] if penalty is not None else 1.0)
        through=np.ascontiguousarray(src.all(0)|goal.all(0),dtype=np.uint8)
        hdist=np.ascontiguousarray(ndimage.distance_transform_edt(~goal.any(0))*weight,dtype=np.float32)
        vcost=np.ascontiguousarray(np.broadcast_to(np.asarray(via_cost,np.float32),(h,w)))
        arrays=[passable,cost,np.ascontiguousarray(via_ok,dtype=np.uint8),through,
                np.ascontiguousarray(src,dtype=np.uint8),np.ascontiguousarray(goal,dtype=np.uint8),hdist,vcost]
        cap=4*(h+w)*L+100000;out=np.empty(cap,np.int32);expanded=ctypes.c_long(0)
        n=lib.grid_astar(L,h,w,*[a.ctypes.data for a in arrays],int(max_expansions),out.ctypes.data,cap,ctypes.byref(expanded))
        if n<0:return None,expanded.value
        idx=out[:n][::-1];plane=h*w
        return [(int(i//plane),int(i%plane//w),int(i%w)) for i in idx],expanded.value
    return astar_py(free,via_ok,src,goal,layer_cost,via_cost,max_expansions,weight,penalty)


def astar_py(free,via_ok,src,goal,layer_cost,via_cost,max_expansions,weight=1.0,penalty=None):
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
                ng=g+(0.5 if thr else (via_cost if np.isscalar(via_cost) else float(via_cost[y,x])));key=(l2,y,x)
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
          escape_halo_mm=0.0,escape_halo_cost=4.0,fill_guards=None,fill_clearance=0.45,
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
    # Stricter than the native fill (zone clearance, minimum width and raster slack) so a pass here is a pass there.
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
                    log(f"RRR-SKIP {net} {name(g)} {'no probe path' if probe is None else f'{len(blockers)} blockers'}")
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
                    log(f"RRR-UNDO {net} {name(g)} victims {victims}")
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


_NEGOTIATE_ROUTE=None


def _negotiate_worker(job):
    net,pfac=job
    return net,_NEGOTIATE_ROUTE(net,pfac)


def negotiate(dump,nets,res=0.1,layer_cost=None,via_cost=30.0,clearance=0.2,width=0.2,via_diameter=0.6,via_drill=0.3,
              hole_clearance=0.25,edge_clearance=0.5,allowed_layers=None,grow=None,iterations=30,present=0.5,present_growth=1.6,
              history=1.0,margin_mm=4.0,wide_margin_mm=12.0,max_expansions=2_000_000,log=print,workers=1,waves=4,
              fill_guards=None,fill_clearance=0.45,state_path=None,deadline=None):
    """PathFinder-style negotiated routing of whole signal nets.

    All copper of the named nets is ripped and every net is rerouted from its pads.
    Other nets' tracks may overlap at a rising cost; cells that stay shared collect
    history cost, so contested nets spread out over the iterations. Vias never
    share space. Returns (results, removed_uuids); nets still in conflict after the
    last iteration come back with path None for a later sequential pass.

    With state_path the negotiation state is saved after every iteration and resumed
    on the next call; past the deadline (time.time()) it saves and returns (None, None).
    Nets that cannot be connected at all are reported with their reason in `failures`.
    """
    import pickle,time
    nets=[n for n in nets if any(p['net']==n for p in dump['pads'])]
    removed={i['uuid'] for k in ('tracks','vias') for i in dump[k] if i['net'] in nets}
    raster=Raster(dump,res,removed,grow or {});L=len(raster.layers);H,W=raster.h,raster.w
    layer_cost=list(layer_cost) if layer_cost else [3.0 if n in ('F.Cu','B.Cu') else 1.0 for n in raster.layers]
    allowed=[raster.layers.index(n) for n in (allowed_layers or raster.layers)]
    margin=res/SQRT2+0.01;vr=via_diameter/2
    foreign=[raster.label[l]!=0 for l in range(L)]
    static_free=np.zeros((L,H,W),bool)
    for l in allowed:
        static_free[l]=((ndimage.distance_transform_edt(~foreign[l])*res>=clearance+width/2+margin)
                        &(raster.d_edge>=edge_clearance+width/2+margin)&(raster.d_keep_track[l]>=width/2+margin))
    any_copper=np.any(foreign,axis=0)
    static_via=((ndimage.distance_transform_edt(~any_copper)*res>=clearance+vr+margin)&(raster.d_edge>=edge_clearance+vr+margin)
                &(raster.d_keep_via>=vr+margin)&(ndimage.distance_transform_edt(~raster.hole)*res>=vr+hole_clearance+margin)
                &(raster.d_smd>=vr+margin))
    disc=lambda r:(lambda k:(np.add.outer(np.arange(-k,k+1)**2,np.arange(-k,k+1)**2)<=(r/res)**2))(int(math.ceil(r/res)))
    # Track cells conflict with another track within width+clearance and with a via within the via spacing.
    occ_track=np.zeros((L,H,W),np.int16);occ_via=np.zeros((H,W),np.int16);hist=np.zeros((L,H,W),np.float32);hist_via=np.zeros((H,W),np.float32)
    pads={p['uuid']:p for p in dump['pads']}
    pads_by_net={n:[p for p in dump['pads'] if p['net']==n] for n in nets}
    routes={}

    def near(mask,r,y0,x0):
        # Cells within r of the mask, computed on the mask's own bounding box only.
        ys,xs=np.nonzero(mask);k=int(math.ceil(r/res))
        a0,a1=max(0,ys.min()-k),min(mask.shape[0],ys.max()+k+1);b0,b1=max(0,xs.min()-k),min(mask.shape[1],xs.max()+k+1)
        sub=ndimage.distance_transform_edt(~mask[a0:a1,b0:b1])<=r/res
        # Bit-packed: hundreds of routes stay resident and travel between processes.
        return y0+a0,y0+a1,x0+b0,x0+b1,np.packbits(sub)

    def unpack(a0,a1,b0,b1,bits):
        return np.unpackbits(bits,count=(a1-a0)*(b1-b0)).reshape(a1-a0,b1-b0).astype(bool)

    def footprint(cl,vias,box):
        # Occupancy one route adds: (layer or None for all, y0, y1, x0, x1, cells) for tracks and for vias.
        (y0,_),(x0,_)=box;track=[];via=[]
        for l in range(L):
            if cl[l].any():track.append((l,*near(cl[l],width+clearance+margin,y0,x0)))
        if vias.any():
            track.append((None,*near(vias,vr+clearance+width/2+margin,y0,x0)))
            via.append(near(vias,2*vr+clearance+margin,y0,x0))
        anyl=cl.any(0)
        if anyl.any():via.append(near(anyl,vr+clearance+width/2+margin,y0,x0))
        return track,via

    def stamp(net,route,sign):
        track,via=route[2:4]
        for l,*box in track:
            sub=unpack(*box).astype(np.int16);a0,a1,b0,b1=box[:4]
            if l is None:occ_track[:,a0:a1,b0:b1]+=sign*sub[None]
            else:occ_track[l,a0:a1,b0:b1]+=sign*sub
        for box in via:a0,a1,b0,b1=box[:4];occ_via[a0:a1,b0:b1]+=sign*unpack(*box).astype(np.int16)

    def own_at(entries,ls,ys,xs):
        # The route's own occupancy at the given cells (ls None for the via plane).
        own=np.zeros(len(ys),np.int16)
        for e in entries:
            l,box=(e[0],e[1:]) if ls is not None else (None,e);a0,a1,b0,b1=box[:4]
            sel=(ys>=a0)&(ys<a1)&(xs>=b0)&(xs<b1)
            if ls is not None and l is not None:sel&=ls==l
            if sel.any():own[sel]+=unpack(*box)[ys[sel]-a0,xs[sel]-b0]
        return own

    def route_net(net,pfac):
        # Retry wider with a larger budget and an inflated heuristic (cost within weight x optimal):
        # under heavy congestion costs an exact search can exhaust its budget on a routable net.
        for window,budget,weight in ((margin_mm,max_expansions,1.0),(wide_margin_mm,3*max_expansions,1.3),(wide_margin_mm,3*max_expansions,2.5)):
            r=route_window(net,pfac,max(margin_mm,window),budget,weight)
            if r[0]!='fail' or 'search limit' not in r[1]:return r
        return r

    def route_window(net,pfac,margin_mm,max_expansions,weight):
        N=raster.net_id[net];group=pads_by_net[net]
        if len(group)<2:return 'fail','single pad'
        pts=np.array([p['xy'] for p in group],float)
        lo=pts.min(0)-margin_mm*1e6;hi=pts.max(0)+margin_mm*1e6
        sl=raster.window(lo,hi);(y0,y1),(x0,x1)=(sl[0].start,sl[0].stop),(sl[1].start,sl[1].stop)
        free=static_free[:,y0:y1,x0:x1].copy();via_ok=static_via[y0:y1,x0:x1].copy()
        # Clearance to the net's own pads does not apply: recompute next to them.
        own=np.zeros((L,y1-y0,x1-x0),bool)
        for p in group:
            m,psl=raster.polygon(p['poly'],conservative=False) if p['poly'] else (None,None)
            if m is None:continue
            ys=slice(psl[0].start-y0,psl[0].stop-y0);xs=slice(psl[1].start-x0,psl[1].stop-x0)
            for name in p['layers']:own[raster.layers.index(name)][ys,xs]|=m
        reach=int(math.ceil((clearance+width/2+margin)/res))+2
        pad_zone=ndimage.binary_dilation(own.any(0),iterations=reach)
        if pad_zone.any():
            # Recompute clearance only around the own pads (bounding box plus the clearance reach).
            ys,xs=np.nonzero(pad_zone);a0,a1=max(0,ys.min()-reach),ys.max()+reach+1;b0,b1=max(0,xs.min()-reach),xs.max()+reach+1
            for l in allowed:
                fl=foreign[l][y0+a0:y0+a1,x0+b0:x0+b1]&(raster.label[l][y0+a0:y0+a1,x0+b0:x0+b1]!=N)
                local=((ndimage.distance_transform_edt(~fl)*res>=clearance+width/2+margin)
                       &(raster.d_edge[y0+a0:y0+a1,x0+b0:x0+b1]>=edge_clearance+width/2+margin)&(raster.d_keep_track[l][y0+a0:y0+a1,x0+b0:x0+b1]>=width/2+margin))
                free[l][a0:a1,b0:b1]|=pad_zone[a0:a1,b0:b1]&local
        # Vias negotiate too: a contested via site costs more instead of being forbidden.
        vcost=via_cost*(1.0+hist_via[y0:y1,x0:x1])*(1.0+pfac*occ_via[y0:y1,x0:x1])
        cost=[(1.0+hist[l,y0:y1,x0:x1])*(1.0+pfac*occ_track[l,y0:y1,x0:x1]) for l in range(L)]
        masks=[]
        for p in group:
            m=np.zeros((L,y1-y0,x1-x0),bool)
            if p['poly']:
                pm,psl=raster.polygon(p['poly'],conservative=False)
                ys=slice(psl[0].start-y0,psl[0].stop-y0);xs=slice(psl[1].start-x0,psl[1].stop-x0)
                for name in p['layers']:m[raster.layers.index(name)][ys,xs]|=pm
            masks.append(m)
        through=np.zeros((y1-y0,x1-x0),bool)
        for m in masks:through|=m.all(0)
        reached=masks[0].copy();cl=np.zeros((L,y1-y0,x1-x0),bool);vias=np.zeros((y1-y0,x1-x0),bool);paths=[]
        order=sorted(range(1,len(group)),key=lambda i:float(np.hypot(*(pts[i]-pts[0]))))
        for i in order:
            src=masks[i]
            if (src&reached).any():continue
            path,expanded=astar(free,via_ok,src,reached,layer_cost,vcost,max_expansions,weight,cost)
            if path is None:
                pad=group[i]['ref']+'.'+group[i]['pad']
                rim=ndimage.binary_dilation(src,structure=np.ones((1,3,3),bool))&~src
                if not (rim&free).any():return 'fail',f'{pad} boxed in (no free cell next to the pad)'
                if expanded>max_expansions:return 'fail',f'{pad} search limit ({margin_mm:g} mm window)'
                return 'fail',f'{pad} no path ({margin_mm:g} mm window)'
            i0=max(k for k,(l,y,x) in enumerate(path) if src[l,y,x]);i1=min(k for k,(l,y,x) in enumerate(path) if reached[l,y,x] and k>=i0)
            path=path[i0:i1+1]
            for k,(l,y,x) in enumerate(path):
                cl[l,y,x]=True;reached[l,y,x]=True
                if k and path[k-1][0]!=l and not through[y,x]:vias[y,x]=True
            reached|=src
            paths.append([(l,y+y0,x+x0,int(through[y,x])) for l,y,x in path])
        ownpad=np.zeros((L,y1-y0,x1-x0),bool)
        for m in masks:ownpad|=m
        # Track inside the net's own pads is pad copper, already kept clear of other nets.
        cl&=~ownpad;fp=footprint(cl,vias,((y0,y1),(x0,x1)))
        ls,ys,xs=np.nonzero(cl);vy,vx=np.nonzero(vias)
        # Stored sparse in board coordinates; the dense window arrays are dropped here.
        return ((ls.astype(np.int8),(ys+y0).astype(np.int32),(xs+x0).astype(np.int32)),((vy+y0).astype(np.int32),(vx+x0).astype(np.int32)),*fp),paths

    order=sorted(nets,key=lambda n:len(pads_by_net[n]))
    pfac=present;conflicted=set(order);start=0;failures={}
    key=(2,res,tuple(order),raster.h,raster.w)
    if state_path and os.path.exists(state_path):
        with open(state_path,'rb') as f:st=pickle.load(f)
        if st['key']==key:
            hist[tuple(st['hist'][0])]=st['hist'][1];hist_via[tuple(st['hist_via'][0])]=st['hist_via'][1];routes.update(st['routes']);pfac=st['pfac']
            conflicted=st['conflicted'];start=st['iteration'];failures=st['failures']
            for net,r in routes.items():stamp(net,r[0],+1)
            log(f'NEGOTIATE resumed after iteration {start}: {len(routes)} nets routed, {len(conflicted)} in conflict')
    def save(it):
        if not state_path:return
        with open(state_path+'.tmp','wb') as f:
            sparse=lambda a:(lambda i:(i,a[tuple(i)]))(np.array(np.nonzero(a)))
            pickle.dump({'key':key,'hist':sparse(hist),'hist_via':sparse(hist_via),'routes':routes,'pfac':pfac,'conflicted':conflicted,'iteration':it,'failures':failures},f)
        os.replace(state_path+'.tmp',state_path)
    global _NEGOTIATE_ROUTE
    for it in range(start,iterations):
        if deadline and time.time()>deadline:
            log(f'NEGOTIATE deadline reached before iteration {it+1}; state saved for resume');return None,None
        failed=0;batch=[n for n in order if not it or n in conflicted or n not in routes]
        if workers>1:
            # Waves of parallel routing: each wave sees the congestion of all earlier waves.
            import multiprocessing
            for wave in (batch[i::waves] for i in range(waves)):
                for net in wave:
                    if net in routes:stamp(net,routes.pop(net)[0],-1)
                _NEGOTIATE_ROUTE=route_net
                with multiprocessing.get_context('fork').Pool(workers) as pool:
                    done=pool.map(_negotiate_worker,[(n,pfac) for n in wave],chunksize=4)
                for net,r in done:
                    if r[0]=='fail':failed+=1;failures[net]=r[1];continue
                    failures.pop(net,None);routes[net]=r;stamp(net,r[0],+1)
        else:
            for net in batch:
                if net in routes:stamp(net,routes[net][0],-1)
                r=route_net(net,pfac)
                if r[0]=='fail':routes.pop(net,None);failed+=1;failures[net]=r[1];continue
                failures.pop(net,None);routes[net]=r;stamp(net,r[0],+1)
        conflicted=set()
        for net,(((ls,ys,xs),(vy,vx),track,via),_) in routes.items():
            hot=occ_track[ls,ys,xs]-own_at(track,ls,ys,xs)>0
            if hot.any():conflicted.add(net);np.add.at(hist,(ls[hot],ys[hot],xs[hot]),history)
            vhot=occ_via[vy,vx]-own_at(via,None,vy,vx)>0
            if vhot.any():conflicted.add(net);np.add.at(hist_via,(vy[vhot],vx[vhot]),history)
        log(f'NEGOTIATE iteration {it+1}: {len(routes)} nets routed, {len(conflicted)} in conflict, {failed} unroutable')
        save(it+1)
        if it==start:
            for net,why in sorted(failures.items()):log(f'NEGOTIATE unroutable {net}: {why}')
        if not conflicted:break
        # Every net touching a contested cell is rerouted next round.
        pfac*=present_growth
    for net,why in sorted(failures.items()):log(f'NEGOTIATE unroutable {net}: {why}')
    # Plane fills sharing a signal layer: accept routes one by one, dropping any that split the fill.
    split_dropped=set()
    for gname,glayer in (fill_guards or {}).items():
        if gname not in raster.net_id:continue
        gl=raster.layers.index(glayer);P=raster.net_id[gname];lab=raster.label[gl].copy()
        base=fill_partition(lab,P,fill_clearance,res);k_cl=disc(width/2+res);k_v=disc(vr)
        for net in order:
            r=routes.get(net)
            if r is None or net in conflicted or net in split_dropped:continue
            (ls,ys,xs),(vy,vx)=r[0][:2];trial=lab.copy()
            for cy,cx,k in ((ys[ls==gl],xs[ls==gl],k_cl),(vy,vx,k_v)):
                if not len(cy):continue
                h=k.shape[0]//2;a0,b0=max(0,cy.min()-h),max(0,cx.min()-h);a1,b1=min(raster.h,cy.max()+h+1),min(raster.w,cx.max()+h+1)
                m=np.zeros((a1-a0,b1-b0),bool);m[cy-a0,cx-b0]=True
                trial[a0:a1,b0:b1][ndimage.binary_dilation(m,structure=k)]=-1
            after=fill_partition(trial,P,fill_clearance,res)
            if splits(base,after):split_dropped.add(net);continue
            lab=trial;base=after
        log(f'NEGOTIATE {gname} fill guard dropped {len(split_dropped)} nets')
    results=[]
    name=lambda p:p['ref']+'.'+p['pad']
    for net in order:
        r=routes.get(net)
        if r is None or net in conflicted or net in split_dropped:
            results.append({'net':net,'island':[name(p) for p in pads_by_net[net]],'path':None});continue
        for path in r[1]:
            out=[]
            for l,y,x,thr in path:
                px,py=raster.point(y,x);out.append([raster.layers[l],px,py,thr])
            results.append({'net':net,'island':[name(p) for p in pads_by_net[net]],'path':out,'width_nm':int(round(width*1e6)),'via_diameter_nm':int(round(via_diameter*1e6))})
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
