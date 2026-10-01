"""Mandatory source/native admission for current white-pad jack conductors.

This gate permits a complete nominal numerical diagnostic only. Historical
jack matrices cannot be rebound after the shared LED pad revision.
"""
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.jack_white_current_binding import verify as verify_native

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def resolve(path):
    p=Path(path)
    if str(p).startswith('/work/'):p=ROOT/p.relative_to('/work')
    elif not p.is_absolute():p=ROOT/p
    p=p.resolve()
    if not p.is_relative_to(ROOT):raise ValueError('jack dependency outside worktree')
    return p


def verify_unchanged(authority):
    if authority is not None:
        for name,want in authority['dependency_sha256'].items():
            if digest(name)!=want:raise ValueError('jack current native dependency changed: '+name)


def enter(source,native_bytes,receipt_path,include_loads,port_limit,main_strands):
    native=json.loads(native_bytes);bid=native.get('board_id')
    if bid not in ('osc-jack-left','osc-jack-right'):
        if receipt_path is not None:raise ValueError('jack receipt supplied for another board')
        return None
    if receipt_path is None:raise ValueError('successful current jack native receipt required')
    if not include_loads or port_limit or not main_strands:
        raise ValueError('complete jack source basis requires all loads, port-limit 0 and main strands')
    source=resolve(source);receipt_path=resolve(receipt_path)
    recorded=json.loads(receipt_path.read_bytes())
    if recorded.get('board_id')!=bid or not recorded.get('status','').startswith('PASS current native jack geometry prerequisite'):
        raise ValueError('wrong or failed current jack native receipt')
    side=bid.removeprefix('osc-jack-')
    actual=verify_native(side)
    if actual!=recorded:raise ValueError('current jack source/native receipt differs from exact regeneration')
    dependencies={str(receipt_path):digest(receipt_path)}
    for name,want in recorded['source_sha256'].items():
        path=resolve(name)
        if digest(path)!=want:raise ValueError('current jack native dependency changed: '+name)
        dependencies[str(path)]=want
    if dependencies.get(str(source))!=hashlib.sha256(native_bytes).hexdigest():
        raise ValueError('jack native export is not the reviewed current board')
    if native['kicad_version']!='10.0.6' or native['board_sha256']!=recorded['board_sha256']:
        raise ValueError('jack native oracle or board differs')
    result={'status':'PASS current native prerequisite only; no contact/material/current/common acceptance',
            'board_id':bid,'dependency_sha256':dependencies,
            'all_source_AGND_connected_count':recorded['all_source_AGND_connected_count']}
    verify_unchanged(result)
    return result


def select_ports(geometry,authority):
    if authority is None:return
    if geometry['data']['board_id']!=authority['board_id']:
        raise ValueError('jack extracted board differs')
    native=geometry['data'];selected=set(native['main_rail_members']['AGND'])
    expected={(p['ref'],p['pad']):p for p in native['items'] if p.get('ref') and p['net']=='AGND'}
    if (len(expected)!=authority['all_source_AGND_connected_count']
        or len(geometry['ports'])!=len(expected)):
        raise ValueError('jack model omitted or duplicated a source ground contact')
    seen=set();mains=0
    for port in geometry['ports']:
        key=port['ref'],port['pad'];item=expected.get(key)
        if item is None or key in seen or item['uuid'] not in selected:
            raise ValueError('jack model contact identity or component differs')
        seen.add(key)
        layer=geometry['active_sheet_layers'][port['layer']]
        if layer not in item['copper'] or port['kind'] not in ('load','GH','main'):
            raise ValueError('jack model face or kind differs')
        if port['kind']=='main':
            mains+=1
            if port.get('strand_count')!=19 or 'maximum_wetting' not in port:
                raise ValueError('jack main lacks finite nineteen-support numerical trial')
    if seen!=set(expected) or mains!=3:
        raise ValueError('jack complete main/load/GH source profiles differ')
