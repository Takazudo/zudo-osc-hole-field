"""PTH wall/face identity, missing material and source-drift negatives."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts.pcbgen.pth_source_geometry import certify,run,ROOT,native_physical_stack


class PTHSourceGeometryTest(unittest.TestCase):
    def fixture(self):
        layers=['F.Cu','In1.Cu','In2.Cu','B.Cu']
        p={'kind':'circle','centre_nm':[0,0],'half_size_nm':[850000,850000],'corner_radius_nm':0,'quarter_turns':0}
        pad={'ref':'RV1','pad':'1','uuid':'pth','net':'AGND','copper':{l:[] for l in layers},'analytic_primitives':{l:dict(p) for l in layers}}
        hole={'uuid':'pth','net':'AGND','plated':True,'xy_mm':[0,0],'size_mm':[1,1],'copper_layers':layers}
        raw=('RV1','(pad "1" thru_hole circle (drill 1) (layers "*.Cu" "*.Mask") (remove_unused_layers no) (net "AGND") (uuid "pth"))')
        stack={'depth_nm':1600000,'enabled_layers':layers,'bands':[{'layer':l,'z_nm':[z,z+70000],'thickness_nm':70000} for l,z in zip(layers,[0,130000,1400000,1530000])]}
        outline=[(-2000000,-2000000),(2000000,-2000000),(2000000,2000000),(-2000000,2000000)]
        return pad,hole,raw,stack,[hole],outline

    def test_distinct_wall_exterior_faces_and_internal_attachments(self):
        r=certify(*self.fixture())
        self.assertEqual(r['inner_wall']['inner_radius_nm'],500000)
        self.assertEqual(r['inner_wall']['contained_shell_outer_radius_nm'],525000)
        self.assertFalse(r['inner_wall']['physical_finished_wall_and_plating_qualified'])
        self.assertEqual(r['inner_wall']['z_nm'],[0,1600000])
        self.assertEqual(r['exterior_source_parts'],['inner_wall','F.Cu_annular_face','B.Cu_annular_face'])
        faces=r['foil_faces'];self.assertEqual(len(faces),4)
        self.assertEqual([f['outward_normal_stack_depth'] for f in faces],[-1,None,None,1])
        for f in faces:
            self.assertGreater(f['shell_to_annulus_overlap_area_nm2'],0)
            self.assertGreater(f['nominal_radial_margin_beyond_minimum_shell_nm'],0)
            self.assertEqual(len(f['domains']),1)  # actual complete circle annulus

    def test_wrong_net_incomplete_wall_and_other_hole(self):
        for kind in ('wrongnet','unplated','missingface','unusedlayers'):
            args=copy.deepcopy(list(self.fixture()))
            if kind=='wrongnet':args[1]['net']='+5V'
            elif kind=='unplated':args[1]['plated']=False
            elif kind=='missingface':args[1]['copper_layers']=args[1]['copper_layers'][:-1]
            else:args[2]=(args[2][0],args[2][1].replace('unused_layers no','unused_layers yes'))
            with self.subTest(kind=kind),self.assertRaises(ValueError):certify(*args)
        args=list(self.fixture());other=copy.deepcopy(args[1]);other.update(uuid='foreign',xy_mm=[.8,0],size_mm=[.3,.3]);args[4]=args[4]+[other]
        with self.assertRaisesRegex(ValueError,'other drill'):certify(*args)

    def test_clipped_annulus_and_insufficient_nominal_wall_width(self):
        args=list(self.fixture());args[5]=[(-2000000,-2000000),(800000,-2000000),(800000,2000000),(-2000000,2000000)]
        with self.assertRaisesRegex(ValueError,'native cut'):certify(*args)
        args=copy.deepcopy(list(self.fixture()))
        for p in args[0]['analytic_primitives'].values():p['half_size_nm']=[520000,520000]
        with self.assertRaisesRegex(ValueError,'insufficient nominal'):certify(*args)



if __name__=='__main__':unittest.main()
