"""Fresh ignored native realization of the unselected, source-owned foil proposal.

--prepare runs on the host and copies hash-checked originals; --run-board runs
only in the pinned oracle under heavy-guard. No canonical board is a destination.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.foil_collar_geometry import PROPOSAL,compile_proposal,digest,union_box,inflate
from scripts.pcbgen.uuid_tools import stable_uuid,top_level_spans,UUID_RE,replace_spans
from scripts.pcbgen.verify_local_links import blocks

DEFINITIONS={'JL':'design/partition/jack-white-current/osc-jack-left.json',
             'K':'design/partition/core-ground-feasibility/osc-core.json'}


def write_json(path,data):path.write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')


def require_cache(path,root=ROOT):
    path=path.resolve();allowed=(root/'.circuit-cache').resolve()
    if not path.is_relative_to(allowed) or path==allowed:raise ValueError('fresh descendant of this worktree .circuit-cache required')
    return path


def prepare(recovery,cache):
    cache=require_cache(cache)
    if cache.exists():raise ValueError('refuse to overwrite an existing native experiment')
    spec=json.loads(PROPOSAL.read_bytes());compiled=compile_proposal(spec,native_root=recovery)
    files={};board_inputs={}
    for b in spec['boards']:
        original=Path(b['native_board_path']);export=json.loads((recovery/b['native_geometry_path']).read_bytes())
        expected={b['native_board_path']:b['native_board_sha256'],b['native_geometry_path']:b['native_geometry_sha256'],
                  DEFINITIONS[b['board_key']]:export['definition_sha256']}
        for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
            name=str(original.with_suffix(suffix));expected[name]=digest(recovery/name)
        # The hierarchical schematic and relative local library tables are
        # part of parity authority, not optional convenience files.
        for path in (recovery/original.parent/'sheets').rglob('*.kicad_sch'):
            expected[str(path.relative_to(recovery))]=digest(path)
        for name in ('fp-lib-table','sym-lib-table'):
            path=original.parent/name;expected[str(path)]=digest(recovery/path)
        if expected[str(original.with_suffix('.kicad_pro'))]!=export['project_sha256']:
            raise ValueError('preserved project differs from native export authority')
        board_inputs[b['board_key']]={'definition':DEFINITIONS[b['board_key']], 'files':expected}
        files.update(expected)
    for base,pattern in [('footprints','*.kicad_mod'),('symbols','*.kicad_sym'),('scripts/schgen/fixtures','fixture.kicad_sym')]:
        for path in (recovery/base).rglob(pattern):files[str(path.relative_to(recovery))]=digest(path)
    # Complete preflight before creating disposable state.
    if any(digest(recovery/name)!=want for name,want in files.items()):raise ValueError('preserved source hash mismatch')
    for name,want in files.items():
        target=cache/'input'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(recovery/name,target)
        if digest(target)!=want or digest(recovery/name)!=want:raise ValueError('source changed while copied')
    write_json(cache/'manifest.json',{'proposal_sha256':digest(PROPOSAL),'source_files':spec['source_files'],
        'boards':board_inputs,'input_sha256':files,'status':'UNSELECTED isolated native experiment; no electrical receipt reuse'})
    write_json(cache/'compiled-proposal.json',compiled)
    print('Prepared exact ignored native inputs:',cache,flush=True)


def verify_inputs(cache,manifest):
    if digest(PROPOSAL)!=manifest['proposal_sha256']:raise ValueError('proposal changed after preparation')
    for name,want in manifest['source_files'].items():
        if digest(ROOT/name)!=want:raise ValueError('source epoch changed after preparation')
    for name,want in manifest['input_sha256'].items():
        if digest(cache/'input'/name)!=want:raise ValueError('retained copied input changed')


def added_ids(board):
    key=board['board_key'];bid=board['board_id']
    ids={'collar_zone':stable_uuid(bid,'foil-collar',key+':solid')}
    if board['board_access']['kind']=='proposed_new_via_and_dogleg':
        ids['via']=board['board_access']['proposal_via_uuid']
        ids['tracks']=[stable_uuid(bid,'foil-collar',key+':dogleg:'+str(i)) for i in range(len(board['board_access']['track_points_native_mm'])-1)]
    return ids


def island_polygon(shape):
    """One connected source polygon includes the entire unchanged pad land."""
    pad=shape['nominal_pad_bbox_mm'];shoulder=shape['shoulder_polygon_mm'];neck=shape['collar_polygon_mm'];flare=shape['board_flare_polygon_mm']
    direction=shape['outer_normal_native_xyz'][1]
    back=pad[1] if direction>0 else pad[3]
    return [[pad[0],back],[pad[2],back],shoulder[1],shoulder[2],neck[2],flare[2],flare[3],neck[3],shoulder[3],shoulder[0]]


def restore_unchanged(source,serialized,retired,added,changed_zones):
    """KiCad owns new/changed copper; every other original block stays exact."""
    old=blocks(source);new=blocks(serialized)
    allowed={'segment':set(added.get('tracks',[])),'via':{added['via']} if 'via' in added else set(),'arc':set()}
    for kind in ('segment','via','arc'):
        wanted=set(old[kind])-retired|allowed[kind]
        if set(new[kind])!=wanted:raise ValueError('unexpected native '+kind+' inventory delta')
    if set(new['zone'])!=set(old['zone'])|{added['collar_zone']}:raise ValueError('unexpected native zone inventory delta')
    if set(new['footprint'])!=set(old['footprint']):raise ValueError('native footprint inventory changed')
    # Build from the source text, transplanting only explicitly owned changes.
    source_text=source.read_text();edits=[]
    for start,end in top_level_spans(source_text):
        block=source_text[start:end];match=UUID_RE.search(block)
        if not match:continue
        uid=match[1];kind=re.match(r'\(([A-Za-z0-9_]+)',block)[1]
        if kind in ('segment','via','arc') and uid in retired:edits.append((start,end,''))
        elif kind=='zone' and uid in changed_zones:edits.append((start,end,new['zone'][uid]))
    text=replace_spans(source_text,edits)
    appended=[new['zone'][added['collar_zone']]]
    for kind,ids in allowed.items():appended.extend(new[kind][uid] for uid in sorted(ids))
    closing=text.rfind(')');text=text[:closing]+'\n'+'\n'.join(appended)+'\n'+text[closing:]
    serialized.write_text(text)
    after=blocks(serialized)
    if old['footprint']!=after['footprint']:raise ValueError('full footprint/pad blocks not byte-preserved')
    for kind in ('segment','via','arc'):
        if set(after[kind])!=set(old[kind])-retired|allowed[kind]:raise ValueError('restored native copper inventory differs')
        if any(after[kind].get(k)!=v for k,v in old[kind].items() if k not in retired):raise ValueError('unowned explicit copper changed')
    if any(after['zone'][k]!=new['zone'][k] for k in changed_zones):raise ValueError('source zone set difference was not transplanted')
    return {'byte_preserved_footprints':len(old['footprint']),'byte_preserved_unretired_explicit_copper':sum(len(old[k])-len(set(old[k])&retired) for k in ('segment','via','arc')),
            'retired_uuids':sorted(retired),'added':added,'changed_zone_uuids':sorted(changed_zones)}


def check_named_connectivity(before,after):
    if before['native_open_edges_by_net']!=after['native_open_edges_by_net']:
        raise ValueError('native named open-edge inventory changed')
    if before['native_unconnected_edges']!=after['native_unconnected_edges']:raise ValueError('native total open edges changed')
    if after['native_open_edges_by_net'].get('AGND',0):raise ValueError('AGND has native open edges')
    return {'unchanged_full_named_open_edges':after['native_unconnected_edges'],
            'unchanged_open_net_count':after['native_open_net_count'],'AGND_open_edges':0}


def declared_edit_windows(board,recipe,clearance):
    """Local geometric authority, derived before observing any refill delta."""
    shape=recipe['proposed_geometry'];windows=[c['subtract_window_mm'] for c in recipe['proposed_zone_clips']]
    points=island_polygon(shape)
    windows.append(inflate([min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)],clearance))
    retired={r['uuid'] for r in board['proposed_retirements']}
    for item in board['snapshot']['items']:
        if item['uuid'] in retired:windows.extend(inflate(box,clearance) for box in item['copper_bbox_mm'].values())
    access=board['board_access']
    if access['kind']=='proposed_new_via_and_dogleg':
        x,y=access['via_centre_native_mm'];r=access['via_diameter_mm']/2
        windows.append(inflate([x-r,y-r,x+r,y+r],clearance))
        for a,b in zip(access['track_points_native_mm'],access['track_points_native_mm'][1:]):
            windows.append(inflate([min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])],access['track_width_mm']/2+clearance))
    return windows


def native_partition(board,excluded):
    """Complete named physical connectivity, independent of zone parent UUIDs."""
    import pcbnew
    conn=board.GetConnectivity();conn.RecalculateRatsnest();seen=set();groups=collections.defaultdict(list)
    for seed in [p for fp in board.GetFootprints() for p in fp.Pads()]+list(board.GetTracks()):
        uid=seed.m_Uuid.AsString()
        if seed.GetNetCode()<=0 or uid in seen:continue
        members={i.m_Uuid.AsString() for i in conn.GetConnectedItems(seed) if i.Type()!=pcbnew.PCB_ZONE_T}|{uid}
        seen.update(members);retained=sorted(members-excluded)
        if retained:groups[seed.GetNetname()].append(retained)
    return {net:sorted(parts) for net,parts in sorted(groups.items())}


def displacement_diagnostic(old_fill,new_fill,allowed):
    """Native bidirectional set-offset measurement, never an admission limit."""
    import pcbnew
    removed=pcbnew.SHAPE_POLY_SET(old_fill);removed.BooleanSubtract(new_fill);removed.BooleanSubtract(allowed)
    added=pcbnew.SHAPE_POLY_SET(new_fill);added.BooleanSubtract(old_fill);added.BooleanSubtract(allowed)
    def covered(nm):
        for difference,reference in ((removed,new_fill),(added,old_fill)):
            if difference.Area()==0:continue
            offset=pcbnew.SHAPE_POLY_SET(reference)
            offset.Inflate(nm,pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,100)
            remainder=pcbnew.SHAPE_POLY_SET(difference);remainder.BooleanSubtract(offset)
            if remainder.Area()!=0:return False
        return True
    low=0;high=1000
    while not covered(high):
        low=high;high*=2
        if high>1000000:return {'status':'exceeds 1 mm diagnostic search range; no tolerance admitted'}
    while high-low>1000:
        middle=((high+low)//2000)*1000
        if covered(middle):high=middle
        else:low=middle
    return {'largest_failed_offset_mm':low/1e6,'smallest_tested_covering_offset_mm':high/1e6,
        'offset_polygon_max_error_mm':.0001,'search_resolution_mm':.001,
        'scope':'Bidirectional material-set displacement outside declared windows, using native rounded offsets. Measures changed boundaries/filled gaps; not an exact Hausdorff certificate, physical tolerance, or passing admission threshold.'}


def run_board(cache,key):
    import pcbnew
    from scripts.pcbgen.extract_power_geometry import extract,contours
    from scripts.pcbgen.ratsnest import inspect
    if pcbnew.GetBuildVersion()!='10.0.6':raise ValueError('exact pinned KiCad 10.0.6 required')
    constructor_hash=digest(Path(__file__))
    cache=require_cache(cache);manifest=json.loads((cache/'manifest.json').read_bytes());verify_inputs(cache,manifest)
    spec=json.loads(PROPOSAL.read_bytes());compiled=compile_proposal(spec)
    b=next(b for b in spec['boards'] if b['board_key']==key);recipe=next(r for r in compiled['boards'] if r['board_key']==key)
    source=cache/'input'/b['native_board_path'];directory=cache/key
    if directory.exists():raise ValueError('fresh per-board candidate directory required')
    directory.mkdir();candidate=cache/'candidate'/b['native_board_path'];candidate.parent.mkdir(parents=True,exist_ok=True)
    if candidate.exists():raise ValueError('candidate board already exists')
    # Preserve the original relative project/library/schematic hierarchy.
    for name,want in manifest['input_sha256'].items():
        relative=Path(name)
        if (relative.suffix in ('.kicad_pro','.kicad_sch','.kicad_dru','.kicad_mod','.kicad_sym')
                or relative.name in ('fp-lib-table','sym-lib-table')):
            destination=cache/'candidate'/relative;destination.parent.mkdir(parents=True,exist_ok=True)
            if destination.exists() and digest(destination)!=want:raise ValueError('candidate support file differs from retained authority')
            if not destination.exists():shutil.copyfile(cache/'input'/relative,destination)
    companion_hashes={}
    for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
        target=candidate.with_suffix(suffix);shutil.copyfile(source.with_suffix(suffix),target);companion_hashes[str(target.relative_to(ROOT))]=digest(target)
    board=pcbnew.LoadBoard(str(source));board.SetFileName(str(candidate))
    vec=lambda p:pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in p))
    def polygon(points):
        poly=pcbnew.SHAPE_POLY_SET();index=poly.NewOutline()
        for p in points:poly.Append(vec(p),index)
        return poly
    def rectangle(box):return polygon([[box[0],box[1]],[box[2],box[1]],[box[2],box[3]],[box[0],box[3]]])
    tracks={i.m_Uuid.AsString():i for i in board.GetTracks()};retired={r['uuid'] for r in b['proposed_retirements']}
    for uid in retired:board.Remove(tracks[uid])
    zones={z.m_Uuid.AsString():z for z in board.Zones()};changed=set()
    for clip in recipe['proposed_zone_clips']:
        uid=clip['zone_uuid'];zone=zones[uid]
        if zone.GetNetname()!=clip['net'] or board.GetLayerName(zone.GetLayer())!=clip['layer']:raise ValueError('zone identity/net/layer differs')
        zone.Outline().BooleanSubtract(rectangle(clip['subtract_window_mm']))
        changed.add(uid)
    ids=added_ids(b);net=board.FindNet('AGND');face=board.GetLayerID(b['face'])
    zone=pcbnew.ZONE(board);zone.SetUuid(pcbnew.KIID(ids['collar_zone']));zone.SetZoneName('UNSELECTED foil collar '+key)
    zone.SetLayer(face);zone.SetNet(net);zone.SetLocalClearance(pcbnew.FromMM(spec['geometry']['copper_isolation_clearance_mm']))
    native_minimum=max(z.GetMinThickness() for z in zones.values() if z.IsOnLayer(face) and not z.GetIsRuleArea())
    zone.SetMinThickness(native_minimum);zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    outline=zone.Outline();index=outline.NewOutline()
    for p in island_polygon(recipe['proposed_geometry']):outline.Append(vec(p),index)
    board.Add(zone)
    access=b['board_access']
    if 'via' in ids:
        via=pcbnew.PCB_VIA(board);via.SetUuid(pcbnew.KIID(ids['via']));via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetPosition(vec(access['via_centre_native_mm']))
        via.SetWidth(pcbnew.FromMM(access['via_diameter_mm']));via.SetDrill(pcbnew.FromMM(access['via_drill_mm']));via.SetNet(net);board.Add(via)
        for uid,a,z in zip(ids['tracks'],access['track_points_native_mm'],access['track_points_native_mm'][1:]):
            track=pcbnew.PCB_TRACK(board);track.SetUuid(pcbnew.KIID(uid));track.SetLayer(face);track.SetStart(vec(a));track.SetEnd(vec(z))
            track.SetWidth(pcbnew.FromMM(access['track_width_mm']));track.SetNet(net);board.Add(track)
    print(key,'refilling isolated native candidate',flush=True)
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):raise ValueError('native refill failed')
    pcbnew.SaveBoard(str(candidate),board)
    # SaveBoard rewrites project metadata. Restore the independently retained
    # project before any parity/geometry check; do not bless rewritten bytes.
    for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru'):
        shutil.copyfile(source.with_suffix(suffix),candidate.with_suffix(suffix))
    preservation=restore_unchanged(source,candidate,retired,ids,changed)
    write_json(directory/'preservation.json',preservation)
    if 'via' in ids:
        native_blocks=blocks(candidate)
        setup=next(block for block in native_blocks['non_copper'] if block.startswith('(setup'))
        if not re.search(r'\(tenting\s+\(front yes\)\s+\(back yes\)\s*\)',setup) or '(tenting' in native_blocks['via'][ids['via']]:
            raise ValueError('new via must inherit retained front/back tenting without an override')
    # Reopened bytes, not an in-memory pre-save object, are the audit authority.
    board=pcbnew.LoadBoard(str(candidate));conn=board.GetConnectivity();conn.RecalculateRatsnest()
    original_board=pcbnew.LoadBoard(str(source))
    original_zones={z.m_Uuid.AsString():z for z in original_board.Zones()}
    candidate_zones={z.m_Uuid.AsString():z for z in board.Zones()}
    definition_data=json.loads((cache/'input'/manifest['boards'][key]['definition']).read_bytes())
    local_clearance=max([spec['geometry']['copper_isolation_clearance_mm']]+[r['clearance_mm'] for r in definition_data['routing']['net_classes']]+[r['clearance_mm'] for r in definition_data['routing']['zones']])
    windows=declared_edit_windows(b,recipe,local_clearance);allowed=pcbnew.SHAPE_POLY_SET()
    for window in windows:allowed.BooleanAdd(rectangle(window))
    deltas=[];outside_polygons=[]
    for uid,old_zone in original_zones.items():
        if old_zone.GetIsRuleArea():continue
        new_zone=candidate_zones[uid]
        for layer_name in b['snapshot']['enabled_copper_layers']:
            layer=board.GetLayerID(layer_name)
            if not old_zone.IsOnLayer(layer):continue
            old_fill=pcbnew.SHAPE_POLY_SET(old_zone.GetFilledPolysList(layer));new_fill=pcbnew.SHAPE_POLY_SET(new_zone.GetFilledPolysList(layer))
            removed=pcbnew.SHAPE_POLY_SET(old_fill);removed.BooleanSubtract(new_fill)
            added=pcbnew.SHAPE_POLY_SET(new_fill);added.BooleanSubtract(old_fill)
            delta=pcbnew.SHAPE_POLY_SET(removed);delta.BooleanAdd(added);delta.BooleanSubtract(allowed)
            outside=delta.Area()/1e12
            if outside>1e-8:
                print(f'FAILED local-only gate: {uid} {layer_name} {outside} mm2 outside declared region',flush=True)
                outside_polygons.append({'zone_uuid':uid,'layer':layer_name,'contours':contours(delta)})
                displacement=displacement_diagnostic(old_fill,new_fill,allowed)
            else:displacement={'status':'no outside area above 1e-8 mm2 audit threshold'}
            topology=[]
            for filled in (old_fill,new_fill):
                p=pcbnew.SHAPE_POLY_SET(filled);p.Unfracture()
                topology.append({'components':p.OutlineCount(),'holes':sum(p.HoleCount(i) for i in range(p.OutlineCount()))})
            deltas.append({'zone_uuid':uid,'layer':layer_name,'removed_area_mm2':removed.Area()/1e12,'added_area_mm2':added.Area()/1e12,'outside_declared_area_mm2':outside,
                'filled_topology_before':topology[0],'filled_topology_after':topology[1]})
            deltas[-1]['boundary_displacement_diagnostic']=displacement
    collar_fill=pcbnew.SHAPE_POLY_SET(candidate_zones[ids['collar_zone']].GetFilledPolysList(face))
    source_island=polygon(island_polygon(recipe['proposed_geometry']))
    new_fill=pcbnew.SHAPE_POLY_SET(collar_fill);new_fill.BooleanSubtract(source_island)
    collar_excess=new_fill.Area()/1e12
    overshoot={'area_mm2':collar_excess}
    if collar_excess>1e-8:
        print('FAILED source-polygon gate: new collar excess',collar_excess,'mm2',flush=True)
        outside_polygons.append({'zone_uuid':ids['collar_zone'],'layer':b['face'],'account':'new collar outside source polygon','contours':contours(new_fill)})
        overshoot['outward_displacement_diagnostic']=displacement_diagnostic(source_island,collar_fill,source_island)
        points=[p for contour in contours(new_fill) for p in contour['shell']]
        overshoot['bbox_mm']=[min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
    shape=recipe['proposed_geometry'];cx=shape['neck_centre_x_mm'];half=spec['geometry']['nominal_neck_width_mm']/2
    lo,hi=sorted([shape['inner_cut_nominal_y_mm'],shape['outer_cut_nominal_y_mm']])
    over_dry=pcbnew.SHAPE_POLY_SET(new_fill);over_dry.BooleanIntersection(rectangle([cx-half-.25,lo,cx+half+.25,hi]))
    overshoot['intersection_with_full_dry_guard_mm2']=over_dry.Area()/1e12
    delta_receipt={'declaration_basis':'Source clip windows, complete source island/access, exact retired copper envelopes and maximum retained native clearance; fixed before evaluating deltas',
        'clearance_halo_mm':local_clearance,'declared_windows_mm':windows,'filled_copper_deltas':deltas,'new_collar_outside_source_polygon_mm2':new_fill.Area()/1e12,
        'local_only_delta_gate_pass':all(r['outside_declared_area_mm2']<=1e-8 for r in deltas),
        'source_polygon_gate_pass':collar_excess<=1e-8}
    delta_receipt['collar_overshoot']=overshoot
    write_json(directory/'outside-region-polygons.json',outside_polygons)
    write_json(directory/'filled-copper-delta.json',delta_receipt)
    excluded=retired|set(ids.get('tracks',[]))|({ids['via']} if 'via' in ids else set())
    old_partition=native_partition(original_board,excluded);new_partition=native_partition(board,excluded)
    write_json(directory/'before-connectivity-partition.json',old_partition);write_json(directory/'after-connectivity-partition.json',new_partition)
    partition_unchanged=old_partition==new_partition
    pads=[p for fp in board.GetFootprints() for p in fp.Pads()];selected=next(p for p in pads if p.m_Uuid.AsString()==b['pad_uuid'])
    members={i.m_Uuid.AsString() for i in conn.GetConnectedItems(selected)}|{b['pad_uuid']}
    old_geometry=json.loads((cache/'input'/b['native_geometry_path']).read_bytes())
    required=set(old_geometry['main_rail_members']['AGND'])-retired
    missing_ground=sorted(required-members)
    paid_via_connected='via' not in ids or ids['via'] in members
    # Filled copper in the full collar interior must equal one single-foil neck.
    shape=recipe['proposed_geometry'];cx=shape['neck_centre_x_mm'];half=spec['geometry']['nominal_neck_width_mm']/2
    lo,hi=sorted([shape['inner_cut_nominal_y_mm'],shape['outer_cut_nominal_y_mm']]);trim=0.0
    section=[cx-half,lo+trim,cx+half,hi-trim];guard=[cx-half-.25,lo+trim,cx+half+.25,hi-trim]
    mask_layer=pcbnew.F_Mask if face==pcbnew.F_Cu else pcbnew.B_Mask
    graphics=list(board.GetDrawings())+[g for fp in board.GetFootprints() for g in fp.GraphicalItems()]
    for graphic in graphics:
        if graphic.GetLayer()!=mask_layer:continue
        box=graphic.GetBoundingBox()
        if not (box.GetRight()<pcbnew.FromMM(section[0]) or box.GetLeft()>pcbnew.FromMM(section[2])
                or box.GetBottom()<pcbnew.FromMM(section[1]) or box.GetTop()>pcbnew.FromMM(section[3])):
            raise ValueError('native mask graphic overlaps the dry collar')
    target=rectangle(section);window=rectangle(guard);isolation=[];section_gate=True
    for layer_name in b['snapshot']['enabled_copper_layers']:
        layer=board.GetLayerID(layer_name);union=pcbnew.SHAPE_POLY_SET()
        for z in board.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(layer):continue
            filled=pcbnew.SHAPE_POLY_SET(z.GetFilledPolysList(layer));filled.BooleanIntersection(window)
            union.BooleanAdd(filled)
        for item in pads+list(board.GetTracks()):
            if not item.IsOnLayer(layer):continue
            box=item.GetBoundingBox()
            if (box.GetRight()<pcbnew.FromMM(guard[0]) or box.GetLeft()>pcbnew.FromMM(guard[2])
                    or box.GetBottom()<pcbnew.FromMM(guard[1]) or box.GetTop()>pcbnew.FromMM(guard[3])):continue
            poly=pcbnew.SHAPE_POLY_SET();item.TransformShapeToPolygon(poly,layer,0,pcbnew.FromMM(.000001),pcbnew.ERROR_OUTSIDE)
            poly.BooleanIntersection(window);union.BooleanAdd(poly)
        actual_area=union.Area()/1e12
        missing_area=excess_area=0.0
        if layer==face:
            missing=pcbnew.SHAPE_POLY_SET(target);missing.BooleanSubtract(union)
            excess=pcbnew.SHAPE_POLY_SET(union);excess.BooleanSubtract(target)
            missing_area=missing.Area()/1e12;excess_area=excess.Area()/1e12
            section_gate=section_gate and missing_area<=1e-8 and excess_area<=1e-8
        elif actual_area>1e-8:section_gate=False
        isolation.append({'layer':layer_name,'filled_guard_area_mm2':actual_area,'guard_rectangle_mm':guard,
            'same_face_missing_area_mm2':missing_area,'same_face_excess_area_mm2':excess_area})
    isolation_receipt={'interior_trim_each_end_mm':trim,'full_nominal_collar_mm':[lo,hi],
        'checked_full_width_interior_mm':section,'native_zone_minimum_thickness_mm':pcbnew.ToMM(native_minimum),
        'note':'Exact nominal filled section only; manufactured full-section geometry/material metric remains OPEN',
        'layers':isolation,'full_nominal_section_gate_pass':section_gate,
        'prior_AGND_member_count':len(required),'missing_prior_AGND_members':missing_ground,'paid_via_connected':paid_via_connected}
    write_json(directory/'collar-isolation.json',isolation_receipt)
    before=inspect(source);after=inspect(candidate);write_json(directory/'before-ratsnest.json',before);write_json(directory/'after-ratsnest.json',after)
    try:connectivity=check_named_connectivity(before,after)|{'gate_pass':True}
    except ValueError as error:connectivity={'gate_pass':False,'failure':str(error)}
    drcs={}
    for label,path in [('before',source),('after',candidate)]:
        out=directory/(label+'-drc.json')
        subprocess.run(['kicad-cli','pcb','drc','--schematic-parity','--format','json','--severity-all','-o',str(out),str(path)],check=True)
        data=json.loads(out.read_bytes());drcs[label]=data
        if data['kicad_version']!='10.0.6':raise ValueError('unexpected native DRC oracle')
    errors=[v for v in drcs['after']['violations'] if v['severity']=='error']
    definition=cache/'input'/manifest['boards'][key]['definition']
    extract(b['board_id'],candidate,directory/'native-geometry.json',definition)
    if any(digest(ROOT/name)!=want for name,want in companion_hashes.items()):raise ValueError('native companion changed during checks')
    verify_inputs(cache,manifest)
    if digest(Path(__file__))!=constructor_hash:raise ValueError('constructor source changed during native execution')
    native_gate=(not errors and not drcs['after']['schematic_parity'] and delta_receipt['local_only_delta_gate_pass'] and delta_receipt['source_polygon_gate_pass']
        and partition_unchanged and not missing_ground and paid_via_connected and section_gate and connectivity['gate_pass'])
    report={'status':('UNSELECTED native checks pass; no electrical or physical admission' if native_gate else 'REJECTED native admission; full failed-gate diagnostics retained'),
        'native_admission_gate_pass':native_gate,'board_key':key,'kicad_version':pcbnew.GetBuildVersion(),
        'proposal_sha256':manifest['proposal_sha256'],'constructor_sha256':constructor_hash,
        'source_board_sha256':b['native_board_sha256'],'candidate_board_sha256':digest(candidate),'companion_sha256':companion_hashes,
        'preservation':preservation,'isolation':isolation_receipt,'connectivity':connectivity,
        'filled_copper_delta':delta_receipt,
        'unchanged_existing_physical_connectivity_partition':partition_unchanged,
        'nominal_full_trace':recipe['full_trace'],
        'native_mask_rule':'Unchanged hash-bound pad openings and tolerances; no mask graphic crosses dry section; new copper is on Cu only; any new via inherits retained two-face tenting. Physical mask seal remains OPEN.',
        'native_rule_errors':len(errors),'schematic_parity_issues':len(drcs['after']['schematic_parity']),
        'warning_types_before':dict(collections.Counter(v['type'] for v in drcs['before']['violations'] if v['severity']=='warning')),
        'warning_types_after':dict(collections.Counter(v['type'] for v in drcs['after']['violations'] if v['severity']=='warning')),
        'reported_warning_records_unchanged':sorted(json.dumps(v,sort_keys=True) for v in drcs['before']['violations'] if v['severity']=='warning')==sorted(json.dumps(v,sort_keys=True) for v in drcs['after']['violations'] if v['severity']=='warning'),
        'artifacts_sha256':{str(p.relative_to(ROOT)):digest(p) for p in directory.iterdir() if p.is_file()},
        'open':'Fixture isolation/remating/process, manufactured material/geometry metric, PCB access energy and joined network acceptance remain OPEN. Historical electrical receipts are not reused.'}
    write_json(directory/'native-receipt.json',report)
    print(key,'native rules',len(errors),'parity',report['schematic_parity_issues'],'open edges',after['native_unconnected_edges'],flush=True)
    if not native_gate:raise ValueError('native admission gate failed; full diagnostics retained, no admission')


def main():
    p=argparse.ArgumentParser();p.add_argument('--prepare',type=Path);p.add_argument('--cache',type=Path,required=True);p.add_argument('--run-board',choices=['JL','K'])
    a=p.parse_args()
    if bool(a.prepare)==bool(a.run_board):p.error('choose exactly one of --prepare or --run-board')
    if a.prepare:prepare(a.prepare,a.cache)
    else:run_board(a.cache,a.run_board)

if __name__=='__main__':main()
