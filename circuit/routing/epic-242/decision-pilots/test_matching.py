import copy
import unittest
import matching as m


def fixture(net='N', groups=None):
    return {'board_sha256': 'fixture', 'pads': [
        {'uuid': u, 'ref': 'R'+u, 'pad': '1', 'net': net, 'xy': [i*1000000, 0],
         'poly': [[i*1000000, 0]], 'layers': ['F.Cu']}
        for i, u in enumerate(('a', 'b', 'c'))],
        'islands': {net: groups or [['a', 'track-a'], ['b', 'c', 'track-b']]},
        'tracks': [{'uuid': 'track-a'}, {'uuid': 'track-b'}], 'vias': [], 'open_edges': 1}


class MatchedDemandTests(unittest.TestCase):
    def test_connected_k_is_partition_debt_not_improvement(self):
        k, c = fixture(groups=[['a', 'b', 'c']]), fixture()
        self.assertEqual(m.classify(k, c, 'N', ['a', 'b']), 'PARTITION_INDUCED_REPAIR')
        with self.assertRaisesRegex(ValueError, 'not matched open demand'):
            m.require_matched(k, c, 'N', ['a', 'b'])

    def test_preconnected_candidate_is_not_routed_gain(self):
        with self.assertRaisesRegex(ValueError, 'CANDIDATE_ALREADY_CONNECTED'):
            m.require_matched(fixture(), fixture(groups=[['a', 'b', 'c']]), 'N', ['a', 'b'])

    def test_absent_open_table_is_not_invented_demand(self):
        k = fixture(); k['islands'] = {}
        with self.assertRaisesRegex(ValueError, 'not matched open demand'):
            m.require_matched(k, k, 'N', ['a', 'b'])

    def test_identity_and_geometry_mutations(self):
        for key, value in [('ref', 'FORGED'), ('pad', '2'), ('net', 'WRONG'), ('xy', [8, 9]), ('layers', ['B.Cu']), ('uuid', 'unknown')]:
            with self.subTest(key=key):
                c = fixture(); c['pads'][0][key] = value
                with self.assertRaisesRegex(ValueError, 'anchor identity/geometry mismatch'):
                    m.require_matched(fixture(), c, 'N', ['a', 'b'])

    def test_missing_native_group_member_fails(self):
        c = fixture(); c['islands']['N'][0].remove('a')
        with self.assertRaisesRegex(ValueError, 'native group member'):
            m.require_matched(fixture(), c, 'N', ['a', 'b'])

    def test_focus_has_exact_anchors_and_keeps_all_geometry(self):
        d = fixture(); original = copy.deepcopy(d)
        row = {'net_token': 'N', 'anchor_records': d['pads'][:2]}
        f = m.focused(d, {'targets': {'signal': row}})
        self.assertEqual(f['islands']['N'], [['a'], ['b']])
        for key in ('pads', 'tracks', 'vias'):
            self.assertEqual(f[key], d[key])
        self.assertEqual(d, original)

    def test_alternate_remote_or_group_omission_rejected_by_manifest(self):
        expected = {'anchors': ['a', 'b'], 'original_group': ['b', 'c', 'track-b'],
                    'ground_pads': ['a', 'b', 'c'], 'partition_obligations': [['a', 'c']]}
        for key, value in [('anchors', ['a', 'c']), ('original_group', ['b', 'c']),
                           ('ground_pads', ['a', 'b']), ('partition_obligations', [])]:
            changed = {**expected, key: value}
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'manifest/group/return'):
                m.validate_published(changed, expected)

    def test_raw_count_decrease_does_not_close_fixed_pair(self):
        d, after = fixture(), fixture(); after['open_edges'] = 0
        result = m.closure_diagnostic(d, after, 'N', ['a', 'b'])
        self.assertFalse(result['exact_pair_closed'])
        self.assertFalse(result['accepted'])

    def test_pair_closure_does_not_fabricate_native_acceptance(self):
        result = m.closure_diagnostic(fixture(), fixture(groups=[['a', 'b', 'c']]), 'N', ['a', 'b'])
        self.assertTrue(result['exact_pair_closed'])
        self.assertFalse(result['accepted'])

    def test_all_source_connected_ground_equivalences_have_zero_credit(self):
        k = fixture('AGND', [['a', 'b', 'c']]); c = fixture('AGND')
        debt = m.return_debt(k, c, c['pads'])
        self.assertEqual(len(debt), 3)
        self.assertEqual(sum(x['classification'] == 'PARTITION_INDUCED_REPAIR' for x in debt), 2)
        self.assertTrue(all(x['baseline_improvement_credit'] == 0 for x in debt))

    def test_removed_copper_and_fabricated_acceptance_rejected(self):
        for patch in [{'removed_uuids': ['track-a']}, {'accepted': True}, {'board_sha256': 'wrong'}]:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                m.validate_proposal({'board_sha256': 'fixture', 'removed_uuids': [], **patch}, fixture())


class PostAuditTests(unittest.TestCase):
    def domain(self, d):
        return {'targets': {'signal': {'net_token': 'N', 'anchor_records': d['pads'][:2]}},
                'boards': {'C': {'source_connected_return_obligations': [
                    {'net_token': 'N', 'anchors': ['b', 'c'], 'baseline_improvement_credit': 0}],
                    'source_connected_rail_obligations': []}}}

    def test_matched_closure_with_return_debt_is_not_coupled_success(self):
        from evaluate_matched import evaluate_pairs
        b = fixture(); a = fixture(groups=[['a', 'b'], ['c']])
        result = evaluate_pairs(b, a, a, self.domain(b), 'C')
        self.assertEqual(result['exact_matched_closures'], 1)
        self.assertEqual(result['outstanding_obligations'], 1)
        self.assertFalse(result['coupled_connectivity_success'])
        self.assertFalse(result['accepted'])

    def test_fresh_mismatch_rejected(self):
        from evaluate_matched import evaluate_pairs
        b = fixture(); a = fixture(groups=[['a', 'b', 'c']])
        with self.assertRaisesRegex(ValueError, 'fresh exact pair mismatch'):
            evaluate_pairs(b, a, b, self.domain(b), 'C')

    def test_coupled_connectivity_is_still_not_adoption(self):
        from evaluate_matched import evaluate_pairs
        b = fixture(); a = fixture(groups=[['a', 'b', 'c']])
        result = evaluate_pairs(b, a, a, self.domain(b), 'C')
        self.assertTrue(result['coupled_connectivity_success'])
        self.assertFalse(result['adopted'])

    def test_method_epoch_drift_rejected(self):
        from unittest.mock import patch
        receipt = {'domain': 'O1', 'board': 'K1402', 'spec_sha256': 'spec',
                   'matched_demands_sha256': 'ledger', 'tool_sha256': {'tool': 'version'}}
        with patch.object(m.check, 'digest', return_value='ledger'), patch.object(m, 'tool_hashes', return_value={'tool': 'version'}):
            m.validate_fixture_method(receipt, {'spec_sha256': 'spec'}, 'O1', 'K1402')
            for key, value in [('spec_sha256', 'old'), ('matched_demands_sha256', 'old'), ('tool_sha256', {})]:
                with self.subTest(key=key), self.assertRaises(ValueError):
                    m.validate_fixture_method({**receipt, key: value}, {'spec_sha256': 'spec'}, 'O1', 'K1402')

    def test_route_requires_admission_before_search(self):
        from unittest.mock import patch
        import route_matched
        with patch.dict('os.environ', {}, clear=True), self.assertRaisesRegex(ValueError, 'requires separately admitted'):
            route_matched.guarded()

    def test_wrong_numerical_environment_rejected(self):
        from unittest.mock import patch
        import route_matched
        with patch.object(route_matched, 'version', return_value='wrong'), self.assertRaisesRegex(ValueError, 'numerical environment version drift'):
            route_matched.numerical_versions()


if __name__ == '__main__':
    unittest.main()
