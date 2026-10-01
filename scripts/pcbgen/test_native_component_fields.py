"""Native field authority stays distinct from properties and original units."""
import unittest
from scripts.pcbgen.core_package_fields import native_field_projection


class NativeComponentFieldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projection=native_field_projection('schematic/boards/osc-core.net')
        cls.rows={r['ref']:r for r in cls.projection['packages']}

    def test_complete_inventory_and_distinct_native_properties(self):
        self.assertEqual(len(self.rows),3594)
        row=self.rows['U103']
        self.assertEqual(row['native_fields']['Role'],'reference_generator:A1')
        self.assertEqual(row['source_properties']['Role'],'reference_generator:A3')
        self.assertEqual(self.rows['U111']['native_fields']['LogicalCellKey'],'')
        self.assertNotEqual(self.rows['U111']['source_properties']['LogicalCellKey'],'')

    def test_mixed_unit_fields_are_each_source_supported_not_guessed_tuple(self):
        row=self.rows['U4209'];units=[u for u in self.projection['all_original_source_units'] if u['ref']=='U4209']
        fields=row['native_fields']
        for name in ('Role','LogicalCellKey','Island'):
            self.assertTrue(any(u['resolved_fields'].get(name)==fields[name] for u in units))
        self.assertFalse(any(all(u['resolved_fields'].get(n)==fields[n] for n in ('Role','LogicalCellKey','Island')) for u in units))

    def test_empty_marker_and_absent_field_are_preserved_separately(self):
        self.assertIn('dnp',self.rows['C106']['source_properties'])
        self.assertEqual(self.rows['C106']['source_properties']['dnp'],'')
        self.assertNotIn('dnp',self.rows['C106']['native_fields'])
        self.assertNotIn('exclude_from_bom',self.rows['TP301']['source_properties'])
        self.assertIn('exclude_from_bom',self.rows['TP990008']['source_properties'])
        self.assertIn('LogicalCellKey',self.rows['U1407']['native_fields'])
        self.assertNotIn('LogicalCellKey',self.rows['U1407']['source_properties'])


if __name__=='__main__':unittest.main()
