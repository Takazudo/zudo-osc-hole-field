import copy
import json
from pathlib import Path
import tempfile
import unittest
import audit as a


class EnvelopeTests(unittest.TestCase):
    def setUp(self):
        self.e=json.loads(a.EVIDENCE.read_text())
        self.g=json.loads((a.ROOT/a.GATE).read_text())
        self.o=json.loads((a.ROOT/a.OPTIONS).read_text())

    def test_declared_interval_and_counterfactual_margin(self):
        r=a.budget('6.1','5.6','0.3','0.25')
        self.assertEqual(r['source_depth_interval'],['5.3','5.9'])
        self.assertEqual(r['field_minus_maximum_depth'],'0.2')
        self.assertEqual(r['centered_residual_per_side'],'0.1')
        self.assertEqual(r['depth_to_retain_growth_at_maximum'],'6.40')
        self.assertIn('COUNTERFACTUAL',r['centering_condition'])
        self.assertIn('COUNTERFACTUAL',r['required_depth_scope'])
        self.assertIsNone(r['adopted_field_depth'])
        self.assertEqual(r['physical_containment'],'NOT_ESTABLISHED')

    def test_tangent_or_negative_residual_never_passes(self):
        for depth,residual in (('5.9','0.0'),('5.8','-0.1')):
            r=a.budget(depth,'5.6','0.3','0.25')
            self.assertEqual(r['field_minus_maximum_depth'],residual)
            self.assertEqual(r['physical_containment'],'NOT_ESTABLISHED')

    def test_registration_cannot_be_assumed_even_when_sufficient_width(self):
        with self.assertRaisesRegex(ValueError,'registration'):
            a.budget('100','5.6','0.3','0.25',registration={'centered':True})
        self.e['field_to_physical_registration']={'centered':True}
        with self.assertRaisesRegex(ValueError,'registration'):a.extract(self.e,self.g,self.o)

    def test_invalid_decimal_or_tolerance(self):
        for value in ('NaN','Infinity','-1',6.1):
            with self.assertRaises(ValueError):a.budget(value,'5.6','0.3','0.25')
        with self.assertRaises(ValueError):a.budget('6.1','0.1','0.3','0.25')

    def test_wrong_source_hash_unit_or_dimension(self):
        for key,value in (('sha256','0'*64),('document','OTHER')):
            e=copy.deepcopy(self.e);e['drawing'][key]=value
            with self.assertRaises(ValueError):a.extract(e,self.g,self.o)
        self.e['drawing']['depth']['unit']='inch'
        with self.assertRaises(ValueError):a.extract(self.e,self.g,self.o)

    def test_exact122_virtual_fields_only(self):
        r=a.extract(self.e,self.g,self.o)
        self.assertEqual(len(r['endpoints']),122)
        self.assertEqual(len({x['endpoint'] for x in r['endpoints']}),122)
        self.assertEqual(r['closed_height_interval_mm'],['1.8','2.2'])
        self.assertTrue(all(x['physical_containment']=='NOT_ESTABLISHED' for x in r['endpoints']))
        self.assertTrue(all('Project nominal' in x['long_axis_scope'] for x in r['endpoints']))

    def test_changed_field_or_variant_rejected(self):
        self.o['field']['depth']['value']=6.4
        with self.assertRaisesRegex(ValueError,'nominal field changed'):a.extract(self.e,self.g,self.o)
        self.o=json.loads((a.ROOT/a.OPTIONS).read_text())
        next(r for r in self.g['links'] if not r.get('gone'))['connector']='alternate'
        with self.assertRaisesRegex(ValueError,'variant'):a.extract(self.e,self.g,self.o)

    def test_altered_field_rectangle_cannot_claim_same_coverage(self):
        row=next(r for r in self.g['links'] if not r.get('gone'))
        row['geometry']['K_connector'][2]+=.1
        with self.assertRaisesRegex(ValueError,'span'):a.extract(self.e,self.g,self.o)

    def test_source_pin_failure_precedes_calculation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for path in self.e['sha256']:
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'source pin changed'):a.run(root)


if __name__=='__main__':unittest.main()
