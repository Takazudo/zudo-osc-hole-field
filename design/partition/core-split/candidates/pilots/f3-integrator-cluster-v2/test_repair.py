import unittest
import repair


class RepairTests(unittest.TestCase):
    def test_domain_deduplicates_and_has_no_adaptive_sites(self):
        pose=dict(x_mm=1,y_mm=2,kicad_orientation_deg=0,side='B.Cu')
        row={'old_physical_pose':pose,'candidate_physical_pose':pose.copy()}
        c={'domain':{'translation_offsets_mm':[-.25,0,.25],'orientations_deg':[0,90,180,270]}}
        domain=repair.pose_domain(row,c)
        self.assertEqual(len(domain),36)
        self.assertEqual({x['side'] for x in domain},{'B.Cu'})
        self.assertTrue(all(.75<=x['x_mm']<=1.25 and 1.75<=x['y_mm']<=2.25 for x in domain))

    def test_source_copper_identity_is_required(self):
        row={'uuid':'example','kind':'segment','source_span':[0,3],'sha256':'bad'}
        with self.assertRaisesRegex(ValueError,'hash drift'):
            repair.load_copper([row],'abc',['B.Cu'])

    def test_preserved_source_segment_geometry(self):
        text='(segment (start 1 2) (end 3 4) (width 0.3) (layer "B.Cu") (net "AGND"))'
        row={'uuid':'example','kind':'segment','net_token':'AGND','source_span':[0,len(text)],'sha256':repair.v1.digest(text.encode())}
        rows,gs,radii,layers,ends=repair.load_copper([row],text,['B.Cu'])
        self.assertEqual(radii,[.15]);self.assertEqual(layers,[['B.Cu']]);self.assertEqual(ends,[[[1,2],[3,4]]])
        self.assertEqual(rows,[row])

    def test_repair_contract_reconciles_prior_objects(self):
        c=repair.v1.read(repair.HERE/'repair-contract.json')
        self.assertEqual(repair.v1.digest((repair.HERE/'repair-contract.json').read_bytes()),repair.CONTRACT_SHA)
        rows=c['copper_classification'];self.assertEqual(len({r['uuid'] for r in rows}),63)
        self.assertEqual(sum(r['classification']=='EXPLICIT_CANDIDATE_RECONSTRUCTION_OBLIGATION' for r in rows),29)
        self.assertEqual(c['prior_conflicts']['unique_copper_objects'],57)
        self.assertNotIn('U2306',c['movable_refs'])

    def test_relaxation_is_exact_object_not_entire_net(self):
        pad={'net':'BP','layers':['B.Cu']}
        row={'uuid':'original-contact','net_token':'FOREIGN'}
        self.assertFalse(repair.preserved_foreign(row,pad,['B.Cu'],{'original-contact'}))
        self.assertTrue(repair.preserved_foreign(row|{'uuid':'adjacent-kept'},pad,['B.Cu'],{'original-contact'}))
        self.assertFalse(repair.preserved_foreign(row,pad,['F.Cu'],set()))

    def test_mid_segment_branch_is_reconstruction_obligation(self):
        s=repair.Screen.__new__(repair.Screen)
        s.rows=[{'uuid':'main','sha256':'a','net_token':'N','kind':'segment'},
                {'uuid':'mid-T','sha256':'b','net_token':'N','kind':'segment'}]
        s.cg=[repair.LineString([(0,0),(10,0)]),repair.LineString([(5,0),(5,2)])]
        s.cr=[.15,.15];s.cl=[['B.Cu'],['B.Cu']];s.max_radius=.15;s.replay={'main'};s.ct=repair.STRtree(s.cg)
        contacts=s.same_net_contacts(0)
        self.assertEqual([r['uuid'] for r in contacts],['mid-T'])
        self.assertEqual(contacts[0]['disposition'],'PRESERVED_IN_PLACE')

    def test_via_drill_is_retained(self):
        text='(via (at 1 2) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu"))'
        row={'uuid':'v','kind':'via','net_token':'N','source_span':[0,len(text)],'sha256':repair.v1.digest(text.encode())}
        rows,*_=repair.load_copper([row],text,['F.Cu','B.Cu'])
        self.assertEqual(rows[0]['drill_mm'],.3)


if __name__=='__main__':unittest.main()
