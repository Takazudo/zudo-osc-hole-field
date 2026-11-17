"""Offline failure tests; no native tool, network or source modification."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import audit


class HeightAuditTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((audit.HERE / 'evidence.json').read_text())
        self.threading = json.loads((audit.ROOT / 'design/stack/fixings/threading-procedure.json').read_text())
        self.packages = json.loads((audit.ROOT / 'design/reports/io-partition.json').read_text())
        self.murata = {'productSearchResult': [{'itemInfoList': [
            {'id': 'partNumWithPackageCode', 'valueList': [{'value': 'GRM188R71H104KA93D'}]},
            {'id': 'thickness', 'valueList': [{'value': '0.8', 'displayName': '0.8mm ±0.1mm'}]},
            {'id': 'thicknessMax', 'valueList': [{'value': '0.8', 'displayName': '0.9mm'}]},
        ]}]}

    def report(self):
        return audit.audit(self.manifest, self.threading, self.packages, self.murata)

    def test_coverage_never_accepts_access(self):
        report = self.report()
        for key in ('source_commit','engineering_commit','procedure_amendment','nut_source_amendment'):
            self.assertEqual(report[key], self.manifest[key])
        self.assertEqual(report['counts'], {'exact': 59, 'conditional_suffix': 2, 'unresolved_identity': 27})
        self.assertEqual(len(report['references']), 88)
        self.assertEqual(len(report['links']), 31)
        self.assertTrue(all(r['mounted_height_mm'] is None for r in report['references']))
        self.assertTrue(all(r['access_verdict'] == 'NOT SHOWN' for r in report['links']))
        self.assertEqual(sum(sum(x['coverage'].values()) for x in report['links']),89)

    def test_input_source_drift(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'source'
            p.write_bytes(b'altered')
            with self.assertRaisesRegex(ValueError, 'source drift'):
                audit.verified_bytes(p, hashlib.sha256(b'original').hexdigest())

    def test_wrong_exact_mpn(self):
        ref = next(iter(self.manifest['expected_refs']))
        next(p for p in self.packages['physical_packages'] if p['ref'] == ref)['mpn'] = 'WRONG'
        with self.assertRaisesRegex(ValueError, 'identity drift'):
            self.report()

    def test_missing_neighbour_ref(self):
        self.threading['latch']['not_shown'][0]['neighbours'].pop()
        with self.assertRaisesRegex(ValueError, 'latch reference set changed'):
            self.report()

    def test_missing_package(self):
        ref = next(iter(self.manifest['expected_refs']))
        self.packages['physical_packages'] = [p for p in self.packages['physical_packages'] if p['ref'] != ref]
        with self.assertRaisesRegex(ValueError, 'missing package'):
            self.report()

    def test_murata_raw_max_is_not_adopted(self):
        report = self.report()
        grm = [r for r in report['references'] if r['mpn'] == 'GRM188R71H104KA93D']
        self.assertEqual(len(grm),29)
        self.assertTrue(all(r['body_max_mm'] == 0.9 for r in grm))
        self.assertEqual(report['murata_conflict']['raw_max'], '0.8')
        self.murata['productSearchResult'][0]['itemInfoList'][2]['valueList'][0]['displayName']='0.8mm'
        with self.assertRaisesRegex(ValueError, 'conflict changed'):
            self.report()

    def test_raw_max_cannot_replace_derived_bound(self):
        self.manifest['groups']['GRM188R71H104KA93D']['body_max_mm']=0.8
        with self.assertRaisesRegex(ValueError, 'derived bound changed'):
            self.report()

    def test_no_suffix_substitution(self):
        self.murata['productSearchResult'][0]['itemInfoList'][0]['valueList'][0]['value']='GRM188R71H104KA93J'
        with self.assertRaisesRegex(ValueError, 'exact suffix absent'):
            self.report()

    def test_input_pins_at_candidate_tree(self):
        for path, digest in self.manifest['pins'].items():
            audit.verified_bytes(audit.ROOT / path, digest)


if __name__ == '__main__':
    unittest.main()
