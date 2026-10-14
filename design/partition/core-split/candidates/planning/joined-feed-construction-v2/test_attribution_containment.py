"""Key-free boundary tests; real-host evidence is retained separately."""
import array,fcntl,hashlib,json,os,socket
from pathlib import Path
import tempfile,time,unittest
from unittest.mock import patch
import attribution_containment as C
import attribution_host as H
import attribution_admission as A

class EnvelopeTests(unittest.TestCase):
    def test_actual_socket_custody_rejects_wrong_peer_payload_and_reopened_fd(self):
        for case in ('valid','peer','digest','extra','reopened'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as d:
                root=Path(d);guard=root/'.agent-guard/heavy';guard.mkdir(parents=True)
                (guard/'slot-0.info').write_text(f'pid={os.getpid()} started=0 cwd=fixture')
                lock=guard/'slot-0.lock';lock.touch();held=os.open(lock,os.O_RDONLY)
                fcntl.flock(held,fcntl.LOCK_EX|fcntl.LOCK_NB)
                reopened=os.open(lock,os.O_RDONLY);sender,receiver=socket.socketpair(socket.AF_UNIX,socket.SOCK_SEQPACKET)
                message={'request_sha256':'b'*64,'run_id':'a'*32,'guard_pid':os.getpid(),
                         'guard_start':C.process_start(os.getpid())}
                if case=='digest':message['request_sha256']='c'*64
                fds=[reopened] if case=='reopened' else ([held,held] if case=='extra' else [held])
                sender.sendmsg([A.canon(message)],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',fds))])
                channel=receiver.detach();before=len(list(Path('/proc/self/fd').iterdir()))
                try:
                    with patch.object(A,'account_home',return_value=root),patch.object(C,'properties',return_value={'MainPID':str(1 if case=='peer' else os.getpid())}),patch.dict(os.environ,{'E16_GUARD_CHANNEL_FD':str(channel)}):
                        if case=='valid':
                            fd=C.receive_guard_custody({'run_id':'a'*32},'b'*64,time.monotonic()+1)
                            from numerical_unit_guard import prove_inherited_lock
                            prove_inherited_lock(fd,lock);os.close(fd)
                        else:
                            with self.assertRaises((ValueError,SystemExit)):
                                C.receive_guard_custody({'run_id':'a'*32},'b'*64,time.monotonic()+1)
                    self.assertEqual(len(list(Path('/proc/self/fd').iterdir())),before-1)
                finally:
                    sender.close();os.close(reopened);os.close(held)

    def test_exact_command_is_async_notify_and_binds_caps(self):
        r={'run_id':'a'*32,'checkout':'/tmp/fixture'}
        args=H.fixed_arguments('/tmp/request','b'*64,'/tmp/auth','/tmp/res')
        cmd=C.command(r,args,123,'456')
        for word in ('--no-block','--service-type=notify','NotifyAccess=main','DelegateSubgroup=bootstrap',
                     'MemoryMax=2080374784','MemorySwapMax=0','RuntimeMaxSec=174s',
                     'KillMode=control-group','Restart=no','TimeoutStopSec=1s'):
            self.assertIn(word,cmd)
        self.assertNotIn('--wait',cmd)
        unset=next(x for x in cmd if x.startswith('UnsetEnvironment='))
        for key in ('LD_PRELOAD','LD_AUDIT','GLIBC_TUNABLES','LD_PREFER_MAP_32BIT_EXEC','PYTHONPATH'):
            self.assertIn(key,unset.split('=',1)[1].split())
        self.assertEqual(C.ROOT_MEMORY+C.EXTERNAL_RESERVE,2*1024**3)
        self.assertEqual(C.BOOTSTRAP_MEMORY+C.CONTROL_MEMORY+H.S.ACTIVE_SCOPE_MEMORY,C.ROOT_MEMORY)
        self.assertEqual(H.S.WORKER_MEMORY,1216*1024**2)

    def test_description_digest_binds_containment_choice(self):
        r={key:{} for key in ('authorization_policy','operation','limits','environment_policy','source_bindings','source_tree','toolchain','packet','host_limits','guard_sha256')}
        r['host_limits']=H.HOST_LIMITS.copy();before=A.operation_digest(r)
        r['host_limits']['outside_swap_contract']='host-SwapTotal-zero'
        self.assertNotEqual(before,A.operation_digest(r))

    def test_no_migration_or_swap_sample_can_replace_root_limit(self):
        with tempfile.TemporaryDirectory() as d:
            r={'run_id':'a'*32};root=Path(d)/C.unit_name(r);root.mkdir()
            for name,value in {'memory.max':str(C.ROOT_MEMORY),'memory.swap.max':'max','memory.swap.current':'0','pids.max':'48'}.items():(root/name).write_text(value)
            with self.assertRaisesRegex(ValueError,'hard limits'):C.verify_root(root,r)
            (root/'memory.swap.max').write_text('0');C.verify_root(root,r)

    def test_rejects_controller_outside_actual_group(self):
        with patch.object(C,'own_group',return_value=Path('/sys/fs/cgroup/other')):
            with self.assertRaisesRegex(ValueError,'escaped'):
                C.prove({'run_id':'a'*32},'b'*64,time.monotonic(),time.monotonic()+180)

    def test_guard_tail_scan_keeps_historical_and_selected_bounds_distinct(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ledger=root/'.agent-guard/heavy/runs.jsonl';ledger.parent.mkdir(parents=True)
            old=A.canon({'label':'old '+'x'*4500})
            current=A.canon({'label':'exact','cwd':'/fixture','ts':1001,'verdict':'PASS','exit':0,'min_mem_mb':2000})
            ledger.write_bytes(old+current)
            with patch.object(A,'account_home',return_value=root):
                self.assertEqual(C.guard_row({'checkout':'/fixture'},'exact',1000,time.monotonic()+1),hashlib.sha256(current).hexdigest())
                ledger.write_bytes(old+current+current)
                with self.assertRaisesRegex(ValueError,'ambiguous'):
                    C.guard_row({'checkout':'/fixture'},'exact',1000,time.monotonic()+1)

    def test_unsigned_fixture_is_refused_before_service_operations(self):
        with patch.object(H,'read_small',return_value={'fixture_only':True}),patch.object(C,'setup') as setup:
            with self.assertRaisesRegex(ValueError,'fixture|unbound'):
                C.outer('/unused','a'*64,'/unused','/unused',1,'1')
        setup.assert_not_called()

    def test_setup_refusal_has_bounded_negative_evidence(self):
        r={'schema':'e16-attribution-request-v1','run_id':'a'*32}
        digest=hashlib.sha256(A.canon(r)).hexdigest()
        with tempfile.TemporaryDirectory() as d,patch.object(A,'state_directory',return_value=Path(d)),patch.object(H,'read_small',return_value=r),patch.object(C,'_outer',side_effect=PermissionError('fixture delegation denied')):
            self.assertEqual(C.outer('/unused',digest,'/unused','/unused',1,'1'),1)
            record=A.read_json(C.receipt_path(r))
            self.assertEqual(record['status'],'INCOMPLETE')
            self.assertFalse(record['cleanup_complete'])
            self.assertIn('fixture delegation denied',record['reason'])
            before=C.receipt_path(r).read_bytes()
            C.outer('/unused',digest,'/unused','/unused',1,'1')
            self.assertEqual(before,C.receipt_path(r).read_bytes())

    def test_pid_start_identity_not_pid_only(self):
        self.assertIsNotNone(C.process_start(os.getpid()))
        self.assertIsNone(C.process_start(2147483647))

    def test_receipt_checks_all_acceptance_flags(self):
        r={'run_id':'a'*32,'host_limits':H.HOST_LIMITS};record={'request_sha256':'b'*64,'run_id':'a'*32,'contract':C.CONTRACT,
            'status':'COMPLETE','cleanup_complete':True,'electrical_acceptance':False,'whole_board_acceptance':True,'adopted':False}
        with patch.object(A,'read_json',return_value=record):
            with self.assertRaisesRegex(ValueError,'incomplete'):
                C.accepted(r,'b'*64,'c'*64)

    def test_process_is_not_moved_by_properties_only(self):
        with patch.object(C,'own_group',return_value=Path('/wrong')),patch.object(C,'verify_root'):
            with self.assertRaisesRegex(ValueError,'placement'):
                C.setup(Path('/fixture'),{'run_id':'a'*32})

if __name__=='__main__':unittest.main()
