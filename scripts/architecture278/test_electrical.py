import copy
import json
import unittest
from pathlib import Path
from electrical import evaluate, build, DIR

class ElectricalTest(unittest.TestCase):
    def setUp(self):
        self.data=json.loads((DIR/'electrical-input.json').read_text())
    def test_no_unknown_becomes_pass(self):
        self.assertTrue(evaluate(self.data)['physical_acceptance'].startswith('OPEN'))
    def test_old_budget_cannot_be_reset(self):
        self.data['limits']['rail_transfer_mohm']=2
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_five_branch_not_single_branch_capacitance(self):
        self.data['reference']['branch']['cable_pF']=900
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_probe_consumes_budget(self):
        self.data['reference']['shared_test_pF']=200
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_no_missing_segment(self):
        self.data['resistance_segments'].pop()
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_actual_violation_not_hidden(self):
        self.data['resistance_segments'][1]['actual_mohm']=2
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_negative_not_credit(self):
        self.data['reference']['branch']['cable_pF']=-80
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_segment_group_cannot_hide_rail_resistance(self):
        self.data['resistance_segments'][1]['group']='source'
        self.data['resistance_segments'][1]['actual_mohm']=20
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_finite_numeric_fields(self):
        for invalid in (float('nan'), float('inf'), -1, True, '0.1'):
            for section, field in [('reference', 'remote_length_mm'), ('reference', 'shared_test_pF')]:
                changed=copy.deepcopy(self.data)
                changed[section][field]=invalid
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):evaluate(changed)
            for field in ['actual_mohm', 'allocation_mohm']:
                changed=copy.deepcopy(self.data)
                changed['resistance_segments'][1][field]=invalid
                with self.subTest(field=field, invalid=invalid), self.assertRaises(ValueError):evaluate(changed)
    def test_preserved_length_and_step_targets(self):
        for field, changed_value in [('remote_limit_mm', 301), ('adjacent_step_target_uV', 2001)]:
            changed=copy.deepcopy(self.data)
            changed['reference'][field]=changed_value
            with self.subTest(field=field), self.assertRaises(ValueError):evaluate(changed)
    def test_required_allocation_not_null(self):
        self.data['resistance_segments'][1]['allocation_mohm']=None
        with self.assertRaises(ValueError):evaluate(self.data)
    def test_no_shared_source_double_count(self):
        report=build()
        self.assertEqual(report['load_cases'][2]['planning_mA']['+12V'],339.5)
        self.assertEqual(report['load_cases'][1]['planning_mA']['+12V'],151.4)
    def test_coverage_and_unknown_states(self):
        report=build(); source=json.loads((DIR/'source-ledger.json').read_text())
        self.assertEqual(len(report['device_coverage']),len(source['packages']))
        self.assertEqual(len({(p['instance'],p['ref']) for p in report['device_coverage']}),len(source['packages']))
        self.assertTrue(all(all(v is None for v in p['state_bounds_mA'].values()) for p in report['device_coverage']))
if __name__=='__main__':unittest.main()
