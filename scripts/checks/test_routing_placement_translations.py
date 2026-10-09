import copy
import json
from pathlib import Path
import unittest

from scripts.checks.routing_placement_translations import apply_translations


class RoutingTranslationTests(unittest.TestCase):
    def setUp(self):
        self.rows = [dict(ref='RB1', board='JR', fixed=False, x_mm=5., y_mm=5.,
                          rotation_deg=0, kicad_orientation_deg=180, side='B.Cu',
                          courtyard_mm=[4., 4., 6., 6.]),
                     dict(ref='R2', board='JR', fixed=False, x_mm=9., y_mm=5.,
                          rotation_deg=0, kicad_orientation_deg=180, side='B.Cu',
                          courtyard_mm=[8., 4., 10., 6.])]
        self.source = {'boards': {'JR': {'outline': [[0, 0], [20, 0], [20, 20], [0, 20]]}}}
        self.change = dict(ref='RB1', expected_source=copy.deepcopy(self.rows[0]),
                           delta_mm=[0., -.2], evidence='immutable native pilot and reviewed proposal')

    def run_change(self, changes=None):
        return apply_translations(self.rows, self.source, dict(schema_version=1,
                                  translations=[self.change] if changes is None else changes), headers=[])

    def test_empty_and_translation_preserve_all_unaffected_source(self):
        original = copy.deepcopy(self.rows)
        self.assertEqual(self.run_change([]), original)
        result = self.run_change()
        self.assertEqual(self.rows, original)
        self.assertEqual(result[1], original[1])
        expected = copy.deepcopy(original[0]); expected['y_mm'] = 4.8
        expected['courtyard_mm'] = [4., 3.8, 6., 5.8]
        self.assertEqual(result[0], expected)

    def test_stale_source_rejected(self):
        self.rows[0]['x_mm'] += .1
        with self.assertRaisesRegex(ValueError, 'stale'):
            self.run_change()

    def test_fixed_sensitive_wrong_board_and_nonresistor_rejected(self):
        for field, value in [('fixed', True), ('bypass_cluster', 'U1'), ('board', 'K'), ('ref', 'C1')]:
            with self.subTest(field=field):
                old = copy.deepcopy(self.rows)
                self.rows[0][field] = value
                self.change['ref'] = self.rows[0]['ref']
                self.change['expected_source'] = copy.deepcopy(self.rows[0])
                with self.assertRaisesRegex(ValueError, 'scope'):
                    self.run_change()
                self.rows = old

    def test_nonfinite_zero_oversized_and_offgrid_translations_rejected(self):
        for delta in ([0, 0], [0, float('nan')], [0, 2.1], [0, .05], [False, .1]):
            with self.subTest(delta=delta):
                self.change['delta_mm'] = delta
                with self.assertRaisesRegex(ValueError, 'increments'):
                    self.run_change()

    def test_courtyard_collision_and_board_edge_rejected(self):
        self.change['delta_mm'] = [2., 0]
        with self.assertRaisesRegex(ValueError, 'separation'):
            self.run_change()
        self.change['delta_mm'] = [-2., 0]
        self.source['boards']['JR']['outline'] = [[2, 0], [20, 0], [20, 20], [2, 20]]
        with self.assertRaisesRegex(ValueError, 'edge'):
            self.run_change()

    def test_diagonal_gap_preserves_conservative_source_margin(self):
        self.rows[1]['courtyard_mm'] = [6.2, 6.2, 8.2, 8.2]
        self.change['delta_mm'] = [0, -.1]
        with self.assertRaisesRegex(ValueError, 'separation'):
            self.run_change()

    def test_duplicate_translation_and_unknown_fields_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            self.run_change([self.change, self.change])
        self.change['rotation_deg'] = 90
        with self.assertRaisesRegex(ValueError, 'fields'):
            self.run_change()

    def test_connector_margin_and_face_scope(self):
        header = dict(id='H1', board='JR', side='B.Cu', land_courtyard_mm=[4., 6.1, 6., 7.])
        adjustments = dict(schema_version=1, translations=[self.change])
        with self.assertRaisesRegex(ValueError, 'connector.*H1'):
            apply_translations(self.rows, self.source, adjustments, headers=[header])
        header['side'] = 'F.Cu'
        self.assertEqual(apply_translations(self.rows, self.source, adjustments, headers=[header]), self.run_change())
        header['side'] = 'B.Cu'
        header['land_courtyard_mm'] = [4., 6.2, 6., 7.]
        self.assertEqual(apply_translations(self.rows, self.source, adjustments, headers=[header]), self.run_change())

    def test_actual_rb4413_connector_conflict_rejected(self):
        root = Path(__file__).resolve().parents[2]
        rows = json.loads((root/'design/partition/floorplan-candidate.json').read_text())['placements']
        source = json.loads((root/'design/partition/partition-input.json').read_text())
        changes = json.loads((root/'circuit/routing/issue189/jr-rb4413-edge-bridge/pending-source-translation.json').read_text())
        headers = json.loads((root/'design/partition/connector-packing-candidate.json').read_text())['headers']
        with self.assertRaisesRegex(ValueError, 'connector.*JR-K-6-JR'):
            apply_translations(rows, source, changes, headers=headers)

    def test_component_only_translation_does_not_certify_connector_clearance(self):
        root = Path(__file__).resolve().parents[2]
        rows = json.loads((root/'design/partition/floorplan-candidate.json').read_text())['placements']
        source = json.loads((root/'design/partition/partition-input.json').read_text())
        changes = json.loads((root/'circuit/routing/issue189/jr-rb4413-edge-bridge/pending-source-translation.json').read_text())
        original = copy.deepcopy(rows)
        index = next(i for i, p in enumerate(original) if p['ref'] == 'RB4413')
        original[index] = changes['translations'][0]['expected_source']
        result = apply_translations(original, source, changes, headers=[])
        self.assertEqual([a['ref'] for a, b in zip(original, result) if a != b], ['RB4413'])
        active = json.loads((root/'design/partition/routing-placement-translations.json').read_text())
        translated = any(row['ref'] == 'RB4413' for row in active['translations'])
        self.assertEqual(rows[index], (result if translated else original)[index])


if __name__ == '__main__':
    unittest.main()
