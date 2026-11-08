#!/usr/bin/env python3
"""Receipt lifecycle and signal propagation of circuit/reviews/osc4-local-transactions-20261107/transaction.py (issue #308).

Every test starts the driver as a real process through the workflow's control path
(`timeout --signal=TERM --kill-after=...` + `bash scripts/pcbgen/with_route_guard.sh`, the workflow's form), with a stub
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
# The workflow drives the wrapper with TERM: on the ubuntu-26.04 runner image `timeout --signal=INT` SIGKILLs the
# child at once (exit 137, receipt left RUNNING; CI run 42490037580), which is the #308 symptom; GNU coreutils 9.4 delivers INT.
TERM=('timeout','--signal=TERM','--kill-after=20s','3s')
TERM_PRESERVE=('timeout','--signal=TERM','--preserve-status','--kill-after=20s','3s')
INT_PRESERVE=('timeout','--signal=INT','--preserve-status','--kill-after=20s','3s')


alive=lifecycle.alive


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
        self.assertEqual([p['phase'] for p in r['phases']],['preflight','base_check','stage','fresh_check','final_gate'])
        self.assertTrue(all(p['ended_utc'] for p in r['phases']))
        self.assertEqual([c['returncode'] for c in r['native_calls']],[0,0,0]);self.assertIsNone(r['current_child'])
        self.assertTrue(all(c['pid']>0 and c['pgid']==c['pid'] for c in r['native_calls']))
        self.assertTrue(r['invocation']);self.assertRegex(r['source_revision'],r'^[0-9a-f]{40}$|^unknown$')
        self.assertTrue(r['environment']['hosted']);self.assertEqual(r['driver']['pid']>0,True);self.assertEqual(r['signals'],[])
        self.assertEqual(r['max_minutes'],80);self.assertIn('budgets.json',r['budget_source'])
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

    def test_term_from_the_timeout_wrapper_finalises_interrupted(self):
        # The workflow's form: no --preserve-status, so the wrapper reports 124 once the driver exited after TERM.
        d=self.start('--mode','sleep','--seconds','60',wrapper=TERM);d.wait_for_oracle();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,124,f'wrapper exit {rc}; receipt {r["status"]}; output:\n{d.output}')
        self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertEqual(r['terminal_outcome'],'INTERRUPTED');self.assertTrue(r['terminal'])
        self.assertEqual((r['interrupt']['signal'],r['interrupt']['name'],r['interrupt']['phase']),(15,'SIGTERM','base_check'))
        self.assertEqual(r['signals'][0]['name'],'SIGTERM');self.assertEqual(r['native_calls'][0]['ended_by'],'exited after signal')
        self.assertIsNotNone(r['native_calls'][0]['returncode']);self.assertIsNone(r['current_child']);self.assertIn('wall_seconds',r)
        self.assertIn('transaction stopped: SIGTERM received',d.output);self.assertNoFalseResult(r);self.assertNoOrphans(d)

    def test_term_exits_143_when_the_wrapper_preserves_status(self):
        d=self.start('--mode','sleep','--seconds','60',wrapper=TERM_PRESERVE);d.wait_for_oracle();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,143,d.output);self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertEqual(r['interrupt']['name'],'SIGTERM')
        self.assertEqual(r['interrupt']['forwarded_signal'],15);self.assertNoFalseResult(r);self.assertNoOrphans(d)

    def test_int_from_the_timeout_wrapper_is_either_honoured_or_reconciled_as_killed(self):
        """INT depends on the host's `timeout`: GNU delivers it (130, INTERRUPTED); the ubuntu-26.04 image SIGKILLs the
        driver at once (137, receipt RUNNING), the #308 symptom. Either way no result is invented and the collector finishes."""
        d=self.start('--mode','sleep','--seconds','60',wrapper=INT_PRESERVE);pids=d.wait_for_oracle();rc=d.wait();r=d.read_receipt()
        self.assertIn(rc,(130,137),f'wrapper exit {rc}; receipt {r["status"]}; output:\n{d.output}')
        if rc==130:
            print('\n[osc4] host timeout delivers --signal=INT: driver finalised',r['status'],flush=True)
            self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertEqual(r['interrupt']['name'],'SIGINT');self.assertNoOrphans(d)
        else:
            print('\n[osc4] host timeout --signal=INT SIGKILLed the driver at once (the #308 symptom); receipt',r['status'],flush=True)
            self.assertFalse(r['terminal']);self.assertEqual(r['phase'],'base_check')
            result=lifecycle.reconcile(d.receipt,rc,invocation=r['invocation']);self.assertEqual(result['status'],'KILLED; OUTCOME UNKNOWN; NOT ADOPTED')
            self.assertNoFalseResult(d.read_receipt())
            # The SIGKILLed driver could not stop its (new-session) child; the test owns that cleanup.
            for pid in pids:
                try:os.killpg(pid,signal.SIGKILL)
                except ProcessLookupError:pass
            wait_until(lambda:not any(alive(p) for p in pids),5,'test-owned orphan cleanup')

    def test_uncooperative_child_is_killed_after_the_grace_period(self):
        d=self.start('--mode','ignore','--seconds','60',wrapper=TERM_PRESERVE);pids=d.wait_for_oracle();t0=time.monotonic();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,143,d.output);self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED')
        self.assertEqual(r['native_calls'][0]['ended_by'],'SIGKILL after grace');self.assertEqual(r['grace_seconds'],1.0)
        self.assertIn(pids[1],r['native_calls'][0]['killed_pids'],'the grandchild that ignored the signal must be among the PIDs killed by name')
        self.assertNoOrphans(d);self.assertFalse(any(alive(p) for p in pids))

    def test_driver_deadline_finalises_timed_out(self):
        # 15 s deadline against a 60 s oracle sleep: only the sleep can exceed it, and the oracle is awaited for up to 60 s first.
        d=self.start('--mode','sleep','--seconds','60',driver_args=('--max-minutes','0.25'));d.wait_for_oracle(timeout=60);rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,124,d.output);self.assertEqual(r['status'],'TIMED OUT; NOT ADOPTED');self.assertEqual(r['terminal_outcome'],'TIMED_OUT')
        self.assertEqual((r['interrupt']['name'],r['interrupt']['forwarded_signal'],r['interrupt']['reason']),('SIGALRM',15,'driver deadline'))
        self.assertTrue(r['terminal']);self.assertNoFalseResult(r);self.assertNoOrphans(d)

    def test_chatty_child_shutdown_is_drained_not_killed(self):
        # The grandchild writes 300 KiB on the forwarded signal: without draining it would block on the pipe and be SIGKILLed.
        d=self.start('--mode','verbose','--seconds','60',wrapper=TERM_PRESERVE);d.wait_for_oracle();rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,143,d.output);self.assertEqual(r['native_calls'][0]['ended_by'],'exited after signal')
        self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertNoOrphans(d)

    def test_late_signals_after_the_result_is_decided_only_get_recorded(self):
        # settle() cancels the deadline timer and demotes later signals: a COMPLETED receipt must stay COMPLETED.
        script=f"""
import importlib.util,json,os,signal,sys,time
spec=importlib.util.spec_from_file_location('lc',{str(TX.with_name('lifecycle.py'))!r});lc=importlib.util.module_from_spec(spec);spec.loader.exec_module(lc)
lc.install(deadline_seconds=0.2)
r=lc.Receipt(sys.argv[1],{{'schema':lc.SCHEMA,'status':'NATIVE CHECKED; RAW GATE PASSED; NOT PROMOTED','terminal':True,'terminal_outcome':'COMPLETED','adopted':False,'raw_gate_passed':True,'signals':[]}})
lc.STATE.receipt=r;r.save();lc.settle()
time.sleep(0.6)                      # the 0.2 s deadline would have fired here without settle()
os.kill(os.getpid(),signal.SIGINT);time.sleep(0.1)
os.kill(os.getpid(),signal.SIGTERM);time.sleep(0.1)
r.save();print('still running');sys.exit(0)
"""
        out=self.tmp/'late.json';done=subprocess.run([sys.executable,'-c',script,str(out)],capture_output=True,text=True,timeout=30)
        self.assertEqual(done.returncode,0,done.stdout+done.stderr);self.assertIn('still running',done.stdout);r=json.loads(out.read_text())
        self.assertEqual((r['status'],r['terminal_outcome'],r['terminal'],r['raw_gate_passed']),('NATIVE CHECKED; RAW GATE PASSED; NOT PROMOTED','COMPLETED',True,True))
        self.assertEqual([x['name'] for x in r['signals']],['SIGINT','SIGTERM']);self.assertNotIn('interrupt',r)

    def test_second_run_in_the_same_interpreter_is_interruptible_and_starts_clean(self):
        # lifecycle.reset(): the first run completes; the second (sleep oracle, out2/) is interrupted and carries only its own signal.
        d=self.start('--mode','quick','--then-sleep-run','--seconds','60');d.wait_for_oracle(count=5,timeout=60)
        os.kill(d.proc.pid,signal.SIGTERM);rc=d.wait();first=d.read_receipt();second=json.loads((self.tmp/'out2/osc4-test.json').read_text())
        self.assertEqual(rc,143,d.output);self.assertEqual(first['terminal_outcome'],'COMPLETED');self.assertEqual(first['signals'],[])
        self.assertEqual(second['status'],'INTERRUPTED; NOT ADOPTED');self.assertEqual([x['name'] for x in second['signals']],['SIGTERM'])
        self.assertNotEqual(first['invocation'],second['invocation']);self.assertNoOrphans(d)

    def test_signal_during_preflight_leaves_a_finalised_receipt_and_no_cid_dir(self):
        d=self.start('--mode','quick','--slow-validate','30',wrapper=TERM_PRESERVE)
        wait_until(lambda:(self.tmp/'validating').exists(),10,'the preflight to start');rc=d.wait();r=d.read_receipt()
        self.assertEqual(rc,143,d.output);self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED');self.assertEqual(r['interrupt']['phase'],'preflight')
        self.assertTrue(r['terminal']);self.assertEqual(r['native_calls'],[]);self.assertFalse((self.tmp/'cids').exists());self.assertEqual(d.oracle_pids(),[])

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

    def docker_start(self,docker,grace):
        """Start the driver on the real run.sh (`sleep` in the pinned image) and wait for that container to run."""
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
        wait_until(running,90,'the owned sleep container');return d,running()

    def container_running(self,docker,cid):
        state=subprocess.run([docker,'inspect','-f','{{.State.Running}}',cid],capture_output=True,text=True)
        return state.returncode==0 and state.stdout.strip()=='true'

    def test_docker_proxied_signal_stops_the_owned_container_with_init(self):
        docker=self.docker_or_skip();d,target=self.docker_start(docker,grace='10')
        os.kill(d.proc.pid,signal.SIGTERM);rc=d.wait(timeout=120);r=d.read_receipt()
        self.assertEqual(rc,143,d.output);self.assertEqual(r['status'],'INTERRUPTED; NOT ADOPTED')
        self.assertEqual(r['native_calls'][-1]['ended_by'],'exited after signal');self.assertNotIn('containers_stopped',r)
        wait_until(lambda:not self.container_running(docker,target),30,'the owned container to stop')
        self.assertFalse((self.tmp/'cids').exists(),'the cid directory is removed once no owned container is left')

    def test_docker_orphaned_container_is_stopped_by_the_collector_through_its_cidfile(self):
        # A SIGKILLed driver (the #308 case) leaves the docker client and its container behind; the collector's
        # reconcile stops exactly the containers listed in the driver's cid directory.
        docker=self.docker_or_skip();d,target=self.docker_start(docker,grace='10')
        os.kill(d.proc.pid,signal.SIGKILL);rc=d.wait(timeout=60);self.assertEqual(rc,-9)
        time.sleep(2);self.assertTrue(self.container_running(docker,target),'without the driver the container keeps running: that is the orphan')
        prior=d.read_receipt();call=prior['current_child'];self.assertTrue(call and call['pid'])
        result=lifecycle.reconcile(d.receipt,137,invocation=prior['invocation']);r=d.read_receipt()
        self.assertEqual(result['status'],'KILLED; OUTCOME UNKNOWN; NOT ADOPTED')
        stopped=r['recovery']['containers_stopped'];self.assertTrue(stopped,'the collector did not stop the orphaned container')
        self.assertTrue(all(c['ok'] and c['action']=='docker stop' for c in stopped));self.assertIn(target,[c['container'] for c in stopped])
        wait_until(lambda:not self.container_running(docker,target),30,'the owned container to stop')
        # The orphaned host processes (bash run.sh and the docker client) are the test's to clean up, by the recorded identity.
        leftovers=[call['pid'],*lifecycle.session_members(call['pid'],{'sid':call['sid'],'starttime':call['starttime_ticks']},exclude=(call['pid'],))]
        for pid in leftovers:
            try:os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:pass
        wait_until(lambda:not any(alive(p) for p in leftovers),10,'test-owned cleanup of the orphaned client')

class OwnedChildTests(unittest.TestCase):
    """In-process checks of lifecycle.owned_run and the /proc session enumeration."""
    def setUp(self):
        self._tmp=tempfile.TemporaryDirectory(prefix='osc4-owned-');self.tmp=Path(self._tmp.name)
        self.saved=(lifecycle.STATE.cwd,lifecycle.STATE.cid_dir,lifecycle.STATE.shim_dir,lifecycle.STATE.receipt)
        lifecycle.STATE.cwd=ROOT;lifecycle.STATE.cid_dir=None;lifecycle.STATE.shim_dir=None;lifecycle.STATE.receipt=None

    def tearDown(self):
        lifecycle.STATE.cwd,lifecycle.STATE.cid_dir,lifecycle.STATE.shim_dir,lifecycle.STATE.receipt=self.saved;self._tmp.cleanup()

    def test_completed_child_never_triggers_a_kill(self):
        from unittest import mock
        with mock.patch.object(lifecycle.os,'kill') as kill,mock.patch.object(lifecycle.os,'killpg') as killpg,mock.patch.object(subprocess.Popen,'send_signal') as send:
            out=lifecycle.owned_run('bash','-c','echo owned-ok')
        self.assertEqual(out.strip(),'owned-ok');kill.assert_not_called();killpg.assert_not_called();send.assert_not_called()
        self.assertEqual(lifecycle.STATE.children,{})

    def test_failed_child_raises_without_any_kill(self):
        from unittest import mock
        with mock.patch.object(lifecycle.os,'kill') as kill,mock.patch.object(lifecycle.os,'killpg') as killpg:
            with self.assertRaisesRegex(RuntimeError,'failed \\(7\\)'):lifecycle.owned_run('bash','-c','exit 7')
        kill.assert_not_called();killpg.assert_not_called()

    def test_success_path_records_stragglers_without_killing(self):
        from unittest import mock
        lifecycle.STATE.receipt=lifecycle.Receipt(self.tmp/'r.json',{'native_calls':[]})
        with mock.patch.object(lifecycle.os,'kill') as kill:
            out=lifecycle.owned_run('bash','-c','sleep 20 >/dev/null 2>&1 & echo leader-done')  # the straggler must not hold the stdout pipe
        call=lifecycle.STATE.receipt.data['native_calls'][0];stragglers=call.get('stragglers')
        self.assertEqual(out.strip(),'leader-done');kill.assert_not_called();self.assertNotIn('ended_by',call)
        self.assertTrue(stragglers,'the background sleep must be recorded as a straggler');self.assertTrue(all(alive(p) for p in stragglers))
        for pid in stragglers:os.kill(pid,signal.SIGKILL)

    def test_unwinding_on_a_foreign_exception_asks_the_child_to_stop_before_the_grace(self):
        from unittest import mock
        lifecycle.STATE.receipt=lifecycle.Receipt(self.tmp/'r.json',{'native_calls':[]});saved=lifecycle.STATE.grace;lifecycle.STATE.grace=3
        try:
            with mock.patch.object(subprocess.Popen,'communicate',side_effect=KeyboardInterrupt):
                with self.assertRaises(KeyboardInterrupt):lifecycle.owned_run('bash','-c','exec sleep 30')
        finally:lifecycle.STATE.grace=saved
        call=lifecycle.STATE.receipt.data['native_calls'][0]
        self.assertEqual(call['forwarded'],'SIGTERM while unwinding');self.assertEqual(call['ended_by'],'exited after signal');self.assertFalse(alive(call['pid']))

    def test_route_jack_grid_native_spawn_goes_through_the_runner_hook(self):
        import importlib.util as iu
        if not (iu.find_spec('numpy') and iu.find_spec('scipy')):self.skipTest('route_jack_grid needs numpy and scipy')
        sys.path.insert(0,str(ROOT));import scripts.pcbgen.route_jack_grid as rjg
        seen=[];rjg.RUNNER=lambda *a:seen.append(a) or 'hooked'
        try:self.assertEqual(rjg.run('bash','-c','echo not-run'),'hooked');self.assertEqual(seen,[('bash','-c','echo not-run')])
        finally:rjg.RUNNER=None
        self.assertEqual(rjg.run('bash','-c','echo default').strip(),'default')

    def test_docker_shim_finds_run_after_global_options(self):
        fake=self.tmp/'fake-docker';fake.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "$@"\n');fake.chmod(0o755)
        cid_dir=self.tmp/'cids';cid_dir.mkdir();shim=lifecycle.docker_shim_dir(cid_dir,real=str(fake))/'docker'
        out=subprocess.run([str(shim),'--context','k','-l','debug','run','--rm','img','cmd'],capture_output=True,text=True,check=True).stdout.splitlines()
        self.assertEqual(out[:7],['--context','k','-l','debug','run','--init','--cidfile']);self.assertTrue(out[7].startswith(str(cid_dir)));self.assertEqual(out[8:],['--rm','img','cmd'])
        out=subprocess.run([str(shim),'run','img'],capture_output=True,text=True,check=True).stdout.splitlines();self.assertEqual((out[0],out[1],out[4]),('run','--init','img'))
        out=subprocess.run([str(shim),'-H','tcp://x','ps','-a'],capture_output=True,text=True,check=True).stdout.splitlines();self.assertEqual(out,['-H','tcp://x','ps','-a'])

    def test_session_members_are_bound_by_session_and_start_time_not_pid_alone(self):
        proc=self.tmp/'proc'
        def stat(pid,state,pgrp,session,start):
            (proc/str(pid)).mkdir(parents=True);fields=['0']*52;fields[0]=state;fields[2]=str(pgrp);fields[3]=str(session);fields[19]=str(start)
            (proc/str(pid)/'stat').write_text(f'{pid} (fake (name) x) '+' '.join(fields)+'\n')
        stat(500,'S',500,500,1000)   # the reaped leader's PID, reused by an unrelated process in another session
        stat(501,'S',500,900,1200)   # member: same group, the child's session, started after it
        stat(502,'S',500,900,800)    # same group and session but started before the child: not ours
        stat(503,'Z',500,900,1300)   # zombie member: nothing to signal
        stat(504,'S',777,900,1300)   # the child's session, a different group
        (proc/'self').mkdir();(proc/'not-a-pid').mkdir()
        identity={'sid':900,'starttime':1000}
        self.assertEqual(lifecycle.session_members(500,identity,proc_root=proc,exclude=(500,)),[501])
        self.assertEqual(lifecycle.session_members(500,{'sid':None,'starttime':1000},proc_root=proc),[])
        self.assertEqual(lifecycle.session_members(500,identity,proc_root=self.tmp/'absent'),[])


class ReconcileTests(unittest.TestCase):
    def setUp(self):
        self._tmp=tempfile.TemporaryDirectory(prefix='osc4-reconcile-');self.tmp=Path(self._tmp.name);self.path=self.tmp/'osc4-test.json'

    def tearDown(self):self._tmp.cleanup()

    def nonterminal(self,**extra):
        data={'schema':lifecycle.SCHEMA,'status':'RUNNING','terminal':False,'terminal_outcome':None,'adopted':False,'raw_gate_passed':False,
              'invocation':'run-1','phases':[{'phase':'stage','started_utc':'2026-11-08T00:00:00Z'}],**extra}
        self.path.write_text(json.dumps(data,indent=1,sort_keys=True)+'\n');return data

    def test_malformed_partial_receipt_is_refused_unless_forced_and_then_kept_byte_for_byte(self):
        raw=b'{"schema": "osc4-transaction-receipt-2", "status": "RUN';self.path.write_bytes(raw)
        refused=lifecycle.reconcile(self.path,137,invocation='run-1',board='osc-core',spec_name='osc4-test')
        self.assertEqual((refused['action'],refused['exit_code']),('refused',4));self.assertEqual(self.path.read_bytes(),raw)
        self.assertFalse(self.path.with_name('osc4-test.raw-events.jsonl').exists())
        result=lifecycle.reconcile(self.path,137,invocation='run-1',board='osc-core',spec_name='osc4-test',force_corrupt=True);r=json.loads(self.path.read_text())
        self.assertEqual(result['action'],'reconciled');self.assertEqual(r['status'],'KILLED; OUTCOME UNKNOWN; NOT ADOPTED')
        self.assertIsNotNone(r['recovery']['prior_parse_error']);self.assertEqual(r['recovery']['prior_sha256'],lifecycle.sha_bytes(raw))
        self.assertFalse(r['adopted']);self.assertFalse(r['raw_gate_passed']);self.assertEqual((r['board'],r['spec_name']),('osc-core','osc4-test'))
        self.assertFalse(r['recovery']['invocation_verified']);self.assertNotIn('invocation',r,'a foreign invocation is never stamped onto unreadable bytes')
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

    def test_terminal_receipt_from_another_invocation_is_refused_not_kept(self):
        self.nonterminal(terminal=True,terminal_outcome='COMPLETED',status='NATIVE CHECKED; RAW GATE PASSED; NOT PROMOTED',raw_gate_passed=True);before=self.path.read_bytes()
        result=lifecycle.reconcile(self.path,0,invocation='run-2');self.assertEqual((result['action'],result['exit_code']),('refused',4));self.assertEqual(self.path.read_bytes(),before)

    def test_missing_receipt_records_that_nothing_was_written(self):
        result=lifecycle.reconcile(self.path,130,invocation='run-1',board='osc-core',spec_name='osc4-test');r=json.loads(self.path.read_text())
        self.assertEqual(result['status'],'INTERRUPTED; NOT ADOPTED');self.assertFalse(r['recovery']['prior_present']);self.assertEqual(r['invocation'],'run-1');self.assertFalse(r['adopted'])

    def test_reconcile_cli_through_transaction_py(self):
        receipt=self.tmp/'osc4-k-agnd-r5243-2.json'
        receipt.write_text(json.dumps({'schema':lifecycle.SCHEMA,'status':'RUNNING','terminal':False,'adopted':False,'raw_gate_passed':False,'invocation':'44-1'})+'\n')
        done=subprocess.run([sys.executable,str(TX),'osc-core','--reconcile','--exit-status','137','--invocation','44-1','--out-dir',str(self.tmp)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(done.returncode,0,done.stdout+done.stderr);self.assertEqual(json.loads(done.stdout)['status'],'KILLED; OUTCOME UNKNOWN; NOT ADOPTED')
        self.assertEqual(json.loads(receipt.read_text())['terminal_outcome'],'KILLED')
        done=subprocess.run([sys.executable,str(TX),'osc-core','--reconcile','--exit-status','unknown','--invocation','44-1','--out-dir',str(self.tmp)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(done.returncode,0);self.assertEqual(json.loads(done.stdout)['action'],'kept')
        done=subprocess.run([sys.executable,str(TX),'osc-core','--reconcile','--exit-status','0','--invocation','other','--out-dir',str(self.tmp)],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(done.returncode,4);self.assertEqual(json.loads(done.stdout)['action'],'refused')


if __name__=='__main__':unittest.main()
