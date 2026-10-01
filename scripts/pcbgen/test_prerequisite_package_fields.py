import unittest
from pathlib import Path
from scripts.pcbgen.prerequisite_package_fields import project
from scripts.pcbgen.core_package_fields import native_field_projection
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware


class PrerequisitePackageFieldsTests(unittest.TestCase):
    def test_control_all_packages_units_and_fixed_panel_hardware(self):
        result=project('schematic/boards/osc-control.net','boards/osc-control')
        packages={r['ref']:r for r in result['packages']};self.assertEqual(len(packages),418)
        hardware=selected_hardware(load_definition(Path('design/boards/osc-control.json')),load_lock(Path('design/grid/placements.lock.json')))
        self.assertEqual(len(hardware),139)
        for h in hardware:
            fields=packages[h['ref']]['source_properties']
            self.assertEqual(list(map(float,fields['FootprintOriginMm'].split(','))),[h['x_mm'],h['y_mm']])
            self.assertEqual(float(fields['KiCadOrientationDeg']),h['rot_deg'])
            self.assertEqual(fields['BoardSide'],'F.Cu')
        missing=[r['ref'] for r in result['packages'] if not r['source_properties'].get('KiCadOrientationDeg')]
        self.assertEqual(sorted(missing),['TP990025','TP990027','TP990029','TP990031','TP990033','TP990035'])
        self.assertTrue(all(any(u['ref']==ref for u in result['all_original_source_units']) for ref in packages))

    def test_same_K_native_field_values_as_reviewed_historical_projection(self):
        old=native_field_projection('schematic/boards/osc-core.net')
        new=project('schematic/boards/osc-core.net','boards/osc-core')
        self.assertEqual(new['packages'],old['packages'])
        normalize=lambda rows:[{**r,'source':str(Path(r['source']).resolve())} for r in rows]
        self.assertEqual(new['all_original_source_units'],normalize(old['all_original_source_units']))
        self.assertEqual(new['source_sheet_sha256'],{str(Path(p).resolve()):h for p,h in old['source_sheet_sha256'].items()})


if __name__=='__main__':unittest.main()
