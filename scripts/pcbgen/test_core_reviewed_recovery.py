import importlib.util,json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'circuit/routing/issue189/core-reviewed'
spec=importlib.util.spec_from_file_location('reviewed_core',HERE/'prepare.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class ReviewedCoreTests(unittest.TestCase):
    def setUp(self):
        self.plan=json.loads((HERE/'plan.json').read_text())
        self.source=json.loads((ROOT/self.plan['source_replay']).read_text())

    def test_omitted_transactions_restore_base_and_other_rows_survive_exactly(self):
        result=module.build(self.plan,self.source);omitted=set(self.plan['omit_new_nets'])
        for kind in ('added','removed'):
            actual={r['uuid']:r for r in result[kind]}
            for row in self.source[kind]:
                if row['net'] in omitted:self.assertNotIn(row['uuid'],actual)
                else:self.assertEqual(actual[row['uuid']],row)

    def test_cluster_repair_keeps_one_original_through_via_and_signal_layer_anchors(self):
        result=module.build(self.plan,self.source);cluster=self.plan['via_cluster']
        removed={r['uuid'] for r in result['removed'] if r['net']==cluster['net']}
        self.assertEqual(removed,{v['uuid'] for v in cluster['members']}-{cluster['retained_via']})
        added=[r for r in result['added'] if r['net']==cluster['net']]
        self.assertEqual(len(added),4*len(removed))
        self.assertEqual(len({r['uuid'] for r in added}),len(added))
        self.assertEqual({r['layer'] for r in added},set(cluster['layers']))
        self.assertTrue(all('(width 0.2)' in r['block'] for r in added))

    def test_wrong_base_and_changed_electrical_constraints_reject(self):
        with self.assertRaisesRegex(ValueError,'wrong base'):
            module.build({**self.plan,'base_sha256':'wrong'},self.source)
        self.plan['via_cluster']['width_nm']=150000
        with self.assertRaisesRegex(ValueError,'constraints changed'):
            module.build(self.plan,self.source)
