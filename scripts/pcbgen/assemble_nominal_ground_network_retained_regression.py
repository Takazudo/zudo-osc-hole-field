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

    def test_production_source_set_is_exact(self):
        self.assertEqual(len(MODEL_FILES), 44)
        hashes = current_model_hashes(Path('.'))
        self.assertEqual(set(hashes), MODEL_FILES)
        current_p = json.loads(Path('.circuit-cache/issue38-recovery/control-feasibility-v4/'
                                    'ground-full-nineteen-checkpoint-v2.json').read_text())
        self.assertEqual(current_p['model_source_sha256'], hashes)


if __name__ == '__main__':
    unittest.main()
