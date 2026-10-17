import copy
import json
import unittest
import stage9_comparison as c
class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope=json.loads((c.OUT/'scope.json').read_text());cls.baseline=json.loads((c.OUT.parent/'stage8/mechanical-report.json').read_text())['placements']
    def test_conservation(self):
        self.assertEqual(c.preserve(self.scope,self.baseline,self.baseline)['whole_source_packages'],56)
    def test_lost_or_split_package(self):
        p=copy.deepcopy(self.baseline);p.pop('U3305')
        with self.assertRaisesRegex(ValueError,'inventory'):c.preserve(self.scope,self.baseline,p)
        p=copy.deepcopy(self.baseline);p['U3305']['units'].pop()
        with self.assertRaisesRegex(ValueError,'units'):c.preserve(self.scope,self.baseline,p)
    def test_fixed_position_and_net(self):
        for ref,key,value in [('SW608','origin_mm',[0,0]),('J809','pins',{'T':'+12V'})]:
            p=copy.deepcopy(self.baseline);p[ref][key]=value
            with self.assertRaisesRegex(ValueError,'source package'):c.preserve(self.scope,self.baseline,p)
    def test_board_ownership_and_fixed_terminal_plane(self):
        p=copy.deepcopy(self.baseline);p['U3305']['board']='X1-control'
        with self.assertRaisesRegex(ValueError,'board'):c.preserve(self.scope,self.baseline,p)
        p=copy.deepcopy(self.baseline);p['J809']['pads_xyz_mm']['T'][0][2]+=1
        with self.assertRaisesRegex(ValueError,'fixed terminal plane'):c.preserve(self.scope,self.baseline,p)
    def test_stage8_mutation_receipt(self):
        s=copy.deepcopy(self.scope);p=next(iter(s['preserved_stage8_sha256']));s['preserved_stage8_sha256'][p]='0'*64
        with self.assertRaisesRegex(ValueError,'Stage8 changed'):c.preserve(s,self.baseline,self.baseline)
    def test_missing_or_stale_bindings(self):
        for r in ({},{'source_sha256':{'design/architecture-278/implementation/stage9/scope.json':'0'*64}}):
            with self.assertRaises(ValueError):c.validate_bindings(r)
if __name__=='__main__':unittest.main()
