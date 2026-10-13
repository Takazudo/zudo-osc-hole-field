#!/usr/bin/env python3
"""Read-only retained-mask diagnosis: no router search, path proposal or KiCad."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from importlib.metadata import version
import numpy as np
from scipy import ndimage
import shapely

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
METHOD='29140d4e19d526eed3a02a73c33f8ce4219c78f0'
INPUTS={'K1402':('1420','9232ff3212f41604a72b3f49a9d3a8b10884186884bf50f367a57693a7e082a5'),
        'two-A':('1438','ed8de7933f40369ecefb3ea28f382662923b414298e0cdb72ed5e32578e64e3f')}
sha=lambda b:hashlib.sha256(b).hexdigest()

def components(passable,via_ok,src,goal):
    """Planar4-connectivity equals8/no-cornercut connectivity; no paths/cost search."""
    labels=np.zeros(passable.shape,np.int32);offset=0
    for layer in range(len(passable)):
        a,n=ndimage.label(passable[layer]);a[a>0]+=offset;labels[layer]=a;offset+=n
    parent=list(range(offset+1))
    def find(x):
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    switches=via_ok|src.all(0)|goal.all(0)
    for i in range(len(passable)):
        for j in range(i):
            ok=switches&(labels[i]>0)&(labels[j]>0)
            for a,b in np.unique(np.stack([labels[i][ok],labels[j][ok]],axis=1),axis=0):
                a,b=find(int(a)),find(int(b));parent[a]=b
    lookup=np.array([find(i) for i in range(offset+1)],np.int32)
    joined=lookup[labels]
    return joined

def component_summary(labels,terminal,other,free,via_ok,origin,res,layers):
    roots=set(map(int,np.unique(labels[terminal])))-{0}
    mask=np.isin(labels,list(roots)) if roots else np.zeros_like(terminal)
    pos=np.argwhere(mask)
    bounds=None if not len(pos) else [origin[0]+float(pos[:,2].min())*res,origin[1]+float(pos[:,1].min())*res,origin[0]+float(pos[:,2].max())*res,origin[1]+float(pos[:,1].max())*res]
    rim=np.stack([ndimage.binary_dilation(t)&~t for t in terminal])
    return {'terminal_cells':int(terminal.sum()),'component_roots':sorted(roots),'reachable_cells':int(mask.sum()),
            'reachable_by_layer':{n:int(mask[i].sum()) for i,n in enumerate(layers)},
            'reachable_bounds_mm':bounds,'free_exit_neighbor_cells':int((rim&free).sum()),
            'reachable_via_sites':int((mask.any(0)&via_ok).sum()),
            'overlaps_other_terminal':bool((mask&other).any())}

def neighbors(dump,pad):
    shape=shapely.Polygon(pad['poly']);out=[];layers=set(pad['layers'])
    for p in dump['pads']:
        if p['net']==pad['net'] or not p['poly'] or not layers.intersection(p['layers']):continue
        distance=shape.distance(shapely.Polygon(p['poly']))/1e6
        if distance<1:out.append({'kind':'pad','id':p['uuid'],'ref':p['ref']+'.'+p['pad'],'net':p['net'],'edge_gap_mm':distance})
    for t in dump['tracks']:
        if t['net']==pad['net'] or t['layer'] not in layers:continue
        distance=max(0,shape.distance(shapely.LineString([t['a'],t['b']]))-t['width']/2)/1e6
        if distance<1:out.append({'kind':'track','id':t['uuid'],'net':t['net'],'edge_gap_mm':distance})
    return sorted(out,key=lambda r:(r['edge_gap_mm'],r['id']))[:20]

def boundary_screen(dump,pad,labels,terminal,passable,origin,res,width,clearance):
    """Pointwise exact-geometry screen at the frozen component boundary, no path."""
    roots=set(map(int,np.unique(labels[terminal])))-{0}
    own=np.isin(labels,list(roots))
    if own.sum()>1000:return {'status':'NOT SCREENED: component larger than1000cells'}
    out=[]
    board=shapely.union_all(shapely.polygonize([shapely.LineString([e[:2],e[2:]]) for e in dump['edges']]))
    for li,layer in enumerate(dump['layers']):
        rim=ndimage.binary_dilation(own[li])&~passable[li]
        cells=np.argwhere(rim)
        if not len(cells):continue
        xy=np.column_stack([origin[0]+cells[:,1]*res,origin[1]+cells[:,0]*res])*1e6
        points=shapely.points(xy);distance=np.full(len(cells),np.inf);nearest=np.empty(len(cells),object)
        lo=xy.min(0)-2e6;hi=xy.max(0)+2e6
        def nearby(bounds):return bounds[0]<=hi[0] and bounds[1]<=hi[1] and bounds[2]>=lo[0] and bounds[3]>=lo[1]
        def add(values,identity):
            less=values<distance;distance[less]=values[less];nearest[less]=identity
        for p in dump['pads']:
            if p['net']==pad['net'] or layer not in p['layers'] or not p['poly']:continue
            v=np.array(p['poly']);bounds=(*v.min(0),*v.max(0))
            if nearby(bounds):add(shapely.distance(points,shapely.Polygon(p['poly']))/1e6,p['ref']+'.'+p['pad'])
        for p in dump['pads']:
            if p['npth'] and p['drill']:
                add(np.maximum(0,np.linalg.norm(xy-np.asarray(p['xy']),axis=1)-p['drill']/2)/1e6,p['ref']+'.'+p['pad']+':NPTH')
        for t in dump['tracks']:
            if t['net']==pad['net'] or t['layer']!=layer:continue
            a,b=t['a'],t['b'];radius=t['width']/2
            if nearby((min(a[0],b[0])-radius,min(a[1],b[1])-radius,max(a[0],b[0])+radius,max(a[1],b[1])+radius)):
                add(np.maximum(0,shapely.distance(points,shapely.LineString([a,b]))-radius)/1e6,t['uuid'])
        for v in dump['vias']:
            if v['net']==pad['net']:continue
            add(np.maximum(0,np.linalg.norm(xy-np.asarray(v['xy']),axis=1)-v['diameter']/2)/1e6,v['uuid'])
        copper_slack=distance-clearance-width/2
        edge_slack=shapely.distance(points,board.boundary)/1e6-.5-width/2
        edge_slack[~shapely.contains(board,points)]=-np.inf
        keep_slack=np.full(len(cells),np.inf)
        for k in dump['keepouts']:
            if not k['tracks'] or layer not in k['layers'] or len(k['poly'])<3:continue
            if k.get('name')=='NECKDOWN' or str(k.get('name','')).endswith(':neckdown'):continue
            keep_slack=np.minimum(keep_slack,shapely.distance(points,shapely.Polygon(k['poly']))/1e6-width/2)
        slack=np.minimum(np.minimum(copper_slack,edge_slack),keep_slack)
        good=np.flatnonzero(slack>=1e-9)
        best=int(np.argmax(slack))
        out.append({'layer':layer,'blocked_boundary_centers':len(cells),'exact_clearance_legal_centers':len(good),
                    'best_center_mm':(xy[best]/1e6).tolist(),'best_minimum_margin_mm':float(slack[best]),'nearest_foreign_at_best':str(nearest[best]),
                    'positive_witnesses':[{'xy_mm':(xy[i]/1e6).tolist(),'minimum_margin_mm':float(slack[i]),'nearest_foreign':str(nearest[i])} for i in good[:8]]})
    return {'status':'POINTWISE SOURCE GEOMETRY ONLY; no edge/sweep, via, terminal-contact or physical qualification',
            'scope':'Same width/clearance; exact dump polygons, analytic track/via radii, outline and track keepouts. Tests blocked boundary centers only; positive center is not a route or proof of usable terminal contact.', 'layers':out}

def analyze(board,path,router,spec,manifest):
    tag,expected=INPUTS[board];assert sha(path.read_bytes())==expected
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        read=lambda n:json.loads(z.read(n))
        dump=read('fixture/before/dump.json');diag=read('fixture/matched-search-diagnostics.json');lock=read('fixture/fixture-lock.json')
        assert lock['source_tree_sha']==METHOD and lock['board']==board
        assert lock['spec_sha256']==diag['spec_sha256']==sha((HERE.parent/'matching-spec.json').read_bytes())
        assert lock['matched_demands_sha256']==sha((HERE.parent/'matched-demands.json').read_bytes())
        assert sha(z.read('fixture/before/dump.json'))==lock['artifact']['dump_sha256']
        assert sha(z.read('fixture/before/osc-core.kicad_pcb'))==lock['artifact']['board_sha256']
        assert sha(z.read('fixture/matched-proposal.json'))==sha((HERE.parent/f'route-{tag}/matched-proposal.json').read_bytes())
        assert not read('fixture/matched-proposal.json')['copper']
    domain=manifest['domains']['O1'];budget=spec['budget'];res=budget['raster_mm'];margin=res/np.sqrt(2)+.01
    raster=router.Raster(dump,res,bounds_mm=domain['common_bounds_mm']);L=len(raster.layers)
    rows=[]
    for kind in spec['route_policy']['target_order']:
        target=domain['targets'][kind];net=target['net_token'];N=raster.net_id[net]
        original_pads={p['uuid']:p for p in dump['pads']}
        assert all(original_pads[p['uuid']]==p for p in target['anchor_records'])
        goalpad,srcpad=target['anchor_records']
        src=router.island_mask(raster,dump,[srcpad['uuid']]);goal=router.island_mask(raster,dump,[goalpad['uuid']])
        d=next(d for d in diag['diagnostics'] if d['net']==net);w=budget['rail_width_mm'] if net in spec['route_policy']['rail_nets'] else budget['signal_width_mm'];vr=budget['via_diameter_mm']/2
        attempts=[]
        for observed in d['attempts']:
            y0,y1,x0,x1=observed['window_cells'];guard=round(1.5/res)
            g0,g1,h0,h1=max(0,y0-guard),min(raster.h,y1+guard),max(0,x0-guard),min(raster.w,x1+guard)
            inner=(slice(y0-g0,y1-g0),slice(x0-h0,x1-h0));win=(slice(y0,y1),slice(x0,x1))
            free=np.zeros((L,y1-y0,x1-x0),bool);foreign_any=np.zeros((g1-g0,h1-h0),bool)
            for li in range(L):
                lab=raster.label[li][g0:g1,h0:h1];fixed=raster.fixed_label[li][g0:g1,h0:h1]
                foreign=((lab!=0)&(lab!=N))|((fixed!=0)&(fixed!=N));foreign_any|=foreign
                dist=ndimage.distance_transform_edt(~foreign)[inner]*res
                free[li]=(dist>=budget['clearance_mm']+w/2+margin)&(raster.d_edge[win]>=.5+w/2+margin)&(raster.d_keep_track[li][win]>=w/2+margin)
            dist_any=ndimage.distance_transform_edt(~foreign_any)[inner]*res
            d_hole=ndimage.distance_transform_edt(~raster.hole[g0:g1,h0:h1])[inner]*res
            via_ok=(dist_any>=budget['clearance_mm']+vr+margin)&(raster.d_edge[win]>=.5+vr+margin)&(raster.d_keep_via[win]>=vr+margin)&(d_hole>=vr+.25+margin)&(raster.d_smd[win]>=vr+margin)
            s=src[:,y0:y1,x0:x1];gl=goal[:,y0:y1,x0:x1];passable=free|s|gl
            labels=components(passable,via_ok,s,gl)
            origin=[raster.x0/1e6+x0*res,raster.y0/1e6+y0*res]
            ss=component_summary(labels,s,gl,free,via_ok,origin,res,raster.layers);gg=component_summary(labels,gl,s,free,via_ok,origin,res,raster.layers)
            attempts.append({'retained':observed,'mask_sha256':{n:sha(a.tobytes()) for n,a in [('free',free),('via_ok',via_ok),('src',s),('goal',gl)]},'source':ss,'goal':gg,'graph_connected':ss['overlaps_other_terminal'],
                'source_boundary_screen':boundary_screen(dump,srcpad,labels,s,passable,origin,res,w,budget['clearance_mm']),
                'goal_boundary_screen':boundary_screen(dump,goalpad,labels,gl,passable,origin,res,w,budget['clearance_mm'])})
        rows.append({'kind':kind,'net':net,'source':srcpad['ref']+'.'+srcpad['pad'],'goal':goalpad['ref']+'.'+goalpad['pad'],'retained_reason':d['reason'],'width_mm':w,'attempts':attempts,'nearby_copper_scope':'Context only, not causal attribution; nearest pads/tracks omit vias/keepouts. Complete boundary screen is separately labeled.', 'near_source_foreign_copper':neighbors(dump,srcpad),'near_goal_foreign_copper':neighbors(dump,goalpad)})
    return {'artifact_sha256':expected,'board_sha256':lock['artifact']['board_sha256'],'dump_sha256':lock['artifact']['dump_sha256'],'demands':rows}

def main():
    p=argparse.ArgumentParser();p.add_argument('--k',type=Path,required=True);p.add_argument('--two-a',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert {n:version(n) for n in ('numpy','scipy','shapely')}=={'numpy':'2.2.6','scipy':'1.15.3','shapely':'2.1.2'}
    source='scripts/pcbgen/grid_router.py';actual=(ROOT/source).read_bytes();assert actual==subprocess.check_output(['git','show',METHOD+':'+source],cwd=ROOT)
    sys.path.insert(0,str(ROOT));from scripts.pcbgen import grid_router as router
    def forbidden(*a,**k):raise AssertionError('routing/native search prohibited in source-only diagnosis')
    router.route=forbidden;router.astar=forbidden;router.astar_py=forbidden;router.native_astar=forbidden
    spec=json.loads((HERE.parent/'matching-spec.json').read_text());manifest=json.loads((HERE.parent/'matched-demands.json').read_text())
    out={'status':'SOURCE-ONLY CONNECTIVITY OF FROZEN RASTER MASKS; NOT NATIVE OR PHYSICAL PROOF','method':METHOD,'router_sha256':sha(actual),'tool_sha256':sha(Path(__file__).read_bytes()),'scope':'No route/astar/native calls; planar4-components unioned only at existing via_ok or through terminals. Same connected components as8-neighbor no-cornercut graph. No path/cost computation, changed rules, proposals or hardware.','boards':{b:analyze(b,path,router,spec,manifest) for b,path in [('K1402',a.k),('two-A',a.two_a)]}}
    a.output.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    for b,r in out['boards'].items():
        for d in r['demands']:print(b,d['kind'],d['retained_reason'],[(x['graph_connected'],x['source']['reachable_cells'],x['goal']['reachable_cells'],x['source']['free_exit_neighbor_cells'],x['goal']['free_exit_neighbor_cells']) for x in d['attempts']])
if __name__=='__main__':main()
