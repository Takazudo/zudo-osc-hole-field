"""Synthetic safety-contract tests; never evaluate the real proposed geometry."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('audit',Path(__file__).with_name('audit.py'))
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)

class AuditContractTests(unittest.TestCase):
    def test_same_net_hole_spacing_and_symmetric_annulus(self):
        via={'radius':.15,'annulus':.35}
        pad={'radius':.2,'annulus':None}
        self.assertTrue(a.hole_margins(.5,via,via)[2])
        self.assertEqual(a.hole_margins(.7,via,pad),a.hole_margins(.7,pad,via))
        self.assertFalse(a.hole_margins(1.0,via,via)[2])
    def test_padless_and_external_contact_components_block(self):
        c={1:{'original_pad_contacts':[]},2:{'original_pad_contacts':[{'uuid':'p'}]}}
        self.assertFalse(a.contact_component_ok({1},set(),c))
        self.assertFalse(a.contact_component_ok({1,2},{1},c))
        self.assertTrue(a.contact_component_ok({1,2},set(),c))
    def test_duplicate_uuid_object_keys_remain_distinct(self):
        x={'uuid':'same','source_span':[1,8],'sha256':'hash'}
        self.assertNotEqual(a.identity(x),a.identity(x|{'source_span':[9,16]}))
    def test_changed_source_seal_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source';p.write_bytes(b'original')
            seals={'source':a.sha(p.read_bytes())};a.verify_seals(seals,Path(d))
            p.write_bytes(b'changed')
            with self.assertRaises(AssertionError):a.verify_seals(seals,Path(d))

if __name__=='__main__':unittest.main()
