"""An apparently easy pair cannot replace a retained open native demand."""
import copy
import hashlib
import json
import unittest

from check_cohorts import group_receipts


class NativeGroupBinding(unittest.TestCase):
    def setUp(self):
        self.target = {'net_token': 'signal', 'anchor_records': [{'uuid': 'a'}, {'uuid': 'b'}]}
        self.dump = {'islands': {'signal': [['track', 'a', 'via'], ['b']]}}

    def test_full_copper_members_are_bound_not_only_pads(self):
        receipt = group_receipts(self.dump, self.target)[0]
        expected = hashlib.sha256(json.dumps(['a', 'track', 'via'], separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(receipt['all_member_count'], 3)
        self.assertEqual(receipt['all_members_sha256'], expected)
        altered = copy.deepcopy(self.dump)
        altered['islands']['signal'][0].remove('via')
        self.assertNotEqual(group_receipts(altered, self.target)[0], receipt)

    def test_connected_omitted_and_missing_groups_are_not_open(self):
        for groups in ({}, {'signal': [['a', 'b']]}, {'signal': [['a']]}, {'signal': [['a'], ['a'], ['b']]}):
            with self.subTest(groups=groups), self.assertRaises(AssertionError):
                group_receipts({'islands': groups}, self.target)

    def test_overlapping_or_duplicate_copper_groups_are_rejected(self):
        for groups in ([['a', 'track'], ['b', 'track']], [['a', 'a'], ['b']]):
            with self.subTest(groups=groups), self.assertRaises(AssertionError):
                group_receipts({'islands': {'signal': groups}}, self.target)


if __name__ == '__main__':
    unittest.main()
