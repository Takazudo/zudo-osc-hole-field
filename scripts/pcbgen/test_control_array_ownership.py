import copy
import json
import unittest
from pathlib import Path
from scripts.pcbgen.control_array_ownership import validate
from scripts.pcbgen.plan_control_arrays import retained_path, ROOT


class ControlArrayOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads(Path('design/partition/control-ground-feasibility/main-via-plan.json').read_text())
        self.manifest = json.loads(Path('design/partition/control-ground-feasibility/osc-control.receipt.json').read_text())
        lands = {row['reference']: row for row in self.manifest['all_P_main_lands']}
        self.native = {'board_id': 'osc-control', 'board_sha256': self.plan['board_sha256'], 'items': [
            {'ref': row['ref'], 'pad': '1', 'net': row['net'], 'uuid': row['owning_pad_uuid'],
             'xy_mm': [lands[row['ref']]['center_mm'][0]+100, lands[row['ref']]['center_mm'][1]+50],
             'copper': {'B.Cu': []}} for row in self.plan['rows']]}

    def test_complete_named_original_grid_and_owner_binding(self):
        result = validate(self.plan, self.manifest, self.native)
        self.assertEqual(result['accepted_count'], 150)
        self.assertEqual(result['accounted_candidate_count'], 150)
        for key, value in [('net', 'FOREIGN'), ('owning_pad_uuid', 'foreign-owner')]:
            changed = copy.deepcopy(self.plan)
            changed['rows'][0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'owner/net/face'):
                validate(changed, self.manifest, self.native)

    def test_shifted_omitted_or_duplicate_site_rejected(self):
        changed = copy.deepcopy(self.plan)
        changed['rows'][0]['legal_sites'][0]['xy_mm'][0] += .01
        with self.assertRaisesRegex(ValueError, 'shifted'):
            validate(changed, self.manifest, self.native)
        changed = copy.deepcopy(self.plan)
        changed['rows'][0]['legal_sites'].pop()
        with self.assertRaisesRegex(ValueError, 'all 25'):
            validate(changed, self.manifest, self.native)
        changed = copy.deepcopy(self.plan)
        changed['rows'][0]['legal_sites'].append(changed['rows'][0]['legal_sites'][0])
        with self.assertRaisesRegex(ValueError, 'duplicated'):
            validate(changed, self.manifest, self.native)

    def test_docker_dependency_translation_confined_to_worktree(self):
        self.assertEqual(retained_path('/work/design/boards/osc-control.json'), ROOT/'design/boards/osc-control.json')
        with self.assertRaisesRegex(ValueError, 'outside'):
            retained_path('/work/../outside.json')
        with self.assertRaisesRegex(ValueError, 'outside'):
            retained_path('/tmp/unrelated.json')


if __name__ == '__main__':
    unittest.main()
