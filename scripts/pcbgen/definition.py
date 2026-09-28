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
    regions: tuple[dict, ...] = ()
    routing: dict | None = None


def _point(raw, name):
    if not isinstance(raw,(list,tuple)) or len(raw)!=2 or any(isinstance(v,bool) or not isinstance(v,(int,float)) for v in raw):
        raise ValueError(f'{name}: expected [x_mm,y_mm]')
    return float(raw[0]),float(raw[1])


def load_definition(path: Path) -> BoardDefinition:
    data=json.loads(path.read_text())
    required={'schema_version','board_id','outline','corner_radius_mm','layers','thickness_mm','stackup','mounting_holes','keepouts','domains','placement_uids','netlist','schematic'}
    if not required.issubset(data) or set(data)-required-{'regions','routing'} or data['schema_version']!=1:raise ValueError('board definition keys/version mismatch')
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
    regions=data.get('regions',[])
    if not isinstance(regions,list):raise ValueError('regions must be a list')
    for region in regions:
        keys={'instance','family','rect','side','edge_clearance_mm','mounting_clearance_mm'}
        if not isinstance(region,dict) or set(region)!=keys:raise ValueError('invalid region keys')
        if any(not isinstance(region[k],str) or not region[k] for k in ('instance','family')):raise ValueError('invalid region identity')
        if region['side'] not in ('F.Cu','B.Cu'):raise ValueError('invalid region side')
        box=region['rect']
        if not isinstance(box,list) or len(box)!=4 or any(isinstance(x,bool) or not isinstance(x,(int,float)) for x in box) or box[0]>=box[2] or box[1]>=box[3]:raise ValueError('invalid region rect')
        for key in ('edge_clearance_mm','mounting_clearance_mm'):
            if isinstance(region[key],bool) or not isinstance(region[key],(int,float)) or region[key]<0:raise ValueError('invalid '+key)
    routing=data.get('routing')
    if routing is not None:
        if not isinstance(routing,dict) or set(routing)!={'min_track_width_mm','net_classes','zones'}:raise ValueError('invalid routing keys')
        if isinstance(routing['min_track_width_mm'],bool) or not isinstance(routing['min_track_width_mm'],(int,float)) or routing['min_track_width_mm']<=0:raise ValueError('invalid minimum track width')
        if not isinstance(routing['net_classes'],list) or not routing['net_classes']:raise ValueError('routing needs net classes')
        seen=set()
        for cls in routing['net_classes']:
            if not isinstance(cls,dict) or set(cls)!={'name','nets','track_width_mm','clearance_mm','via_diameter_mm','via_drill_mm'}:raise ValueError('invalid net class')
            if not isinstance(cls['name'],str) or not cls['name'] or cls['name'] in seen:raise ValueError('duplicate/blank net class')
            seen.add(cls['name'])
            if not isinstance(cls['nets'],list) or any(not isinstance(n,str) or not n for n in cls['nets']):raise ValueError('invalid class nets')
            for key in ('track_width_mm','clearance_mm','via_diameter_mm','via_drill_mm'):
                if isinstance(cls[key],bool) or not isinstance(cls[key],(int,float)) or cls[key]<=0:raise ValueError('invalid '+key)
            if cls['via_drill_mm']>=cls['via_diameter_mm']:raise ValueError('via drill must be smaller than diameter')
        if not isinstance(routing['zones'],list):raise ValueError('invalid routing zones')
        for zone in routing['zones']:
            if not isinstance(zone,dict) or set(zone) not in ({'name','net','layers','clearance_mm','min_thickness_mm'},{'name','net','layers','clearance_mm','min_thickness_mm','pad_connection'}):raise ValueError('invalid routing zone')
            if zone.get('pad_connection','thermal') not in ('thermal','full'):raise ValueError('invalid zone pad connection')
            if not isinstance(zone['name'],str) or not zone['name'] or not isinstance(zone['net'],str) or not zone['net']:raise ValueError('invalid zone identity')
            if not isinstance(zone['layers'],list) or not zone['layers'] or any(layer not in copper for layer in zone['layers']):raise ValueError('invalid zone layers')
            for key in ('clearance_mm','min_thickness_mm'):
                if isinstance(zone[key],bool) or not isinstance(zone[key],(int,float)) or zone[key]<=0:raise ValueError('invalid zone '+key)
    return BoardDefinition(board_id,outline,float(radius),layers,float(thick),tuple(stack),tuple(data['mounting_holes']),tuple(data['keepouts']),tuple(data['domains']),tuple(data['placement_uids']),data['netlist'],data['schematic'],tuple(regions),routing)


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
