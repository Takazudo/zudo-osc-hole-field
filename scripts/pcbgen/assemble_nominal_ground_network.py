"""Source-bound ten-board ground composition, strictly a nominal diagnostic.

No scalar wire value or numerical PCB patch in this program is a physical
terminal trace. In particular, its two matrix compositions are not paired
continuum bounds and cannot establish any current or voltage acceptance.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.pcbgen.network_port_composition import compose


MODEL_FILES = frozenset('''active_foil_domains.py barrel_volume.py batch_checkpoint_store.py
conserved_flow.py contact_constraints.py contact_transfer.py control_ground_inventory.py
control_model_entry.py control_model_gate.py control_project_source.py copper_envelope.py
core_full_ground_inventory.py core_ground_inventory.py core_model_entry.py core_model_gate.py
current_j_rail_entry.py current_trial_matrix.py design/partition/contact-transfer-proposal.json
design/reports/io-partition.json foil_stack.py generate_peripheral_ground.py
ground_reference.py ground_volume_geometry.py jack_model_entry.py jack_white_current_binding.py
peripheral_ground_inventory.py peripheral_model_entry.py peripheral_project_source.py
positive_energy_bound.py potential_refinement.py potential_trial_matrix.py
propose_rail_transfers.py residual_work.py selected_conductor_export.py shared_interface.py
sheet_conservation.py sheet_flux.py sheet_mesh.py sheet_volume.py solve_conductor_volume.py
solve_ground_interfaces.py source_contact_inventory.py terminal_face.py trial_energy.py'''.split())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                     allow_nan=False).encode('ascii')
    return hashlib.sha256(raw).hexdigest()


def dependency_path(root, name):
    path = Path(name)
    if str(path).startswith('/work/'):
        path = Path(root) / path.relative_to('/work')
    elif not path.is_absolute():
        path = Path(root) / path
    path = path.resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('native authority dependency outside current worktree: ' + name)
    return path


def current_model_hashes(root):
    root = Path(root)
    return {name: digest(root / (name if name.startswith('design/') else 'scripts/pcbgen/' + name))
            for name in MODEL_FILES}


def check_graph(graph, root, full=True):
    if full:
        if len(graph['contacts']) != 4921 or len(graph['wire_edges']) != 389 or len(graph['board_source_ids']) != 10:
            raise ValueError('current ten-board ground inventory count differs')
        if graph['counts']['source_own_load_contacts'] != {
                'JL': 1070, 'JR': 896, 'P': 214, 'K': 1903, 'EL': 60,
                **{f'O{i}': 0 for i in range(1, 6)}}:
            raise ValueError('current own-load inventory differs')
        for name, expected in graph['source_sha256'].items():
            if digest(Path(root) / name) != expected:
                raise ValueError('ground incidence source changed: ' + name)
        if digest(Path(root) / 'scripts/pcbgen/ground_network_incidence.py') != graph['generator_sha256']:
            raise ValueError('ground incidence generator changed')
    contacts = {row['id']: row for row in graph['contacts']}
    if len(contacts) != len(graph['contacts']):
        raise ValueError('duplicate graph contact')
    boards = graph['board_source_ids']
    if set(boards) != {row['board'] for row in contacts.values()}:
        raise ValueError('graph board contact coverage differs')
    edges = graph['wire_edges']
    if len({row['id'] for row in edges}) != len(edges):
        raise ValueError('duplicate graph wire')
    for edge in edges:
        a, b = edge['from_contact'], edge['to_contact']
        if a not in contacts or b not in contacts or a == b:
            raise ValueError('wire endpoint is not a distinct graph contact')
        if edge['incidence'] != {a: -1, b: 1}:
            raise ValueError('wire signed incidence differs')
    return contacts


def check_board(board, graph, result, native, profile, model_hashes,
                full=True, root='.', native_path=None):
    expected_board = graph['board_source_ids'][board]
    if native['board_id'] != expected_board:
        raise ValueError(f'{board}: native board identity differs')
    if result['model_source_sha256'] != model_hashes or profile['model_source_sha256'] != model_hashes:
        raise ValueError(f'{board}: historical or incomplete model source epoch')
    if result['native_export_sha256'] != profile['native_export_sha256']:
        raise ValueError(f'{board}: profile/native digest differs')
    if result['board_sha256'] != native['board_sha256']:
        raise ValueError(f'{board}: native board digest differs')
    if result['status'] != 'NOT ACCEPTED: nominal finite-profile full-native diagnostic only':
        raise ValueError(f'{board}: unexpected nominal receipt status')
    if full:
        prerequisite = ('jack' if board in ('JL', 'JR') else 'core' if board == 'K'
                        else 'control' if board == 'P' else 'peripheral') + '_native_prerequisite'
        for key in ('jack_native_prerequisite', 'core_native_prerequisite',
                    'control_native_prerequisite', 'peripheral_native_prerequisite'):
            if result.get(key) != profile.get(key):
                raise ValueError(f'{board}: profile/native authority differs')
            if key != prerequisite and result.get(key) is not None:
                raise ValueError(f'{board}: foreign native prerequisite')
        authority = result.get(prerequisite)
        if not isinstance(authority, dict):
            raise ValueError(f'{board}: required native authority absent')
        dependency_hashes = authority.get('source_sha256' if board == 'K' else 'dependency_sha256')
        if not isinstance(dependency_hashes, dict) or not dependency_hashes:
            raise ValueError(f'{board}: native authority source closure absent')
        resolved = {}
        for name, expected in dependency_hashes.items():
            path = dependency_path(root, name)
            if path in resolved and resolved[path] != expected:
                raise ValueError(f'{board}: contradictory native authority dependencies')
            resolved[path] = expected
            if digest(path) != expected:
                raise ValueError(f'{board}: native authority dependency changed: {name}')
        if native_path is None or resolved.get(Path(native_path).resolve()) != result['native_export_sha256']:
            raise ValueError(f'{board}: native export absent from authority closure')
        if board != 'P' and authority.get('board_id') != expected_board:
            raise ValueError(f'{board}: native authority board identity differs')
        if board == 'P':
            inventory = authority.get('full_source_ground_inventory', {})
            if (authority.get('diagnostic_include_loads') is not True
                    or inventory.get('connected_count') != 344
                    or len(inventory.get('contacts', [])) != 344):
                raise ValueError('P: incomplete own-load native authority')
            authority_contacts = inventory.get('contacts', [])
        elif board == 'K':
            if (authority.get('balanced_function_count') != 2287
                    or len(authority.get('contacts', [])) != 2288
                    or authority.get('board_sha256') != native['board_sha256']):
                raise ValueError('K: incomplete full native authority')
            authority_contacts = authority.get('contacts', [])
        elif board in ('EL', 'O1', 'O2', 'O3', 'O4', 'O5'):
            authority_contacts = authority.get('source_ground_inventory', {}).get('contacts', [])
            if len(authority_contacts) != (72 if board == 'EL' else 7):
                raise ValueError(f'{board}: incomplete peripheral native authority')
        else:
            if authority.get('all_source_AGND_connected_count') != len(
                    [row for row in graph['contacts'] if row['board'] == board]):
                raise ValueError(f'{board}: incomplete jack native authority')
            authority_contacts = None
        if authority_contacts is not None:
            source_set = {(row['ref'], row['pad']) for row in authority_contacts}
            graph_set = {(row['ref'], row['pad']) for row in graph['contacts'] if row['board'] == board}
            if len(source_set) != len(authority_contacts) or source_set != graph_set:
                raise ValueError(f'{board}: native authority contact inventory differs from graph')
    rows = result['ports'] + [result['reference_contact']]
    identities = [f"{board}:{row['ref']}:{row['pad']}" for row in rows]
    expected = {row['id']: row for row in graph['contacts'] if row['board'] == board}
    if len(set(identities)) != len(identities) or set(identities) != set(expected):
        raise ValueError(f'{board}: result omits or duplicates exact graph contacts')
    recorded = profile['profiles']
    if len(recorded) != len(rows) or any((a['ref'], a['pad'], a['layer']) !=
                                         (b['ref'], b['pad'], b['layer'])
                                         for a, b in zip(rows, recorded)):
        raise ValueError(f'{board}: ordered profile/result contacts differ')
    for row, identity in zip(rows, identities):
        kind = {'fitted_source_contact': 'load', 'GH_terminal': 'GH',
                'main_terminal': 'main'}[expected[identity]['kind']]
        if row['kind'] != kind:
            raise ValueError(f'{board}: graph/result contact roles differ')
    n = len(rows) - 1
    matrices = {}
    for mode in ('upper', 'lower'):
        matrix = np.asarray(result['matrices_ohm'][mode], dtype=float)
        if matrix.shape != (n, n) or not np.isfinite(matrix).all() or not np.allclose(
                matrix, matrix.T, rtol=1e-12, atol=1e-15):
            raise ValueError(f'{board}: invalid {mode} nominal matrix')
        matrices[mode] = matrix
    return identities[-1], identities[:-1], matrices


def assemble(graph, records, wire_values, scenario, model_hashes, root='.', full=True):
    """Validate all ten inputs before any nominal floating composition."""
    input_hashes = {'graph_canonical': canonical_digest(graph),
                    'wire_values_canonical': canonical_digest(wire_values),
                    'scenario_canonical': canonical_digest(scenario),
                    'driver_source': digest(__file__)}
    contacts = check_graph(graph, root, full)
    boards = set(graph['board_source_ids'])
    if set(records) != boards:
        raise ValueError('one current-epoch board result and native export required for every board')
    operators = {'upper': {}, 'lower': {}}
    input_digests = {}
    board_input_paths = {}
    for board in sorted(boards):
        row = records[board]
        for key in ('result', 'native'):
            if key not in row:
                raise ValueError(f'{board}: missing {key} path')
        result_path, native_path = Path(row['result']), Path(row['native'])
        result_bytes, native_bytes = result_path.read_bytes(), native_path.read_bytes()
        result, native = json.loads(result_bytes), json.loads(native_bytes)
        profile_path = Path(result['profile_receipt']['path'])
        profile_bytes = profile_path.read_bytes()
        if hashlib.sha256(profile_bytes).hexdigest() != result['profile_receipt']['sha256']:
            raise ValueError(f'{board}: profile receipt bytes differ')
        if hashlib.sha256(native_bytes).hexdigest() != result['native_export_sha256']:
            raise ValueError(f'{board}: native export bytes differ')
        profile = json.loads(profile_bytes)
        reference, ports, matrices = check_board(board, graph, result, native, profile,
                                                  model_hashes, full, root, native_path)
        for mode in operators:
            operators[mode][board] = {'reference': reference, 'ports': ports,
                                      'energy': matrices[mode]}
        if any(digest(path) != hashlib.sha256(raw).hexdigest()
               for path, raw in ((result_path, result_bytes), (profile_path, profile_bytes),
                                 (native_path, native_bytes))):
            raise ValueError(f'{board}: input changed during nominal assembly')
        input_digests[board] = {'result': hashlib.sha256(result_bytes).hexdigest(),
                                'profile': hashlib.sha256(profile_bytes).hexdigest(),
                                'native': hashlib.sha256(native_bytes).hexdigest()}
        board_input_paths[board] = {'result': result_path, 'profile': profile_path,
                                    'native': native_path}
    edges = graph['wire_edges']
    if wire_values.get('basis') != 'ASSUMED_NOMINAL_ONLY' or set(wire_values.get('ohm', {})) != {e['id'] for e in edges}:
        raise ValueError('exact assumed nominal resistance required for every physical wire')
    wires = []
    for edge in edges:
        resistance = wire_values['ohm'][edge['id']]
        if not isinstance(resistance, (int, float)) or isinstance(resistance, bool) or not np.isfinite(resistance) or resistance <= 0:
            raise ValueError('positive finite assumed nominal resistance required: ' + edge['id'])
        if full:
            if edge['kind'] == 'GH_wire':
                minimum = edge['wire_lower_requirement_ohm']
                maximum = edge['wire_upper_hot_requirement_ohm'] + edge['two_assembled_contacts_upper_allowance_ohm']
                if not minimum <= resistance <= maximum:
                    raise ValueError('assumed GH scalar outside source requirement envelope: ' + edge['id'])
            elif edge['kind'] == 'main_wire':
                if resistance > edge['whole_wire_and_two_terminations_upper_requirement_ohm']:
                    raise ValueError('assumed main scalar exceeds source requirement: ' + edge['id'])
            else:
                raise ValueError('unknown physical ground wire class')
        wires.append({'id': edge['id'], 'from_contact': edge['from_contact'],
                      'to_contact': edge['to_contact'], 'resistance': resistance})
    columns = scenario['columns']
    ids = [row['id'] for row in columns]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('unique named scenario columns required')
    sources = {name: [0] * len(columns) for name in contacts}
    for index, column in enumerate(columns):
        terms = column['terms']
        if not terms or any(name not in contacts or not isinstance(value, int) or isinstance(value, bool)
                            or value == 0 for name, value in terms.items()):
            raise ValueError('scenario requires nonzero integer terms at exact contacts')
        if sum(terms.values()) != 0:
            raise ValueError('each scenario column must balance globally')
        for name, value in terms.items():
            sources[name][index] = value
    contact_boards = {name: row['board'] for name, row in contacts.items()}
    result = {mode: compose(operators[mode], contact_boards, wires, sources)
              for mode in ('upper', 'lower')}
    if input_hashes != {'graph_canonical': canonical_digest(graph),
                        'wire_values_canonical': canonical_digest(wire_values),
                        'scenario_canonical': canonical_digest(scenario),
                        'driver_source': digest(__file__)}:
        raise ValueError('nominal assembly source changed during composition')
    if full and current_model_hashes(Path(root)) != model_hashes:
        raise ValueError('nominal model source changed during composition')
    for board, paths in board_input_paths.items():
        if any(digest(path) != input_digests[board][kind] for kind, path in paths.items()):
            raise ValueError(f'{board}: input changed during nominal composition')
    return {'status': 'NOT ACCEPTED: source-bound nominal floating diagnostic only',
            'physical_contact_material_current_trace_class': 'NOT ACCEPTED',
            'joined_common_current_voltage_bounds': 'NOT ACCEPTED',
            'graph_contact_count': len(contacts), 'physical_wire_count': len(edges),
            'input_sha256': input_hashes,
            'board_input_sha256': input_digests, 'scenario_column_ids': ids,
            'signed_scenario_columns': json.loads(json.dumps(columns)),
            'assumed_nominal_wire_ohm': wire_values['ohm'],
            'matrices_ohm': {mode: result[mode]['energy'].tolist() for mode in result},
            'nominal_wire_current_map_A_per_unit_column': {
                mode: result[mode]['wire_current_map'].tolist() for mode in result},
            'floating_KCL_residual': {mode: result[mode]['floating_board_KCL_residual'] for mode in result},
            'warning': 'PCB numerical patches and scalar wire assumptions are not compatible physical terminal witnesses.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--graph', type=Path, default=Path('design/partition/ground-network-incidence.json'))
    parser.add_argument('--board', action='append', required=True, metavar='ID=RESULT,NATIVE')
    parser.add_argument('--wire-values', required=True, type=Path)
    parser.add_argument('--scenario', required=True, type=Path)
    args = parser.parse_args()
    records = {}
    for entry in args.board:
        board, sep, files = entry.partition('=')
        if not sep or board in records or len(files.split(',')) != 2:
            raise ValueError('each --board must uniquely name ID=RESULT,NATIVE')
        records[board] = dict(zip(('result', 'native'), files.split(',')))
    inputs = {'graph': args.graph, 'wire_values': args.wire_values, 'scenario': args.scenario}
    raw = {key: path.read_bytes() for key, path in inputs.items()}
    result = assemble(json.loads(raw['graph']), records,
                      json.loads(raw['wire_values']), json.loads(raw['scenario']),
                      current_model_hashes(Path('.')))
    result['input_file_sha256'] = {key: hashlib.sha256(data).hexdigest()
                                   for key, data in raw.items()}
    if any(digest(path) != result['input_file_sha256'][key] for key, path in inputs.items()) or \
            digest(__file__) != result['input_sha256']['driver_source']:
        raise ValueError('nominal assembly input file changed before publication')
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write('\n')
    print(result['status'])


if __name__ == '__main__':
    main()
