import copy
import json
import math
import unittest
import projection as p


class ProjectionTests(unittest.TestCase):
    def setUp(self):self.m=json.loads(p.MANIFEST.read_text())

    def test_four_counts_and_exact_sheet_binding(self):
        for n in (8,14,26,40):
            pattern=p.pattern(n)
            self.assertEqual(pattern['source_sheet'],1 if n<=34 else 2)
            self.assertEqual(len(pattern['contacts']),n)
            xs=[x['relative_local_mm'][0] for x in pattern['contacts']]
            self.assertEqual(xs[0],-(n-1)*.25)
            self.assertTrue(all(xs[i+1]-xs[i]==.5 for i in range(n-1)))
            self.assertTrue(all(x['relative_local_mm'][1]==0 for x in pattern['contacts']))
            for tab in pattern['nominal_tab_rectangles_local_mm']:
                self.assertAlmostEqual(tab[2]-tab[0],1.8)
                self.assertEqual(tab[1:4:2],[2.15,4.35])
        with self.assertRaises(ValueError):p.pattern(35)

    def test_cardinal_and_face_parity(self):
        for d in ([1,0],[-1,0],[0,1],[0,-1]):
            f=p.basis(d,'F');b=p.basis(d,'B')
            self.assertEqual(f['y_basis'],d);self.assertEqual(b['y_basis'],d)
            self.assertEqual(b['x_basis'],[-v for v in f['x_basis']])
            self.assertEqual(f['determinant'],1);self.assertEqual(b['determinant'],-1)
            for basis in (f,b):
                x,y=basis['x_basis'],basis['y_basis']
                self.assertEqual(sum(a*b for a,b in zip(x,y)),0)
                self.assertEqual(x[0]*y[1]-x[1]*y[0],basis['determinant'])

    def test_source_view_mirror_requires_both_point_and_basis(self):
        for face in ('F','B'):
            for d in ([1,0],[-1,0],[0,1],[0,-1]):
                self.assertEqual(p.relative_vector([-3.25,2.15],d,face),
                                 p.relative_vector([-3.25,2.15],d,face,True))
                self.assertNotEqual(p.basis(d,face)['x_basis'],p.basis(d,face,True)['x_basis'])

    def test_no_arbitrary40_contact_reversal(self):
        for face in ('F','B'):
            for d in ([1,0],[-1,0],[0,1],[0,-1]):
                x=p.basis(d,face)['x_basis']
                for n in (8,14,26,40):
                    v=p.relative_vector(p.pattern(n)['contacts'][0]['relative_local_mm'],d,face)
                    self.assertLess(sum(a*b for a,b in zip(x,v)),0)

    def test_122_endpoint_projection_keeps_physical_unknowns(self):
        r=p.run();self.assertEqual(r['virtual_endpoints'],122)
        self.assertEqual(r['physical_mappings_established'],0)
        self.assertEqual(len({e['endpoint_id'] for e in r['endpoints']}),122)
        for e in r['endpoints']:
            for key in ('row_midpoint_offset_from_field_center_mm','row_midpoint_panel_mm',
                        'physical_pad1_local_mm','physical_pad1_panel_mm','physical_footprint_rotation_deg'):
                self.assertIsNone(e[key])
            self.assertEqual(e['physical_end_to_end_cable_parity'],'UNESTABLISHED')
            self.assertEqual(e['logical_to_physical_contact_mapping'],'NOT_ESTABLISHED')

    def test_reference_height_cannot_promote(self):
        self.m['manufacturer']['open_height_mm']['guaranteed_maximum']=True
        with self.assertRaisesRegex(ValueError,'reference open'):p.verify_manifest(self.m,p.ROOT)

    def test_sheet_or_absolute_registration_drift_rejected(self):
        for kind in ('sheet','registration'):
            m=copy.deepcopy(self.m)
            if kind=='sheet':m['variants']['40']['sheet']=1
            else:m['manufacturer']['registration']='FIELD_CENTER_IS_ROW_CENTER'
            with self.assertRaises(ValueError):p.verify_manifest(m,p.ROOT)

    def test_invalid_direction_face_source_pin(self):
        for d in ([1,1],[0,0],[float('nan'),0]):
            with self.assertRaises(ValueError):p.basis(d,'B')
        with self.assertRaises(ValueError):p.basis([1,0],'unknown')
        self.m['sha256'][p.GATE]='0'*64
        with self.assertRaisesRegex(ValueError,'source pin changed'):p.verify_manifest(self.m,p.ROOT)


if __name__=='__main__':unittest.main()
