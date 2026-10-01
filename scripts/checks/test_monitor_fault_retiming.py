import copy
import json
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch
from scripts.checks import monitor_fault_retiming as model


class MonitorFaultRetimingTests(unittest.TestCase):
    def setUp(self):
        self.spec=json.loads(model.SPEC.read_text())
        self.facts,self.identities=model.source_facts()

    def build(self):
        return model.calculate(self.spec,self.facts,self.identities)

    def test_clamp_current_accounts_for_bottom_branch(self):
        r=self.build()
        self.assertAlmostEqual(r['nominal_required_total_comparator_sink_A'],(3.3-.175)/7250-.175/1000)
        self.assertLess(r['nominal_required_total_comparator_sink_A'],r['nominal_clamped_top_current_A'])
        self.assertTrue(r['conditional_clamp_below_lowest_UV_trip'])
        self.assertFalse(r['assumed_clamp_point_requires_sourcing'])
        self.assertGreater(r['nominal_zero_clamp_reference_current_A'],r['nominal_released_divider_current_A'])

    def test_nominal_recovery_cannot_promote_source_timing_limits(self):
        r=self.build()
        self.assertAlmostEqual(r['nominal_recovery_overdrive_fraction'],.028/.372)
        self.assertFalse(r['nominal_recovery_at_least_table_overdrive'])
        self.assertIsNone(r['physical_recovery_bounds_s'])
        self.assertIsNone(r['physical_assertion_bound_s'])
        self.assertIsNone(r['guaranteed_minimum_detectable_negative_fault_s'])
        self.assertFalse(r['qualification_accepted'])

    def test_direct_fault_bypass_rejected(self):
        next(p for p in self.spec['components'] if p['ref']=='U102')['pins']['1']='FAULT_N'
        with self.assertRaisesRegex(ValueError,'topology'): self.build()

    def test_resistor_change_changes_leakage_sensitivity(self):
        before=self.build()
        next(p for p in self.spec['components'] if p['ref']=='R109')['value']+=1000
        after=self.build()
        self.assertEqual(after['reference_equivalent_shift_V_per_total_leakage_A'],
                         before['reference_equivalent_shift_V_per_total_leakage_A']+1000)
        self.assertNotEqual(before['nominal_required_total_comparator_sink_A'],after['nominal_required_total_comparator_sink_A'])

    def test_wrong_device_and_programming_rejected(self):
        self.identities['tlv9022dr']='TLV9032DR'
        with self.assertRaisesRegex(ValueError,'identity'): self.build()
        self.facts,self.identities=model.source_facts()
        self.spec['model_conditions']['supervisor_reset_s']=.001
        with self.assertRaisesRegex(ValueError,'reset time'): self.build()

    def test_undervoltage_is_not_recovery_overdrive(self):
        next(p for p in self.spec['components'] if p['ref']=='R109')['value']=20000
        r=self.build()
        self.assertLess(r['nominal_recovery_overdrive_fraction'],0)
        self.assertFalse(r['nominal_node_above_UV_trip'])
        self.assertFalse(r['nominal_recovery_at_least_table_overdrive'])
        next(p for p in self.spec['components'] if p['ref']=='R109')['value']=40000
        r=self.build()
        self.assertTrue(r['assumed_clamp_point_requires_sourcing'])
        self.assertLess(r['nominal_required_total_comparator_sink_A'],0)

    def test_snapshot_parsing_and_mutation_rejection(self):
        snapshot=model.snapshot_sources()
        with patch.object(Path,'read_bytes',side_effect=AssertionError('live source read')):
            facts,identities=model.source_facts(snapshot)
        self.assertEqual(facts,self.facts)
        self.assertEqual(identities,self.identities)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'source.json';p.write_bytes(b'old')
            frozen={p:p.read_bytes()}
            model.verify_unchanged(frozen)
            p.write_bytes(b'new')
            with self.assertRaisesRegex(ValueError,'inputs changed'):
                model.verify_unchanged(frozen)

    def test_committed_report_current(self):
        model.run(check=True)
