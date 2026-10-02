"""Reject source/model drift before running an old ideal filter deck."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from design.spec.modules.noise import family
from design.spec.modules.noise_model_contract import model_contract
from design.spec.modules import run_noise_spice


class NoiseModelSourceTests(unittest.TestCase):
    def setUp(self):
        self.capture = family()

    def changed(self, role, **changes):
        return tuple(replace(p, **changes) if p.attributes.get('Role') == role else p
                     for p in self.capture.parts)

    def test_canonical_and_placement_only_changes(self):
        expected = model_contract(self.capture.parts)
        self.assertEqual(len(expected['checked_parts']), 20)
        self.assertEqual(model_contract(tuple(replace(p, x=p.x+1) for p in self.capture.parts)), expected)

    def test_every_filter_value_change_is_rejected(self):
        for p in self.capture.parts:
            role = p.attributes.get('Role', '')
            if role in model_contract(self.capture.parts)['checked_parts'] and role.startswith(('noise:R_', 'noise:C_')):
                with self.subTest(role=role), self.assertRaisesRegex(ValueError, 'value/connectivity'):
                    model_contract(self.changed(role, value='changed'))

    def test_rewired_colour_input_fails_before_oracle_or_file_write(self):
        bad = self.changed('noise:R_BROWN_IN', pins={'1': 'PINK_SIGNAL', '2': 'BROWN_SUM'})
        with patch('design.spec.modules.noise.family', return_value=replace(self.capture, parts=bad)), \
                patch.object(run_noise_spice.subprocess, 'run') as run, \
                patch.object(run_noise_spice.Path, 'write_text') as write:
            with self.assertRaisesRegex(ValueError, 'value/connectivity'):
                run_noise_spice.main()
            run.assert_not_called()
            write.assert_not_called()

    def test_passive_primitive_identity_is_not_inferred_from_role_or_value(self):
        for changes in ({'prefix': 'C'}, {'symbol': 'Wrong:C0603C101J5GACTU'}, {'symbol': 'Wrong:RT0603BRD07100KL'}, {'unit': 1}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'passive identity'):
                model_contract(self.changed('noise:R_WHITE_RECON', **changes))

    def test_amplifier_polarity_and_identity(self):
        p = next(p for p in self.capture.parts if p.attributes.get('Role') == 'noise:BROWN_LEAK')
        pins = dict(p.pins)
        pins['12'], pins['13'] = pins['13'], pins['12']
        for changes in ({'pins': pins}, {'symbol': 'Wrong:OPA4197IPWR'}, {'symbol': 'Wrong:OPA4196IDR'}, {'prefix': 'R'}, {'unit': 5}):
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, 'amplifier'):
                model_contract(self.changed('noise:BROWN_LEAK', **changes))

    def test_missing_dnp_duplicate_and_extra_internal_parts(self):
        p = next(p for p in self.capture.parts if p.attributes.get('Role') == 'noise:R_BROWN_IN')
        variants = [tuple(q for q in self.capture.parts if q is not p),
                    self.changed('noise:R_BROWN_IN', dnp=True),
                    self.capture.parts + (replace(p, key='duplicate'),),
                    self.capture.parts + (replace(p, attributes={'Role': 'extra'}),),
                    self.capture.parts + (replace(p, key='extra', attributes={'Role': 'extra'}),)]
        for parts in variants:
            with self.subTest(count=len(parts)), self.assertRaises(ValueError):
                model_contract(parts)

    def test_excluded_level_value_is_not_filter_evidence(self):
        self.assertEqual(model_contract(self.capture.parts),
                         model_contract(self.changed('noise:R_BROWN_LEVEL_IN', value='30 kΩ')))


if __name__ == '__main__':
    unittest.main()
