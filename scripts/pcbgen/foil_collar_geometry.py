"""Local proposed foil collars from a retained native projection; no board edits.

Default runs check portable retained geometry. --native-root additionally
checks the exact preserved native/export bytes and recomputes the projection.
Neither mode reconstructs a proposed PCB or admits its electrical model.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.netlist import TOKEN,parse,one,many
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE

PROPOSAL=ROOT/'design/partition/gh-foil-collar-proposal.json'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def inflate(box,r):return [box[0]-r,box[1]-r,box[2]+r,box[3]+r]
def overlaps(a,b):return all(a[i]<b[i+2]-1e-10 and b[i]<a[i+2]-1e-10 for i in (0,1))
def contains(a,b):return all(a[i]<=b[i]+1e-9 and b[i+2]<=a[i+2]+1e-9 for i in (0,1))
def union_box(boxes):return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]
def gap(a,b):return max(a[0]-b[2],b[0]-a[2],a[1]-b[3],b[1]-a[3])


def positive_interval(value):
    if len(value)!=2 or not all(math.isfinite(v) for v in value) or not 0<value[0]<value[1]:
        raise ValueError('finite positive nonzero-width parameter interval required')
    return value


def point_inside(point,polygon):
    x,y=point;inside=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside


def require_interior_rectangle(box,polygon):
    # A rectangle with all corners inside can still cross a concave notch.
    # Exclude every outline edge whose bounding box touches its interior too.
    corners=[[box[i],box[j]] for i in (0,2) for j in (1,3)]
    if not all(point_inside(p,polygon) for p in corners):raise ValueError('proposal leaves actual board outline')
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        edge=[min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])]
        if overlaps(inflate(edge,1e-8),box):raise ValueError('proposal intersects board outline')


def copper_boxes(item):
    result={}
    for layer,polys in item['copper'].items():
        points=[p for poly in polys for p in poly['shell']]
        if points:result[layer]=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
    return result


def footprint_node(text,ref):
    marker='(property "Reference" '+json.dumps(ref)
    position=text.find(marker)
    if position<0 or text.find(marker,position+len(marker))>=0:raise ValueError('one exact native footprint reference required')
    start=text.rfind('\n\t(footprint ',0,position)+2
    if start<2:raise ValueError('native footprint block missing')
    depth=0;quoted=False;escaped=False
    for end in range(start,len(text)):
        c=text[end]
        if quoted:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c=='"':quoted=False
            continue
        if c=='"':quoted=True
        elif c=='(':depth+=1
        elif c==')':
            depth-=1
            if depth==0:return parse(TOKEN.findall(text[start:end+1]))[0]
    raise ValueError('unterminated native footprint')


def project_items(data,window):
    result=[]
    for item in data['items']:
        boxes=copper_boxes(item)
        if any(overlaps(box,window) for box in boxes.values()):
            result.append({k:item[k] for k in ('uuid','net','ref','pad') if k in item}|{
                'copper_bbox_mm':boxes,'primitive_kinds':{l:p['kind'] for l,p in item.get('analytic_primitives',{}).items()}})
    return result


def hole_box(hole):
    x,y=hole['xy_mm'];r=max(hole['size_mm'])/2
    return [x-r,y-r,x+r,y+r]


def project_zones(data,window):
    result=[]
    for zone in data['zones']:
        points=[p for poly in zone['contours'] for p in poly['shell']]
        if not points:continue
        box=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
        if overlaps(box,window):
            result.append({k:zone[k] for k in ('uuid','layer','net','keepout','tracks_forbidden','vias_forbidden') if k in zone}|{'bbox_mm':box})
    return result


def verify_native(board,root):
    path=root/board['native_board_path'];export=root/board['native_geometry_path']
    if not path.is_file() or not export.is_file():raise ValueError('required preserved native artifact unavailable; no native check passed')
    if digest(path)!=board['native_board_sha256'] or digest(export)!=board['native_geometry_sha256']:
        raise ValueError('preserved native/export hash mismatch')
    data=json.loads(export.read_bytes());snapshot=board['snapshot'];window=snapshot['scan_window_mm']
    if data['board_sha256']!=board['native_board_sha256'] or data['board_id']!=board['board_id']:
        raise ValueError('native export belongs to another board')
    actual=next(i for i in data['items'] if i['uuid']==board['pad_uuid'])
    primitive=actual['analytic_primitives'][board['face']]
    if (actual['xy_mm']!=board['native_pad_xy_mm'] or primitive['quarter_turns']!=board['native_pad_quarter_turns']
            or primitive['kind']!='rectangle' or [2*v/1e6 for v in primitive['half_size_nm']]!=board['native_pad_size_mm']):
        raise ValueError('native analytic pad transform/shape differs')
    if max(data['native_project_rules']['min_track_width'],data['routing']['min_track_width_mm'])!=snapshot['minimum_native_track_width_mm']:
        raise ValueError('retained minimum track width differs from exported project/routing rules')
    if project_items(data,window)!=snapshot['items']:raise ValueError('retained item projection differs from complete native export')
    if [h for h in data['holes'] if overlaps(hole_box(h),window)]!=snapshot['holes']:
        raise ValueError('retained hole projection differs from complete native export')
    if project_zones(data,window)!=snapshot['zone_clip_candidates']:raise ValueError('zone clip identity coverage differs')
    for key in ('coordinate_frame','outline_mm','stackup','enabled_copper_layers'):
        if data[key]!=snapshot[key]:raise ValueError('native projection metadata differs: '+key)
    if len(data['items'])!=snapshot['whole_export_item_count'] or len(data['holes'])!=snapshot['whole_export_hole_count']:
        raise ValueError('full native inventory count differs')
    text=path.read_text();fp=footprint_node(text,board['reference'])
    targets={z['uuid'] for z in snapshot['zone_clip_candidates'] if z['layer']==board['board_access']['target_plane'] and z['net']=='AGND'}
    found={}
    for start,end in top_level_spans(text):
        block=text[start:end]
        if not re.match(r'\(zone\s',block):continue
        match=UUID_RE.search(block)
        if match and match[1] in targets:
            priority=re.search(r'\(priority\s+(\d+)\)',block)
            found[match[1]]=int(priority[1]) if priority else 0
    if set(found)!=targets or any(p!=board['board_access']['target_zone_priority'] for p in found.values()):
        raise ValueError('retained target-zone priority differs from source')
    pad=next(p for p in many(fp,'pad') if p[1]==board['pad'])
    if (one(fp,'uuid')[1]!=board['footprint_uuid'] or one(fp,'layer')[1]!=board['face']
            or list(map(float,one(fp,'at')[1:]))!=board['native_footprint_at_mm_deg']
            or one(pad,'uuid')[1]!=board['pad_uuid'] or one(pad,'net')[1]!='AGND'
            or list(map(float,one(pad,'size')[1:]))!=board['native_pad_size_mm']):
        raise ValueError('native footprint/pad identity, face or transform differs')
    # All local pad masks must obey the retained zero-expansion baseline.
    if not re.search(r'\(pad_to_mask_clearance\s+0\)',text):raise ValueError('native global mask expansion changed')
    cached={board['reference']:fp}
    for item in snapshot['items']:
        if 'ref' not in item:continue
        ref=item['ref']
        if ref not in cached:cached[ref]=footprint_node(text,ref)
        f=cached[ref];p=next(p for p in many(f,'pad') if p[1]==item['pad'])
        if any(float(row[1])!=0 for node in (f,p) for row in many(node,'solder_mask_margin')):
            raise ValueError('local mask override exceeds retained baseline')
    return 'PASS: exact preserved native bytes and complete local projection; proposed reconstruction NOT RUN'


def geometry(board,g):
    x,y=board['native_pad_xy_mm'];direction=board['outward_direction_y'];w,h=board['native_pad_size_mm']
    edge=y+direction*h/2;cx=x+g['neck_x_offset_mm'];n0=edge+direction*g['nominal_shoulder_length_mm'];n1=n0+direction*g['nominal_neck_length_mm']
    end=n1+direction*g['nominal_flare_length_mm'];width=g['nominal_neck_width_mm'];fw=sum(g['flare_width_interval_mm'])/2
    def face(xc,yy,ww):return [[xc-ww/2,yy],[xc+ww/2,yy]]
    def taper(a,b):return a+b[::-1]
    eps=g['foreign_and_pad_copper_edge_abs_max_mm'];reg=g['relative_registration_abs_max_mm']
    shoulder=g['finished_shoulder_length_interval_mm'];length=g['finished_neck_length_interval_mm'];flare=g['finished_flare_length_interval_mm']
    near=[edge+direction*s+e for s in shoulder for e in (-eps,eps)]
    far=[v+direction*l for v in near for l in length]
    tail=[v+direction*l for v in far for l in flare]
    dry=[cx-reg-g['finished_neck_width_interval_mm'][1]/2,min(near+far),cx+reg+g['finished_neck_width_interval_mm'][1]/2,max(near+far)]
    pad=[x-w/2,y-h/2,x+w/2,y+h/2];pad_worst=inflate(pad,eps)
    island=union_box([pad_worst,dry])
    flare_box=[cx-reg-g['flare_width_interval_mm'][1]/2,min(far+tail),cx+reg+g['flare_width_interval_mm'][1]/2,max(far+tail)]
    clear_window=inflate(island,g['copper_isolation_clearance_mm'])
    overlap=(min(tail)-clear_window[3]) if direction>0 else (clear_window[1]-max(tail))
    if overlap<=0:raise ValueError('flare cannot reach beyond the island isolation over its full interval')
    return {'nominal_pad_bbox_mm':pad,'shoulder_polygon_mm':taper(face(x,edge,w),face(cx,n0,width)),
            'collar_polygon_mm':taper(face(cx,n0,width),face(cx,n1,width)),
            'board_flare_polygon_mm':taper(face(cx,n1,width),face(cx,end,fw)),
            'worst_dry_collar_bbox_mm':dry,'worst_island_bbox_mm':island,'worst_flare_bbox_mm':flare_box,
            'own_face_zone_clear_window_mm':clear_window,'minimum_flare_reconnection_overlap_mm':overlap,
            'other_foil_zone_clear_window_mm':inflate(dry,g['copper_isolation_clearance_mm']),
            'inner_cut_nominal_y_mm':n0,'outer_cut_nominal_y_mm':n1,'neck_centre_x_mm':cx,
            'outer_normal_native_xyz':[0,direction,0]}


def compile_proposal(spec,*,verify_source=True,native_root=None):
    if verify_source:
        for name,want in spec['source_files'].items():
            if digest(ROOT/name)!=want:raise ValueError('source file hash drift: '+name)
        if 'source_transition' in spec:
            bound=spec['source_transition'];proof_path=ROOT/bound['proof']
            if not proof_path.is_file() or digest(proof_path)!=bound['proof_sha256']:
                raise ValueError('source transition proof unavailable or changed')
            proof=json.loads(proof_path.read_bytes());transition=dict(proof['connector_locality_transition'])
            jack=proof.get('jack_locality_transition')
            if jack:
                # Later jack-half-only change: chain it onto the connector transition.
                if jack['base_partition_sha256']!=transition['current_partition_sha256']:raise ValueError('source transition chain is broken')
                transition['current_partition_sha256']=jack['current_partition_sha256']
            if (any(bound.get(k)!=transition.get(k) for k in
                    ('base_commit','historical_partition_sha256','current_partition_sha256')) or
                    bound['current_partition_sha256']!=spec['source_files']['design/partition/partition.json'] or
                    digest(ROOT/transition['proposal'])!=transition['proposal_sha256']):
                raise ValueError('source transition does not match the bounded connector change')
    g=spec['geometry']
    for name,value in g.items():
        if name.endswith('_interval_mm'):positive_interval(value)
    for part in ('neck_width','neck_length','shoulder_length','flare_length'):
        nominal=g['nominal_'+part+'_mm'];lo,hi=g['finished_'+part+'_interval_mm']
        if not math.isfinite(nominal) or not lo<=nominal<=hi:raise ValueError('nominal geometry must belong to proposed finished interval')
    if not math.isfinite(g['neck_x_offset_mm']):raise ValueError('finite neck offset required')
    rho=positive_interval(spec['material']['volume_resistivity_interval_ohm_mm'])
    for name in ('relative_registration_abs_max_mm','foreign_and_pad_copper_edge_abs_max_mm','copper_isolation_clearance_mm','mask_expansion_upper_mm','mask_registration_abs_max_mm','solder_over_mask_extent_upper_mm','required_dry_separation_mm'):
        if not math.isfinite(g[name]) or g[name]<=0:raise ValueError('positive finite geometry allowance required')
    if len(spec['boards'])!=2 or {b['board_key'] for b in spec['boards']}!={'JL','K'}:raise ValueError('one complete JL/K pair required')
    partition=json.loads((ROOT/'design/partition/partition.json').read_bytes())
    headers={r['id']:r for r in partition['connectors']};results=[]
    for board in spec['boards']:
        snapshot=board['snapshot'];header=headers[board['connector_id']]
        if (board['outward_direction_y']!={'JL':-1,'K':1}[board['board_key']]
                or board['net']!='AGND' or board['native_pad_quarter_turns']!=2):
            raise ValueError('this bound projection requires the selected pad orientation and AGND net')
        shape=geometry(board,g)
        origin=[header['footprint_origin_mm'][i]+snapshot['coordinate_frame']['source_to_native_translation_mm'][i] for i in (0,1)]
        if (header['pcb_reference']!=board['reference'] or header['side']!=board['face'] or header['pin_map'].get(board['pad'])!='AGND'
                or origin!=board['native_footprint_at_mm_deg'][:2] or header['kicad_orientation_deg']!=board['native_footprint_at_mm_deg'][2]):
            raise ValueError('source/native connector identity or transform differs')
        if any(header[key]!=spec[key] for key in ('header_mpn','housing_mpn','contact_mpn')):
            raise ValueError('exact connector component identity differs')
        items={r['uuid']:r for r in snapshot['items']}
        if len(items)!=len(snapshot['items']):raise ValueError('duplicate native item UUID')
        target=items.get(board['pad_uuid'])
        if (not target or target.get('ref')!=board['reference'] or target.get('pad')!=board['pad'] or target['net']!='AGND'
                or set(target['copper_bbox_mm'])!={board['face']} or not all(math.isclose(a,b,rel_tol=0,abs_tol=1e-9) for a,b in zip(target['copper_bbox_mm'][board['face']],shape['nominal_pad_bbox_mm']))):
            raise ValueError('retained actual pad identity/geometry differs')
        if g['nominal_neck_width_mm']<snapshot['minimum_native_track_width_mm']:
            raise ValueError('nominal neck violates native minimum track rule')
        retire={r['uuid'] for r in board['proposed_retirements']}
        if len(retire)!=len(board['proposed_retirements']):raise ValueError('duplicate retirement')
        holes={h['uuid']:h for h in snapshot['holes']}
        for r in board['proposed_retirements']:
            item=items.get(r['uuid'])
            if not item or item.get('ref') or item['net']!='AGND':raise ValueError('retirement may remove only exact non-pad AGND copper')
            if r['kind']=='via':
                if r['uuid'] not in holes or not holes[r['uuid']]['plated']:raise ValueError('retired via lacks actual plated hole')
            elif r['kind']!='track' or set(item['primitive_kinds'].values())!={'segment'}:raise ValueError('retired track is not exact native segment')
        access=board['board_access'];added=[]
        for priority in (board['collar_zone_priority'],access['target_zone_priority']):
            if type(priority) is not int or not 0<=priority<=2147483647:raise ValueError('explicit nonnegative native zone priority required')
        if board['native_realization_scope'] not in ('local_only_experiment','full_refill_draft_epoch'):
            raise ValueError('explicit native realization scope required')
        if access['net']!='AGND':raise ValueError('PCB-side access must remain AGND')
        if access['kind']=='proposed_new_via_and_dogleg':
            positive_interval(access['finished_drill_interval_mm']);positive_interval(access['finished_barrel_copper_interval_mm'])
            if (not math.isfinite(access['via_diameter_mm']) or access['via_diameter_mm']-2*g['foreign_and_pad_copper_edge_abs_max_mm']<=access['finished_drill_interval_mm'][1]
                    or not access['finished_drill_interval_mm'][0]<=access['via_drill_mm']<=access['finished_drill_interval_mm'][1]
                    or not math.isfinite(access['track_width_mm']) or access['track_width_mm']<snapshot['minimum_native_track_width_mm']):
                raise ValueError('new via/track requires positive annulus, finite dimensions and native track rule')
            points=access['track_points_native_mm']
            if len(points)<2 or not all(len(p)==2 and all(math.isfinite(v) for v in p) for p in points):raise ValueError('finite connected dogleg vertices required')
            if points[-1]!=access['via_centre_native_mm'] or not point_inside(points[0],shape['board_flare_polygon_mm']):
                raise ValueError('new dogleg must join the flare and end at its via')
            x,y=access['via_centre_native_mm'];r=access['via_diameter_mm']/2+g['foreign_and_pad_copper_edge_abs_max_mm']+g['relative_registration_abs_max_mm']
            added.append(('new via',[x-r,y-r,x+r,y+r],snapshot['enabled_copper_layers']))
            radius=access['track_width_mm']/2+g['foreign_and_pad_copper_edge_abs_max_mm']+g['relative_registration_abs_max_mm']
            for i,(a,b) in enumerate(zip(access['track_points_native_mm'],access['track_points_native_mm'][1:])):
                added.append(('new dogleg '+str(i),inflate([min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])],radius),[board['face']]))
        elif access['kind']!='same_foil_AGND_pour':raise ValueError('explicit PCB-side access required')
        eps=g['foreign_and_pad_copper_edge_abs_max_mm'];clearance=g['copper_isolation_clearance_mm'];separations=[];mask_gaps=[]
        query=union_box([shape['own_face_zone_clear_window_mm'],shape['other_foil_zone_clear_window_mm'],inflate(shape['worst_flare_bbox_mm'],clearance)]+[inflate(b,clearance) for _,b,_ in added])
        if not contains(snapshot['scan_window_mm'],inflate(query,eps)):raise ValueError('proposal exceeds complete retained projection window')
        require_interior_rectangle(inflate(query,eps),snapshot['outline_mm'])
        for item in snapshot['items']:
            if item['uuid'] in retire or item['uuid']==board['pad_uuid']:continue
            for layer,box in item['copper_bbox_mm'].items():
                obstacle=inflate(box,eps)
                checks=[('dry collar',shape['worst_dry_collar_bbox_mm'])]
                if layer==board['face']:checks += [('island',shape['worst_island_bbox_mm']),('flare',shape['worst_flare_bbox_mm'])]
                checks += [(name,b) for name,b,layers in added if layer in layers]
                for name,region in checks:
                    distance=gap(region,obstacle)
                    if distance<clearance-1e-9:raise ValueError(f'{board["board_key"]}: {name} conflicts with {item["uuid"]} on {layer}; conservative separation {distance:.6f} mm < {clearance}')
                    separations.append({'region':name,'obstacle_uuid':item['uuid'],'layer':layer,'axis_separation_lower_mm':distance})
        for hole in snapshot['holes']:
            if hole['uuid'] in retire:continue
            for region in [shape['worst_island_bbox_mm'],shape['worst_flare_bbox_mm']]+[b for _,b,_ in added]:
                if gap(inflate(hole_box(hole),eps),region)<clearance-1e-9:raise ValueError('unretired drill/barrel enters island/collar or paid access clearance')
        for name,box,layers in added:
            if overlaps(box,shape['worst_island_bbox_mm']):raise ValueError('new PCB-side access enters isolated island/collar and bypasses its cut')
        wet=g['mask_expansion_upper_mm']+g['mask_registration_abs_max_mm']+g['solder_over_mask_extent_upper_mm']
        for item in snapshot['items']:
            if 'ref' not in item or board['face'] not in item['copper_bbox_mm']:continue
            maximum=inflate(item['copper_bbox_mm'][board['face']],wet+eps)
            distance=gap(shape['worst_dry_collar_bbox_mm'],maximum)
            if distance<g['required_dry_separation_mm']-1e-9:raise ValueError('full possible solder/mask support enters required dry collar')
            mask_gaps.append({'pad_uuid':item['uuid'],'possible_wetting_bbox_mm':maximum,'dry_separation_lower_mm':distance})
        clips=[]
        for zone in snapshot['zone_clip_candidates']:
            window=shape['own_face_zone_clear_window_mm'] if zone['layer']==board['face'] else shape['other_foil_zone_clear_window_mm']
            if zone['keepout'] and overlaps(window,zone['bbox_mm']):raise ValueError('proposal enters pre-existing native keepout')
            if not zone['keepout']:
                clips.append({'zone_uuid':zone['uuid'],'layer':zone['layer'],'net':zone['net'],'subtract_window_mm':window,'status':'PROPOSED local set difference; no complete native zone retired or refilled'})
                # JL's outer foil is +5V, not ground. Every new AGND access
                # primitive needs its own rail-pour clearance, including all
                # via antipads. Retain the intended AGND landing plane.
                if zone['net']!='AGND':
                    if zone['layer']==board['face']:
                        clips.append({'zone_uuid':zone['uuid'],'layer':zone['layer'],'net':zone['net'],
                                      'subtract_window_mm':inflate(shape['worst_flare_bbox_mm'],clearance),
                                      'status':'PROPOSED clearance for the complete AGND flare'})
                    for name,box,layers in added:
                        if zone['layer'] in layers:
                            clips.append({'zone_uuid':zone['uuid'],'layer':zone['layer'],'net':zone['net'],
                                          'subtract_window_mm':inflate(box,clearance),'status':'PROPOSED AGND '+name+' clearance/antipad'})
        if not any(z.get('net')=='AGND' and z['layer']==access['target_plane'] for z in snapshot['zone_clip_candidates']):
            raise ValueError('PCB-side access has no retained AGND target plane')
        if access['target_plane']==board['face'] and board['collar_zone_priority']==access['target_zone_priority']:
            raise ValueError('same-face collar and landing zone require distinct priorities')
        layer=next(r for r in snapshot['stackup'] if r['layer']==board['face']);t=layer['copper_thickness_mm'];mid=layer['nominal_midplane_depth_mm']
        results.append({'board_key':board['board_key'],'actual_pad_uuid':board['pad_uuid'],'proposed_geometry':shape,
            'collar_zone_priority':board['collar_zone_priority'],'native_realization_scope':board['native_realization_scope'],
            'proposed_retirements':board['proposed_retirements'],'proposed_zone_clips':clips,'proposed_PCB_access':access,
            'minimum_conservative_copper_separation_mm':min(v['axis_separation_lower_mm'] for v in separations),
            'minimum_dry_wetting_separation_mm':min(v['dry_separation_lower_mm'] for v in mask_gaps),
            'clearance_receipts':separations,'mask_receipts':mask_gaps,
            'proposed_mask_rule':'Retain existing pad openings only; no opening on shoulder, complete collar, flare, dogleg or new via. Full possible pad wetting includes copper edge, expansion, registration and over-mask extent. Seal/process and three-dimensional solder support remain unqualified.',
            'full_trace':{'nominal_native_x_mm':[shape['neck_centre_x_mm']-g['nominal_neck_width_mm']/2,shape['neck_centre_x_mm']+g['nominal_neck_width_mm']/2],
                          'nominal_native_y_mm':shape['outer_cut_nominal_y_mm'],'nominal_stack_depth_mm':[mid-t/2,mid+t/2],
                          'normal':shape['outer_normal_native_xyz'],'profile':'Signed I/(actual full width * actual full foil thickness), over the complete cut; opposing endpoint net currents sum to zero. Potential constant across the complete possible cut support; geometry/material pullback metric not yet proved.'},
            'native_snapshot_binding':verify_native(board,native_root) if native_root else 'NOT RUN: retained projection only; use --native-root with preserved artifacts',
            'new_native_reconstruction':'NOT RUN: proposal has not been applied/refilled/rule-checked on either native board'})
    return {'status':'PASS: bounded retained-projection geometry screen for an UNSELECTED proposal only','pair_id':spec['pair_id'],'boards':results,
            'straight_reference_neck_resistance_upper_ohm':rho[1]*g['finished_neck_length_interval_mm'][1]/(g['finished_neck_width_interval_mm'][0]*g['finished_foil_thickness_interval_mm'][0]),
            'cost_ledger':[
                {'region':'both isolated pads, pad-side shoulders, full collars, both contacts/crimps and complete wire','account':'One independently certified isolated assembled-harness test domain; collar costs already inside that bound, never added again. No such test certificate exists.'},
                {'region':'JL board-side flare, dogleg, new via/annular transfer and In1 spreading','account':'Outside tested domain; full matched current/voltage energy bounds OPEN. An axial barrel estimate alone is insufficient.'},
                {'region':'K board-side flare and F.Cu spreading','account':'Outside tested domain; full matched current/voltage energy bounds OPEN.'},
                {'region':'remaining branch+K common copper and every other return path','account':'Original combined <=0.5 mOhm common requirement remains; no resistance is removed or ideal ground invented.'}],
            'electrical_limits':spec['electrical_limits'],'test_admission':spec['test_admission'],
            'limits':[spec['claim_boundary'],'Cross-layer XY overlap alone is not a DC short. This candidate conservatively reserves a clear projection around its full collar and excludes all drills/barrels; dielectric/side isolation still requires actual process evidence.','The resistance number is for a straight homogeneous reference prism, not the complete access or a proved manufactured-class upper.','Nominal CAD minimum track width and finished etch-width interval are different requirements. No fabrication capability, mask seal, fixture isolation or remating certificate is implied.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--proposal',type=Path,default=PROPOSAL);parser.add_argument('--native-root',type=Path)
    args=parser.parse_args();print(json.dumps(compile_proposal(json.loads(args.proposal.read_bytes()),native_root=args.native_root),indent=2))

if __name__=='__main__':main()
