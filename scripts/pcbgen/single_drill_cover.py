"""Exact nominal cover certificates for single circular-drill SMD sources.

Domains are implicit analytic pad/halfplane intersections and one full annulus.
Shapely proposes overlap witnesses ONLY; rational predicates prove every one.
Historical native input is not promoted to current or physical model authority.
"""
import argparse
from collections import Counter
from fractions import Fraction as Q
import hashlib
import json
from pathlib import Path
import re

from scripts.pcbgen.uuid_tools import top_level_spans

ROOT = Path(__file__).resolve().parents[2]
NM = 1000000
MAPPING_SHA256 = 'bc766e053d76791c68afd41f65ea9ce184b93fdf11725d9b019c7d018e9b9ad4'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def nm(v):
    result = Q(str(v))*NM
    if result.denominator != 1:
        raise ValueError('native coordinate is not an exact integer nanometre')
    return int(result)


def primitive(p):
    kind = p['kind']; c = p['centre_nm']; half = p['half_size_nm']
    turn = p['quarter_turns']; r = p.get('corner_radius_nm', 0)
    if any(type(v) is not int for v in [*c, *half, turn, r]) or len(c)!=2 or len(half)!=2:
        raise ValueError('exact integer primitive required')
    if turn not in range(4) or min(half)<=0:
        raise ValueError('invalid primitive dimensions/orientation')
    hx, hy = half
    if kind == 'circle':
        if hx != hy or r: raise ValueError('invalid circle')
        r = hx
    elif kind == 'rectangle':
        if r: raise ValueError('rectangle corner radius')
    elif kind == 'roundrect':
        if not 0<r<=min(half): raise ValueError('roundrect radius')
    else: raise ValueError('unsupported analytic pad')
    if turn%2: hx, hy = hy, hx
    return tuple(c), hx, hy, r


def inside_pad(point, p, strict=False):
    (cx,cy),hx,hy,r = primitive(p); x,y = point
    dx=max(abs(x-cx)-(hx-r),0); dy=max(abs(y-cy)-(hy-r),0)
    if r: return dx*dx+dy*dy < r*r if strict else dx*dx+dy*dy <= r*r
    return abs(x-cx)<hx and abs(y-cy)<hy if strict else abs(x-cx)<=hx and abs(y-cy)<=hy


def pad_circle_disjoint(p, centre, radius):
    (cx,cy),hx,hy,r=primitive(p);x,y=centre
    dx=max(abs(x-cx)-(hx-r),0);dy=max(abs(y-cy)-(hy-r),0)
    return dx*dx+dy*dy > (r+radius)**2


def plane_nonempty(p, n, threshold):
    (cx,cy),hx,hy,r=primitive(p);nx,ny=n
    residual=threshold-(nx*cx+ny*cy+(hx-r)*abs(nx)+(hy-r)*abs(ny))
    # Exact support comparison, including irrational diagonal support radius.
    return residual<0 or (r>0 and r*r*(nx*nx+ny*ny)>residual*residual)


def native_outline(text, exported):
    """Bind a simple axis-aligned native Edge.Cuts polygon, reject other cuts."""
    points=[tuple(map(nm,p)) for p in exported]
    if len(points)>1 and points[0]==points[-1]: points.pop()
    if len(set(points))!=len(points) or len(points)<4: raise ValueError('invalid outline')
    edges=list(zip(points,points[1:]+points[:1]));actual=[]
    for a,b in top_level_spans(text):
        block=text[a:b]
        if '(layer "Edge.Cuts")' not in block: continue
        if not block.startswith('(gr_line\n'): raise ValueError('unsupported native cut')
        ends=[]
        for name in ('start','end'):
            m=re.search(r'\('+name+r'\s+([^\s()]+)\s+([^\s()]+)\)',block)
            if not m: raise ValueError('native cut endpoint missing')
            ends.append(tuple(nm(v) for v in m.groups()))
        actual.append(tuple(ends))
    canonical=lambda e:tuple(sorted(e))
    if Counter(map(canonical,edges))!=Counter(map(canonical,actual)):
        raise ValueError('native cuts differ from complete exported outline')
    if any((a[0]!=b[0] and a[1]!=b[1]) or a==b for a,b in edges):
        raise ValueError('axis-aligned nonzero native cuts required')
    for i,(a,b) in enumerate(edges):
        for j,(c,d) in enumerate(edges):
            if j<=i or j==i+1 or (i==0 and j==len(edges)-1):continue
            if max(min(a[0],b[0]),min(c[0],d[0]))<=min(max(a[0],b[0]),max(c[0],d[0])) and max(min(a[1],b[1]),min(c[1],d[1]))<=min(max(a[1],b[1]),max(c[1],d[1])):
                raise ValueError('self-intersecting/touching outline')
    return points


def rectangle_in_board(box, outline):
    x0,y0,x1,y1=box
    if x0>=x1 or y0>=y1: return False
    # No actual boundary can touch the rectangle; one interior point then
    # certifies its entire connected area, including nonconvex board outlines.
    edges=list(zip(outline,outline[1:]+outline[:1]))
    for a,b in edges:
        if min(a[0],b[0])<=x1 and max(a[0],b[0])>=x0 and min(a[1],b[1])<=y1 and max(a[1],b[1])>=y0:return False
    x=Q(x0+x1,2);y=Q(y0+y1,2)
    return sum(a[0]>x for a,b in edges if a[0]==b[0] and min(a[1],b[1])<=y<max(a[1],b[1]))%2==1


def square_valid(box, domains, p, centre, ri, ro):
    x0,y0,x1,y1=map(Q,box)
    if x0>=x1 or y0>=y1:return False
    corners=[(x,y) for x in (x0,x1) for y in (y0,y1)]
    cx,cy=centre
    for domain in domains:
        if domain['kind']=='annulus':
            dx=max(x0-cx,cx-x1,0);dy=max(y0-cy,cy-y1,0)
            if dx*dx+dy*dy<=ri*ri:return False
            if any((x-cx)**2+(y-cy)**2>=ro*ro for x,y in corners):return False
        else:
            nx,ny=domain['normal'];t=domain['threshold_nm']
            if any(not inside_pad(c,p,True) or nx*c[0]+ny*c[1]<=t for c in corners):return False
    return True


def propose_overlap(left,right,p,centre,ri,ro):
    """Floating polygons are search aids; no polygon predicate certifies Cu."""
    from shapely.geometry import Point,box as shape_box,Polygon
    (cx,cy),hx,hy,r=primitive(p)
    pad=shape_box(cx-hx+r,cy-hy+r,cx+hx-r,cy+hy-r)
    if r: pad=pad.buffer(r,quad_segs=48)
    shapes=[]
    for domain in (left,right):
        if domain['kind']=='annulus':
            shapes.append(Point(*centre).buffer(ro,quad_segs=64).difference(Point(*centre).buffer(ri,quad_segs=64)))
        else:
            nx,ny=domain['normal'];t=domain['threshold_nm']
            vertices=[(cx-hx-1,cy-hy-1),(cx+hx+1,cy-hy-1),(cx+hx+1,cy+hy+1),(cx-hx-1,cy+hy+1)]
            clipped=[]
            for a,b in zip(vertices,vertices[1:]+vertices[:1]):
                fa=nx*a[0]+ny*a[1]-t;fb=nx*b[0]+ny*b[1]-t
                if fa>=0:clipped.append(a)
                if (fa<0<fb) or (fb<0<fa):
                    fraction=fa/(fa-fb);clipped.append((a[0]+fraction*(b[0]-a[0]),a[1]+fraction*(b[1]-a[1])))
            if len(clipped)<3:return None
            shapes.append(pad.intersection(Polygon(clipped)))
    region=shapes[0].intersection(shapes[1])
    if region.is_empty or region.area<=0:return None
    point=region.representative_point();x=round(point.x);y=round(point.y)
    # Positive integer-nm squares; search failure is unresolved, never PASS.
    for half in (10000,5000,1000,100,10,1):
        square=[x-half,y-half,x+half,y+half]
        if square_valid(square,(left,right),p,centre,ri,ro):return square
    return None


def certify(pad, hole, via, all_holes, outline, face):
    if pad['net']!='AGND' or hole['net']!='AGND' or via['net']!='AGND' or not hole['plated']:
        raise ValueError('same-net plated actual source via required')
    if via['uuid']!=hole['uuid'] or face not in via['copper'] or face not in hole['copper_layers']:
        raise ValueError('via identity/physical foil mismatch')
    p=pad['analytic_primitives'][face];centre,hx,hy,r=primitive(p)
    vp=via['analytic_primitives'][face];vc,vx,vy,vr=primitive(vp)
    if vp['kind']!='circle' or vx!=vy:raise ValueError('full actual circular land required')
    hc=tuple(map(nm,hole['xy_mm']));diameter=tuple(map(nm,hole['size_mm']))
    if hc!=vc or diameter[0]!=diameter[1] or min(diameter)<=0:raise ValueError('circular concentric drill required')
    ri=Q(diameter[0],2);ro=Q(vx)
    if ri.denominator!=1:raise ValueError('integer-nm radius required')
    ri=int(ri);ro=int(ro)
    if ro*ro<=Q(5,4)*ri*ri:raise ValueError('annulus does not cover the missing octagon')
    if pad_circle_disjoint(p,hc,ri):raise ValueError('actual source pad does not meet its drill')
    if not rectangle_in_board([centre[0]-hx,centre[1]-hy,centre[0]+hx,centre[1]+hy],outline) or not rectangle_in_board([hc[0]-ro,hc[1]-ro,hc[0]+ro,hc[1]+ro],outline):
        raise ValueError('native cut clips/touches pad or annulus bounding rectangle')
    checked=[]
    for other in all_holes:
        if other['uuid']==hole['uuid']:continue
        oc=tuple(map(nm,other['xy_mm']));sx,sy=map(nm,other['size_mm'])
        if min(sx,sy)<=0:raise ValueError('invalid foreign drill')
        # A circle of radius (sx+sy)/2 encloses any orientation of a slot;
        # circular drills retain the exact smaller radius.
        radius=Q(sx,2) if sx==sy else Q(sx+sy,2)
        if not pad_circle_disjoint(p,oc,radius) or sum((a-b)**2 for a,b in zip(oc,hc))<=(radius+ro)**2:
            raise ValueError('other native drill clips/touches pad or full annulus: '+other['uuid'])
        checked.append(other['uuid'])
    domains=[{'kind':'annulus','centre_nm':list(hc),'inner_radius_nm':ri,'outer_radius_nm':ro}]
    excluded=[]
    for nx,ny in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
        offset=ri if nx*ny==0 else Q(3,2)*ri
        t=nx*hc[0]+ny*hc[1]+offset
        if Q(t).denominator!=1:raise ValueError('integer threshold required')
        d={'kind':'pad_halfplane','normal':[nx,ny],'threshold_nm':int(t)}
        if plane_nonempty(p,(nx,ny),t):domains.append(d)
        else:excluded.append(d)
    edges=[]
    for i in range(len(domains)):
        for j in range(i):
            square=propose_overlap(domains[i],domains[j],p,hc,ri,ro)
            if square:edges.append((i,j,square))
    reached={0};tree=[]
    while len(reached)<len(domains):
        choices=[e for e in edges if (e[0] in reached)!=(e[1] in reached)]
        if not choices:raise ValueError('no certified positive-overlap tree for all nonempty pieces')
        i,j,square=choices[0]
        if i in reached:i,j=j,i
        reached.add(i);tree.append({'child':i,'parent':j,'square_nm':square,'area_nm2':(square[2]-square[0])*(square[3]-square[1])})
    order=[0]+[edge['child'] for edge in tree]
    positions={domain:i for i,domain in enumerate(order)}
    return {'ref':pad['ref'],'pad':pad['pad'],'pad_uuid':pad['uuid'],'net':'AGND','face':face,
            'source_primitive':p,'via_uuid':via['uuid'],'via_primitive':vp,'drill':hole,
            'domains':domains,'empty_halfplanes':excluded,'overlap_tree':tree,
            'ordered_domain_ids':order,'ordered_parents':[-1]+[positions[edge['parent']] for edge in tree],
            'source_partition':'S_i=(actual pad minus open drill) intersect D_i minus all preceding D_j in ordered_domain_ids; disjoint measurable partition up to zero-area boundaries.',
            'foreign_holes_checked':len(checked),'foreign_holes_uuid_sha256':sha(json.dumps(sorted(checked)).encode()),
            'coverage':'Exact pad minus actual open drill is covered: eight halfplanes cover outside octagon; full annulus covers remainder. Boundary sets of area zero do not carry L2 source mass.',
            'status':'EXACT NOMINAL GEOMETRY ONLY; source profile, 3D lift/primal/material and current model admission OPEN'}


def run(mapping_path, output):
    from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native
    mapping_path=Path(mapping_path);output=Path(output)
    if output.exists():raise ValueError('fresh certificate receipt required')
    mapping_bytes=mapping_path.read_bytes();mapping=json.loads(mapping_bytes)
    if sha(mapping_bytes)!=MAPPING_SHA256:raise ValueError('unreviewed retained mapping epoch')
    # Retained input epochs are explicit, never inferred from today's aggregate.
    frozen=ROOT/'.circuit-cache/issue38-recovery/white-land-review'
    paths=[mapping_path,frozen/'partition.json',frozen/'io-partition.json',Path(__file__),ROOT/'scripts/pcbgen/source_contact_inventory.py',ROOT/'scripts/pcbgen/uuid_tools.py']
    bindings={str(p.resolve().relative_to(ROOT)):sha(p.read_bytes()) for p in paths}
    part=json.loads((frozen/'partition.json').read_bytes());io=json.loads((frozen/'io-partition.json').read_bytes())
    for key,name in [('design/partition/partition.json','partition.json'),('design/reports/io-partition.json','io-partition.json')]:
        if sha((frozen/name).read_bytes())!=mapping['source_sha256'][key]:raise ValueError('frozen source epoch mismatch')
    results=[];unresolved=[];untargeted=[];board_bindings=[]
    for group in mapping['boards']:
        path=ROOT/group['native_export_path'];raw=path.read_bytes()
        if sha(raw)!=group['native_export_sha256']:raise ValueError('native export changed')
        native=json.loads(raw);boardpath=Path(native['board'].replace('/work/',str(ROOT)+'/'))
        if not boardpath.is_absolute():boardpath=ROOT/boardpath
        boardbytes=boardpath.read_bytes()
        if sha(boardbytes)!=native['board_sha256'] or native['board_sha256']!=group['board_sha256']:raise ValueError('native board epoch mismatch')
        bindings[str(path.relative_to(ROOT))]=sha(raw);bindings[str(boardpath.relative_to(ROOT))]=sha(boardbytes)
        board_bindings.append({'board_id':group['board_id'],'native_export_sha256':sha(raw),'board_sha256':sha(boardbytes)})
        key=next(b['board_key'] for b in part['boards'] if b['id']==group['board_id'])
        refs={p['ref'] for p in part['assignment']['components'] if p['board']==key and p['fitted']}
        pads=reconcile_native(native,expected_contacts(group['board_id'],part,io,{'AGND'}),refs,{'AGND'})
        identities=[(r['ref'],r['pad'],r['net']) for r in group['own_source_contacts']]
        if len(set(identities))!=len(identities) or set(identities)!=set(pads):raise ValueError('complete mapped source set differs')
        items={i['uuid']:i for i in native['items']};holes={h['uuid']:h for h in native['holes']}
        if len(items)!=len(native['items']) or len(holes)!=len(native['holes']):raise ValueError('duplicate native UUID')
        outline=None
        for row in group['own_source_contacts']:
            pad=pads[row['ref'],row['pad'],row['net']]
            if pad['uuid']!=row['uuid']:raise ValueError('source UUID changed')
            if row['family']=='PTH':untargeted.append({'board_id':group['board_id'],'ref':row['ref'],'pad':row['pad'],'reason':'PTH boundary transfer OPEN'});continue
            if row['family']!='SMD_drill_overlap_unresolved':continue
            ids=row['actual_or_unproved_drill_uuids']
            if len(ids)!=1:untargeted.append({'board_id':group['board_id'],'ref':row['ref'],'pad':row['pad'],'reason':'multiple drills OPEN','drill_uuids':ids});continue
            if pad['analytic_primitives'][row['face']]!=row['primitive']:raise ValueError('mapped pad primitive changed')
            if outline is None:outline=native_outline(boardbytes.decode(),native['outline_mm'])
            try:
                cert=certify(pad,holes[ids[0]],items[ids[0]],native['holes'],outline,row['face'])
                cert.update(board_id=group['board_id'],native_export_sha256=sha(raw),board_sha256=sha(boardbytes));results.append(cert)
            except ValueError as error:unresolved.append({'board_id':group['board_id'],'ref':row['ref'],'pad':row['pad'],'reason':str(error)})
    if any(sha((ROOT/name).read_bytes())!=value for name,value in bindings.items()):raise ValueError('source changed during certification')
    if len(results)+len(unresolved)!=213 or len(untargeted)!=310:
        raise ValueError('retained single/multiple-drill/PTH scope differs')
    import shapely
    receipt={'scope':'Exact nominal native geometry certificates only; historical exports stay historical. No source/current/3D/primal/material/model admission.',
             'source_sha256':bindings,'native_epochs':board_bindings,'overlap_search_only_shapely_version':shapely.__version__,
             'certified_count':len(results),'single_drill_unresolved_count':len(unresolved),'untargeted_count':len(untargeted),
             'certificates':results,'single_drill_unresolved':unresolved,'untargeted_open':untargeted}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as handle:json.dump(receipt,handle,indent=2,sort_keys=True);handle.write('\n')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mapping',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    receipt=run(args.mapping,args.output);print({k:receipt[k] for k in ('certified_count','single_drill_unresolved_count','untargeted_count')})
