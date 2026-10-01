"""Build a disposable P ground prerequisite from its passing bare authority.

No candidate may pass with any rule/parity error or disconnected one of the
344 declared AGND contacts. Rail/signal routing remains issue 39 work.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pcbnew
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.prepare_source_planes import prepare
from scripts.pcbgen.extract_power_geometry import extract
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.control_ground_inventory import audit
from scripts.pcbgen.control_array_ownership import validate
from scripts.pcbgen.verify_local_links import blocks
from scripts.pcbgen.native_companion_binding import verify as verify_companions
from scripts.pcbgen.control_project_source import derive as derive_project
from scripts.pcbgen.control_hidden_field_preservation import restore as restore_hidden_fields


def resolve(name):
    path = Path(name)
    if str(path).startswith('/work/'):
        path = ROOT/path.relative_to('/work')
    elif not path.is_absolute():
        path = ROOT/path
    if not path.resolve().is_relative_to(ROOT):
        raise ValueError('P candidate dependency outside worktree')
    return path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(config_path, output, cache):
    if any(output.with_suffix(suffix).exists() for suffix in ('.kicad_pcb', '.kicad_pro', '.kicad_sch', '.kicad_dru')) or cache.exists() or output.name == 'osc-control.kicad_pcb':
        raise ValueError('Fresh disposable P candidate board and cache required')
    config_bytes = config_path.read_bytes()
    config = json.loads(config_bytes)
    inputs = {name: resolve(row['path']) for name, row in config['inputs'].items()}
    hashes = {str(config_path.resolve().relative_to(ROOT)): hashlib.sha256(config_bytes).hexdigest()}
    for name, path in inputs.items():
        expected = config['inputs'][name]['sha256']
        if digest(path) != expected:
            raise ValueError('P candidate configured input changed: '+name)
        hashes[str(path.relative_to(ROOT))] = expected
    receipt = json.loads(inputs['bare_receipt'].read_bytes())
    native = json.loads(inputs['bare_geometry'].read_bytes())
    manifest = json.loads(inputs['manifest'].read_bytes())
    plan = json.loads(inputs['main_via_plan'].read_bytes())
    if receipt['stage'] != 'bare_source_planning' or receipt['model_entry_allowed'] or receipt['rule_error_count'] or receipt['schematic_parity_count']:
        raise ValueError('Passing bare source-rule/parity authority required')
    source_authority = {resolve(name): expected for name, expected in receipt['source_sha256'].items()}
    artifact_authority = {resolve(name): expected for name, expected in receipt['artifacts_sha256'].items()}
    for name in ('manifest', 'definition'):
        if source_authority.get(inputs[name]) != digest(inputs[name]):
            raise ValueError('P configured source was not bound by the bare native receipt: '+name)
    for name in ('bare_geometry', 'bare_drc'):
        if artifact_authority.get(inputs[name]) != digest(inputs[name]):
            raise ValueError('P configured artifact was not bound by the bare native receipt: '+name)
    if resolve(native['board']) != inputs['bare_board'] or native['definition_sha256'] != digest(inputs['definition']) or manifest['definition_sha256'] != digest(inputs['definition']):
        raise ValueError('P configured board/definition authority mismatch')
    for source_map in (receipt['source_sha256'], receipt['artifacts_sha256'], plan['source_sha256']):
        for name, expected in source_map.items():
            path = resolve(name)
            if digest(path) != expected:
                raise ValueError('P upstream dependency changed: '+name)
            key = str(path.relative_to(ROOT))
            if key in hashes and hashes[key] != expected:
                raise ValueError('Inconsistent P upstream source digest')
            hashes[key] = expected
    if native['board_id'] != 'osc-control' or native['board_sha256'] != receipt['board_sha256'] or digest(inputs['bare_board']) != native['board_sha256']:
        raise ValueError('P bare board identity changed')
    drc = json.loads(inputs['bare_drc'].read_bytes())
    if drc['source'] != inputs['bare_board'].name or drc['kicad_version'] != '10.0.6' or drc['schematic_parity'] or any(row['severity'] == 'error' for row in drc['violations']):
        raise ValueError('Actual bare native DRC is not a passing same-board artifact')
    ownership = validate(plan, manifest, native)
    for name in ('build_control_ground_feasibility.py', 'control_array_ownership.py', 'control_ground_inventory.py',
                 'source_contact_inventory.py', 'prepare_source_planes.py', 'route_kicad.py', 'definition.py',
                 'uuid_tools.py', 'source_zones.py', 'source_copper.py', 'extract_power_geometry.py', 'ratsnest.py', 'verify_local_links.py', 'native_companion_binding.py', 'control_project_source.py', 'control_hidden_field_preservation.py'):
        path = ROOT/'scripts/pcbgen'/name
        key = str(path.relative_to(ROOT))
        value = digest(path)
        if key in hashes and hashes[key] != value:
            raise ValueError('P shared helper changed after upstream validation')
        hashes[key] = value
    for suffix in ('.kicad_pro', '.kicad_sch', '.kicad_dru'):
        path = inputs['bare_board'].with_suffix(suffix)
        hashes[str(path.relative_to(ROOT))] = digest(path)
    # These exact companions were certified at bare generation. Verify their
    # original bindings instead of hashing an arbitrary replacement as valid.
    if hashes[str(inputs['bare_board'].with_suffix('.kicad_pro').relative_to(ROOT))] != native['project_sha256']:
        raise ValueError('Bare project companion changed')
    if digest(inputs['bare_board'].with_suffix('.kicad_sch')) != hashes['boards/osc-control/osc-control.kicad_sch']:
        raise ValueError('Bare schematic companion changed')
    if digest(inputs['bare_board'].with_suffix('.kicad_dru')) != manifest['native_rule_sha256']:
        raise ValueError('Bare custom rule companion changed')
    project_bytes, project_derivation = derive_project(inputs['bare_board'].with_suffix('.kicad_pro').read_bytes(),
        inputs['definition'].read_bytes(), output.with_suffix('.kicad_pro').name)
    expected_companions = {
        str(output.with_suffix('.kicad_pro')): project_derivation['expected_project_sha256'],
        str(output.with_suffix('.kicad_sch')): hashes['boards/osc-control/osc-control.kicad_sch'],
        str(output.with_suffix('.kicad_dru')): manifest['native_rule_sha256'],
    }
    cache.mkdir(parents=True)
    for suffix in ('.kicad_sch', '.kicad_dru'):
        shutil.copyfile(inputs['bare_board'].with_suffix(suffix), output.with_suffix(suffix))
    output.with_suffix('.kicad_pro').write_bytes(project_bytes)
    board = pcbnew.LoadBoard(str(inputs['bare_board']))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    arrays = []
    for row in plan['rows']:
        pad = next(p for p in fps[row['ref']].Pads() if p.GetNumber() == '1')
        if pad.m_Uuid.AsString() != row['owning_pad_uuid'] or pad.GetNetname() != row['net']:
            raise ValueError('Actual native P array owner differs')
        ids = []
        for site in row['legal_sites']:
            via = pcbnew.PCB_VIA(board)
            via.SetViaType(pcbnew.VIATYPE_THROUGH)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(value) for value in site['xy_mm'])))
            via.SetWidth(pcbnew.FromMM(.7))
            via.SetDrill(pcbnew.FromMM(.3))
            via.SetNetCode(pad.GetNetCode())
            via.SetUuid(pcbnew.KIID(site['uuid']))
            board.Add(via)
            ids.append(site['uuid'])
        arrays.append({'ref': row['ref'], 'net': row['net'], 'via_uuids': ids})
    with tempfile.TemporaryDirectory(prefix='P-ground-arrays-', dir=cache) as directory:
        path = Path(directory)/'arrays.kicad_pcb'
        pcbnew.SaveBoard(str(path), board)
        prepare('osc-control', path, output, cache/'owned-ground-planes.json', inputs['definition'])
    preserved, hidden_field_receipt = restore_hidden_fields(output.read_text(), blocks(inputs['bare_board'])['footprint'])
    output.write_text(preserved)
    board_hash = digest(output)
    drc_path = cache/'ground-feasibility-drc.json'
    verify_companions(expected_companions)
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--schematic-parity', '--refill-zones', '--format', 'json',
                    '--severity-all', '-o', str(drc_path), str(output)], check=True)
    verify_companions(expected_companions)
    drc = json.loads(drc_path.read_bytes())
    if drc['source'] != output.name or drc['kicad_version'] != '10.0.6':
        raise ValueError('Wrong P candidate native oracle/board')
    geometry_path = cache/'ground-feasibility-geometry.json'
    extract('osc-control', output, geometry_path, inputs['definition'])
    geometry = json.loads(geometry_path.read_bytes())
    if geometry['project_sha256'] != expected_companions[str(output.with_suffix('.kicad_pro'))]:
        raise ValueError('P extracted candidate project differs from retained source authority')
    def old_items(data):
        return {row['uuid']: row for row in data['items'] if 'ref' in row}
    if old_items(native) != old_items(geometry):
        raise ValueError('P candidate altered an existing physical pad/net/face/UUID')
    old_holes = {row['uuid']: row for row in native['holes']}
    new_holes = {row['uuid']: row for row in geometry['holes']}
    if any(new_holes.get(uid) != row for uid, row in old_holes.items()):
        raise ValueError('P candidate altered an existing drilled feature')
    old_blocks, new_blocks = blocks(inputs['bare_board']), blocks(output)
    for kind in ('footprint', 'segment', 'arc'):
        if old_blocks[kind] != new_blocks[kind]:
            raise ValueError('P candidate changed original '+kind+' blocks')
    if any(new_blocks['zone'].get(uid) != value for uid, value in old_blocks['zone'].items()):
        raise ValueError('P candidate changed an original reservation/window')
    expected_vias = {site['uuid'] for row in plan['rows'] for site in row['legal_sites']}
    if set(new_blocks['via'])-set(old_blocks['via']) != expected_vias or set(new_holes)-set(old_holes) != expected_vias:
        raise ValueError('P added native vias/holes differ from explicit source plan')
    via_items = {row['uuid']: row for row in geometry['items'] if row['uuid'] in expected_vias}
    for row in plan['rows']:
        for site in row['legal_sites']:
            item, hole = via_items[site['uuid']], new_holes[site['uuid']]
            if item['net'] != row['net'] or hole['net'] != row['net'] or hole['size_mm'] != [.3, .3] or not hole['plated']:
                raise ValueError('P added via net or physical barrel differs from plan')
            if max(abs(a-b) for a, b in zip(site['xy_mm'], hole['xy_mm'])) > 1.001e-6 or set(item['copper']) != {'F.Cu', 'In1.Cu', 'In2.Cu', 'B.Cu'}:
                raise ValueError('P added via location or layer span differs from plan')
            if any(primitive['kind'] != 'circle' or primitive['half_size_nm'] != [350000, 350000] for primitive in item['analytic_primitives'].values()):
                raise ValueError('P added via annulus differs from plan')
    inventory = audit(geometry, manifest, json.loads((ROOT/'design/partition/partition.json').read_bytes()),
                      json.loads((ROOT/'design/reports/io-partition.json').read_bytes()), require_connected=False)
    rats = inspect(output)
    rats_path = cache/'ground-feasibility-ratsnest.json'
    rats_path.write_text(json.dumps(rats, indent=2, sort_keys=True)+'\n')
    errors = [row for row in drc['violations'] if row['severity'] == 'error']
    connected = set(geometry['main_rail_members']['AGND'])
    if digest(output) != board_hash or any(digest(resolve(path)) != expected for path, expected in hashes.items()):
        raise ValueError('P candidate source/native dependency changed')
    verify_companions(expected_companions)
    ground_vias = {uid for row in arrays if row['net'] == 'AGND' for uid in row['via_uuids']}
    passed = not errors and not drc['schematic_parity'] and not inventory['disconnected'] and ground_vias <= connected
    report = {'status': 'PASS native P ground prerequisite only' if passed else 'FAIL native P prerequisite; model entry prohibited',
        'board_id': 'osc-control', 'board_sha256': board_hash, 'source_sha256': hashes,
        'companion_sha256': {str(resolve(path).relative_to(ROOT)): value for path, value in expected_companions.items()},
        'project_source_derivation': project_derivation,
        'exact_hidden_field_preservation': hidden_field_receipt,
        'rule_error_count': len(errors), 'schematic_parity_count': len(drc['schematic_parity']),
        'warning_count': sum(row['severity'] == 'warning' for row in drc['violations']),
        'source_ground_inventory': inventory, 'arrays': arrays, 'array_ownership': ownership,
        'source_footprint_origins': receipt['source_footprint_origins'],
        'all_prior_footprints_pads_holes_exact': True, 'all_prior_reservations_exact': True,
        'new_array_via_count': len(expected_vias),
        'ground_array_vias_connected': sum(uid in connected for row in arrays if row['net'] == 'AGND' for uid in row['via_uuids']),
        'full_named_open_edges': rats['native_unconnected_edges'],
        'native_model_prerequisite_passed': passed,
        'artifacts_sha256': {str(path.relative_to(ROOT) if path.is_absolute() else path): digest(path) for path in
                            (drc_path, geometry_path, rats_path, cache/'owned-ground-planes.json')},
        'scope': 'UNSELECTED prerequisite only. All344 own-load/GH/main AGND contacts must connect. Rail/signal routing remains issue39; actual current, contact, material, common/K and voltage acceptance remain OPEN.'}
    (cache/'ground-feasibility-native-receipt.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print('P ground candidate:', len(errors), 'rule errors,', len(drc['schematic_parity']), 'parity,', inventory['connected_count'], '/344 ground contacts connected', flush=True)
    if not passed:
        raise ValueError('P candidate failed actual native geometry/parity/full ground continuity')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('config', 'output', 'cache'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    build(args.config, args.output, args.cache)
