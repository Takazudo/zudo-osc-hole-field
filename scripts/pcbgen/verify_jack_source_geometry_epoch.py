"""Bridge exact local AGND source geometry to the white-pad jack epoch.

This is a nominal geometry equivalence check, not a model, contact, current,
material, or whole-board copper equivalence claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.jack_white_current_binding import verify as verify_current_native

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'.circuit-cache/issue38-recovery'
RECEIPTS={
    'mapping':('own-source-flux-boundaries-v2.json','bc766e053d76791c68afd41f65ea9ce184b93fdf11725d9b019c7d018e9b9ad4'),
    'single':('single-drill-cover-certificate-v2.json','9750c2e223e963e2ce2bf344967a5a78fb687be9fd263369cd1568e8e461dd79'),
    'multi':('multi-drill-cover-certificate-v2.json','1e2bd5decc29c5ed003e92222c5952a7a5cc1b5ce7ba47715ca5f036b090fc53'),
    'pth':('pth-source-geometry-certificate-v2.json','777af6fb22334f140a9b4a649e843c62957ed093ba4004835f45933d330cd245'),
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_items(native):
    rows={(item['ref'],item['pad']):item for item in native['items']
          if item.get('ref') and item['net']=='AGND'}
    if len(rows)!=sum(bool(item.get('ref')) and item['net']=='AGND' for item in native['items']):
        raise ValueError('duplicate native AGND source identity')
    return rows


def compare_epoch(old,new):
    if old['board_id']!=new['board_id']:
        raise ValueError('wrong jack native board epoch')
    for key in ('holes','outline_mm','stackup'):
        if old[key]!=new[key]:raise ValueError('jack local source geometry changed: '+key)
    before=source_items(old);after=source_items(new)
    if before!=after:
        raise ValueError('jack native AGND pad identities or geometry changed')
    all_before={item['uuid']:item for item in old['items'] if item['net']=='AGND'}
    all_after={item['uuid']:item for item in new['items'] if item['net']=='AGND'}
    if (len(all_before)!=sum(item['net']=='AGND' for item in old['items'])
        or len(all_after)!=sum(item['net']=='AGND' for item in new['items'])
        or all_before!=all_after):
        raise ValueError('jack native AGND via/pad land identity or geometry changed')
    return before


def exact_cover_keys(certificate,board_id):
    rows=[r for r in certificate['certificates'] if r['board_id']==board_id]
    keys={(r['ref'],r['pad']) for r in rows}
    if len(keys)!=len(rows):raise ValueError('duplicate historical source cover identity')
    return rows,keys


def verify():
    own_source_sha=digest(Path(__file__).read_bytes())
    paths={key:CACHE/name for key,(name,_) in RECEIPTS.items()}
    raw={key:path.read_bytes() for key,path in paths.items()}
    for key,(_,want) in RECEIPTS.items():
        if digest(raw[key])!=want:raise ValueError('historical source cover receipt changed: '+key)
    evidence={key:json.loads(value) for key,value in raw.items()}
    sources={str(path.relative_to(ROOT)):digest(raw[key]) for key,path in paths.items()}
    sources['scripts/pcbgen/verify_jack_source_geometry_epoch.py']=own_source_sha
    summary={}
    for side in ('left','right'):
        bid='osc-jack-'+side
        group=next((g for g in evidence['mapping']['boards'] if g['board_id']==bid),None)
        if group is None:raise ValueError('historical jack source group absent')
        folder=CACHE/'white-current-boards'/bid
        current_inventory=folder/'current-own-source-inventory-v1.json'
        current_native=folder/'native-geometry.json'
        current_receipt=folder/'current-native-receipt-v6.json'
        old_native=ROOT/group['native_export_path']
        old_board=ROOT/'boards'/bid/(bid+'-parallel-feeds.kicad_pcb')
        current_board=ROOT/'boards'/bid/(bid+'-white-current-v1.kicad_pcb')
        for path in (current_inventory,current_native,current_receipt,old_native,old_board,current_board):
            sources[str(path.relative_to(ROOT))]=digest(path.read_bytes())
        before=json.loads(old_native.read_bytes());after=json.loads(current_native.read_bytes())
        prior=json.loads(current_receipt.read_bytes());inventory=json.loads(current_inventory.read_bytes())
        if (group['native_export_sha256']!=digest(old_native.read_bytes())
            or group['board_sha256']!=before['board_sha256']
            or digest(old_board.read_bytes())!=before['board_sha256']
            or prior['native_export_sha256']!=digest(current_native.read_bytes())
            or prior['board_sha256']!=after['board_sha256']
            or digest(current_board.read_bytes())!=after['board_sha256']
            or inventory['board_sha256']!=after['board_sha256']):
            raise ValueError('jack old/current native receipt binding differs')
        if verify_current_native(side)!=prior:
            raise ValueError('current white-pad jack source/native authority differs')
        for name,want in prior['source_sha256'].items():
            if name in sources and sources[name]!=want:
                raise ValueError('conflicting current jack source dependency: '+name)
            sources[name]=want
        pads=compare_epoch(before,after)
        if inventory['own_source_contacts']!=group['own_source_contacts']:
            raise ValueError('jack fitted source boundary inventory changed')
        expected={(r['ref'],r['pad']):r for r in inventory['own_source_contacts']}
        if len(expected)!=len(inventory['own_source_contacts']):
            raise ValueError('duplicate fitted source inventory')
        single_rows,single=exact_cover_keys(evidence['single'],bid)
        multi_rows,multi=exact_cover_keys(evidence['multi'],bid)
        pth_rows,pth=exact_cover_keys(evidence['pth'],bid)
        drilled={key for key,row in expected.items() if row['family']=='SMD_drill_overlap_unresolved'}
        through={key for key,row in expected.items() if row['family']=='PTH'}
        if single & multi or single|multi!=drilled or pth!=through:
            raise ValueError('historical nominal source cover population differs')
        for row in single_rows+multi_rows:
            item=pads[row['ref'],row['pad']]
            if (row['pad_uuid']!=item['uuid'] or row['face'] not in item['analytic_primitives']
                or row['source_primitive']!=item['analytic_primitives'][row['face']]):
                raise ValueError('historical drilled SMD witness differs from current native pad')
        holes={row['uuid']:row for row in after['holes']}
        for row in pth_rows:
            item=pads[row['ref'],row['pad']]
            if (row['uuid']!=item['uuid'] or row['native_hole']!=holes.get(item['uuid'])
                or {face['layer']:face['native_primitive'] for face in row['foil_faces']}!=item['analytic_primitives']):
                raise ValueError('historical PTH witness differs from current native wall/land')
        summary[bid]={'fitted_AGND_source_contacts':len(expected),'all_native_AGND_pads':len(pads),
                      'all_AGND_pads_and_via_lands':sum(item['net']=='AGND' for item in after['items']),
                      'single_drill_SMD_nominal_covers':len(single),'multi_drill_SMD_nominal_covers':len(multi),
                      'PTH_nominal_face_wall_records':len(pth),'old_board_sha256':before['board_sha256'],
                      'current_board_sha256':after['board_sha256']}
    for name,want in sources.items():
        if digest((ROOT/name).read_bytes())!=want:
            raise ValueError('jack source epoch input changed during comparison: '+name)
    return {'status':'PASS exact local nominal AGND source geometry equivalence only',
            'historical_cover_receipts_sha256':{key:want for key,(_,want) in RECEIPTS.items()},
            'source_sha256':sources,'boards':summary,
            'scope':'Old local cover witnesses retain exact pad/drill/outline/stack geometry in current white-pad J epoch. Whole-board conductor, source flux, physical contact/process, 3D/primal, current, material and electrical/common acceptance remain OPEN. Old numerical matrices are not rebound.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('fresh source equivalence receipt required')
    report=verify()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as handle:json.dump(report,handle,indent=2,sort_keys=True);handle.write('\n')
    print(report['status'],report['boards'])
