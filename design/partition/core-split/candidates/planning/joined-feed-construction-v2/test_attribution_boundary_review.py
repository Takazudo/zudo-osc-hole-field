"""Independent boundary regressions; disposable signatures and source fixtures.

No original numerical artifacts, real campaign ledger, host guard, cgroup or
mount is opened or executed. The journal is produced by the actual admission
implementation rather than being handwritten to match the result verifier.
"""
import hashlib
import os
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import attribution_admission as A
import attribution_host as H
import attribution_worker as W
import numerical_unit_guard as G
import test_attribution_admission as fixtures


class IndependentBoundaryReview(unittest.TestCase):
    def signed_fixture(self):
        fixture = fixtures.Admission()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        return fixture

    def test_actual_terminal_journal_matches_acceptance_contract(self):
        fixture = self.signed_fixture()
        A.claim(fixture.request,fixture.digest)
        files = {'retained/result/components.jsonl': {'bytes':12,'sha256':'a'*64}}
        terminal = {'status':'PENDING_SHARED_GUARD','cleanup_complete':True,'files':files}
        A.finish_accounting(fixture.request,fixture.digest,terminal)
        journal = A.read_json(fixture.state/(fixture.request['run_id']+'.terminal.json'))
        self.assertEqual(journal['request_sha256'],fixture.digest)
        self.assertEqual(journal['run_id'],fixture.request['run_id'])
        self.assertEqual(journal['request_kind'],'resource-qualification')
        self.assertEqual(journal['terminal_status'],'PENDING_SHARED_GUARD')
        self.assertIs(journal['cleanup_complete'],True)
        self.assertEqual(journal['output_manifest_sha256'],hashlib.sha256(A.canon(files)).hexdigest())
        self.assertEqual(journal['ledger_sha256'],A.sha(fixture.ledger))

    def test_metadata_only_rejects_signed_path_traversal_before_claim(self):
        fixture = self.signed_fixture()
        fixture.request['run_id'] = '../../escape'
        fixture.request['environment_policy'] = A.ENVIRONMENT_POLICY
        output_root = fixture.root/'runs'
        fixture.request['output'] = str(output_root/('attribution-'+fixture.request['run_id']))
        fixture.save_request();fixture.grants()
        original = fixture.ledger.read_bytes()
        with patch.object(A,'output_root',return_value=output_root),patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'identity|run.id'):
                A.verify_for_host(fixture.request_path,fixture.digest,fixture.authority,
                                  fixture.reservation,metadata_only=True)
        self.assertEqual(fixture.ledger.read_bytes(),original)
        self.assertFalse(fixture.state.exists())

    def test_metadata_only_rejects_second_attempt_before_claim(self):
        fixture = self.signed_fixture()
        fixture.request['attempt'] = 2
        fixture.request['environment_policy'] = A.ENVIRONMENT_POLICY
        output_root = fixture.root/'runs'
        fixture.request['output'] = str(output_root/('attribution-'+fixture.request['run_id']))
        fixture.save_request();fixture.grants()
        with patch.object(A,'output_root',return_value=output_root),patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'identity|attempt'):
                A.verify_for_host(fixture.request_path,fixture.digest,fixture.authority,
                                  fixture.reservation,metadata_only=True)
        self.assertFalse(fixture.state.exists())

    def test_worker_requires_live_exclusive_controller_before_kernel_reads(self):
        with patch.object(G.UnitGuard,'prove_owner'),\
             patch.object(H,'prove_reservation_owner',side_effect=ValueError('no live reservation')) as owner:
            with self.assertRaisesRegex(ValueError,'no live reservation'):
                W.prove_worker({'guard_sha256':'a'*64})
        owner.assert_called_once()

    def test_fixed_import_flags_ignore_timestamp_valid_stale_bytecode(self):
        with tempfile.TemporaryDirectory(prefix='e16-cache-fixture-') as directory:
            source = Path(directory)/'review_cache_module.py'
            source.write_text('value="BAD_"\n')
            stamp = source.stat().st_mtime_ns
            py_compile.compile(str(source),doraise=True)
            source.write_text('value="GOOD"\n')
            os.utime(source,ns=(stamp,stamp))
            code = 'import sys;sys.path.insert(0,sys.argv[1]);import review_cache_module;print(review_cache_module.value)'
            common = [sys.executable,'-I','-S','-B']
            cached = subprocess.check_output(common+['-c',code,directory],text=True,timeout=5)
            sealed = subprocess.check_output(common+['-X','pycache_prefix=/dev/null','-c',code,directory],text=True,timeout=5)
            self.assertEqual(cached.strip(),'BAD_')
            self.assertEqual(sealed.strip(),'GOOD')
            self.assertEqual(A.ENVIRONMENT_POLICY['python_flags'],['-I','-S','-B','-X','pycache_prefix=/dev/null'])


if __name__ == '__main__':
    unittest.main()
