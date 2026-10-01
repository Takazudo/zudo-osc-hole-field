"""Small complete network and fail-closed input regressions for the diagnostic."""
import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

from scripts.pcbgen.assemble_nominal_ground_network import (
    assemble, check_board, current_model_hashes, MODEL_FILES)


def write(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NominalAssemblyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.hashes = {'fixture.py': 'fixture-current'}
        self.graph = {
            'board_source_ids': {'J': 'jack', 'K': 'core'},
            'contacts': [
                {'id': 'J:L:1', 'board': 'J', 'kind': 'fitted_source_contact'},
                {'id': 'J:T:1', 'board': 'J', 'kind': 'main_terminal'},
                {'id': 'K:L:1', 'board': 'K', 'kind': 'fitted_source_contact'},
                {'id': 'K:T:1', 'board': 'K', 'kind': 'main_terminal'}],
            'wire_edges': [{'id': 'main', 'from_contact': 'J:T:1', 'to_contact': 'K:T:1',
                            'incidence': {'J:T:1': -1, 'K:T:1': 1}}]}
        self.records = {}
        for board, board_id, ohm in (('J', 'jack', 2.), ('K', 'core', 3.)):
            native_path = root / f'{board}-native.json'
            native_sha = write(native_path, {'board_id': board_id, 'board_sha256': f'{board}-board'})
            profile_path = root / f'{board}-profiles.json'
            profile_sha = write(profile_path, {'native_export_sha256': native_sha,
                                                'model_source_sha256': self.hashes,
                                                'profiles': [{'ref': 'L', 'pad': '1', 'layer': 0},
                                                             {'ref': 'T', 'pad': '1', 'layer': 0}]})
            result_path = root / f'{board}-result.json'
            write(result_path, {
                'status': 'NOT ACCEPTED: nominal finite-profile full-native diagnostic only',
                'board_sha256': f'{board}-board', 'native_export_sha256': native_sha,
                'model_source_sha256': self.hashes,
                'ports': [{'ref': 'L', 'pad': '1', 'layer': 0, 'kind': 'load'}],
                'reference_contact': {'ref': 'T', 'pad': '1', 'layer': 0, 'kind': 'main'},
                'profile_receipt': {'path': str(profile_path), 'sha256': profile_sha},
                'matrices_ohm': {'upper': [[ohm]], 'lower': [[ohm]]}})
            self.records[board] = {'result': str(result_path), 'native': str(native_path)}
        self.wires = {'basis': 'ASSUMED_NOMINAL_ONLY', 'ohm': {'main': 5.}}
        self.scenario = {'columns': [{'id': 'J-load-to-K-load',
                                      'terms': {'J:L:1': 1, 'K:L:1': -1}}]}

    def run_model(self, records=None, wires=None, scenario=None, hashes=None):
        return assemble(self.graph, records or self.records, wires or self.wires,
                        scenario or self.scenario, hashes or self.hashes, full=False)

    def test_complete_nominal_series_network(self):
        result = self.run_model()
        self.assertEqual(result['status'], 'NOT ACCEPTED: source-bound nominal floating diagnostic only')
        self.assertEqual(result['graph_contact_count'], 4)
        self.assertEqual(result['physical_wire_count'], 1)
        self.assertAlmostEqual(result['matrices_ohm']['upper'][0][0], 10.)
        self.assertAlmostEqual(result['matrices_ohm']['lower'][0][0], 10.)
        self.assertEqual(result['joined_common_current_voltage_bounds'], 'NOT ACCEPTED')

    def test_stale_model_epoch_and_missing_board_rejected(self):
        with self.assertRaisesRegex(ValueError, 'historical or incomplete model source epoch'):
            self.run_model(hashes={'fixture.py': 'later-source'})
        with self.assertRaisesRegex(ValueError, 'every board'):
            self.run_model(records={'J': self.records['J']})

    def test_profile_native_and_exact_contact_mutations_rejected(self):
        path = Path(self.records['J']['result'])
        original = json.loads(path.read_text())
        modified = copy.deepcopy(original)
        modified['ports'][0]['ref'] = 'wrong'
        write(path, modified)
        with self.assertRaisesRegex(ValueError, 'exact graph contacts'):
            self.run_model()
        write(path, original)
        profile_path = Path(original['profile_receipt']['path'])
        profile_path.write_text(profile_path.read_text() + ' ')
        with self.assertRaisesRegex(ValueError, 'profile receipt bytes differ'):
            self.run_model()

    def test_wire_and_scenario_cannot_gain_implicit_credit(self):
        with self.assertRaisesRegex(ValueError, 'exact assumed nominal resistance'):
            self.run_model(wires={'basis': 'ASSUMED_NOMINAL_ONLY', 'ohm': {}})
        with self.assertRaisesRegex(ValueError, 'balance globally'):
            self.run_model(scenario={'columns': [{'id': 'bad', 'terms': {'J:L:1': 1}}]})

    def test_signed_scenario_mutation_changes_replay_provenance(self):
        first = self.run_model()
        changed = {'columns': [{'id': 'J-load-to-K-load',
                                'terms': {'J:L:1': 1, 'K:T:1': -1}}]}
        second = self.run_model(scenario=changed)
        self.assertEqual(first['scenario_column_ids'], second['scenario_column_ids'])
        self.assertNotEqual(first['input_sha256']['scenario_canonical'],
                            second['input_sha256']['scenario_canonical'])
        self.assertEqual(first['signed_scenario_columns'], self.scenario['columns'])
        self.assertEqual(second['signed_scenario_columns'], changed['columns'])
        self.assertEqual(len(first['input_sha256']['driver_source']), 64)


    def test_production_source_set_is_exact(self):
        self.assertEqual(len(MODEL_FILES), 44)
        self.assertEqual(set(current_model_hashes(Path('.'))), MODEL_FILES)

    def test_full_p_authority_without_board_id_and_root_relative_dependency(self):
        root = Path(self.tmp.name)
        native_path = root / 'native.json'
        native = {'board_id': 'osc-control', 'board_sha256': 'P-board'}
        native_sha = write(native_path, native)
        graph_contacts = []
        authority_contacts = []
        rows = []
        for kind, count, prefix in (('fitted_source_contact', 214, 'L'),
                                    ('GH_terminal', 127, 'J'), ('main_terminal', 3, 'T')):
            for index in range(count):
                ref = f'{prefix}{index}'
                graph_contacts.append({'id': f'P:{ref}:1', 'board': 'P', 'kind': kind,
                                       'ref': ref, 'pad': '1'})
                authority_contacts.append({'ref': ref, 'pad': '1',
                                           'kind': 'own_load' if kind == 'fitted_source_contact' else
                                                   'GH' if kind == 'GH_terminal' else 'main'})
                rows.append({'ref': ref, 'pad': '1', 'layer': 0,
                             'kind': 'load' if kind == 'fitted_source_contact' else
                                     'GH' if kind == 'GH_terminal' else 'main'})
        authority = {'dependency_sha256': {'native.json': native_sha},
                     'diagnostic_include_loads': True,
                     'full_source_ground_inventory': {'connected_count': 344,
                                                      'contacts': authority_contacts},
                     'selected_contacts': authority_contacts[214:]}
        result = {
            'status': 'NOT ACCEPTED: nominal finite-profile full-native diagnostic only',
            'board_sha256': native['board_sha256'], 'native_export_sha256': native_sha,
            'model_source_sha256': self.hashes, 'control_native_prerequisite': authority,
            'ports': rows[:-1], 'reference_contact': rows[-1],
            'matrices_ohm': {'upper': [[float(i == j) for j in range(343)] for i in range(343)],
                             'lower': [[float(i == j) for j in range(343)] for i in range(343)]}}
        profile = {'native_export_sha256': native_sha, 'model_source_sha256': self.hashes,
                   'control_native_prerequisite': copy.deepcopy(authority), 'profiles': rows}
        graph = {'board_source_ids': {'P': 'osc-control'}, 'contacts': graph_contacts}
        old_cwd = Path.cwd()
        try:
            os.chdir('/')
            reference, ports, matrices = check_board('P', graph, result, native, profile,
                                                      self.hashes, True, root, native_path)
        finally:
            os.chdir(old_cwd)
        self.assertEqual(reference, 'P:T2:1')
        self.assertEqual(len(ports), 343)
        self.assertEqual(matrices['upper'].shape, (343, 343))
        broken = copy.deepcopy(result)
        broken['control_native_prerequisite']['full_source_ground_inventory']['contacts'].pop()
        broken_profile = copy.deepcopy(profile)
        broken_profile['control_native_prerequisite'] = copy.deepcopy(broken['control_native_prerequisite'])
        with self.assertRaisesRegex(ValueError, 'incomplete own-load native authority'):
            check_board('P', graph, broken, native, broken_profile, self.hashes, True, root, native_path)


if __name__ == '__main__':
    unittest.main()
