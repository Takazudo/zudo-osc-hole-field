"""An ideal algebra result must not survive a changed captured subgraph."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from design.spec.modules.offset import family
from design.spec.modules.offset_model_contract import model_contract
from design.spec.modules import run_offset_spice


class OffsetModelSourceTests(unittest.TestCase):
    def setUp(self):
        self.family = family()

    def change(self, role, **changes):
        return tuple(replace(p, **changes) if p.attributes.get('Role') == role else p
                     for p in self.family.parts)

    def test_canonical_capture_and_nonfunctional_placement_change(self):
        expected = model_contract(self.family.parts)
        moved = tuple(replace(p, x=p.x+1) for p in self.family.parts)
        self.assertEqual(model_contract(moved), expected)
        self.assertIn('three-input summer', expected['included'])

    def test_every_checked_primitive_identity_is_bound(self):
        checked = model_contract(self.family.parts)['checked_parts']
        for part in self.family.parts:
            role = part.attributes.get('Role')
            if role not in checked:
                continue
            wrong_kind = ('zudo-osc-hole-field:C0603C101J5GACTU' if part.prefix != 'C'
                          else 'zudo-osc-hole-field:RT0603BRD07100KL')
            for changes in ({'prefix': 'WRONG'}, {'symbol': wrong_kind},
                            {'symbol': 'other-library:' + part.symbol.split(':', 1)[1]},
                            {'unit': 0 if part.prefix == 'U' else 1}):
                with self.subTest(role=role, changes=changes), self.assertRaisesRegex(ValueError, 'identity'):
                    model_contract(self.change(role, **changes))

    def test_resistor_to_capacitor_swap_fails_before_oracle_or_write(self):
        # Same role, value and endpoints previously admitted the wrong primitive.
        bad = self.change('offset:R_SUM_FB', prefix='C',
                          symbol='zudo-osc-hole-field:C0603C101J5GACTU')
        with patch('design.spec.modules.offset.family', return_value=replace(self.family, parts=bad)), \
                patch.object(run_offset_spice, 'run_case') as run, \
                patch.object(run_offset_spice.Path, 'write_text') as write:
            with self.assertRaisesRegex(ValueError, 'passive identity'):
                run_offset_spice.main()
            run.assert_not_called()
            write.assert_not_called()

    def test_pot_body_contacts_remain_explicitly_unconnected(self):
        part = next(p for p in self.family.parts if p.attributes.get('Role') == 'bipolar_attenuverter:RV')
        series = next(p for p in self.family.parts if p.attributes.get('Role') == 'bipolar_attenuverter:R_W')
        for pin in ('4', '5'):
            for net in (series.pins['2'], part.pins['2'], 'AGND'):
                with self.subTest(pin=pin, net=net), self.assertRaisesRegex(ValueError, 'pot source'):
                    model_contract(self.change('bipolar_attenuverter:RV', pins={**part.pins, pin: net}))
        for pins in ({key: value for key, value in part.pins.items() if key != '4'},
                     {**part.pins, '6': None}):
            with self.subTest(pins=pins), self.assertRaisesRegex(ValueError, 'pot source'):
                model_contract(self.change('bipolar_attenuverter:RV', pins=pins))

    def test_wrong_summer_wire_is_rejected_before_any_model_execution(self):
        bad = self.change('offset:R_SUM_MANUAL', pins={'1': 'AGND', '2': 'SUM_NODE'})
        with patch('design.spec.modules.offset.family', return_value=replace(self.family, parts=bad)), \
                patch.object(run_offset_spice, 'run_case') as run:
            with self.assertRaisesRegex(ValueError, 'connectivity changed'):
                run_offset_spice.main()
            run.assert_not_called()

    def test_swapped_amplifier_inputs_are_rejected(self):
        part = next(p for p in self.family.parts if p.attributes.get('Role') == 'offset:SUM')
        pins = dict(part.pins)
        pins['9'], pins['10'] = pins['10'], pins['9']
        with self.assertRaisesRegex(ValueError, 'amplifier connectivity'):
            model_contract(self.change('offset:SUM', pins=pins))

    def test_missing_duplicate_dnp_and_extra_feedback_branches_fail(self):
        role = 'offset:R_SUM_MANUAL'
        original = next(p for p in self.family.parts if p.attributes.get('Role') == role)
        variants = [tuple(p for p in self.family.parts if p is not original),
                    self.family.parts+(replace(original, key=original.key+'duplicate'),),
                    self.change(role, dnp=True),
                    self.family.parts+(replace(original, key='extra', attributes={'Role': 'extra'}),)]
        for parts in variants:
            with self.subTest(count=len(parts)), self.assertRaises(ValueError):
                model_contract(parts)

    def test_coherent_private_node_aliases_fail_but_private_renames_pass(self):
        pot = next(p for p in self.family.parts if p.attributes.get('Role') == 'bipolar_attenuverter:RV')
        series = next(p for p in self.family.parts if p.attributes.get('Role') == 'bipolar_attenuverter:R_W')
        for original in (pot.pins['2'], series.pins['2']):
            def renamed(target):
                return tuple(replace(p, pins={pin: target if net == original else net
                                             for pin, net in p.pins.items()})
                             for p in self.family.parts)
            model_contract(renamed('PRIVATE_RENAMED'))
            for target in ('IN_BUFFER', 'IN_REMOTE', 'MANUAL_OFFSET', 'OFFSET_BUFFER',
                           'AGND', 'ATTEN_SUM', 'ATTEN_OUT', 'SUM_NODE', 'SUM_NEG',
                           'RESTORE_NODE', 'OUT_INTERNAL'):
                with self.subTest(original=original, target=target), \
                        self.assertRaisesRegex(ValueError, 'private wiper/sense'):
                    model_contract(renamed(target))

    def test_extra_branch_cannot_reuse_a_checked_part_identity(self):
        original = next(p for p in self.family.parts if p.attributes.get('Role') == 'offset:R_SUM_MANUAL')
        extra = replace(original, attributes={'Role': 'extra'},
                        pins={'1': 'AGND', '2': 'SUM_NODE'})
        with self.assertRaisesRegex(ValueError, 'duplicate part identities'):
            model_contract(self.family.parts + (extra,))

    def test_source_value_and_wiper_polarity_changes_fail(self):
        with self.assertRaisesRegex(ValueError, 'value/connectivity'):
            model_contract(self.change('offset:R_SUM_FB', value='200 kΩ'))
        pot = next(p for p in self.family.parts if p.attributes.get('Role') == 'bipolar_attenuverter:RV')
        pins = dict(pot.pins)
        pins['1'], pins['3'] = pins['3'], pins['1']
        with self.assertRaisesRegex(ValueError, 'pot source'):
            model_contract(self.change('bipolar_attenuverter:RV', pins=pins))


if __name__ == '__main__':
    unittest.main()
