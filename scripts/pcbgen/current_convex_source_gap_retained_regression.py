import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.pcbgen.current_convex_source_gap import SOURCE, classify, checked_source, inventory


class CurrentConvexSourceGapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = checked_source()
        cls.row = next(
            row for board in cls.source['boards']
            for row in board['own_source_contacts'] if row['family'] == 'convex_SMD'
        )

    def test_complete_reviewed_epoch_remains_blocked(self):
        result = inventory()
        self.assertEqual(result['contact_count'], 3620)
        self.assertEqual(result['face_counts'], {'B.Cu': 3365, 'F.Cu': 255})
        self.assertTrue(all(
            row['coefficient_status'] == 'BLOCKED_PHYSICAL_SOURCE_INPUTS'
            and row['net_to_uniform_profile_energy_ohm_upper'] is None
            and row['unit_normalized_redistribution_energy_ohm_upper'] is None
            for board in result['boards'] for row in board['contacts']
        ))

    def test_geometry_and_physical_claims_fail_closed(self):
        for mutation in (
            {'physical_support_qualified': True},
            {'actual_or_unproved_drill_uuids': ['a-drill']},
            {'nearby_drill_uuids': ['a-drill'], 'drill_separation': {}},
            {'area_mm2_rational_bounds': [[1, 1], [1, 1]]},
            {'face': 'F.Cu'},
            {'family': 'PTH'},
        ):
            with self.subTest(mutation=mutation):
                row = copy.deepcopy(self.row)
                row.update(mutation)
                with self.assertRaises(ValueError):
                    classify(row)

    def test_modified_aggregate_is_rejected_before_classification(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'source.json'
            source = copy.deepcopy(self.source)
            source['boards'][0]['own_source_contacts'][0]['ref'] = 'CHANGED'
            path.write_text(json.dumps(source))
            with self.assertRaisesRegex(ValueError, 'reviewed v6 aggregate bytes changed'):
                checked_source(path)

    def test_original_source_exists(self):
        self.assertTrue(SOURCE.is_file())


if __name__ == '__main__':
    unittest.main()
