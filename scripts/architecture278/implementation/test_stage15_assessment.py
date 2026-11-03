import json
import unittest
from unittest.mock import patch
import stage15_assessment as m

class Assessment(unittest.TestCase):
    def test_complete_composition(self):
        r=m.build()
        self.assertEqual(r['counts']['power_return_endpoints'],108)
        self.assertFalse(r['hardware_acceptance'])
        self.assertFalse(r['canonical_source_changed'])
    def test_missing_historical_file_fails(self):
        x=json.loads((m.OUT/'scope.json').read_text());x['preserved_prior_source_sha256'].popitem()
        with self.assertRaises(ValueError):m.preserve(x)
    def test_wrong_baseline_fails(self):
        x=json.loads((m.OUT/'scope.json').read_text());x['baseline_commit']='HEAD'
        with self.assertRaises(ValueError):m.preserve(x)
    def test_frozen_stage14(self):m.check_predecessor()
if __name__=='__main__':unittest.main()
