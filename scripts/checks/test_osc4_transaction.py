#!/usr/bin/env python3
"""Unit tests for circuit/reviews/osc4-local-transactions-20261107/transaction.py with the native driver stubbed (no KiCad, numpy or scipy)."""
from __future__ import annotations
import hashlib,importlib.util,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
DRIVER=ROOT/'circuit/reviews/osc4-local-transactions-20261107/transaction.py'
spec=importlib.util.spec_from_file_location('osc4_transaction',DRIVER)
tx=importlib.util.module_from_spec(spec);spec.loader.exec_module(tx)


class StubDriver:
    class StageRejected(RuntimeError):pass

    def __init__(self,tmp,interrupt):self.tmp=Path(tmp);self.interrupt=interrupt

    def workspace(self,board_id,name):
        d=self.tmp/name;d.mkdir(parents=True,exist_ok=True);return d

    def check(self,board):
        if self.interrupt:raise KeyboardInterrupt
        raise AssertionError('not reached')


def plan_for(board,sha):
    return {'input_board':str(board),'input_board_sha256':sha,
            'transaction':{'spec':{'name':'osc4-test','repair_targets':['AGND']}}}


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.dir=Path(self.tmp.name)
        self.board=self.dir/'board.kicad_pcb';self.board.write_text('(kicad_pcb)\n')
        self.sha=hashlib.sha256(self.board.read_bytes()).hexdigest()

    def tearDown(self):self.tmp.cleanup()

    def test_refuses_changed_board_before_any_driver_call(self):
        driver=mock.Mock()
        with mock.patch.object(tx,'load',return_value=plan_for(self.board,'0'*64)):
            with self.assertRaisesRegex(SystemExit,'accepted board changed'):
                tx.run('osc-core',driver=driver,delta=mock.Mock(),retention=mock.Mock(),out_dir=self.dir,cid_dir=self.dir/'cids')
        driver.assert_not_called();self.assertFalse((self.dir/'osc4-test.json').exists())

    def test_invalid_plan_gates_the_native_run(self):
        driver=mock.Mock()
        with mock.patch.object(tx,'load',return_value=plan_for(self.board,self.sha)), \
             mock.patch.object(tx,'validate',return_value={'errors':['no target pad in the frame']}):
            with self.assertRaisesRegex(SystemExit,'plan invalid'):
                tx.run('osc-core',driver=driver,delta=mock.Mock(),retention=mock.Mock(),out_dir=self.dir,cid_dir=self.dir/'cids')
        driver.assert_not_called()

    def test_interrupt_is_recorded_not_left_running(self):
        driver=StubDriver(self.dir/'ws',interrupt=True)
        with mock.patch.object(tx,'load',return_value=plan_for(self.board,self.sha)), \
             mock.patch.object(tx,'validate',return_value={'errors':[]}):
            with self.assertRaises(KeyboardInterrupt):
                tx.run('osc-core',driver=driver,delta=mock.Mock(),retention=mock.Mock(),out_dir=self.dir,cid_dir=self.dir/'cids')
        receipt=json.loads((self.dir/'osc4-test.json').read_text())
        self.assertEqual(receipt['status'],'INTERRUPTED; NOT ADOPTED')
        self.assertIn('KeyboardInterrupt',receipt['error'])
        self.assertFalse(receipt['adopted']);self.assertFalse(receipt['raw_gate_passed'])


if __name__=='__main__':unittest.main()


WORKFLOW=ROOT/'.github/workflows/local-transactions.yml'
BUDGETS=ROOT/'circuit/reviews/osc4-local-transactions-20261107/budgets.json'


def workflow_env(name):
    m=re.search(r'^  %s: "(\d+)"$'%name,WORKFLOW.read_text(),re.M);assert m,name;return int(m.group(1))


class BudgetInvariantTests(unittest.TestCase):
    def setUp(self):self.text=WORKFLOW.read_text();self.budgets=json.loads(BUDGETS.read_text())

    def test_every_board_fits_the_job(self):
        job=workflow_env('JOB_TIMEOUT_MINUTES')
        overhead=sum(workflow_env(n) for n in ('WRAPPER_GRACE_MINUTES','KILL_AFTER_MINUTES','SETUP_ALLOWANCE_MINUTES','COLLECT_ALLOWANCE_MINUTES'))
        step=int(re.search(r'id: run\n\s+# .*\n\s+# .*\n\s+timeout-minutes: (\d+)',self.text).group(1))
        for board,minutes in self.budgets['minutes'].items():
            self.assertLessEqual(minutes+overhead,job,board);self.assertLessEqual(minutes+5,step,board);self.assertLessEqual(step,job-20,board)
        self.assertEqual(self.budgets['minutes']['osc-core'],140);self.assertEqual(self.budgets['minutes']['osc-jack-left'],60);self.assertEqual(self.budgets['minutes']['osc-jack-right'],60)

    def test_job_timeout_matches_and_stays_under_the_campaign_ceiling(self):
        job=workflow_env('JOB_TIMEOUT_MINUTES')
        m=re.search(r'^  transaction:\n(?:.*\n)*?    timeout-minutes: (\d+)$',self.text,re.M)
        self.assertEqual(int(m.group(1)),job);self.assertLessEqual(job,330)

    def test_input_range_matches_largest_budget(self):
        self.assertIn('1-%d'%max(self.budgets['minutes'].values()),self.text)


class HoldTests(unittest.TestCase):
    TX=DRIVER

    def run_tx(self,*args):return subprocess.run([sys.executable,str(self.TX),*args],cwd=ROOT,capture_output=True,text=True)

    def test_osc_core_is_held_and_names_the_release_condition(self):
        held=json.loads(BUDGETS.read_text())['holds']
        self.assertEqual(set(held),{'osc-core'});self.assertIn('K2226 adoption decision (#311)',held['osc-core'])

    def test_held_board_refused_with_zero_native_calls(self):
        driver=mock.Mock()
        with mock.patch.object(tx,'run') as run,mock.patch.object(tx,'load') as load,mock.patch.object(tx.lifecycle,'install') as install:
            code=tx.main(['osc-core'])
        self.assertEqual(code,4);run.assert_not_called();install.assert_not_called();driver.assert_not_called()

    def test_held_board_cli_message_and_validate_budget_unaffected(self):
        r=self.run_tx('osc-core');self.assertEqual(r.returncode,4);self.assertIn('NOT ADMITTED',r.stderr);self.assertEqual(r.stdout,'')
        self.assertEqual(self.run_tx('osc-core','--print-budget').stdout.strip(),'140')
        self.assertEqual(self.run_tx('osc-core','--validate').returncode in (0,1),True)

    def test_unheld_board_is_not_refused_by_the_hold(self):
        self.assertIsNone(tx.held_reason('osc-jack-left'))

    def test_prepare_checks_holds_before_writing_the_matrix(self):
        text=WORKFLOW.read_text()
        self.assertIn("'.holds[$b] // empty'",text);self.assertLess(text.index(".holds[$b]"),text.index('echo "matrix='))
        self.assertLess(text.index(".holds[$b]"),text.index('eff=$MAX_MINUTES'))
