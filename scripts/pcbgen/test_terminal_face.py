"""Native terminal-face selection and a reflected four-foil current witness."""
import unittest
import numpy as np
from shapely.geometry import box,Polygon
from scripts.pcbgen.terminal_face import external_smd_face,main_land_face
from scripts.pcbgen.barrel_volume import BarrelVolume
from scripts.pcbgen.sheet_mesh import Sheet,make_cells
from scripts.pcbgen.sheet_volume import SheetVolume
from scripts.pcbgen.test_sheet_volume import RHO,BANDS,THICKNESS


class TerminalFaceTests(unittest.TestCase):
    def test_exact_smd_face_and_land_shape(self):
        for name,layer in [('F.Cu',0),('B.Cu',3)]:
            self.assertEqual(external_smd_face({name:box(0,0,.2,.7)},'GH:1'),layer)
            self.assertEqual(main_land_face({name:box(-2,-2,2,2)}),layer)
            self.assertIsNone(main_land_face({name:box(-1,-4,1,4)}))
        for shapes in ({'In1.Cu':box(0,0,1,1)},
                       {'F.Cu':box(0,0,1,1),'B.Cu':box(0,0,1,1)}):
            with self.assertRaisesRegex(ValueError,'exactly one external'):
                external_smd_face(shapes,'GH:1')

    def test_reflected_stack_and_actual_source_foil_keep_energy(self):
        source=box(.4,.4,.65,.65);sink=box(-.7,-.5,-.45,-.25)
        results=[]
        for reflected in (False,True):
            bands=[(round(1.6-b,12),round(1.6-a,12)) for a,b in BANDS[::-1]] if reflected else BANDS
            thickness=THICKNESS[::-1] if reflected else THICKNESS
            barrel=BarrelVolume(.15,.025,.275,1.6,bands,RHO,polygon_sides=8,
                angular_subdivisions=1,radial_steps=1,band_steps=1,gap_steps=2)
            copper=box(-1,-1,1,1).difference(Polygon(barrel.interface_polygon()))
            cells=make_cells(copper.bounds,.5,.125,source.union(sink).buffer(.2))
            sheets=[Sheet(copper,cells,RHO/t,source_patches=[source,sink],
                interfaces=[{'relative':barrel.interface_polygon(),'centre':(0,0)}]) for t in thickness]
            conductor=SheetVolume(sheets,[RHO/t for t in thickness],[(barrel,(0,0))])
            terminal=external_smd_face({'F.Cu' if reflected else 'B.Cu':source},'GH:1')
            result,_,_=conductor.area_pair(terminal,source,2 if reflected else 1,sink,RHO,thickness)
            self.assertLess(result['maximum_volume_sheet_divergence_A'],1e-8)
            results.append([result['lower_ohm'],result['upper_ohm']])
        np.testing.assert_allclose(results[0],results[1],rtol=1e-8,atol=1e-12)


if __name__=='__main__':unittest.main()
