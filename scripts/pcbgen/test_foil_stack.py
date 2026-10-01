import unittest
import json
from pathlib import Path
from scripts.pcbgen.foil_stack import resolve_stack, require_native_layers,validate_export_stack
from scripts.pcbgen.native_stack import apply


class FoilStackTests(unittest.TestCase):
    def test_all_actual_legacy_definitions_remain_raw_exportable_only(self):
        paths=sorted(Path('design/boards').glob('osc-*.json'))
        self.assertEqual(len(paths),10)
        for path in paths:
            definition=json.loads(path.read_text());rows=definition['stackup']
            self.assertEqual(validate_export_stack(rows,definition['thickness_mm'])['mode'],
                             'legacy copper-weight labels only')
            with self.assertRaises((ValueError,KeyError)):
                resolve_stack(rows,definition['thickness_mm'])
            partial=[dict(r) for r in rows];partial[0]['copper_thickness_mm']=.035
            with self.assertRaises((ValueError,KeyError)):
                validate_export_stack(partial,definition['thickness_mm'])

    def test_existing_four_foil_bands_match_historical_extractor_exactly(self):
        for path in ('design/partition/core-ground-feasibility/osc-core.json',
                     'design/partition/control-ground-feasibility/osc-control.json'):
            definition=json.loads(Path(path).read_text())
            rows=[r for r in definition['stackup'] if r['layer'].endswith('.Cu')]
            old=[(r['nominal_midplane_depth_mm']-r['copper_thickness_mm']/2,
                  r['nominal_midplane_depth_mm']+r['copper_thickness_mm']/2) for r in rows]
            old[0]=(0.,old[0][1]);old[-1]=(old[-1][0],1.6)
            current=resolve_stack(definition['stackup'],definition['thickness_mm'])
            self.assertEqual(old,current['bands'])

    def test_actual_two_foil_depths_and_native_layer_rejection(self):
        for depth in (.4, 1.6):
            rows=[{'layer':'F.Cu','copper_thickness_mm':.035},
                  {'layer':'dielectric-1','thickness_mm':depth-.07},
                  {'layer':'B.Cu','copper_thickness_mm':.035}]
            result=resolve_stack(rows,depth)
            self.assertEqual(result['layers'],('F.Cu','B.Cu'))
            self.assertEqual(result['bands'][0],(0.,.035))
            self.assertAlmostEqual(result['bands'][1][0],depth-.035)
            original=f'(kicad_pcb (general (thickness {depth})) (layers (0 "F.Cu" signal) (2 "B.Cu" signal)) (setup (grid_origin 100 50)))'
            new,_=apply(original,{'stackup':rows,'thickness_mm':depth})
            self.assertEqual(apply(new,{'stackup':rows,'thickness_mm':depth})[0],new)
            self.assertNotIn('In1.Cu',new)
            with self.assertRaisesRegex(ValueError,'enabled copper'):
                require_native_layers(('F.Cu','In1.Cu','In2.Cu','B.Cu'),result['layers'])
            with self.assertRaisesRegex(ValueError,'depth differs'):
                resolve_stack(rows[:-1]+[{**rows[-1],'nominal_midplane_depth_mm':.1}],depth)

    def test_missing_physical_thickness_is_not_inferred_from_weight(self):
        with self.assertRaises(KeyError):
            resolve_stack([{'layer':'F.Cu','copper_oz':1},
                {'layer':'dielectric-1','thickness_mm':.33},
                {'layer':'B.Cu','copper_oz':1}],.4)


if __name__=='__main__':unittest.main()
