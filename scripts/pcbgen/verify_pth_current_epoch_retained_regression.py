"""Adversarial local geometry transfer checks."""
import copy
import json
import unittest

from scripts.pcbgen.verify_pth_current_epoch import CACHE, check_rows, compare_local_epoch


class PthCurrentEpochTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = json.loads((CACHE / 'control-feasibility-v3/ground-feasibility-geometry.json').read_bytes())
        cls.current = json.loads((CACHE / 'control-feasibility-v4/ground-feasibility-geometry.json').read_bytes())
        cert = json.loads((CACHE / 'pth-source-geometry-certificate-v2.json').read_bytes())
        cls.row = next(row for row in cert['certificates'] if row['board_id'] == 'osc-control')
        cls.expected = {(cls.row['ref'], cls.row['pad']): {
            'historical_board_sha256': cls.old['board_sha256'],
            'historical_native_sha256': cert['source_sha256']['.circuit-cache/issue38-recovery/control-feasibility-v3/ground-feasibility-geometry.json'],
        }}

    def test_exact_epoch_and_witness(self):
        compare_local_epoch(self.old, self.current)
        self.assertEqual(check_rows([self.row], self.current, self.expected), set(self.expected))

    def test_reject_changed_drill(self):
        altered = dict(self.current)
        altered['holes'] = copy.deepcopy(self.current['holes'])
        next(hole for hole in altered['holes'] if hole['uuid'] == self.row['uuid'])['size_mm'][0] += 0.01
        with self.assertRaisesRegex(ValueError, 'holes'):
            compare_local_epoch(self.old, altered)

    def test_reject_changed_native_foil_primitive(self):
        altered = dict(self.current)
        altered['items'] = list(self.current['items'])
        i = next(i for i, item in enumerate(altered['items']) if item['uuid'] == self.row['uuid'])
        altered['items'][i] = copy.deepcopy(altered['items'][i])
        altered['items'][i]['analytic_primitives']['F.Cu']['shape'] = 'tampered'
        with self.assertRaisesRegex(ValueError, 'source pad'):
            compare_local_epoch(self.old, altered)

    def test_reject_non_fitted_or_duplicate_witness(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            check_rows([self.row, self.row], self.current, self.expected)
        with self.assertRaisesRegex(ValueError, 'non-fitted'):
            check_rows([self.row], self.current, {})


if __name__ == '__main__':
    unittest.main()
