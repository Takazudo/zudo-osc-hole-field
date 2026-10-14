"""Disposable signed fixtures only; no production trust/grants/ledger is created."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import attribution_admission as A
import attribution_request as P


class Admission(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='e16-admission-fixture-',dir='/tmp')
        self.root=Path(self.temp.name);self.key=self.root/'fixture-key'
        subprocess.run(['/usr/bin/ssh-keygen','-q','-t','ed25519','-N','','-f',str(self.key)],check=True)
        self.trust=self.root/'allowed-signers'
        public=self.key.with_suffix('.pub').read_text().split();public=' '.join(public[:2])
        self.trust.write_text('\n'.join(identity+' '+public for identity in ('e16-operator','e16-controller','e16-resource-reviewer'))+'\n')
        self.trust.chmod(0o600)
        self.ledger=self.root/'campaign.json';self.state=self.root/'state'
        self.initial={'activity':'COMPLETE original campaign','live_owned_work':False,
                      'execution_budget':{'full_baseline_used':2,'full_baseline_limit':3,'production_diagnostic_used':8,'production_diagnostic_limit':24},
                      'runs':[{'attempt':5,'state':'terminal numerical PASS'}]}
        self.ledger.write_bytes(A.canon(self.initial))
        self.request={'authorization_policy':copy.deepcopy(A.AUTHORIZATION_POLICY),'schema':'e16-attribution-request-v1','operation':A.OPERATION,'request_kind':'resource-qualification',
                      'run_id':'b'*32,'attempt':1,'source_sha':'c'*40,'limits':copy.deepcopy(A.LIMITS),
                      'host':A.host_identity(),'trust_sha256':A.sha(self.trust),'qualification':None,
                      'ledger':{'path':str(self.ledger),'sha256':A.sha(self.ledger)},'output':str(self.root/'output')}
        self.request_path=self.root/'request.json';self.save_request()
        self.authority=self.root/'authorization.json';self.reservation=self.root/'reservation.json'
        self.grants()
        self.patches=[patch.object(A,'trust_path',return_value=self.trust),patch.object(A,'ledger_path',return_value=self.ledger),
                      patch.object(A,'state_directory',return_value=self.state)]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.temp.cleanup()
    def save_request(self):
        self.request_path.write_bytes(A.canon(self.request));self.digest=A.sha(self.request_path)
    def sign(self,path,data,namespace):
        path.write_bytes(A.canon(data));Path(str(path)+'.sig').unlink(missing_ok=True)
        subprocess.run(['/usr/bin/ssh-keygen','-Y','sign','-f',str(self.key),'-n',namespace,str(path)],
                       check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    def grants(self):
        prefix='e16-attribution' if self.request['request_kind']=='production-attribution' else 'e16-attribution-qualification'
        common={'authorization_policy':copy.deepcopy(A.AUTHORIZATION_POLICY),'request_sha256':self.digest,'run_id':self.request['run_id'],'request_kind':self.request['request_kind'],
                'operation':A.OPERATION,'limits':copy.deepcopy(A.LIMITS),'issued_unix':time.time()-1,'expires_unix':time.time()+300}
        self.auth=common|{'schema':prefix+'-authorization-v1','approved':True}
        self.res=common|{'schema':prefix+'-reservation-v1','exclusive':True,'host':A.host_identity(),
                        'ledger_sha256':self.request['ledger']['sha256']}
        self.sign(self.authority,self.auth,prefix+'-authorization-v1');self.sign(self.reservation,self.res,prefix+'-reservation-v1')
    def verify(self):
        with patch.object(A,'validate_metadata') as metadata:
            result=A.verify_for_host(self.request_path,self.digest,self.authority,self.reservation)
        metadata.assert_called_once()
        return result

    def test_policy_binding_cannot_be_missing_changed_or_external(self):
        for policy in (None, A.AUTHORIZATION_POLICY|{'owner':'someone else'},
                       A.AUTHORIZATION_POLICY|{'signature_provenance':'independent-external'}):
            self.sign(self.authority,self.auth|{'authorization_policy':policy},
                      'e16-attribution-qualification-authorization-v1')
            with patch.object(A,'validate_metadata') as metadata,self.assertRaisesRegex(ValueError,'delegation'):
                A.verify_for_host(self.request_path,self.digest,self.authority,self.reservation)
            metadata.assert_not_called()
        self.grants()
        self.request.pop('authorization_policy');self.save_request();self.grants()
        with self.assertRaisesRegex(ValueError,'delegation'):self.verify()

    def test_serial_checkout_status_preserves_failure_and_dirty_gates(self):
        for code,out,err,message in ((128,'','thread allocation refused','checkout status command failed'),
                                    (0,' M file.py','','not clean'),(0,'','','')):
            with patch.object(A.subprocess,'run',return_value=SimpleNamespace(returncode=code,stdout=out,stderr=err)) as run:
                if message:
                    with self.assertRaisesRegex(ValueError,message):A.prove_clean_checkout()
                else:A.prove_clean_checkout()
            command=run.call_args.args[0]
            self.assertIn('core.preloadIndex=false',command);self.assertIn('index.threads=1',command)
            self.assertEqual(command[-2:],['status','--porcelain'])

    def test_owner_decision_drift_refused(self):
        changed=self.root/'decision';changed.write_text('changed authorization')
        with patch.object(A,'OWNER_DECISION',changed),self.assertRaisesRegex(ValueError,'owner decision'):
            self.verify()

    def test_resource_attestation_requires_actual_separate_bound_review(self):
        receipt=self.root/'receipt';receipt.write_text('complete tiny fixture evidence')
        evidence=[{'path':str(receipt),'sha256':A.sha(receipt)}]
        operation='a'*64
        review={'schema':'e16-technical-resource-review-v1','reviewer_identity':'fixture-reviewer',
                'author_identity':'wsl-coordinator','operation_sha256':operation,'verdict':'PASS','evidence':evidence}
        review_path=self.root/'review.json';report_path=self.root/'resource.json'
        report={'schema':'e16-attribution-resource-v1','status':'RESOURCE_QUALIFIED',
                'authorization_policy':dict(A.AUTHORIZATION_POLICY),'operation_sha256':operation,
                'limits':A.LIMITS,'combined_operation':True,'evidence_kind':'admitted_combined_operation',
                'expires_unix':time.time()+300,'measured':{'elapsed_seconds':1,'memory_peak_bytes':100,
                'output_peak_bytes':100,'swap_bytes':0,'max_concurrency':1,'attempts':1},
                'production_admission_allowance_seconds_upper':10,'cleanup_complete':True,
                'all_required_phases':True,'evidence':evidence}
        def bind(r):
            review_path.write_bytes(A.canon(r))
            report['technical_review']={'path':str(review_path),'sha256':A.sha(review_path),
                                        'reviewer_identity':r['reviewer_identity']}
            self.sign(report_path,report,'e16-attribution-resource-v1')
            self.request['qualification']={'path':str(report_path),'sha256':A.sha(report_path)}
        bind(review)
        with patch.object(A,'operation_digest',return_value=operation):
            A.verify_qualification(self.request)
            for delta in ({'reviewer_identity':'wsl-coordinator'},{'verdict':'FAIL'},
                          {'operation_sha256':'b'*64},{'evidence':[]}):
                bind(review|delta)
                with self.assertRaisesRegex(ValueError,'technical review'):A.verify_qualification(self.request)
            bind(review);review_path.write_text('{}')
            with self.assertRaisesRegex(ValueError,'technical review bytes'):A.verify_qualification(self.request)

    def test_actual_detached_signatures_with_distinct_qualification_authority(self):
        result=self.verify();self.assertEqual(result['request_kind'],'resource-qualification')
        self.assertFalse(self.state.exists());self.assertEqual(A.read_json(self.ledger),self.initial)

    def test_unsigned_or_forged_grants_fail_before_inputs(self):
        self.authority.write_bytes(A.canon(self.auth|{'approved':False}))
        with patch.object(A,'validate_metadata') as metadata,self.assertRaisesRegex(ValueError,'signed'):
            A.verify_for_host(self.request_path,self.digest,self.authority,self.reservation)
        metadata.assert_not_called()

    def test_unknown_trust_store_fails_closed(self):
        self.trust.unlink()
        with self.assertRaises(FileNotFoundError):self.verify()

    def test_changed_trust_store_refused(self):
        self.trust.write_text(self.trust.read_text()+'# changed\n')
        with self.assertRaisesRegex(ValueError,'signer store binding'):self.verify()

    def test_expired_short_nonexclusive_wrong_host_reservations(self):
        for delta in ({'expires_unix':0},{'expires_unix':time.time()+10},{'exclusive':False},{'host':{'uid':-1}}):
            self.sign(self.reservation,self.res|delta,'e16-attribution-qualification-reservation-v1')
            with self.assertRaises(ValueError):self.verify()

    def test_production_grant_cannot_authorize_qualification(self):
        self.sign(self.authority,self.auth,'e16-attribution-authorization-v1')
        with self.assertRaisesRegex(ValueError,'signed'):self.verify()

    def test_qualification_grant_cannot_authorize_production(self):
        self.request['request_kind']='production-attribution';self.save_request()
        with self.assertRaisesRegex(ValueError,'signed'):self.verify()

    def test_production_requires_separate_resource_qualification(self):
        self.request['request_kind']='production-attribution';self.save_request();self.grants()
        with self.assertRaises((TypeError,ValueError,KeyError)):self.verify()

    def test_stale_request_digest(self):
        self.request['attempt']=2;self.request_path.write_bytes(A.canon(self.request))
        with self.assertRaisesRegex(ValueError,'stale request'):self.verify()

    def test_signed_duplicate_json_or_nonfinite_expiry_refused(self):
        for raw in (b'{"approved":true,"approved":false}',b'{"expires_unix":Infinity}'):
            self.authority.write_bytes(raw);Path(str(self.authority)+'.sig').unlink()
            subprocess.run(['/usr/bin/ssh-keygen','-Y','sign','-f',str(self.key),'-n','e16-attribution-qualification-authorization-v1',str(self.authority)],
                           check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            with self.assertRaisesRegex(ValueError,'duplicate|nonfinite'):self.verify()

    def test_source_and_toolchain_manifest_cannot_omit_dependencies(self):
        one=self.root/'one.py';one.write_text('source')
        two=self.root/'two.so';two.write_text('library')
        request={'source_tree':{'files':{str(one):A.sha(one)}},'toolchain':{'files':{str(two):A.sha(two)}}}
        with patch.object(P,'source_paths',return_value=[one]),patch.object(P,'toolchain_paths',return_value=[two]):
            A.verify_manifests(request)
            request['toolchain']['files'].clear()
            with self.assertRaisesRegex(ValueError,'incomplete'):A.verify_manifests(request)

    def test_one_charge_preserves_attempt5_and_original_bytes(self):
        original=self.ledger.read_bytes();path,size=A.claim(self.request,self.digest)
        journal=A.read_json(path);current=A.read_json(self.ledger)
        self.assertEqual(base64.b64decode(journal['original_ledger_base64']),original)
        self.assertEqual(current['runs'],self.initial['runs'])
        self.assertEqual(current['execution_budget']['full_baseline_used'],2)
        self.assertEqual(current['execution_budget']['production_diagnostic_used'],9)
        self.assertTrue(current['live_owned_work']);self.assertLess(size,65536)
        with self.assertRaises(ValueError):A.claim(self.request,self.digest)
        self.assertEqual(A.read_json(self.ledger)['execution_budget']['production_diagnostic_used'],9)

    def test_terminal_failure_charged_once_and_no_worker_resume(self):
        A.claim(self.request,self.digest);A.claim_worker(self.request,self.digest)
        with self.assertRaises(FileExistsError):A.claim_worker(self.request,self.digest)
        A.finish_accounting(self.request,self.digest,{'status':'INCOMPLETE','cleanup_complete':True,'files':{}})
        current=A.read_json(self.ledger)
        self.assertFalse(current['live_owned_work']);self.assertEqual(current['attribution_charges'][0]['state'],'TERMINAL')
        self.assertEqual(current['execution_budget']['production_diagnostic_used'],9)
        with self.assertRaises(ValueError):A.finish_accounting(self.request,self.digest,{'status':'INCOMPLETE','cleanup_complete':True,'files':{}})

    def test_cleanup_failure_preserves_live_block(self):
        A.claim(self.request,self.digest)
        A.finish_accounting(self.request,self.digest,{'status':'INCOMPLETE','cleanup_complete':False,'files':{}})
        self.assertTrue(A.read_json(self.ledger)['live_owned_work'])

    def test_crash_after_claim_is_consumed_without_ledger_overwrite(self):
        original=self.ledger.read_bytes()
        with patch.object(A.os,'replace',side_effect=OSError('interrupted')),self.assertRaises(OSError):
            A.claim(self.request,self.digest)
        self.assertEqual(self.ledger.read_bytes(),original)
        self.assertTrue((self.state/(self.request['run_id']+'.json')).exists())
        with self.assertRaises(FileExistsError):A.claim(self.request,self.digest)

    def test_missing_consumed_claim_prevents_worker(self):
        with self.assertRaises(FileNotFoundError):A.claim_worker(self.request,self.digest)

    def test_oversized_bootstrap_source_refused_before_hashing(self):
        source=self.root/'oversized.py'
        with source.open('wb') as stream:stream.truncate(1024**2+1)
        with patch.object(A,'HERE',self.root),patch.object(A,'SOURCE_NAMES',('oversized.py',)),self.assertRaisesRegex(ValueError,'oversized'):
            A.source_bindings()

    def test_bundled_library_binding_requires_unique_existing_identity(self):
        one=self.root/'libfixture.so';one.write_bytes(b'fixture')
        output='libfixture.so => not found\n'
        self.assertEqual(P.linked_paths(output,{one}),{one})
        with self.assertRaisesRegex(ValueError,'unresolved'):P.linked_paths(output,set())
        other=self.root/'other';other.mkdir();two=other/'libfixture.so';two.write_bytes(b'other')
        with self.assertRaisesRegex(ValueError,'ambiguous'):P.linked_paths(output,{one,two})

    def test_request_description_is_not_approval_or_production_request(self):
        op={'authorization_policy':A.AUTHORIZATION_POLICY,'operation':A.OPERATION,'limits':A.LIMITS,'environment_policy':A.ENVIRONMENT_POLICY,'source_bindings':{},'source_tree':{},'toolchain':{},'packet':{},'host_limits':{},'guard_sha256':'0'*64}
        first=A.operation_digest(op);changed=op|{'run_id':'a'*32,'request_kind':'resource-qualification'}
        self.assertEqual(first,A.operation_digest(changed))
        self.assertNotEqual(first,A.operation_digest(op|{'limits':A.LIMITS|{'seconds':181}}))


if __name__=='__main__':unittest.main()
