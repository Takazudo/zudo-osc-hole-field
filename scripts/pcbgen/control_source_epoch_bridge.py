"""Retained P local own-source geometry across an unrelated IO/helper epoch.

The v3 native/model gate stays stale. This bridges only local source contact
identities for a current-source boundary inventory; no conductor/model result.
"""
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.control_ground_inventory import audit
from scripts.pcbgen.source_flux_boundary_inventory import inventory

ROOT=Path(__file__).resolve().parents[2]
CACHE=ROOT/'.circuit-cache/issue38-recovery'
NATIVE=CACHE/'control-feasibility-v3/ground-feasibility-geometry.json'
RECEIPT=CACHE/'control-feasibility-v3/ground-feasibility-native-receipt.json'
RECEIPT_SHA256='e9cf9cc9780283aad4e67920c772303846f5d2fb6dc01b6ac4b93347917c4639'
MANIFEST=ROOT/'design/partition/control-ground-feasibility/osc-control.receipt.json'
PARTITION=ROOT/'design/partition/partition.json'
IO=ROOT/'design/reports/io-partition.json'
OLD_IO=CACHE/'white-land-review/io-partition.json'
ARCHIVE=ROOT/'design/partition/model-history/pre-two-layer/sources'
OLD_SOURCES={
    'design/reports/io-partition.json':OLD_IO,
    'scripts/pcbgen/extract_power_geometry.py':ARCHIVE/'092f54e1f24c45545ad74c8105dd148d070043d6633ab09adb0bbe9f04ff993c.py',
    'scripts/pcbgen/native_stack.py':ARCHIVE/'3de2f981b7af80500b37245ff74fa29a5f08ee1423d04cdafe336635892556d0.py',
}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bind(hashes,path,want=None):
    key=str(Path(path).resolve());actual=sha(path)
    if want is not None and actual!=want:raise ValueError('P epoch source changed: '+key)
    if key in hashes and hashes[key]!=actual:raise ValueError('P epoch source digest conflict: '+key)
    hashes[key]=actual
    return actual


def unique_packages(data):
    rows=data['physical_packages'];by_ref={r['ref']:r for r in rows}
    if len(rows)!=len(by_ref):raise ValueError('duplicate source package identity')
    return by_ref


def project_io(old,current,partition):
    if {k:v for k,v in old.items() if k!='physical_packages'}!={k:v for k,v in current.items() if k!='physical_packages'}:
        raise ValueError('P source non-package IO projection changed')
    boards=[b for b in partition['boards'] if b['id']=='osc-control']
    if len(boards)!=1:raise ValueError('P exact board assignment absent')
    refs={r['ref'] for r in partition['assignment']['components'] if r['board']==boards[0]['board_key']}
    if len(refs)!=285:raise ValueError('P assigned package population changed')
    before,after=unique_packages(old),unique_packages(current)
    if refs-set(before) or refs-set(after) or any(before[ref]!=after[ref] for ref in refs):
        raise ValueError('P assigned package source projection changed')
    return refs


def verify():
    own=sha(__file__)
    receipt_raw=RECEIPT.read_bytes();receipt=json.loads(receipt_raw)
    if hashlib.sha256(receipt_raw).hexdigest()!=RECEIPT_SHA256:
        raise ValueError('original retained P v3 receipt changed')
    native_raw=NATIVE.read_bytes();native=json.loads(native_raw)
    manifest_raw=MANIFEST.read_bytes();manifest=json.loads(manifest_raw)
    partition_raw=PARTITION.read_bytes();partition=json.loads(partition_raw)
    old_io_raw=OLD_IO.read_bytes();old_io=json.loads(old_io_raw)
    current_io_raw=IO.read_bytes();current_io=json.loads(current_io_raw)
    if (receipt.get('board_id')!='osc-control' or receipt.get('native_model_prerequisite_passed') is not True
        or receipt.get('rule_error_count')!=0 or receipt.get('schematic_parity_count')!=0
        or native.get('board_id')!='osc-control' or native.get('kicad_version')!='10.0.6'
        or native['board_sha256']!=receipt['board_sha256']):
        raise ValueError('historical P native prerequisite failed')
    project_io(old_io,current_io,partition)
    hashes={str(Path(__file__).resolve()):own,
            str(RECEIPT.resolve()):hashlib.sha256(receipt_raw).hexdigest(),
            str(NATIVE.resolve()):hashlib.sha256(native_raw).hexdigest(),
            str(MANIFEST.resolve()):hashlib.sha256(manifest_raw).hexdigest(),
            str(PARTITION.resolve()):hashlib.sha256(partition_raw).hexdigest(),
            str(IO.resolve()):hashlib.sha256(current_io_raw).hexdigest(),
            str(OLD_IO.resolve()):hashlib.sha256(old_io_raw).hexdigest()}
    for name in ('control_ground_inventory.py','source_flux_boundary_inventory.py','source_contact_inventory.py'):
        path=ROOT/'scripts/pcbgen'/name
        bind(hashes,path)
    old_hashes={}
    for group in ('source_sha256','artifacts_sha256'):
        for name,want in receipt[group].items():
            original=ROOT/name.removeprefix('/work/')
            actual=OLD_SOURCES.get(name,original)
            bind(hashes,actual,want)
            if name in OLD_SOURCES:
                current_sha=bind(hashes,original)
                old_hashes[name]={'archive_path':str(actual.resolve()),'archive_sha256':want,
                                  'current_sha256':current_sha}
    if set(old_hashes)!=set(OLD_SOURCES):raise ValueError('P expected exact three source epoch changes')
    if hashlib.sha256(native_raw).hexdigest()!=receipt['artifacts_sha256'][str(NATIVE.relative_to(ROOT))]:
        raise ValueError('P native geometry not retained by old receipt')
    board=ROOT/native['board'].removeprefix('/work/')
    bind(hashes,board,native['board_sha256'])
    companions=receipt.get('companion_sha256',{})
    expected_companions={str(board.with_suffix(suffix).relative_to(ROOT)) for suffix in ('.kicad_pro','.kicad_sch','.kicad_dru')}
    if set(companions)!=expected_companions:
        raise ValueError('P copied companion receipt differs')
    for name,want in companions.items():bind(hashes,ROOT/name,want)
    if sha(board.with_suffix('.kicad_pro'))!=native['project_sha256']:
        raise ValueError('P native project companion differs')
    drc=ROOT/next(n for n in receipt['artifacts_sha256'] if n.endswith('ground-feasibility-drc.json'))
    drc_raw=drc.read_bytes()
    if hashlib.sha256(drc_raw).hexdigest()!=receipt['artifacts_sha256'][str(drc.relative_to(ROOT))]:
        raise ValueError('P retained same-board DRC bytes differ')
    native_drc=json.loads(drc_raw)
    if (native_drc['source']!=board.name or native_drc['kicad_version']!='10.0.6'
        or native_drc['schematic_parity'] or any(row['severity']=='error' for row in native_drc['violations'])):
        raise ValueError('P retained same-board DRC fails')
    old_ground=audit(native,manifest,partition,old_io)
    current_ground=audit(native,manifest,partition,current_io)
    if old_ground!=receipt['source_ground_inventory'] or current_ground!=old_ground or current_ground['connected_count']!=344:
        raise ValueError('P complete ground source projection changed')
    old_rows=inventory(native,partition,old_io)['own_source_contacts']
    current_rows=inventory(native,partition,current_io)['own_source_contacts']
    if old_rows!=current_rows or len(current_rows)!=214:
        raise ValueError('P own-source boundary geometry changed')
    for path in (NATIVE,MANIFEST,PARTITION,OLD_IO,board,drc):bind(hashes,path)
    for name,want in hashes.items():
        if sha(name)!=want:raise ValueError('P source bridge input changed: '+name)
    return {'status':'PASS P local own-source geometry epoch equivalence only; current native/model and physical/electrical acceptance OPEN',
            'source_sha256':hashes,'old_source_epochs':old_hashes,
            'native_export_sha256':hashlib.sha256(native_raw).hexdigest(),
            'own_source_contact_count':214,
            'family_counts':dict(__import__('collections').Counter(r['family'] for r in current_rows)),
            'scope':'Old passing v3 P candidate and local pad/drill/AGND source projection match current IO. Native/model receipt is not rebound to changed exporter/native_stack/IO code; no current global model or physical flux acceptance.'}
