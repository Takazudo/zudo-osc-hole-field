import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import unittest
import sys
from unittest.mock import patch
import osc_fill_check as f

class FillController(unittest.TestCase):
    def test_failure_json_cleanup_and_global_restore(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t)/'source';root.mkdir();out=Path(t)/'out';state=Path(t)/'state';state.mkdir()
            before_pins,before_deadline=f.c.PINS,f.c.DEADLINE
            results=[{'failure':None,'exit_code':0,'output':f.c.SOURCE},
                {'failure':None,'exit_code':0,'output':'"unix:///var/run/docker.sock"'},
                {'failure':None,'exit_code':0,'output':''},
                *[{'failure':None,'exit_code':0,'output':'10.0.6'}]*2,
                {'failure':None,'exit_code':1,'output':'{"status":"FAILED","failure":{"phase":"fill"}}'}]
            calls=[]
            def cleanup(*args,**kwargs):
                calls.append(1)
                if len(calls)>=3: raise ValueError('cleanup failure preserved')
            with patch.object(sys,'argv',['osc_fill_check.py',str(root),str(out)]),patch.dict(os.environ,{'TOOLING_SHA':'a'*40,'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted'}),patch.object(f.c,'snapshot',return_value={'p':'h'}),patch.object(f.c,'run_command',side_effect=results) as runner,patch.object(f.shutil,'which',return_value='/docker'),patch.object(f.tempfile,'mkdtemp',return_value=str(state)),patch.object(f.c,'cleanup_owned',side_effect=cleanup),patch.object(f.c,'normal_exit'):
                self.assertEqual(f.main(),1)
                self.assertEqual(runner.call_args_list[3].args[3]['GITHUB_ACTIONS'],'true')
                self.assertEqual(runner.call_args_list[3].args[3]['RUNNER_ENVIRONMENT'],'github-hosted')
            self.assertEqual(json.loads((out/'fill.json').read_text())['status'],'FAILED')
            receipt=json.loads((out/'receipt.json').read_text())
            self.assertIn('cleanup failure',receipt['cleanup_error']);self.assertEqual(len(calls),4)
            self.assertIs(f.c.PINS,before_pins);self.assertEqual(f.c.DEADLINE,before_deadline)
    def test_summary_excludes_drc_samples(self):
        s=json.loads(f.summary_for({'status':'FAILED','cleanup':[]},{'drc':{'before':{'x':1},'after':{'x':2},'delta':{'added':{'count':1,'sample':'x'*20000}}}}))
        self.assertEqual(s['drc_delta_counts'],{'added':1});self.assertNotIn('sample',json.dumps(s))
    def test_summary_preserves_partial_drc_and_phases(self):
        detail={'drc_counts':{'before':{'x':2}},'drc_checkpoints':{'drc-before':{'report_sha256':'a'*64,'report_bytes':10,'counts':{'x':2},'identities':{'sample':'private'}}},'phase_results':[{'phase':'fill','status':'FAILED'}]}
        s=json.loads(f.summary_for({'status':'FAILED'},detail))
        self.assertEqual(s['drc_checkpoint_counts'],{'before':{'x':2}})
        self.assertEqual(s['drc_checkpoints']['drc-before']['report_sha256'],'a'*64)
        self.assertEqual(s['phase_results'],detail['phase_results']);self.assertNotIn('private',json.dumps(s))
    def test_summary_preserves_command_failure_outcome(self):
        row={'phase':'fill','status':'FAILED','error':'phase timeout','start_monotonic_seconds':1,'end_monotonic_seconds':2,'deadline_monotonic_seconds':2,'elapsed_seconds':1,'argv':['private']}
        s=json.loads(f.summary_for({'status':'FAILED'},{'commands':[row]}))
        self.assertEqual(s['command_outcomes'][0],{k:v for k,v in row.items() if k!='argv'})
    def args(self):
        return ['run','--rm','--network','none','--volume','/source:/work','--volume','/tmp/home:/tmp/kicad-home',f.c.IMAGE]
    def test_minimal_readonly_mounts(self):
        a=f.readonly_args(self.args(),PurePosixPath('/source'),PurePosixPath('/bundle'))
        mounts=[a[i+1] for i,x in enumerate(a[:-1]) if x=='--volume']
        self.assertEqual(mounts,['/source:/work:ro','/bundle:/analysis:ro'])
        self.assertNotIn('/tmp/home:/tmp/kicad-home',a)
        self.assertIn('--read-only',a)
        self.assertIn('/scratch:rw,nosuid,nodev,noexec,size=256m,mode=1777',a)
        self.assertIn('/tmp:rw,nosuid,nodev,noexec,size=32m,mode=1777',a)
    def test_extra_mounts_fail(self):
        for extra in (['-v','/evil:/x'],['--mount=type=bind'],['--tmpfs','/extra'],['--read-only']):
            with self.assertRaises(ValueError): f.readonly_args(self.args()+extra,PurePosixPath('/source'),PurePosixPath('/bundle'))
    def workflow(self):
        return json.loads((Path(__file__).resolve().parents[2]/'.github/workflows/osc-candidate-check.yml').read_text())
    def test_wiring(self):
        w=self.workflow();self.assertEqual(w['permissions'],{'contents':'read'})
        self.assertEqual(w['on']['workflow_dispatch']['inputs']['mode']['default'],'smoke')
        j=next(iter(w['jobs'].values()));self.assertEqual(j['timeout-minutes'],20)
        steps=j['steps'];sparse=steps[1]['with']['sparse-checkout'].splitlines()
        for p in Path(__file__).parent.glob('*.py'):
            self.assertIn('/scripts/ci/'+p.name,sparse)
        for suffix in ('pro','dru'):
            self.assertIn("inputs.mode == 'fill' && '/boards/osc-core/osc-core.kicad_"+suffix+"'",steps[2]['with']['sparse-checkout'])
        self.assertIn('osc_fill_check.py frozen fill-receipts',steps[4]['run'])
    def test_artifact_policy(self):
        script=next(iter(self.workflow()['jobs'].values()))['steps'][-2]['run'].split('\n',1)[1].rsplit('\nPY',1)[0]
        for bad in (False,True):
            with tempfile.TemporaryDirectory() as t:
                old=Path.cwd()
                try:
                    os.chdir(t);Path('receipts').mkdir();Path('receipts/receipt.json').write_text('{}')
                    Path('fill-receipts').mkdir();Path('fill-receipts/receipt.json').write_text('{}');Path('fill-receipts/fill.json').write_text('{}')
                    if bad:Path('fill-receipts/board.kicad_pcb').write_text('forbidden')
                    with patch.dict(os.environ,{'OSC_MODE':'fill'}):
                        if bad:
                            with self.assertRaises(SystemExit):exec(script,{})
                        else:exec(script,{})
                    if not bad:self.assertTrue(Path('upload-safe/fill.json').is_file())
                    else:self.assertFalse(Path('upload-safe/fill.json').exists())
                finally:os.chdir(old)

if __name__=='__main__':unittest.main()
