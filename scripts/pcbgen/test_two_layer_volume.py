import unittest
import tempfile
import json
from pathlib import Path
import numpy as np
import shapely
from shapely.geometry import box, Polygon, GeometryCollection
from scripts.pcbgen.active_foil_domains import active_domains
from scripts.pcbgen.barrel_volume import BarrelVolume
from scripts.pcbgen.sheet_mesh import Sheet, make_cells
from scripts.pcbgen.sheet_volume import SheetVolume
from scripts.pcbgen.current_trial_matrix import current_matrix
from scripts.pcbgen.potential_trial_matrix import potential_matrix
from scripts.pcbgen.ground_volume_geometry import extract
from scripts.pcbgen.ground_reference import ordered_profiles

RHO=2.3e-5


class TwoLayerVolumeTests(unittest.TestCase):
    def test_extractor_keeps_physical_b_face_after_active_sheet_reindex(self):
        items=[]
        for ref,x in [('J900379',.4),('J900381',1.6)]:
            items.append({'ref':ref,'pad':'2','net':'AGND','uuid':ref,'xy_mm':[x,.5],
                'copper':{'B.Cu':[]},'analytic_primitives':{'B.Cu':{'kind':'rectangle',
                    'centre_nm':[int(x*1e6),500000],'half_size_nm':[250000,250000],
                    'quarter_turns':0,'corner_radius_nm':0}}})
        shell=[[0,0],[2,0],[2,1],[0,1]]
        data={'items':items,'holes':[],'main_rail_members':{},
            'enabled_copper_layers':['F.Cu','B.Cu'],'thickness_mm':1.6,
            'ground_reference':{'ref':'J900379','pad':'2','uuid':'J900379','layer':'B.Cu','xy_mm':[.4,.5]},
            'ground_reference_members':['J900379','J900381'],
            'stackup':[{'layer':'F.Cu','copper_thickness_mm':.035},
                {'layer':'dielectric-1','thickness_mm':1.53},
                {'layer':'B.Cu','copper_thickness_mm':.035}],
            'zones':[{'uuid':'ground','layer':'B.Cu','net':'AGND','keepout':False,
                'original_filled_contours':[{'shell':shell,'holes':[]}],'native_unfracture_audit':{}}]}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'native.json';path.write_text(json.dumps(data))
            geometry=extract(path,RHO)
        self.assertEqual(geometry['physical_foil_layers'],['F.Cu','B.Cu'])
        self.assertEqual(geometry['active_sheet_layers'],['B.Cu'])
        self.assertEqual(geometry['physical_to_active_sheet'],{'F.Cu':None,'B.Cu':0})
        self.assertEqual(geometry['barrels'],[])
        for port in geometry['ports']:
            self.assertEqual((port['layer'],port['physical_foil_index'],port['physical_layer'],port['source_face']),
                (0,1,'B.Cu','bottom'))
        self.assertEqual(ordered_profiles(geometry)[4]['pad'],'2')

    def test_b_only_zero_barrels_and_separate_source_free_island(self):
        empty=GeometryCollection();body=box(0,0,2,1);island=box(3,0,4,1)
        a=box(.1,.2,.35,.45);b=box(1.65,.2,1.9,.45)
        domains=active_domains([empty,body.union(island)],[empty,body.union(island)],
            ['F.Cu','B.Cu'],[[],[a,b]],0)
        self.assertEqual(domains['physical_indices'],[1])
        self.assertEqual(domains['layers'],['B.Cu'])
        self.assertEqual(domains['outer'],[body])
        with self.assertRaisesRegex(ValueError,'empty physical foil'):
            active_domains([empty,body],[empty,body],['F.Cu','B.Cu'],[[a],[b]],0)
        with self.assertRaisesRegex(ValueError,'interlayer connection'):
            active_domains([body,body],[body,body],['F.Cu','B.Cu'],[[a],[b]],0)
        with self.assertRaisesRegex(ValueError,'source-bearing physical'):
            active_domains([empty,body.union(island)],[empty,body.union(island)],
                ['F.Cu','B.Cu'],[[],[a,b,box(3.2,.2,3.4,.4)]],0)
        sheet=Sheet(body,make_cells(body.bounds,.25,.125,a.union(b).buffer(.1)),RHO/.035,source_patches=[a,b])
        conductor=SheetVolume([sheet],[RHO/.035],[])
        profiles=[[(0,a,1.),(0,b,-1.)]]
        conductor.certificate_mode='current';upper=current_matrix(conductor,profiles,RHO,[.035])
        conductor.certificate_mode='potential';lower=potential_matrix(conductor,profiles)
        self.assertGreater(upper['energy'][0,0],lower['energy'][0,0])
        self.assertLess(upper['maximum_equation_residual_A'],1e-8)
        self.assertEqual(upper['conservation_correction'][0]['maximum_last_port_change_A'],0.)
        # Physically mirror the B foil into an F foil. Identical scalar energy
        # follows from reflected one-face lifting; no phantom second sheet.
        reflected=active_domains([body,empty],[body,empty],['F.Cu','B.Cu'],[[a,b],[]],0)
        self.assertEqual(reflected['physical_indices'],[0])
        disconnected=Sheet(body.union(island),make_cells((0,0,4,1),.25,.125,a.union(b)),RHO/.035,source_patches=[a,b])
        with self.assertRaisesRegex(ValueError,'disconnected'):
            SheetVolume([disconnected],[RHO/.035],[])

    def test_two_foil_barrel_at_both_actual_depths(self):
        for depth in (.4,1.6):
            thickness=[.035,.035];bands=[(0,.035),(depth-.035,depth)]
            barrel=BarrelVolume(.15,.025,.275,depth,bands,RHO,polygon_sides=8,
                angular_subdivisions=1,radial_steps=1,band_steps=1,gap_steps=2)
            copper=box(-1,-1,1,1).difference(Polygon(barrel.interface_polygon()))
            a=box(.4,.4,.65,.65);b=box(-.7,-.5,-.45,-.25)
            cells=make_cells(copper.bounds,.5,.125,a.union(b).buffer(.2))
            sheets=[Sheet(copper,cells,RHO/t,source_patches=[a,b],
                interfaces=[{'relative':barrel.interface_polygon(),'centre':(0,0)}]) for t in thickness]
            conductor=SheetVolume(sheets,[RHO/t for t in thickness],[(barrel,(0,0))])
            forward,_,_=conductor.area_pair(0,a,1,b,RHO,thickness)
            reverse,_,_=conductor.area_pair(1,b,0,a,RHO,thickness)
            self.assertGreater(forward['upper_ohm'],forward['lower_ohm'])
            self.assertAlmostEqual(forward['upper_ohm'],reverse['upper_ohm'],places=12)
            self.assertLess(forward['maximum_volume_sheet_divergence_A'],1e-8)


if __name__=='__main__':unittest.main()
