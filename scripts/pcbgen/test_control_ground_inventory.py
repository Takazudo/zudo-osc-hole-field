import copy
import unittest
from scripts.pcbgen.control_ground_inventory import audit


class ControlGroundInventoryTests(unittest.TestCase):
    def setUp(self):
        packages = [{'ref': 'U'+str(i), 'dnp': False} for i in range(214)]
        headers = [{'pcb_reference': 'J'+str(i), 'board': 'P', 'pin_map': {'2': 'AGND'}} for i in range(127)]
        lands = [{'reference': 'TP'+str(i), 'board': 'P', 'net': 'AGND', 'side': 'B.Cu', 'center_mm': [i*17, 179]} for i in range(3)]
        self.partition = {'boards': [{'id': 'osc-control', 'board_key': 'P'}],
            'assignment': {'components': [{'ref': row['ref'], 'board': 'P', 'fitted': True} for row in packages]},
            'connectors': headers, 'load_side_terminals': lands}
        self.io = {'physical_packages': packages, 'allowed_crossings': [{'net': 'AGND',
            'members': [{'ref': row['ref'], 'pin': '1'} for row in packages]}]}
        self.manifest = {'selected_P_ground_ports': [{'ref': row['pcb_reference'], 'pad': '2', 'side': 'B.Cu'} for row in headers],
            'all_P_main_lands': lands}
        pads = [(row['ref'], '1', [0, 0]) for row in packages]
        pads += [(row['pcb_reference'], '2', [0, 0]) for row in headers]
        pads += [(row['reference'], '1', [row['center_mm'][0]+100, 229]) for row in lands]
        items = [{'ref': ref, 'pad': pad, 'uuid': ref+':'+pad, 'net': 'AGND', 'copper': {'B.Cu': []}, 'xy_mm': xy} for ref, pad, xy in pads]
        self.native = {'board_id': 'osc-control', 'coordinate_frame': {'source_to_native_translation_mm': [100, 50]},
            'items': items, 'main_rail_members': {'AGND': [row['uuid'] for row in items]}}

    def test_every_own_load_GH_and_main_connectivity_is_mandatory(self):
        result = audit(self.native, self.manifest, self.partition, self.io)
        self.assertEqual(result['connected_count'], 344)
        for kind in ('own_load', 'GH', 'main'):
            changed = copy.deepcopy(self.native)
            uid = next(row['uuid'] for row in result['contacts'] if row['kind'] == kind)
            changed['main_rail_members']['AGND'].remove(uid)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'disconnected'):
                audit(changed, self.manifest, self.partition, self.io)

    def test_omitted_source_pad_wrong_face_and_duplicate_UUID_rejected(self):
        changed = copy.deepcopy(self.native)
        changed['items'].pop(0)
        with self.assertRaisesRegex(ValueError, 'contact mismatch'):
            audit(changed, self.manifest, self.partition, self.io)
        changed = copy.deepcopy(self.native)
        changed['items'][214]['copper'] = {'F.Cu': []}
        with self.assertRaisesRegex(ValueError, 'physical face'):
            audit(changed, self.manifest, self.partition, self.io)
        changed = copy.deepcopy(self.native)
        changed['items'][-1]['uuid'] = changed['items'][-2]['uuid']
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            audit(changed, self.manifest, self.partition, self.io)


if __name__ == '__main__':
    unittest.main()
