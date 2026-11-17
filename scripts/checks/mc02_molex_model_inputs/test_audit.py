import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('audit', Path(__file__).with_name('audit.py'))
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)

class Tests(unittest.TestCase):
    def inputs(self):
        return {'ds62': {'pitch':'pitch_0_5'}, 'cable': {'pitch_0_5': {'conductor_thickness_mm':.035},
          'eps_eff': {'value':[1.,2.1,3.2]}, 'end_equivalent_mm':{'value':5}},
          'conductor_resistance_mohm':{'pitch_0_5':{'min':65.3,'max':106.4}}, 'contact':{}}
    def test_no_assumption_no_factor(self):
        self.assertIsNone(a.conditional_factor(a.FACTS))
    def test_conditional_exact_factors(self):
        result=a.conditional_factor(a.FACTS,'0.10')
        self.assertEqual(result['exact_rational_interval'],['49000/33','53000/27'])
        self.assertEqual(result['unit'],'1/mm')
    def test_undeclared_assumption_rejected(self):
        for t in ('0.035','0','NaN',float('nan')):
            with self.assertRaises(ValueError):a.conditional_factor(a.FACTS,t)
    def test_nominal_cannot_be_interval(self):
        f=copy.deepcopy(a.FACTS);f['copper_interval_mm']=['0.10','0.10']
        with self.assertRaises(ValueError):a.contract(f,self.inputs())
    def test_unknowns_cannot_be_invented(self):
        for key,value in [('rho_ohm_m_of_T','1.724e-8'),('effective_dielectric',3.2),('end_equivalent_mm',5),('width_mm',['NaN','0.33']),('mpn','150200076')]:
            f=copy.deepcopy(a.FACTS);f[key]=value
            with self.assertRaises(ValueError):a.contract(f,self.inputs())
    def test_no_product_bounds(self):
        r=a.contract(a.FACTS,self.inputs())
        self.assertIsNone(r['guaranteed_electrical_bounds']);self.assertFalse(r['product_qualified'])
        self.assertIsNone(r['resistance']['guaranteed_product_interval_ohm'])
    def test_runtime_qualification_guard(self):
        for key,value in [('product_qualified',True),('guaranteed_electrical_bounds',[0,1])]:
            r=a.contract(a.FACTS,self.inputs());r[key]=value
            with self.assertRaises(ValueError):a.validate_output(r)
    def test_runtime_resistance_guard(self):
        r=a.contract(a.FACTS,self.inputs());r['resistance']['guaranteed_product_interval_ohm']=[0,1]
        with self.assertRaises(ValueError):a.validate_output(r)
    def test_geometry_not_resistance_substitution(self):
        i=self.inputs();i['cable']['pitch_0_5']['conductor_thickness_mm']=.10
        with self.assertRaises(ValueError):a.contract(a.FACTS,i)
    def test_resistance_source_change_rejected(self):
        i=self.inputs();i['conductor_resistance_mohm']['pitch_0_5']['max']=50
        with self.assertRaises(ValueError):a.contract(a.FACTS,i)
    def test_source_drift_fails_before_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/a.PDF;p.parent.mkdir(parents=True);p.write_bytes(b'drift')
            with self.assertRaisesRegex(ValueError,'source drift'):a.audit(root)

if __name__=='__main__':unittest.main()
