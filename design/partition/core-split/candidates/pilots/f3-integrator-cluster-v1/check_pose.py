#!/usr/bin/env python3
"""Check the one sealed F3 pose and account copper; no optimizer, router or native."""
import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import time
from collections import Counter, defaultdict

import shapely
from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union, nearest_points
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[6]
HERE = Path(__file__).resolve().parent
EPOCH_SHA = '008cb8e318005bb8db36a75cf3ea321ef45de473a878697c0c3241fe8b96a47f'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def transform_xy(xy, old, new, scale=1):
    """Exact quarter turns on serialized nm or mm; same-face only."""
    require(old['side'] == new['side'], 'face changes forbidden')
    angle = (old['kicad_orientation_deg'] - new['kicad_orientation_deg']) % 360
    require(angle in (0, 90, 180, 270), 'only exact quarter turns supported')
    ox, oy = [round(old[k]*scale) if scale != 1 else old[k] for k in ('x_mm', 'y_mm')]
    nx, ny = [round(new[k]*scale) if scale != 1 else new[k] for k in ('x_mm', 'y_mm')]
    x, y = xy[0]-ox, xy[1]-oy
    x, y = {0:(x,y), 90:(-y,x), 180:(-x,-y), 270:(y,-x)}[angle]
    return [x+nx, y+ny]


def transform_pad(pad, old, new):
    result = copy.deepcopy(pad)
    result['xy'] = transform_xy(pad['xy'], old, new, 1_000_000)
    result['poly'] = [transform_xy(xy, old, new, 1_000_000) for xy in pad['poly']]
    return result


def shape(placement, pose=None):
    polygons = [[(x+100, y+50) for x,y in poly] for poly in placement['courtyard_polygons_mm']]
    if pose:
        polygons = [[transform_xy(xy, pose['old_physical_pose'], pose['candidate_physical_pose']) for xy in poly] for poly in polygons]
    result = unary_union([Polygon(poly) for poly in polygons])
    require(not result.is_empty and result.is_valid, 'invalid courtyard')
    return result


def closure(board, seeds):
    result = set(seeds)
    while True:
        before = result.copy()
        for group in board['sensitive_nets']:
            if result.intersection(group['refs']):
                result.update(group['refs'])
        for part in board['source_parts']:
            if part['decouples_ref'] in result:
                result.add(part['ref'])
        if before == result:
            return sorted(result)


def placement_checks(board, poses, partition):
    by_ref = {p['ref']:p for p in board['placements']}
    old = {r:shape(p) for r,p in by_ref.items()}
    new = {r:shape(p, poses.get(r)) for r,p in by_ref.items()}
    moved = {r for r,p in poses.items() if p['moved']}
    rows = []
    for r in sorted(moved):
        for s in sorted(by_ref):
            if r == s or (s in moved and s < r) or by_ref[r]['side'] != by_ref[s]['side']:
                continue
            distance = new[r].distance(new[s])
            overlap = new[r].intersection(new[s]).area
            if distance < .35-1e-7 or overlap > 1e-7:
                rows.append({'refs':[r,s], 'distance_mm':distance, 'required_mm':.35,
                             'overlap_mm2':overlap, 'old_distance_mm':old[r].distance(old[s]),
                             'neighbor_outside_closure':s not in poses})
    outline = affinity.translate(Polygon(board['outline_mm']), 100, 50).buffer(-.30, join_style=2)
    edges = [{'ref':r, 'outside_mm2':new[r].difference(outline).area}
             for r in sorted(moved) if not outline.covers(new[r])]
    reservations = []
    for r in sorted(moved):
        face = by_ref[r]['side']
        for reserve in board['measurement']['faces'][face]['reservation_polygons_mm']:
            g = unary_union([Polygon([(x+100,y+50) for x,y in poly]) for poly in reserve['polygons']])
            area = new[r].intersection(g).area
            if area > 1e-7:
                reservations.append({'ref':r, 'reservation':reserve['id'], 'overlap_mm2':area,
                    'old_same_ref_overlap_mm2':old[r].intersection(g).area,
                    'old_all_closure_overlap_mm2':unary_union([old[s] for s in poses if by_ref[s]['side']==face]).intersection(g).area,
                    'candidate_polygon_mm':[list(new[r].exterior.coords)],
                    'reservation_polygons_mm':[[(x+100,y+50) for x,y in poly] for poly in reserve['polygons']],
                    'method':'Exact polygon intersection; retained 128-edge circle reservations are polygon approximations, not native fit'})
    # Analytic circle distances avoid relying on the polygon approximation for holes.
    holes = []
    for r in sorted(moved):
        for aperture in partition['K_service_apertures']:
            center = Point(aperture['center_mm'][0]+100, aperture['center_mm'][1]+50)
            radius = aperture['diameter_mm']/2
            margin = new[r].distance(center)-radius
            if margin < -1e-7:
                holes.append({'ref':r, 'header_id':aperture['header_id'], 'center_mm':list(center.coords)[0],
                              'radius_mm':radius, 'courtyard_to_hole_margin_mm':margin,
                              'old_margin_mm':old[r].distance(center)-radius})
    return {'moved_ref_count':len(moved), 'same_face_gap_violations':rows,
            'edge_allocation_violations':edges, 'reservation_conflicts':reservations,
            'analytic_service_hole_conflicts':holes,
            'pass':not(rows or edges or reservations or holes),
            'scope':'All moved courtyards against all same-face candidate placements and all frozen reservations; inherited reservation occupancy is reported, not waived.'}


def scalar(block, tag):
    found = re.search(r'\('+re.escape(tag)+r'\s+([^()]+)\)', block)
    require(found is not None, 'missing copper field '+tag)
    return found.group(1).strip().strip('"')


def copper_accounting(board, original, pads, moved, index, pcb_text):
    """All accepted segments/vias, not just the reduced candidate fixture."""
    rows, geometry, radii, layers = [], [], [], []
    for record in index:
        a,b = record['source_span']; block = pcb_text[a:b]
        require(digest(block.encode()) == record['sha256'], 'accepted copper object changed '+record['uuid'])
        if record['kind'] == 'segment':
            g = LineString([list(map(float,scalar(block,t).split())) for t in ('start','end')])
            radius = float(scalar(block,'width'))/2
            face = [scalar(block,'layer')]
        elif record['kind'] == 'via':
            g = Point(list(map(float,scalar(block,'at').split())))
            radius = float(scalar(block,'size'))/2
            require(scalar(block,'layers') == 'F.Cu" "B.Cu', 'unexpected blind/buried via')
            face = original['layers']
        else:
            require(record['kind'] in ('zone','rule_area'), 'unsupported original copper kind')
            continue
        rows.append(record); geometry.append(g); radii.append(radius); layers.append(face)
    tree = STRtree(geometry); radius_max = max(radii)
    original_pads = {p['uuid']:p for p in original['pads']}
    fixture_ids = {r['uuid'] for k in ('tracks','vias') for r in original[k]}
    contacts, collisions = [], []
    touched = set()
    for pad in pads:
        if pad['ref'] not in moved:
            continue
        for phase, target in [('old',original_pads[pad['uuid']]),('candidate',pad)]:
            poly = Polygon([(x/1e6,y/1e6) for x,y in target['poly']])
            x0,y0,x1,y1 = poly.bounds; margin = radius_max+.25
            for j in tree.query(box(x0-margin,y0-margin,x1+margin,y1+margin)):
                j=int(j); row=rows[j]
                if not set(target['layers']).intersection(layers[j]):
                    continue
                gap = poly.distance(geometry[j])-radii[j]
                if phase=='old' and row['net_token']==pad['net'] and gap<=1e-7:
                    touched.add(row['uuid'])
                    contacts.append({'pad_uuid':pad['uuid'],'ref':pad['ref'],'pad':pad['pad'],
                                     'copper_uuid':row['uuid'],'gap_mm':gap})
                if phase=='candidate' and row['net_token']!=pad['net'] and gap<.25-1e-7:
                    touched.add(row['uuid'])
                    collisions.append({'pad_uuid':pad['uuid'],'ref':pad['ref'],'pad':pad['pad'],'net':pad['net'],
                         'copper_uuid':row['uuid'],'copper_net':row['net_token'],'gap_mm':gap,
                         'required_clearance_mm':.25,'present_in_original_candidate_fixture':row['uuid'] in fixture_ids})
    moved_nets = {p['net'] for p in pads if p['ref'] in moved}
    obligation_nets = moved_nets | {r['copper_net'] for r in collisions}
    groups=defaultdict(list)
    for row in index:
        if row['net_token'] in obligation_nets:
            groups[row['net_token']].append(row)
    net_obligations=[]
    for net, records in sorted(groups.items()):
        net_obligations.append({'net':net,'reason':'MOVED_ENDPOINT_NET' if net in moved_nets else 'NEW_PAD_FOREIGN_COLLISION',
            'object_count':len(records),'kinds':dict(Counter(r['kind'] for r in records)),
            'uuid_sha256_pairs_digest':digest(canonical(sorted([r['uuid'],r['sha256']] for r in records))),
            'selector':'All records with this net_token in the sealed original copper-index.jsonl.gz; recheck obligation, NOT deletion authorization'})
    bp = next(p['net'] for p in pads if p['ref']=='C2312' and p['pad']=='1')
    bp_a = next(p['uuid'] for p in pads if p['ref']=='C2312' and p['pad']=='1')
    bp_b = next(p['uuid'] for p in pads if p['ref']=='U2312' and p['pad']=='12')
    group = next(g for g in original['islands'][bp] if bp_a in g)
    require(bp_b in group, 'lost original BP_INT connected-group evidence')
    summary={'accepted_index_objects':len(index),'all_index_object_hashes_verified':True,
        'accepted_segments_vias_checked':len(rows),'original_fixture_segments_vias':len(fixture_ids),
        'moved_pad_old_same_net_contacts':contacts,'candidate_pad_foreign_copper_conflicts':collisions,
        'direct_impact_objects':[r for r in index if r['uuid'] in touched],
        'net_recheck_obligations':net_obligations,
        'bp_int':{'net':bp,'original_pair':['C2312.1','U2312.12'],'original_group_members':group,
                  'accepted_copper_objects':groups[bp],
                  'disposition':'Existing connected copper cannot simply follow both changed pads; exact objects retained, replay/continuity unresolved. No automatic invalidation or cut.'},
        'zone_obligations':[r for r in index if r['kind']=='zone'],
        'all_actual_copper_preserved':True,'removed_uuids':[],'added_uuids':[],
        'geometry_scope':'Source pad/straight segment/circular via distances; existing zones require later refill and native original-group checks. Not full-chain validation or native DRC.',
        'disposition':'Every accepted object remains byte-identical. Direct impacts and complete net selectors identify replay/recheck obligations only; no wholesale discard.'}
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dump',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args(); started=time.monotonic()
    epoch_path=HERE/'pose-epoch.json'
    require(digest(epoch_path.read_bytes())==EPOCH_SHA,'pose epoch changed; no alternate pose allowed')
    epoch=read(epoch_path)
    require(shapely.__version__=='2.1.2' and shapely.geos_version_string=='3.13.1','geometry runtime drift')
    for name,h in epoch['input_sha256'].items():
        require(digest((ROOT/name).read_bytes())==h,'input drift '+name)
    require(digest(args.input_dump.read_bytes())==epoch['original_dump_sha256'],'original dump drift')
    require(not args.output.exists(),'fresh evidence directory required; never overwrite an attempt')
    board=read(ROOT/'design/partition/core-split/candidates/two.json')['boards']['two-A']
    original=read(args.input_dump); poses={p['ref']:p for p in epoch['poses']}
    require(len(poses)==24 and sorted(poses)==closure(board,{'C2312','U2306','U2312'})==epoch['closure_refs'],'incomplete closure')
    require(not poses['U2306']['moved'],'fixed U2306 anchor changed')
    require(not set(poses).intersection(board['mechanical_refs']),'mechanical scope changed')
    by_ref={p['ref']:p for p in board['placements']}
    for ref,row in poses.items():
        p=by_ref[ref]
        require(row['old_physical_pose']==dict(x_mm=p['x_mm']+100,y_mm=p['y_mm']+50,
                kicad_orientation_deg=p['kicad_orientation_deg'],side=p['side']),'old pose drift '+ref)
        require(row['moved']==(row['old_physical_pose']!=row['candidate_physical_pose']),'wrong moved flag')
    pads=[transform_pad(p,poses[p['ref']]['old_physical_pose'],poses[p['ref']]['candidate_physical_pose'])
          if p['ref'] in poses else copy.deepcopy(p) for p in original['pads']]
    moved={r for r,p in poses.items() if p['moved']}
    for p in pads:
        if p['ref'] in poses:
            identity=next(x for x in by_ref[p['ref']]['pad_identity'] if x['pad']==p['pad'])
            require((p['uuid'],p['net'])==(identity['uuid'],identity['net_token']),'pad identity changed')
    placement=placement_checks(board,poses,read(ROOT/'design/partition/partition.json'))
    index=[json.loads(x) for x in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')]
    copper=copper_accounting(board,original,pads,moved,index,(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text())
    manifest=read(ROOT/'circuit/routing/epic-242/decision-pilots/matched-demands.json')['domains']['F3']
    by_uuid={p['uuid']:p for p in pads}
    demands={k:{'source_net':v['source_net'],'net_token':v['net_token'],
                'original_anchor_records':v['anchor_records'],
                'candidate_anchor_records':[by_uuid[p['uuid']] for p in v['anchor_records']],
                'complete_geometry':'NOT RUN; candidate fit/copper obligations are prerequisite'} for k,v in manifest['targets'].items()}
    lookup={(p['ref'],p['pad']):p for p in pads}
    distances={r+'.'+n:math.dist(lookup[r,n]['xy'],lookup['U2306','5']['xy'])/1e6 for r,n in [('C2312','1'),('U2312','12')]}
    result={'status':'NO FIT FOR THIS SEALED POSE' if not placement['pass'] else 'BLOCKED BY RETAINED COPPER; NO COMPLETE GEOMETRY',
        'pose_epochs_evaluated':1,'placement_screen_pass':placement['pass'],
        'proximity_objective_mm':10,'proximity_is_owner_constraint':False,'bp_int_distances_mm':distances,
        'moved_refs':sorted(moved),'closure_refs':sorted(poses),'fixed_U2306':True,
        'native_executed':False,'adopted':False,'candidate_board_emitted':False,
        'route_searches':0,'complete_signal_return_geometry':False,'partial_paths_emitted':False,
        'whole_chain_cross_path_and_fill_checks':'NOT RUN: placement/copper prerequisite did not pass; no path success claimed',
        'rails':'Original U2309.4/+12V and U2309.11/-12V own-pad access blockers unchanged',
        'scope':'Single pose no-fit/blocked result only, not physical impossibility or necessity of changing placement',
        'elapsed_seconds':time.monotonic()-started,'peak_memory':'NOT MEASURED',
        'source_sha256':digest(Path(__file__).read_bytes()),'epoch_sha256':EPOCH_SHA,
        'input_sha256':epoch['input_sha256'],'original_dump_sha256':epoch['original_dump_sha256']}
    # Fail closed if a later historical replay unexpectedly has no blocker.
    require(not placement['pass'] or copper['candidate_pad_foreign_copper_conflicts'],
            'No justified no-fit: full combined geometry still required; do not claim completion')
    for name,h in epoch['input_sha256'].items():
        require(digest((ROOT/name).read_bytes())==h,'input mutated during check '+name)
    require(digest(args.input_dump.read_bytes())==epoch['original_dump_sha256'],'original dump mutated during check')
    args.output.mkdir(parents=True)
    for name,value in [('placement-checks.json',placement),('copper-accounting.json',copper),
                       ('demands.json',demands),('candidate-pads.json',[p for p in pads if p['ref'] in poses]),('result.json',result)]:
        (args.output/name).write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'moved_refs':result['moved_refs'],
        'gap_violations':len(placement['same_face_gap_violations']),
        'reservation_conflicts':len(placement['reservation_conflicts']),
        'analytic_hole_conflicts':len(placement['analytic_service_hole_conflicts']),
        'foreign_copper_conflicts':len(copper['candidate_pad_foreign_copper_conflicts']),
        'distances_mm':distances,'output':str(args.output),'native':False}))


if __name__=='__main__':
    main()
