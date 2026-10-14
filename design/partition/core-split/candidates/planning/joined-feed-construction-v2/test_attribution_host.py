"""Mocked Linux host operations and bounded synthetic retention tests only."""
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import patch

import attribution_host as H
import attribution_supervisor as S


class FakeOps:
    def __init__(self,parent):
        self.parent=parent;self.events=[];self.fail_mount=False;self.fail_unmount=False
        self.values={parent/'memory.max':str(S.MEMORY_MAX),parent/'memory.swap.max':'0',
                     parent/'cgroup.procs':str(os.getpid()),parent/'cgroup.controllers':'memory pids'}
        self.dirs=set()
    def read(self,path):return self.values.get(path,'populated 0' if path.name=='cgroup.events' else '')
    def write(self,path,value):
        self.events.append(('write',path.name,value));self.values[path]=value
        if path.name=='cgroup.procs' and path.parent!=self.parent:self.values[self.parent/'cgroup.procs']=''
    def mkdir(self,path):
        if path in self.dirs:raise FileExistsError(path)
        self.dirs.add(path);self.events.append(('mkdir',path.name))
    def rmdir(self,path):self.dirs.remove(path);self.events.append(('rmdir',path.name))
    def exists(self,path):return path.name=='cgroup.kill'
    def command(self,command,deadline):
        self.events.append(('command',command))
        if command[0]=='mount' and self.fail_mount:raise OSError('fixture mount denied')
        if command[0]=='umount' and self.fail_unmount:raise OSError('fixture unmount denied')
        return b''


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.parent=Path('/sys/fs/cgroup/fixture-e16.scope')
        self.ops=FakeOps(self.parent)
        self.layout=H.OwnedLayout(self.parent,Path('/tmp/e16-host-fixture-work'),1024**2,time.monotonic()+10,self.ops)

    def test_provision_and_ordered_cleanup(self):
        self.layout.provision();receipt=self.layout.cleanup()
        self.assertTrue(receipt['tmpfs_unmounted'])
        self.assertFalse(self.ops.dirs)
        writes=[e for e in self.ops.events if e[0]=='write']
        self.assertIn(('write','memory.max',str(S.WORKER_MEMORY)),writes)
        self.assertIn(('write','memory.max',str(S.ACTIVE_SCOPE_MEMORY)),writes)
        self.assertLess(writes.index(('write','cgroup.subtree_control','-memory')),
                        writes.index(('write','cgroup.procs',str(os.getpid())),2))

    def test_scope_ownership_refuses_extra_process(self):
        self.ops.values[self.parent/'cgroup.procs']=str(os.getpid())+' 999'
        with self.assertRaisesRegex(ValueError,'unexpected scope processes'):self.layout.provision()
        self.assertFalse(self.ops.events)

    def test_missing_swap_boundary_refuses_before_mutation(self):
        self.ops.values[self.parent/'memory.swap.max']='max'
        with self.assertRaisesRegex(ValueError,'limits differ'):self.layout.provision()
        self.assertFalse(self.ops.events)

    def test_mount_denial_cleans_created_groups_without_fake_unmount(self):
        self.ops.fail_mount=True
        with self.assertRaises(OSError):self.layout.provision()
        self.layout.cleanup()
        self.assertFalse(self.ops.dirs)
        self.assertFalse(any(e[0]=='command' and e[1][0]=='umount' for e in self.ops.events))

    def test_unmount_failure_is_not_cleanup_pass(self):
        self.layout.provision();self.ops.fail_unmount=True
        with self.assertRaisesRegex(ValueError,'unmount'):self.layout.cleanup()
        self.assertTrue(self.layout.mounted)

    def test_no_memory_delegation_refuses_before_mutation(self):
        self.ops.values[self.parent/'cgroup.controllers']='pids'
        with self.assertRaisesRegex(ValueError,'delegation'):self.layout.provision()
        self.assertFalse(self.ops.events)


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='e16-host-fixture-')
        self.root=Path(self.temp.name);self.source=self.root/'source';self.source.mkdir()
        self.dest=self.root/'retained'
    def tearDown(self):self.temp.cleanup()

    def test_full_copy_verified_before_original_release(self):
        (self.source/'a').write_bytes(b'a'*1200)
        (self.source/'sub').mkdir();(self.source/'sub/b').write_bytes(b'b'*20)
        receipt=H.retain_tree(self.source,self.dest,time.monotonic()+5,aggregate_limit=3000,other_bytes=100)
        self.assertEqual(receipt['bytes'],1220)
        self.assertTrue(receipt['source_released'])
        self.assertEqual((self.dest/'a').read_bytes(),b'a'*1200)
        self.assertEqual(list(self.source.iterdir()),[])

    def test_peak_two_copy_quota_refuses_before_creation(self):
        (self.source/'a').write_bytes(b'x'*1000)
        with self.assertRaisesRegex(ValueError,'aggregate quota'):
            H.retain_tree(self.source,self.dest,time.monotonic()+5,aggregate_limit=1999)
        self.assertFalse(self.dest.exists())
        self.assertTrue((self.source/'a').exists())

    def test_traversal_symlink_refused(self):
        (self.source/'escape').symlink_to('/etc/passwd')
        with self.assertRaisesRegex(ValueError,'nonregular'):
            H.retain_tree(self.source,self.dest,time.monotonic()+5,aggregate_limit=100000)
        self.assertFalse(self.dest.exists())

    def test_fsync_failure_keeps_source_and_partial_negative_copy(self):
        (self.source/'a').write_bytes(b'negative evidence')
        with patch.object(H.os,'fsync',side_effect=OSError('fixture fsync')):
            with self.assertRaises(H.RetentionFailure):H.retain_tree(self.source,self.dest,time.monotonic()+5,aggregate_limit=1000)
        self.assertTrue((self.source/'a').exists());self.assertTrue((self.dest/'a').exists())

    def test_expired_retention_does_not_create_destination(self):
        with self.assertRaisesRegex(ValueError,'TIMEOUT'):
            H.retain_tree(self.source,self.dest,time.monotonic()-1,aggregate_limit=1000)
        self.assertFalse(self.dest.exists())


class HostBoundaryTests(unittest.TestCase):
    def test_aggregate_memory_roles_and_retention_reserve(self):
        self.assertEqual(S.OUTER_MEMORY+S.LAUNCHER_MEMORY+S.SUPERVISOR_MEMORY+S.BOOTSTRAP_MEMORY+S.CONTROLLER_FILECACHE+S.SHARED_GUARD_MEMORY+S.WORKER_MEMORY,S.MEMORY_MAX)
        cap=H.tmpfs_capacity(1234)
        self.assertLessEqual(2*cap+H.HOST_LOG_MAX+S.LOG_RESERVE+H.HOST_RECEIPTS+S.RECEIPT_RESERVE+1234,S.OUTPUT_MAX)
        self.assertEqual(cap%4096,0)

    def test_fixed_scope_command_preserves_uid_and_isolation(self):
        r={'run_id':'a'*32,'attempt':1}
        cmd=H.scope_command(r,['--request','/tmp/request','--digest','f'*64],time.monotonic())
        self.assertIn('Delegate=memory',cmd)
        self.assertIn('--map-current-user',cmd);self.assertIn('--keep-caps',cmd)
        self.assertNotIn('--map-root-user',cmd)
        self.assertIn('--no-ask-password',cmd)
        self.assertIn('-I',cmd);self.assertIn('-B',cmd)
        self.assertIn('MemorySwapMax=0',cmd)

    def test_fixed_worker_command_refuses_arbitrary_command_field(self):
        with tempfile.TemporaryDirectory(prefix='e16-host-fixture-') as temp:
            path=Path(temp)/'request';path.write_text(json.dumps({'output':temp,'command':['bad']}))
            cmd=H.worker_command(path,'a'*64,Path(temp)/'authority',Path(temp)/'reservation')
        self.assertEqual(cmd[0],H.PYTHON)
        self.assertIn(str(H.HERE/'attribution_worker.py'),cmd)
        self.assertNotIn('bad',cmd)
        self.assertIn('-I',cmd);self.assertIn('-B',cmd)

    def test_launch_refuses_fixture_before_queueing(self):
        with tempfile.TemporaryDirectory(prefix='e16-host-fixture-') as temp:
            request=Path(temp)/'request';request.write_text(json.dumps({'fixture_only':True}))
            with patch.object(H.resource,'setrlimit'),patch.object(H.os,'execvpe') as execute:
                with self.assertRaisesRegex(ValueError,'refuses fixture'):
                    H.launch(request,'a'*64,Path(temp)/'auth',Path(temp)/'reservation')
            execute.assert_not_called()

    def test_real_environment_validator_blocks_loader_override_before_guard(self):
        # Exercise the real API signature, not a mock accepting arbitrary kwargs.
        import attribution_admission as admission
        with patch.object(H.resource,'setrlimit'),patch.dict(os.environ,{'LD_PRELOAD':'fixture-untrusted.so'}),             patch.object(H,'read_small') as read,patch.object(H,'UnitGuard') as guard:
            with self.assertRaisesRegex(ValueError,'environment override'):
                H.guard_entry('/tmp/unopened','a'*64,'/tmp/auth','/tmp/reservation')
        read.assert_not_called();guard.assert_not_called()

    def test_shared_guard_label_exactly_matches_isolated_command(self):
        guard=types.SimpleNamespace(path=Path('/fixture/heavy-guard.sh'),check=lambda:None)
        args=('/tmp/request','a'*64,'/tmp/auth','/tmp/reservation','b'*64)
        with patch.object(H,'UnitGuard',return_value=guard):cmd=H.guard_command(*args)
        self.assertEqual(' '.join(cmd[3:]),H.guard_label(*args))
        self.assertEqual(cmd.count('pycache_prefix=/dev/null'),2)
        self.assertEqual(cmd.count('-S'),2)

    def test_host_swap_disabled_is_required_for_outside_controllers(self):
        H.prove_no_host_swap('SwapTotal: 0 kB\n')
        for data in ('SwapTotal: 1024 kB\n','MemAvailable: 100000 kB\n'):
            with self.assertRaisesRegex(ValueError,'SwapTotal=0'):H.prove_no_host_swap(data)

    def test_soft_watchdog_interrupts_blocked_work_and_restores_timer(self):
        old=signal.getsignal(signal.SIGALRM)
        with self.assertRaisesRegex(TimeoutError,'watchdog'):
            with H.DeadlineWatchdog(time.monotonic()+.15,cleanup_seconds=.1):time.sleep(1)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL),(0.,0.))
        self.assertEqual(signal.getsignal(signal.SIGALRM),old)

    def test_hard_watchdog_cannot_be_swallowed_by_cleanup_handler(self):
        code=("import sys,time;sys.path.insert(0,"+repr(str(H.HERE))+");"
              "from attribution_host import DeadlineWatchdog\n"
              "with DeadlineWatchdog(time.monotonic()+.2,cleanup_seconds=.15):\n"
              " try:time.sleep(2)\n"
              " except TimeoutError:time.sleep(2)\n")
        result=subprocess.run([sys.executable,'-I','-S','-B','-X','pycache_prefix=/dev/null','-c',code],
                              capture_output=True,timeout=2)
        self.assertEqual(result.returncode,-signal.SIGALRM,result.stderr)

    def test_bounded_controller_capture(self):
        data=H._capture([sys.executable,'-c','print("synthetic")'],time.monotonic()+2,limit=100)
        self.assertEqual(data,b'synthetic\n')
        with self.assertRaisesRegex(ValueError,'log quota'):
            H._capture([sys.executable,'-c','print("x"*1000)'],time.monotonic()+2,limit=100)

    def test_controller_timeout_kills_synthetic_process(self):
        start=time.monotonic()
        with self.assertRaisesRegex(ValueError,'deadline'):
            H._capture([sys.executable,'-c','import time;time.sleep(30)'],start+.1)
        self.assertLess(time.monotonic()-start,1.)

    def test_scope_query_failure_never_passes_cleanup(self):
        with patch.object(H,'_capture',side_effect=ValueError('fixture query unavailable')):
            with self.assertRaisesRegex(ValueError,'cannot establish'):H._scope_cleanup('e16-test.scope',time.monotonic()+1)

    def test_preexisting_scope_is_never_claimed_or_stopped(self):
        with patch.object(H,'_capture',return_value=b'LoadState=loaded\nDescription=someone else\n') as command:
            with self.assertRaisesRegex(ValueError,'already exists'):
                H._fresh_scope('e16-existing.scope',time.monotonic()+1)
        self.assertEqual(len(command.call_args_list),1)
        self.assertIn('show',command.call_args.args[0])
        self.assertNotIn('stop',command.call_args.args[0])

    def test_scope_cleanup_refuses_other_description(self):
        with patch.object(H,'_capture',return_value=b'LoadState=loaded\nDescription=someone else\n') as command:
            with self.assertRaisesRegex(ValueError,'ownership description differs'):
                H._scope_cleanup('e16-existing.scope',time.monotonic()+1,'this exact request')
        self.assertEqual(len(command.call_args_list),1)
        self.assertIn('show',command.call_args.args[0])

    def test_missing_reservation_owner_cannot_be_environment_boolean(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(KeyError):H.prove_reservation_owner()

    def test_final_terminal_never_sets_acceptance_flags(self):
        with tempfile.TemporaryDirectory(prefix='e16-host-fixture-') as temp:
            root=Path(temp);H._host_receipt(root,{'status':'INCOMPLETE','reason':'fixture denial'},time.monotonic()+2)
            r=json.loads((root/'terminal.json').read_text())
            self.assertFalse(r['electrical_acceptance']);self.assertFalse(r['adopted'])

    def test_cleanup_failure_revokes_contained_success(self):
        # Full outer state machine, real O_EXCL flock only under this temp root;
        # authority, ledger, cgroups, mounts and commands are all test doubles.
        with tempfile.TemporaryDirectory(prefix='e16-host-fixture-') as temp:
            base=Path(temp);output=base/'output';guarddir=base/'guard';guarddir.mkdir()
            (guarddir/'slot-0.info').write_text(f'pid=1 started={int(time.time())} cwd=fixture')
            r={'run_id':'a'*32,'attempt':1,'guard_sha256':'b'*64,'output':str(output),'python':H.PYTHON,'host_limits':H.HOST_LIMITS,'request_kind':'resource-qualification'}
            request=base/'request';request.write_text(json.dumps(r))
            guard=types.SimpleNamespace(directory=guarddir,prove_owner=lambda:None)
            def capture(*args,**kw):
                (output/'contained.unaccepted.json').write_text(json.dumps({'request_sha256':'c'*64,'status':'COMPLETE'}))
                return b''
            admission=types.SimpleNamespace(claim=lambda *args:(base/'claim',100),check_environment=lambda *a,**k:None)
            with patch.object(H,'UnitGuard',return_value=guard),patch.object(H,'_verify',return_value=r),\
                 patch.object(H.pwd,'getpwuid',return_value=types.SimpleNamespace(pw_dir=temp)),\
                 patch.object(H.resource,'setrlimit'),patch.object(H,'prove_no_host_swap'),patch.object(H,'_fresh_scope'),patch.object(H,'_capture',side_effect=capture),\
                 patch.object(H,'_scope_cleanup',side_effect=ValueError('fixture cleanup failure')),\
                 patch.dict(sys.modules,{'attribution_admission':admission}),patch.dict(os.environ,{},clear=False):
                code=H.guard_entry(request,'c'*64,base/'authority',base/'reservation')
            self.assertEqual(code,1)
            receipt=json.loads((output/'terminal.json').read_text())
            self.assertEqual(receipt['status'],'INCOMPLETE')
            self.assertIn('scope cleanup',receipt['reason'])

class AcceptedResultTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='e16-host-fixture-')
        self.root=Path(self.temp.name);self.out=self.root/'output';self.out.mkdir()
        self.request=self.root/'request';self.authority=self.root/'authority';self.reservation=self.root/'reservation'
        self.data={'schema':'e16-attribution-request-v1','run_id':'a'*32,'output':str(self.out),
                   'request_kind':'resource-qualification','operation':'e16-selected-attribution-v1',
                   'limits':{'units':1},'guard_sha256':'b'*64,'trust_sha256':'c'*64,'checkout':str(self.root)}
        self.request.write_bytes(S.encoded(self.data));self.digest=hashlib.sha256(S.encoded(self.data)).hexdigest()
        self.claim=self.root/('a'*32+'.json');self.claim.write_text(json.dumps({'request_sha256':self.digest}))
        (self.out/'payload').write_text('tiny result')
        _,files=S._inventory(self.out,time.monotonic()+2,100000)
        self.receipt={'status':'PENDING_SHARED_GUARD','request_sha256':self.digest,
            'run_id':'a'*32,'request_kind':'resource-qualification','cleanup_complete':True,
            'electrical_acceptance':False,'whole_board_acceptance':False,'adopted':False,
            'guard_started_unix':1000,'guard_cwd':str(self.root),'scope_cleanup':{'collected':True},
            'guard_label':H.guard_label(self.request,self.digest,self.authority,self.reservation,'b'*64),
            'authority_path':str(self.authority),'reservation_path':str(self.reservation),
            'claim_path':str(self.claim),'claim_sha256':hashlib.sha256(self.claim.read_bytes()).hexdigest(),
            'claim_bytes':self.claim.stat().st_size,'files':files}
        (self.out/'terminal.json').write_bytes(S.encoded(self.receipt))
        journal={'request_sha256':self.digest,'run_id':'a'*32,'request_kind':'resource-qualification',
                 'terminal_status':'PENDING_SHARED_GUARD','cleanup_complete':True,
                 'output_manifest_sha256':hashlib.sha256(S.encoded(files)).hexdigest()}
        (self.root/('a'*32+'.terminal.json')).write_bytes(S.encoded(journal))
        guard=self.root/'.agent-guard/heavy';guard.mkdir(parents=True)
        self.ledger=guard/'runs.jsonl'
        self.row={'label':self.receipt['guard_label'],'cwd':str(self.root),'verdict':'PASS','exit':0,
                  'secs':3,'ts':1003,'min_mem_mb':2200}
        self.ledger.write_bytes(S.encoded(self.row))
        grant={'request_sha256':self.digest,'run_id':'a'*32,'request_kind':'resource-qualification',
               'operation':self.data['operation'],'limits':self.data['limits'],'approved':True,'exclusive':True,
               'issued_unix':999,'expires_unix':2000}
        self.admission=types.SimpleNamespace(verify_signature=lambda *args:grant,
            state_directory=lambda:self.root,read_json=lambda p:json.loads(Path(p).read_text()))
    def tearDown(self):self.temp.cleanup()
    def accepted(self):
        with patch.dict(sys.modules,{'attribution_admission':self.admission}),             patch.object(H.pwd,'getpwuid',return_value=types.SimpleNamespace(pw_dir=str(self.root))):
            return H.accepted_result(self.request,self.digest)
    def test_two_durable_receipts_required(self):
        result=self.accepted()
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(json.loads((self.out/'terminal.json').read_text())['status'],'PENDING_SHARED_GUARD')
    def test_missing_or_duplicate_guard_row_refuses(self):
        self.ledger.write_bytes(b'')
        with self.assertRaisesRegex(ValueError,'missing/ambiguous'):self.accepted()
        self.ledger.write_bytes(S.encoded(self.row)*2)
        with self.assertRaisesRegex(ValueError,'missing/ambiguous'):self.accepted()
    def test_guard_failure_or_unknown_memory_refuses(self):
        for change in ({'verdict':'ENV_SUSPECT'},{'min_mem_mb':None},{'exit':1},{'secs':181}):
            self.ledger.write_bytes(S.encoded(self.row|change))
            with self.assertRaises(ValueError):self.accepted()
    def test_retained_file_edit_refuses(self):
        (self.out/'payload').write_text('edited')
        with self.assertRaisesRegex(ValueError,'output changed'):self.accepted()
    def test_claim_from_another_operation_refuses(self):
        self.claim.write_text(json.dumps({'request_sha256':'f'*64}))
        with self.assertRaisesRegex(ValueError,'another operation'):self.accepted()
    def test_coordinated_output_and_receipt_hash_tamper_refused(self):
        (self.out/'payload').write_text('edited')
        self.receipt['files']['payload']={'bytes':6,'sha256':hashlib.sha256(b'edited').hexdigest()}
        (self.out/'terminal.json').write_bytes(S.encoded(self.receipt))
        with self.assertRaisesRegex(ValueError,'immutable terminal journal'):self.accepted()
    def test_acceptance_flag_tamper_refused(self):
        self.receipt['adopted']=True
        (self.out/'terminal.json').write_bytes(S.encoded(self.receipt))
        with self.assertRaisesRegex(ValueError,'flags changed'):self.accepted()
    def test_actual_finish_accounting_binds_later_acceptance(self):
        import attribution_admission as admission
        ledger=self.root/'campaign.json'
        raw=admission.canon({'attribution_charges':[{'run_id':'a'*32,'state':'ACTIVE'}],
                             'live_owned_work':True,'activity':'fixture active'})
        ledger.write_bytes(raw)
        self.claim.write_bytes(admission.canon({'request_sha256':self.digest,
            'after_ledger_sha256':hashlib.sha256(raw).hexdigest()}))
        self.receipt['claim_sha256']=hashlib.sha256(self.claim.read_bytes()).hexdigest()
        self.receipt['claim_bytes']=self.claim.stat().st_size
        (self.root/('a'*32+'.terminal.json')).unlink()
        grant=self.admission.verify_signature()
        self.admission=admission
        with patch.object(admission,'state_directory',return_value=self.root),             patch.object(admission,'ledger_path',return_value=ledger),             patch.object(admission,'verify_signature',return_value=grant):
            extra=admission.finish_accounting(self.data,self.digest,self.receipt,time.monotonic()+3)
            self.receipt['accounting_output_bytes']=self.receipt['claim_bytes']+extra
            (self.out/'terminal.json').write_bytes(S.encoded(self.receipt))
            self.assertEqual(self.accepted()['status'],'COMPLETE')
            self.assertFalse(json.loads(ledger.read_text())['live_owned_work'])
            (self.out/'payload').write_text('edited')
            self.receipt['files']['payload']={'bytes':6,'sha256':hashlib.sha256(b'edited').hexdigest()}
            (self.out/'terminal.json').write_bytes(S.encoded(self.receipt))
            with self.assertRaisesRegex(ValueError,'immutable terminal journal'):self.accepted()

    def test_self_asserted_approval_is_not_a_signature(self):
        self.admission.verify_signature=lambda *args:(_ for _ in ()).throw(ValueError('untrusted signature'))
        with self.assertRaisesRegex(ValueError,'signature'):self.accepted()



if __name__=='__main__':unittest.main()
