"""Mandatory current-J native/source admission for a selected rail role.

The selected export is an exact mathematical net relabeling. This admits a
complete nominal rail diagnostic, not physical contact/current acceptance.
"""
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.jack_white_current_binding import verify as verify_jack_native
from scripts.pcbgen.selected_conductor_export import select
from scripts.pcbgen.source_contact_inventory import expected_contacts,reconcile_native

ROOT=Path(__file__).resolve().parents[2]
COUNTS={
    'osc-jack-left':{'+12V':271,'-12V':269,'+5V':59},
    'osc-jack-right':{'+12V':251,'-12V':243,'+5V':59},
}


def digest(data):return hashlib.sha256(data).hexdigest()


def resolve(name):
    path=Path(name)
    if str(path).startswith('/work/'):path=ROOT/path.relative_to('/work')
    elif not path.is_absolute():path=ROOT/path
    path=path.resolve()
    if not path.is_relative_to(ROOT):raise ValueError('selected J rail input outside worktree')
    return path


def verify_unchanged(authority):
    if authority is None:return
    for name,want in authority['dependency_sha256'].items():
        if digest(Path(name).read_bytes())!=want:
            raise ValueError('current J rail dependency changed: '+name)


def enter(selected_path,selected_bytes,original_path,receipt_path,net,include_loads,port_limit,main_strands):
    if original_path is None or receipt_path is None:
        raise ValueError('selected J rail requires original current native and successful v6 receipt')
    helpers=(ROOT/'scripts/pcbgen/current_j_rail_entry.py',ROOT/'scripts/pcbgen/selected_conductor_export.py',
             ROOT/'scripts/pcbgen/source_contact_inventory.py',ROOT/'scripts/pcbgen/jack_white_current_binding.py')
    helper_sha={str(path):digest(path.read_bytes()) for path in helpers}
    if net not in ('+12V','-12V','+5V'):
        raise ValueError('one exact current J rail role required')
    if not include_loads or port_limit or not main_strands:
        raise ValueError('complete J rail basis requires all loads, port-limit 0 and main strands')
    selected_path,original_path,receipt_path=map(resolve,(selected_path,original_path,receipt_path))
    selected=json.loads(selected_bytes)
    bid=selected.get('board_id')
    if bid not in COUNTS:raise ValueError('selected rail must belong to one current J half')
    original_bytes=original_path.read_bytes();original=json.loads(original_bytes)
    receipt_bytes=receipt_path.read_bytes();recorded=json.loads(receipt_bytes)
    if original.get('board_id')!=bid or recorded.get('board_id')!=bid:
        raise ValueError('original/current J rail board identity differs')
    if verify_jack_native(bid.removeprefix('osc-jack-'))!=recorded:
        raise ValueError('current J original native receipt/source differs')
    if recorded['native_export_sha256']!=digest(original_bytes):
        raise ValueError('current J original export differs from native receipt')
    regenerated=(json.dumps(select(original,net,digest(original_bytes)),separators=(',',':'))+'\n').encode()
    if selected_bytes!=regenerated or selected_path.read_bytes()!=selected_bytes:
        raise ValueError('selected J rail role differs from exact original-native relabeling')
    role=selected['conductor_role_mapping']
    if role['actual_native_net']!=net or role['original_native_export_sha256']!=digest(original_bytes):
        raise ValueError('selected J rail role metadata differs')
    partition_path=ROOT/'design/partition/partition.json'
    io_path=ROOT/'design/reports/io-partition.json'
    partition_bytes=partition_path.read_bytes();io_bytes=io_path.read_bytes()
    partition=json.loads(partition_bytes);io=json.loads(io_bytes)
    board=next(b for b in partition['boards'] if b['id']==bid)
    fitted={r['ref'] for r in partition['assignment']['components'] if r['board']==board['board_key'] and r['fitted']}
    expected=expected_contacts(bid,partition,io,{net})
    pads=reconcile_native(original,expected,fitted,{net})
    if len(pads)!=COUNTS[bid][net]:
        raise ValueError('current J fitted rail source inventory count differs')
    terminal=[row for row in partition['load_side_terminals']
              if row['board']==board['board_key'] and row['net']==net]
    if len(terminal)!=1:raise ValueError('one exact J rail main source terminal required')
    main=[item for item in original['items'] if item.get('ref')==terminal[0]['reference']
          and item.get('pad')==terminal[0]['manufacturer_pin'] and item['net']==net]
    members=set(original['main_rail_members'][net])
    if (len(main)!=1 or main[0]['uuid'] not in members or set(main[0]['copper'])!={'B.Cu'}
        or any(item['uuid'] not in members for item in pads.values())):
        raise ValueError('current J rail source/main native component differs')
    all_rail=[item for item in original['items'] if item.get('ref') and item['net']==net]
    if len(all_rail)!=len(pads)+1 or {item['uuid'] for item in all_rail}!={p['uuid'] for p in pads.values()}|{main[0]['uuid']}:
        raise ValueError('current J rail native source/main contact set differs')
    dependencies=dict(helper_sha)
    paths=(selected_path,original_path,receipt_path,partition_path,io_path,
           *helpers)
    for path in paths:
        value=digest(path.read_bytes());key=str(path)
        if key in dependencies and dependencies[key]!=value:
            raise ValueError('current J rail helper changed during admission: '+key)
        dependencies[key]=value
    if (dependencies[str(original_path)]!=digest(original_bytes)
        or dependencies[str(selected_path)]!=digest(selected_bytes)
        or dependencies[str(receipt_path)]!=digest(receipt_bytes)
        or dependencies[str(partition_path)]!=digest(partition_bytes)
        or dependencies[str(io_path)]!=digest(io_bytes)):
        raise ValueError('current J rail native/selected/receipt changed during admission')
    for name,want in recorded['source_sha256'].items():
        path=resolve(name);key=str(path)
        if key in dependencies and dependencies[key]!=want:
            raise ValueError('conflicting current J native/rail dependency: '+key)
        dependencies[key]=want
    authority={'status':'PASS current J selected-rail nominal model prerequisite only; physical/contact/current/common acceptance OPEN',
               'board_id':bid,'physical_net':net,'original_native_export_sha256':digest(original_bytes),
               'selected_native_export_sha256':digest(selected_bytes),'native_receipt_sha256':digest(receipt_bytes),
               'expected_load_contacts':[{'ref':ref,'pad':pad,'uuid':item['uuid'],'native_layers':sorted(item['copper'])}
                                         for (ref,pad,_),item in sorted(pads.items())],
               'main_contact':{'ref':main[0]['ref'],'pad':main[0]['pad'],'uuid':main[0]['uuid'],'layer':'B.Cu'},
               'dependency_sha256':dependencies}
    verify_unchanged(authority)
    return authority


def select_ports(geometry,authority):
    if authority is None:return
    if geometry['data']['board_id']!=authority['board_id']:
        raise ValueError('selected J rail extracted board identity differs')
    expected={(p['ref'],p['pad']):p for p in authority['expected_load_contacts']}
    main=authority['main_contact'];ports=geometry['ports'];seen=set();mains=0
    native={(item['ref'],item['pad']):item for item in geometry['data']['items']
            if item.get('ref') and item['net']=='AGND'}
    if len(native)!=sum(bool(item.get('ref')) and item['net']=='AGND' for item in geometry['data']['items']):
        raise ValueError('selected J rail extracted native contact duplicate')
    if len(ports)!=len(expected)+1:
        raise ValueError('selected J rail model source basis incomplete')
    for port in ports:
        key=port['ref'],port['pad']
        if key in seen:raise ValueError('duplicate selected J rail model port')
        seen.add(key)
        layer=geometry['active_sheet_layers'][port['layer']]
        if key==(main['ref'],main['pad']):
            mains+=1
            if (port['kind']!='main' or layer!='B.Cu' or port.get('strand_count')!=19
                or 'maximum_wetting' not in port or native.get(key,{}).get('uuid')!=main['uuid']):
                raise ValueError('selected J rail main profile differs')
        else:
            item=expected.get(key)
            if (item is None or port['kind']!='load' or layer not in item['native_layers']
                or native.get(key,{}).get('uuid')!=item['uuid']):
                raise ValueError('selected J rail fitted load profile differs')
    if mains!=1 or seen!=set(expected)|{(main['ref'],main['pad'])}:
        raise ValueError('selected J rail reference/source set differs')
