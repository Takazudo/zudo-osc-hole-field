"""Mandatory native authority and exact nominal port selection for K."""
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.core_model_gate import require_native_prerequisite
from scripts.pcbgen.core_full_ground_inventory import verify as verify_full_inventory


def enter(source, native_bytes, receipt_path, manifest_path, include_loads, port_limit, main_strands=False):
    own_path=str(Path(__file__).resolve())
    own_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    is_core = json.loads(native_bytes).get('board_id') == 'osc-core'
    if not is_core:
        if receipt_path is not None or manifest_path is not None:
            raise ValueError('K prerequisite arguments require the actual osc-core export')
        return None
    if receipt_path is None or manifest_path is None:
        raise ValueError('K conductor requires its successful native receipt and source manifest')
    if port_limit or not isinstance(include_loads,bool):
        raise ValueError('K diagnostic requires port-limit 0 and an explicit load mode')
    if include_loads:
        if not main_strands:
            raise ValueError('K full diagnostic requires nineteen-support main strands')
        result=verify_full_inventory(source,receipt_path,manifest_path)
        if result['source_sha256'].get(str(Path(source).resolve()))!=hashlib.sha256(native_bytes).hexdigest():
            raise ValueError('K full inventory differs from the immutable conductor input')
        if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=own_hash:
            raise ValueError('K model entry changed during full admission')
        result['source_sha256'][own_path]=own_hash
        return result
    result = require_native_prerequisite(source, receipt_path, manifest_path)
    expected = hashlib.sha256(native_bytes).hexdigest()
    if result['dependency_sha256'].get(str(Path(source).resolve())) != expected:
        raise ValueError('K prerequisite differs from the immutable conductor input')
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=own_hash:
        raise ValueError('K model entry changed during coupling admission')
    result['dependency_sha256'][own_path]=own_hash
    return result


def select_ports(geometry, prerequisite):
    """Retain exact certified ports; never remove native copper or load mapping."""
    if prerequisite is None:
        return
    if geometry['data']['board_id'] != 'osc-core':
        raise ValueError('K extracted board identity changed')
    full='contacts' in prerequisite
    contacts=prerequisite['contacts'] if full else prerequisite['selected_contacts']
    expected = {(p['ref'], p['pad']): p for p in contacts}
    required=2288 if full else 215
    if len(expected)!=required or len(contacts)!=required:
        raise ValueError('K prerequisite identities are not unique and complete')
    native_pads = [p for p in geometry['data']['items'] if 'ref' in p]
    native = {(p['ref'], p['pad']): p for p in native_pads}
    if len(native) != len(native_pads):
        raise ValueError('K native pad identities are duplicated')
    selected = []
    seen = set()
    for p in geometry['ports']:
        key = p['ref'], p['pad']
        if key not in expected:
            continue
        row = expected[key]
        physical = native.get(key)
        face=row['physical_layer'] if full else row['native_layer']
        physical_index=geometry['physical_foil_layers'].index(face) if full else 0
        active_index=geometry['physical_to_active_sheet'][face] if full else 0
        if (key in seen or p['kind'] != row['kind'] or p['layer'] != active_index
                or (p.get('physical_layer')!=face if full else face!='F.Cu') or physical is None
                or physical['uuid'] != row['uuid'] or physical['net'] != 'AGND'
                or (face not in physical['copper'] if full else set(physical['copper']) != {'F.Cu'})
                or physical['xy_mm'] != row['native_xy_mm']):
            raise ValueError('K selected physical port identity/face differs: ' + str(key))
        if full and (p.get('physical_foil_index')!=physical_index or p.get('source_face')!=('top' if face=='F.Cu' else 'bottom')):
            raise ValueError('K full port physical face mapping differs: '+str(key))
        if full and row['kind']=='main' and (p.get('strand_count')!=19 or p.get('maximum_wetting') is None):
            raise ValueError('K full main requires nineteen supported numerical strands: '+str(key))
        seen.add(key)
        selected.append(p)
    if seen != set(expected):
        raise ValueError('K extraction omitted required contacts')
    geometry['ports'] = selected


def verify_unchanged(prerequisite):
    if prerequisite is not None:
        hashes=prerequisite['source_sha256'] if 'contacts' in prerequisite else prerequisite['dependency_sha256']
        for path, expected in hashes.items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
                raise ValueError('K native prerequisite changed during diagnostic: ' + path)
