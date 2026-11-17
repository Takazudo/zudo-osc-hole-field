import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import audit as a


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.report = json.loads((a.ROOT / a.REPORT).read_text())
        self.evidence = json.loads((a.HERE / 'evidence.json').read_text())
        self.maps = a.pin_maps(a.ROOT)

    def check(self):
        return a.validate(self.report, self.maps, self.evidence)

    def unit(self, ref, number):
        return next(u for u in self.report['package_units'] if u['ref'] == ref and u['unit'] == number)

    def test_independent_contact_counts(self):
        rows = self.check()
        self.assertEqual({n: len(r) for n, r in rows.items()}, {'CLOCK_RC': 3, 'CLOCK': 19, 'READY': 20})
        self.assertEqual(sum(r['classification'] == 'CLOCK_INPUT' for r in rows['CLOCK']), 17)
        self.assertEqual(sum(r['classification'] == 'CLEAR_INPUT' for r in rows['READY']), 15)
        self.assertEqual([(r['ref'], r['pin']) for r in rows['READY'] if r['classification'] == 'Q_DRIVER'], [('U4530', '9')])
        self.assertEqual([(r['ref'], r['pin']) for r in rows['READY'] if r['classification'] == 'ONE_SHOT_RESET_INPUT'], [('U4505', '3')])

    def test_missing_sink(self):
        self.unit('U4538', 1)['pins']['3'] = '/E5/OTHER'
        with self.assertRaisesRegex(ValueError, 'drift'): self.check()

    def test_added_sink(self):
        self.unit('U4538', 2)['pins']['11'] = '/E5/CLOCK'
        with self.assertRaisesRegex(ValueError, 'drift'): self.check()

    def test_duplicate_contact(self):
        self.report['package_units'].append(copy.deepcopy(self.unit('U4538', 1)))
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.check()

    def test_changed_unit_role(self):
        self.unit('U4530', 2)['role'] = 'invented role'
        with self.assertRaisesRegex(ValueError, 'drift'): self.check()

    def test_blank_mpn_not_template_identity(self):
        for p in self.report['physical_packages']:
            if p['ref'] == 'C4509': p['mpn'] = p['symbol']
        with self.assertRaisesRegex(ValueError, 'promoted'): self.check()

    def test_pin_map_drift(self):
        self.maps['SN74HC74DR']['3'] = 'output'
        with self.assertRaisesRegex(ValueError, 'drift'): self.check()

    def test_ci_conditions_cannot_be_broadened(self):
        self.evidence['ci_observations']['SN74HC14DR']['VCC_V'] = [2, 6]
        with self.assertRaisesRegex(ValueError, 'conditions'): self.check()

    def test_typical_not_maximum(self):
        self.evidence['ci_observations']['SN74HC74DR']['maximum_pF'] = 3
        with self.assertRaisesRegex(ValueError, 'conditions'): self.check()

    def test_nominal_rc_cannot_gain_tolerance(self):
        self.evidence['nominal_RC']['resistor']['tolerance'] = 0.01
        with self.assertRaisesRegex(ValueError, 'nominal RC'): self.check()

    def test_receiver_only_conditional_sums(self):
        sums = a.receiver_sums(self.check(), a.CI)
        self.assertEqual(sums['CLOCK']['conditional_catalog_max_sum_pF'], 170)
        self.assertEqual(sums['READY']['conditional_catalog_max_sum_pF'], 190)
        self.assertEqual([g['conditional_catalog_max_sum_pF'] for g in sums['READY']['groups']], [150, 30, 10])
        self.assertEqual({r['ref'] for r in sums['CLOCK']['excluded_contacts']}, {'R4533', 'U4512'})
        self.assertEqual([r['ref'] for r in sums['READY']['excluded_contacts']], ['U4530'])
        for result in sums.values():
            self.assertEqual(result['status'], 'CONDITIONAL_CATALOG_ARITHMETIC_ONLY')
            self.assertEqual(result['timing_verdict'], 'NOT_ESTABLISHED')
            for key in ('actual_receiver_load_pF', 'actual_total_load_pF', 'actual_load_lower_bound_pF'):
                self.assertIsNone(result[key])

    def test_hc221_voltage_dash_not_invented(self):
        ci = copy.deepcopy(a.CI)
        self.assertIsNone(ci['CD74HC221M96']['VCC_V'])
        self.assertEqual(ci['CD74HC221M96']['VCC_source_cell'], '-')
        ci['CD74HC221M96']['VCC_V'] = [2, 6]
        with self.assertRaisesRegex(ValueError, 'conditions'): a.receiver_sums(self.check(), ci)

    def test_hc221_header_and_grade_preserved(self):
        ci = copy.deepcopy(a.CI)
        ci['CD74HC221M96']['table_header'] = 'unconditional capacitance'
        with self.assertRaisesRegex(ValueError, 'conditions'): a.receiver_sums(self.check(), ci)
        ci = copy.deepcopy(a.CI)
        ci['SN74HC00DR']['temperature_C'] = [-55, 125]
        with self.assertRaisesRegex(ValueError, 'conditions'): a.receiver_sums(self.check(), ci)

    def test_sum_rejects_double_count(self):
        rows = self.check()
        rows['CLOCK'].append(copy.deepcopy(rows['CLOCK'][2]))
        with self.assertRaisesRegex(ValueError, 'duplicate'): a.receiver_sums(rows, a.CI)

    def test_sum_rejects_driver_promotion(self):
        rows = self.check()
        driver = next(r for r in rows['READY'] if r['classification'] == 'Q_DRIVER')
        driver['classification'] = 'CLEAR_INPUT'
        with self.assertRaisesRegex(ValueError, 'classification'): a.receiver_sums(rows, a.CI)

    def test_source_pin_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises((ValueError, FileNotFoundError)): a.audit(Path(directory))

    def test_actual_source_and_no_physical_promotion(self):
        result = a.audit()
        for k in ('actual_total_load_pF', 'guaranteed_clock_frequency_Hz', 'clock_edge_bound_ns', 'ready_recovery_slack_ns'):
            self.assertIsNone(result[k])
        self.assertEqual(result['physical_timing_acceptance'], 'NOT_ESTABLISHED')
        self.assertEqual(result['nominal_RC']['resistor']['ohm'], 47000)
        self.assertEqual(result['nominal_RC']['capacitor']['farad'], 1e-9)
        self.assertEqual(result['counts']['READY']['NAND_INPUT'], 3)


if __name__ == '__main__':
    unittest.main()
