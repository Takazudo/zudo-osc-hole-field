"""Generic fixtures must use actual source pins and reject unsupported devices."""
from dataclasses import replace
import json
import unittest
from unittest.mock import patch
from design.spec.modules import run_wavefolder_spice as model


class WavefolderModelPins(unittest.TestCase):
    def setUp(self):
        self.family = model.family()

    def changed(self, role, **changes):
        return replace(self.family, parts=tuple(
            replace(p, **changes) if p.attributes.get('Role') == role else p
            for p in self.family.parts))

    def test_nominal_body_matches_retained_oracle_deck(self):
        report = json.loads(model.OUT.read_text())
        deck = model.DIR / 'wavefolder-dc-f5-b0.cir'
        body = '\n'.join(deck.read_text().splitlines()[1:]).split('.control\n')[0]
        self.assertEqual(model.common(5, 0, offset=report['model_offset_calibration_V']), body)

    def test_transistor_clamp_and_trim_pins_reach_the_deck(self):
        for role, pin, expected in (
            ('wavefolder:BIAS_PNP', '3', 'QBIAS 0 BASE EMITTER GENERIC_PNP'),
            ('wavefolder:CONTROL_CLAMP', '3', 'DCLOW 0 0 SCHOTTKY'),
            ('wavefolder:PRE_GAIN_MAX', '1', 'RGAIN_TRIM 0 PRE_GAIN_SUM 5k'),
        ):
            original = next(p for p in self.family.parts if p.attributes.get('Role') == role)
            changed = self.changed(role, pins={**original.pins, pin: 'AGND'})
            with self.subTest(role=role), patch.object(model, 'family', return_value=changed):
                self.assertIn(expected, model.common().splitlines())

    def test_bjt_and_dual_diode_pin_order_is_preserved(self):
        for role, expected in (
            ('wavefolder:BIAS_PNP', ['QBIAS THIRD FIRST SECOND GENERIC_PNP']),
            ('wavefolder:CONTROL_CLAMP', ['DCLOW FIRST THIRD SCHOTTKY', 'DCHIGH THIRD SECOND SCHOTTKY']),
        ):
            changed = self.changed(role, pins={'1': 'FIRST', '2': 'SECOND', '3': 'THIRD'})
            with self.subTest(role=role), patch.object(model, 'family', return_value=changed):
                lines = model.common().splitlines()
                for line in expected:
                    self.assertIn(line, lines)

    def test_distinct_source_nodes_cannot_alias_after_spice_conversion(self):
        original = next(p for p in self.family.parts if p.attributes.get('Role') == 'wavefolder:BIAS_PNP')
        for node in ('CURRENT/SOURCE', 'current_source', '0', 'gnd', 'GND', 'P_12V', 'NC_0_2', 'nc_1_15'):
            changed = self.changed('wavefolder:BIAS_PNP', pins={**original.pins, '3': node})
            with self.subTest(node=node), patch.object(model, 'family', return_value=changed), \
                    self.assertRaisesRegex(ValueError, 'node collision'):
                model.common()

    def test_numeric_node_double_zero_is_not_ground(self):
        original = next(p for p in self.family.parts if p.attributes.get('Role') == 'wavefolder:BIAS_PNP')
        changed = self.changed('wavefolder:BIAS_PNP', pins={**original.pins, '3': '00'})
        with patch.object(model, 'family', return_value=changed):
            self.assertIn('QBIAS 00 BASE EMITTER GENERIC_PNP', model.common().splitlines())

    def test_unsupported_identity_dnp_or_pinset_fails(self):
        for role in ('wavefolder:BIAS_PNP', 'wavefolder:CONTROL_CLAMP', 'wavefolder:PRE_GAIN_MAX'):
            for changes in ({'symbol': 'Wrong:Part'}, {'prefix': 'WRONG'}, {'unit': 9},
                            {'dnp': True}, {'pins': {'1': None, '2': 'A', '3': 'B'}}):
                with self.subTest(role=role, changes=changes), \
                        patch.object(model, 'family', return_value=self.changed(role, **changes)), \
                        self.assertRaisesRegex(ValueError, 'identity/pins'):
                    model.common()

    def test_missing_and_duplicate_fixture_fail_before_oracle(self):
        role = 'wavefolder:BIAS_PNP'
        original = next(p for p in self.family.parts if p.attributes.get('Role') == role)
        for parts in (tuple(p for p in self.family.parts if p is not original),
                      self.family.parts + (replace(original, key='duplicate'),)):
            with patch.object(model, 'family', return_value=replace(self.family, parts=parts)), \
                    patch.object(model, 'invoke') as invoke:
                with self.assertRaisesRegex(ValueError, 'unique'):
                    model.main()
                invoke.assert_not_called()

    def test_trim_fixture_requires_nominal_value_and_tied_wiper_end(self):
        for changes in ({'value': '20 kΩ'},
                        {'pins': {'1': 'PRE_GAIN_TRIM', '2': 'PRE_GAIN_SUM', '3': 'OTHER'}}):
            with self.subTest(changes=changes), \
                    patch.object(model, 'family', return_value=self.changed('wavefolder:PRE_GAIN_MAX', **changes)), \
                    self.assertRaisesRegex(ValueError, 'mid-trim'):
                model.common()


if __name__ == '__main__':
    unittest.main()
