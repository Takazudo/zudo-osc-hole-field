import copy
import unittest
from scripts.checks.check_catalogue_publication import check_publication


class PublicationCoverageTests(unittest.TestCase):
    def setUp(self):
        self.lines = [{'line_id': 'fitted', 'dnp': False, 'function': 'part'},
                      {'line_id': 'dnp', 'dnp': True, 'function': 'part'}]
        self.records = [{'line_id': 'fitted', 'record_id': 'parent'},
                        {'line_id': 'dnp', 'record_id': 'child', 'parent_record_id': 'parent'}]
        self.selection = {'recordIds': ['parent'], 'documentSelections': []}
        self.decisions = {'schema_version': 1, 'renderer': {'version': '0.1.0'},
                          'blocked_records': [{'record_id': 'child', 'reason': 'No model',
                                               'blockers': ['model-required'], 'unblock': 'Optional model support'}],
                          'intentional_exclusions': [], 'document_constraints': []}

    def check(self, version='0.1.0', sources=None, facts=None):
        return check_publication(self.lines, self.records, self.selection, self.decisions,
                                 sources or {}, facts or {}, version)

    def test_parent_selection_does_not_implicitly_publish_child(self):
        self.decisions['blocked_records'] = []
        with self.assertRaisesRegex(ValueError, 'missing=.*child'):
            self.check()

    def test_dnp_still_requires_a_publication_decision(self):
        self.assertEqual(self.check(), {'inventory': 2, 'published': 1, 'blocked': 1, 'excluded': 0})
        self.selection['recordIds'] = []
        with self.assertRaisesRegex(ValueError, 'missing=.*parent'):
            self.check()

    def test_stale_duplicate_blank_and_conflicting_exemptions_fail(self):
        original = copy.deepcopy(self.decisions)
        for change in ('stale', 'duplicate', 'blank', 'conflict'):
            self.decisions = copy.deepcopy(original)
            row = self.decisions['blocked_records'][0]
            if change == 'stale': row['record_id'] = 'retired'
            if change == 'duplicate': self.decisions['blocked_records'].append(copy.deepcopy(row))
            if change == 'blank': row['reason'] = ' '
            if change == 'conflict': row['record_id'] = 'parent'
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check()

    def test_renderer_upgrade_requires_blocker_review(self):
        with self.assertRaisesRegex(ValueError, 'renderer changed'):
            self.check('0.2.0')

    def test_explicit_future_exclusion_is_counted_separately(self):
        self.decisions['blocked_records'] = []
        self.decisions['intentional_exclusions'] = [{'record_id': 'child', 'reason': 'Reviewed research-only exclusion'}]
        self.assertEqual(self.check()['excluded'], 1)

    def test_family_pdf_cannot_become_exact_datasheet_or_primary_claim(self):
        self.lines[0]['function'] = 'part; FAMILY applicability UNSOURCED'
        self.selection['documentSelections'] = [{'recordId': 'parent', 'sourceId': 'mirror', 'documentKind': 'specification'}]
        self.decisions['document_constraints'] = [{'record_id': 'parent', 'source_id': 'mirror',
            'document_kind': 'specification', 'source_title': 'Actual cover title',
            'authority_class': 'MANUFACTURER_MIRROR', 'applicability_fact_id': 'gap',
            'applicability_verdict': 'UNSOURCED', 'required_record_terms': ['FAMILY', 'UNSOURCED']}]
        sources = {'mirror': {'document_title': 'Actual cover title', 'authority_class': 'MANUFACTURER_MIRROR'}}
        facts = {'gap': {'verdict': 'UNSOURCED', 'conditions': 'FAMILY applicability UNSOURCED'}}
        self.check(sources=sources, facts=facts)
        self.selection['documentSelections'][0]['documentKind'] = 'datasheet'
        with self.assertRaises(ValueError): self.check(sources=sources, facts=facts)
        self.selection['documentSelections'][0]['documentKind'] = 'specification'
        facts['gap']['verdict'] = 'PASS - primary-source confirmed'
        with self.assertRaises(ValueError): self.check(sources=sources, facts=facts)
        facts['gap']['verdict'] = 'UNSOURCED'
        self.lines[0]['function'] = 'part'
        with self.assertRaises(ValueError): self.check(sources=sources, facts=facts)


if __name__ == '__main__':
    unittest.main()
