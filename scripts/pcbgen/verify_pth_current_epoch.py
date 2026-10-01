"""Transfer the historical fitted AGND PTH nominal cover to current J/P/K.

Exact local source geometry is the sole conclusion. The conditional project
plating wall is not finished-copper, source-flux, or electrical evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.control_model_gate import require_native_prerequisite as require_p
from scripts.pcbgen.core_model_gate import require_native_prerequisite as require_k
from scripts.pcbgen.verify_jack_source_geometry_epoch import verify as verify_j

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / '.circuit-cache/issue38-recovery'
HISTORICAL = {
    'pth': ('pth-source-geometry-certificate-v2.json', '777af6fb22334f140a9b4a649e843c62957ed093ba4004835f45933d330cd245'),
    'mapping': ('own-source-flux-boundaries-v2.json', 'bc766e053d76791c68afd41f65ea9ce184b93fdf11725d9b019c7d018e9b9ad4'),
}
CURRENT = {
    'osc-control': ('control-feasibility-v4', 'design/partition/control-ground-feasibility/osc-control.receipt.json', require_p),
    'osc-core': ('core-feasibility-v7', 'design/partition/core-ground-feasibility/osc-core.receipt.json', require_k),
}
J_BRIDGE = CACHE / 'jack-ground-source-epoch-bridge-v4.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_bound(path, sources, *, parse_json=True):
    path = Path(path)
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError('PTH dependency outside worktree')
    data = path.read_bytes()
    name = str(path.relative_to(ROOT))
    value = digest(data)
    if name in sources and sources[name] != value:
        raise ValueError('PTH dependency digest conflict: ' + name)
    sources[name] = value
    return json.loads(data) if parse_json else data


def pads(native):
    rows = [item for item in native['items'] if item.get('ref') and item['net'] == 'AGND']
    keyed = {(item['ref'], item['pad']): item for item in rows}
    if len(keyed) != len(rows):
        raise ValueError('duplicate native AGND pad identity')
    return keyed


def compare_local_epoch(old, current):
    if old['board_id'] != current['board_id'] or old['kicad_version'] != '10.0.6' or current['kicad_version'] != '10.0.6':
        raise ValueError('wrong native board or KiCad oracle')
    for key in ('holes', 'outline_mm', 'stackup'):
        if old[key] != current[key]:
            raise ValueError('PTH source geometry changed: ' + key)
    before, after = pads(old), pads(current)
    if before != after:
        raise ValueError('PTH native AGND source pad identity or primitive changed')
    return after


def check_rows(rows, native, expected):
    source = pads(native)
    holes = {row['uuid']: row for row in native['holes']}
    if len(holes) != len(native['holes']):
        raise ValueError('duplicate native drill identity')
    keys = set()
    for row in rows:
        key = (row['ref'], row['pad'])
        if key in keys or key not in expected:
            raise ValueError('duplicate or non-fitted PTH cover identity')
        keys.add(key)
        item = source.get(key)
        if item is None or row['net'] != 'AGND' or row['uuid'] != item['uuid'] or row['native_hole'] != holes.get(item['uuid']):
            raise ValueError('PTH nominal cover pad/drill differs from current native source')
        faces = {face['layer']: face['native_primitive'] for face in row['foil_faces']}
        if len(faces) != len(row['foil_faces']) or faces != item['analytic_primitives']:
            raise ValueError('PTH nominal cover foil primitive differs from current native source')
        if row['board_sha256'] != expected[key]['historical_board_sha256'] or row['native_export_sha256'] != expected[key]['historical_native_sha256']:
            raise ValueError('PTH cover belongs to another historical epoch')
    return keys


def verify():
    own_source = digest(Path(__file__).read_bytes())
    sources = {'scripts/pcbgen/verify_pth_current_epoch.py': own_source}
    historical = {}
    for label, (name, expected_sha) in HISTORICAL.items():
        path = CACHE / name
        historical[label] = read_bound(path, sources)
        if sources[str(path.relative_to(ROOT))] != expected_sha:
            raise ValueError('historical PTH authority changed: ' + label)
    cert = historical['pth']
    if (cert['certified_nominal_geometry_count'] != 305 or cert['unresolved_count'] != 0
            or cert['actual_finished_plating_qualified_count'] != 0 or len(cert['certificates']) != 305):
        raise ValueError('historical PTH certificate scope changed')
    # The historical certificate freezes its own source closure. Model and
    # generator source code has since advanced; rechecking old code digests
    # against current code would falsely claim that old evidence is current.
    for board_id in ('osc-control', 'osc-core'):
        group = next(row for row in historical['mapping']['boards'] if row['board_id'] == board_id)
        if cert['source_sha256'].get(group['native_export_path']) != group['native_export_sha256']:
            raise ValueError('historical PTH certificate lacks native export binding')
    j_receipt = read_bound(J_BRIDGE, sources)
    if verify_j() != j_receipt:
        raise ValueError('current J geometry bridge no longer verifies')
    for name, value in j_receipt['source_sha256'].items():
        if name in sources and sources[name] != value:
            raise ValueError('J PTH source dependency conflict: ' + name)
        sources[name] = value
    rows_by_board = {}
    for row in cert['certificates']:
        rows_by_board.setdefault(row['board_id'], []).append(row)
    if set(rows_by_board) != {'osc-jack-left', 'osc-jack-right', *CURRENT}:
        raise ValueError('PTH certificate board set changed')
    summary = {}
    expected_counts = {'osc-jack-left': 100, 'osc-jack-right': 80, 'osc-control': 120, 'osc-core': 5}
    for board_id, (folder, manifest, native_gate) in CURRENT.items():
        group = next((row for row in historical['mapping']['boards'] if row['board_id'] == board_id), None)
        if group is None:
            raise ValueError('historical source inventory board absent: ' + board_id)
        old_path = ROOT / group['native_export_path']
        current_dir = CACHE / folder
        new_path = current_dir / 'ground-feasibility-geometry.json'
        receipt_path = current_dir / 'ground-feasibility-native-receipt.json'
        old = read_bound(old_path, sources)
        current = read_bound(new_path, sources)
        native_receipt = read_bound(receipt_path, sources)
        authority = native_gate(new_path, receipt_path, ROOT / manifest)
        if not authority['dependency_sha256'] or native_receipt['board_sha256'] != current['board_sha256']:
            raise ValueError('current native authority incomplete')
        for path, value in authority['dependency_sha256'].items():
            name = str(Path(path).relative_to(ROOT))
            if name in sources and sources[name] != value:
                raise ValueError('native source dependency conflict: ' + name)
            sources[name] = value
        if (group['native_export_sha256'] != sources[str(old_path.relative_to(ROOT))]
                or group['board_sha256'] != old['board_sha256']):
            raise ValueError('historical source inventory binding changed')
        for native in (old, current):
            board = ROOT / native['board']
            read_bound(board, sources, parse_json=False)
            if sources[str(board.relative_to(ROOT))] != native['board_sha256']:
                raise ValueError('native board bytes differ from export')
        items = compare_local_epoch(old, current)
        own = group['own_source_contacts']
        expected = {(row['ref'], row['pad']): {
            'historical_board_sha256': group['board_sha256'],
            'historical_native_sha256': group['native_export_sha256'],
        } for row in own if row['family'] == 'PTH'}
        if len(expected) != sum(row['family'] == 'PTH' for row in own):
            raise ValueError('duplicate fitted PTH source identity')
        inventory = native_receipt['source_ground_inventory']
        contacts = inventory['contacts'] if board_id == 'osc-control' else inventory['source_fitted_AGND_mapping']
        current_own = {(row['ref'], row['pad'], row['uuid']) for row in contacts
                       if board_id == 'osc-core' or row['kind'] == 'own_load'}
        if len(current_own) != inventory['source_fitted_AGND_count']:
            raise ValueError('current fitted source inventory count differs')
        if any((ref, pad, items[ref, pad]['uuid']) not in current_own for ref, pad in expected):
            raise ValueError('current fitted PTH source identity differs')
        covered = check_rows(rows_by_board[board_id], current, expected)
        if covered != set(expected) or len(covered) != expected_counts[board_id]:
            raise ValueError('current PTH fitted cover population differs')
        summary[board_id] = {'nominal_PTH_source_geometry_records': len(covered),
                             'historical_board_sha256': old['board_sha256'],
                             'current_board_sha256': current['board_sha256'],
                             'native_AGND_pads_exact': len(items),
                             'native_holes_exact': len(current['holes'])}
    for board_id in ('osc-jack-left', 'osc-jack-right'):
        if j_receipt['boards'][board_id]['PTH_nominal_face_wall_records'] != expected_counts[board_id]:
            raise ValueError('J PTH cover count differs')
        summary[board_id] = {'nominal_PTH_source_geometry_records': expected_counts[board_id],
                             'delegated_exact_epoch_bridge_sha256': sources[str(J_BRIDGE.relative_to(ROOT))]}
    for name, expected in sources.items():
        if digest((ROOT / name).read_bytes()) != expected:
            raise ValueError('PTH input changed during comparison: ' + name)
    return {'status': 'PASS exact current-epoch local nominal PTH source geometry only',
            'source_sha256': sources, 'boards': summary, 'nominal_geometry_record_count': 305,
            'physical_wall_flux_contact_or_electrical_accepted_count': 0,
            'scope': 'Historical local PTH foil and conditional project wall geometry matches current J/P/K source pads, drills, outline and stack. Finished plating, contact, 3D/primal, material, source flux, current and joined electrical acceptance remain OPEN. Historical model results are not rebound.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('fresh PTH current-epoch receipt required')
    report = verify()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(report['status'], {board: row['nominal_PTH_source_geometry_records'] for board, row in report['boards'].items()})
