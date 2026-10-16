import copy
import json
from pathlib import Path
import tempfile
import unittest
import stage17_schematic as m


class Schematic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp=m.inputs()
        cls.files=m.build_files(cls.inp)

    def test_regeneration_exact_independent_build(self):
        self.assertEqual(self.files,m.build_files(copy.deepcopy(self.inp)))
        self.assertEqual(len([n for n in self.files if n.startswith('sheets/')]),8)
        self.assertEqual(len([n for n in self.files if n.startswith('transport/')]),8)

    def test_roundtrip_and_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);m.write_files(self.files,p);m.write_files(self.files,p,check=True)
            (p/'a01.kicad_sch').write_text('invalid')
            with self.assertRaisesRegex(ValueError,'generated drift'):m.write_files(self.files,p,check=True)

    def test_unknown_output_refused_not_deleted(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'foreign.txt').write_text('retain')
            with self.assertRaisesRegex(ValueError,'unexpected generated'):m.write_files(self.files,p)
            self.assertEqual((p/'foreign.txt').read_text(),'retain')

    def test_output_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,'unsafe'):m.write_files({'../escape':'bad'},Path(tmp)/'out')

    def test_symbol_pin_inventory_and_no_inferred_mpn(self):
        library=m.library_objects(self.files['A01Candidate.kicad_sym'])
        self.assertEqual(len(library),86)
        self.assertEqual(sum(len(pins) for s in library.values() for pins in s.units.values()),291)
        for ref,row in self.inp['packages'].items():
            sym=library['A01Candidate:A01_'+ref]
            self.assertEqual({p.number for ps in sym.units.values() for p in ps},set(row['pins']))
        self.assertEqual(set(library['A01Candidate:A01_RN7102'].units),{1,2,3,4,5})

    def test_transport_is_separate_and_complete(self):
        self.assertNotIn('transport/',self.files['a01.kicad_sch'])
        self.assertEqual(json.loads(self.files['transport-source.json']),self.inp['transport_contract'])
        self.assertEqual(sum(s.count('(wire ') for n,s in self.files.items() if n.startswith('transport/')),320)

    def test_historical_scan_rejects_unrelated_drift(self):
        baseline={'source_sha256':{'prior':'unchanged'},'pins':{'1':'AGND'}}
        m.compare_historical_extract(copy.deepcopy(baseline),baseline,[])
        bad=copy.deepcopy(baseline);bad['pins']['1']='WRONG'
        with self.assertRaisesRegex(ValueError,'interface extraction drift'):m.compare_historical_extract(bad,baseline,[])
        bad=copy.deepcopy(baseline);bad['source_sha256']['unexpected']='new'
        with self.assertRaisesRegex(ValueError,'source expansion'):m.compare_historical_extract(bad,baseline,[])
        bad=copy.deepcopy(baseline);bad['source_sha256']['prior']='changed'
        with self.assertRaisesRegex(ValueError,'interface extraction drift'):m.compare_historical_extract(bad,baseline,[])

    def test_historical_wrapper(self):
        m.predecessor()


if __name__=='__main__':unittest.main()
