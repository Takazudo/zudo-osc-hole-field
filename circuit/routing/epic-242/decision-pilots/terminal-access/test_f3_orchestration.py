"""Source-only launch/receipt regressions; subprocess execution is mocked."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run_f3_k1402 as r

PACKET = r.read(r.HERE/'f3-packet/request.json')


def proposal():
    targets=PACKET['demand_and_preservation_contract']['targets']
    return {'accepted':False,'adopted':False,'coupled_connectivity_success':False,'removed_uuids':[],
            'copper':[],'demands':[{'kind':k,'net':targets[k]['net_token'],
            'anchors':[p['uuid'] for p in targets[k]['anchor_records']], 'accepted':False,
            'native_exact_pair_closed':False, 'status':'NO_VALID_SAVED_ACCESS', 'portal_counts':[0,3]}
            for k in PACKET['route_policy']['target_order']]}


class F3OrchestrationTests(unittest.TestCase):
    def test_exact_packet_argv_only_replaces_four_identity_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            argv=r.route_argv(PACKET,{'worker':'new-worker'},Path(tmp),'/actual/python')
            replacements={'{ACTUAL_EXECUTION_PYTHON}':'/actual/python','{NEW_PARENT_CASE_ADMISSION_ID}':r.ADMISSION,
              '{UNIQUE_CASE_WORKER}':'new-worker','{NEW_CASE_GUARD_JSON_FILE}':tmp+'/native-guard.json'}
            self.assertEqual(argv,[replacements.get(v,v) for v in PACKET['cases']['K1402']['route_argv']])
            self.assertEqual(argv[argv.index('--seconds')+1],'300')
            self.assertEqual(argv[argv.index('--board')+1],'K1402')
            Path(tmp,'native-guard.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'no retry'):r.route_argv(PACKET,{'worker':'new'},Path(tmp),'/python')

    def test_rerun_rejected_before_source_or_native_calls(self):
        env={'PARENT_ADMISSION_ID':r.ADMISSION,'GITHUB_REPOSITORY':r.REPOSITORY,'GITHUB_REF_NAME':r.BRANCH,
             'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted','GITHUB_RUN_ID':'42','GITHUB_RUN_ATTEMPT':'2'}
        with patch.dict(os.environ,env,clear=True),patch.object(r,'command',side_effect=AssertionError('no commands')):
            with self.assertRaisesRegex(ValueError,'first attempt'):r.identity()

    def test_recreated_branch_rejected_from_complete_run_history(self):
        ident={'run_id':'42','orchestration_sha':'f'*40}
        current={'id':42,'head_sha':'f'*40,'path':'.github/workflows/'+r.WORKFLOW}
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'request',return_value=(PACKET,ident)):
            for runs in ({'total_count':2,'workflow_runs':[current,{**current,'id':41}]},
                         {'total_count':101,'workflow_runs':[current]}):
                with patch.object(r,'command',return_value=json.dumps(runs)):
                    with self.assertRaises(ValueError):r.initialize(Path('/method'),Path(tmp))
            self.assertFalse(Path(tmp,'one-shot.json').exists())

    def test_missing_outputs_explicitly_not_produced(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=r.inventory(Path(tmp),Path(tmp))
            self.assertTrue(all(v=={'status':'NOT PRODUCED'} for v in result.values()))

    def test_unchanged_demand_contract_rejects_credit_substitution_and_rail_erasure(self):
        r.proposal_contract(proposal(),PACKET)
        for mutate in (lambda p:p.update(accepted=True), lambda p:p['demands'].pop(0),
                       lambda p:p['demands'][0].update(status='UNCHECKED_COMPLETE_PAIR_PROPOSAL'),
                       lambda p:p['demands'][3].update(anchors=['other','pads']),
                       lambda p:p['demands'][2].update(native_exact_pair_closed=True)):
            p=proposal();mutate(p)
            with self.assertRaises(ValueError):r.proposal_contract(p,PACKET)

    def test_failure_before_guard_retains_error_and_does_not_launch(self):
        with tempfile.TemporaryDirectory() as tmp,patch.object(r,'request',side_effect=ValueError('wrong host')),patch.object(r.subprocess,'run',side_effect=AssertionError('native forbidden')):
            self.assertEqual(r.execute(Path(tmp),Path(tmp),Path(tmp)),1)
            receipt=r.read(Path(tmp,'route.json'))
            self.assertFalse(receipt['guard_invoked']);self.assertIn('wrong host',receipt['error'])

    def test_source_hash_drift_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'source').write_text('changed')
            packet={'source_commit':r.METHOD,'input_file_sha256':{'source':'0'*64},'orchestration_control_sha256':{}}
            with patch.object(r,'command',side_effect=[r.METHOD,'']):
                with self.assertRaisesRegex(ValueError,'hash mismatch'):r.verify_sources(p,packet)

    def test_workflow_has_only_one_shot_branch_and_failure_retention(self):
        import yaml
        workflow=yaml.safe_load((r.REQUEST_ROOT/'.github/workflows'/r.WORKFLOW).read_text())
        trigger=workflow.get('on',workflow.get(True))
        self.assertEqual(trigger,{'push':{'branches':[r.BRANCH]}})
        job=workflow['jobs']['route'];self.assertEqual(job['timeout-minutes'],43)
        self.assertEqual(job['if'],'github.event.created && github.run_attempt == 1')
        self.assertNotIn('strategy',job)
        retention=[s for s in job['steps'] if s.get('if')=='always()']
        self.assertEqual(len(retention),2)
        self.assertEqual(retention[-1]['with']['retention-days'],30)
        self.assertIn('finalize',retention[0]['run'])


# Reuse previous source receipt boundary regressions with this frozen binding.
# This invokes no qualification fixtures or native calls.
import sys
sys.path.insert(0,str(r.HERE.parent))
import test_route_1420 as prior_tests

class F3ReceiptTests(prior_tests.Route1420Tests):
    def setUp(self):
        import test_route_1420
        self.patcher=patch.object(test_route_1420,'run',r)
        self.patcher.start()
        # Prior test reads run.host.METHOD; a test-only namespace preserves it.
        from types import SimpleNamespace
        self.host=patch.object(r,'host',SimpleNamespace(METHOD=r.METHOD),create=True);self.host.start()
    def tearDown(self):self.host.stop();self.patcher.stop()
    def test_workflow_rerun_rejected_before_any_source_or_native_call(self):
        # Current identity() has the same early attempt gate, tested above.
        F3OrchestrationTests().test_rerun_rejected_before_source_or_native_calls()


if __name__=='__main__':unittest.main()
