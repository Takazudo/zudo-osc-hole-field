"""Require the actual complete P native prerequisite before model entry.

Neither a zero-error bare board nor a partial selected-port report is enough.
All 344 declared source ground contacts and all added ground vias must connect.
This gate does not accept a physical contact/current/material class.
"""
import hashlib
import json
from pathlib import Path
from scripts.pcbgen.control_ground_inventory import audit
from scripts.pcbgen.control_project_source import derive as derive_project

ROOT = Path(__file__).resolve().parents[2]


def resolve(name):
    path = Path(name)
    if str(path).startswith('/work/'):
        path = ROOT/path.relative_to('/work')
    elif not path.is_absolute():
        path = ROOT/path
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError('P model dependency lies outside worktree')
    return path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_native_prerequisite(native_path, receipt_path, manifest_path):
    native_path, receipt_path, manifest_path = map(resolve, (native_path, receipt_path, manifest_path))
    receipt_bytes = receipt_path.read_bytes()
    receipt = json.loads(receipt_bytes)
    if receipt.get('board_id') != 'osc-control' or receipt.get('native_model_prerequisite_passed') is not True or receipt.get('rule_error_count') != 0 or receipt.get('schematic_parity_count') != 0:
        raise ValueError('P model requires the successful full native prerequisite, never a bare or failed export')
    hashes = {str(receipt_path): hashlib.sha256(receipt_bytes).hexdigest()}
    for group in ('source_sha256', 'artifacts_sha256'):
        if not receipt.get(group):
            raise ValueError('P native receipt lacks complete source/artifact provenance')
        for name, expected in receipt[group].items():
            path = resolve(name)
            if digest(path) != expected:
                raise ValueError('P prerequisite dependency changed: '+name)
            if str(path) in hashes and hashes[str(path)] != expected:
                raise ValueError('P prerequisite dependency digest conflict')
            hashes[str(path)] = expected
    if str(native_path) not in hashes or str(manifest_path) not in hashes:
        raise ValueError('P model export or source manifest is not bound by the native receipt')
    native = json.loads(native_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    if native['board_id'] != 'osc-control' or native['kicad_version'] != '10.0.6' or native['board_sha256'] != receipt['board_sha256']:
        raise ValueError('P native board/oracle identity changed')
    board = resolve(native['board'])
    actual_drc_paths = [resolve(path) for path in receipt['artifacts_sha256'] if path.endswith('ground-feasibility-drc.json')]
    if len(actual_drc_paths) != 1:
        raise ValueError('P prerequisite needs one exact full native DRC artifact')
    drc = json.loads(actual_drc_paths[0].read_bytes())
    if drc['source'] != board.name or drc['kicad_version'] != '10.0.6' or drc['schematic_parity'] or any(row['severity'] == 'error' for row in drc['violations']):
        raise ValueError('P full same-board native DRC artifact does not pass')
    schematic = ROOT/'boards/osc-control/osc-control.kicad_sch'
    if str(schematic) not in hashes:
        raise ValueError('P source schematic authority is absent')
    derivation = receipt.get('project_source_derivation')
    if not derivation:
        raise ValueError('P native receipt lacks source-derived project authority')
    original_projects = [Path(path) for path, value in hashes.items()
                         if path.endswith('.kicad_pro') and value == derivation['bare_project_sha256']]
    if not manifest_path.name.endswith('.receipt.json'):
        raise ValueError('P source manifest filename is not a definition receipt')
    definition_path = manifest_path.with_name(manifest_path.name.removesuffix('.receipt.json')+'.json')
    if len(original_projects) != 1 or str(definition_path) not in hashes:
        raise ValueError('P generated project lacks exact bare/definition source inputs')
    expected_project, expected_derivation = derive_project(original_projects[0].read_bytes(),
        definition_path.read_bytes(), board.with_suffix('.kicad_pro').name)
    if expected_derivation != derivation or expected_project != board.with_suffix('.kicad_pro').read_bytes():
        raise ValueError('P candidate project differs from its exact source derivation')
    companions = {str(board): native['board_sha256'],
        str(board.with_suffix('.kicad_pro')): native['project_sha256'],
        str(board.with_suffix('.kicad_sch')): hashes[str(schematic)],
        str(board.with_suffix('.kicad_dru')): manifest['native_rule_sha256']}
    for path, expected in companions.items():
        if digest(path) != expected:
            raise ValueError('P candidate board or copied companion changed: '+path)
        hashes[path] = expected
    copied = {str(resolve(path)): expected for path, expected in receipt.get('companion_sha256', {}).items()}
    if copied != {path: value for path, value in companions.items() if path != str(board)}:
        raise ValueError('P copied companion receipt differs from retained source authority')
    partition_path = ROOT/'design/partition/partition.json'
    io_path = ROOT/'design/reports/io-partition.json'
    for path in (partition_path, io_path):
        if str(path) not in hashes:
            raise ValueError('P complete source inventory is absent from native authority')
    inventory = audit(native, manifest, json.loads(partition_path.read_bytes()), json.loads(io_path.read_bytes()))
    if inventory != receipt['source_ground_inventory'] or inventory['connected_count'] != 344:
        raise ValueError('P full source/native inventory differs from the passing receipt')
    ground_vias = {uid for row in receipt['arrays'] if row['net'] == 'AGND' for uid in row['via_uuids']}
    if not ground_vias <= set(native['main_rail_members']['AGND']) or len(ground_vias) != receipt['ground_array_vias_connected']:
        raise ValueError('P declared ground arrays are not all connected')
    for name in ('control_model_gate.py', 'control_ground_inventory.py', 'source_contact_inventory.py', 'control_project_source.py'):
        path = ROOT/'scripts/pcbgen'/name
        expected = digest(path)
        if str(path) in hashes and hashes[str(path)] != expected:
            raise ValueError('P inventory helper changed during model entry')
        hashes[str(path)] = expected
    if any(digest(path) != expected for path, expected in hashes.items()):
        raise ValueError('P authority changed during model entry')
    return {'status': 'PASS complete P native prerequisite only; physical/electrical source adoption OPEN',
        'dependency_sha256': hashes, 'full_source_ground_inventory': inventory,
        'selected_contacts': [row for row in inventory['contacts'] if row['kind'] in ('GH', 'main')],
        'own_load_scope': 'All214 P own-load contacts remain represented in native geometry and the source current ledger. A coupling-only function basis does not set their currents to zero.'}
