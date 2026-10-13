"""Adversarial cross-lane mutations that retain the original count totals."""
import copy
import unittest
from unittest.mock import patch
import check


class ContractMutations(unittest.TestCase):
    def rejects(self, relative, mutate, message):
        path = check.ROOT / relative
        changed = copy.deepcopy(check.read(path))
        mutate(changed)
        original_read = check.read
        with patch.object(check, 'read', side_effect=lambda p: changed if p == path else original_read(p)):
            with self.assertRaisesRegex(ValueError, message):
                check.source_checks()

    def test_pin_permutation_same_count(self):
        def mutate(j):
            p = j['endpoints'][0]['pin_map']
            p['1'], p['2'] = p['2'], p['1']
        self.rejects('design/partition/core-split/candidates/interface-contract.json', mutate, 'endpoint drift')

    def test_order_derived_ref_renumber(self):
        self.rejects('design/partition/core-split/candidates/interface-contract.json',
                     lambda j: j['endpoints'][0].update(pcb_reference='J999999'), 'endpoint drift')

    def test_package_count_hides_wrong_module(self):
        self.rejects('design/partition/core-split/candidates/two.json',
                     lambda j: j['boards']['two-B']['source_parts'][0].update(module='O1'), 'module crosses')

    def test_duplicate_part_keeps_total(self):
        self.rejects('design/partition/core-split/candidates/two.json',
                     lambda j: j['boards']['two-B']['source_parts'][0].update(ref='C301'), 'source part coverage')

    def test_unselected_topology_cannot_be_promoted(self):
        self.rejects('design/partition/core-split/candidates/three.json',
                     lambda j: j.update(selected=True), 'promoted without decision')

    def test_decision_flag_cannot_admit_execution(self):
        self.rejects('design/partition/core-split/decision.json',
                     lambda j: j.update(production_generalization_ready=True), 'unreviewed decision promotion')

    def test_contract_cannot_invent_final_z(self):
        self.rejects('design/partition/core-split/contract.json',
                     lambda j: j.update(final_stack_z_mm={'KA': -100}), 'unreviewed execution contract promotion')


if __name__ == '__main__':
    unittest.main()
