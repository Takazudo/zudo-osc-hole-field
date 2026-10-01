"""Current native/source identities for all fitted own AGND boundaries.

This is a nominal geometry/provenance inventory, never a physical flux class.
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from scripts.pcbgen.core_model_gate import require_native_prerequisite as core_gate
from scripts.pcbgen.control_model_gate import require_native_prerequisite as control_gate
from scripts.pcbgen.jack_white_current_binding import verify as jack_gate
from scripts.pcbgen.peripheral_model_entry import enter as peripheral_gate
from scripts.pcbgen.source_flux_boundary_inventory import inventory
from scripts.pcbgen.verify_jack_source_geometry_epoch import verify as jack_epoch

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'.circuit-cache/issue38-recovery'
PARTITION=ROOT/'design/partition/partition.json'
IO=ROOT/'design/reports/io-partition.json'
EXPECTED={'osc-jack-left':1070,'osc-jack-right':896,'osc-core':1903,'osc-control':214,'osc-stage-optical':60}
FAMILIES={'convex_SMD':3620,'SMD_drill_overlap_unresolved':218,'PTH':305}


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def add_hashes(target,source):
    for name,want in source.items():
        path=Path(name)
        if not path.is_absolute():path=ROOT/path
        key=str(path.resolve())
        if key in target and target[key]!=want:raise ValueError('contradictory current source dependency: '+key)
        if digest(path)!=want:raise ValueError('current source dependency changed: '+key)
        target[key]=want


def current_boards():
    for side in ('left','right'):
        bid='osc-jack-'+side
        folder=CACHE/'white-current-boards'/bid
        yield bid,folder/'native-geometry.json',folder/'current-native-receipt-v6.json',None
    yield ('osc-core',CACHE/'core-feasibility-v7/ground-feasibility-geometry.json',
           CACHE/'core-feasibility-v7/ground-feasibility-native-receipt.json',
           ROOT/'design/partition/core-ground-feasibility/osc-core.receipt.json')
    yield ('osc-control',CACHE/'control-feasibility-v4/ground-feasibility-geometry.json',
           CACHE/'control-feasibility-v4/ground-feasibility-native-receipt.json',
           ROOT/'design/partition/control-ground-feasibility/osc-control.receipt.json')
    yield ('osc-stage-optical',CACHE/'optical-ground-prerequisite-v3/native-geometry.json',
           CACHE/'optical-ground-prerequisite-v3/native-receipt.json',
           ROOT/'design/partition/peripheral-ground-feasibility/optical-ground-v2/osc-stage-optical.receipt.json')


def verify():
    own_hash=digest(__file__)
    initial_helpers={str(Path(__file__).resolve()):own_hash}
    for module in list(sys.modules.values()):
        name=getattr(module,'__name__','');path=getattr(module,'__file__',None)
        if name.startswith('scripts.pcbgen.') and path and Path(path).suffix=='.py':
            file=Path(path).resolve()
            if not file.is_relative_to(ROOT/'scripts/pcbgen'):
                raise ValueError('source manifest imported helper outside source tree')
            initial_helpers[str(file)]=digest(file)
    partition_raw=PARTITION.read_bytes();io_raw=IO.read_bytes()
    partition=json.loads(partition_raw);io=json.loads(io_raw)
    hashes={str(PARTITION):hashlib.sha256(partition_raw).hexdigest(),
            str(IO):hashlib.sha256(io_raw).hexdigest(),**initial_helpers}
    # This retained bridge proves both current J pad/holes and old local cover
    # identity; it cannot transfer electrical or manufactured acceptance.
    bridge=jack_epoch()
    add_hashes(hashes,bridge['source_sha256'])
    boards=[];total=Counter();all_keys=set()
    for bid,native_path,receipt_path,manifest_path in current_boards():
        raw=native_path.read_bytes();native=json.loads(raw)
        if native['board_id']!=bid:raise ValueError('wrong current native board: '+bid)
        if bid.startswith('osc-jack-'):
            side=bid.removeprefix('osc-jack-');authority=jack_gate(side)
            if authority['native_export_sha256']!=hashlib.sha256(raw).hexdigest():
                raise ValueError('current jack native export differs')
            if json.loads(receipt_path.read_bytes())!=authority:
                raise ValueError('current jack native receipt differs')
            add_hashes(hashes,authority['source_sha256'])
            add_hashes(hashes,{str(receipt_path):digest(receipt_path)})
        elif bid=='osc-core':
            authority=core_gate(native_path,receipt_path,manifest_path)
            add_hashes(hashes,authority['dependency_sha256'])
        elif bid=='osc-control':
            authority=control_gate(native_path,receipt_path,manifest_path)
            if authority['dependency_sha256'].get(str(native_path.resolve()))!=hashlib.sha256(raw).hexdigest():
                raise ValueError('P fresh native source authority changed')
            add_hashes(hashes,authority['dependency_sha256'])
        else:
            authority=peripheral_gate(native_path,raw,receipt_path,manifest_path,True,0)
            add_hashes(hashes,authority['dependency_sha256'])
        if digest(native_path)!=hashlib.sha256(raw).hexdigest():
            raise ValueError('native export changed after admission: '+bid)
        rows=inventory(native,partition,io)['own_source_contacts']
        keys={(r['ref'],r['pad']) for r in rows}
        if len(rows)!=EXPECTED[bid] or len(keys)!=len(rows) or all_keys&keys:
            raise ValueError('current fitted own source population differs: '+bid)
        all_keys|=keys
        counts=Counter(row['family'] for row in rows);total.update(counts)
        boards.append({'board_id':bid,'board_sha256':native['board_sha256'],
                       'native_export_sha256':hashlib.sha256(raw).hexdigest(),
                       'native_stack_sha256':hashlib.sha256(json.dumps(native['stackup'],sort_keys=True).encode()).hexdigest(),
                       'native_outline_sha256':hashlib.sha256(json.dumps(native['outline_mm'],sort_keys=True).encode()).hexdigest(),
                       'native_holes_sha256':hashlib.sha256(json.dumps(native['holes'],sort_keys=True).encode()).hexdigest(),
                       'own_source_contacts':rows,'family_counts':dict(counts),
                       'source_authority_status':authority['status'],
                       'physical_source_support_qualified':False})
    if len(all_keys)!=4143 or dict(total)!=FAMILIES:
        raise ValueError('current complete source family split differs')
    add_hashes(hashes,{str(Path(__file__).resolve()):own_hash,
                      str(ROOT/'scripts/pcbgen/source_flux_boundary_inventory.py'):digest(ROOT/'scripts/pcbgen/source_flux_boundary_inventory.py'),
                      str(ROOT/'scripts/pcbgen/source_contact_inventory.py'):digest(ROOT/'scripts/pcbgen/source_contact_inventory.py')})
    if digest(PARTITION)!=hashes[str(PARTITION)] or digest(IO)!=hashes[str(IO)]:
        raise ValueError('source partition or IO changed during inventory')
    for name,want in hashes.items():
        if digest(name)!=want:raise ValueError('current source manifest dependency changed: '+name)
    return {'status':'PASS current-native nominal fitted own-contact geometry inventory only; physical/electrical acceptance NOT ACCEPTED',
            'source_sha256':hashes,'own_source_contact_count':len(all_keys),
            'family_counts':dict(total),'boards':boards,
            'scope':'Current source/native pad/drill/stack identity only. Real terminal flux/contact/process/material/current, complete 3D dual/primal and joined electrical acceptance OPEN.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('fresh manifest output required')
    report=verify();args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as handle:json.dump(report,handle,indent=2,sort_keys=True);handle.write('\n')
    print(report['status'],report['own_source_contact_count'],report['family_counts'])
