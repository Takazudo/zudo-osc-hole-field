"""Regression tests for real source coverage, MPN loss and retained-input drift."""
from copy import deepcopy
from contextlib import redirect_stderr
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.service import build_trimmer_inventory as inventory


class TrimmerInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families, cls.instances = inventory.specification()
        cls.dictionary = json.loads((inventory.ROOT / inventory.FUNCTIONS).read_text())
        cls.components, cls.pins = inventory.netlist_data((inventory.ROOT / inventory.NETLIST).read_text())
        cls.placements = json.loads((inventory.ROOT / inventory.PLACEMENTS).read_text())['placements']
        cls.native = inventory.pcb_trimmers((inventory.ROOT / inventory.PCB).read_text())

    def build(self, **changes):
        args = dict(families=self.families, instances=self.instances,
                    dictionary=self.dictionary, components=self.components,
                    pins=self.pins, placements=self.placements, native=self.native)
        return inventory.build(**{**args, **changes})

    def mutate_part(self, **changes):
        f = next(f for f in self.families if f.name == 'oscillator')
        p = next(p for p in f.parts if p.attributes.get('Role') == 'oscillator:SINE_LEVEL')
        return tuple(replace(f, parts=tuple(replace(p, **changes) if x == p else x for x in f.parts))
                     if x == f else x for x in self.families)

    def test_complete_source_mapping_and_real_faces(self):
        result = self.build()
        self.assertEqual(result['summary']['faces'], {'B.Cu': 56, 'F.Cu': 44})
        self.assertEqual(result['summary']['trimmers'], 100)
        rows = {r['ref']: r for r in result['trimmers']}
        self.assertEqual(rows['RVO1111']['label'], 'OSC1 SINE LEVEL')
        self.assertEqual(rows['RV1601']['label'], 'ALL OSC OCT SPAN')
        self.assertEqual(rows['RV1601']['value'], 'TC33X-2-102E')
        self.assertEqual(rows['RV1601']['nominal_resistance'], '1 kΩ')

    def test_unknown_source_role_fails(self):
        attrs = {'Role': 'oscillator:SINE_SHAPE', 'MPN': 'TC33X-2-103E'}
        with self.assertRaisesRegex(ValueError, 'roles'):
            self.build(families=self.mutate_part(attributes=attrs))

    def test_missing_role_or_footprint_cannot_hide_trim(self):
        for changes in ({'attributes': {}}, {'footprint': ''}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'footprint or Role'):
                self.build(families=self.mutate_part(**changes))

    def test_source_mpn_loss_fails_even_with_same_package_and_value(self):
        attrs = next(p.attributes for f in self.families for p in f.parts
                     if p.attributes.get('Role') == 'oscillator:SINE_LEVEL')
        with self.assertRaisesRegex(ValueError, 'mpn differs'):
            self.build(families=self.mutate_part(attributes={**attrs, 'MPN': ''}))

    def test_missing_duplicate_or_stale_dictionary_rows_fail(self):
        for mode in ('missing', 'duplicate', 'unknown_role'):
            d = deepcopy(self.dictionary)
            if mode == 'missing': d['trimmers'].pop()
            if mode == 'duplicate': d['trimmers'][-1] = d['trimmers'][0]
            if mode == 'unknown_role': d['roles'][0]['role'] = 'unknown:new_trim'
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.build(dictionary=d)

    def test_dictionary_cannot_assign_mpn_candidate_or_direction(self):
        for changes in ({'mpn': 'TC33X-2-203E'}, {'rotation_direction': 'CW+'},
                        {'x_mm': 0}, {'function_label': 'SINE SHAPE'},
                        {'reference_label': ''}, {'label': 'WRONG MODULE'},
                        {'nominal_resistance': '10 kΩ'}, {'calibration_status': 'PASS'}):
            d = deepcopy(self.dictionary)
            d['trimmers'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.build(dictionary=d)

    def test_all_calibration_links_and_component_gap_dispositions(self):
        doc = (inventory.ROOT / 'doc/src/content/docs/verification/osc-trimmer-calibration.mdx').read_text()
        for row in self.dictionary['trimmers']:
            anchor = row['calibration_reference'].split('#')[1]
            self.assertIn('### ' + anchor + '\n', doc)
        review = json.loads((inventory.ROOT / 'design/service/component-review/review.json').read_text())
        gaps = {r['ref']: r for r in review['gaps']}
        expected = {r['ref']: r for r in self.dictionary['trimmers'] if not r['mpn']}
        self.assertEqual(set(gaps), set(expected))
        self.assertEqual(len(review['gaps']), 23)
        for ref, row in expected.items():
            self.assertEqual(gaps[ref]['source_role'], row['role'])
            self.assertEqual(gaps[ref]['source_value'], row['value'])
            self.assertEqual(gaps[ref]['production_mpn'], '')
        for source in review['source_locks']:
            self.assertEqual(inventory.digest(inventory.ROOT / source['retained_path']), source['sha256'])

    def test_retained_netlist_mpn_loss_or_pin_swap_fails(self):
        components = deepcopy(self.components)
        components['RVO1106']['MPN'] = ''
        with self.assertRaisesRegex(ValueError, 'MPN drift'):
            self.build(components=components)
        pins = {**self.pins, ('RVO1106', '1'): '/O1/BASE_REF5'}
        with self.assertRaisesRegex(ValueError, 'connectivity drift'):
            self.build(pins=pins)
        with self.assertRaisesRegex(ValueError, 'connectivity drift'):
            self.build(pins={**self.pins, ('RVO1106', '4'): 'AGND'})

    def test_role_cannot_smuggle_pose_or_calibration_claim(self):
        for changes in ({'board': 'KA'}, {'rotation_direction': 'CW+'}, {'calibration_status': 'PASS'}):
            d = deepcopy(self.dictionary)
            d['roles'][0].update(changes)
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'invalid role'):
                self.build(dictionary=d)

    def test_native_pad_pose_and_identity_drift_fail(self):
        for mode in ('pad', 'pose', 'mpn', 'missing'):
            native = deepcopy(self.native)
            if mode == 'pad': native['RVO1106']['pads']['1'] = 'AGND'
            if mode == 'pose': native['RVO1106']['x_mm'] += 0.1
            if mode == 'mpn': native['RVO1106']['properties']['MPN'] = ''
            if mode == 'missing': native.pop('RVO1106')
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.build(native=native)

    def test_check_rejects_stale_inventory_without_rewriting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / inventory.OUTPUT
            path.parent.mkdir(parents=True)
            path.write_text('stale\n')
            error = io.StringIO()
            with patch.object(inventory, 'ROOT', root), patch.object(inventory, 'generate', return_value='fresh\n'), patch('sys.argv', ['builder', '--check']):
                with redirect_stderr(error):
                    self.assertEqual(inventory.main(), 1)
            self.assertIn('inventory is stale', error.getvalue())
            self.assertEqual(path.read_text(), 'stale\n')


if __name__ == '__main__':
    unittest.main()
