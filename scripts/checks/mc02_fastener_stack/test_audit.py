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
        self.assertEqual(len(r['sites']), 4)
        for row in r['sites']:
            expected = ('.15','.65') if row['front_board'] != 'P' else ('2.15','2.65')
            got = row['conditional_washer_plus_protrusion_capacity_mm']
            self.assertEqual(a.number(got['lower']), a.number(expected[0]))
            self.assertEqual(a.number(got['upper']), a.number(expected[1]))
            self.assertEqual(row['assembly_verdict'], 'NOT_SHOWN')
            self.assertIsNone(row['worst_case_washer_limit_mm'])
            self.assertEqual(len(row['unknowns']), 6)

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

    def test_unverified_handoff_cannot_promote(self):
        for key,value in (('status','PRIMARY_CONFIRMED'),('verified_pdf_sha256','a'*64),
                          ('identity','Keystone 4688'),('nominal_mm','2.3'),
                          ('finish_disposition','RESOLVED')):
            e=copy.deepcopy(self.e);e['nut_handoff'][key]=value
            with self.assertRaisesRegex(ValueError,'handoff changed'): a.audit(e)

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


if __name__ == '__main__': unittest.main()
