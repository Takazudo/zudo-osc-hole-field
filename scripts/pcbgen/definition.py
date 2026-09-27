"""Strict, dependency-free board definition and placement-lock parsing."""
from __future__ import annotations
from dataclasses import dataclass
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

@dataclass(frozen=True)
class BoardDefinition:
    board_id: str
    outline: tuple[tuple[float,float], ...]
    corner_radius_mm: float
    layers: int
    thickness_mm: float
    stackup: tuple[dict, ...]
    mounting_holes: tuple[dict, ...]
    keepouts: tuple[dict, ...]
    domains: tuple[str, ...]
    placement_uids: tuple[str, ...]
    netlist: str
    schematic: str


def _point(raw, name):
    if not isinstance(raw,(list,tuple)) or len(raw)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in raw):
        raise ValueError(f'{name}: expected [x_mm,y_mm]')
    return float(raw[0]),float(raw[1])


def load_definition(path: Path) -> BoardDefinition:
    data=json.loads(path.read_text())
    required={'schema_version','board_id','outline','corner_radius_mm','layers','thickness_mm','stackup','mounting_holes','keepouts','domains','placement_uids','netlist','schematic'}
    if set(data)!=required or data['schema_version']!=1:raise ValueError('board definition keys/version mismatch')
    board_id=data['board_id']
    if not isinstance(board_id,str) or not board_id or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in board_id):raise ValueError('invalid board_id')
    if path.stem!=board_id:raise ValueError('board_id must match filename')
    outline=tuple(_point(p,'outline') for p in data['outline'])
    if len(outline)<3 or len(set(outline))!=len(outline):raise ValueError('outline needs three distinct points')
    radius=data['corner_radius_mm']
    if isinstance(radius,bool) or not isinstance(radius,(float,int)) or radius<0:raise ValueError('invalid corner radius')
    layers=data['layers'];thick=data['thickness_mm']
    if layers not in (2,4,6,8) or isinstance(layers,bool):raise ValueError('unsupported layer count')
    if isinstance(thick,bool) or not isinstance(thick,(float,int)) or thick<=0:raise ValueError('invalid thickness')
    stack=data['stackup']
    if not isinstance(stack,list) or not stack or any(not isinstance(x,dict) for x in stack):raise ValueError('stackup must be a nonempty layer list')
    copper=[x.get('layer') for x in stack if isinstance(x.get('layer'),str) and x['layer'].endswith('.Cu')]
    if len(copper)!=layers or len(set(copper))!=layers or 'F.Cu' not in copper or 'B.Cu' not in copper:
        raise ValueError('stackup copper layers do not match layer count')
    for key in ('mounting_holes','keepouts','domains','placement_uids'):
        if not isinstance(data[key],list):raise ValueError(f'{key}: expected list')
    if any(not isinstance(v,str) or not v for key in ('domains','placement_uids') for v in data[key]):raise ValueError('blank domain or UID')
    if len(set(data['domains']))!=len(data['domains']) or len(set(data['placement_uids']))!=len(data['placement_uids']):raise ValueError('duplicate domain or UID')
    if len({h.get('id') for h in data['mounting_holes']})!=len(data['mounting_holes']):raise ValueError('duplicate mounting hole id')
    if len({k.get('id') for k in data['keepouts']})!=len(data['keepouts']):raise ValueError('duplicate keepout id')
    for h in data['mounting_holes']:
        if set(h)!={'id','center','diameter_mm'} or not isinstance(h['id'],str) or h['diameter_mm']<=0:raise ValueError('invalid mounting hole')
        _point(h['center'],'mounting hole center')
    for k in data['keepouts']:
        if set(k)!={'id','polygon','layers'} or len(k['polygon'])<3:raise ValueError('invalid keepout')
        polygon=[_point(p,'keepout polygon') for p in k['polygon']]
        if len(set(polygon))!=len(polygon):raise ValueError('keepout polygon repeats a vertex')
        if not isinstance(k['layers'],list) or not k['layers'] or any(x not in copper for x in k['layers']):raise ValueError('keepout layer unavailable in stackup')
    for key in ('netlist','schematic'):
        if not isinstance(data[key],str) or not data[key] or Path(data[key]).is_absolute() or '..' in Path(data[key]).parts:raise ValueError(f'invalid {key} path')
    return BoardDefinition(board_id,outline,float(radius),layers,float(thick),tuple(stack),tuple(data['mounting_holes']),tuple(data['keepouts']),tuple(data['domains']),tuple(data['placement_uids']),data['netlist'],data['schematic'])


def load_lock(path: Path):
    data=json.loads(path.read_text())
    if data['schema_version']!=1 or data['frame']['kicad_translation_mm']!={'x':100.0,'y':50.0}:raise ValueError('unexpected placement lock frame')
    by_uid={p['uid']:p for p in data['placements']}
    if len(by_uid)!=len(data['placements']):raise ValueError('duplicate lockfile UID')
    return by_uid


def selected_hardware(definition: BoardDefinition, lock: dict):
    selected=[]
    for uid in definition.placement_uids:
        if uid not in lock:raise ValueError(f'unknown placement UID {uid}')
        p=lock[uid]
        if p['domain'] not in definition.domains:raise ValueError(f'{uid}: domain not on board')
        selected.append(p)
    return selected
