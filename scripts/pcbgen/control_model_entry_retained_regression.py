import copy
import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import control_model_entry
from scripts.pcbgen.control_ground_inventory import audit
from scripts.pcbgen import test_control_ground_inventory as fixture_module


class ControlModelEntryTests(unittest.TestCase):
    def setUp(self):
        fixture = fixture_module.ControlGroundInventoryTests()
        fixture.setUp()
        self.native = fixture.native
        inventory = audit(fixture.native, fixture.manifest, fixture.partition, fixture.io)
        self.prerequisite = {'full_source_ground_inventory': inventory,
            'selected_contacts': [row for row in inventory['contacts'] if row['kind'] != 'own_load']}

    def geometry(self, include):
        rows = self.prerequisite['full_source_ground_inventory']['contacts'] if include else self.prerequisite['selected_contacts']
        return {'data': self.native, 'ports': [{'ref': row['ref'], 'pad': row['pad'], 'layer': 3,
            'kind': 'load' if row['kind'] == 'own_load' else row['kind']} for row in rows]}

    def test_actual_native_positive_and_generic_missing_receipt_bypass_rejection(self):
        source = Path('.circuit-cache/issue38-recovery/control-feasibility-v4/ground-feasibility-geometry.json')
        receipt = source.with_name('ground-feasibility-native-receipt.json')
        manifest = Path('design/partition/control-ground-feasibility/osc-control.receipt.json')
        stale = Path('.circuit-cache/issue38-recovery/control-feasibility-v3/ground-feasibility-geometry.json')
        with self.assertRaisesRegex(ValueError,'prerequisite dependency changed'):
            control_model_entry.enter(stale,stale.read_bytes(),stale.with_name('ground-feasibility-native-receipt.json'),manifest,True,0)
        result = control_model_entry.enter(source, source.read_bytes(), receipt, manifest, True, 0)
        self.assertEqual(result['full_source_ground_inventory']['connected_count'], 344)
        self.assertEqual(len(result['selected_contacts']), 130)
        from scripts.pcbgen import solve_conductor_volume as driver
        with patch.object(driver, 'extract') as extractor:
            with self.assertRaisesRegex(ValueError, 'successful full native receipt'):
                driver.solve(source, Path('.circuit-cache/P-entry-test-no-output.json'), 2., .25, 1, 0, True)
            extractor.assert_not_called()
        # A genuine bare zero-error receipt still cannot pass the generic
        # command path, even when the caller supplies both P arguments.
        bare = Path('.circuit-cache/issue38-recovery/control-ground-bare-v2')
        with patch.object(driver, 'extract') as extractor:
            with self.assertRaisesRegex(ValueError, 'successful full native'):
                driver.solve(bare/'bare-geometry.json', Path('.circuit-cache/P-entry-test-no-output.json'),
                    2., .25, 1, 0, True, control_receipt=bare/'bare-native-receipt.json', control_manifest=manifest)
            extractor.assert_not_called()


if __name__ == '__main__':
    unittest.main()
