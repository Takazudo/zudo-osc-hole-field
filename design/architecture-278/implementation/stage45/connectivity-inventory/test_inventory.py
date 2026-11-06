"""Fail closed when native evidence, local topology or interface assignments drift."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('stage45_inventory', HERE / 'generate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projection = json.loads((HERE / 'open-partitions.json').read_text())
        cls.report = m.build()

    def test_all_117_are_local_failures(self):
        r = self.report['inventory']
        self.assertEqual(r['affected_nets'], 90)
        self.assertEqual(r['local_open_edges'], 117)
        self.assertEqual(r['intentional_local_open_edges'], 0)
        self.assertEqual(r['open_edges_by_category'], {
            'ground': 14, 'local circuit': 35, 'local feed on interface net': 68})

    def test_common_circuit_is_not_common_manufactured_board(self):
        r = self.report['reuse']
        self.assertEqual(r['package_pairs'], 36)
        self.assertEqual(r['physical_contacts_per_cell'], 115)
        self.assertEqual(r['bijective_native_net_pairs'], 33)
        self.assertEqual(set(r['pose_exceptions']), {'R3204', 'R3209'})
        self.assertFalse(r['identical_manufactured_PCB_established'])

    def test_wrong_board_rejected(self):
        p = copy.deepcopy(self.projection); p['board_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'provenance'): m.inventory(p)

    def test_pad_renet_rejected(self):
        p = copy.deepcopy(self.projection)
        key = next(k for k, v in p['objects'].items() if v['kind'] == 'pad')
        p['objects'][key]['net'] = 'WRONG'
        with self.assertRaisesRegex(ValueError, 'native net'): m.inventory(p)

    def test_component_merge_cannot_hide_open(self):
        p = copy.deepcopy(self.projection)
        groups = next(v for v in p['groups'].values() if len(v) > 2)
        groups[0] += groups.pop()
        with self.assertRaisesRegex(ValueError, 'open count'): m.inventory(p)

    def test_duplicate_membership_rejected(self):
        p = copy.deepcopy(self.projection); groups = p['groups']['AGND']
        groups[1].append(groups[0][0])
        with self.assertRaisesRegex(ValueError, 'two components'): m.inventory(p)

    def test_semantic_alias_tamper_rejected(self):
        original = m.read
        def corrupt(path):
            d = original(path)
            if path == 'design/reports/board-net-tokens.json': d[next(iter(d))] = '/wrong'
            return d
        with patch.object(m, 'read', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'alias hash'): m.inventory(self.projection)

    def test_harness_wrong_mate_pin_rejected(self):
        original = m.read
        def corrupt(path):
            d = original(path)
            if path == 'design/partition/partition.json':
                h = next(c for c in d['connectors'] if c['id'] == 'JL-K-1-K')
                h['pin_map']['7'] = '/wrong'
            return d
        with patch.object(m, 'read', side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, 'mate pin'): m.inventory(self.projection)

    def test_deterministic_report(self):
        self.assertEqual((HERE / 'inventory.json').read_text(), m.encoded(self.report))
        self.assertEqual((HERE / 'OPEN-NETS.md').read_text(), m.table(self.report))

    def test_failed_searches_are_not_repairs(self):
        for folder, name in [('first-attempt', 'ground-proposal.json'), ('second-attempt', 'ground-v2-proposal.json')]:
            p = json.loads((HERE / 'evidence' / folder / name).read_text())
            s = json.loads((HERE / 'evidence' / folder / 'ground-search.json').read_text())
            self.assertEqual(p['board_sha256'], m.BOARD_HASH)
            self.assertEqual(p['copper'], [])
            self.assertEqual(p['removed_uuids'], [])
            self.assertEqual(s['failed_links'], 1)

    def test_local_geometry_replay_when_available(self):
        if not all((m.ROOT / path).exists() for path in (m.SNAPSHOT, m.BOARD)):
            self.skipTest('large ignored native snapshot or board unavailable; source checks still run')
        self.assertEqual(json.loads((HERE / 'geometry.json').read_text()), m.export_geometry())

    def test_local_native_projection_matches_when_available(self):
        if not all((m.ROOT / path).exists() for path in (m.SNAPSHOT, m.BOARD)):
            self.skipTest('large ignored native snapshot or board unavailable; source checks still run')
        self.assertEqual(self.projection, m.export_snapshot())


if __name__ == '__main__': unittest.main()
