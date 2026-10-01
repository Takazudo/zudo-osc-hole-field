import copy
import json
import unittest
from pathlib import Path
from scripts.pcbgen.control_project_source import derive


class ControlProjectSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = Path('boards/osc-control/osc-control-ground-bare-v2.kicad_pro').read_bytes()
        cls.definition = Path('design/partition/control-ground-feasibility/osc-control.json').read_bytes()

    def test_exact_native_stopped_run_project_matches_independent_source_derivation(self):
        path = Path('boards/osc-control/osc-control-ground-feasibility-v1.kicad_pro')
        expected, receipt = derive(self.original, self.definition, path.name)
        self.assertEqual(expected, path.read_bytes())
        before, after = json.loads(self.original), json.loads(expected)
        self.assertEqual(before['board'], after['board'])
        self.assertTrue(receipt['board_design_rules_unchanged'])
        # Stripping exactly the three declared deltas leaves every other
        # source project property unchanged, including board clearances.
        after['meta']['filename'] = before['meta']['filename']
        after['net_settings']['classes'] = before['net_settings']['classes']
        after['net_settings']['netclass_patterns'] = before['net_settings']['netclass_patterns']
        self.assertEqual(before, after)

    def test_foreign_class_semantics_or_destination_are_rejected(self):
        source = json.loads(self.original)
        source['net_settings']['classes'][0]['diff_pair_width'] = .4
        with self.assertRaisesRegex(ValueError, 'constructor'):
            derive(json.dumps(source).encode(), self.definition, 'candidate.kicad_pro')
        source = json.loads(self.original)
        source['net_settings']['netclass_patterns'] = [{'netclass': 'Other', 'pattern': '*'}]
        with self.assertRaisesRegex(ValueError, 'unexpected class'):
            derive(json.dumps(source).encode(), self.definition, 'candidate.kicad_pro')
        with self.assertRaisesRegex(ValueError, 'basename'):
            derive(self.original, self.definition, '../other.kicad_pro')


if __name__ == '__main__':
    unittest.main()
