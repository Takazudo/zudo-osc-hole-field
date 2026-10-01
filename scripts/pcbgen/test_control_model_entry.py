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

    def test_exact_coupling_and_complete_own_load_profile_sets(self):
        for include, count in ((False, 130), (True, 344)):
            prerequisite = {**self.prerequisite, 'diagnostic_include_loads': include}
            geometry = self.geometry(include)
            control_model_entry.select_ports(geometry, prerequisite)
            self.assertEqual(len(geometry['ports']), count)
            for mutation in ('omit', 'face', 'duplicate'):
                changed = copy.deepcopy(geometry)
                if mutation == 'omit':
                    changed['ports'].pop(0)
                elif mutation == 'face':
                    changed['ports'][0]['layer'] = 0
                else:
                    changed['ports'].append(changed['ports'][0])
                with self.subTest(include=include, mutation=mutation), self.assertRaises(ValueError):
                    control_model_entry.select_ports(changed, prerequisite)

    def test_entry_requires_actual_receipt_and_immutable_input_without_port_limit(self):
        source = Path('not-a-real-model.json')
        native_bytes = json.dumps(self.native).encode()
        with self.assertRaisesRegex(ValueError, 'successful full native receipt'):
            control_model_entry.enter(source, native_bytes, None, None, True, 0)
        with self.assertRaisesRegex(ValueError, 'port-limit 0'):
            control_model_entry.enter(source, native_bytes, 'receipt', 'manifest', True, 1)
        good = {'dependency_sha256': {str(source.resolve()): hashlib.sha256(native_bytes).hexdigest()}, **self.prerequisite}
        with patch.object(control_model_entry, 'require_native_prerequisite', return_value=good):
            result = control_model_entry.enter(source, native_bytes, 'receipt', 'manifest', True, 0)
            self.assertTrue(result['diagnostic_include_loads'])
        bad = {**good, 'dependency_sha256': {str(source.resolve()): '0'*64}}
        with patch.object(control_model_entry, 'require_native_prerequisite', return_value=bad), self.assertRaisesRegex(ValueError, 'immutable'):
            control_model_entry.enter(source, native_bytes, 'receipt', 'manifest', True, 0)



if __name__ == '__main__':
    unittest.main()
