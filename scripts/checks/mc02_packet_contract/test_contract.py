"""Mutation tests for evidence reconciliation, with no native/model run."""
import copy
import unittest

import contract


class PacketContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded = contract.load(contract.ROOT)

    def setUp(self):
        self.manifest, self.historical, self.candidate = copy.deepcopy(self.loaded[:3])
        self.projection = self.loaded[3]

    def check(self, revision=None):
        return contract.reconcile(self.manifest, revision or self.manifest['historical_revision'],
                                  self.historical, self.candidate, self.projection)

    def test_real_data_keeps_case_and_scope_boundaries(self):
        r = self.check()
        self.assertEqual(r['formal_gate_status'], 'NOT ASSESSED')
        self.assertFalse(r['model_recalculated'])
        self.assertFalse(r['native_run'])
        self.assertEqual(len(r['unplaced']), 26)
        self.assertEqual(len(r['not_shown_latches']), 31)
        self.assertEqual(r['cases']['candidate']['numeric_ratios'], 56)
        self.assertEqual(len(r['cases']['candidate']['intentional_nulls']), 5)
        self.assertNotEqual(r['cases']['historical']['current_cases_A']['P'],
                            r['cases']['candidate']['current_cases_A']['P'])

    def test_procedure_amendment_has_separate_exact_source_identity(self):
        r=self.check()['cases']['candidate']
        self.assertEqual(r['source_revision'],'5620eea27dd2e3232f4ba81a4592660c3f439a26')
        self.assertEqual(r['engineering_revision'],'2c53715d49a4a7639723595590d1fd4eeb3a3c1f')
        self.assertEqual(r['procedure_amendment'],r['source_revision'])
        self.assertEqual(self.manifest['candidate_pins'][contract.THREADING],
                         '22b19d117ee0f9ea946b83a5c47cc0abbbd024757d229ae129e8cae338cee3a7')

    def test_amendment_cannot_change_geometry_or_cases(self):
        original=self.candidate[contract.THREADING]
        for section in ('links','latch','counts'):
            amended=copy.deepcopy(original)
            if section=='links':amended['links'][0]['id']='changed'
            elif section=='latch':amended['latch']['not_shown'].pop()
            else:amended['counts']['holding_hand']=0
            with self.assertRaisesRegex(ValueError,'non-method data'):
                contract.verify_amendment(original,amended)

    def test_amendment_does_not_hide_deleted_producer_pin(self):
        original=self.candidate[contract.THREADING];amended=copy.deepcopy(original)
        del amended['provenance']['pins']['files_sha256']['scripts/stack/fixings/procedure.py']
        with self.assertRaisesRegex(ValueError,'missing procedure producer pin'):
            contract.verify_amendment(original,amended)

    def test_amendment_cannot_restore_tool_alternative(self):
        original=self.candidate[contract.THREADING];amended=copy.deepcopy(original)
        next(r for r in amended['steps'] if r['n']==7)['do']='Close with one fingertip or a plastic tool.'
        with self.assertRaisesRegex(ValueError,'manual method regressed'):
            contract.verify_amendment(original,amended)

    def test_wrong_historical_revision_refused(self):
        with self.assertRaisesRegex(ValueError, 'wrong historical revision'):
            self.check(self.manifest['candidate_revision'])

    def test_current_case_conflation_refused(self):
        branches = self.candidate[contract.ELECTRICAL]['ground_share']['branches']
        p = next(r for r in branches if r['branch'] == 'P')
        p['worst_contact_A']['all_posts_open'] = p['worst_contact_A']['one_post_open']
        with self.assertRaisesRegex(ValueError, 'current-case conflation'):
            self.check()

    def test_missing_unplaced_member_refused(self):
        rows = self.candidate[contract.GATE]['replacement']['footprints']
        next(r for r in rows if r['step'] == 'no position')['step'] = 'placed'
        with self.assertRaisesRegex(ValueError, 'unplaced set changed'):
            self.check()

    def test_missing_latch_member_refused(self):
        self.candidate[contract.THREADING]['latch']['not_shown'].pop()
        with self.assertRaisesRegex(ValueError, 'latch set changed'):
            self.check()

    def test_null_is_not_zero_ratio(self):
        next(r for r in self.candidate[contract.ELECTRICAL]['links']
             if r['ratio'] is None)['ratio'] = 0.0
        with self.assertRaisesRegex(ValueError, 'null classification'):
            self.check()

    def test_null_class_change_even_with_matching_projection_refused(self):
        link = next(r for r in self.candidate[contract.GATE]['links'] if r['id'] == 'O-K-O1')
        for pos in link['positions']:
            if pos['kind'] == 'signal':
                pos['class'] = 'ANALOGUE'
        electrical = self.candidate[contract.ELECTRICAL]
        next(r for r in electrical['links'] if r['id'] == 'O-K-O1')['signals_by_class'] = {'ANALOGUE': 7}
        electrical['record_projection_sha256'] = self.projection['candidate'](
            [r for r in self.candidate[contract.GATE]['links'] if not r.get('gone')])
        self.candidate[contract.INPUTS]['link_record']['projection_sha256'] = electrical['record_projection_sha256']
        with self.assertRaisesRegex(ValueError, 'null classification'):
            self.check()

    def test_consumed_geometry_drift_refused(self):
        next(r for r in self.candidate[contract.GATE]['links'] if not r.get('gone'))['cable_length_mm'] += 1
        with self.assertRaisesRegex(ValueError, 'projection mismatch'):
            self.check()

    def test_candidate_projection_cannot_rebind_historical_case(self):
        self.projection = dict(self.projection)
        self.projection['historical'] = self.projection['candidate']
        with self.assertRaisesRegex(ValueError, 'historical: consumed projection mismatch'):
            self.check()

    def test_null_with_missing_reference_is_not_intentional(self):
        next(r for r in self.candidate[contract.ELECTRICAL]['links']
             if r['ratio'] is None)['pairs_without_reference'] = ['UNKNOWN']
        with self.assertRaisesRegex(ValueError, 'unexplained null'):
            self.check()


if __name__ == '__main__':
    unittest.main()
