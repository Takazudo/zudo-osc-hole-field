"""Mandatory successful native authority and finite-port selection for K.

This is a coupling-only diagnostic entry. It preserves all conductor geometry
and the complete own-load inventory, without setting those load currents to zero.
"""
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.core_model_gate import require_native_prerequisite


def enter(source, native_bytes, receipt_path, manifest_path, include_loads, port_limit):
    is_core = json.loads(native_bytes).get('board_id') == 'osc-core'
    if not is_core:
        if receipt_path is not None or manifest_path is not None:
            raise ValueError('K prerequisite arguments require the actual osc-core export')
        return None
    if receipt_path is None or manifest_path is None:
        raise ValueError('K conductor requires its successful native receipt and source manifest')
    if include_loads or port_limit:
        raise ValueError('K coupling diagnostic requires all 215 selected ports; use port-limit 0 without include-loads')
    result = require_native_prerequisite(source, receipt_path, manifest_path)
    expected = hashlib.sha256(native_bytes).hexdigest()
    if result['dependency_sha256'].get(str(Path(source).resolve())) != expected:
        raise ValueError('K prerequisite differs from the immutable conductor input')
    return result


def select_ports(geometry, prerequisite):
    """Retain exact certified ports; never remove native copper or load mapping."""
    if prerequisite is None:
        return
    if geometry['data']['board_id'] != 'osc-core':
        raise ValueError('K extracted board identity changed')
    expected = {(p['ref'], p['pad']): p for p in prerequisite['selected_contacts']}
    if len(expected) != 215 or len(prerequisite['selected_contacts']) != 215:
        raise ValueError('K selected prerequisite identities are not unique and complete')
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
        if (key in seen or p['kind'] != row['kind'] or p['layer'] != 0
                or row['native_layer'] != 'F.Cu' or physical is None
                or physical['uuid'] != row['uuid'] or physical['net'] != 'AGND'
                or set(physical['copper']) != {'F.Cu'}
                or physical['xy_mm'] != row['native_xy_mm']):
            raise ValueError('K selected physical port identity/face differs: ' + str(key))
        seen.add(key)
        selected.append(p)
    if seen != set(expected):
        raise ValueError('K extraction omitted selected coupling contacts')
    geometry['ports'] = selected


def verify_unchanged(prerequisite):
    if prerequisite is not None:
        for path, expected in prerequisite['dependency_sha256'].items():
            if hashlib.sha256(Path(path).read_bytes()).hexdigest() != expected:
                raise ValueError('K native prerequisite changed during diagnostic: ' + path)
