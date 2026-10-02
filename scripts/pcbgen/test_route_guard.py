"""Dispatch controls only: fake commands never invoke routing or native tools."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


class RouteGuardDispatchTests(unittest.TestCase):
    def test_only_complete_github_hosted_identity_uses_direct_dispatch(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary)
            for name in ('bash','python3'):
                tool=folder/name
                tool.write_text('#!'+sys.executable+'\nimport json,sys\nprint(json.dumps({"tool":'+repr(name)+',"args":sys.argv[1:]}))\n')
                tool.chmod(0o755)
            for variables,direct in (({},False),({'CI':'true'},False),
                    ({'GITHUB_ACTIONS':'true'},False),({'RUNNER_ENVIRONMENT':'github-hosted'},False),
                    ({'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'self-hosted'},False),
                    ({'GITHUB_ACTIONS':'false','RUNNER_ENVIRONMENT':'github-hosted'},False),
                    ({'GITHUB_ACTIONS':'true','RUNNER_ENVIRONMENT':'github-hosted'},True)):
                with self.subTest(variables=variables):
                    env={k:v for k,v in os.environ.items() if k not in ('CI','GITHUB_ACTIONS','RUNNER_ENVIRONMENT')}
                    env.update(variables);env['PATH']=str(folder)+os.pathsep+env.get('PATH','')
                    done=subprocess.run(['/bin/bash',str(ROOT/'scripts/pcbgen/with_route_guard.sh'),
                                         'python3','fake-route','argument with spaces'],
                                        env=env,check=True,capture_output=True,text=True)
                    result=json.loads(done.stdout)
                    if direct:
                        self.assertEqual(result,{'tool':'python3','args':['fake-route','argument with spaces']})
                    else:
                        self.assertEqual(result['tool'],'bash')
                        self.assertTrue(result['args'][0].endswith('/.codex/scripts/heavy-guard.sh'))
                        self.assertEqual(result['args'][1:],['--','python3','fake-route','argument with spaces'])
