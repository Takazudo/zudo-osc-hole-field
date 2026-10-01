import copy
import json
import unittest
from scripts.pcbgen.core_package_fields import projection
from scripts.pcbgen.footprint_attributes import source_attribute_bits,source_rotation_degrees,capture_template_digests,verify_template_digest
from scripts.pcbgen.netlist import read_netlist
from pathlib import Path
import tempfile


class CorePackageFieldsTests(unittest.TestCase):
    def test_actual_representatives_preserve_distinct_units_and_reject_fabricated_value(self):
        with open('design/partition/core-ground-feasibility/package-field-source-audit.json') as f:audit=json.load(f)
        p=projection(audit,'schematic/boards/osc-core.net')
        self.assertEqual(len(p['representatives']),199)
        roles={r['resolved_fields']['Role'] for r in p['all_original_source_units'] if r['ref']=='U103'}
        self.assertIn('reference_generator:A1',roles);self.assertIn('reference_generator:A3',roles)
        bad=copy.deepcopy(audit)
        next(r for r in bad['parity_records'] if 'field' in r)['expected_source_value']='invented'
        with self.assertRaisesRegex(ValueError,'exact source unit'):projection(bad,'schematic/boards/osc-core.net')

    def test_exact_source_flags_preserve_unrelated_attributes(self):
        dnp,bom,position,smd=1,2,4,8
        self.assertEqual(source_attribute_bits(position|smd,{'dnp':''},dnp,bom),position|smd|dnp)
        self.assertEqual(source_attribute_bits(position|smd|bom,{},dnp,bom),position|smd)
        self.assertEqual(source_attribute_bits(dnp,{'exclude_from_bom':''},dnp,bom),bom)
        with self.assertRaisesRegex(ValueError,'unexpected native'):source_attribute_bits(0,{'dnp':'false'},dnp,bom)

    def test_source_rotations_distinguish_master_header_and_library_terminal(self):
        components,_=read_netlist(Path('schematic/boards/osc-core.net'));by={c.ref:dict(c.fields) for c in components}
        self.assertEqual(source_rotation_degrees(by['U103']),180)
        self.assertEqual(source_rotation_degrees(by['J900002']),180)
        absent={r for r,f in by.items() if not f.get('KiCadOrientationDeg')}
        partition=json.loads(Path('design/partition/partition.json').read_text())
        self.assertEqual(absent,{r['reference'] for r in partition['load_side_terminals'] if r['board']=='K'})
        with self.assertRaisesRegex(ValueError,'native source template'):source_rotation_degrees(by['TP990008'])
        self.assertEqual(source_rotation_degrees(by['TP990008'],37),37)

    def test_template_mutation_before_load_or_during_validation_never_rebinds(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'terminal.kicad_mod';path.write_text('original template')
            retained=capture_template_digests([path]*18);before=dict(retained)
            self.assertEqual(len(retained),1)
            path.write_text('changed before native load')
            with self.assertRaisesRegex(ValueError,'template changed'):verify_template_digest(path,retained)
            path.write_text('original template');verify_template_digest(path,retained)
            path.write_text('changed during native validation')
            with self.assertRaisesRegex(ValueError,'template changed'):verify_template_digest(path,retained)
            self.assertEqual(retained,before)


if __name__=='__main__':unittest.main()
