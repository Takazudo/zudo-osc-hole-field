"""Keep only legal fixed-grid K main vias; no displaced or ideal connection."""
import argparse
import hashlib
import json
from pathlib import Path
import shapely
from shapely.geometry import Point,Polygon,box
from scripts.pcbgen.propose_rail_transfers import geometry,drill_geometry
from scripts.pcbgen.core_terminal_access import source_entries
from scripts.pcbgen.uuid_tools import stable_uuid


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def plan(native_path,receipt_path,partition_path,definition_path,output):
    inputs=(native_path,receipt_path,partition_path,definition_path,Path(__file__),
        Path('scripts/pcbgen/core_terminal_access.py'),Path('scripts/pcbgen/propose_rail_transfers.py'),Path('scripts/pcbgen/uuid_tools.py'))
    contents={str(p):Path(p).read_bytes() for p in inputs};hashes={p:hashlib.sha256(b).hexdigest() for p,b in contents.items()}
    native=json.loads(contents[str(native_path)]);receipt=json.loads(contents[str(receipt_path)])
    partition=json.loads(contents[str(partition_path)]);definition=json.loads(contents[str(definition_path)])
    source_lands=[r for r in partition['load_side_terminals'] if r['board']=='K']
    if len(source_lands)!=18:raise ValueError('K source main land inventory changed')
    own_rules={r['ref']:r for r in source_entries(definition,source_lands)}
    if native['board_id']!='osc-core' or native['board_sha256']!=receipt['board_sha256']:
        raise ValueError('K trial geometry/receipt identity mismatch')
    if receipt['artifacts_sha256'][str(native_path)]!=hashes[str(native_path)]:raise ValueError('stale K native export')
    owned={u for a in receipt['arrays'] for u in a['via_uuids']}
    items=[i for i in native['items'] if i['uuid'] not in owned]
    shapes=[geometry(c) for i in items for c in i['copper'].values()]
    owners=[i for i in items for c in i['copper'].values()];tree=shapely.STRtree(shapes)
    holes=[h for h in native['holes'] if h['uuid'] not in owned];hs=[drill_geometry(h) for h in holes];ht=shapely.STRtree(hs)
    by={h['uuid']:h for h in native['holes']};lands={l['reference']:l for l in source_lands}
    keepouts=[(z,geometry(z['contours'])) for z in native['zones'] if z['keepout'] and z['vias_forbidden']]
    outline=Polygon(native['outline_mm']);rows=[]
    for array in receipt['arrays']:
        land=lands[array['ref']];centre=[land['center_mm'][0]+100,land['center_mm'][1]+50]
        own_area=box(centre[0]-2,centre[1]-2,centre[0]+2,centre[1]+2)
        own_keepout_uuid=stable_uuid('osc-core','keepout',own_rules[array['ref']]['keepout_id']+':F.Cu')
        accepted=[];blocked=[]
        for uid in array['via_uuids']:
            h=by[uid];p=Point(h['xy_mm']);issues=[]
            if h['net']!=land['net'] or h['size_mm']!=[.3,.3]:raise ValueError('K trial array source changed')
            if not own_area.covers(p.buffer(.352)):raise ValueError('K via is not inside its finite owning land')
            if not outline.buffer(-.852).covers(p):issues.append({'type':'board-edge'})
            for j in tree.query(p.buffer(.602)):
                if owners[j]['net']!=array['net'] and p.distance(shapes[j])<.602:
                    issues.append({'type':'foreign-copper','uuid':owners[j]['uuid'],'ref':owners[j].get('ref'),
                        'pad':owners[j].get('pad'),'net':owners[j]['net'],'centre_distance_mm':p.distance(shapes[j])})
            for j in ht.query(p.buffer(.402)):
                if p.distance(hs[j])<.402:issues.append({'type':'foreign-hole','uuid':holes[j]['uuid']})
            for zone,shape in keepouts:
                if not shape.intersects(p.buffer(.352)):continue
                # Only the POWER reservation enclosing this exact owning land
                # may receive the separately native-tested same-net exception.
                if zone['uuid']==own_keepout_uuid and shape.covers(own_area) and zone['layer']=='F.Cu':continue
                issues.append({'type':'retained-keepout','uuid':zone['uuid']})
            row={'uuid':uid,'xy_mm':h['xy_mm'],'collisions':issues}
            (blocked if issues else accepted).append(row)
        if not accepted:raise ValueError('no legal main via sites: '+array['ref'])
        rows.append({'ref':array['ref'],'net':array['net'],'legal_sites':accepted,'blocked_sites':blocked})
    if any(digest(p)!=h for p,h in hashes.items()):raise ValueError('K array input changed during planning')
    report={'status':'UNSELECTED explicit finite K array subset; native rule/connectivity and electrical checks required',
        'source_sha256':hashes,
        'board_sha256':native['board_sha256'],'via_diameter_mm':.7,'via_drill_mm':.3,
        'copper_clearance_mm':.25,'hole_clearance_mm':.25,'geometry_guard_mm':.002,
        'rows':rows,'retained_via_count':sum(len(r['legal_sites']) for r in rows),
        'physical_scope':'Original 0.7 mm grid positions only; no terminal movement or shifted array. Every omitted trial via is absent from subsequent conductor extraction. Same-net keepout exception requires entire via inside the exact owning 4x4 land.'}
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('K explicit legal main vias:',report['retained_via_count'],'over',len(rows),'lands')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('native','receipt','partition','definition','output'):parser.add_argument(name,type=Path)
    a=parser.parse_args();plan(a.native,a.receipt,a.partition,a.definition,a.output)
