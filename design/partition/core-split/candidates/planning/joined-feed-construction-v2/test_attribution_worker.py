"""Worker orchestration on bounded fixtures; kernel/auth facts are explicit mocks."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

import attribution_admission as A
import attribution_executor as E
import attribution_worker as W
from test_attribution_executor import packet


class Worker(unittest.TestCase):
    def test_actual_worker_pipeline_after_admission_and_single_use_claim(self):
        with tempfile.TemporaryDirectory(prefix='e16-fixture-',dir='/tmp') as name:
            root=Path(name);p,_,_,_=packet(root)
            request={'packet':p,'request_kind':'resource-qualification'};path=root/'request.json';path.write_bytes(A.canon(request))
            output=root/'result';deadline=time.monotonic()+10;order=[]
            def verified(*a,**kw):order.append('verified');return request
            def claimed(*a,**kw):order.append('claimed');return 256
            before=list(sys.path)
            try:
                with patch.object(W,'prove_worker',return_value=(output,deadline,2*1024**2)), \
                     patch.object(A,'verify_for_host',side_effect=verified),patch.object(A,'claim_worker',side_effect=claimed), \
                     patch.dict(os.environ,{'E16_GUARD_ENTRY_AT':str(time.monotonic())}):
                    self.assertEqual(W.run(path,hashlib.sha256(path.read_bytes()).hexdigest(),'fixture-auth','fixture-reservation'),0)
            finally:sys.path[:]=before
            self.assertEqual(order,['verified','claimed'])
            result=A.read_json(output/'terminal.json')
            self.assertEqual(result['status'],'COMPLETE')
            self.assertFalse(result['summary']['production_evidence'])
            self.assertEqual(result['component_rows'],5)
            self.assertFalse(result['adopted'])

    def test_failed_authority_or_consumed_claim_cannot_start_pipeline(self):
        with tempfile.TemporaryDirectory(prefix='e16-fixture-',dir='/tmp') as name:
            root=Path(name);path=root/'request.json';path.write_bytes(b'{}')
            for which in ('verify_for_host','claim_worker'):
                with self.subTest(which=which),patch.object(W,'prove_worker',return_value=(root/'result',time.monotonic()+10,1024**2)), \
                     patch.object(A,'verify_for_host',return_value={}),patch.object(A,'claim_worker',return_value=1), \
                     patch.object(A,which,side_effect=ValueError('refused')),patch.object(E,'run_pipeline') as pipeline, \
                     self.assertRaisesRegex(ValueError,'refused'):
                    W.run(path,'0'*64,'absent','absent')
                pipeline.assert_not_called()
                self.assertFalse((root/'result').exists())

    def test_loader_overrides_and_inherited_execution_identity_refused(self):
        for key in ('PYTHONPATH','PYTHONHOME','LD_PRELOAD','DYLD_LIBRARY_PATH','E16_CGROUP_WORKER','HEAVY_GUARD_HELD'):
            with self.subTest(key=key),self.assertRaises(ValueError):A.clean_environment({key:'bad'})
        env=A.clean_environment({'SECRET_TOKEN':'private','PATH':'wrong','HOME':'wrong'})
        self.assertNotIn('SECRET_TOKEN',env)
        self.assertEqual(env['PATH'],'/usr/bin:/bin')
        self.assertEqual(env['HOME'],str(A.account_home()))
        self.assertEqual(env['OPENBLAS_NUM_THREADS'],'1')


if __name__=='__main__':unittest.main()
