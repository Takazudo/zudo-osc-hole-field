"""Manual selector bindings, source isolation and partial-current report contract."""
import unittest

from design.spec.modules.manual_ab import family, panel_bindings, specification, SENSITIVE
from design.spec.modules.build_manual_ab_current import build as current_report
from scripts.schgen.core import designator


class ManualABContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = family()

    def test_locked_jacks_controls_and_indicators_bind_once(self):
        rows = panel_bindings()
        panel_parts = [part for part in self.family.parts if part.panel_refs]
        self.assertEqual(len(rows), 14)
        self.assertEqual(len(panel_parts), 7)
        self.assertEqual([item.index for item in specification()[1]], [33, 34])
        for instance in specification()[1]:
            self.assertEqual({designator(part, instance) for part in panel_parts},
                             {row['ref'] for row in rows if row['instance'] == instance.name})
            self.assertEqual({part.attributes['PanelUid'].replace('${SHEETNAME}', instance.name)
                              for part in panel_parts},
                             {row['uid'] for row in rows if row['instance'] == instance.name})
        toggles = {row['uid']: row for row in rows if row['uid'].endswith('.SELECT')}
        self.assertEqual(toggles['C:X1.SELECT']['x_mm'], 99.5)
        self.assertEqual(toggles['C:X2.SELECT']['x_mm'], 116.5)
        self.assertEqual(toggles['C:X1.SELECT']['y_mm'], 283.0)
        self.assertEqual(toggles['C:X2.SELECT']['y_mm'], 283.0)

    def test_each_raw_source_isolated_before_buffer_and_toggle(self):
        switches = [part for part in self.family.parts
                    if part.symbol.endswith('ADG5412FBRUZ') and part.unit == 1]
        self.assertEqual(len(switches), 2)
        self.assertEqual({part.pins['3'] for part in switches}, {'A_TIP', 'B_TIP'})
        self.assertEqual({part.pins['2'] for part in switches}, {'A_PROTECTED', 'B_PROTECTED'})
        toggle = next(part for part in self.family.parts if part.symbol.endswith('2MS1T1B1M2QES-5'))
        self.assertEqual(toggle.pins, {
            '1': 'SELECT_B_CONTACT', '2': 'SELECTOR_COMMON', '3': 'SELECT_A_CONTACT'})
        self.assertEqual(toggle.attributes['MPN'], '2MS1T1B1M2QES-5')
        resistors = {part.attributes['Role']: part for part in self.family.parts
                     if part.attributes.get('Role', '').startswith('manual_ab:R_SELECT_')}
        self.assertEqual(resistors['manual_ab:R_SELECT_A_SERIES'].value, '2.2 kΩ')
        self.assertEqual(resistors['manual_ab:R_SELECT_A_SERIES'].pins,
                         {'1': 'A_BUFFER', '2': 'SELECT_A_CONTACT'})
        self.assertEqual(resistors['manual_ab:R_SELECT_B_SERIES'].pins,
                         {'1': 'B_BUFFER', '2': 'SELECT_B_CONTACT'})
        self.assertEqual(resistors['manual_ab:R_SELECT_COMMON_BIAS'].pins,
                         {'1': 'SELECTOR_COMMON', '2': 'AGND'})
        self.assertEqual(resistors['manual_ab:R_SELECT_COMMON_BIAS'].value, '10 MΩ')
        self.assertFalse(any(net in {'A_TIP', 'B_TIP'} for net in toggle.pins.values()))

    def test_output_and_all_magnitude_monitors_are_buffered(self):
        jacks = [part for part in self.family.parts if part.symbol.endswith('WQP518MA')]
        self.assertEqual(len(jacks), 3)
        self.assertTrue(all(part.pins['TN'] is None for part in jacks))
        amps = [part for part in self.family.parts
                if part.symbol.endswith('OPA4197IPWR') and part.unit in (1, 2, 3, 4)]
        self.assertEqual(len(amps), 4)
        positive_nets = [part.pins[{1: '3', 2: '5', 3: '10', 4: '12'}[part.unit]] for part in amps]
        self.assertCountEqual(positive_nets, ['A_SENSE', 'B_SENSE', 'SELECTOR_COMMON', 'AGND'])
        outputs = [part for part in self.family.parts
                   if part.symbol.endswith('OPA4197IPWR') and part.pins.get('8') == 'OUT_BUFFERED']
        self.assertEqual(len(outputs), 1)
        indicators = [part for part in self.family.parts if part.symbol.endswith('OPA4196IDR')]
        monitored = {part.pins[number] for part in indicators
                     for number in ('3', '5', '10', '12') if number in part.pins}
        self.assertTrue({'A_BUFFER', 'B_BUFFER', 'OUT_BUFFERED'} <= monitored)
        self.assertEqual(set(self.family.sensitive_nets), set(SENSITIVE))
        self.assertTrue(set(SENSITIVE).isdisjoint(self.family.global_nets))

    def test_complete_packages_and_current_report_is_honest(self):
        packages = {}
        for part in self.family.parts:
            if part.symbol.endswith(('OPA4196IDR', 'OPA4197IPWR')):
                packages.setdefault((part.symbol, part.ordinal), set()).add(part.unit)
        self.assertEqual(len([key for key in packages if key[0].endswith('OPA4197IPWR')]), 1)
        self.assertEqual(len([key for key in packages if key[0].endswith('OPA4196IDR')]), 1)
        self.assertTrue(all(units == {1, 2, 3, 4, 5} for units in packages.values()))
        report = current_report()
        self.assertEqual(report['IC_packages_per_instance'], {
            'ADG5412FBRUZ': 2, 'OPA4196IDR': 1, 'OPA4197IPWR': 1})
        row = report['instances'][0]
        self.assertEqual(row['typical_mA_per_rail'], {'+12V': 7.1605, '-12V': 6.3605, '+5V': .1})
        self.assertEqual(row['planning_maximum_mA_per_rail'], {'+12V': 13.8505, '-12V': 12.6505, '+5V': .15})
        self.assertTrue(all(value is None for value in row['guaranteed_maximum_mA_per_rail'].values()))


if __name__ == '__main__':
    unittest.main()
