"""Power-budget decomposition controls."""
from pathlib import Path
import importlib.util, json, unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('power_contract_decompose', HERE / 'decompose.py')
decompose = importlib.util.module_from_spec(spec)
spec.loader.exec_module(decompose)


class DecompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = decompose.build()

    def test_committed_decomposition_matches_build(self):
        committed = json.loads((HERE / 'decomposition.json').read_text())
        self.assertEqual(committed, json.loads(json.dumps(self.data, ensure_ascii=False, default=sorted)))

    def test_parts_sum_to_canonical_planning(self):
        steps = self.data['budget_steps']
        for r in decompose.RAILS:
            self.assertAlmostEqual(steps['fixed_quiescent_and_static_planning_mA'][r]
                                   + steps['patch_signal_and_operation_planning_mA'][r],
                                   steps['canonical_planning_mA'][r], places=5)

    def test_requirements_unchanged(self):
        lv = self.data['levels']
        self.assertEqual(lv['continuous_requirement']['mA'], {'+12V': 1700, '-12V': 1600, '+5V': 300})
        self.assertEqual(lv['transient_requirement_20ms']['mA'], {'+12V': 2000, '-12V': 1900, '+5V': 400})
        self.assertEqual(lv['canonical_planning_all_upper_terms']['continuous_rule_result_mA'],
                         {'+12V': 1700, '-12V': 1600, '+5V': 300})

    def test_no_blanket_halving_of_analog_rails(self):
        lv = self.data['levels']
        for r in ('+12V', '-12V'):
            self.assertEqual(lv['heavy_realistic_patch']['mA'][r], lv['canonical_planning_all_upper_terms']['mA'][r])

    def test_lower_levels_are_not_requirements(self):
        lv = self.data['levels']
        self.assertIn('CANDIDATE', lv['explicit_usage_limit_candidate']['classification'])
        for name in ('normal_typical', 'heavy_realistic_patch', 'explicit_usage_limit_candidate'):
            self.assertIn('UNVERIFIED', lv[name]['classification'])
        self.assertTrue(all(v is None for v in self.data['measured'].values()))


if __name__ == '__main__':
    unittest.main()
