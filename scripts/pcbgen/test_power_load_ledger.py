"""Native feed lists cannot replace the independent source contact inventory."""
import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.pcbgen.power_load_ledger import mapping


class PowerLedgerTests(unittest.TestCase):
    def setUp(self):
        self.documents = {
            'design/reports/io-partition.json': {
                'physical_packages': [{'ref': r, 'dnp': False, 'instance': 'X', 'symbol': 'U'} for r in ('U1', 'U2')],
                'allowed_crossings': [{'net': '+5V', 'members': [{'ref': r, 'pin': '1'} for r in ('U1', 'U2')]}]},
            'design/power/rail-ledger.json': {'physical_ic_packages': []},
            'design/partition/partition-input.json': {'load_distribution': {'rail_max_A': {'+5V': .5}}},
            'design/partition/partition.json': {'boards': [{'id': 'left', 'board_key': 'JL'}],
                'assignment': {'components': [{'ref': r, 'board': 'JL', 'fitted': True} for r in ('U1', 'U2')]}}}
        self.native = {'board_sha256': 'board', 'board_id': 'left',
            'main_rail_members': {'+5V': ['one', 'two']},
            'items': [{'ref': r, 'pad': '1', 'net': '+5V', 'uuid': u} for r, u in [('U1', 'one'), ('U2', 'two')]]}
        self.feeds = {'board_sha256': 'board', 'fitted_rail_pad_feeds': [
            dict(item, connected_to_load_land=True) for item in self.native['items']]}

    def run_mapping(self, native, feeds):
        docs = self.documents
        with patch.object(Path, 'read_text', lambda p: json.dumps(docs[str(p)])), \
             patch.object(Path, 'read_bytes', lambda p: json.dumps(docs[str(p)]).encode()):
            return mapping(native, feeds)

    def test_exact_source_inventory_is_reconciled(self):
        report = self.run_mapping(self.native, self.feeds)
        self.assertEqual(report['independent_expected_source_contact_count'], 2)
        self.assertEqual(report['fitted_rail_pad_count'], 2)

    def test_omitted_wrong_duplicate_and_disconnected_contacts_fail(self):
        for defect in ('omit_both', 'wrong_uuid', 'duplicate_feed', 'main_membership'):
            native, feeds = copy.deepcopy(self.native), copy.deepcopy(self.feeds)
            if defect == 'omit_both':
                native['items'].pop(); feeds['fitted_rail_pad_feeds'].pop()
            elif defect == 'wrong_uuid':
                feeds['fitted_rail_pad_feeds'][0]['uuid'] = 'wrong'
            elif defect == 'duplicate_feed':
                feeds['fitted_rail_pad_feeds'].append(copy.deepcopy(feeds['fitted_rail_pad_feeds'][0]))
            else:
                native['main_rail_members']['+5V'].remove('one')
            with self.subTest(defect=defect), self.assertRaises(ValueError):
                self.run_mapping(native, feeds)


if __name__ == '__main__': unittest.main()
