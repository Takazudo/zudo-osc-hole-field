"""Source-only local admission regressions: no Docker, systemd or approval issued."""
import concurrent.futures
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('local_admission_test', Path(__file__).with_name('local_native_admission.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
SHA = 'a' * 40
RUN = 'b' * 32


class LocalAdmission(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.cache = self.root / '.circuit-cache/run'
        self.cache.mkdir(parents=True)
        self.path = self.cache / 'request.json'
        self.approval = self.cache / 'approval.json'
        self.heavy = self.root / 'heavy-guard.sh'
        self.heavy.write_text('fixture guard')
        inputs = (*a.METHODS, 'design/spec/cells/test_sweep_precision_vendor.py',
                  'design/spec/cells/sweep_precision_vendor.py', 'design/spec/cells/_builder.py',
                  'design/spec/model_contracts.py', 'design/spec/modules/spice_trace.py',
                  '.circuit-cache/sources/opa197-model/SBOMA34D.ZIP',
                  '.circuit-cache/sources/opa197-model/OPAx197.LIB')
        for name in inputs:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('fixture ' + name)
        self.head = patch.object(a, 'clean_head', return_value=SHA)
        self.head.start()
        self.addCleanup(self.head.stop)
        guard_check = patch.object(a, 'check_shared_guard')
        guard_check.start()
        self.addCleanup(guard_check.stop)
        self.request = a.prepare(self.root, '.circuit-cache/run/request.json', 'oracle', RUN, 1,
                                 '.circuit-cache/run/guard.json', heavy_guard=self.heavy)

    def approve_fixture(self):
        # In-memory/unit-test fixtures only: no real checkout or operator receipt.
        return a.approve(self.root, self.path, a.sha(self.path), str(self.approval.relative_to(self.root)),
                         'unit-test fixture', 'fixture reservation', 'fixture qualification')

    def context(self):
        return {'EPIC242_ADMISSION_MODE': 'local', 'EPIC242_LOCAL_REQUEST': str(self.path.relative_to(self.root)),
                'EPIC242_PARENT_LOCAL_REQUEST_SHA256': a.sha(self.path),
                'EPIC242_LOCAL_APPROVAL': '.circuit-cache/run/approval.json',
                'EPIC242_LOCAL_APPROVAL_SHA256': a.sha(self.approval)}

    def mutate(self, **changes):
        value = a.read(self.path) | changes
        self.path.write_text(json.dumps(value))

    def prepare_annulus_fixture(self, **changes):
        for name in (a.ANNULUS_FIXTURE, a.ANNULUS_SCRIPT):
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('synthetic source ' + name)
        self.path = self.cache / 'annulus-request.json'
        args = dict(root=self.root, output='.circuit-cache/run/annulus-request.json',
                    kind='annulus-fixture', run_id=RUN, attempt=1,
                    evidence='.circuit-cache/run/annulus-guard.json', target='annulus',
                    heavy_guard=self.heavy)
        args.update(changes)
        self.request = a.prepare(**args)
        return self.request

    def test_annulus_fixture_preparation_is_exact_bounded_and_never_launches(self):
        with patch.object(a.subprocess, 'run') as launch, patch.object(a, 'approve') as approval:
            request = self.prepare_annulus_fixture()
        launch.assert_not_called(); approval.assert_not_called()
        self.assertEqual(request['command'], ['python3', a.ANNULUS_SCRIPT, 'worker', '--output',
                                             '.circuit-cache/run/annulus-guard.json.annulus'])
        self.assertEqual(request['seconds'], 60)
        self.assertEqual(request['limits'], a.LIMITS)
        self.assertEqual(set(request['input_sha256']), set(a.METHODS) | {a.ANNULUS_SCRIPT, a.ANNULUS_FIXTURE})
        self.assertLessEqual(len(request['worker']), 61)
        self.assertFalse(self.approval.exists())
        self.assertFalse(a.annulus_output(request, self.root).exists())
        self.assertEqual(a.validate_request(self.root, self.path), request)

    def test_annulus_fixture_rejects_stage_target_and_escaping_evidence(self):
        for changes in ({'target': 'KA-t2'}, {'target': 'annulus-fixture'},
                        {'stage': '.circuit-cache/run'}, {'stage': ''},
                        {'evidence': '/tmp/annulus.json'},
                        {'evidence': '.circuit-cache/../annulus.json'}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.prepare_annulus_fixture(**changes)
            self.assertFalse(self.path.exists())

    def test_annulus_fixture_input_and_output_command_tampering_refused(self):
        request = self.prepare_annulus_fixture()
        for name in (a.ANNULUS_FIXTURE, a.ANNULUS_SCRIPT, *a.METHODS):
            p = self.root / name; original = p.read_bytes()
            p.write_bytes(b'changed fixture or import')
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'sealed input'):
                a.validate_request(self.root, self.path)
            p.write_bytes(original)
        original = self.path.read_text()
        for changes in ({'command': request['command'][:-1] + ['.circuit-cache/other']},
                        {'seconds': 61}, {'stage': '.circuit-cache/run'},
                        {'input_sha256': {a.ANNULUS_FIXTURE: a.sha(self.root/a.ANNULUS_FIXTURE)}}):
            self.path.write_text(original); self.mutate(**changes)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                a.validate_request(self.root, self.path)
        self.path.write_text(original)

    def test_annulus_output_freshness_checked_at_prepare_execute_and_worker(self):
        output = self.cache / 'annulus-guard.json.annulus'
        output.mkdir()
        with self.assertRaisesRegex(ValueError, 'fresh annulus'):
            self.prepare_annulus_fixture()
        output.rmdir()
        request = self.prepare_annulus_fixture()
        env, proc, cg = self.worker_fixture()
        env['EPIC242_NATIVE_DEADLINE'] = str(int(time.time()) + 50)
        output.mkdir()
        with patch.object(a.subprocess, 'run') as launch:
            with self.assertRaisesRegex(ValueError, 'fresh annulus'):
                a.execute(self.root, self.path, self.approval, env={}, claims=self.root/'claims')
            with self.assertRaisesRegex(ValueError, 'fresh annulus'):
                a.worker(self.root, env, proc, cg)
        launch.assert_not_called(); self.assertFalse((self.root/'claims').exists())
        output.rmdir()
        with patch.object(a.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0)) as launch:
            self.assertEqual(a.worker(self.root, env, proc, cg), 0)
        self.assertEqual(launch.call_args.args[0], request['command'])

    def test_annulus_derived_output_symlink_and_request_alias_refused(self):
        output = self.cache / 'annulus-guard.json.annulus'
        output.symlink_to(self.root/'elsewhere')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            self.prepare_annulus_fixture()
        output.unlink()
        with self.assertRaisesRegex(ValueError, 'cannot occupy'):
            self.prepare_annulus_fixture(output='.circuit-cache/run/annulus-guard.json.annulus')
        self.assertFalse(output.exists())

    def test_startup_kinds_are_fixed_sixty_second_commands(self):
        for name in ('scripts/kicad/qualify_startup_handshake.py','scripts/kicad/settle_only_pilot.py'):
            (self.root/name).write_text('fixture source')
        for kind,argv in [('startup-success',['kicad-cli','version']),('startup-failure',['/bin/false'])]:
            result=a.prepare(self.root,'.circuit-cache/run/'+kind+'.json',kind,RUN,1,
                             '.circuit-cache/run/'+kind+'-guard.json',target=kind,heavy_guard=self.heavy)
            self.assertEqual(result['command'],['bash','scripts/kicad/run.sh',*argv])
            self.assertEqual(result['seconds'],60)
            self.assertEqual(result['worker'],'local-'+RUN+'-1-'+kind)
        with self.assertRaises(ValueError):
            a.prepare(self.root,'.circuit-cache/run/bad.json','startup-failure',RUN,1,
                      '.circuit-cache/run/bad-guard.json',target='arbitrary',heavy_guard=self.heavy)

    def test_startup_execution_verifies_complete_synthetic_guard_receipts(self):
        from scripts.kicad.test_qualify_startup_handshake import receipt as fixture_receipt
        import shutil
        for name in ('qualify_startup_handshake.py','settle_only_pilot.py'):
            shutil.copyfile(Path(__file__).with_name(name),self.root/'scripts/kicad'/name)
        for kind in ('startup-success','startup-failure'):
            self.path=self.cache/(kind+'.json');self.approval=self.cache/(kind+'-approval.json')
            self.request=a.prepare(self.root,str(self.path.relative_to(self.root)),kind,RUN,1,
                '.circuit-cache/run/'+kind+'-guard.json',target=kind,heavy_guard=self.heavy)
            self.approve_fixture()
            def launch(command, **kwargs):
                r=fixture_receipt(kind=='startup-failure');name=self.request['worker']
                slice_name='epic242-w'+name.encode().hex()+'.slice'
                r['plan'].update(worker=name,sha=SHA,hook_sha256=self.request['input_sha256']['scripts/kicad/run.sh'],
                    admission_id='local-'+RUN+'-1',command=command[command.index('--',3)+1:])
                for entry in r['container_admissions'].values():entry['request']['worker']=name
                for entry in r['container_memberships'].values():
                    entry.update(worker=name,cgroup='0::/epic242.slice/'+slice_name+'/docker.scope')
                    entry['host_config']['CgroupParent']=slice_name
                (self.root/self.request['evidence']).write_text(json.dumps(r))
                return subprocess.CompletedProcess(command,1 if kind=='startup-failure' else 0)
            with patch.object(a.subprocess,'run',side_effect=launch):
                self.assertEqual(a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims'),0)
            result=a.read(Path(str(self.root/self.request['evidence'])+'.qualification.json'))
            self.assertEqual(result['status'],'PASS BOUNDED STARTUP PHASE ONLY')
            self.assertEqual(result['guard_exit_code'],1 if kind=='startup-failure' else 0)

    def test_post_run_source_change_retains_failure_and_log(self):
        self.approve_fixture()
        def launch(command,**kwargs):
            (self.root/'scripts/kicad/native_start_gate.sh').write_text('changed while running')
            return subprocess.CompletedProcess(command,0)
        with patch.object(a.subprocess,'run',side_effect=launch):
            self.assertEqual(a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims'),1)
        result=a.read(next((self.root/'claims').glob('*.result')))
        self.assertEqual(result['exit_code'],0)
        self.assertFalse(result['post_run_inputs_unchanged'])
        self.assertTrue(Path(result['driver_log']).is_file())

    def test_interactive_auth_is_request_bound_and_requires_tty_before_claim(self):
        self.mutate(authentication='operator-pty')
        self.approve_fixture()
        with patch.object(a.os,'isatty',return_value=False),patch.object(a.subprocess,'run') as launch, self.assertRaisesRegex(ValueError,'terminal'):
            a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims')
        launch.assert_not_called();self.assertFalse((self.root/'claims').exists())

    def test_interactive_bridge_has_no_transcript_or_password_capture(self):
        self.mutate(authentication='operator-pty')
        self.approve_fixture()
        with patch.object(a.os,'isatty',return_value=True),patch.object(a.subprocess,'run',return_value=subprocess.CompletedProcess([],1)) as launch:
            self.assertEqual(a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims'),1)
        command=launch.call_args.args[0]
        self.assertEqual(command[:4],['bash',str(self.heavy),'--','/usr/bin/script'])
        self.assertIn('--return',command);self.assertIn('--echo=never',command)
        self.assertEqual(command[-1],'/dev/null')
        self.assertNotIn('stdout',launch.call_args.kwargs);self.assertNotIn('input',launch.call_args.kwargs)
        import shlex
        inner=shlex.split(command[command.index('--command')+1])
        self.assertEqual(inner[:2],['python3','scripts/kicad/operator_terminal.py'])
        self.assertEqual(inner[-1],str(self.approval.relative_to(self.root)))

    def test_prepare_does_not_approve_or_launch(self):
        self.assertFalse(self.approval.exists())
        self.assertEqual(self.request['command'], ['python3', '-m', 'unittest', a.ORACLE_TEST])
        self.assertEqual(self.request['seconds'], 1680)
        self.assertFalse(any('GITHUB' in key for key in self.request))
        with patch.object(a.subprocess, 'run') as launch:
            with self.assertRaises(FileNotFoundError):
                a.execute(self.root, self.path, self.approval, env={}, claims=self.root/'claims')
            launch.assert_not_called()

    def test_separate_operator_exact_digest_and_attestations_required(self):
        for digest, operator, reservation, qualifier in [('0'*64, 'owner', 'slot', 'proof'),
                (a.sha(self.path), '', 'slot', 'proof'), (a.sha(self.path), 'owner', '', 'proof'),
                (a.sha(self.path), 'owner', 'slot', '')]:
            with self.assertRaises(ValueError):
                a.approve(self.root, self.path, digest, '.circuit-cache/run/approval.json', operator, reservation, qualifier)
        self.assertFalse(self.approval.exists())

    def test_preparation_cannot_stand_in_for_approval(self):
        self.approval.write_text(self.path.read_text())
        with self.assertRaisesRegex(ValueError, 'operator approval'):
            a.validate_approval(self.root, self.approval, self.request, a.sha(self.path))

    def test_changed_head_hook_model_heavy_guard_and_checkout_refused(self):
        with patch.object(a, 'clean_head', return_value='c'*40), self.assertRaisesRegex(ValueError, 'source SHA'):
            a.validate_request(self.root, self.path)
        for p in (self.root/'scripts/kicad/run.sh', self.root/'.circuit-cache/sources/opa197-model/OPAx197.LIB', self.heavy):
            original = p.read_bytes()
            p.write_bytes(b'changed')
            with self.subTest(path=p), self.assertRaises(ValueError):
                a.validate_request(self.root, self.path)
            p.write_bytes(original)
        self.mutate(checkout='/another/checkout')
        with self.assertRaisesRegex(ValueError, 'checkout'):
            a.validate_request(self.root, self.path)

    def test_replay_ledger_cannot_move_to_tmp_or_change_with_home(self):
        expected=a.persistent_claim_directory()
        with patch.dict(os.environ,{'HOME':str(self.root/'other-home')}):
            self.assertEqual(a.persistent_claim_directory(),expected)
        self.mutate(claim_directory=str(self.root/'alternate-claims'))
        with self.assertRaisesRegex(ValueError,'fixed account'):
            a.validate_request(self.root,self.path)

    def test_command_deadline_limits_target_and_incomplete_seals_refused(self):
        original = self.path.read_text()
        changes = [{'command':['bash','arbitrary.sh']}, {'seconds':2580}, {'limits':{}},
                   {'target':'other'}, {'input_sha256':{}}, {'kind':'arbitrary'},
                   {'run_id':'a-b'}, {'attempt':True}]
        for change in changes:
            self.path.write_text(original)
            self.mutate(**change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                a.validate_request(self.root, self.path)

    def test_approval_is_exact_attempt_target_request_not_portable(self):
        approval = self.approve_fixture()
        for key in ('source_sha','run_id','attempt','target','request_sha256','worker'):
            changed = copy.deepcopy(approval)
            changed[key] = 'changed'
            self.approval.write_text(json.dumps(changed))
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'binding'):
                a.validate_approval(self.root, self.approval, self.request, a.sha(self.path))

    def test_paths_reject_escape_and_symlink(self):
        for name in ('../outside','/absolute','.circuit-cache/../escape','scripts/request.json'):
            with self.assertRaises(ValueError):
                a.local_path(self.root,name,cache=True)
        (self.cache/'link').symlink_to(self.root/'scripts')
        with self.assertRaisesRegex(ValueError,'symlink'):
            a.local_path(self.root,'.circuit-cache/run/link/file',cache=True)

    def test_missing_or_used_evidence_refuses_before_claim_and_launch(self):
        self.approve_fixture()
        for missing in (False, True):
            if missing:
                self.mutate(evidence='.circuit-cache/missing/guard.json')
                self.approval.unlink()
                self.approve_fixture()
            else:
                (self.cache/'guard.json').write_text('old evidence')
            with patch.object(a.subprocess,'run') as launch, self.assertRaises(ValueError):
                a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims')
            launch.assert_not_called()
        self.assertFalse((self.root/'claims').exists())

    def test_mixed_ci_local_and_changed_approval_digest_refused(self):
        self.approve_fixture()
        env = self.context()
        for key in a.CI_KEYS:
            with self.subTest(key=key), self.assertRaisesRegex(ValueError,'mixed'):
                a.authority(self.root,env|{key:'ci-value'})
        self.approval.write_text(self.approval.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'approval digest'):
            a.authority(self.root,env)

    def test_failed_launch_keeps_persistent_claim_and_replay_refuses(self):
        self.approve_fixture()
        with patch.object(a.subprocess,'run',return_value=subprocess.CompletedProcess([],1)) as launch:
            self.assertEqual(a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims'),1)
            cmd=launch.call_args.args[0]
            self.assertEqual(cmd[:3],['bash',str(self.heavy),'--'])
            self.assertIn('scripts/kicad/local_native_admission.py',cmd)
            self.assertEqual(cmd[-1],'worker')
            self.assertFalse(any('GITHUB_' in arg for arg in cmd))
            with self.assertRaises(ValueError):
                a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims')
            # Even if a disposable log is absent, the persistent claim survives.
            (self.cache/'guard.json.driver.log').unlink()
            with self.assertRaises(FileExistsError):
                a.execute(self.root,self.path,self.approval,env={},claims=self.root/'claims')
            self.assertEqual(launch.call_count,1)
        self.assertTrue(list((self.root/'claims').glob('*.json.result')))

    def test_concurrent_claim_permits_one_attempt(self):
        def attempt():
            try:
                a.claim(self.request,a.sha(self.path),self.root/'claims')
                return True
            except FileExistsError:
                return False
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(lambda _:attempt(),range(2))),1)

    def worker_fixture(self):
        self.approve_fixture()
        name=self.request['worker'];slice_name='epic242-w'+name.encode().hex()+'.slice'
        env=self.context()|{'EPIC242_NATIVE_WORKER':name,'EPIC242_NATIVE_SLICE':slice_name,
                           'EPIC242_NATIVE_DEADLINE':str(int(time.time())+1600)}
        proc=self.root/'proc';proc.write_text('0::/epic242.slice/'+slice_name+'/epic242-'+name+'-checks.service\n')
        cg=self.root/'cgroups'
        for p,cap in ((cg/'epic242.slice',12884901888),(cg/'epic242.slice'/slice_name,6442450944)):
            p.mkdir(parents=True,exist_ok=True);(p/'memory.max').write_text(str(cap));(p/'memory.swap.max').write_text('0')
        return env,proc,cg

    def test_worker_rechecks_authority_and_actual_cgroup_before_command(self):
        env,proc,cg=self.worker_fixture()
        with patch.object(a.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as launch:
            self.assertEqual(a.worker(self.root,env,proc,cg),0)
            self.assertEqual(launch.call_args.args[0],self.request['command'])
            proc.write_text('0::/unrelated.scope')
            with self.assertRaisesRegex(ValueError,'guarded service'):
                a.worker(self.root,env,proc,cg)
            self.assertEqual(launch.call_count,1)

    def test_worker_refuses_changed_input_while_waiting_in_queue(self):
        env,proc,cg=self.worker_fixture()
        (self.root/'.circuit-cache/sources/opa197-model/OPAx197.LIB').write_text('changed in queue')
        with patch.object(a.subprocess,'run') as launch, self.assertRaisesRegex(ValueError,'sealed input'):
            a.worker(self.root,env,proc,cg)
        launch.assert_not_called()

    def test_worker_no_swap_caps_and_deadline_not_caller_claims(self):
        env,proc,cg=self.worker_fixture()
        for change in ({'EPIC242_NATIVE_DEADLINE':str(int(time.time())-1)},
                       {'EPIC242_NATIVE_DEADLINE':str(int(time.time())+2580)},
                       {'EPIC242_NATIVE_WORKER':'ci-1-1-python'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                a.worker(self.root,env|change,proc,cg)
        (cg/'epic242.slice/memory.swap.max').write_text('max')
        with self.assertRaisesRegex(ValueError,'limits'):
            a.worker(self.root,env,proc,cg)


class SharedQueueChecks(unittest.TestCase):
    def test_nested_or_changed_queue_configuration_refused(self):
        for env in ({'HEAVY_GUARD_HELD':'1'}, {'HEAVY_GUARD_DIR':'/another/queue'},
                    {'HEAVY_GUARD_SLOTS':'2'}):
            with self.assertRaises(ValueError):
                a.check_shared_guard({'heavy_guard_environment':a.heavy_settings(env)},env)
        with self.assertRaisesRegex(ValueError,'configuration changed'):
            a.check_shared_guard({'heavy_guard_environment':{}},{'HEAVY_GUARD_MIN_MEM_MB':'4096'})

    def test_missing_backend_does_not_use_heavy_helper_fail_open(self):
        with patch.object(a.shutil,'which',return_value=None),self.assertRaisesRegex(ValueError,'backend'):
            a.check_shared_guard({'heavy_guard_environment':{}},{})


if __name__=='__main__':
    unittest.main()
