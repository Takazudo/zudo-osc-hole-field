#!/usr/bin/env python3
"""Receipt lifecycle and signal propagation of circuit/reviews/osc4-local-transactions-20261107/transaction.py (issue #308).

Every test starts the driver as a real process through the workflow's control path
(`timeout --signal=... --kill-after=...` + `bash scripts/pcbgen/with_route_guard.sh`), with a stub
native driver (osc4_signal_harness.py) whose native calls spawn osc4_fake_oracle.sh through
lifecycle.owned_run. The hosted-runner variables are set for the child processes only, so
with_route_guard.sh execs the command instead of queueing on the machine-wide heavy guard.
No KiCad, numpy or scipy. The one docker test is skipped unless docker and the pinned image are present.
"""
from __future__ import annotations
import importlib.util,json,os,shutil,signal,subprocess,sys,tempfile,time,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
HARNESS=HERE/'osc4_signal_harness.py';GUARD=ROOT/'scripts/pcbgen/with_route_guard.sh'
TX=ROOT/'circuit/reviews/osc4-local-transactions-20261107/transaction.py'
spec=importlib.util.spec_from_file_location('osc4_lifecycle',TX.with_name('lifecycle.py'))
lifecycle=importlib.util.module_from_spec(spec);spec.loader.exec_module(lifecycle)
CHILD_ENV={**os.environ,'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted','OSC4_GRACE_SECONDS':'1'}
INT=('timeout','--signal=INT','--kill-after=20s','3s')
INT_PRESERVE=('timeout','--signal=INT','--preserve-status','--kill-after=20s','3s')
TERM_PRESERVE=('timeout','--signal=TERM','--preserve-status','--kill-after=20s','3s')


def alive(pid):
    try:os.kill(pid,0)
    except ProcessLookupError:return False
    except PermissionError:return True
    try:return 'Z' not in Path(f'/proc/{pid}/stat').read_text().split(')')[-1].split()[0]
    except OSError:return True


def wait_until(predicate,timeout,what):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if predicate():return
        time.sleep(0.05)
    raise AssertionError(f'timed out waiting for {what}')


class Driver:
    """The driver as the workflow starts it: wrapper + with_route_guard.sh + python harness."""
    def __init__(self,tmp,*harness_args,wrapper=(),driver_args=()):
        self.tmp=Path(tmp);self.pidfile=self.tmp/'oracle.pids';self.receipt=self.tmp/'out/osc4-test.json'
        cmd=[*wrapper,'bash',str(GUARD),sys.executable,'-u',str(HARNESS),'--tmp',str(self.tmp),'--pidfile',str(self.pidfile),*harness_args,'--',*driver_args]
        self.proc=subprocess.Popen(cmd,cwd=ROOT,env=CHILD_ENV,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)

    def wait(self,timeout=60):
        self.output,_=self.proc.communicate(timeout=timeout);return self.proc.returncode

    def oracle_pids(self):
        return [int(x) for x in self.pidfile.read_text().split()] if self.pidfile.exists() else []

    def wait_for_oracle(self,count=2,timeout=10):
        wait_until(lambda:len(self.oracle_pids())>=count,timeout,f'{count} fake oracle processes');return self.oracle_pids()

    def read_receipt(self):return json.loads(self.receipt.read_text())


class LifecycleProcessTests(unittest.TestCase):
    def setUp(self):
        self._tmp=tempfile.TemporaryDirectory(prefix='osc4-lifecycle-');self.tmp=Path(self._tmp.name);self.drivers=[]

    def tearDown(self):
        for d in self.drivers:
            if d.proc.poll() is None:d.proc.kill();d.proc.wait()
            for pid in d.oracle_pids():
                if alive(pid):
                    try:os.killpg(pid,signal.SIGKILL)
                    except ProcessLookupError:pass
        self._tmp.cleanup()

    def start(self,*harness_args,wrapper=(),driver_args=()):
        d=Driver(self.tmp,*harness_args,wrapper=wrapper,driver_args=driver_args);self.drivers.append(d);return d

    def assertNoFalseResult(self,receipt):
        self.assertFalse(receipt['adopted']);self.assertEqual(receipt['schema'],lifecycle.SCHEMA)
        if receipt.get('terminal_outcome')!='COMPLETED':self.assertFalse(receipt['raw_gate_passed'])

    def assertNoOrphans(self,driver):
        pids=driver.oracle_pids();self.assertTrue(pids,'the fake oracle never started')
        wait_until(lambda:not any(alive(p) for p in pids),5,f'fake oracle processes {pids} to exit')

    def test_completion_raw_gate_failed(self):
        d=self.start('--mode','quick');rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,0,d.output);self.assertEqual(r['status'],'NATIVE CHECKED; RAW GATE FAILED; NOT ADOPTED')
        self.assertTrue(r['terminal']);self.assertEqual(r['terminal_outcome'],'COMPLETED');self.assertNoFalseResult(r)
        self.assertEqual([p['phase'] for p in r['phases']],['base_check','stage','fresh_check','final_gate'])
        self.assertTrue(all(p['ended_utc'] for p in r['phases']))
        self.assertEqual([c['returncode'] for c in r['native_calls']],[0,0,0]);self.assertIsNone(r['current_child'])
        self.assertTrue(all(c['pid']>0 and c['pgid']==c['pid'] for c in r['native_calls']))
        self.assertTrue(r['invocation']);self.assertRegex(r['source_revision'],r'^[0-9a-f]{40}$|^unknown$')
        self.assertTrue(r['environment']['hosted']);self.assertEqual(r['driver']['pid']>0,True);self.assertEqual(r['signals'],[])
        self.assertEqual(r['max_minutes'],80);self.assertIn('driver default',r['budget_source'])
        self.assertTrue((self.tmp/'out/osc4-test-copper.json').exists());self.assertNoOrphans(d)

    def test_completion_raw_gate_passed_sets_only_raw_gate_passed(self):
        d=self.start('--mode','quick','--gate',driver_args=('--max-minutes','5'));rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,0,d.output);self.assertEqual(r['status'],'NATIVE CHECKED; RAW GATE PASSED; NOT PROMOTED')
        self.assertTrue(r['raw_gate_passed']);self.assertFalse(r['adopted']);self.assertEqual(r['max_minutes'],5);self.assertEqual(r['budget_source'],'--max-minutes')

    def test_raw_rejection(self):
        d=self.start('--mode','quick','--reject');rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,0,d.output);self.assertEqual(r['status'],'REJECTED OR NOTHING TO DO; NOT ADOPTED')
        self.assertEqual(r['terminal_outcome'],'REJECTED');self.assertTrue(r['terminal']);self.assertNoFalseResult(r)
        self.assertEqual(len(r['native_calls']),1);self.assertFalse((self.tmp/'out/osc4-test-copper.json').exists())

    def test_child_failure_is_an_error(self):
        d=self.start('--mode','fail');rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,1,d.output);self.assertEqual(r['status'],'ERROR; NOT ADOPTED');self.assertEqual(r['terminal_outcome'],'ERROR')
        self.assertIn('failed (7)',r['error']);self.assertTrue(r['terminal']);self.assertEqual(r['native_calls'][0]['returncode'],7)
        self.assertEqual(r['phase'],'base_check');self.assertNoFalseResult(r);self.assertNoOrphans(d)

    def test_int_from_the_timeout_wrapper_finalises_interrupted(self):
        d=self.start('--mode','sleep','--seconds','60',wrapper=INT);d.wait_for_oracle();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,124,f'wrapper exit {rc}; receipt {r["status"]}; output:\n{d.output}')
        self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertEqual(r['terminal_outcome'],'INTERRUPTED');self.assertTrue(r['terminal'])
        self.assertEqual((r['interrupt']['signal'],r['interrupt']['name'],r['interrupt']['phase']),(2,'SIGINT','base_check'))
        self.assertEqual(r['signals'][0]['name'],'SIGINT');self.assertEqual(r['native_calls'][0]['ended_by'],'exited after signal')
        self.assertIsNotNone(r['native_calls'][0]['returncode']);self.assertIsNone(r['current_child']);self.assertIn('wall_seconds',r)
        self.assertIn('transaction stopped: SIGINT received',d.output);self.assertNoFalseResult(r);self.assertNoOrphans(d)

    def test_int_exits_130_when_the_wrapper_preserves_status(self):
        d=self.start('--mode','sleep','--seconds','60',wrapper=INT_PRESERVE);d.wait_for_oracle();rc=d.wait()
        self.assertEqual(rc,130,d.output);self.assertEqual(d.read_receipt()['status'],'INTERRUPTED; NOT ADOPTED');self.assertNoOrphans(d)

    def test_term_exits_143(self):
        d=self.start('--mode','sleep','--seconds','60',wrapper=TERM_PRESERVE);d.wait_for_oracle();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,143,d.output);self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertEqual(r['interrupt']['name'],'SIGTERM')
        self.assertEqual(r['interrupt']['forwarded_signal'],15);self.assertNoFalseResult(r);self.assertNoOrphans(d)

    def test_uncooperative_child_is_killed_after_the_grace_period(self):
        d=self.start('--mode','ignore','--seconds','60',wrapper=INT_PRESERVE);pids=d.wait_for_oracle();t0=time.monotonic();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,130,d.output);self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED')
        self.assertEqual(r['native_calls'][0]['ended_by'],'SIGKILL after grace');self.assertEqual(r['grace_seconds'],1.0)
        self.assertNoOrphans(d);self.assertFalse(any(alive(p) for p in pids))

    def test_driver_deadline_finalises_timed_out(self):
        d=self.start('--mode','sleep','--seconds','60',driver_args=('--max-minutes','0.03'));d.wait_for_oracle();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,124,d.output);self.assertEqual(r['status'],'TIMED OUT; NOT ADOPTED');self.assertEqual(r['terminal_outcome'],'TIMED_OUT')
        self.assertEqual((r['interrupt']['name'],r['interrupt']['forwarded_signal'],r['interrupt']['reason']),('SIGALRM',15,'driver deadline'))
        self.assertTrue(r['terminal']);self.assertNoFalseResult(r);self.assertNoOrphans(d)

    def test_sigkill_of_the_driver_leaves_a_checkpoint_and_reconcile_marks_killed(self):
        d=self.start('--mode','sleep','--seconds','60');pids=d.wait_for_oracle()
        wait_until(lambda:d.receipt.exists() and d.read_receipt().get('current_child'),5,'the child checkpoint')
        os.kill(d.proc.pid,signal.SIGKILL);rc=d.wait();prior_bytes=d.receipt.read_bytes();prior=json.loads(prior_bytes)
        self.assertEqual(rc,-9);self.assertEqual(prior['status'],'RUNNING');self.assertFalse(prior['terminal']);self.assertEqual(prior['phase'],'base_check')
        self.assertEqual(prior['current_child']['pid'],pids[0]);self.assertTrue(alive(pids[0]),'the orphaned oracle is the point of this test')
        result=lifecycle.reconcile(d.receipt,137,invocation=prior['invocation'])
        self.assertEqual(result['action'],'reconciled');r=d.read_receipt()
        self.assertEqual(r['status'],'KILLED; OUTCOME UNKNOWN; NOT ADOPTED');self.assertEqual(r['terminal_outcome'],'KILLED');self.assertTrue(r['terminal'])
        self.assertEqual(r['recovery']['prior_status'],'RUNNING');self.assertEqual(r['recovery']['last_checkpoint']['phase'],'base_check')
        self.assertEqual(r['recovery']['prior_sha256'],lifecycle.sha_bytes(prior_bytes));self.assertTrue(r['recovery']['invocation_verified'])
        self.assertTrue(r['recovery']['child_at_exit']['alive_at_reconcile']);self.assertIn('never signalled',r['recovery']['child_at_exit']['action'])
        events=[json.loads(l) for l in d.receipt.with_name('osc4-test.raw-events.jsonl').read_text().splitlines()]
        self.assertEqual(events[0]['prior_raw'],prior_bytes.decode());self.assertEqual(events[0]['exit_status'],137);self.assertNoFalseResult(r)
        bytes_after=d.receipt.read_bytes();kept=lifecycle.reconcile(d.receipt,137,invocation=prior['invocation'])
        self.assertEqual(kept['action'],'kept');self.assertEqual(d.receipt.read_bytes(),bytes_after)
        os.killpg(pids[0],signal.SIGKILL);wait_until(lambda:not any(alive(p) for p in pids),5,'test-owned orphan cleanup')

    def test_stale_receipt_from_another_invocation_is_refused_before_any_child(self):
        out=self.tmp/'out';out.mkdir();stale=out/'osc4-test.json'
        stale.write_text(json.dumps({'schema':'osc4-transaction-receipt-1','status':'RUNNING','adopted':False,'raw_gate_passed':False})+'\n');before=stale.read_bytes()
        d=self.start('--mode','quick',driver_args=('--invocation','run-2'));rc=d.wait()
        self.assertEqual(rc,3,d.output);self.assertIn('refusing to start',d.output);self.assertEqual(stale.read_bytes(),before);self.assertEqual(d.oracle_pids(),[])
        self.assertFalse((self.tmp/'cids').exists())

    def docker_or_skip(self):
        docker=shutil.which('docker')
        if not docker:self.skipTest('docker is not installed')
        image=dict(l.split('=',1) for l in (ROOT/'scripts/kicad/pin.env').read_text().splitlines() if '=' in l)['KICAD_IMAGE'].strip("'")
        if subprocess.run([docker,'image','inspect',image],capture_output=True).returncode:self.skipTest('pinned KiCad image is not present locally; no pull from a test')
        return docker

    def docker_run_until_sleeping(self,docker,grace):
        """Start the driver on the real run.sh (`sleep` in the pinned image), wait for that container, TERM the driver."""
        global CHILD_ENV
        saved=CHILD_ENV;CHILD_ENV={**CHILD_ENV,'OSC4_GRACE_SECONDS':grace}
        try:d=self.start('--mode','sleep','--seconds','60','--docker')
        finally:CHILD_ENV=saved
        cids=self.tmp/'cids'
        def running():
            for cid in lifecycle.owned_containers(cids):
                state=subprocess.run([docker,'inspect','-f','{{.State.Running}} {{.Config.Cmd}}',cid],capture_output=True,text=True).stdout
                if state.startswith('true') and 'sleep' in state:return cid
            return None
        wait_until(running,90,'the owned sleep container');target=running()
        os.kill(d.proc.pid,signal.SIGTERM);rc=d.wait(timeout=120);r=d.read_receipt()
        self.assertEqual(rc,143,d.output);self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertIn('ended_by',r['native_calls'][-1])
        def gone():
            state=subprocess.run([docker,'inspect','-f','{{.State.Running}}',target],capture_output=True,text=True)
            return state.returncode!=0 or state.stdout.strip()!='true'
        wait_until(gone,30,'the owned container to stop')
        for cid in lifecycle.owned_containers(cids):
            self.assertFalse(subprocess.run([docker,'inspect','-f','{{.State.Running}}',cid],capture_output=True,text=True).stdout.startswith('true'),cid)
        return r

    def test_docker_proxied_signal_stops_the_owned_container_with_init(self):
        r=self.docker_run_until_sleeping(self.docker_or_skip(),grace='10')
        self.assertEqual(r['native_calls'][-1]['ended_by'],'exited after signal');self.assertNotIn('containers_stopped',r)

    def test_docker_orphaned_container_is_stopped_by_its_cidfile(self):
        # Grace 0: the client is SIGKILLed at once, which orphans the container; the driver must docker stop exactly it.
        r=self.docker_run_until_sleeping(self.docker_or_skip(),grace='0')
        self.assertEqual(r['native_calls'][-1]['ended_by'],'SIGKILL after grace')
        self.assertTrue(r.get('containers_stopped'),'the orphaned container was not stopped through its cidfile')
        self.assertTrue(all(c['ok'] and c['action']=='docker stop' for c in r['containers_stopped']))

class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self._tmp=tempfile.TemporaryDirectory(prefix='osc4-reconcile-');self.tmp=Path(self._tmp.name);self.path=self.tmp/'osc4-test.json'

    def tearDown(self):self._tmp.cleanup()

    def nonterminal(self,**extra):
        data={'schema':lifecycle.SCHEMA,'status':'RUNNING','terminal':False,'terminal_outcome':None,'adopted':False,'raw_gate_passed':False,
              'invocation':'run-1','phases':[{'phase':'stage','started_utc':'2026-11-08T00:00:00Z'}],**extra}
        self.path.write_text(json.dumps(data,indent=1,sort_keys=True)+'\n');return data

    def test_malformed_partial_receipt_is_reconciled_with_its_bytes_kept(self):
        raw=b'{"schema": "osc4-transaction-receipt-2", "status": "RUN';self.path.write_bytes(raw)
        result=lifecycle.reconcile(self.path,137,invocation='run-1',board='osc-core',spec_name='osc4-test');r=json.loads(self.path.read_text())
        self.assertEqual(result['action'],'reconciled');self.assertEqual(r['status'],'KILLED; OUTCOME UNKNOWN; NOT ADOPTED')
        self.assertIsNotNone(r['recovery']['prior_parse_error']);self.assertEqual(r['recovery']['prior_sha256'],lifecycle.sha_bytes(raw))
        self.assertFalse(r['adopted']);self.assertFalse(r['raw_gate_passed']);self.assertEqual((r['board'],r['spec_name']),('osc-core','osc4-test'))
        self.assertFalse(r['recovery']['invocation_verified'])
        events=self.path.with_name('osc4-test.raw-events.jsonl').read_text().splitlines();self.assertEqual(json.loads(events[0])['prior_raw'],raw.decode())

    def test_unknown_exit_status_keeps_the_receipt_nonterminal(self):
        self.nonterminal();result=lifecycle.reconcile(self.path,None,invocation='run-1');r=json.loads(self.path.read_text())
        self.assertEqual(result['action'],'reconciled');self.assertFalse(r['terminal']);self.assertEqual(r['terminal_outcome'],'UNKNOWN');self.assertEqual(r['status'],'RUNNING')
        self.assertIn('no exit status known',r['recovery']['note'])

    def test_exit_codes_map_to_distinct_states(self):
        for code,status in ((130,'INTERRUPTED; NOT ADOPTED'),(143,'INTERRUPTED; NOT ADOPTED'),(124,'TIMED OUT; NOT ADOPTED'),(137,'KILLED; OUTCOME UNKNOWN; NOT ADOPTED'),(1,'ERROR; NOT ADOPTED'),(0,'ERROR; NOT ADOPTED')):
            with self.subTest(code=code):
                self.nonterminal(raw_gate_passed=True);lifecycle.reconcile(self.path,code,invocation='run-1');r=json.loads(self.path.read_text())
                self.assertEqual(r['status'],status);self.assertTrue(r['terminal']);self.assertFalse(r['raw_gate_passed']);self.assertFalse(r['adopted'])
                self.assertEqual(r['recovery']['exit_status'],code)

    def test_other_invocation_and_historical_receipts_are_refused(self):
        self.nonterminal();before=self.path.read_bytes()
        self.assertEqual(lifecycle.reconcile(self.path,137,invocation='run-2')['exit_code'],4);self.assertEqual(self.path.read_bytes(),before)
        self.path.write_text(json.dumps({'schema':'osc4-transaction-receipt-1','status':'RUNNING','adopted':False,'raw_gate_passed':False})+'\n');before=self.path.read_bytes()
        self.assertEqual(lifecycle.reconcile(self.path,137,invocation='run-2')['action'],'refused');self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(self.path.with_name('osc4-test.raw-events.jsonl').exists())

    def test_terminal_receipt_is_kept_byte_for_byte(self):
        self.nonterminal(terminal=True,terminal_outcome='COMPLETED',status='NATIVE CHECKED; RAW GATE PASSED; NOT PROMOTED',raw_gate_passed=True);before=self.path.read_bytes()
        result=lifecycle.reconcile(self.path,137,invocation='run-1');self.assertEqual(result['action'],'kept');self.assertEqual(self.path.read_bytes(),before)

    def test_missing_receipt_records_that_nothing_was_written(self):
        result=lifecycle.reconcile(self.path,130,invocation='run-1',board='osc-core',spec_name='osc4-test');r=json.loads(self.path.read_text())
        self.assertEqual(result['status'],'INTERRUPTED; NOT ADOPTED');self.assertFalse(r['recovery']['prior_present']);self.assertEqual(r['invocation'],'run-1');self.assertFalse(r['adopted'])

    def test_reconcile_cli_through_transaction_py(self):
        receipt=self.tmp/'osc4-k-agnd-r5243-2.json'
        receipt.write_text(json.dumps({'schema':lifecycle.SCHEMA,'status':'RUNNING','terminal':False,'adopted':False,'raw_gate_passed':False,'invocation':'44-1'})+'\n')
        done=subprocess.run([sys.executable,str(TX),'osc-core','--reconcile','--exit-status','137','--invocation','44-1','--out-dir',str(self.tmp)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(done.returncode,0,done.stdout+done.stderr);self.assertEqual(json.loads(done.stdout)['status'],'KILLED; OUTCOME UNKNOWN; NOT ADOPTED')
        self.assertEqual(json.loads(receipt.read_text())['terminal_outcome'],'KILLED')
        done=subprocess.run([sys.executable,str(TX),'osc-core','--reconcile','--exit-status','unknown','--invocation','other','--out-dir',str(self.tmp)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(done.returncode,0);self.assertEqual(json.loads(done.stdout)['action'],'kept')


if __name__=='__main__':unittest.main()
