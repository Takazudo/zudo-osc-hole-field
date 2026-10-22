import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
import osc_fill_check as f
import osc_candidate_check as c

class Resources(unittest.TestCase):
    def mem(self,total=8,available=5):
        return f'MemTotal: {total*1024*1024} kB\nMemAvailable: {available*1024*1024} kB\n'
    def test_thresholds(self):
        self.assertTrue(f.capacity_decision(self.mem(6,4),4*f.GIB,6*f.GIB,'')['passed'])
        for mem,disk,docker,active in [(self.mem(5,4),4*f.GIB,6*f.GIB,''),(self.mem(6,3),4*f.GIB,6*f.GIB,''),(self.mem(),3*f.GIB,6*f.GIB,''),(self.mem(),4*f.GIB,5*f.GIB,''),(self.mem(),4*f.GIB,6*f.GIB,'abc')]:
            self.assertFalse(f.capacity_decision(mem,disk,docker,active)['passed'])
        with self.assertRaises(ValueError): f.capacity_decision('MemTotal: 6 kB',4*f.GIB,6*f.GIB,'')
    def test_not_hosted_never_reads_proc(self):
        with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{'OSC_STATE':t,'GITHUB_ACTIONS':'false'},clear=True),patch.object(Path,'read_text') as read:
            with self.assertRaisesRegex(ValueError,'GitHub-hosted'): f.resource_preflight()
            read.assert_not_called()
    def test_gate_precedes_create(self):
        env={'OSC_INPUT_ROOT':'/source','OSC_PAYLOAD':'/bundle'}
        args=['run','--rm','--network','none','--volume','/source:/work','--volume','/tmp/h:/tmp/kicad-home',c.IMAGE]
        with patch.dict(os.environ,env),patch.object(f,'readonly_args',return_value=args),patch.object(f,'resource_preflight',side_effect=ValueError('gate failed')) as gate,patch.object(c,'adapter') as create:
            with self.assertRaisesRegex(ValueError,'gate failed'):f.adapter(args)
            gate.assert_called_once()
            create.assert_not_called()
    def test_measurements_mocked_and_persisted(self):
        with tempfile.TemporaryDirectory() as t:
            env={'OSC_STATE':t,'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted','OSC_REAL_DOCKER':'docker','OSC_DEADLINE':str(time.monotonic()+480)}
            responses=[{'failure':None,'exit_code':0,'output':'"unix:///var/run/docker.sock"'},{'failure':None,'exit_code':0,'output':str(8*f.GIB)},{'failure':None,'exit_code':0,'output':''}]
            old=c.DEADLINE
            try:
                with patch.dict(os.environ,env,clear=True),patch.object(Path,'read_text',return_value=self.mem()),patch.object(f.shutil,'disk_usage',return_value=type('D',(),{'free':8*f.GIB})()),patch.object(c,'run_command',side_effect=responses) as run:
                    f.resource_preflight()
                row=json.loads(next(Path(t).glob('resource-*.json')).read_text())
                self.assertEqual(row['status'],'PASS');self.assertEqual(run.call_count,3)
                self.assertEqual(row['docker_endpoint'],'unix:///var/run/docker.sock')
                self.assertEqual(row['container_memory_bytes'],2*f.GIB)
            finally:c.DEADLINE=old
    def test_default_and_fill_policy(self):
        for policy,expected in [('default',['--memory','512m']),('fill-2g-noswap',['--memory','2g','--memory-swap','2g'])]:
            with tempfile.TemporaryDirectory() as t,patch.dict(os.environ,{'OSC_STATE':t,'OSC_REAL_DOCKER':'docker'}),patch.object(c,'run_command',side_effect=[{'failure':None,'exit_code':0,'output':'a'*64},{'failure':None,'exit_code':0,'output':''}]) as run:
                c.adapter(['run','--rm',c.IMAGE,'sh','-c','python3 -c "import pcbnew"'],memory_policy=policy)
                args=run.call_args_list[0].args[0]
                self.assertEqual(args[args.index('--memory'):args.index('--memory')+len(expected)],expected)
                self.assertEqual(args[args.index('--cpus')+1],'1');self.assertEqual(args[args.index('--pids-limit')+1],'64')
    def test_resource_override_rejected(self):
        for flag in ('--memory','--memory=4g','--memory-swap=4g','--cpus=8','--pids-limit=100','-m4g','-c2'):
            with self.assertRaises(ValueError):c.adapter(['run','--rm',flag,c.IMAGE])
    def test_effective_context_endpoint(self):
        for endpoint in ('unix:///var/run/docker.sock','tcp://remote:2375',None,''):
            with patch.object(c,'run_command',return_value={'failure':None,'exit_code':0,'output':json.dumps(endpoint)}) as run:
                measurement={}
                if endpoint=='unix:///var/run/docker.sock':self.assertEqual(f.local_docker_endpoint('docker',Path('.'),measurement),endpoint)
                else:
                    with self.assertRaises(ValueError):f.local_docker_endpoint('docker',Path('.'),measurement)
                    self.assertEqual(measurement['docker_endpoint'],'REJECTED_NONLOCAL_OR_MISSING')
                self.assertEqual(run.call_args.args[0],['docker','context','inspect','--format','{{json .Endpoints.docker.Host}}'])

if __name__=='__main__': unittest.main()
