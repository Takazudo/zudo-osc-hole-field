"""Allocation regressions against the captured instrument and worksheet rows."""
import copy
import unittest

from scripts.schgen.build_rail_ledger import build, no_duplicate_keys, read_allocation


class RailLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = read_allocation()

    def test_complete_ledger_and_ref5050_pin(self):
        report = build(self.source)
        self.assertEqual(report['physical_package_count'], 650)
        self.assertEqual(len(report['worksheet_loads']), 347)
        self.assertEqual(report['selected_domain']['id'], 'EXT')
        self.assertEqual(report['selected_domain']['module_count'], 33)
        self.assertEqual(report['selected_domain']['worksheet_load_count'], 347)
        self.assertEqual(report['selected_domain']['physical_ic_package_count'], 650)
        self.assertEqual(report['original_single_source_ceiling_mA'], {'+12V': 960, '-12V': 640, '+5V': 400})
        for rail in ('+12V', '-12V', '+5V'):
            self.assertIsNone(report['guaranteed_whole_instrument_maximum_mA'][rail])
            self.assertIsNone(report['measured_source_capacity_mA'][rail])
        refs = [p for p in report['physical_ic_packages'] if p['instance'] == 'H1' and p['symbol'] == 'REF5050AIDR']
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['supply_pins']['2'], '+12V')
        self.assertNotIn('+5V', refs[0]['rails'])
        self.assertGreater(sum(x['-12V'] for x in report['two_feed_planning_mA'].values()), 2 * 640)

    def test_missing_load_is_rejected(self):
        source = copy.deepcopy(self.source)
        source['load_domain_assignment'].pop('H1:0')
        with self.assertRaisesRegex(ValueError, 'missing/extra per-load allocation'):
            build(source)

    def test_duplicate_load_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate allocation key'):
            no_duplicate_keys([('H1:0', {'feed': 'A'}), ('H1:0', {'feed': 'B'})])

    def test_wrong_rail_is_rejected(self):
        source = copy.deepcopy(self.source)
        source['load_domain_assignment']['H1:0']['rails'] = ['+5V']
        with self.assertRaisesRegex(ValueError, 'wrong feed or rail for load'):
            build(source)
        source = copy.deepcopy(self.source)
        source['required_draft_allowances']['H1:reference']['rail'] = '+5V'
        with self.assertRaisesRegex(ValueError, 'wrong rail for H1:reference'):
            build(source)

    def test_missing_allowance_and_module_are_rejected(self):
        source = copy.deepcopy(self.source)
        del source['required_draft_allowances']['inlet:B:+5V']
        with self.assertRaisesRegex(ValueError, 'missing/extra required allowances'):
            build(source)
        source = copy.deepcopy(self.source)
        del source['module_feed_assignment']['H2']
        with self.assertRaisesRegex(ValueError, 'missing/extra/invalid complete-module'):
            build(source)


if __name__ == '__main__':
    unittest.main()
