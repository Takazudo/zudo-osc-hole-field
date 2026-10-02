"""The ideal lag fixture must describe the captured RC island it claims to test."""
from dataclasses import replace
from pathlib import Path
import copy
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from design.spec.modules.sample_hold import family
from design.spec.modules.sample_hold_model_contract import model_contract, positive_value, AMP_MAPS
from design.spec.modules import run_sample_hold_spice as runner


class SampleHoldModel(unittest.TestCase):
    def setUp(self):
        self.family = family()
        self.facts = json.loads(runner.FACTS.read_text())

    def changed(self, role, **changes):
        return tuple(replace(p, **changes) if p.attributes.get('Role') == role else p
                     for p in self.family.parts)

    def test_nominal_capture_and_ideal_boundary_are_explicit(self):
        r = model_contract(self.family.parts, self.facts)
        self.assertEqual((r['r_min_ohm'], r['r_pot_nominal_ohm'], r['c_lag_F']), (2200, 500000, 500e-9))
        self.assertEqual(len(r['source_parts']), 9)
        self.assertIn('±20%', r['pot_nominal_evidence']['conditions'])
        self.assertIn('unlimited rails', r['scope'])
        self.assertIn('1 milliohm', r['scope'])
        self.assertIn('Rpot_fast rfast lagfast 0.001', runner.deck(r))

    def test_changed_source_values_change_model_and_analytic_inputs(self):
        r = model_contract(self.changed('slew_island:R_MIN', value='3.3 kΩ'), self.facts)
        self.assertEqual(r['r_min_ohm'], 3300)
        self.assertIn('Rmin_fast pre rfast 3300', runner.deck(r))
        r = model_contract(self.changed('slew_island:C3', value='200 nF'), self.facts)
        self.assertEqual(r['c_lag_F'], 600e-9)
        self.assertNotEqual(runner.deck(r), runner.deck(model_contract(self.family.parts, self.facts)))

    def test_missing_duplicate_dnp_and_wrong_passive_fail(self):
        role = 'slew_island:C1'
        p = next(p for p in self.family.parts if p.attributes.get('Role') == role)
        variants = [tuple(q for q in self.family.parts if q is not p),
                    self.family.parts + (replace(p, key='duplicate_cap'),)]
        for change in ({'dnp': True}, {'prefix': 'R'}, {'unit': 1},
                       {'symbol': 'Other:1206CG104J500NT'}, {'pins': {'1': 'RAW_HELD', '2': 'AGND'}},
                       {'value': '0 F'}, {'value': '1e999 F'}, {'value': '1e-999 F'}):
            variants.append(self.changed(role, **change))
        for parts in variants:
            with self.subTest(parts=parts[-1].key), self.assertRaises(ValueError):
                model_contract(parts, self.facts)

    def test_pot_strap_body_and_primitive_cannot_be_silently_changed(self):
        p = next(p for p in self.family.parts if p.attributes.get('Role') == 'slew_island:RV')
        variants = [{'pins': {**p.pins, '3': None}}, {'pins': {**p.pins, '4': p.pins['2']}},
                    {'prefix': 'C'}, {'unit': 1}, {'symbol': 'zudo-osc-hole-field:PTV09A-4020F-B104'}]
        for changes in variants:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                model_contract(self.changed('slew_island:RV', **changes), self.facts)

    def test_follower_feedback_and_amplifier_identity_fail_closed(self):
        p = next(p for p in self.family.parts if p.attributes.get('Role') == 'slew_island:POST' and p.unit != 5)
        negative = AMP_MAPS[p.unit - 1][1]
        for replacement in (replace(p, pins={**p.pins, negative: 'AGND'}),
                            replace(p, prefix='R'), replace(p, symbol='Other:OPA4197IPWR')):
            parts = tuple(replacement if q is p else q for q in self.family.parts)
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                model_contract(parts, self.facts)

    def test_private_rename_is_supported_but_unmodeled_internal_branch_rejected(self):
        p = next(p for p in self.family.parts if p.attributes.get('Role') == 'slew_island:R_MIN')
        private = p.pins['1']
        parts = tuple(replace(q, pins={pin: 'renamed_private' if net == private else net
                                       for pin, net in q.pins.items()}) for q in self.family.parts)
        self.assertEqual(model_contract(parts, self.facts)['r_min_ohm'], 2200)
        extra = replace(p, key='extra', attributes={'Role': 'extra'}, pins={'1': private, '2': 'AGND'})
        with self.assertRaisesRegex(ValueError, 'unprojected internal'):
            model_contract(self.family.parts + (extra,), self.facts)
        # Actual post-buffer loads lie outside the explicitly ideal output boundary.
        outside = replace(extra, pins={'1': 'SLEW_BUFFERED', '2': 'AGND'})
        self.assertEqual(model_contract(self.family.parts + (outside,), self.facts)['c_lag_F'], 500e-9)

    def test_nominal_owner_fact_is_required_without_claiming_tolerance_coverage(self):
        f = next(f for f in self.facts['facts'] if f['fact_id'] == 'fact-b504-resistance')
        for changes in ({'unit': 'F'}, {'verdict': 'UNSOURCED'}, {'value': float('inf')}, {'value': True}):
            facts = copy.deepcopy(self.facts)
            next(x for x in facts['facts'] if x['fact_id'] == f['fact_id']).update(changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                model_contract(self.family.parts, facts)
        facts = copy.deepcopy(self.facts); facts['facts'].append(copy.deepcopy(f))
        with self.assertRaisesRegex(ValueError, 'one B504'):
            model_contract(self.family.parts, facts)

    def test_source_rejection_and_stale_deck_check_precede_oracle(self):
        parts = self.changed('slew_island:R_MIN', prefix='C')
        with patch.object(runner, 'family', return_value=replace(self.family, parts=parts)), \
                patch.object(runner.subprocess, 'run') as oracle, patch.object(Path, 'write_text') as write:
            with self.assertRaises(ValueError): runner.build()
            oracle.assert_not_called(); write.assert_not_called()
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'stale.cir'; path.write_text('old captured value')
            with patch.object(runner, 'DECK', path), patch.object(runner.subprocess, 'run') as oracle:
                with self.assertRaisesRegex(SystemExit, 'deck drift'): runner.build(check=True)
                oracle.assert_not_called()

    def test_nonfinite_unordered_and_false_success_native_results_fail(self):
        for output in ('f10=1e999\nf90=1e999', 'f10=1\nf90=1', 'f10=2\nf90=1',
                       'f10=-1\nf90=1', 'f10=0\nf90=1e999'):
            with self.subTest(output=output), self.assertRaises(ValueError):
                runner.timing_error(output, 'f', 1)
        for expected in (float('inf'), float('nan'), 0, -1):
            with self.subTest(expected=expected), self.assertRaises(ValueError):
                runner.timing_error('f10=1\nf90=2', 'f', expected)
        self.assertEqual(runner.timing_error('f10=1\nf90=2', 'f', 1), (1, 0))
        for message in ('Error: transient failed', 'Fatal error: failed', 'doAnalyses: convergence problem',
                        'run simulation(s) aborted'):
            with self.subTest(message=message), self.assertRaises(RuntimeError):
                runner.require_success(SimpleNamespace(returncode=0, stdout='f10=1\nf90=2', stderr=message))
        runner.require_success(SimpleNamespace(returncode=0, stdout='f10=1\nf90=2', stderr=''))

    def test_value_parser_rejects_trailing_junk_and_nonfinite_tokens(self):
        for text in ('nan F', '-1 F', '1 F trailing', 'inf F', '0 F'):
            with self.subTest(text=text), self.assertRaises(ValueError): positive_value(text, 'F')


if __name__ == '__main__':
    unittest.main()
