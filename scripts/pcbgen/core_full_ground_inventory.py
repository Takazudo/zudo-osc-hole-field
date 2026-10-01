"""All actual K normal-ground contacts from the source and current native board.

This is a complete nominal model-port inventory. It does not select physical
contact support, source flux, hot material or joined K/J/P electrical limits.
"""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.core_model_gate import require_native_prerequisite
from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native

ROOT=Path(__file__).resolve().parents[2]


def sha(data):return hashlib.sha256(data).hexdigest()


def project(native,partition,io):
    if native['board_id']!='osc-core' or native['kicad_version']!='10.0.6':
        raise ValueError('current pinned K native export required')
    board=next(b for b in partition['boards'] if b['id']=='osc-core')
    fitted={r['ref'] for r in partition['assignment']['components'] if r['board']==board['board_key'] and r['fitted']}
    expected=expected_contacts('osc-core',partition,io,{'AGND'})
    own=reconcile_native(native,expected,fitted,{'AGND'})
    if len(own)!=1903:raise ValueError('complete K fitted own-ground inventory changed')
    pads=[r for r in native['items'] if r.get('ref') and r['net']=='AGND']
    by_key={(r['ref'],r['pad']):r for r in pads}
    if len(by_key)!=len(pads):raise ValueError('duplicate K native ground contact identity')
    main=set(native['main_rail_members']['AGND'])
    header_sources={(c['pcb_reference'],pad):c['id'] for c in partition['connectors'] if c['board']=='K'
                    for pad,net in c['pin_map'].items() if net=='AGND'}
    if len(header_sources)!=376:raise ValueError('complete K source GH return inventory changed')
    actual_headers={key for key in by_key if key[0].startswith('J900')}
    if actual_headers!=set(header_sources):raise ValueError('K native/source GH return identities differ')
    terminals=[r for r in partition['load_side_terminals'] if r['board']=='K' and r['net']=='AGND']
    if len(terminals)!=9:raise ValueError('nine exact K source ground main lands required')
    main_keys={(r['reference'],r['manufacturer_pin']) for r in terminals}
    if len(main_keys)!=9 or {key for key in by_key if key[0].startswith('TP990')}!=main_keys:
        raise ValueError('K native/source main land identities differ')
    own_keys={(ref,pad) for ref,pad,_ in own}
    if own_keys & set(header_sources) or own_keys & main_keys:
        raise ValueError('K own/GH/main ground contacts overlap')
    dnp_refs={p['ref'] for p in io['physical_packages'] if p['dnp']}
    omitted=set(by_key)-own_keys-set(header_sources)-main_keys
    if len(omitted)!=8 or any(ref not in dnp_refs for ref,pad in omitted):
        raise ValueError('K nominal model omits fitted or includes non-DNP ground contacts')
    rows=[]
    for ref,pad,net in sorted(own):
        item=own[ref,pad,net]
        if item['uuid'] not in main:raise ValueError('K own ground outside native main component')
        face='B.Cu' if 'B.Cu' in item['copper'] else 'F.Cu'
        if face not in item['copper']:raise ValueError('K fitted own load lacks external foil')
        rows.append({'ref':ref,'pad':pad,'uuid':item['uuid'],'kind':'load','physical_layer':face,
                     'native_xy_mm':item['xy_mm']})
    for key,connector in sorted(header_sources.items()):
        item=by_key.get(key)
        if item is None or item['uuid'] not in main or set(item['copper'])!={'F.Cu'}:
            raise ValueError('K GH source/native F ground return differs: '+str(key))
        rows.append({'ref':key[0],'pad':key[1],'uuid':item['uuid'],'kind':'GH','physical_layer':'F.Cu',
                     'native_xy_mm':item['xy_mm'],'source_connector':connector})
    for terminal in sorted(terminals,key=lambda r:r['reference']):
        key=terminal['reference'],terminal['manufacturer_pin'];item=by_key.get(key)
        expected_xy=[x+y for x,y in zip(terminal['center_mm'],[100,50])]
        if (item is None or item['uuid'] not in main or set(item['copper'])!={'F.Cu'}
                or item['xy_mm']!=expected_xy):
            raise ValueError('K main source/native F ground land differs: '+str(key))
        rows.append({'ref':key[0],'pad':key[1],'uuid':item['uuid'],'kind':'main','physical_layer':'F.Cu',
                     'native_xy_mm':item['xy_mm']})
    if len(rows)!=2288 or len({(r['ref'],r['pad']) for r in rows})!=2288:
        raise ValueError('K complete source model basis differs')
    return {'board_id':'osc-core','board_sha256':native['board_sha256'],
            'fitted_own_count':1903,'GH_return_count':376,'main_land_count':9,'source_DNP_omission_count':8,
            'contacts':rows,'balanced_function_count':2287,
            'scope':'Complete actual nominal K fitted-own/GH/main contact identities and connected native component only. Physical source/current/3D/primal/material/joined electrical acceptance OPEN.'}


def verify(native_path,receipt_path,manifest_path):
    native_path,receipt_path,manifest_path=map(Path,(native_path,receipt_path,manifest_path))
    own_code=Path(__file__).read_bytes();native_raw=native_path.read_bytes()
    authority=require_native_prerequisite(native_path,receipt_path,manifest_path)
    partition_path=ROOT/'design/partition/partition.json';io_path=ROOT/'design/reports/io-partition.json'
    partition_raw=partition_path.read_bytes();io_raw=io_path.read_bytes()
    hashes=dict(authority['dependency_sha256'])
    if (hashes[str(native_path.resolve())]!=sha(native_raw)
        or hashes[str(partition_path)]!=sha(partition_raw)
        or hashes[str(io_path)]!=sha(io_raw)):
        raise ValueError('K full inventory parse bytes differ from v7 native authority')
    rows=project(json.loads(native_raw),json.loads(partition_raw),json.loads(io_raw))
    source=str(Path(__file__).resolve())
    if source in hashes and hashes[source]!=sha(own_code):
        raise ValueError('conflicting K full inventory source')
    hashes[source]=sha(own_code)
    for name,want in hashes.items():
        if sha(Path(name).read_bytes())!=want:raise ValueError('K full inventory input changed: '+name)
    return {'status':'PASS complete K nominal source/native model basis only; electrical/physical acceptance OPEN',
            'native_prerequisite_status':authority['status'],'source_sha256':hashes,**rows}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('native','receipt','manifest','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('fresh K full basis path required')
    report=verify(args.native,args.receipt,args.manifest)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as handle:json.dump(report,handle,indent=2,sort_keys=True);handle.write('\n')
    print(report['status'],report['fitted_own_count'],report['GH_return_count'],report['main_land_count'])
