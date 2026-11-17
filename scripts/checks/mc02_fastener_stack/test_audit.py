import copy
import json
from pathlib import Path
import tempfile
import unittest
import audit as a


class FastenerTests(unittest.TestCase):
    def setUp(self): self.e = json.loads(a.EVIDENCE.read_text())

    def test_conditional_nominal_budgets(self):
        r = a.audit(self.e)
        for key in ('source_commit','engineering_commit','procedure_amendment','nut_source_amendment'):
            self.assertEqual(r[key],self.e[key])
        self.assertEqual(len(r['sites']), 4)
        for row in r['sites']:
            expected = ('.15','.65') if row['front_board'] != 'P' else ('2.15','2.65')
            got = row['conditional_washer_plus_protrusion_capacity_mm']
            self.assertEqual(a.number(got['lower']), a.number(expected[0]))
            self.assertEqual(a.number(got['upper']), a.number(expected[1]))
            self.assertEqual(row['assembly_verdict'], 'NOT_SHOWN')
            self.assertIsNone(row['worst_case_washer_limit_mm'])
            self.assertEqual(len(row['unknowns']), 5)

    def test_full_interval_extrema_not_nominal_subtraction(self):
        self.assertEqual(a.residual(('24.8','25.2'),('22.0','22.4'),('2.15','2.65')),
                         {'lower':'-0.25','upper':'1.05','unit':'mm'})

    def test_negative_capacity_preserved(self):
        self.assertEqual(a.residual(('20','20'),('22','22'),('2','3'))['upper'], '-4')

    def test_touching_boundary_is_zero_not_pass(self):
        self.assertEqual(a.residual(('25','25'),('22.35','22.35'),('2.65','2.65'))['lower'], '0.00')

    def test_invalid_intervals(self):
        for value in (('2','1'),('NaN','3'),('-1','2'),('0','Infinity'),(1,'2')):
            with self.assertRaises(ValueError): a.residual(value,('1','1'),('1','1'))

    def test_reviewed_source_cannot_waive_version_or_change_identity(self):
        for key,value in (('status','PRIMARY_CONFIRMED'),('verified_pdf_sha256','a'*64),
                          ('identity','Keystone 4688'),('nominal_mm','2.3'),
                          ('finish_disposition','RESOLVED'),('retained_catalog_finish','steel / zinc'),
                          ('material_finish','steel / nickel')):
            e=copy.deepcopy(self.e);e['nut_handoff'][key]=value
            with self.assertRaisesRegex(ValueError,'reviewed source contract changed'): a.audit(e)

    def test_verified_dimension_removes_only_source_gap(self):
        result=a.audit(self.e)
        self.assertEqual(result['nut_handoff']['status'],'PRIMARY_DIMENSION_VERIFIED')
        self.assertEqual(result['nut_handoff']['verified_pdf_sha256'],result['nut_handoff']['expected_pdf_sha256'])
        self.assertEqual(result['nut_handoff']['reviewed_drawing']['thread'],'M3 x 0.5')
        self.assertIsNone(result['nut_handoff']['reviewed_drawing']['revision'])
        self.assertIsNone(result['nut_handoff']['current_product_page']['html_sha256'])
        self.assertEqual(result['nut_handoff']['current_product_page']['finish_plating'],'Zinc & Clear Chromate')
        self.assertEqual(result['nut_handoff']['finish_disposition'],'UNRESOLVED_VERSION_DISCREPANCY')
        for row in result['sites']:
            self.assertNotIn('nut dimension primary-source verification',row['unknowns'])
            self.assertIn('nut finish/version discrepancy',row['unknowns'])
            self.assertIn('washer exact identity and thickness tolerance',row['unknowns'])
            self.assertEqual(row['reviewed_nut_interval_mm'],['2.15','2.65'])
            self.assertEqual(row['assembly_verdict'],'NOT_SHOWN')
            self.assertIsNone(row['worst_case_washer_limit_mm'])

    def test_changed_source_pin(self):
        e=copy.deepcopy(self.e);e['sha256'][a.THREAD]='0'*64
        with self.assertRaisesRegex(ValueError,'source pin changed'): a.audit(e)

    def test_source_closure_missing(self):
        e=copy.deepcopy(self.e);del e['sha256'][a.STACK]
        with self.assertRaisesRegex(ValueError,'source closure'): a.audit(e)

    def test_site_and_grip_not_silently_rebound(self):
        # A changed site must fail even if someone refreshes its source digest.
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);e=copy.deepcopy(self.e)
            for path in e['sha256']:
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((a.ROOT/path).read_bytes())
            p=root/a.RULED;x=json.loads(p.read_text());x['sleeves'][0]['xy'][0]+=1;p.write_text(json.dumps(x))
            e['sha256'][a.RULED]=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError,'fixed site'):a.audit(e,root)

    def test_canonical_nut_disagrees_with_supplement_even_after_file_repin(self):
        import hashlib
        for kind in ('height','unknowns','finish'):
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory);e=copy.deepcopy(self.e)
                for name in e['sha256']:
                    path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((a.ROOT/name).read_bytes())
                path=root/a.THREAD;doc=json.loads(path.read_text())
                if kind=='height':doc['screws']['nut_height_mm']['nominal']=2.3
                elif kind=='unknowns':doc['screws']['nut_height_source']['remaining_unknowns']=[]
                else:doc['screws']['nut_height_source']['finish_disposition']='RESOLVED'
                path.write_text(json.dumps(doc));e['sha256'][a.THREAD]=hashlib.sha256(path.read_bytes()).hexdigest()
                with self.assertRaisesRegex(ValueError,'canonical nut source differs'):a.audit(e,root)


if __name__ == '__main__': unittest.main()
