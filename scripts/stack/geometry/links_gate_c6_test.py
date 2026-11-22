"""Regression tests for the ruled DA-03 c6 conductor pass over the frozen record."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
sys.path.insert(0, str(ROOT / 'scripts/stack/link_electrical'))

import links_gate_c6 as c6
import link_ratios as lr
import link_electrical as le
import ds62_table as d62
import c6_report


class C6PassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads((ROOT / lr.RECORD).read_text())
        snapshot = json.loads((ROOT / 'design/stack/geometry/links/link-gate-c6-source.json').read_text())
        cls.assert_source = snapshot['source_sha256']
        saved = {x['id']: x for x in snapshot['links']}
        cls.original['links'] = [saved.get(x['id'], x) for x in cls.original['links']]
        cls.original.pop('c6', None)
        cls.inputs = le.load_inputs(ROOT / 'design/stack/link-electrical/inputs.json')
        cls.baseline = d62.build(cls.inputs)['baseline']

    def test_frozen_geometry_and_signal_identity(self):
        self.assertEqual(self.assert_source, c6.SOURCE_SHA256)
        revised = c6.apply(copy.deepcopy(self.original), self.inputs)
        self.assertEqual(c6.geometry_digest(self.original), c6.geometry_digest(revised))
        self.assertEqual(c6.signal_digest(self.original), c6.signal_digest(revised))
        # 62 since MC04-S7 Revision 11: the stage 7 pairs JL-K-26 and JL-K-27 form JL-K-JL-L09
        self.assertEqual(len([x for x in revised['links'] if not x.get('gone')]), 62)

    def test_all_link_ratios_and_ruled_orders(self):
        revised = c6.apply(copy.deepcopy(self.original), self.inputs)
        original = {x['id']: x for x in self.original['links']}
        for link in revised['links']:
            if link.get('gone'):
                continue
            self.assertFalse(c6.order_errors(link, original[link['id']]), link['id'])
            result = lr.link_row(self.inputs, link, self.baseline)
            if result['ratio'] is not None:
                self.assertLessEqual(result['ratio'], 1.0, link['id'])

    def test_idempotent_and_rider_provenance(self):
        once = c6.apply(copy.deepcopy(self.original), self.inputs)
        twice = c6.apply(copy.deepcopy(once), self.inputs)
        self.assertEqual(once, twice)
        old = {x['id']: x for x in self.original['links']}
        for link in once['links']:
            for direction in ('riders_in', 'riders_out'):
                for rider in link.get(direction, []):
                    if rider not in old[link['id']].get(direction, []):
                        self.assertEqual(rider['reason'], 'coupling')

    def test_ds78_exception_refuses_arbitrary_split(self):
        revised = c6.apply(copy.deepcopy(self.original), self.inputs)
        original = {x['id']: x for x in self.original['links']}
        link = copy.deepcopy(next(x for x in revised['links'] if x['id'] == c6.L07))
        p = link['positions']
        p[23], p[24] = dict(p[24], pos=24), dict(p[23], pos=25)
        self.assertTrue(any('DS-78' in e for e in c6.order_errors(link, original[c6.L07])))

    def test_historical_snapshot_cannot_relabel_changed_source(self):
        current = json.loads((ROOT / lr.RECORD).read_text())
        snapshot = json.loads((ROOT / 'design/stack/geometry/links/link-gate-c6-source.json').read_text())
        self.assertEqual(c6_report.verified_source(current, snapshot)['links'][0]['id'], current['links'][0]['id'])
        bad = copy.deepcopy(snapshot)
        bad['links'][0]['positions'][0]['net'] = '/ALTERED'
        with self.assertRaisesRegex(ValueError, 'historical record hash mismatch'):
            c6_report.verified_source(current, bad)


if __name__ == '__main__':
    unittest.main()
