"""MULT bindings, topology and partial-current report contract."""
import unittest

from design.spec.modules.mult import family, panel_bindings, specification
from design.spec.modules.build_mult_current import build as current_report
from scripts.schgen.core import designator


class MultContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.family = family()

    def test_all_locked_jacks_and_input_led_bind_once(self):
        rows = panel_bindings()
        panel_parts = [part for part in self.family.parts if part.panel_refs]
        self.assertEqual(len(rows), 10)
        self.assertEqual(len(panel_parts), 5)
        self.assertEqual([item.index for item in specification()[1]], [31, 32])
        for instance in specification()[1]:
            resolved = {designator(part, instance) for part in panel_parts}
            expected = {row['ref'] for row in rows if row['instance'] == instance.name}
            self.assertEqual(resolved, expected)
            uids = {part.attributes['PanelUid'].replace('${SHEETNAME}', instance.name)
                    for part in panel_parts}
            self.assertEqual(uids, {row['uid'] for row in rows if row['instance'] == instance.name})
        self.assertEqual({row['uid'] for row in rows if row['uid'].startswith('L:')},
                         {'L:B1.IN.mag', 'L:B2.IN.mag'})

    def test_protected_input_and_three_independent_precision_outputs(self):
        switches = [part for part in self.family.parts
                    if part.symbol.endswith('ADG5412FBRUZ') and part.unit == 1]
        self.assertEqual(len(switches), 1)
        self.assertEqual(switches[0].pins['3'], 'IN_TIP')
        self.assertEqual(switches[0].pins['2'], 'IN_PROTECTED')
        jacks = [part for part in self.family.parts if part.symbol.endswith('WQP518MA')]
        self.assertEqual(len(jacks), 4)
        self.assertTrue(all(part.pins['TN'] is None for part in jacks))
        amps = [part for part in self.family.parts
                if part.symbol.endswith('OPA4197IPWR') and part.unit in (1, 2, 3, 4)]
        self.assertEqual(len(amps), 4)
        positive_nets = [part.pins[{1: '3', 2: '5', 3: '10', 4: '12'}[part.unit]] for part in amps]
        self.assertCountEqual(positive_nets, ['IN_SENSE', 'IN_BUFFER', 'IN_BUFFER', 'IN_BUFFER'])
        self.assertIn('IN_PROTECTED', self.family.sensitive_nets)
        self.assertIn('IN_SENSE', self.family.sensitive_nets)
        self.assertNotIn('IN_SENSE', self.family.global_nets)

    def test_packages_complete_and_current_report_is_honest(self):
        packages = {}
        for part in self.family.parts:
            if part.symbol.endswith(('OPA4196IDR', 'OPA4197IPWR')):
                packages.setdefault((part.symbol, part.ordinal), set()).add(part.unit)
        self.assertEqual(len([key for key in packages if key[0].endswith('OPA4197IPWR')]), 1)
        self.assertEqual(len([key for key in packages if key[0].endswith('OPA4196IDR')]), 1)
        self.assertTrue(all(units == {1, 2, 3, 4, 5} for units in packages.values()))
        report = current_report()
        self.assertEqual(report['IC_packages_per_instance'], {
            'ADG5412FBRUZ': 1, 'OPA4196IDR': 1, 'OPA4197IPWR': 1})
        row = report['instances'][0]
        self.assertEqual(row['typical_mA_per_rail'], {'+12V': 5.86, '-12V': 5.46, '+5V': .05})
        self.assertEqual(row['planning_maximum_mA_per_rail'], {'+12V': 11.05, '-12V': 10.45, '+5V': .075})
        self.assertTrue(all(value is None for value in row['guaranteed_maximum_mA_per_rail'].values()))


if __name__ == '__main__':
    unittest.main()
