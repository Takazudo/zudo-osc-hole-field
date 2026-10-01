"""Mandatory full native P authority and exact optional own-load profile set."""
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.control_model_gate import require_native_prerequisite


def enter(source, native_bytes, receipt_path, manifest_path, include_loads, port_limit):
    is_control = json.loads(native_bytes).get('board_id') == 'osc-control'
    if not is_control:
        if receipt_path is not None or manifest_path is not None:
            raise ValueError('P prerequisite arguments require the actual osc-control export')
        return None
    if receipt_path is None or manifest_path is None:
        raise ValueError('P conductor requires its successful full native receipt and source manifest')
    if port_limit:
        raise ValueError('P diagnostic requires all source coupling contacts; use port-limit 0')
    result = require_native_prerequisite(source, receipt_path, manifest_path)
    if result['dependency_sha256'].get(str(Path(source).resolve())) != hashlib.sha256(native_bytes).hexdigest():
        raise ValueError('P prerequisite differs from immutable conductor input')
    result['diagnostic_include_loads'] = bool(include_loads)
    return result


def select_ports(geometry, prerequisite):
    if prerequisite is None:
        return
    if geometry['data']['board_id'] != 'osc-control':
        raise ValueError('P extracted board identity changed')
    include = prerequisite['diagnostic_include_loads']
    rows = prerequisite['full_source_ground_inventory']['contacts'] if include else prerequisite['selected_contacts']
    expected = {(row['ref'], row['pad']): row for row in rows}
    count = 344 if include else 130
    if len(rows) != count or len(expected) != count:
        raise ValueError('P complete diagnostic contact set is missing or duplicated')
    physical = [row for row in geometry['data']['items'] if 'ref' in row]
    native = {(row['ref'], row['pad']): row for row in physical}
    if len(native) != len(physical):
        raise ValueError('P native pad identities are duplicated')
    seen = set()
    for port in geometry['ports']:
        key = port['ref'], port['pad']
        if key not in expected or key in seen:
            raise ValueError('Unexpected or duplicated P diagnostic port')
        row, pad = expected[key], native.get(key)
        kind = 'load' if row['kind'] == 'own_load' else row['kind']
        # Through-hole own loads have several real foil contacts. The fixed
        # numerical profile uses B when present, exactly as the extractor;
        # this does not assert actual package-current injection on that face.
        layer = 3 if 'B.Cu' in row['native_layers'] else 0
        if pad is None or pad['uuid'] != row['uuid'] or pad['net'] != 'AGND' or sorted(pad['copper']) != row['native_layers'] or port['kind'] != kind or port['layer'] != layer:
            raise ValueError('P diagnostic physical identity/foil/kind changed: '+str(key))
        if kind in ('GH', 'main') and (row['native_layers'] != ['B.Cu'] or layer != 3):
            raise ValueError('P coupling contact lost its actual B-side foil')
        seen.add(key)
    if seen != set(expected):
        raise ValueError('P extraction omitted required source contact functions')


def verify_unchanged(prerequisite):
    if prerequisite is not None:
        for path, expected in prerequisite['dependency_sha256'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
                raise ValueError('P prerequisite changed during diagnostic: '+path)
