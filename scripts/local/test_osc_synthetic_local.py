import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'ci'))
import osc_candidate_check as c
import osc_synthetic_check as s
import osc_synthetic_local as l

GUARD={'HEAVY_GUARD_HELD':'1'}

def env(**extra):
    base={k:v for k,v in os.environ.items() if k not in ('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','CI','DOCKER_HOST','DOCKER_CONTEXT','HEAVY_GUARD_HELD','OSC_LOCAL_ADAPTER')}
    base.update(extra);return base

class LocalGate(unittest.TestCase):
    def test_constants_match_hosted(self):
        self.assertEqual(l.TOTAL,120);self.assertEqual(l.RESERVE,32);self.assertEqual(l.OUTER_STOP_SECONDS,120)
        self.assertEqual(l.STATUS,s.q.STATUS)
    def test_accepts_guarded_local(self):
        l.local_gate(env(**GUARD))
    def test_refuses_hosted_and_ci(self):
        for key in ('GITHUB_ACTIONS','RUNNER_ENVIRONMENT','CI'):
            with self.assertRaises(ValueError):l.local_gate(env(**GUARD,**{key:'true'}))
    def test_refuses_alternate_docker_endpoint(self):
        for key in ('DOCKER_HOST','DOCKER_CONTEXT'):
            with self.assertRaises(ValueError):l.local_gate(env(**GUARD,**{key:'x'}))
    def test_refuses_without_heavy_guard_slot(self):
        with self.assertRaises(ValueError):l.local_gate(env())
        with self.assertRaises(ValueError):l.local_gate(env(HEAVY_GUARD_HELD='0'))
        l.local_gate(env(),require_guard=False)
    def test_authorization_note(self):
        self.assertEqual(l.authorization('  user instruction 2026-10-23  '),'user instruction 2026-10-23')
        for bad in (None,'','short note','x'*501):
            with self.assertRaises(ValueError):l.authorization(bad)
    def test_image_identity_requires_pinned_digest(self):
        row={'Id':'sha256:'+'a'*64,'RepoDigests':[c.IMAGE],'Size':1}
        self.assertEqual(l.image_identity(json.dumps([row]))['id'],row['Id'])
        for bad in ([],[row,row],[{**row,'RepoDigests':['kicad/kicad@sha256:'+'b'*64]}],[{**row,'Id':'abc'}],{}):
            with self.assertRaises(ValueError):l.image_identity(json.dumps(bad))
    def test_state_dir_must_not_preexist(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):l.state_dir(t)
            p=l.state_dir(Path(t)/'state');self.assertTrue(p.is_dir())
            self.assertEqual(p.stat().st_mode&0o777,0o700)
    def test_adapter_requires_local_marker(self):
        with patch.dict(os.environ,env(),clear=True):
            with self.assertRaises(ValueError):l.adapter(['run'])
        for key in ('GITHUB_ACTIONS','CI','DOCKER_HOST'):
            with patch.dict(os.environ,env(OSC_LOCAL_ADAPTER='1',**{key:'x'}),clear=True):
                with self.assertRaises(ValueError):l.adapter(['run'])
        with patch.dict(os.environ,env(OSC_LOCAL_ADAPTER='1'),clear=True),patch.object(s,'adapter',return_value=0) as hosted:
            self.assertEqual(l.adapter(['run','--rm',c.IMAGE]),0)
            hosted.assert_called_once_with(['run','--rm',c.IMAGE])

class LocalRun(unittest.TestCase):
    def run_with(self,environment,source,out,state):
        args=l.parse(['run',str(source),str(out),'--state',str(state),'--authorization','offline unit test authorization note'])
        with patch.dict(os.environ,environment,clear=True),patch.object(c,'run_command') as runner,contextlib.redirect_stdout(io.StringIO()):
            code=l.run(args)
        return code,json.loads((out/'receipt.json').read_text()),runner
    def test_gate_failure_before_any_command(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'src';source.mkdir();out=Path(t)/'out';state=Path(t)/'state'
            code,receipt,runner=self.run_with(env(TOOLING_SHA='a'*40),source,out,state)
            self.assertEqual(code,1);self.assertEqual(receipt['status'],'FAILED')
            self.assertIn('heavy-guard',receipt['error']);self.assertEqual(receipt['commands'],[])
            runner.assert_not_called();self.assertFalse(state.exists())
            self.assertEqual(receipt['mode'],'LOCAL_WSL_CONTAINMENT');self.assertIs(receipt['hosted'],False)
            self.assertIs(receipt['full_board_executed'],False);self.assertIs(receipt['board_acceptance'],False)
    def test_source_allowlist_failure_before_docker(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'src';source.mkdir();(source/'extra').write_text('x');out=Path(t)/'out';state=Path(t)/'state'
            code,receipt,runner=self.run_with(env(TOOLING_SHA='a'*40,**GUARD),source,out,state)
            self.assertEqual(code,1);self.assertIn('allowlist',receipt['error']);runner.assert_not_called()
            self.assertEqual(receipt['authorization'],'offline unit test authorization note')
    def test_separate_output_required(self):
        with tempfile.TemporaryDirectory() as t:
            args=l.parse(['run',t,str(Path(t)/'out'),'--state',str(Path(t)/'s'),'--authorization','offline unit test authorization note'])
            with self.assertRaises(ValueError):l.run(args)

class OracleFailure(unittest.TestCase):
    def test_missing_receipt_reports_oracle_failure(self):
        with tempfile.TemporaryDirectory() as t:
            source=Path(t)/'src';(source/'scripts/kicad').mkdir(parents=True);out=Path(t)/'out';state=Path(t)/'state'
            for name in c.PINS:(source/name).write_text(name)
            pins={name:c.sha(source/name) for name in c.PINS}
            replies=[dict(failure=None,exit_code=0,output=c.SOURCE+'\n'),dict(failure=None,exit_code=0,output='"29.3.0"'),
                     dict(failure=None,exit_code=0,output='"unix:///var/run/docker.sock"'),dict(failure=None,exit_code=0,output='12000000000'),
                     dict(failure=None,exit_code=0,output=''),dict(failure=None,exit_code=0,output=json.dumps([{'Id':'sha256:'+'a'*64,'RepoDigests':[c.IMAGE],'Size':1}])),
                     dict(failure=None,exit_code=1,output='Unable to start the pinned KiCad Docker oracle\n')]
            meminfo='MemTotal:       12000000 kB\nMemAvailable:   10000000 kB\n'
            args=l.parse(['run',str(source),str(out),'--state',str(state),'--authorization','offline unit test authorization note'])
            with patch.dict(os.environ,env(TOOLING_SHA='a'*40,**GUARD),clear=False),patch.object(c,'PINS',pins),patch.object(c,'run_command',side_effect=replies),\
                 patch.object(l,'host_meminfo',return_value=meminfo),patch.object(l.shutil,'which',return_value='/usr/bin/docker'),contextlib.redirect_stdout(io.StringIO()):
                code=l.run(args)
            receipt=json.loads((out/'receipt.json').read_text())
            self.assertEqual(code,1);self.assertIn('Docker operation failed',receipt['error']);self.assertIn('receipt missing',receipt['receipt_parse_error'])
            self.assertFalse((out/'synthetic.json').exists());self.assertEqual(receipt['cleanup'],[])

class PostStopCleanup(unittest.TestCase):
    def cleanup_with(self,state,out,side_effect=None):
        args=l.parse(['cleanup',str(state),str(out)])
        with patch.object(c,'run_command',side_effect=side_effect) as runner,contextlib.redirect_stdout(io.StringIO()):
            code=l.cleanup(args)
        return code,json.loads((out/'post-stop-cleanup.json').read_text()),runner
    def test_no_records_is_complete(self):
        with tempfile.TemporaryDirectory() as t:
            state=Path(t)/'state';state.mkdir();out=Path(t)/'out'
            code,record,runner=self.cleanup_with(state,out)
            self.assertEqual(code,0);self.assertEqual(record['status'],'COMPLETE');self.assertEqual(record['outcomes'],[])
            self.assertEqual(record['remaining_records'],[]);runner.assert_not_called()
    def test_missing_state_fails_closed(self):
        with tempfile.TemporaryDirectory() as t:
            code,record,runner=self.cleanup_with(Path(t)/'absent',Path(t)/'out')
            self.assertEqual(code,1);self.assertIn('state directory missing',record['error']);self.assertIsNone(record['remaining_records'])
    def test_uncertain_create_fails_closed_and_keeps_record(self):
        with tempfile.TemporaryDirectory() as t:
            state=Path(t)/'state';state.mkdir();out=Path(t)/'out';owner='a'*32
            (state/('owned-'+owner+'.json')).write_text(json.dumps({'owner':owner,'name':'osc-smoke-'+owner,'cid':None}))
            code,record,runner=self.cleanup_with(state,out,side_effect=[dict(failure=None,exit_code=0,output='')])
            self.assertEqual(code,1);self.assertIn('uncertain',record['error'])
            self.assertEqual(record['remaining_records'],['owned-'+owner+'.json'])
    def test_orphaned_container_removed(self):
        with tempfile.TemporaryDirectory() as t:
            state=Path(t)/'state';state.mkdir();out=Path(t)/'out';owner='a'*32;cid='b'*64
            (state/('owned-'+owner+'.json')).write_text(json.dumps({'owner':owner,'name':'osc-smoke-'+owner,'cid':cid}))
            info=[{'Id':cid,'Name':'/osc-smoke-'+owner,'Config':{'Labels':{'osc.smoke.owner':owner}},'State':{'Running':True,'ExitCode':0}}]
            replies=[dict(failure=None,exit_code=0,output=cid),dict(failure=None,exit_code=0,output=json.dumps(info)),
                     dict(failure=None,exit_code=0,output=cid),dict(failure=None,exit_code=0,output='')]
            code,record,runner=self.cleanup_with(state,out,side_effect=replies)
            self.assertEqual(code,0);self.assertEqual(record['outcomes'][0]['status'],'REMOVED_CONFIRMED')
            self.assertEqual(record['remaining_records'],[]);self.assertIn('rm',runner.call_args_list[2].args[0])

class PayloadFailureReceipt(unittest.TestCase):
    def test_oversized_events_still_yield_failed_receipt(self):
        events=[{'stage':'loaded','monotonic_seconds':1.0,'observation':'x'*120000}]
        with contextlib.redirect_stdout(io.StringIO()) as captured:s.q.emit_failed(events,'ValueError: receipt bound')
        receipt=json.loads(captured.getvalue().strip().splitlines()[-1])
        self.assertEqual(receipt['status'],'FAILED');self.assertIn('receipt fallback',receipt['error'])
        self.assertEqual(receipt['events'],[{'stage':'loaded','monotonic_seconds':1.0}]);self.assertIs(receipt['board_acceptance'],False)
    def test_small_failure_keeps_full_events(self):
        events=[{'stage':'versions','cli':'10.0.6','monotonic_seconds':1.0}]
        with contextlib.redirect_stdout(io.StringIO()) as captured:s.q.emit_failed(events,'ValueError: x')
        self.assertEqual(json.loads(captured.getvalue().strip().splitlines()[-1])['events'],events)

class Wrapper(unittest.TestCase):
    def test_outer_stop_contract(self):
        text=(Path(__file__).with_name('osc_synthetic_local.sh')).read_text()
        self.assertIn('outer_stop_seconds=120',text);self.assertIn('kill -KILL -- "-$pid"',text);self.assertNotIn('ps -o pgid',text)
        self.assertIn('TOOLING_SHA=$(git -C "$script_dir" rev-parse HEAD)',text)
        self.assertIn('setsid python3 -B',text);self.assertIn('osc_synthetic_local.py" cleanup',text)
        self.assertIn('HEAVY_GUARD_HELD',text);self.assertNotIn('GITHUB_ACTIONS=',text);self.assertNotIn('RUNNER_ENVIRONMENT=',text)
    def test_no_hosted_spoof_in_adapter_source(self):
        text=Path(l.__file__).read_text()
        self.assertNotIn("environ['GITHUB_ACTIONS']=",text);self.assertNotIn('RUNNER_ENVIRONMENT=',text);self.assertNotIn('docker pull',text)
        self.assertNotIn("'pull'",text)

if __name__=='__main__':unittest.main()
