"""Bounded same-ground stitching near the exact 52 J-facing K headers.

No equal sharing or ideal access is inferred. All source pads, plane spreading,
added holes and finite barrels remain in the subsequent native conductor.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shapely
from shapely.geometry import Point,Polygon
from scripts.pcbgen.propose_rail_transfers import geometry,drill_geometry
from scripts.pcbgen.uuid_tools import stable_uuid


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def plan(native_path,receipt_path,partition_path,output):
    inputs=(native_path,receipt_path,partition_path,Path(__file__),Path('scripts/pcbgen/propose_rail_transfers.py'),Path('scripts/pcbgen/uuid_tools.py'))
    contents={str(p):Path(p).read_bytes() for p in inputs}
    hashes={p:hashlib.sha256(b).hexdigest() for p,b in contents.items()}
    native=json.loads(contents[str(native_path)]);receipt=json.loads(contents[str(receipt_path)]);partition=json.loads(contents[str(partition_path)])
    if native['board_id']!='osc-core' or receipt['board_sha256']!=native['board_sha256']:
        raise ValueError('K stitch source/native identity mismatch')
    if receipt['artifacts_sha256'][str(native_path)]!=hashes[str(native_path)]:raise ValueError('K stitch native geometry changed')
    # A failed metadata/reservation trial may support geometric planning only
    # after explicitly excluding every short, clearance or hole error.
    drc_paths=[Path(p) for p in receipt['artifacts_sha256'] if p.endswith('ground-feasibility-drc.json')]
    if len(drc_paths)!=1:raise ValueError('K stitch needs one DRC artifact')
    drc_bytes=drc_paths[0].read_bytes();hashes[str(drc_paths[0])]=hashlib.sha256(drc_bytes).hexdigest()
    if hashes[str(drc_paths[0])]!=receipt['artifacts_sha256'][str(drc_paths[0])]:raise ValueError('K stitch DRC artifact changed')
    drc=json.loads(drc_bytes);main_refs={r['reference'] for r in partition['load_side_terminals'] if r['board']=='K'}
    for row in drc['violations']:
        if row['severity']!='error':continue
        if row['type']!='items_not_allowed' or not all(any((' of '+ref+' ') in i['description'] or i['description']=='Footprint '+ref for ref in main_refs) for i in row['items']):
            raise ValueError('K stitch planning source has unresolved conductor geometry errors')
    items=native['items'];by={(i['ref'],i['pad']):i for i in items if 'ref' in i}
    foreign=[geometry(c) for i in items if i['net']!='AGND' for c in i['copper'].values()]
    pads=[geometry(c) for i in items if 'ref' in i for c in i['copper'].values()]
    holes=[drill_geometry(h) for h in native['holes']]
    foreign_tree=shapely.STRtree(foreign);pad_tree=shapely.STRtree(pads);hole_tree=shapely.STRtree(holes)
    keepouts=shapely.union_all([geometry(z['contours']) for z in native['zones'] if z['keepout']])
    planes={layer:shapely.union_all([geometry(z['contours']) for z in native['zones'] if not z['keepout'] and z['net']=='AGND' and z['layer']==layer]) for layer in ('F.Cu','In1.Cu','B.Cu')}
    front=shapely.union_all([planes['F.Cu']]+[geometry(i['copper']['F.Cu']) for i in items if i['net']=='AGND' and 'F.Cu' in i['copper']])
    front_components=list(shapely.get_parts(front));outline=Polygon(native['outline_mm']).buffer(-.852)
    headers={}
    for c in partition['connectors']:
        if c['board']!='K' or not c['id'].startswith(('JL-K-','JR-K-')):continue
        headers[c['id']]=[{'ref':c['pcb_reference'],'pad':pin,'header_id':c['id'],'side':c['side']}
            for pin,net in c['pin_map'].items() if net=='AGND']
    if len(headers)!=52:raise ValueError('K stitch header inventory changed')
    accepted=[];unresolved=[]
    for header,ports in sorted(headers.items()):
        native_ports=[by[p['ref'],p['pad']] for p in ports]
        if any(p['net']!='AGND' or set(p['copper'])!={'F.Cu'} for p in native_ports):raise ValueError('K stitch source port net/face changed')
        components=[g for g in front_components if all(g.intersects(geometry(p['copper']['F.Cu'])) for p in native_ports)]
        if len(components)!=1:raise ValueError('K header ground contacts lack one actual F-sheet component')
        component=components[0];candidates={}
        for pad in native_ports:
            x,y=pad['xy_mm']
            for distance in (.8,1.1,1.5,2.,2.75,3.5):
                for angle in range(0,360,15):
                    a=math.radians(angle);xy=(round(x+distance*math.cos(a),6),round(y+distance*math.sin(a),6));point=Point(xy)
                    if xy in candidates:continue
                    if not outline.covers(point) or keepouts.intersects(point.buffer(.352)):continue
                    if any(point.distance(foreign[j])<.602 for j in foreign_tree.query(point.buffer(.602))):continue
                    if any(point.distance(pads[j])<.502 for j in pad_tree.query(point.buffer(.502))):continue
                    if any(point.distance(holes[j])<.402 for j in hole_tree.query(point.buffer(.402))):continue
                    if any(point.distance(Point(v['xy_mm']))<.552 for v in accepted):continue
                    if not component.covers(point.buffer(.352)) or not all(p.covers(point.buffer(.352)) for p in planes.values()):continue
                    candidates[xy]=[Point(p['xy_mm']).distance(point) for p in native_ports]
        chosen=[]
        for index in range(2):
            feasible=[xy for xy in candidates if all(Point(xy).distance(Point(p))>=.702 for p in chosen)]
            if not feasible:break
            def rank(xy):
                distances=candidates[xy]
                if chosen:distances=[min(d,candidates[chosen[0]][j]) for j,d in enumerate(distances)]
                return max(distances),sum(distances),xy
            xy=min(feasible,key=rank);chosen.append(xy)
        if len(chosen)!=2:
            unresolved.append({'header':header,'ports':ports,'legal_candidate_count':len(candidates)});continue
        for index,xy in enumerate(chosen):
            accepted.append({'header_id':header,'ports':[{'ref':p['ref'],'pad':p['pad'],'uuid':p['uuid'],
                'native_xy_mm':p['xy_mm'],'native_layers':list(p['copper'])} for p in native_ports],
                'uuid':stable_uuid('osc-core','ground-stitch:'+header,str(index)),'xy_mm':list(xy),
                'net':'AGND','diameter_mm':.7,'drill_mm':.3,'layers':['F.Cu','B.Cu'],
                'maximum_source_pad_distance_mm':max(candidates[xy]),
                'access':'Actual connected F-sheet copper; no added track and no zero-resistance snap. Complete plane spreading and finite barrel remain charged.'})
        print(header,'stitches',len(chosen),flush=True)
    if any(digest(p)!=h for p,h in hashes.items()):raise ValueError('K stitch input changed during planning')
    output.write_text(json.dumps({'status':'UNSELECTED bounded source stitching proposal; new native and electrical checks required',
        'source_sha256':hashes,'source_board_sha256':native['board_sha256'],'added':accepted,'unresolved':unresolved,
        'maximum_search_radius_mm':3.5,'minimum_annulus_to_any_pad_mm':.15,'clearance_mm':.25,
        'geometry_guard_mm':.002,'physical_scope':'All foreign copper, holes, native keepouts and original-grid main vias retained. Every selected stitch joins actual filled F/In1/B AGND copper. New holes invalidate earlier operator witnesses. Future #43 routing and all K own loads remain required.'},indent=2,sort_keys=True)+'\n')
    if unresolved:raise ValueError('K header stitching has unresolved source geometry')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for n in ('native','receipt','partition','output'):parser.add_argument(n,type=Path)
    a=parser.parse_args();plan(a.native,a.receipt,a.partition,a.output)
