import copy
import json
import unittest
import stage15_detent as m
class Detent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.args=[json.loads(p.read_text()) for p in [m.ROOT/'design/standard/electrical-standard.json',m.ROOT/'design/standard/parts-shortlist.json',m.ROOT/'design/architecture-278/implementation/stage10/inventory-report.json',m.OUT/'primary-evidence.json']]
    def test_exact_no_detent(self):
        r=m.analyze(*self.args);self.assertEqual(r['selected_mpn'],'PTV09A-4020F-B104');self.assertEqual(r['detent'],'NONE')
        self.assertEqual(r['ordering_decode']['detent_option'],'0');self.assertFalse(r['component_geometry_changed'])
    def test_centre_variant_rejected(self):
        a=copy.deepcopy(self.args);next(p for p in a[1]['parts'] if p['id']=='pot_104')['mpn']='PTV09A-4220F-B104'
        with self.assertRaises(ValueError):m.analyze(*a)
    def test_bom_mismatch_rejected(self):
        a=copy.deepcopy(self.args);a[2]['packages']['RV1308']['attributes']['MPN']='PTV09A-4220F-B104'
        with self.assertRaises(ValueError):m.analyze(*a)
    def test_wrong_option_definition_rejected(self):
        a=copy.deepcopy(self.args);a[3]['option_definitions']['0']='Center'
        with self.assertRaises(ValueError):m.analyze(*a)
    def test_electrical_centre_is_not_detent(self):
        r=m.analyze(*self.args);self.assertIn('never tactile click',r['contract_addendum']['centre_definition'])
        self.assertFalse(r['hardware_acceptance'])
if __name__=='__main__':unittest.main()
