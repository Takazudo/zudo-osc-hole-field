import copy
import hashlib
import json
from unittest.mock import patch
import unittest
import stage14_assessment as s

class Assessment(unittest.TestCase):
    def test_complete_frozen_inventory(self):
        scope=json.loads((s.OUT/'scope.json').read_text())
        self.assertGreater(s.preserve(scope),289)

    def test_missing_frozen_file_rejected(self):
        scope=json.loads((s.OUT/'scope.json').read_text());scope['preserved_prior_source_sha256'].popitem()
        with self.assertRaises(ValueError):s.preserve(scope)

    def test_historical_mutable_hash_checked(self):
        name='scripts/architecture278/implementation/check_source.py'
        raw=s.subprocess.check_output(['git','show',s.BASE+':'+name],cwd=s.ROOT)
        s.historical_review_binding(name,hashlib.sha256(raw).hexdigest())
        with self.assertRaises(ValueError):s.historical_review_binding(name,'0'*64)

    def test_live_prior_evidence_checked(self):
        with patch.object(s.common,'digest',return_value='0'*64):
            with self.assertRaises(ValueError):s.historical_review_binding('design/architecture-278/implementation/STAGE13.md','1'*64)

    def test_finite_disposition(self):
        report=s.build();self.assertEqual(report['validation_case_count'],10)
        self.assertEqual(report['disposition'],'CONDITIONAL_CANDIDATE')
        self.assertFalse(report['hardware_acceptance']);self.assertTrue(report['frozen_calibration_unchanged'])

if __name__=='__main__':unittest.main()
