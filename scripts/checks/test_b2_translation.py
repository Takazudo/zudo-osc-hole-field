"""Negative and exact-unit checks for the disposable Stage43 translation."""
from pathlib import Path
import importlib.util
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
spec=importlib.util.spec_from_file_location('b2_translation',ROOT/'design/architecture-278/implementation/stage43/b2-translation/translation.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.segment={'kind':'segment','net':'a','start_nm':[123456789,987654321],'end_nm':[123456790,987654320],'width_nm':200000,'layer':'B.Cu','uuid':'source'}
    def test_exact_integer_translation(self):
        r=m.translated(self.segment,{'a':'b'})
        self.assertEqual(r['start_nm'],[157456789,987654321]);self.assertEqual(r['end_nm'],[157456790,987654320])
        self.assertEqual((r['width_nm'],r['layer'],r['net']),(200000,'B.Cu','b'))
        self.assertEqual(self.segment['start_nm'],[123456789,987654321])
    def test_shared_net_stays_shared(self):
        r=dict(self.segment,net='+5V');self.assertEqual(m.translated(r,{'+5V':'+5V'})['net'],'+5V')
    def test_via_geometry_preserved(self):
        v={'kind':'via','net':'a','at_nm':[1,2],'diameter_nm':700000,'drill_nm':300000,'layers':['F.Cu','B.Cu'],'locked':False,'uuid':'via'}
        r=m.translated(v,{'a':'b'});self.assertEqual(r['at_nm'],[34000001,2])
        for key in ('diameter_nm','drill_nm','layers','locked'):self.assertEqual(r[key],v[key])
    def test_unmapped_net_rejected(self):
        with self.assertRaises(KeyError):m.translated(self.segment,{'other':'b'})
    def test_collapsed_nets_rejected(self):
        with self.assertRaises(ValueError):m.translated(self.segment,{'a':'b','c':'b'})
    def test_unsupported_copper_rejected(self):
        with self.assertRaises(ValueError):m.translated(dict(self.segment,kind='arc'),{'a':'b'})
    def test_deterministic_distinct_new_ids(self):
        a=m.translated(self.segment,{'a':'b'});b=m.translated(self.segment,{'a':'b'})
        self.assertEqual(a,b);self.assertNotEqual(a['uuid'],self.segment['uuid'])
        self.assertNotEqual(a['uuid'],m.translated(dict(self.segment,uuid='other'),{'a':'b'})['uuid'])

if __name__=='__main__':unittest.main()
