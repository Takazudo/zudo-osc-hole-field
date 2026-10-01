"""Exact nominal finite covers for the five retained multiple-drill sources.

Every convex domain avoids ALL drills. Annuli must independently remain full.
Floating polygons only suggest rational square witnesses; they prove nothing.
"""
import argparse
from collections import Counter
from fractions import Fraction as Q
import itertools
import json
from pathlib import Path

from scripts.pcbgen.single_drill_cover import (
    ROOT, MAPPING_SHA256, sha, nm, primitive, inside_pad,
    pad_circle_disjoint, native_outline, rectangle_in_board,
)
from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native

PREVIOUS_SHA256='9750c2e223e963e2ce2bf344967a5a78fb687be9fd263369cd1568e8e461dd79'
TARGETS={('osc-jack-right','U8304','6'),('osc-core','C6113','2'),
         ('osc-core','C7305','2'),('osc-core','C7417','2'),('osc-core','R2169','2')}
NORMALS=[(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]


def rational(v):return [v.numerator,v.denominator]
def encode_polygon(poly):return [[rational(Q(x)),rational(Q(y))] for x,y in poly]


def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def clean(poly):
    result=[]
    for p in poly:
        if not result or p!=result[-1]:result.append(p)
    if len(result)>1 and result[0]==result[-1]:result.pop()
    while len(result)>=3:
        redundant=next((i for i in range(len(result)) if cross(result[i-1],result[i],result[(i+1)%len(result)])==0),None)
        if redundant is None:break
        result.pop(redundant)
    return result


def clip(poly, normal, threshold):
    """Exact intersection with a closed rational halfplane n.x >= t."""
    if not poly:return []
    nx,ny=normal;out=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        fa=nx*a[0]+ny*a[1]-threshold;fb=nx*b[0]+ny*b[1]-threshold
        if fa>=0:out.append(a)
        if (fa<0<fb) or (fb<0<fa):
            q=Q(fa,fa-fb);out.append((a[0]+q*(b[0]-a[0]),a[1]+q*(b[1]-a[1])))
    return clean(out)


def area2(poly):
    return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1]))) if poly else Q(0)


def point_segment_squared(p,a,b):
    dx=b[0]-a[0];dy=b[1]-a[1];d2=dx*dx+dy*dy
    q=max(Q(0),min(Q(1),Q((p[0]-a[0])*dx+(p[1]-a[1])*dy,d2))) if d2 else Q(0)
    return (p[0]-a[0]-q*dx)**2+(p[1]-a[1]-q*dy)**2


def pad_intersection_positive(poly,p):
    """Exact positive-area test for polygon intersect (core rectangle+B_r)."""
    if len(poly)<3 or area2(poly)==0:return False,{'reason':'zero-area rational polygon'}
    (cx,cy),hx,hy,r=primitive(p)
    if r==0:return True,None  # poly was clipped from the pad bounding box
    x0=cx-hx+r;x1=cx+hx-r;y0=cy-hy+r;y1=cy+hy-r
    core=[(Q(x0),Q(y0)),(Q(x1),Q(y0)),(Q(x1),Q(y1)),(Q(x0),Q(y1))]
    intersection=poly
    for normal,t in [((1,0),x0),((-1,0),-x1),((0,1),y0),((0,-1),-y1)]:intersection=clip(intersection,normal,t)
    if intersection:distance=Q(0)
    else:
        distance=min([point_segment_squared(v,a,b) for v in poly for a,b in zip(core,core[1:]+core[:1])]+
                     [point_segment_squared(v,a,b) for v in core for a,b in zip(poly,poly[1:]+poly[:1])])
    return distance<r*r,{'reason':'rounded-pad core distance','distance_squared_nm2':rational(distance),'corner_radius_squared_nm2':r*r}


def convex_branches(p,annuli):
    """Enumerate all 8^m choices, pruning only exact zero-area intersections."""
    (cx,cy),hx,hy,_=primitive(p)
    initial=[(Q(cx-hx),Q(cy-hy)),(Q(cx+hx),Q(cy-hy)),(Q(cx+hx),Q(cy+hy)),(Q(cx-hx),Q(cy+hy))]
    accepted=[];rejected=[]
    def visit(poly,planes,choices):
        if len(choices)==len(annuli):
            accepted.append({'kind':'convex_piece','planes':planes,'choices':choices,'polygon':poly});return
        ann=annuli[len(choices)];cx,cy=ann['centre_nm'];a=ann['inner_radius_nm']
        for i,(nx,ny) in enumerate(NORMALS):
            t=nx*cx+ny*cy+(a if nx*ny==0 else Q(3,2)*a)
            plane={'normal':[nx,ny],'threshold_nm':rational(Q(t))}
            clipped=clip(poly,(nx,ny),t);positive,proof=pad_intersection_positive(clipped,p)
            if positive:visit(clipped,planes+[plane],choices+[i])
            else:rejected.append({'choice_prefix':choices+[i],'empty_proof':proof})
    visit(initial,[],[])
    # Exact distribution accounting: every complete choice is a positive leaf
    # or lies below exactly one pruned prefix.
    if len(accepted)+sum(8**(len(annuli)-len(r['choice_prefix'])) for r in rejected)!=8**len(annuli):
        raise ValueError('halfplane coverage branch accounting failed')
    return accepted,rejected


def square_inside(square,domain,p):
    x0,y0,x1,y1=map(Q,square)
    if x0>=x1 or y0>=y1:return False
    corners=list(itertools.product((x0,x1),(y0,y1)))
    if domain['kind']=='annulus':
        cx,cy=domain['centre_nm'];a=domain['inner_radius_nm'];r=domain['outer_radius_nm']
        dx=max(x0-cx,cx-x1,0);dy=max(y0-cy,cy-y1,0)
        return dx*dx+dy*dy>a*a and all((x-cx)**2+(y-cy)**2<r*r for x,y in corners)
    if any(not inside_pad(point,p,True) for point in corners):return False
    return all(nx*x+ny*y>Q(*plane['threshold_nm']) for plane in domain['planes']
               for nx,ny in [plane['normal']] for x,y in corners)


def search_shapes(domains,p):
    from shapely.geometry import Point,box,Polygon
    (cx,cy),hx,hy,r=primitive(p)
    pad=box(cx-hx+r,cy-hy+r,cx+hx-r,cy+hy-r)
    if r:pad=pad.buffer(r,quad_segs=64)
    result=[]
    for d in domains:
        if d['kind']=='annulus':result.append(Point(*d['centre_nm']).buffer(d['outer_radius_nm'],quad_segs=64).difference(Point(*d['centre_nm']).buffer(d['inner_radius_nm'],quad_segs=64)))
        else:result.append(pad.intersection(Polygon([(float(x),float(y)) for x,y in d['polygon']])))
    return result


def overlap_square(left,right,a,b,p):
    region=left.intersection(right)
    if region.is_empty or region.area<=0:return None
    point=region.representative_point();x=round(point.x);y=round(point.y)
    for h in (10000,5000,1000,100,10,1):
        square=[x-h,y-h,x+h,y+h]
        if square_inside(square,a,p) and square_inside(square,b,p):return square
    return None


def overlap_tree(domains,p):
    shapes=search_shapes(domains,p);seen={0};order=[0];tree=[]
    # Each reached node is processed once; no requirement for annuli to overlap
    # directly. Any missing constructive connection causes a fail-closed row.
    cursor=0
    while cursor<len(order):
        parent=order[cursor];cursor+=1
        for child in range(len(domains)):
            if child in seen:continue
            square=overlap_square(shapes[parent],shapes[child],domains[parent],domains[child],p)
            if square:
                seen.add(child);order.append(child)
                tree.append({'parent':parent,'child':child,'square_nm':square,'area_nm2':(square[2]-square[0])*(square[3]-square[1])})
    if len(seen)!=len(domains):raise ValueError('missing exact positive-overlap tree: '+str(sorted(set(range(len(domains)))-seen)))
    return order,tree


def certify(pad,targets,items,all_holes,outline,face):
    p=pad['analytic_primitives'][face];(cx,cy),hx,hy,_=primitive(p)
    if pad['net']!='AGND' or set(pad['copper'])!={face}:raise ValueError('one actual AGND SMD face required')
    if not rectangle_in_board([cx-hx,cy-hy,cx+hx,cy+hy],outline):raise ValueError('native cut clips source pad')
    ids={h['uuid'] for h in targets}
    if len(ids)!=len(targets) or not 2<=len(ids)<=4:raise ValueError('exact two-to-four unique target drills required')
    annuli=[]
    for hole in targets:
        via=items[hole['uuid']];vp=via['analytic_primitives'][face];centre,rx,ry,_=primitive(vp)
        hc=tuple(map(nm,hole['xy_mm']));sx,sy=map(nm,hole['size_mm']);ri=Q(sx,2)
        if hole['net']!='AGND' or via['net']!='AGND' or not hole['plated'] or face not in hole['copper_layers'] or face not in via['copper'] or via['uuid']!=hole['uuid']:
            raise ValueError('same-net plated target via identity/face required')
        if vp['kind']!='circle' or rx!=ry or hc!=centre or sx!=sy or sx<=0 or ri.denominator!=1:raise ValueError('actual concentric circular annulus required')
        ri=int(ri)
        if rx*rx<=Q(5,4)*ri*ri:raise ValueError('full annulus fails octagon radius margin')
        if pad_circle_disjoint(p,hc,ri):raise ValueError('target drill does not intersect actual source pad')
        if not rectangle_in_board([hc[0]-rx,hc[1]-rx,hc[0]+rx,hc[1]+rx],outline):raise ValueError('native cut clips full annulus')
        annuli.append({'kind':'annulus','centre_nm':list(hc),'inner_radius_nm':ri,'outer_radius_nm':rx,'via_uuid':via['uuid'],'via_primitive':vp,'drill':hole})
    for other in all_holes:
        oc=tuple(map(nm,other['xy_mm']));sx,sy=map(nm,other['size_mm'])
        if min(sx,sy)<=0:raise ValueError('invalid hole geometry')
        radius=Q(sx,2) if sx==sy else Q(sx+sy,2)
        if other['uuid'] not in ids and not pad_circle_disjoint(p,oc,radius):raise ValueError('foreign drill clips source pad')
        for ann in annuli:
            if other['uuid']==ann['via_uuid']:continue
            if sum((x-y)**2 for x,y in zip(oc,ann['centre_nm']))<=(radius+ann['outer_radius_nm'])**2:
                raise ValueError('other drill clips full annulus: '+ann['via_uuid']+' / '+other['uuid'])
    pieces,empty=convex_branches(p,annuli);domains=annuli+pieces
    order,tree=overlap_tree(domains,p);positions={v:i for i,v in enumerate(order)}
    for d in pieces:d['bounding_polygon_nm_rationals']=encode_polygon(d.pop('polygon'))
    return {'ref':pad['ref'],'pad':pad['pad'],'pad_uuid':pad['uuid'],'net':'AGND','face':face,'source_primitive':p,
            'domains':domains,'pruned_choice_prefixes':empty,'complete_halfplane_choices':8**len(annuli),
            'positive_convex_leaves':len(pieces),'ordered_domain_ids':order,
            'ordered_parents':[-1]+[positions[e['parent']] for e in tree],'overlap_tree':tree,
            'all_hole_uuids_sha256':sha(json.dumps(sorted(h['uuid'] for h in all_holes)).encode()),
            'source_partition':'S=(actual pad minus ALL actual open drill disks). S_i=S intersect D_i minus all preceding D_j in ordered_domain_ids. L2-null boundaries ignored only.',
            'coverage':'Outside the union of full actual annuli, every point of S lies in at least one of the eight halfplanes for EACH drill. Distributive enumeration retains every positive-area intersection; exact pruned prefixes have zero source area.',
            'status':'EXACT HISTORICAL NOMINAL GEOMETRY ONLY; physical source/current/3D/primal/model admission OPEN'}


def run(mapping_path,previous_path,output):
    mapping_path=Path(mapping_path);previous_path=Path(previous_path);output=Path(output)
    if output.exists():raise ValueError('fresh multi-drill certificate required')
    mapping_raw=mapping_path.read_bytes();previous_raw=previous_path.read_bytes()
    if sha(mapping_raw)!=MAPPING_SHA256 or sha(previous_raw)!=PREVIOUS_SHA256:raise ValueError('retained historical mapping/single-drill receipt changed')
    mapping=json.loads(mapping_raw);previous=json.loads(previous_raw)
    bindings=dict(previous['source_sha256'])
    paths=[mapping_path,previous_path,Path(__file__),ROOT/'scripts/pcbgen/single_drill_cover.py']
    for p in paths:
        name=str(p.resolve().relative_to(ROOT));value=sha(p.read_bytes())
        if name in bindings and bindings[name]!=value:raise ValueError('source epoch conflicts')
        bindings[name]=value
    if any(sha((ROOT/n).read_bytes())!=h for n,h in bindings.items()):raise ValueError('historical dependency changed')
    frozen=ROOT/'.circuit-cache/issue38-recovery/white-land-review'
    part=json.loads((frozen/'partition.json').read_bytes());io=json.loads((frozen/'io-partition.json').read_bytes())
    done=[];unresolved=[];seen=set()
    for group in mapping['boards']:
        rows=[r for r in group['own_source_contacts'] if (group['board_id'],r['ref'],r['pad']) in TARGETS]
        if not rows:continue
        native=json.loads((ROOT/group['native_export_path']).read_bytes());boardpath=Path(native['board'].replace('/work/',str(ROOT)+'/'))
        if not boardpath.is_absolute():boardpath=ROOT/boardpath
        outline=native_outline(boardpath.read_text(),native['outline_mm'])
        key=next(b['board_key'] for b in part['boards'] if b['id']==group['board_id'])
        refs={p['ref'] for p in part['assignment']['components'] if p['board']==key and p['fitted']}
        pads=reconcile_native(native,expected_contacts(group['board_id'],part,io,{'AGND'}),refs,{'AGND'})
        items={i['uuid']:i for i in native['items']};holes={h['uuid']:h for h in native['holes']}
        if len(items)!=len(native['items']) or len(holes)!=len(native['holes']):raise ValueError('duplicate native identity')
        for row in rows:
            identity=(group['board_id'],row['ref'],row['pad'])
            if identity in seen:raise ValueError('duplicate target')
            seen.add(identity);pad=pads[row['ref'],row['pad'],'AGND']
            if pad['uuid']!=row['uuid'] or pad['analytic_primitives'][row['face']]!=row['primitive']:raise ValueError('source/native primitive mismatch')
            try:
                cert=certify(pad,[holes[u] for u in row['actual_or_unproved_drill_uuids']],items,native['holes'],outline,row['face'])
                cert.update(board_id=group['board_id'],native_export_sha256=group['native_export_sha256'],board_sha256=group['board_sha256']);done.append(cert)
            except ValueError as error:unresolved.append({'board_id':group['board_id'],'ref':row['ref'],'pad':row['pad'],'reason':str(error)})
    if seen!=TARGETS:raise ValueError('five actual source identities incomplete')
    if any(sha((ROOT/n).read_bytes())!=h for n,h in bindings.items()):raise ValueError('source changed during certificate construction')
    import shapely
    result={'scope':'Additional exact nominal geometry only; previous213 receipt immutable, all305PTH OPEN. No source/physical/current/3D/primal/model admission.',
            'source_sha256':bindings,'previous_single_drill_receipt_sha256':sha(previous_raw),
            'overlap_search_only_shapely_version':shapely.__version__,'certified_count':len(done),'unresolved_count':len(unresolved),
            'certificates':done,'unresolved':unresolved,'PTH_open_count':305}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mapping',type=Path);parser.add_argument('previous',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()
    receipt=run(args.mapping,args.previous,args.output);print({k:receipt[k] for k in ('certified_count','unresolved_count','PTH_open_count')})
