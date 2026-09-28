"""The SES recovery boundary rejects owner and prior-copper damage."""
import tempfile,unittest
from pathlib import Path
from scripts.pcbgen.transplant_routed_copper import transplant
from scripts.pcbgen.verify_local_links import blocks

OLD='(segment (start 1 2) (end 3 4) (width 0.2)\n (layer "F.Cu") (net "SIG") (uuid "11111111-1111-1111-1111-111111111111"))'
NEW='(segment (start 3 4) (end 5 6) (width 0.2)\n (layer "F.Cu") (net "SIG") (uuid "22222222-2222-2222-2222-222222222222"))'
FP='(footprint "test" (property "Reference" "U1") (uuid "33333333-3333-3333-3333-333333333333"))'

class TransplantTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source';self.prepared=self.root/'prepared';self.routed=self.root/'routed';self.output=self.root/'output';self.receipt=self.root/'receipt'
        self.source.write_text('(kicad_pcb\n'+FP+'\n'+OLD+'\n)\n')
        self.prepared.write_text(self.source.read_text().replace('\n (layer','\n (locked yes)\n (layer'))
        self.routed.write_text(self.prepared.read_text().replace('\n)\n','\n'+NEW+'\n)\n'))
    def tearDown(self):self.temp.cleanup()
    def run_transplant(self):return transplant(self.source,self.prepared,self.routed,self.output,self.receipt)
    def test_owner_bytes_preserved_despite_preparation_locking(self):
        report=self.run_transplant();a=blocks(self.source);b=blocks(self.output)
        self.assertEqual(a['non_copper'],b['non_copper'])
        self.assertEqual(b['segment']['11111111-1111-1111-1111-111111111111'],OLD)
        self.assertEqual(len(report['added']),1)
    def test_reject_imported_prior_track_or_footprint_changes(self):
        routed=self.routed.read_text()
        for before,after in (('(end 3 4)','(end 3 5)'),('"Reference" "U1"','"Reference" "U2"'),('(net "SIG") (uuid "222','(net "OTHER") (uuid "222')):
            self.routed.write_text(routed.replace(before,after))
            with self.assertRaises(ValueError):self.run_transplant()
    def test_never_overwrite_canonical(self):
        with self.assertRaises(ValueError):transplant(self.source,self.prepared,self.routed,self.source,self.receipt)

if __name__=='__main__':unittest.main()
