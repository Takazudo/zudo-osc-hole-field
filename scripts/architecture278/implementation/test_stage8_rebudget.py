import hashlib
import tempfile
import unittest
from pathlib import Path
import stage8_rebudget as r

class RebudgetBindingTests(unittest.TestCase):
    def test_mechanical_stale_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/'placement.json';p.write_text('original')
            report={'source_sha256':{'placement.json':hashlib.sha256(p.read_bytes()).hexdigest()}}
            r.validate_bindings(report,root)
            p.write_text('changed')
            with self.assertRaisesRegex(ValueError,'stale source'):r.validate_bindings(report,root)
    def test_missing_mechanical_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError,'missing source'):r.validate_bindings({})
    def test_electrical_report_cannot_reuse_old_interface(self):
        interface={'pad_xyz_mm':[1,2,21.6]}
        report={'interface_object_sha256':hashlib.sha256(r.encode(interface).encode()).hexdigest()}
        r.validate_interface_object(interface,report)
        interface['pad_xyz_mm'][0]=2
        with self.assertRaisesRegex(ValueError,'different interface'):r.validate_interface_object(interface,report)

if __name__=='__main__':unittest.main()
