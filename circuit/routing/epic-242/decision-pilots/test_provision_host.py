"""Source-only launch boundary tests; no Docker/systemd/native calls."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import provision_host as host


class ProvisionHostTests(unittest.TestCase):
    def setUp(self):
        self.packet=json.loads((host.HERE/'minimum-native-request.json').read_text())

    def test_exact_guard_parser_accepts_plan_and_preserves_payload(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            plan=host.route_plan(host.HERE.parents[3],sys.executable,root/'fixture',root/'guard.json',self.packet)
            argv=plan['argv']
            # Omit only the platform-dispatch wrapper; --plan exits before all native activity.
            at=argv.index('scripts/kicad/native_resource_guard.py')
            result=subprocess.run(argv[at-1:at+1]+['--plan']+argv[at+1:],
                cwd=host.HERE.parents[3],check=True,text=True,capture_output=True)
            observed=json.loads(result.stdout)['proposal_plan']
            self.assertEqual(observed['seconds'],300)
            self.assertEqual(observed['memory_max'],6442450944)
            self.assertEqual(observed['memory_swap_max'],0)
            self.assertEqual(observed['aggregate_memory_max'],12884901888)
            self.assertEqual(observed['sha'],host.METHOD)
            self.assertEqual(observed['command'][:4],['bash','-c',
                'bash scripts/kicad/run.sh kicad-cli version && exec "$@"','epic242-route-probe'])
            self.assertEqual(observed['command'][4],sys.executable)
            self.assertFalse((root/'guard.json').exists())

    def test_existing_evidence_and_directory_are_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);evidence=root/'guard.json';evidence.mkdir()
            with self.assertRaisesRegex(ValueError,'NEW JSON FILE'):
                host.route_plan(root,sys.executable,root/'fixture',evidence,self.packet)
            with self.assertRaisesRegex(ValueError,'JSON file'):
                host.route_plan(root,sys.executable,root/'fixture',root/'directory',self.packet)

    def test_existing_fixture_is_not_a_retry(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);fixture=root/'fixture';fixture.mkdir()
            with self.assertRaisesRegex(ValueError,'new private'):
                host.route_plan(root,sys.executable,fixture,root/'guard.json',self.packet)

    def test_new_provisioning_inputs_exist_at_frozen_method(self):
        import hashlib
        root=host.HERE.parents[3]
        for path,digest in host.PROVISION_SOURCES.items():
            data=subprocess.check_output(['git','show',host.METHOD+':'+path],cwd=root)
            self.assertEqual(hashlib.sha256(data).hexdigest(),digest)
            self.assertEqual(self.packet['input_file_sha256'][path],digest)


if __name__=='__main__':unittest.main()
