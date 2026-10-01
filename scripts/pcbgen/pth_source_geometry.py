"""Native-bound PTH face geometry and explicitly conditional nominal wall.

Every physical foil is retained. F/B source faces and the complete inner wall
are separate records; interior foils are attachments, not exposed sources.
No current, lead, solder, process or paired primal witness is admitted here.
"""
import argparse
import json
from pathlib import Path
from fractions import Fraction as Q
import re

from scripts.pcbgen.single_drill_cover import (
    ROOT,MAPPING_SHA256,sha,nm,primitive,pad_circle_disjoint,
    native_outline,rectangle_in_board,
)
from scripts.pcbgen.multi_drill_cover import (
    convex_branches,overlap_tree,encode_polygon,square_inside,
)
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE
from scripts.pcbgen.netlist import TOKEN,parse,one,many
from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native

SINGLE_SHA='9750c2e223e963e2ce2bf344967a5a78fb687be9fd263369cd1568e8e461dd79'
MULTI_SHA='1e2bd5decc29c5ed003e92222c5952a7a5cc1b5ce7ba47715ca5f036b090fc53'
CLASS=ROOT/'design/partition/pth-boundary-geometry-class.json'


def native_physical_stack(text,rows):
    blocks=[text[a:b] for a,b in top_level_spans(text)]
    def unique(name):
        found=[b for b in blocks if b.startswith('('+name+'\n')]
        if len(found)!=1:raise ValueError('exact native '+name+' block required')
        return parse(TOKEN.findall(found[0]))[0]
    general=unique('general');depth=nm(one(general,'thickness')[1])
    setup=unique('setup');stack=one(setup,'stackup');native=many(stack,'layer')
    if len(native)!=len(rows):raise ValueError('native/source stack layer count differs')
    bands=[];z=0;gap=0
    for node,row in zip(native,rows):
        copper=row['layer'].endswith('.Cu')
        if copper:name=row['layer'];width=nm(row['copper_thickness_mm']);kind='copper'
        else:gap+=1;name='dielectric '+str(gap);width=nm(row['thickness_mm']);kind='dielectric'
        if node[1]!=name or one(node,'type')[1]!=kind or nm(one(node,'thickness')[1])!=width or width<=0:
            raise ValueError('native/source physical stack differs')
        if copper:bands.append({'layer':name,'z_nm':[z,z+width],'thickness_nm':width})
        z+=width
    layers=[b['layer'] for b in bands]
    if layers not in [['F.Cu','B.Cu'],['F.Cu','In1.Cu','In2.Cu','B.Cu']] or z!=depth:
        raise ValueError('complete supported physical stack/depth required')
    native_layers=unique('layers')
    enabled=[n[1] for n in native_layers[1:] if isinstance(n,list) and len(n)>1 and isinstance(n[1],str) and n[1].endswith('.Cu')]
    if enabled!=layers:raise ValueError('native enabled foil sequence differs')
    return {'depth_nm':depth,'bands':bands,'enabled_layers':layers,
            'depth_coordinate':'Board-local stack depth: z=0 at F outer face, z=depth at B outer face; no assembly/world transform implied.'}


def native_pad_blocks(text):
    result={}
    for a,b in top_level_spans(text):
        block=text[a:b]
        if not block.startswith('(footprint'):continue
        ref=re.search(r'\(property "Reference" "([^"]+)"',block)
        if not ref:raise ValueError('native footprint reference absent')
        for x,y in top_level_spans(block):
            pad=block[x:y]
            if not pad.startswith('(pad '):continue
            match=UUID_RE.search(pad)
            if not match or match[1] in result:raise ValueError('native pad UUID absent/duplicate')
            result[match[1]]=(ref[1],pad)
    return result


def complete_wall(pad,hole,raw_pad,stack,plating_nm):
    ref,block=raw_pad
    parsed=parse(TOKEN.findall(block))[0]
    if ref!=pad['ref'] or parsed[1]!=pad['pad'] or parsed[2]!='thru_hole' or one(parsed,'uuid')[1]!=pad['uuid']:
        raise ValueError('source/native plated through-hole identity differs')
    if one(parsed,'net')[1]!='AGND' or pad['net']!='AGND' or hole['net']!='AGND' or not hole['plated'] or hole['uuid']!=pad['uuid']:
        raise ValueError('AGND plated wall required')
    drill=one(parsed,'drill')
    if len(drill)!=2:raise ValueError('circular native drill without offset required')
    sx,sy=map(nm,hole['size_mm']);ri=Q(sx,2)
    if sx!=sy or sx<=0 or nm(drill[1])!=sx or ri.denominator!=1:raise ValueError('circular exact drill radius required')
    if one(parsed,'layers')[1:]!=['*.Cu','*.Mask'] or one(parsed,'remove_unused_layers')[1:]!=['no']:
        raise ValueError('complete native through-hole foil span required')
    if hole['copper_layers']!=stack['enabled_layers'] or set(pad['copper'])!=set(stack['enabled_layers']) or set(pad['analytic_primitives'])!=set(stack['enabled_layers']):
        raise ValueError('incomplete actual wall/foil attachment inventory')
    if plating_nm!=25000:raise ValueError('unreviewed nominal plating condition')
    return {'native_evidence':'circular plated thru_hole, all physical foils retained; no native plating-thickness measurement',
            'kind':'inner_wall_source','centre_nm':list(map(nm,hole['xy_mm'])),
            'inner_radius_nm':int(ri),'contained_shell_outer_radius_nm':int(ri)+plating_nm,
            'z_nm':[0,stack['depth_nm']],'periodic_angular_domain':'0<=theta<2*pi, seam identified',
            'area_measure':'ri*dtheta*dz; full nominal area 2*pi*ri*depth',
            'minimum_finished_plating_nm_PROJECT_REQUIREMENT':plating_nm,
            'physical_finished_wall_and_plating_qualified':False}


def face_geometry(pad,hole,band,wall,all_holes,outline):
    face=band['layer'];p=pad['analytic_primitives'][face]
    centre,hx,hy,r=primitive(p);hc=tuple(map(nm,hole['xy_mm']));ri=wall['inner_radius_nm'];shell_ro=wall['contained_shell_outer_radius_nm'];R=min(hx,hy)
    if centre!=hc or p['kind'] not in ('rectangle','circle'):raise ValueError('actual concentric rectangle/circle PTH land required')
    if R<=shell_ro or R*R<=Q(5,4)*ri*ri:raise ValueError('insufficient nominal annular width beyond conditional plating')
    if not rectangle_in_board([hc[0]-hx,hc[1]-hy,hc[0]+hx,hc[1]+hy],outline):raise ValueError('native cut clips/touches annular source land')
    for other in all_holes:
        if other['uuid']==hole['uuid']:continue
        oc=tuple(map(nm,other['xy_mm']));sx,sy=map(nm,other['size_mm'])
        if min(sx,sy)<=0:raise ValueError('invalid other hole')
        radius=Q(sx,2) if sx==sy else Q(sx+sy,2)
        if not pad_circle_disjoint(p,oc,radius):raise ValueError('other drill clips annular source land: '+other['uuid'])
    ann={'kind':'annulus','centre_nm':list(hc),'inner_radius_nm':ri,'outer_radius_nm':R}
    # For circles the annulus is the entire source face. Rectangle corners
    # need the exact eight-halfplane cover; no rectangular hull fills a hole.
    pieces,empty=convex_branches(p,[ann]) if p['kind']=='rectangle' else ([],[])
    domains=[ann]+pieces;order,tree=overlap_tree(domains,p)
    for d in pieces:d['bounding_polygon_nm_rationals']=encode_polygon(d.pop('polygon'))
    # A finite contained patch in the shell/foil radial overlap at this band.
    # This is geometry of overlapping trial domains, not double Cu ownership
    # or a declaration that an intermediate surface is a physical electrode.
    t=shell_ro-ri;x=Q(hc[0])+ri+Q(t,2);y=Q(hc[1]);h=Q(t,8)
    square=[x-h,y-h,x+h,y+h]
    if any(v.denominator!=1 for v in square):raise ValueError('integer shell overlap witness required')
    square=list(map(int,square));narrow={**ann,'outer_radius_nm':shell_ro}
    if not square_inside(square,narrow,p) or not square_inside(square,ann,p):raise ValueError('missing finite shell-annulus overlap')
    exterior=face in ('F.Cu','B.Cu')
    return {'layer':face,'band_z_nm':band['z_nm'],'thickness_nm':band['thickness_nm'],
            'role':'exterior_annular_source_face' if exterior else 'interior_foil_attachment_only_NOT_exposed_source',
            'exterior_z_nm':0 if face=='F.Cu' else wall['z_nm'][1] if face=='B.Cu' else None,
            'outward_normal_stack_depth':-1 if face=='F.Cu' else 1 if face=='B.Cu' else None,
            'native_primitive':p,'annulus_outer_radius_nm':R,'nominal_radial_margin_beyond_minimum_shell_nm':R-shell_ro,
            'domains':domains,'pruned_halfplane_prefixes':empty,'ordered_domain_ids':order,
            'ordered_parents':[-1]+[order.index(e['parent']) for e in tree],'overlap_tree':tree,
            'shell_to_annulus_overlap_square_nm':square,'shell_to_annulus_overlap_area_nm2':(square[2]-square[0])*(square[3]-square[1]),
            'shell_to_foil_overlap_volume_nm3':(square[2]-square[0])*(square[3]-square[1])*band['thickness_nm'],
            'source_partition':'For this exterior face only: native land minus open drill, assigned to first covering domain. Internal foils have no independent exterior source.',
            'scope':'Exact nominal face/support overlap only. Wall-to-face/ref fields, flux cancellation, material ownership/cross energy and primal continuity NOT supplied.'}


def certify(pad,hole,raw_pad,stack,all_holes,outline,plating_nm=25000):
    wall=complete_wall(pad,hole,raw_pad,stack,plating_nm)
    faces=[face_geometry(pad,hole,band,wall,all_holes,outline) for band in stack['bands']]
    return {'ref':pad['ref'],'pad':pad['pad'],'uuid':pad['uuid'],'net':'AGND',
            'native_pad_block_sha256':sha(raw_pad[1].encode()),'native_hole':hole,'inner_wall':wall,
            'foil_faces':faces,'exterior_source_parts':['inner_wall','F.Cu_annular_face','B.Cu_annular_face'],
            'no_top_face_substitution':True,'all_foreign_holes_checked':len(all_holes)-1,
            'status':'NATIVE NOMINAL FACES + CONDITIONAL PROJECT WALL GEOMETRY ONLY; source/3D/primal/process/electrical admission OPEN'}


def run(mapping_path,single_path,multi_path,output):
    paths=list(map(Path,(mapping_path,single_path,multi_path)));output=Path(output)
    if output.exists():raise ValueError('fresh PTH geometry output required')
    raws=[p.read_bytes() for p in paths]
    if [sha(b) for b in raws]!=[MAPPING_SHA256,SINGLE_SHA,MULTI_SHA]:raise ValueError('historical mapping/SMD receipt drift')
    mapping,single,multi=map(json.loads,raws);bindings=dict(multi['source_sha256'])
    rule_raw=CLASS.read_bytes();rule=json.loads(rule_raw)
    if nm(rule['minimum_finished_plating_mm'])!=25000:raise ValueError('unreviewed PTH plating class')
    sources=paths+[CLASS,Path(__file__),ROOT/'scripts/pcbgen/multi_drill_cover.py',ROOT/'scripts/pcbgen/netlist.py']+[ROOT/p for p in rule['existing_nominal_sources']]
    for p in sources:
        key=str(p.resolve().relative_to(ROOT));value=sha(p.read_bytes())
        if key in bindings and bindings[key]!=value:raise ValueError('conflicting historical dependency')
        bindings[key]=value
    if any(sha((ROOT/p).read_bytes())!=h for p,h in bindings.items()):raise ValueError('native/source dependency drift')
    frozen=ROOT/'.circuit-cache/issue38-recovery/white-land-review'
    part=json.loads((frozen/'partition.json').read_bytes());io=json.loads((frozen/'io-partition.json').read_bytes())
    certificates=[];unresolved=[];seen=set()
    for group in mapping['boards']:
        rows=[r for r in group['own_source_contacts'] if r['family']=='PTH']
        if not rows:continue
        native=json.loads((ROOT/group['native_export_path']).read_bytes());boardpath=Path(native['board'].replace('/work/',str(ROOT)+'/'))
        if not boardpath.is_absolute():boardpath=ROOT/boardpath
        text=boardpath.read_text();stack=native_physical_stack(text,native['stackup']);outline=native_outline(text,native['outline_mm']);raw_pads=native_pad_blocks(text)
        key=next(b['board_key'] for b in part['boards'] if b['id']==group['board_id'])
        refs={p['ref'] for p in part['assignment']['components'] if p['board']==key and p['fitted']}
        pads=reconcile_native(native,expected_contacts(group['board_id'],part,io,{'AGND'}),refs,{'AGND'});holes={h['uuid']:h for h in native['holes']}
        if len(holes)!=len(native['holes']):raise ValueError('duplicate actual native hole UUID')
        for row in rows:
            pad=pads[row['ref'],row['pad'],'AGND'];identity=(group['board_id'],row['ref'],row['pad'])
            if pad['uuid']!=row['uuid'] or identity in seen:raise ValueError('PTH source identity drift')
            seen.add(identity)
            try:
                c=certify(pad,holes[row['uuid']],raw_pads[row['uuid']],stack,native['holes'],outline)
                c.update(board_id=group['board_id'],native_export_sha256=group['native_export_sha256'],board_sha256=group['board_sha256'],native_stack=stack);certificates.append(c)
            except (ValueError,KeyError) as error:
                unresolved.append({'board_id':group['board_id'],'ref':row['ref'],'pad':row['pad'],'uuid':row['uuid'],'native_hole':holes.get(row['uuid']),'native_primitives':pad.get('analytic_primitives'),'reason':str(error)})
    if len(seen)!=305:raise ValueError('complete305 PTH inventory required')
    if any(sha((ROOT/p).read_bytes())!=h for p,h in bindings.items()):raise ValueError('native/source changed during PTH geometry construction')
    import shapely
    result={'scope':'Exact retained nominal PTH faces; complete wall/plating CONDITIONAL PROJECT geometry. No manufactured wall/current/3D/primal/model admission.',
            'source_sha256':bindings,'plating_class':rule,'certified_nominal_geometry_count':len(certificates),'unresolved_count':len(unresolved),
            'actual_finished_plating_qualified_count':0,'previous_SMD_receipts_unchanged':[SINGLE_SHA,MULTI_SHA],
            'overlap_search_only_shapely_version':shapely.__version__,'certificates':certificates,'unresolved':unresolved}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f:json.dump(result,f,indent=2,sort_keys=True);f.write('\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('mapping','single','multi','output'):parser.add_argument(name,type=Path)
    a=parser.parse_args();r=run(a.mapping,a.single,a.multi,a.output)
    print({k:r[k] for k in ('certified_nominal_geometry_count','unresolved_count','actual_finished_plating_qualified_count')})
