import copy
import unittest
from scripts.pcbgen.source_flux_boundary_inventory import circle_drill_separation,inventory


class SourceBoundaryInventoryTest(unittest.TestCase):
    def test_circle_corner_false_positive_and_actual_overlap(self):
        p={'kind':'roundrect','centre_nm':[100000000,50000000],'half_size_nm':[737500,200000],'quarter_turns':0,'corner_radius_nm':100000}
        hole={'size_mm':[.3,.3],'xy_mm':[100.87,50.33]}
        self.assertEqual(circle_drill_separation(p,hole)['status'],'proved disjoint')
        hole['xy_mm']=[100.7,50.1]
        self.assertEqual(circle_drill_separation(p,hole)['status'],'actual guarded drill overlap')
        for turn,xy in [(1,[99.9,50.7]),(2,[99.3,49.9]),(3,[100.1,49.3])]:
            r=copy.deepcopy(p);r['quarter_turns']=turn;hole['xy_mm']=xy
            self.assertEqual(circle_drill_separation(r,hole)['status'],'actual guarded drill overlap')
        hole['size_mm']=[.3,.6]
        self.assertEqual(circle_drill_separation(p,hole)['status'],'unsupported drill shape; not admitted')

    def test_source_face_identity_and_foreign_drill(self):
        p={'kind':'rectangle','centre_nm':[0,0],'half_size_nm':[300000,400000],'quarter_turns':0,'corner_radius_nm':0}
        item={'ref':'C1','pad':'2','uuid':'pad1','net':'AGND','copper':{'B.Cu':[]},'analytic_primitives':{'B.Cu':p}}
        n={'board_id':'test','board_sha256':'test','items':[item],'holes':[]}
        part={'boards':[{'id':'test','board_key':'J'}],'assignment':{'components':[{'ref':'C1','board':'J','fitted':True}]}}
        io={'physical_packages':[{'ref':'C1','dnp':False}],'allowed_crossings':[{'net':'AGND','members':[{'ref':'C1','pin':'2'}]}]}
        r=inventory(n,part,io)['own_source_contacts'][0];self.assertEqual(r['family'],'convex_SMD');self.assertEqual(r['face'],'B.Cu')
        n['holes']=[{'uuid':'foreign','size_mm':[.3,.3],'xy_mm':[0.,0.]}]
        r=inventory(n,part,io)['own_source_contacts'][0];self.assertEqual(r['family'],'SMD_drill_overlap_unresolved');self.assertEqual(r['actual_or_unproved_drill_uuids'],['foreign'])
        n['items']=[]
        with self.assertRaises(ValueError):inventory(n,part,io)

    def test_unexpected_ground_on_assigned_fitted_package_rejects(self):
        primitive={'kind':'rectangle','centre_nm':[0,0],'half_size_nm':[300000,400000],
                   'quarter_turns':0,'corner_radius_nm':0}
        def item(ref,uuid):
            return {'ref':ref,'pad':'2','uuid':uuid,'net':'AGND','copper':{'B.Cu':[]},
                    'analytic_primitives':{'B.Cu':primitive}}
        native={'board_id':'test','board_sha256':'test','items':[item('C1','pad1'),item('C2','pad2')],
                'holes':[]}
        partition={'boards':[{'id':'test','board_key':'J'}],
                   'assignment':{'components':[{'ref':ref,'board':'J','fitted':True}
                                               for ref in ('C1','C2')]}}
        io={'physical_packages':[{'ref':ref,'dnp':False} for ref in ('C1','C2')],
            'allowed_crossings':[{'net':'AGND','members':[{'ref':'C1','pin':'2'}]}]}
        with self.assertRaisesRegex(ValueError,'native/source fitted contact mismatch'):
            inventory(native,partition,io)


if __name__=='__main__':unittest.main()
