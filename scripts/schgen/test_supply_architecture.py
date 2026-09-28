#!/usr/bin/env python3
"""Negative checks for omitted loads, joined domains and optimistic interface limits."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.schgen import build_supply_architecture as architecture


class SupplyArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.input = json.loads(architecture.INPUT.read_text())
        cls.ledger = architecture.ledger_build()

    def build(self, mutate=None):
        c=copy.deepcopy(self.input)
        if mutate:mutate(c)
        with patch.object(architecture, 'ledger_build', return_value=self.ledger):
            return architecture.build(c)

    def reject(self, mutate, message):
        with self.assertRaisesRegex(ValueError, message):self.build(mutate)

    def test_requirements_are_not_capacity(self):
        r=self.build()
        self.assertEqual(r['minimum_arithmetic_independent_sources'],3)
        self.assertEqual(r['selected_requirement']['minimum_continuous_mA'],{'+12V':1600,'-12V':1500,'+5V':300})
        self.assertTrue(all(v is None for v in r['measured_source_capacity_mA'].values()))

    def test_missing_module(self):
        self.reject(lambda c:c['domains']['EXT']['module_instances'].pop(), 'module allocation')

    def test_split_module_load(self):
        self.reject(lambda c:c['load_allocation']['H1:0'].update(domain='A'), 'wrong load domain')

    def test_missing_load(self):
        self.reject(lambda c:c['load_allocation'].pop('H1:0'), 'worksheet load')

    def test_parallel_source(self):
        self.reject(lambda c:c['domains'].update(EXTRA=copy.deepcopy(c['domains']['EXT'])), 'exactly one EXT')

    def test_joined_rails(self):
        self.reject(lambda c:c['domains']['EXT']['regulated_nets'].update({'-12V':'+12V'}), 'rail merging')

    def test_missing_allowance(self):
        self.reject(lambda c:c['load_envelope']['auxiliary_allowance_mA'].update({'+12V':0}), 'allowance missing')

    def test_ground_rating_uses_full_current(self):
        self.reject(lambda c:c['inlet'].update(min_required_simultaneous_contact_rating_A=2), 'return contact/cable overload')

    def test_bad_voltage_source(self):
        self.reject(lambda c:c['source_requirement']['voltage_magnitude_at_source_V'].update({'-12V':[11.74,12.2]}), 'voltage band')

    def test_return_shift_can_raise_positive_rail(self):
        self.reject(lambda c:c['source_requirement']['voltage_magnitude_at_source_V'].update({'+5V':[5.05,5.15]}), 'voltage band')

    def test_current_limiter_not_minimum_source_rating(self):
        self.reject(lambda c:c['source_requirement']['maximum_delivered_current_mA'].update({'+12V':1700}), 'limiter cannot deliver')
        self.reject(lambda c:c['source_requirement']['maximum_delivered_current_mA'].update({'+12V':4000}), 'return contact/cable overload')

    def test_negative_loss_is_not_a_saving(self):
        self.reject(lambda c:c['inlet']['harness'].update(max_protection_drop_V=-1), 'negative cable')

    def test_nonfinite_allowance(self):
        self.reject(lambda c:c['load_envelope']['auxiliary_allowance_mA'].update({'+12V':float('nan')}), 'nonfinite')

    def test_cable_loss(self):
        self.reject(lambda c:c['inlet']['harness'].update(max_length_mm=1000), 'voltage loss')

    def test_no_domain_off_case(self):
        self.reject(lambda c:c['fault_cases'].pop(0), 'fault analysis')

    def test_reference_crosses_domains(self):
        def mutate(c):
            c['independent_candidate']['domains']['A'].remove('OCTAVE_REF')
            c['independent_candidate']['domains']['B'].append('OCTAVE_REF')
        self.reject(mutate,'reference crosses')

    def test_old_single_pocket_not_reused(self):
        self.reject(lambda c:c['independent_candidate']['pockets'][1].update(support_xyz_mm=c['independent_candidate']['pockets'][0]['support_xyz_mm']), 'source outside|collision')

    def test_pocket_depth_conflict(self):
        self.reject(lambda c:c['independent_candidate'].update(enclosure_inside_xyz_mm=[318,298,60]), 'outside rear chamber')

    def test_invented_capacity(self):
        self.reject(lambda c:c['physical_source']['measured_capacity_mA'].update({'+12V':1600}), 'invented source')

if __name__ == '__main__':unittest.main()
