import copy
import math
import unittest
import stage27_hf_trim as s

class HFTrimTests(unittest.TestCase):
    def setUp(self):
        self.c=s.read(s.OUT/'candidate.json');self.e=s.read(s.OUT/'evidence.json');self.n=s.read(s.ROOT/s.REL/'candidate-netlist.json')
    def test_exact_candidate(self):s.validate(self.c,self.e)
    def test_wrong_identity_rating_or_promise(self):
        for key,value in [('mpn','TC33X-2-103E'),('mpn','TC33X-1-203E'),('supplier_code','C000'),('resistance_ohm',10000),
            ('tolerance_fraction',.1),('primary_power_W_at_70C',.1),('catalog_power_W',.15),('new_controls',1),
            ('frequency_coverage_Hz',[20,20000]),('tracking_acceptance',True),('order_ready',True),('physical_coverage','PASS')]:
            c=copy.deepcopy(self.c);c[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):s.validate(c,self.e)
    def test_supplier_confusion(self):
        for key,value in [('componentModelEn','TC33X-2-103E'),('componentCode','C0'),('componentBrandEn','OTHER'),('assemblyMode','hand'),('stock_is_allocated',True),('visible_services',{})]:
            e=copy.deepcopy(self.e);e['supplier_observation'][key]=value
            with self.assertRaises(ValueError):s.validate(self.c,e)
    def test_source_authority_loss(self):
        for key in ('manufacturer','supplier'):
            for field,value in [('url','https://example.com'),('availability','SOURCE UNAVAILABLE'),('sha256','0'*64),('retrieved_UTC',''),('retrieved_UTC','2026-10-17Tgarbage'),('retrieved_UTC','2026-10-17T00:00:00'),('sha256','z'*64)]:
                e=copy.deepcopy(self.e);e[key][field]=value
                with self.assertRaises(ValueError):s.validate(self.c,e)
    def test_core_identity_bound(self):
        for field in self.e['core_primary']:
            e=copy.deepcopy(self.e);e['core_primary'][field]='substitute'
            with self.assertRaises(ValueError):s.validate(self.c,e)
    def test_materialize_complete(self):
        after=s.materialize(self.n,self.c);s.validate_delta(self.n,after,self.c)
        self.assertEqual(len(after['packages']),250)
    def test_every_package_pin_and_metadata_preserved(self):
        after=s.materialize(self.n,self.c)
        for i,p in enumerate(after['packages']):
            for field in p:
                broken=copy.deepcopy(after);broken['packages'][i][field]=None
                with self.subTest(ref=p['ref'],field=field),self.assertRaises(ValueError):s.validate_delta(self.n,broken,self.c)
    def test_nc_short_missing_unit_and_extra_control(self):
        after=s.materialize(self.n,self.c)
        cases=[(i,pin) for i,p in enumerate(after['packages']) for pin,net in p['pins'].items() if net is None]
        self.assertTrue(cases)
        for i,pin in cases:
            x=copy.deepcopy(after);x['packages'][i]['pins'][pin]='AGND'
            with self.assertRaises(ValueError):s.validate_delta(self.n,x,self.c)
        for action in ('omit','extra','unit'):
            x=copy.deepcopy(after)
            if action=='omit':x['packages'].pop()
            elif action=='extra':x['packages'].append(x['packages'][0])
            else:x['packages'][0]['units']=[]
            with self.assertRaises(ValueError):s.validate_delta(self.n,x,self.c)
    def test_source_topology(self):self.assertEqual(s.source_values()['HF_TRIM'],['20 kΩ','HF_PIN','LINEAR_REF','AGND'])
    def test_loaded_kcl_and_segment_power(self):
        result=s.network(20000,.5,1,0)
        self.assertAlmostEqual(result['core13_current_A'],110e-6)
        self.assertAlmostEqual(result['track_segment_power_W'],.0001)
        # Equal endpoint potentials can still dissipate power from wiper injection.
        injected=s.network(20000,.5,0,1)
        self.assertAlmostEqual(injected['track_segment_power_W'],.0002)
        self.assertNotEqual(injected['track_segment_power_W'],0)
    def test_nonideal_unknown_operating_point_not_invented(self):
        self.assertNotEqual(s.network(20000,.5,1,0)['core13_current_A'],s.network(20000,.5,1,.5)['core13_current_A'])
        for args in [(20000,0,1,0),(20000,1,1,0),(10000,.5,1,0),(20000,.5,float('nan'),0)]:
            with self.assertRaises(ValueError):s.network(*args)
    def test_hf_pin_swap(self):
        n=copy.deepcopy(self.n);p=next(p for p in n['packages'] if p['ref']=='RVO1109');p['pins']['1'],p['pins']['3']=p['pins']['3'],p['pins']['1']
        with self.assertRaises(ValueError):s.materialize(n,self.c)

if __name__=='__main__':unittest.main()
