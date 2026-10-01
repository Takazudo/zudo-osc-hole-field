"""Depth changes must update reported clearance or fail stale source assertions."""
import copy
import json
import unittest
from scripts.checks.partition35_mechanical import ROOT, core_rear_envelope


class CoreRearEnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.source = json.loads((ROOT/'design/partition/partition-input.json').read_text())
        self.allowance = json.loads((ROOT/'design/mechanical/core-rear-allowance.json').read_text())

    def test_current_proposal_and_consistent_depth_change(self):
        original = core_rear_envelope(self.source, self.allowance)
        self.assertEqual(original['nominal_back_component_clearance_mm'], 13.4)
        changed = copy.deepcopy(self.source)
        changed['boards']['K']['face_z_mm'] = -80
        changed['boards']['K']['thickness_mm'] = 2
        changed['enclosure']['inside_depth_mm'] = 100
        changed['enclosure']['rear_clearance_from_K_B_face_mm'] = 18
        result = core_rear_envelope(changed, {'component_height_ceiling_mm': 6})
        self.assertEqual(result['back_face_z_mm'], -82)
        self.assertEqual(result['nominal_back_component_clearance_mm'], 12)
        self.assertEqual(result['enclosure_inside_depth_mm'], 100)

    def test_stale_source_summary_is_rejected(self):
        self.source['boards']['K']['face_z_mm'] = -80
        with self.assertRaisesRegex(ValueError, 'stale enclosure'):
            core_rear_envelope(self.source, self.allowance)

    def test_negative_clearance_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'negative component clearance'):
            core_rear_envelope(self.source, {'component_height_ceiling_mm': 19})
