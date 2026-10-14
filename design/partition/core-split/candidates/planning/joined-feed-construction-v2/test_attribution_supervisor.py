"""Synthetic subprocess/transport failures; never production data or cgroups."""
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import attribution_supervisor as S
import attribution_transport as T

SUCCESS = '''
from pathlib import Path
import hashlib,json
p=Path('result');p.mkdir()
data=b'{"component":"tiny"}\\n'
(p/'components.jsonl').write_bytes(data)
r={'status':'COMPLETE','components_sha256':hashlib.sha256(data).hexdigest(),
   'electrical_acceptance':False,'whole_board_acceptance':False,'adopted':False}
(p/'terminal.json').write_text(json.dumps(r))
'''


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='e16-supervisor-fixture-',dir='/tmp'))
        self.root.rmdir()

    def tearDown(self):
        if self.root.exists():shutil.rmtree(self.root)

    def run_child(self, code, **kwargs):
        return S.supervise([sys.executable,'-c',code],self.root,
                           started=time.monotonic(),seconds=3.,cleanup_seconds=1.5,
                           containment=S.FixtureContainment(self.root),**kwargs)

    def test_complete_requires_supervisor_hash_and_cleanup(self):
        record=self.run_child(SUCCESS+'\nprint("fixture only")')
        self.assertEqual(record['status'],'COMPLETE')
        self.assertTrue(record['fixture_only'])
        self.assertTrue(record['cleanup_complete'])
        self.assertFalse((self.root/'.work.partial/result/terminal.json').exists())
        self.assertTrue((self.root/'.work.partial/result/terminal.worker-unaccepted.json').exists())
        total=sum(p.stat().st_size for p in self.root.rglob('*') if p.is_file())
        self.assertLessEqual(total,S.OUTPUT_MAX)
        self.assertEqual(record['retained_bytes_before_receipt']+ (self.root/'terminal.json').stat().st_size,total)

    def test_actual_bounded_lifecycle_pipeline_under_supervisor(self):
        # The fixed child creates only the original tiny test mesh. It invokes
        # the real admission-core/claim/decoder/numerical/output pipeline, not a
        # mocked success marker or a production artifact path.
        source=str(Path(__file__).resolve().parent)
        code="""
import hashlib,json,os,sys,time
from pathlib import Path
sys.path.insert(0,SOURCE)
import attribution_lifecycle as L
import attribution_reconstruction as C
import attribution_transport as T
from test_attribution_executor import packet
root=Path(os.environ['E16_SUPERVISOR_WORK'])
p,ops,_,_=packet(root)
C.check_fixture_size(ops)
del ops
p['source_bindings']=L.source_bindings()
r={'fixture_only':True,'limits':L.LIMITS,'operation':'e16-selected-attribution-v1',
   'run_id':'8'*32,'attempt':1,'source_bindings':p['source_bindings'],
   'packet':p,'output':os.environ['E16_SUPERVISOR_RESULT']}
digest=hashlib.sha256(T.canonical(r)).hexdigest()
evidence={'request_sha256':digest,'run_id':r['run_id'],'limits':L.LIMITS,
          'expires_unix':time.time()+30,'fixture_only':True,'exclusive':True}
index={str(Path(b['path']).resolve()):b['sha256'] for b in L.artifact_bindings(p)}
remaining=float(os.environ['E16_WORK_DEADLINE'])-time.monotonic()
assert remaining>0
budget=T.Budget(seconds=min(180,remaining),output_bytes=int(os.environ['E16_OUTPUT_LIMIT']))
result=L._once(r,digest,index,root/'claims',evidence,evidence,budget)
assert result['status']=='COMPLETE'
print(json.dumps({'fixture_only':True,'rows':result['component_rows']}))
""".replace('SOURCE',repr(source))
        record=S.supervise([sys.executable,'-c',code],self.root,started=time.monotonic(),
            seconds=6.,cleanup_seconds=2.,containment=S.FixtureContainment(self.root))
        self.assertEqual(record['status'],'COMPLETE',record['reason'])
        result=json.loads((self.root/'.work.partial/result/terminal.worker-unaccepted.json').read_text())
        self.assertEqual(result['component_rows'],5)
        self.assertIn('KA',result['summary']['boards'])
        self.assertEqual(len(result['summary']['boards']['KA']['source_reactions_A']),3)
        self.assertTrue((self.root/'.work.partial/claims'/('8'*32+'.json')).is_file())
        self.assertTrue(any(name.startswith('.work.partial/claims/') for name in record['files']))
        self.assertFalse(result['summary']['production_evidence'])

    def test_partial_output_never_complete(self):
        record=self.run_child("from pathlib import Path;Path('components.partial').write_text('partial')")
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertTrue(record['cleanup_complete'])

    def test_bad_component_binding_rejected(self):
        record=self.run_child(SUCCESS+"\nfrom pathlib import Path;Path('result/components.jsonl').write_text('changed')")
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertIn('digest mismatch',record['reason'])

    def test_nonzero_exit_revokes_worker_success(self):
        record=self.run_child(SUCCESS+'\nraise SystemExit(9)')
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertEqual(record['worker_exit'],9)
        self.assertFalse((self.root/'.work.partial/result/terminal.json').exists())

    def test_timeout_revokes_early_success_and_cleans_process_group(self):
        record=S.supervise([sys.executable,'-c',SUCCESS+'\nimport time;time.sleep(30)'],self.root,
            started=time.monotonic(),seconds=2.,cleanup_seconds=1.8,
            containment=S.FixtureContainment(self.root))
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertIn('TIMEOUT',record['reason'])
        self.assertTrue(record['cleanup_complete'])
        self.assertLess(record['elapsed_seconds'],2.)
        self.assertFalse((self.root/'.work.partial/result/terminal.json').exists())

    def test_cancel_revokes_success(self):
        start=time.monotonic()
        record=self.run_child(SUCCESS+'\nimport time;time.sleep(30)',cancelled=lambda:time.monotonic()-start>.2)
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertIn('CANCELLED',record['reason'])
        self.assertTrue(record['cleanup_complete'])

    def test_oom_event_is_terminal_despite_worker_zero_exit(self):
        record=S.supervise([sys.executable,'-c',SUCCESS],self.root,
            started=time.monotonic(),seconds=3.,cleanup_seconds=1.5,
            containment=S.FixtureContainment(self.root,pretend_oom=True))
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertEqual(record['reason'],'worker OOM')

    def test_log_quota_is_bounded_and_preserves_negative_receipt(self):
        record=self.run_child('import os\nwhile True:os.write(1,b"x"*65536)')
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertIn('log quota',record['reason'])
        self.assertEqual((self.root/'worker.log.partial').stat().st_size,S.LOG_RESERVE)
        self.assertLess((self.root/'terminal.json').stat().st_size,S.RECEIPT_RESERVE)

    def test_duplicate_output_refused_before_launch(self):
        self.run_child(SUCCESS)
        with self.assertRaises(FileExistsError):self.run_child(SUCCESS)

    def test_symlink_output_never_accepted(self):
        record=self.run_child(SUCCESS+"\nfrom pathlib import Path;Path('escape').symlink_to('/etc/passwd')")
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertIn('nonregular output',record['reason'])

    def test_launch_failure_has_negative_receipt(self):
        record=S.supervise(['/definitely/no/e16-fixture-worker'],self.root,
            started=time.monotonic(),seconds=3.,cleanup_seconds=1.5,
            containment=S.FixtureContainment(self.root))
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertNotEqual(record['worker_exit'],0)

    def test_supervisor_spawn_failure_has_negative_receipt(self):
        with patch.object(S.subprocess,'Popen',side_effect=OSError('fixture spawn failure')):
            record=self.run_child(SUCCESS)
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertIsNone(record['worker_exit'])

    def test_missing_production_guard_refuses_without_launch(self):
        self.root.mkdir();work=self.root/'.work.partial';work.mkdir()
        containment=S.LinuxContainment('/sys/fs/cgroup/e16-absent','/sys/fs/cgroup/e16-absent/worker',work,'0'*64)
        with patch.object(S.subprocess,'Popen',side_effect=AssertionError('must not launch')) as launch:
            record=S.supervise([sys.executable,'-c',SUCCESS],self.root,
                              started=time.monotonic(),containment=containment)
        launch.assert_not_called()
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertFalse(record['fixture_only'])

    def test_log_fsync_failure_retains_negative_receipt_and_revokes_success(self):
        original=S.os.fsync
        calls=[]
        def fsync(fd):
            calls.append(fd)
            if len(calls)==1:raise OSError('fixture log fsync failure')
            return original(fd)
        with patch.object(S.os,'fsync',side_effect=fsync):
            record=self.run_child(SUCCESS)
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertIn('log finalization',record['reason'])
        self.assertTrue(record['worker_marker_revoked'])
        self.assertFalse((self.root/'.work.partial/result/terminal.json').exists())
        self.assertEqual(json.loads((self.root/'terminal.json').read_text())['status'],'INCOMPLETE')

    def test_worker_marker_rename_failure_is_recorded(self):
        original=Path.rename
        def rename(path,target):
            if path.name=='terminal.json':raise OSError('fixture marker rename failure')
            return original(path,target)
        with patch.object(Path,'rename',rename):
            record=self.run_child(SUCCESS)
        self.assertEqual(record['status'],'INCOMPLETE')
        self.assertFalse(record['worker_marker_revoked'])
        self.assertIn('marker revocation',record['reason'])

    def test_prior_claim_bytes_are_retained_in_quota_accounting(self):
        record=self.run_child(SUCCESS,prior_output_bytes=1234)
        self.assertEqual(record['prior_output_bytes'],1234)
        self.assertEqual(record['status'],'COMPLETE')

    def test_expired_guard_timestamp_refuses_before_output(self):
        with self.assertRaisesRegex(ValueError,'guard-entry'):
            S.supervise([sys.executable,'-c',SUCCESS],self.root,started=time.monotonic()-181,
                        containment=S.FixtureContainment(self.root))
        self.assertFalse(self.root.exists())


class TransportFailureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='e16-supervisor-fixture-',dir='/tmp')
        self.root=Path(self.temp.name)/'out'

    def tearDown(self):self.temp.cleanup()

    def test_large_success_summary_keeps_failure_reserve(self):
        budget=T.Budget(output_bytes=T.RECEIPT_RESERVE+1024)
        output=T.Output(self.root,budget)
        output.row({'x':1})
        with self.assertRaisesRegex(ValueError,'quota'):
            output.finish({'large':'x'*4096})
        receipt=output.fail('summary over quota')
        self.assertEqual(receipt['status'],'INCOMPLETE')
        self.assertLessEqual(sum(p.stat().st_size for p in self.root.iterdir()),budget.limit)

    def test_failure_after_success_revokes_component_name(self):
        output=T.Output(self.root,T.Budget())
        output.row({'x':1});output.finish({'fixture_only':True})
        output.fail('late cleanup error')
        self.assertFalse((self.root/'components.jsonl').exists())
        self.assertTrue((self.root/'components.partial').exists())
        self.assertEqual(json.loads((self.root/'terminal.json').read_text())['status'],'INCOMPLETE')

    def test_failure_is_idempotent_and_does_not_recharge(self):
        budget=T.Budget();output=T.Output(self.root,budget)
        first=output.fail('interrupted');used=budget.used
        self.assertEqual(output.fail('interrupted again'),first)
        self.assertEqual(budget.used,used)

    def test_output_parent_symlink_refused(self):
        link=Path(self.temp.name)/'link';link.symlink_to(Path(self.temp.name),target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'canonical'):
            T.Output(link/'out',T.Budget())

    def test_fsync_failure_stays_partial_and_has_negative_receipt(self):
        output=T.Output(self.root,T.Budget());output.row({'x':1})
        with patch.object(T.os,'fsync',side_effect=OSError('fixture fsync failure')):
            with self.assertRaises(OSError):output.finish({})
        output.fail('fsync failed')
        self.assertTrue((self.root/'components.partial').exists())
        self.assertEqual(json.loads((self.root/'terminal.json').read_text())['status'],'INCOMPLETE')


if __name__=='__main__':unittest.main()
