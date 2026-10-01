"""A paid local feed stays in the rail drop; incomplete mappings fail."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.screen_rail_transfers import screen, bind_artifact_paths


class RailTransferTests(unittest.TestCase):
    def setUp(self):
        self.matrix = {'board_sha256': 'board', 'reference_main': 'TP1',
            'conductor_role_mapping': {'actual_native_net': '+5V', 'original_native_export_sha256': 'native'},
            'native_export_sha256': 'selected', 'model_source_sha256': {'model': 'model-sha'},
            'rail_wrapper_source_sha256': {'wrapper': 'wrapper-sha'},
            'profile_receipt': {'path': 'synthetic', 'sha256': 'profile-sha'},
            'ports': [{'kind': 'load', 'ref': 'R1', 'pad': '1'},
                      {'kind': 'load', 'ref': 'U1', 'pad': '5'}],
            # Two 4 mOhm / 1 mOhm private feeds after a 0.5 mOhm common sheet.
            'matrices_ohm': {'upper': [[.0045, .0005], [.0005, .0015]],
                            'lower': [[.0045, .0005], [.0005, .0015]]}}
        self.ledger = {'board_sha256': 'board', 'native_export_sha256': 'native', 'source_envelope_A': {'+5V': .5},
            'pads': [{'ref': 'R1', 'pad': '1', 'net': '+5V', 'native_connected_to_load_land': True},
                     {'ref': 'U1', 'pad': '5', 'net': '+5V', 'native_connected_to_load_land': True}]}

    def test_local_access_remains_charged(self):
        result = screen(self.matrix, self.ledger, '+5V')
        self.assertAlmostEqual(result['worst']['absolute_drop_upper_V'], .00225)
        self.assertEqual(result['worst']['extreme_injection_ref'], 'R1')
        self.assertTrue(result['common_rail_and_K_allocation'].startswith('NOT RUN'))

    def test_identity_coverage_and_connectivity_are_required(self):
        for defect in ('missing', 'wrong_net', 'unfed'):
            matrix, ledger = copy.deepcopy(self.matrix), copy.deepcopy(self.ledger)
            if defect == 'missing': ledger['pads'].append({'ref': 'U2', 'pad': '5', 'net': '+5V'})
            if defect == 'wrong_net': matrix['conductor_role_mapping']['actual_native_net'] = '+12V'
            if defect == 'unfed': ledger['pads'][0]['native_connected_to_load_land'] = False
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                screen(matrix, ledger, '+5V')

    def test_exact_artifact_and_profile_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = root / 'profiles.json'; profile.write_text('{"patches": []}')
            self.matrix['profile_receipt'] = {'path': str(profile), 'sha256': hashlib.sha256(profile.read_bytes()).hexdigest()}
            matrix = root / 'matrix.json'; matrix.write_text(json.dumps(self.matrix))
            ledger = root / 'ledger.json'; ledger.write_text(json.dumps(self.ledger))
            report = screen(self.matrix, self.ledger, '+5V')
            bind_artifact_paths(report, matrix, ledger)
            self.assertEqual(report['input_artifacts']['matrix']['sha256'], hashlib.sha256(matrix.read_bytes()).hexdigest())
            changed = copy.deepcopy(self.matrix); changed['matrices_ohm']['upper'][0][0] += .001
            matrix.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, 'differs'):
                bind_artifact_paths(report, matrix, ledger)
            matrix.write_text(json.dumps(self.matrix)); profile.write_text('{"patches": [1]}')
            with self.assertRaisesRegex(ValueError, 'profile receipt'):
                bind_artifact_paths(report, matrix, ledger)


if __name__ == '__main__': unittest.main()
