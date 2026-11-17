import copy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest
import audit as a


class LandTests(unittest.TestCase):
    def setUp(self):
        self.e=json.loads(a.EVIDENCE.read_text());self.g=json.loads((a.ROOT/a.GATE).read_text());self.o=json.loads((a.ROOT/a.OPTIONS).read_text())
    def test_derive_chain_extrema(self):
        y=a.land_y(self.e['dimensions'])
        self.assertEqual(list(map(Decimal,y['nominal'])),[Decimal('-.65'),Decimal('4.35')])
        self.assertEqual(list(map(Decimal,y['outer_interval'])),[Decimal('-.7'),Decimal('4.6')])
    def test_conditional_offsets_all_four_variants(self):
        r=a.extract(self.e,self.g,self.o)
        self.assertEqual(sum(x['endpoints'] for x in r['variants']),122)
        for variant in r['variants']:
            zero,margin=variant['scenarios']
            for actual,expected in ((zero['delta_x'],('-.2','.2')),(zero['delta_y'],('-2.35','-1.55')),
                                    (margin['delta_x'],('.05','-.05')),(margin['delta_y'],('-2.10','-1.80'))):
                self.assertEqual((Decimal(actual['lower_mm']),Decimal(actual['upper_mm'])),tuple(map(Decimal,expected)))
            self.assertEqual(margin['joint_interval_status'],'EMPTY_CONDITIONAL_RECTANGLE')
            self.assertEqual(variant['physical_containment'],'NOT_ESTABLISHED')
            self.assertIsNone(variant['actual_registration']);self.assertIsNone(variant['adopted_registration'])
            self.assertTrue(variant['tab_G_dominates_signal_pad_span'])
    def test_exact_tangent_is_only_conditional(self):
        x=a.registration_interval('2','-1','1','0')
        self.assertEqual((x['lower_mm'],x['upper_mm']),('0','0'))
        self.assertEqual(x['status'],'NONEMPTY_CONDITIONAL_INTERVAL')
        self.assertEqual(a.registration_interval('2','-1','1','.0001')['status'],'EMPTY_CONDITIONAL_INTERVAL')
    def test_signed_translation_not_absolute_clearance(self):
        x=a.registration_interval('6.1','-.7','4.6','0')
        self.assertLess(Decimal(x['upper_mm']),0)
        self.assertNotIn('PASS',json.dumps(x))
    def test_no_real_registration_or_body_union_promotion(self):
        for key,value in (('actual_registration',[0,-2]),('full_body_terminal_union_established',True)):
            e=copy.deepcopy(self.e);e[key]=value
            with self.assertRaisesRegex(ValueError,'not established'):a.extract(e,self.g,self.o)
    def test_wrong_primary_source_or_unit(self):
        e=copy.deepcopy(self.e);e['drawing']['sha256']='0'*64
        with self.assertRaises(ValueError):a.extract(e,self.g,self.o)
        self.e['dimensions']['signal_pad_length']['unit']='inch'
        with self.assertRaises(ValueError):a.extract(self.e,self.g,self.o)
    def test_tolerance_is_not_dropped(self):
        self.e['dimensions']['pad_to_tab_gap']['tolerance']='0'
        with self.assertRaises(ValueError):a.extract(self.e,self.g,self.o)
    def test_invalid_interval_inputs(self):
        for values in [('0','-1','1','0'),('2','1','-1','0'),('2','-1','1','-1'),('NaN','-1','1','0')]:
            with self.assertRaises(ValueError):a.registration_interval(*values)
    def test_source_bytes_checked_before_arithmetic(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for path in self.e['sha256']:
                target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b'bad')
            with self.assertRaisesRegex(ValueError,'source pin changed'):a.run(root)


if __name__=='__main__':unittest.main()
