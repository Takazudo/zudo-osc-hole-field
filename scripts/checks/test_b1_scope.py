"""Existing-open attribution must not hide B1 splits or incomplete membership."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('b1_scope', ROOT / 'design/architecture-278/implementation/stage42/full-b1/scope.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def snapshot():
    return {'objects': {'a': {'kind': 'pad', 'ref': 'U3101', 'pin': '5', 'net': 'AGND'},
                        'b': {'kind': 'pad', 'ref': 'U9000', 'pin': '5', 'net': 'AGND'}},
            'groups': {'AGND': [['a'], ['b']]}, 'native_open_edges': 1}


class B1Scope(unittest.TestCase):
    def test_shared_open_is_not_b1_private_open(self):
        row = m.classify(snapshot(), {'U3101'})[0]
        self.assertEqual(row['classification'], 'shared ground openings')
        self.assertEqual(row['b1_components'], 1)
        self.assertEqual(row['components'], 2)

    def test_b1_split_remains_visible(self):
        s = snapshot();s['objects']['b']['ref'] = 'U3101'
        self.assertEqual(m.classify(s, {'U3101'})[0]['b1_components'], 2)

    def test_private_open_is_not_closed(self):
        s = snapshot();s['groups']['PRIVATE'] = s['groups'].pop('AGND')
        for v in s['objects'].values():v['net'] = 'PRIVATE'
        self.assertEqual(m.classify(s, {'U3101'})[0]['classification'], 'B1-associated open')

    def test_missing_or_duplicate_membership_rejected(self):
        for groups in ([['a']], [['a'], ['a', 'b']], [['a'], []]):
            s = snapshot();s['groups']['AGND'] = groups
            with self.assertRaises(ValueError):m.classify(s, {'U3101'})

    def test_wrong_count_or_net_rejected(self):
        for field in ('count', 'net'):
            s = snapshot()
            if field == 'count':s['native_open_edges'] = 0
            else:s['objects']['b']['net'] = 'OTHER'
            with self.assertRaises(ValueError):m.classify(s, {'U3101'})

    def test_missing_scope_rejected(self):
        with self.assertRaises(ValueError):m.classify(snapshot(), {'ABSENT'})

    def test_partially_missing_scope_rejected(self):
        with self.assertRaises(ValueError):m.classify(snapshot(), {'U3101', 'ABSENT'})

    def test_drc_count_mismatch_rejected(self):
        m.validate_drc_count(snapshot(), {'unconnected_items': [{}]})
        for items in ([], [{}, {}]):
            with self.assertRaises(ValueError):m.validate_drc_count(snapshot(), {'unconnected_items': items})
