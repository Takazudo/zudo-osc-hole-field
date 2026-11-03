"""Mutation tests for coverage and interface polarity, not circuit qualification."""
import copy
import unittest
from scripts.architecture278.extract import build, validate

class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=build()
    def test_complete_source(self):validate(self.data)
    def reject(self,mutate,message):
        data=copy.deepcopy(self.data);mutate(data)
        with self.assertRaisesRegex(AssertionError,message):validate(data)
    def test_missing_endpoint(self):self.reject(lambda d:d['nets'][0]['endpoints'].pop(),'endpoint coverage')
    def test_net_swap_rejected(self):
        def mutate(d):
            a,b=d['nets'][:2]
            a['net'],b['net']=b['net'],a['net']
        self.reject(mutate,'endpoint net drift')
    def test_owner_summary_rejected(self):
        self.reject(lambda d:d['nets'][0]['owners'].append('invented'),'owner summary')
    def test_endpoint_owner_rejected(self):
        def mutate(d):
            n=d['nets'][0]
            for e in n['endpoints']:e['owner']='invented'
            n['owners']=['invented']
        self.reject(mutate,'endpoint owner drift')
    def test_new_shared_reference_boundary(self):
        for net in ('OSC_REF5','OSC_REFN5','OSC_GATE_REF'):
            n=next(n for n in self.data['nets'] if n['net']==net)
            self.assertEqual(n['classification'],'shared reference')
            self.assertEqual(n['owners'],['rear-core','shared-reference'])
        self.reject(lambda d:next(n for n in d['nets'] if n['net']=='OSC_REF5').update(classification='source-local'),'service classification')
    def test_duplicate_unit(self):self.reject(lambda d:d['parts'].append(d['parts'][0]),'duplicate package')
    def test_missing_pin_including_nc(self):self.reject(lambda d:d['parts'][0]['pins'].pop(next(iter(d['parts'][0]['pins']))),'endpoint coverage|symbol pin')
    def test_split_package(self):
        def mutate(d):
            pack=next(p for p in d['packages'] if len(p['units'])>1)
            next(p for p in d['parts'] if p['ref']==pack['ref'])['proposed_owner']='wrong-front'
        self.reject(mutate,'split package')
    def test_wrong_connector_polarity(self):self.reject(lambda d:d['harnesses'][0]['faces'][1]['pin_map'].update({'1':'AGND'}),'polarity mismatch')
    def test_forbidden_crossing(self):self.reject(lambda d:next(n for n in d['nets'] if n['restriction']=='local-only')['owners'].append('middle'),'sensitive crossing|owner summary')
    def test_wipers_are_not_buffered(self):
        pots=[c for c in self.data['controls'] if c['wiper_pin']]
        self.assertEqual(len(pots),5)
        self.assertTrue(all(not c['buffer_assumed'] for c in pots))
    def test_polarity_and_replication(self):
        for row in self.data['instance_mapping']:
            for pin,net in row['pins']['O1'].items():
                for name in ('O2','O5'):
                    self.assertEqual(row['pins'][name][pin],net.replace('/O1/',f'/{name}/') if net else None)
if __name__=='__main__':unittest.main()
