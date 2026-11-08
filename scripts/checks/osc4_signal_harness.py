#!/usr/bin/env python3
"""Child process for test_osc4_transaction_signals.py: transaction.main() with a stub native driver.

The stub's native calls go through the real control path, lifecycle.owned_run (installed by
transaction.run()), to osc4_fake_oracle.sh or, with --docker, to scripts/kicad/run.sh. KiCad,
numpy and scipy are never imported. The plan and the host-side validation are patched so the
run works on a one-line fake board in a temporary directory.
"""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
TX=ROOT/'circuit/reviews/osc4-local-transactions-20261107/transaction.py'
spec=importlib.util.spec_from_file_location('osc4_transaction',TX);tx=importlib.util.module_from_spec(spec);spec.loader.exec_module(tx)
ORACLE=HERE/'osc4_fake_oracle.sh'
BEFORE={'open_edges':10,'islands':{'AGND':[['a'],['b']]},'pads':[]}
AFTER={'open_edges':9,'islands':{'AGND':[['a','b']]},'pads':[]}


class StubDriver:
    """Mirrors route_jack_grid's RUNNER hook: transaction.run() installs lifecycle.owned_run there."""
    class StageRejected(RuntimeError):pass
    RUNNER=None

    def __init__(self,tmp,mode,seconds,pidfile,reject=False,gate=False,docker=False):
        self.tmp=Path(tmp);self.mode=mode;self.seconds=seconds;self.pidfile=pidfile
        self.reject=reject;self.gate=gate;self.docker=docker;self.after=None

    def run(self,*args):
        if self.RUNNER is None:raise AssertionError('transaction.run() did not install lifecycle.owned_run on the RUNNER hook')
        return self.RUNNER(*args)

    def workspace(self,board_id,name):
        d=self.tmp/name
        if d.exists():shutil.rmtree(d)
        d.mkdir(parents=True);return d

    def oracle(self,mode,seconds):
        if self.docker:return self.run('bash','scripts/kicad/run.sh','sleep',str(seconds))
        return self.run('bash',str(ORACLE),mode,str(seconds),str(self.pidfile))

    def check(self,board):
        self.oracle(self.mode,self.seconds)
        dump=self.after or BEFORE
        Path(board).with_name('dump.json').write_text(json.dumps(dump))
        return {'violations':[],'schematic_parity':False},dump

    def run_stage(self,board_id,current,spec,definition,log):
        if self.reject:
            return None,{'stage':spec['name'],'status':'REJECTED: stub','rejected':True,'open_edges_before':10,'open_edges_after':10}
        self.after=AFTER
        candidate=self.workspace(board_id,spec['name']+'-cand')/Path(current).name;shutil.copyfile(current,candidate)
        candidate.with_name('dump.json').write_text(json.dumps(AFTER))
        self.oracle('quick',0)  # the stage's own native calls (apply, candidate and verify checks)
        return candidate,{'stage':spec['name'],'status':'NATIVE CHECKED DRAFT STAGE','open_edges_before':10,'open_edges_after':9,'open_by_net_after':{'AGND':0}}

    def split_pad_groups(self,before,after):return []

    def stitched(self,*args):raise AssertionError('not reached by the stub flow')

    def connectivity_signature(self,dump):return dump['open_edges'],json.dumps(dump['islands'],sort_keys=True)

    def promotion_gate(self,before,after,before_drc,after_drc):
        return {'adopted':self.gate,'native_errors':False,'new_warning_identities':[],'split_pad_groups':[]}


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--tmp',required=True);p.add_argument('--pidfile',required=True)
    p.add_argument('--mode',default='quick');p.add_argument('--seconds',default='60')
    p.add_argument('--reject',action='store_true');p.add_argument('--gate',action='store_true');p.add_argument('--docker',action='store_true')
    p.add_argument('--then-sleep-run',action='store_true',help='after a completed quick run, start a second run (sleep oracle) into out2/ in the same interpreter')
    p.add_argument('--slow-validate',type=float,default=0,help='seconds the patched validate() sleeps (a signal during preflight)')
    p.add_argument('driver_args',nargs=argparse.REMAINDER,help='arguments for transaction.py after the board')
    a=p.parse_args()
    tmp=Path(a.tmp);tmp.mkdir(parents=True,exist_ok=True);out=tmp/'out';out.mkdir(exist_ok=True)
    board=tmp/'board.kicad_pcb';board.write_text('(kicad_pcb)\n')
    plan={'input_board':str(board),'input_board_sha256':hashlib.sha256(board.read_bytes()).hexdigest(),
          'transaction':{'spec':{'name':'osc4-test','repair_targets':['AGND']}}}
    driver=StubDriver(tmp/'ws',a.mode,a.seconds,a.pidfile,reject=a.reject,gate=a.gate,docker=a.docker)
    args=[x for x in a.driver_args if x!='--']
    import time
    def validate(board_id):
        if a.slow_validate:
            Path(a.pidfile).parent.joinpath('validating').write_text('1');time.sleep(a.slow_validate)
        return {'errors':[]}
    with mock.patch.object(tx,'load',return_value=plan),mock.patch.object(tx,'validate',validate):
        code=tx.main(['osc-core',*args,'--out-dir',str(out),'--cid-dir',str(tmp/'cids')],
                     driver=driver,delta=lambda a_,b_:{'stub':True},retention=lambda b_,a_:{'stub':True})
        if code or not a.then_sleep_run:return code
        out2=tmp/'out2';out2.mkdir(exist_ok=True);second=StubDriver(tmp/'ws2','sleep',a.seconds,a.pidfile)
        return tx.main(['osc-core',*args,'--out-dir',str(out2),'--cid-dir',str(tmp/'cids2')],
                       driver=second,delta=lambda a_,b_:{'stub':True},retention=lambda b_,a_:{'stub':True})


if __name__=='__main__':sys.exit(main())
