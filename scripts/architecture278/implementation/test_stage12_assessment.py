import copy
import json
import unittest
import stage12_assessment as study


class HistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((study.OUT / 'scope.json').read_text())
        cls.history = json.loads((study.OUT / 'criteria-history.json').read_text())

    def test_frozen_predecessors_and_exact_history(self):
        self.assertEqual(study.preserve(self.scope), 267)
        self.assertEqual(study.history(self.history), 10)

    def test_cannot_omit_frozen_geometry_or_rehash_history(self):
        for removal in (True, False):
            scope = copy.deepcopy(self.scope)
            path = 'design/architecture-278/implementation/stage11/support-input.json'
            if removal:
                scope['preserved_prior_source_sha256'].pop(path)
            else:
                scope['preserved_prior_source_sha256'][path] = '0' * 64
            with self.assertRaisesRegex(ValueError, 'frozen'):
                study.preserve(scope)

    def test_criteria_cannot_change_checkpoint_or_excerpt(self):
        for key, value in (('commit', 'main'), ('excerpt', 'New owner-approved target'),
                           ('sha256', '0' * 64), ('immutable_url', 'https://example.com')):
            report = copy.deepcopy(self.history)
            report['records'][0][key] = value
            with self.assertRaises(ValueError):
                study.history(report)

    def test_criteria_cannot_drop_or_duplicate_record(self):
        report = copy.deepcopy(self.history)
        report['records'].pop()
        with self.assertRaisesRegex(ValueError, 'coverage'):
            study.history(report)
        report = copy.deepcopy(self.history)
        report['records'][1] = report['records'][0]
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            study.history(report)


class CompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def read(path):
            return json.loads(path.read_text())
        cls.budget = read(study.OUT / 'budget-report.json')
        cls.cap = read(study.OUT / 'capacitor-report.json')
        cls.inventory = read(study.OUT.parent / 'stage10/inventory-report.json')
        cls.graph = read(study.OUT.parent / 'stage10/interfaces-report.json')
        cls.old = read(study.OUT.parent / 'stage10/electrical-report.json')
        cls.standard = read(study.ROOT / 'design/standard/electrical-standard.json')

    def mapping(self, report):
        return study.resistance_mapping(report, self.graph, self.inventory, self.old)

    def test_exact_endpoint_and_overlay_crosschecks(self):
        self.assertEqual(self.mapping(self.budget)['endpoints'], 106)
        self.assertFalse(study.capacitor_overlay(self.cap, self.inventory)['correction_qualified'])
        study.criteria_boundaries(self.budget, self.standard)

    def test_endpoint_walk_cannot_be_dropped_or_relocated(self):
        for mode in ('endpoint', 'edge', 'pad'):
            r = copy.deepcopy(self.budget)
            if mode == 'endpoint': r['resistance_endpoint_mapping'].pop()
            elif mode == 'edge': r['resistance_endpoint_mapping'][0]['edge_terms'].pop()
            else: r['resistance_endpoint_mapping'][0]['source_pad_xyz_mm'][0] += 1
            with self.assertRaises(ValueError): self.mapping(r)

    def test_contact_domains_and_shared_usage_cannot_be_erased(self):
        for key, value in (('domains', ['PCB_spreading_necks_vias']),
                           ('domains', ['wire', 'crimp_termination', 'GH_mated_contact']),
                           ('GH_contacts', 0), ('wire_max_mm', -1),
                           ('endpoint_walk_use_count', 0), ('shared_current_A', .1)):
            r = copy.deepcopy(self.budget)
            term = next(t for row in r['resistance_endpoint_mapping'] for t in row['edge_terms'] if t['kind'] == 'GH_harness')
            term[key] = value
            with self.assertRaises(ValueError): self.mapping(r)

    def test_old_limits_and_unknown_complete_transfer_remain_open(self):
        for mode in ('limit', 'redefinition', 'complete', 'sharing'):
            r = copy.deepcopy(self.budget)
            row = r['resistance_endpoint_mapping'][0]
            if mode == 'limit': row['original_plane_requirement']['limit_ohm'] = .1
            elif mode == 'redefinition': row['expanded_architecture_comparison']['accepted_redefinition'] = True
            elif mode == 'complete': row['complete_transfer_error_V'] = 0
            else: r['resistance_accounting']['equal_sharing_credit'] = True
            with self.assertRaises(ValueError): self.mapping(r)

    def test_criteria_cannot_be_conflated_or_promoted(self):
        for mode in ('static', 'timing', 'execution', 'proposal', 'mapping', 'complete'):
            r = copy.deepcopy(self.budget)
            c = r['criteria']
            if mode == 'static': c['static']['target_V'] = c['output_load_change']['target_V']
            elif mode == 'timing': c['timing']['A01_settling_target_s'] = .0004
            elif mode == 'execution': c['ideal_AO_runner']['executed'] = True
            elif mode == 'proposal': c['new_proposals'][0]['status'] = 'APPROVED'
            elif mode == 'mapping': c['recommended_domain_mapping']['status'] = 'APPROVED'
            else: r['complete_error_bound_V'] = .001
            with self.assertRaises(ValueError): study.criteria_boundaries(r, self.standard)

    def test_capacitor_scope_population_and_topology_bound(self):
        for mode in ('third', 'unchanged', 'pin', 'value', 'units', 'hash'):
            r = copy.deepcopy(self.cap)
            if mode == 'third': r['overlay']['C7107'] = copy.deepcopy(r['overlay']['C7101'])
            elif mode == 'unchanged': r['conservation']['unchanged_refs'].remove('C7107')
            elif mode == 'pin': r['overlay']['C7101']['pins'] = {}
            elif mode == 'value': r['overlay']['C7101']['candidate_value_F'] = 1e-6
            elif mode == 'units': r['conservation']['units'] = 117
            else: r['conservation']['source_topology_sha256'] = '0' * 64
            with self.assertRaises(ValueError): study.capacitor_overlay(r, self.inventory)

    def test_capacitor_arithmetic_and_unqualified_guarantees(self):
        for key, value in (('initial_tolerance_interval_F', [4.7e-6, 4.7e-6]),
                           ('required_combined_retention_after_initial_min_for_1uF', .1),
                           ('application_minimum_proven', True),
                           ('effective_C_at_bias_temperature_age_F', 1e-6),
                           ('guaranteed_ESR_ohm', 1)):
            r = copy.deepcopy(self.cap)
            r['overlay']['C7101'][key] = value
            with self.assertRaises(ValueError): study.capacitor_overlay(r, self.inventory)
        r = copy.deepcopy(self.cap)
        r['ESR_assessment']['stability_proven'] = True
        with self.assertRaises(ValueError): study.capacitor_overlay(r, self.inventory)


if __name__ == '__main__':
    unittest.main()
