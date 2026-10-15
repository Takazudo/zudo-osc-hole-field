import copy
import json
import unittest

import stage11_assessment as study


class PredecessorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((study.OUT / 'scope.json').read_text())

    def test_complete_preserved_history(self):
        self.assertEqual(study.preserve(self.scope), 241)

    def test_cannot_drop_a_predecessor(self):
        changed = copy.deepcopy(self.scope)
        changed['preserved_prior_source_sha256'].pop(next(iter(changed['preserved_prior_source_sha256'])))
        with self.assertRaisesRegex(ValueError, 'inventory'):
            study.preserve(changed)

    def test_cannot_rehash_changed_history(self):
        changed = copy.deepcopy(self.scope)
        changed['preserved_prior_source_sha256'][next(iter(changed['preserved_prior_source_sha256']))] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'predecessor digest'):
            study.preserve(changed)

    def test_wrong_baseline(self):
        changed = copy.deepcopy(self.scope)
        changed['baseline_commit'] = 'main'
        with self.assertRaisesRegex(ValueError, 'baseline'):
            study.preserve(changed)

    def test_instrument_count_cannot_change(self):
        changed = copy.deepcopy(self.scope)
        changed['instrument_invariants']['OSC'] = 1
        with self.assertRaisesRegex(ValueError, 'instrument scope'):
            study.preserve(changed)

    def test_stale_or_absent_source_binding(self):
        for report in ({}, {'source_sha256': {'design/architecture-278/implementation/stage11/scope.json': '0' * 64}}):
            with self.assertRaisesRegex(ValueError, 'source binding'):
                study.bindings(report)

    def test_nonfinite_result_cannot_hide_in_nested_budget(self):
        for number in (float('nan'), float('inf'), -float('inf')):
            with self.assertRaisesRegex(ValueError, 'nonfinite'):
                study.finite({'budget': [{'resistance': number}]})
        study.finite({'budget': [None, 0.0, 1.0]})

    def test_domain_acceptance_cannot_be_promoted(self):
        for report in ({}, {'hardware_acceptance': True},
                       {'physical_acceptance': False, 'native': 'PASS'}):
            with self.assertRaisesRegex(ValueError, 'unreviewed'):
                study.acceptance(report)
        study.acceptance({'hardware_acceptance': False, 'physical': 'NOT RUN'})


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        old = study.OUT.parent / 'stage10'
        cls.inventory = json.loads((old / 'inventory-report.json').read_text())
        cls.graph = json.loads((old / 'interfaces-report.json').read_text())
        cls.old_electrical = json.loads((old / 'electrical-report.json').read_text())
        cls.identity = json.loads((study.OUT / 'identity-report.json').read_text())
        cls.electrical = json.loads((study.OUT / 'electrical-report.json').read_text())
        cls.support = json.loads((study.OUT / 'support-report.json').read_text())

    def test_complete_identity_and_path_composition(self):
        self.assertEqual(study.identities(self.identity, self.inventory)['candidate_assignments'], 20)
        self.assertEqual(study.endpoints(self.electrical, self.old_electrical, self.graph)['power_return_source_endpoints'], 106)

    def test_identity_cannot_omit_or_rewire(self):
        changed = copy.deepcopy(self.identity)
        changed['candidate_assignments'].pop('C7102')
        with self.assertRaisesRegex(ValueError, 'coverage'):
            study.identities(changed, self.inventory)
        changed = copy.deepcopy(self.identity)
        changed['candidate_assignments']['C7102']['pins']['1'] = '+12V'
        with self.assertRaisesRegex(ValueError, 'detached'):
            study.identities(changed, self.inventory)

    def test_capacitance_cannot_silently_increase_or_become_qualified(self):
        changed = copy.deepcopy(self.identity)
        changed['candidate_assignments']['C7102']['candidate_ratings']['value_SI'] = 2.2e-6
        with self.assertRaisesRegex(ValueError, 'value changed'):
            study.identities(changed, self.inventory)
        changed = copy.deepcopy(self.identity)
        changed['reference_capacitor_application']['tolerance_only_establishes_application_min'] = True
        with self.assertRaisesRegex(ValueError, 'gap hidden'):
            study.identities(changed, self.inventory)

    def test_path_cannot_omit_endpoint_or_change_target(self):
        changed = copy.deepcopy(self.electrical)
        changed['power_endpoint_comparison'].pop()
        with self.assertRaisesRegex(ValueError, 'coverage'):
            study.endpoints(changed, self.old_electrical, self.graph)
        changed = copy.deepcopy(self.electrical)
        changed['power_endpoint_comparison'][0]['source_boundary'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'detached'):
            study.endpoints(changed, self.old_electrical, self.graph)

    def test_no_unknown_resistance_promotion_or_contact_omission(self):
        for key, value in (('actual_complete_resistance_ohm', 0.0001), ('GH_contacts', 999)):
            changed = copy.deepcopy(self.electrical)
            changed['power_endpoint_comparison'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'promoted|accounting'):
                study.endpoints(changed, self.old_electrical, self.graph)

    def test_complete_alternative_feed(self):
        counts = study.feed_composition(self.electrical, self.support, self.graph, self.inventory)
        self.assertEqual(counts['affected_rear_endpoints'] + counts['unchanged_front_endpoints'], 106)

    def test_feed_dimensions_or_stud_cannot_detach(self):
        for key, value in (('width_mm', 11), ('rear_stud_xyz_mm', [0, 0, 0])):
            changed = copy.deepcopy(self.support)
            changed['low_R_feed_option']['straps'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'detached'):
                study.feed_composition(self.electrical, changed, self.graph, self.inventory)

    def test_no_missing_feed_target_or_copper_leg(self):
        changed = copy.deepcopy(self.electrical)
        changed['lowR_complete_endpoint_paths'].pop()
        with self.assertRaisesRegex(ValueError, 'partition'):
            study.feed_composition(changed, self.support, self.graph, self.inventory)
        changed = copy.deepcopy(self.electrical)
        changed['lowR_complete_endpoint_paths'][0]['new_segments'].pop()
        with self.assertRaisesRegex(ValueError, 'segment omitted'):
            study.feed_composition(changed, self.support, self.graph, self.inventory)

    def test_no_fake_path_total_or_upstream_zero(self):
        for key, value in (('complete_boundary_to_pad_allocation_mm', 0),
                           ('upstream_source_to_boundary_resistance_ohm', 0)):
            changed = copy.deepcopy(self.electrical)
            changed['lowR_complete_endpoint_paths'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'pad path|resistance promoted'):
                study.feed_composition(changed, self.support, self.graph, self.inventory)


if __name__ == '__main__':
    unittest.main()
