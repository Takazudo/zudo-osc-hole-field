"""Focused conservation and rejection checks; no native execution or mocks of KiCad."""
import copy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('power_contract', Path(__file__).with_name('build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)


class PowerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report, cls.harnesses, cls.packages = build.assemble()
        cls.config = build.read('design/partition/core-split/power/input.json')

    def test_independent_expected_counts(self):
        self.assertEqual(len(self.packages), 5904)
        self.assertEqual(sum(p['source_board'] == 'K' for p in self.packages), 3385)
        self.assertEqual(self.harnesses['positions_per_endpoint'],
                         {'signal':505,'AGND':376,'+12V':6,'-12V':6,'+5V':6,'NC':4})
        for option, counts in [('two', [1795,1590]), ('three', [919,1134,1332])]:
            boards = self.report['options'][option]['boards']
            self.assertEqual([b['package_count'] for b in boards.values()], counts)
            self.assertEqual(sum(b['fitted_ic_count'] for b in boards.values()), 425)
            self.assertEqual(sum(b['existing_harness_count'] for b in boards.values()), 191)
            self.assertEqual(sum(b['fitted_return_contact_count'] for b in boards.values()), 1903)

    def test_dnp_not_charged_and_power_parts_not_duplicated(self):
        expected = {'C106','C146','C147','C148','C206','C246','C247','C248'}
        self.assertEqual({p['ref'] for p in self.packages if p['dnp']}, expected)
        for option in self.report['options'].values():
            self.assertEqual(option['capacitance']['fitted_nominal_uF'],
                             {'+12V':49.9,'-12V':42.7,'+5V':24.5})
        self.assertEqual(len(self.report['power_parts']),13)
        self.assertTrue(all(p['two_owner'] == p['three_owner'] == 'KA' for p in self.report['power_parts']))

    def test_conservation_and_reserves_have_known_values(self):
        expected = {'two': [71.9,79.1,47.3], 'three':[67.2,74.4,42.6]}
        for key, option in self.report['options'].items():
            self.assertEqual(list(option['capacitance']['remaining_nominal_uF'].values()),expected[key])
            self.assertEqual(option['total_planning_mA'],
                             {'+12V':1534.819166,'-12V':1435.56866,'+5V':224.286445})
            for rail, total in option['total_planning_mA'].items():
                independent = sum(b['module_responsibility_planning_mA'][rail] for b in option['boards'].values())
                independent += option['noncore_only_planning_mA'][rail] + option['global_allowances_charged_once_mA'][rail]
                self.assertAlmostEqual(total, independent, places=5)
        self.assertEqual(self.report['conductor_screen']['one_edge_rail_plus_return_drop_mV'],
                         {'+12V':15.321,'-12V':15.058,'+5V':11.113})
        self.assertTrue(all(v > 20 for v in self.report['conductor_screen']['rejected_two_full_serial_allowances_mV'].values()))

    def test_new_namespace_and_both_endpoint_reservations(self):
        old = {e['id'] for h in self.harnesses['harnesses'] for e in h['endpoints']}
        for key, count in [('two',1),('three',2)]:
            option = self.report['options'][key]
            self.assertEqual(len(option['new_feeds']),count)
            terminals = []
            for feed in option['new_feeds']:
                self.assertEqual([w['net'] for w in feed['wires']],['+12V','-12V','+5V','AGND','AGND','AGND'])
                self.assertEqual(len(feed['endpoint_envelopes']),2)
                terminals += [t for w in feed['wires'] for t in w['terminal_ids']]
            self.assertEqual(len(set(terminals)),12*count)
            self.assertFalse(old.intersection(terminals))
            self.assertEqual(option['mechanical_budget']['new_main_lands'],12*count)

    def test_missing_or_duplicate_module_rejected(self):
        for change in ('missing','duplicate'):
            config = copy.deepcopy(self.config)
            config['options']['two']['KA'].pop() if change == 'missing' else config['options']['two']['KB'].append('O1')
            with self.assertRaisesRegex(ValueError,'missing/duplicate core module'):
                build.assemble(config)

    def test_split_reference_rejected(self):
        config = copy.deepcopy(self.config)
        config['options']['two']['KA'].remove('O1')
        config['options']['two']['KB'].append('O1')
        with self.assertRaisesRegex(ValueError,'split oscillator/Kelvin reference'):
            build.assemble(config)

    def test_new_feed_repacking_and_double_auxiliary_rejected(self):
        config = copy.deepcopy(self.config)
        config['new_feed']['net_order'][0:2] = ['-12V','+12V']
        with self.assertRaisesRegex(ValueError,'new feed pin order'):
            build.assemble(config)
        config = copy.deepcopy(self.config)
        config['auxiliary_reserve_mA_per_rail']['two']['KB'] = 20
        with self.assertRaisesRegex(ValueError,'global auxiliary allowance'):
            build.assemble(config)

    def test_changed_existing_pin_map_rejected(self):
        original = build.read
        def changed(path):
            result = original(path)
            if path == 'design/partition/partition.json':
                result['connectors'][0]['pin_map']['1'] = 'NC'
            return result
        with patch.object(build,'read',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'endpoint pin order mismatch'):
                build.assemble()

    def test_split_bypass_rejected(self):
        original = build.read
        def changed(path):
            result = original(path)
            if path == 'design/reports/io-partition.json':
                row = next(p for p in result['physical_packages'] if p['ref'] == 'C301')
                row['decouples_ref'] = 'U101'  # H1 belongs to KB in two-core option.
            return result
        with patch.object(build,'read',side_effect=changed):
            with self.assertRaisesRegex(ValueError,'split bypass'):
                build.assemble()

    def test_manifest_covers_direct_symbol_and_standard_dependencies(self):
        paths = build.source_hashes()
        self.assertIn('design/standard/electrical-standard.json',paths)
        self.assertIn('design/standard/parts-shortlist.json',paths)
        self.assertIn('symbols/src/OPA4196IDR.kicad_sym',paths)
        self.assertTrue(all(str(p.relative_to(build.ROOT)) in paths
                            for p in (build.ROOT/'symbols/src').glob('*.kicad_sym')))

    def test_immutable_comparison_rejects_symmetric_pin_and_pose_changes(self):
        partition = build.read('design/partition/partition.json')
        original_hash = build.digest((build.ROOT/'design/partition/partition.json').read_bytes())
        # Conservation alone cannot detect a matching edit at both cable ends.
        first_harness = partition['harnesses'][0]
        for h in partition['connectors']:
            if h['id'] in first_harness['header_ids']:
                h['pin_map']['1'],h['pin_map']['2'] = h['pin_map']['2'],h['pin_map']['1']
                h['center_mm'][0] += 1
        altered_hash = build.digest(build.canonical(partition).encode())
        path = 'design/partition/partition.json'
        self.assertEqual(build.changed_at_ref({path:original_hash},self.config['source_main_sha']),[])
        self.assertEqual(build.changed_at_ref({path:altered_hash},self.config['source_main_sha']),[path])


if __name__ == '__main__':
    unittest.main()
