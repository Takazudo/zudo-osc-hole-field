import copy, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'circuit/routing/issue189/core-outer'
spec=importlib.util.spec_from_file_location('outer_core',HERE/'prepare.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class OuterRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((HERE/'plan.json').read_text())
        self.source=json.loads((ROOT/self.plan['source_replay']).read_text())
    def test_complete_selected_transactions_and_original_copper_retained(self):
        actual=module.build(self.plan,self.source)
        self.assertEqual(actual['removed'],[])
        self.assertEqual(actual['added'],[r for r in self.source['added'] if r['net'] in self.plan['selected_nets']])
        self.assertEqual(len(actual['nets']),63)
        self.assertEqual(len(actual['added']),333)
    def test_inner_layer_via_removal_and_stale_base_reject(self):
        selected=self.plan['selected_nets'][0]
        for mode in ('inner','via','remove','stale'):
            with self.subTest(mode=mode):
                source=copy.deepcopy(self.source)
                row=next(r for r in source['added'] if r['net']==selected)
                if mode=='inner':row['layer']='In3.Cu'
                if mode=='via':row['block']='(via (at 0 0))'
                if mode=='remove':source['removed'].append({'net':selected,'uuid':'existing'})
                if mode=='stale':source['base_sha256']='changed'
                with self.assertRaises(ValueError):module.build(self.plan,source)
if __name__=='__main__':unittest.main()
