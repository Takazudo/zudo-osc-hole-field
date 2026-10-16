"""Independent regression of interpretation and historical/live review boundaries."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import stage15_interpretation as m


class IndependentInterpretation(unittest.TestCase):
    def test_mutable_review_hash_cannot_be_waived(self):
        original=Path.read_text
        def changed(path,*args,**kwargs):
            raw=original(path,*args,**kwargs)
            if path==m.previous.OUT/'review-root.json':
                r=json.loads(raw)
                r['source_sha256']['design/architecture-278/implementation/README.md']='0'*64
                return json.dumps(r)
            return raw
        with patch.object(m,'preserve',return_value=0),patch.object(Path,'read_text',changed):
            with self.assertRaisesRegex(ValueError,'historical review binding'):m.predecessor()

    def test_frozen_live_byte_mutation_cannot_use_historical_fallback(self):
        # Simulate wrong live bytes without editing any protected file.
        with patch.object(m.common,'digest',return_value='0'*64):
            with self.assertRaisesRegex(ValueError,'preserved'):m.preserve()

    def test_missing_preserved_source_cannot_be_silently_ignored(self):
        original=Path.read_text
        def changed(path,*args,**kwargs):
            raw=original(path,*args,**kwargs)
            if path==m.OUT/'scope.json':
                r=json.loads(raw);r['preserved_prior_source_sha256'].popitem()
                return json.dumps(r)
            return raw
        with patch.object(Path,'read_text',changed):
            with self.assertRaisesRegex(ValueError,'historical inventory'):m.preserve()

    def test_actual_report_numbers_have_distinct_units_and_conditions(self):
        r=json.loads((m.OUT/'interpretation-report.json').read_text())
        n=r['unchanged_diagnostic_numbers'];terms=n['manual_endpoint_signed_terms_V']
        self.assertEqual(terms['CV_slope'],0)
        self.assertAlmostEqual(terms['manual_network_ratio'],.00100005,places=12)
        self.assertAlmostEqual(terms['reference_initial'],.00500100005,places=12)
        self.assertAlmostEqual(sum(terms.values()),n['four_idealized_manual_endpoint_max_V'],places=12)
        for gain,span in zip(n['paired_CV_gain_interval'],n['paired_CV_10V_span_error_interval_V']):
            self.assertAlmostEqual(span,10*(gain-1),places=12)
        self.assertLess(max(map(abs,n['four_idealized_CV_5V_fixed_setting_interval_V'])),.001001)
        self.assertIsNone(r['calibrated_static_residual_V'])
        self.assertEqual(r['canonical_static_condition'],'after factory calibration')
        self.assertEqual((r['canonical_static_target_V'],r['canonical_load_change_target_V']),(.002,.001))

    def test_manual_witness_cannot_be_relabelled_cv(self):
        args=[json.loads(p.read_text()) for p in [m.ROOT/'design/standard/electrical-standard.json',m.previous.OUT/'allocation-report.json',m.OUT/'measurement-contract.json']]
        s=next(s for s in args[1]['scenarios'] if len(s['removed_nonidealities'])==4)
        row=next(r for r in s['state_rows'] if r['state']=='manual_high')
        row['with_reference_initial_worst_witness']['signed_terms_V']['CV_slope']=.00600105005
        with self.assertRaisesRegex(ValueError,'not CV'):m.analyze(*args)


if __name__=='__main__':unittest.main()
