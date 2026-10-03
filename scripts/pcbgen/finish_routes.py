#!/usr/bin/env python3
"""Grid maze finishing pass for the few connections a heuristic router left open.

Run through scripts/kicad/run.sh after route.sh. Pads, footprints, holes,
keepouts and zones never move. Nets that still have more than one native
connectivity cluster get new tracks and vias. When no path exists, the pass may
rip up the tracks and vias of the fewest blocking nets and route those nets
again (bounded rounds). The caller must re-run full native DRC with schematic
parity (check.sh or route.sh) before keeping the result. Draft only.
"""
from __future__ import annotations
import argparse,heapq,json,math,os,subprocess,sys
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.definition import load_definition

GRID_MM=0.1
MARGIN_MM=0.03
VIA_COST=25.0
TURN_COST=0.4
RIP_COST=60.0
PROTECTED_RIP_COST=240.0
MAX_EXPANSIONS=4_000_000
LAYERS=(pcbnew.F_Cu,pcbnew.B_Cu)
DIRECTIONS=((1,0,1.0),(-1,0,1.0),(0,1,1.0),(0,-1,1.0),(1,1,math.sqrt(2)),(1,-1,math.sqrt(2)),(-1,1,math.sqrt(2)),(-1,-1,math.sqrt(2)))
BLOCKED=-1


def mm(value):return pcbnew.FromMM(value)
def point_seg(point):return pcbnew.SEG(point,point)


class Grid:
    def __init__(self,box,pitch):
        self.x0=box.GetLeft();self.y0=box.GetTop();self.pitch=mm(pitch)
        self.nx=box.GetWidth()//self.pitch+1;self.ny=box.GetHeight()//self.pitch+1
    def point(self,ix,iy):return pcbnew.VECTOR2I(self.x0+ix*self.pitch,self.y0+iy*self.pitch)
    def cells(self,bbox,inflate):
        left=max(0,(bbox.GetLeft()-inflate-self.x0)//self.pitch);right=min(self.nx-1,(bbox.GetRight()+inflate-self.x0)//self.pitch+1)
        top=max(0,(bbox.GetTop()-inflate-self.y0)//self.pitch);bottom=min(self.ny-1,(bbox.GetBottom()+inflate-self.y0)//self.pitch+1)
        for iy in range(top,bottom+1):
            for ix in range(left,right+1):yield ix,iy
    def index(self,ix,iy):return iy*self.nx+ix


def mark(layer_map,grid,shape,bbox,inflate,owner):
    for ix,iy in grid.cells(bbox,inflate):
        if shape.Collide(point_seg(grid.point(ix,iy)),inflate):
            k=grid.index(ix,iy);current=layer_map[k]
            if current==0:layer_map[k]=owner
            elif current!=owner:layer_map[k]=BLOCKED


def classes_for(definition):
    by_net={};default=None
    for spec in definition.routing['net_classes']:
        if spec['name']=='Default':default=spec
        for net in spec['nets']:by_net[net]=spec
    return by_net,default


def clusters(board):
    board.BuildConnectivity();connectivity=board.GetConnectivity();connectivity.RecalculateRatsnest()
    seeds=[p for fp in board.GetFootprints() for p in fp.Pads()]+list(board.GetTracks())
    seen=set();result={}
    for item in seeds:
        if item.GetNetCode()<=0 or item.m_Uuid.AsString() in seen:continue
        members=[m for m in connectivity.GetConnectedItems(item) if m.Type()!=pcbnew.PCB_ZONE_T]
        keys={m.m_Uuid.AsString() for m in members}|{item.m_Uuid.AsString()}
        seen.update(keys)
        group=[item]+[m for m in members if m.m_Uuid.AsString()!=item.m_Uuid.AsString()]
        result.setdefault(item.GetNetCode(),[]).append(group)
    return {net:groups for net,groups in result.items() if len(groups)>1}


def item_layers(item):
    return [layer for layer in LAYERS if item.IsOnLayer(layer)]


class Maps:
    """Per-layer hard (pads, holes, keepouts, edge) and soft (tracks, vias) owners."""
    def __init__(self,size):
        self.hard={layer:[0]*size for layer in LAYERS};self.soft={layer:[0]*size for layer in LAYERS}


class Finisher:
    def __init__(self,board,definition):
        self.board=board;self.definition=definition
        settings=board.GetDesignSettings()
        self.hole_clearance=settings.m_HoleClearance;self.edge_clearance=settings.m_CopperEdgeClearance
        self.by_net,self.default=classes_for(definition)
        self.outline=board.GetBoardEdgesBoundingBox()
        self.grid=Grid(self.outline,GRID_MM)
        self.maps={};self.no_via={}
        self.nets=dict(board.GetNetsByNetcode())
        # Rails and ground keep their copper; only signal nets may be ripped up.
        self.protected={BLOCKED}|{board.FindNet(name).GetNetCode() for spec in definition.routing['net_classes'] if spec['name']!='Default' for name in spec['nets'] if board.FindNet(name)}

    def spec(self,netname):return self.by_net.get(netname,self.default)
    def name(self,net):return self.nets[net].GetNetname()

    def obstacle_maps(self,half_width,clearance):
        key=(half_width,clearance)
        if key in self.maps:return self.maps[key]
        maps=Maps(self.grid.nx*self.grid.ny)
        inflate=half_width+clearance+mm(MARGIN_MM)
        hole_inflate=half_width+self.hole_clearance+mm(MARGIN_MM)
        for fp in self.board.GetFootprints():
            for pad in fp.Pads():
                for layer in item_layers(pad):
                    mark(maps.hard[layer],self.grid,pad.GetEffectiveShape(layer),pad.GetBoundingBox(),inflate,pad.GetNetCode() or BLOCKED)
                if pad.HasHole():
                    hole=pad.GetEffectiveHoleShape()
                    for layer in LAYERS:mark(maps.hard[layer],self.grid,hole,pad.GetBoundingBox(),hole_inflate,BLOCKED)
        for item in self.board.GetTracks():self.add_item(maps,item,inflate,hole_inflate)
        keepout=half_width+mm(MARGIN_MM)
        for zone in self.board.Zones():
            if not zone.GetIsRuleArea() or not zone.GetDoNotAllowTracks():continue
            outline=zone.Outline()
            for layer in LAYERS:
                if zone.IsOnLayer(layer):mark(maps.hard[layer],self.grid,outline,zone.GetBoundingBox(),keepout,BLOCKED)
        edge=half_width+self.edge_clearance+mm(MARGIN_MM)
        g=self.grid
        xs=[ix for ix in range(g.nx) if g.x0+ix*g.pitch-self.outline.GetLeft()<edge or self.outline.GetRight()-(g.x0+ix*g.pitch)<edge]
        ys=[iy for iy in range(g.ny) if g.y0+iy*g.pitch-self.outline.GetTop()<edge or self.outline.GetBottom()-(g.y0+iy*g.pitch)<edge]
        for layer in LAYERS:
            for iy in range(g.ny):
                for ix in xs:maps.hard[layer][g.index(ix,iy)]=BLOCKED
            for iy in ys:
                for ix in range(g.nx):maps.hard[layer][g.index(ix,iy)]=BLOCKED
        self.maps[key]=maps
        return maps

    def add_item(self,maps,item,inflate,hole_inflate):
        net=item.GetNetCode() or BLOCKED
        for layer in item_layers(item):
            mark(maps.soft[layer],self.grid,item.GetEffectiveShape(layer),item.GetBoundingBox(),inflate,net)
        if item.Type()==pcbnew.PCB_VIA_T:
            hole=pcbnew.SHAPE_CIRCLE(item.GetPosition(),item.GetDrillValue()//2)
            for layer in LAYERS:mark(maps.soft[layer],self.grid,hole,item.GetBoundingBox(),hole_inflate,net)

    def own_cells(self,group,layer):
        cells=set()
        for item in group:
            if not item.IsOnLayer(layer):continue
            shape=item.GetEffectiveShape(layer)
            for ix,iy in self.grid.cells(item.GetBoundingBox(),0):
                if shape.Collide(point_seg(self.grid.point(ix,iy)),0):cells.add((ix,iy))
        return cells

    def no_via_cells(self,radius):
        """Cells where a via pad would overlap any SMD pad, including its own net."""
        if radius in self.no_via:return self.no_via[radius]
        blocked=self.no_via[radius]=set()
        for fp in self.board.GetFootprints():
            for pad in fp.Pads():
                if pad.HasHole():continue
                for layer in item_layers(pad):
                    shape=pad.GetEffectiveShape(layer)
                    for ix,iy in self.grid.cells(pad.GetBoundingBox(),radius):
                        if shape.Collide(point_seg(self.grid.point(ix,iy)),radius):blocked.add((ix,iy))
        return blocked

    def search(self,net,source,targets,rip):
        """A* over two layers. With rip=True, other nets' tracks/vias are passable at a cost."""
        spec=self.spec(self.name(net))
        half=mm(spec['track_width_mm'])//2;clearance=mm(spec['clearance_mm'])
        via_radius=mm(spec['via_diameter_mm'])//2
        track=self.obstacle_maps(half,clearance);via=self.obstacle_maps(via_radius,clearance)
        no_via=self.no_via_cells(via_radius+mm(0.05))
        grid=self.grid
        protected=self.protected
        def cost(maps,layer,k):
            hard=maps.hard[layer][k]
            if hard not in (0,net):return None
            soft=maps.soft[layer][k]
            if soft in (0,net):return 0.0
            if not rip:return None
            return PROTECTED_RIP_COST if soft in protected else RIP_COST
        target_set={(layer,ix,iy) for layer,cells in targets.items() for ix,iy in cells}
        if not target_set:return None
        tx=[c[1] for c in target_set];ty=[c[2] for c in target_set]
        box=(min(tx),max(tx),min(ty),max(ty))
        def h(ix,iy):
            dx=max(box[0]-ix,0,ix-box[1]);dy=max(box[2]-iy,0,iy-box[3])
            return max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy)
        heap=[];best={};parent={}
        for layer,cells in source.items():
            for ix,iy in cells:
                node=(layer,ix,iy,0,0);best[node]=0.0;parent[node]=None
                heapq.heappush(heap,(h(ix,iy),0.0,node))
        found=None;expanded=0
        while heap:
            f,g,node=heapq.heappop(heap)
            if g>best.get(node,math.inf):continue
            layer,ix,iy,pdx,pdy=node
            if (layer,ix,iy) in target_set:found=node;break
            expanded+=1
            if expanded>MAX_EXPANSIONS:break
            moves=[]
            for dx,dy,step in DIRECTIONS:
                nx,ny=ix+dx,iy+dy
                if not(0<=nx<grid.nx and 0<=ny<grid.ny):continue
                extra=cost(track,layer,grid.index(nx,ny))
                if extra is None:continue
                if dx and dy:
                    side=(cost(track,layer,grid.index(ix+dx,iy)),cost(track,layer,grid.index(ix,iy+dy)))
                    if None in side:continue
                    extra+=max(side)
                turn=TURN_COST if (pdx,pdy)!=(0,0) and (pdx,pdy)!=(dx,dy) else 0.0
                moves.append(((layer,nx,ny,dx,dy),step+extra+turn))
            other=LAYERS[1] if layer==LAYERS[0] else LAYERS[0]
            if (ix,iy) not in no_via:
                k=grid.index(ix,iy);a=cost(via,layer,k);b=cost(via,other,k)
                if a is not None and b is not None:moves.append(((other,ix,iy,0,0),VIA_COST+a+b))
            for nxt,step in moves:
                ng=g+step
                if ng<best.get(nxt,math.inf):
                    best[nxt]=ng;parent[nxt]=node
                    heapq.heappush(heap,(ng+h(nxt[1],nxt[2]),ng,nxt))
        if found is None:return None
        path=[];node=found
        while node is not None:path.append(node[:3]);node=parent[node]
        path.reverse()
        victims=set();items=set()
        if rip:
            for i,(layer,ix,iy) in enumerate(path):
                k=grid.index(ix,iy)
                via_step=i+1<len(path) and path[i+1][0]!=layer
                maps,reach=(via,via_radius) if via_step else (track,half)
                for l in (LAYERS if via_step else (layer,)):
                    if maps.soft[l][k] in (0,net):continue
                    point=point_seg(grid.point(ix,iy));gap=reach+clearance+mm(MARGIN_MM)
                    for item in self.board.GetTracks():
                        other=item.GetNetCode()
                        if other in (0,net) or not item.IsOnLayer(l) or not item.GetEffectiveShape(l).Collide(point,gap):continue
                        # Rail and ground copper loses only the crossed pieces; signal nets are rerouted whole.
                        if other in protected:items.add(item.m_Uuid.AsString())
                        else:victims.add(other)
        return path,spec,(victims,items)

    def commit(self,net,path,spec):
        netinfo=self.nets[net]
        width=mm(spec['track_width_mm']);added=[]
        runs=[];current=[path[0]]
        for node in path[1:]:
            if node[0]!=current[-1][0]:
                runs.append(current);via=pcbnew.PCB_VIA(self.board);via.SetPosition(self.grid.point(node[1],node[2]))
                via.SetWidth(mm(spec['via_diameter_mm']));via.SetDrill(mm(spec['via_drill_mm']));via.SetNet(netinfo)
                self.board.Add(via);added.append(via);current=[node]
            else:current.append(node)
        runs.append(current)
        for run in runs:
            if len(run)<2:continue
            points=[run[0]]
            for a,b,c in zip(run,run[1:],run[2:]):
                if (b[1]-a[1],b[2]-a[2])!=(c[1]-b[1],c[2]-b[2]):points.append(b)
            points.append(run[-1])
            for a,b in zip(points,points[1:]):
                segment=pcbnew.PCB_TRACK(self.board);segment.SetStart(self.grid.point(a[1],a[2]));segment.SetEnd(self.grid.point(b[1],b[2]))
                segment.SetWidth(width);segment.SetLayer(a[0]);segment.SetNet(netinfo);self.board.Add(segment);added.append(segment)
        for (half,clearance),maps in self.maps.items():
            inflate=half+clearance+mm(MARGIN_MM);hole_inflate=half+self.hole_clearance+mm(MARGIN_MM)
            for item in added:self.add_item(maps,item,inflate,hole_inflate)
        return added

    def rip_up(self,nets,items):
        removed=0
        for item in list(self.board.GetTracks()):
            if item.GetNetCode() in nets or item.m_Uuid.AsString() in items:self.board.Remove(item);removed+=1
        self.maps={}
        return removed

    def remove_dangling(self):
        """Remove track stubs and vias that end on no same-net copper; never changes connectivity."""
        poured={zone.GetNetCode() for zone in self.board.Zones() if not zone.GetIsRuleArea()}
        pads=[p for fp in self.board.GetFootprints() for p in fp.Pads()]
        alive=[item for item in self.board.GetTracks()]
        def links(item,point,layers):
            # KiCad joins copper by overlap, so a round track end or via pad counts, not only its centre.
            reach=item.GetWidth()//2 if item.Type()!=pcbnew.PCB_VIA_T else item.GetWidth(LAYERS[0])//2
            count=0
            for other in alive+pads:
                if other.GetNetCode()!=item.GetNetCode() or other.m_Uuid.AsString()==item.m_Uuid.AsString():continue
                box=other.GetBoundingBox();box.Inflate(reach)
                if not box.Contains(point):continue
                if any(other.IsOnLayer(layer) and other.GetEffectiveShape(layer).Collide(point_seg(point),reach) for layer in layers):count+=1
            return count
        stale=[]
        while True:
            found=[]
            for item in alive:
                if item.GetNetCode() in poured:continue
                if item.Type()==pcbnew.PCB_VIA_T:
                    if links(item,item.GetPosition(),LAYERS)<2:found.append(item)
                elif not links(item,item.GetStart(),(item.GetLayer(),)) or not links(item,item.GetEnd(),(item.GetLayer(),)):
                    found.append(item)
            if not found:break
            gone={item.m_Uuid.AsString() for item in found}
            alive=[item for item in alive if item.m_Uuid.AsString() not in gone];stale+=found
        # Remove only at the end: KiCad's SWIG wrappers are unreliable after removal.
        for item in stale:self.board.Remove(item)
        return len(stale)

    def endpoints(self,groups):
        groups=sorted(groups,key=len,reverse=True)
        source={layer:self.own_cells(groups[0],layer) for layer in LAYERS}
        targets={layer:set().union(*(self.own_cells(g,layer) for g in groups[1:])) for layer in LAYERS}
        return source,targets


def finish_pass(board_path,board_id,max_rounds,may_rip,first=None):
    """Route what is reachable; stop after at most one rip-up and save the board."""
    board=pcbnew.LoadBoard(str(board_path));definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
    if definition.routing is None:raise ValueError('board definition has no routing block')
    finisher=Finisher(board,definition);log=[]
    for _ in range(max_rounds):
        open_nets=clusters(board)
        if not open_nets:break
        progress=False
        # The net that caused the latest rip-up is routed before its victims.
        for net in sorted(open_nets,key=lambda n:(finisher.name(n)!=first,finisher.name(n))):
            while True:
                groups=clusters(board).get(net)
                if not groups:break
                source,targets=finisher.endpoints(groups)
                result=finisher.search(net,source,targets,False)
                if result is None and may_rip:
                    candidate=finisher.search(net,source,targets,True)
                    if candidate is not None and any(candidate[2]):
                        victims,items=candidate[2]
                        log.append({'net':finisher.name(net),'status':'RIP UP','victims':sorted(finisher.name(v) for v in victims),
                                    'removed_items':finisher.rip_up(victims,items)})
                        # KiCad's SWIG wrappers are unreliable after removal; continue in a new process.
                        pcbnew.SaveBoard(str(board_path),board)
                        return {'log':log,'ripped':True,'first':finisher.name(net)}
                if result is None:
                    log.append({'net':finisher.name(net),'status':'NO PATH'});break
                path,spec,_=result;added=finisher.commit(net,path,spec);progress=True
                log.append({'net':finisher.name(net),'status':'ROUTED','tracks':sum(i.Type()==pcbnew.PCB_TRACE_T for i in added),
                            'vias':sum(i.Type()==pcbnew.PCB_VIA_T for i in added)})
        if not progress:break
    stubs=finisher.remove_dangling()
    pcbnew.SaveBoard(str(board_path),board)
    return {'log':log,'ripped':False,'removed_dangling_items':stubs}


def open_edges(board_path):
    board=pcbnew.LoadBoard(str(board_path));board.BuildConnectivity()
    connectivity=board.GetConnectivity();connectivity.RecalculateRatsnest()
    return {'remaining_native_unconnected':connectivity.GetUnconnectedCount(False)}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('board_id');p.add_argument('--board',type=Path);p.add_argument('--report',type=Path)
    p.add_argument('--max-rounds',type=int,default=8);p.add_argument('--max-rips',type=int,default=12)
    p.add_argument('--single-pass',type=Path,help=argparse.SUPPRESS);p.add_argument('--may-rip',action='store_true',help=argparse.SUPPRESS);p.add_argument('--first',help=argparse.SUPPRESS);p.add_argument('--count-only',action='store_true',help=argparse.SUPPRESS)
    a=p.parse_args();board=a.board or ROOT/'boards'/a.board_id/f'{a.board_id}.kicad_pcb'
    if a.single_pass:
        result=open_edges(board) if a.count_only else finish_pass(board,a.board_id,a.max_rounds,a.may_rip,a.first)
        a.single_pass.write_text(json.dumps(result))
        sys.stdout.flush();os._exit(0)  # skip SWIG teardown, which can crash after item removal
    log=[];rips=0;first=None;state=board.with_name(board.stem+'.finish-pass.json')
    while True:
        state.unlink(missing_ok=True)
        command=[sys.executable,__file__,a.board_id,'--board',str(board),'--max-rounds',str(a.max_rounds),'--single-pass',str(state)]
        if rips<a.max_rips:command.append('--may-rip')
        if first:command+=['--first',first]
        subprocess.run(command,check=True)
        result=json.loads(state.read_text());log.extend(result['log'])
        if not result['ripped']:break
        rips+=1;first=result['first']
    stubs=result['removed_dangling_items']
    subprocess.run([sys.executable,__file__,a.board_id,'--board',str(board),'--single-pass',str(state),'--count-only'],check=True)
    result=json.loads(state.read_text())
    state.unlink(missing_ok=True)
    report={'schema_version':1,'board':str(board),'board_id':a.board_id,'status':'FINISHING PASS DRAFT; native DRC/parity must be re-run',
            'grid_mm':GRID_MM,'margin_mm':MARGIN_MM,'rip_up_rounds':rips,'routes':log,'remaining_native_unconnected':result['remaining_native_unconnected'],
            'removed_dangling_items':stubs}
    report_path=a.report or board.parent/'reports'/'finish-routes.json'
    report_path.parent.mkdir(parents=True,exist_ok=True);report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f"{a.board_id}: finishing pass routed {sum(r['status']=='ROUTED' for r in log)} connections, {rips} rip-ups; "
          f"{report['remaining_native_unconnected']} native open edges remain")


if __name__=='__main__':main()
