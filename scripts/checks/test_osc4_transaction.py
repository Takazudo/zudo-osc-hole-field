#!/usr/bin/env python3
"""Unit tests for circuit/reviews/osc4-local-transactions-20261107/transaction.py with the native driver stubbed (no KiCad, numpy or scipy)."""
from __future__ import annotations
import hashlib,importlib.util,json,tempfile,unittest
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
