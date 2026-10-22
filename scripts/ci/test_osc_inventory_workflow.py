import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

class WiringTests(unittest.TestCase):
    def workflow(self):
        return json.loads((Path(__file__).resolve().parents[2]/'.github/workflows/osc-candidate-check.yml').read_text())
    def test_modes_and_command_arguments(self):
        w=self.workflow();mode=w['on']['workflow_dispatch']['inputs']['mode']
        self.assertEqual(mode['default'],'smoke');self.assertEqual(mode['options'],['smoke','identity','topology','fill','synthetic'])
        self.assertEqual(mode['type'],'choice')
        j=next(iter(w['jobs'].values()));self.assertEqual(j['env']['OSC_MODE'],'${{ inputs.mode }}')
        steps=j['steps'];command=steps[4]['run']
        self.assertIn('case "$OSC_MODE" in',command)
        self.assertIn('smoke) python3 -B tooling/scripts/ci/osc_candidate_check.py --source frozen --out receipts ;;',command)
        self.assertIn('identity) python3 -B tooling/scripts/ci/osc_inventory_check.py frozen inventory-receipts ;;',command)
        self.assertIn('exit 2',command);self.assertNotIn('${{',command)
        self.assertIn("inputs.mode == 'identity'",steps[2]['with']['sparse-checkout'])
        self.assertIn('test_osc*.py',steps[3]['run'])
        self.assertEqual(w['on']['workflow_dispatch']['inputs']['source_tests_only']['default'],False)
        self.assertEqual(w['on']['workflow_dispatch']['inputs']['source_tests_only']['type'],'boolean')
        self.assertEqual(steps[2]['if'],'${{ !inputs.source_tests_only }}')
        self.assertEqual(steps[4]['if'],'${{ !inputs.source_tests_only }}')
        self.assertIn('/scripts/ci/test_osc_mismatch.py',steps[1]['with']['sparse-checkout'].splitlines())
        # Exercise the actual embedded source-only runner with no subprocess/native execution.
        code=steps[3]['run'].split('\n',1)[1].rsplit('\nPY',1)[0]
        import osc_candidate_check as c
        old=Path.cwd()
        with tempfile.TemporaryDirectory() as folder:
            try:
                os.chdir(folder);Path('receipts').mkdir();Path('tooling/scripts/ci').mkdir(parents=True)
                Path('tooling/.github/workflows').mkdir(parents=True)
                Path('tooling/.github/workflows/osc-candidate-check.yml').write_text('{}')
                with patch.dict(os.environ,{'SOURCE_TESTS_ONLY':'true','TOOLING_SHA':'a'*40}), patch.object(c,'run_command',return_value={'output':'mock suite','failure':None,'exit_code':0}) as runner:
                    exec(compile(code,'pure-tests','exec'),{})
                receipt=json.loads(Path('receipts/receipt.json').read_text())
                self.assertEqual(receipt['status'],'SOURCE_TESTS_ONLY_PASSED')
                self.assertIs(receipt['native_executed'],False)
                self.assertIs(receipt['source_checkout_executed'],False)
                self.assertEqual(runner.call_count,2)
                for call in runner.call_args_list:
                    self.assertEqual(call.args[0][0],'python3')
                    self.assertIn('unittest',call.args[0])
            finally:os.chdir(old)
        self.assertEqual(sum(10 if x['timeout-minutes']=="${{ inputs.mode == 'synthetic' && 2 || 10 }}" else x['timeout-minutes'] for x in steps),18)
    def stage(self,mode,inventory=False,extra=False):
        script=next(iter(self.workflow()['jobs'].values()))['steps'][-2]['run'].split('\n',1)[1].rsplit('\nPY',1)[0]
        with tempfile.TemporaryDirectory() as t:
            prev=Path.cwd()
            try:
                os.chdir(t);Path('receipts').mkdir()
                Path('receipts/receipt.json').write_text('{"status":"SETUP_INCOMPLETE"}')
                Path('receipts/tests.json').write_text('[]')
                if inventory:
                    Path('inventory-receipts').mkdir();Path('inventory-receipts/receipt.json').write_text('{"status":"IDENTITY_ONLY"}')
                    Path('inventory-receipts/inventory.json').write_text('{}')
                    if extra:Path('inventory-receipts/board.kicad_pcb').write_text('forbidden')
                with patch.dict(os.environ,{'OSC_MODE':mode}):
                    if mode not in ('smoke','identity') or extra or (inventory and mode=='smoke'):
                        with self.assertRaises(SystemExit):exec(compile(script,'artifact-stage','exec'),{})
                        self.assertEqual(json.loads(Path('upload-safe/receipt.json').read_text())['status'],'ARTIFACT_POLICY_FAILURE')
                        self.assertEqual(len(list(Path('upload-safe').iterdir())),1)
                    else:
                        exec(compile(script,'artifact-stage','exec'),{})
                        expected={'receipt.json','tests.json'}|({'inventory.json'} if inventory else set())
                        self.assertEqual({p.name for p in Path('upload-safe').iterdir()},expected)
                        self.assertEqual(json.loads(Path('upload-safe/receipt.json').read_text())['status'],'IDENTITY_ONLY' if inventory else 'SETUP_INCOMPLETE')
            finally:os.chdir(prev)
    def test_smoke_artifacts(self):self.stage('smoke')
    def test_identity_artifacts(self):self.stage('identity',True)
    def test_setup_failure_receipt(self):self.stage('identity')
    def test_reject_board_artifact(self):self.stage('identity',True,True)
    def test_reject_inventory_in_smoke(self):self.stage('smoke',True)
    def test_reject_invalid_mode(self):self.stage('arbitrary')

if __name__=='__main__':unittest.main()
