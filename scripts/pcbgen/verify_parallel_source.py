"""Read-only source-to-native UUID/dimension and prior-copper reconciliation."""
import argparse
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_local_links import blocks
from scripts.pcbgen.replay_equivalence import verify_export_provenance


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_items(spec,native,old,new):
    items={i['uuid']:i for i in native['items']};holes={h['uuid']:h for h in native['holes']}
    if len(items)!=len(native['items']) or len(holes)!=len(native['holes']):raise ValueError('duplicate native object UUID')
    expected={'via':set(),'segment':set(),'arc':set()};maximum_error=0.
    def near(actual,source):
        nonlocal maximum_error
        if len(actual)!=len(source):raise ValueError('coordinate dimension mismatch')
        error=max(abs(float(a)-float(b)*1e6) for a,b in zip(actual,source));maximum_error=max(maximum_error,error)
        if error>1.000001:raise ValueError('native source dimension differs beyond one integer coordinate unit')
    for row in spec['added']:
        identity=row['net']+':'+row['cluster'];net=row['net']
        pad=items[row['pad']['uuid']]
        if (pad.get('ref'),pad.get('pad'),pad['net'])!=(row['pad']['ref'],row['pad']['pad'],net):
            raise ValueError('parallel source pad identity/net mismatch')
        near([v*1e6 for v in pad['xy_mm']],row['points_mm'][0])
        uid=stable_uuid(spec['board_id'],'rail-transfer-via',identity);expected['via'].add(uid)
        via=items[uid];hole=holes[uid]
        if via['net']!=net or hole['net']!=net or not hole['plated']:raise ValueError('parallel via net/plating mismatch')
        if set(via['analytic_primitives'])!={'F.Cu','In1.Cu','In2.Cu','B.Cu'}:raise ValueError('parallel via layer span mismatch')
        near([v*1e6 for v in hole['size_mm']],[row['via_drill_mm']]*2)
        near([v*1e6 for v in hole['xy_mm']],row['via_xy_mm'])
        for primitive in via['analytic_primitives'].values():
            if primitive['kind']!='circle':raise ValueError('parallel via annulus is not circular')
            near(primitive['centre_nm'],row['via_xy_mm']);near(primitive['half_size_nm'],[row['via_diameter_mm']/2]*2)
        for index,(start,end) in enumerate(zip(row['points_mm'],row['points_mm'][1:])):
            uid=stable_uuid(spec['board_id'],'rail-transfer-track',identity+':'+str(index));expected['segment'].add(uid)
            item=items[uid];layer=row.get('segment_layers',[row['layer']]*(len(row['points_mm'])-1))[index]
            if item['net']!=net or set(item['analytic_primitives'])!={layer}:raise ValueError('parallel track net/layer mismatch')
            primitive=item['analytic_primitives'][layer]
            if primitive['kind']!='segment':raise ValueError('parallel source segment changed type')
            near(primitive['start_nm'],start);near(primitive['end_nm'],end)
            width=row.get('segment_widths_mm',[row['width_mm']]*(len(row['points_mm'])-1))[index]
            near([primitive['radius_nm']],[width/2])
    if len(expected['via'])!=len(spec['added']):raise ValueError('duplicate parallel source request identity')
    if old['footprint']!=new['footprint']:raise ValueError('parallel source changed a prior footprint or owner style')
    for kind in expected:
        if any(new[kind].get(uid)!=body for uid,body in old[kind].items()):raise ValueError('parallel source changed prior '+kind)
        if set(new[kind])-set(old[kind])!=expected[kind]:raise ValueError('new copper differs from exact source UUID set: '+kind)
    return {'exact_source_new_uuid_counts':{k:len(v) for k,v in expected.items()},
        'all_prior_footprint_track_via_arc_blocks_equal':True,'maximum_native_dimension_error_nm':maximum_error,
        'comparison_scope':'One KiCad integer unit (1 nm) plus 0.000001 nm floating comparison guard; not a physical manufacturing tolerance.'}


def run(specification,source,candidate,geometry,output):
    paths=[specification,source,candidate,candidate.with_suffix('.kicad_pro'),geometry,Path(__file__),Path('scripts/pcbgen/extract_power_geometry.py')]
    hashes={str(p):digest(p) for p in paths}
    spec=json.loads(specification.read_text());native=json.loads(geometry.read_text())
    if spec['board_sha256']!=digest(source):raise ValueError('parallel source has wrong predecessor board')
    verify_export_provenance(native,spec['board_id'],candidate,candidate.with_suffix('.kicad_pro'),'scripts/pcbgen/extract_power_geometry.py')
    report=verify_items(spec,native,blocks(source),blocks(candidate))
    if any(digest(p)!=expected for p,expected in hashes.items()):raise ValueError('source reconciliation input changed')
    report.update({'status':'PASS - exact source/new native copper and prior-copper reconciliation only',
        'board_id':spec['board_id'],'input_sha256':hashes,'electrical_acceptance':'NOT RUN for changed conductor'})
    output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(report['board_id'],report['exact_source_new_uuid_counts'],report['maximum_native_dimension_error_nm'])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('specification','source','candidate','geometry','output'):parser.add_argument(name,type=Path)
    a=parser.parse_args();run(a.specification,a.source,a.candidate,a.geometry,a.output)
