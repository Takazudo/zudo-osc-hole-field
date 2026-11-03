import copy
import unittest
import stage15_packages as m

class Packages(unittest.TestCase):
    def setUp(self):
        self.args=[m.read(n) for n in ('stage15/package-input.json','stage13/package-report.json','stage10/mechanical-report.json')]
    def test_complete_local_replacement(self):
        r=m.analyze(*self.args)
        self.assertEqual(len(r['endpoint_aliases']),12)
        self.assertEqual(r['counts']['source_pads_after'],291)
        self.assertEqual([e['replaces'] for e in r['elements'] if e['connected']],m.REPLACED)
    def test_fixed_and_capacitor_unchanged(self):
        r=m.analyze(*self.args)
        for ref,p in self.args[1]['placements'].items():
            if ref not in m.REPLACED:self.assertEqual(p,r['placements'][ref])
    def test_quiet_shield_and_spares(self):
        r=m.analyze(*self.args)
        for ref in ('RN7101','RN7102'):self.assertEqual(r['placements'][ref]['pins']['9'],'AGND')
        self.assertEqual({p for p,n in r['placements']['RN7102']['pins'].items() if n is None},{'3','4','5','6'})
    def test_wrong_grade(self):
        self.args[0]['MPN']='LT5400BIMS8E-2#PBF'
        with self.assertRaises(ValueError):m.analyze(*self.args)
    def test_remote_network_rejected(self):
        self.args[0]['networks']['RN7102']['board']='A01-core'
        with self.assertRaises(ValueError):m.analyze(*self.args)
    def test_collision(self):
        self.args[0]['networks']['RN7101']['origin_mm']=[264,249]
        with self.assertRaises(ValueError):m.analyze(*self.args)
    def test_wrong_pad(self):
        self.args[0]['geometry']['pads_mm']['1']=[0,0]
        with self.assertRaises(ValueError):m.analyze(*self.args)
    def test_missing_function(self):
        self.args[0]['networks']['RN7101']['replaces'].pop()
        with self.assertRaises(ValueError):m.analyze(*self.args)

if __name__=='__main__':unittest.main()
