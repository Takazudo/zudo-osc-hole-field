"""Full-wetting primal restriction and nineteen-support source integration."""
import unittest
import numpy as np
import shapely
from shapely.geometry import box
from scripts.pcbgen.test_sheet_volume import assembly,RHO,THICKNESS
from scripts.pcbgen.contact_transfer import main_contact_supports
from scripts.pcbgen.contact_constraints import restrict_wetted_terminals


class ContactConstraintTests(unittest.TestCase):
    def test_main_array_wetting_extension_and_distributed_source(self):
        centres=[(.7*i,.7*j) for i in range(-2,3) for j in range(-2,3)]
        source=shapely.union_all(main_contact_supports((0,0)))
        sink=box(2.3,-.2,2.55,.05)
        conductor=assembly(centres,(-2,-2,3,2),source,sink,1)
        profiles=[[(3,source,1.),(3,sink,-1.)]]
        unrestricted=conductor.area_profile_matrices(profiles,RHO,THICKNESS)
        receipt=restrict_wetted_terminals(conductor,[{'ref':'main','layer':3,'maximum_wetting':box(-2,-2,2,2)}])
        restricted=conductor.area_profile_matrices(profiles,RHO,THICKNESS)
        self.assertEqual(len(receipt['terminals'][0]['tied_barrels']),25)
        self.assertLess(restricted['lower'][0,0],unrestricted['lower'][0,0])
        self.assertGreater(restricted['lower'][0,0],0)
        self.assertAlmostEqual(restricted['upper'][0,0],unrestricted['upper'][0,0],places=12)
        potential=conductor.projections[3]@restricted['potential']
        sheet=conductor.sheets[3]
        selected=shapely.covers(box(-2,-2,2,2),shapely.points(sheet.xy))
        self.assertLess(np.ptp(potential[selected,0]),1e-14)
        self.assertLess(abs(source.area-19*.24**2),1e-12)


if __name__=='__main__':unittest.main()
