"""Disposable signed characterization admission; no live original reads or keys."""
import copy
import hashlib
import time
import unittest
from unittest.mock import patch
import attribution_admission as A
import attribution_request as R
import attribution_worker as W
import test_attribution_admission as Original

class CharacterizationAdmission(unittest.TestCase):
    setUp=Original.Admission.setUp
    tearDown=Original.Admission.tearDown
    sign=Original.Admission.sign
    save_request=Original.Admission.save_request
    grants=Original.Admission.grants
    verify=Original.Admission.verify

    def prepare(self):
        self.request.update(request_kind='resource-characterization',
            environment_policy=A.ENVIRONMENT_POLICY,source_bindings={},source_tree={},toolchain={},
            packet={'purpose':'raw-construction-metadata-v1'},host_limits={},guard_sha256='d'*64)
        self.review=self.root/'review.json'
        self.review_data={'schema':'e16-characterization-technical-review-v1','verdict':'PASS',
            'operation_sha256':A.operation_digest(self.request),'reviewer_identity':'independent-fixture-reviewer',
            'author_identity':'wsl-coordinator','purpose':'raw-construction-metadata-v1','resource_status':'NOT_QUALIFIED'}
        self.update_review()
    def update_review(self):
        self.review.write_bytes(A.canon(self.review_data))
        self.request['characterization_review']={'path':str(self.review),'sha256':A.sha(self.review)}
        self.save_request();self.new_grants()
    def new_grants(self):
        prefix=A.grant_prefix(self.request['request_kind'])
        common={'authorization_policy':copy.deepcopy(self.request['authorization_policy']),
            'request_sha256':self.digest,'run_id':self.request['run_id'],'request_kind':self.request['request_kind'],
            'operation':A.OPERATION,'limits':copy.deepcopy(A.LIMITS),'issued_unix':time.time()-1,'expires_unix':time.time()+300}
        self.auth=common|{'schema':prefix+'-authorization-v1','approved':True}
        self.res=common|{'schema':prefix+'-reservation-v1','exclusive':True,'host':A.host_identity(),'ledger_sha256':self.request['ledger']['sha256']}
        self.sign(self.authority,self.auth,A.grant_namespace(self.request['request_kind'],'authorization'));self.sign(self.reservation,self.res,A.grant_namespace(self.request['request_kind'],'reservation'))
    def test_distinct_signed_request_review_and_single_use(self):
        self.prepare();self.assertEqual(self.verify()['request_kind'],'resource-characterization')
        with patch.object(A,'validate_structure'),patch.object(A,'prove_clean_checkout'):
            A.claim(self.request,self.digest);A.claim_worker(self.request,self.digest)
            with self.assertRaises(FileExistsError):A.claim_worker(self.request,self.digest)
        ledger=A.read_json(self.ledger)
        self.assertEqual(ledger['execution_budget']['production_diagnostic_used'],9)
        self.assertEqual(ledger['execution_budget']['full_baseline_used'],2)
        self.assertEqual(ledger['attribution_charges'][-1]['request_kind'],'resource-characterization')
    def test_review_missing_stale_wrong_scope_and_self_review(self):
        self.prepare()
        for key,value in [('verdict','FAIL'),('operation_sha256','e'*64),('reviewer_identity','wsl-coordinator'),
                          ('resource_status','RESOURCE_QUALIFIED'),('purpose','full-qualification')]:
            previous=self.review_data[key];self.review_data[key]=value;self.update_review()
            with self.assertRaises(ValueError):self.verify()
            self.review_data[key]=previous
        self.update_review();self.review.write_text('{}')
        with self.assertRaisesRegex(ValueError,'review changed'):self.verify()
        self.request.pop('characterization_review');self.save_request();self.new_grants()
        with self.assertRaisesRegex(ValueError,'review missing'):self.verify()
    def test_namespace_and_legacy_policy_cannot_admit_new_kind(self):
        self.prepare()
        self.sign(self.authority,self.auth,'e16-attribution-authorization-v1')
        with self.assertRaisesRegex(ValueError,'signed'):self.verify()
        self.new_grants();self.request['authorization_policy']=copy.deepcopy(A.LEGACY_AUTHORIZATION_POLICY)
        self.save_request();self.new_grants()
        with self.assertRaisesRegex(ValueError,'outside bound'):self.verify()
        A.verify_policy({'authorization_policy':A.LEGACY_AUTHORIZATION_POLICY,'request_kind':'resource-qualification'})
    def test_restricted_existing_trust_and_cross_kind_payloads(self):
        public=' '.join(self.key.with_suffix('.pub').read_text().split()[:2])
        self.trust.write_text('e16-operator namespaces="e16-attribution-qualification-authorization-v1,e16-attribution-authorization-v1" '+public+'\n'
            +'e16-controller namespaces="e16-attribution-qualification-reservation-v1,e16-attribution-reservation-v1" '+public+'\n'
            +'e16-resource-reviewer namespaces="e16-attribution-resource-v1" '+public+'\n')
        self.request['trust_sha256']=A.sha(self.trust);self.prepare()
        self.assertEqual(self.verify()['request_kind'],'resource-characterization')
        self.sign(self.authority,self.auth,'e16-attribution-characterization-authorization-v1')
        with self.assertRaisesRegex(ValueError,'signed'):self.verify()
        self.new_grants()
        for changed in (self.auth|{'schema':'e16-attribution-qualification-authorization-v1','request_kind':'resource-qualification'},
                        self.auth|{'request_sha256':'e'*64}):
            self.sign(self.authority,changed,A.grant_namespace('resource-characterization','authorization'))
            with self.assertRaises(ValueError):self.verify()
        self.new_grants()
        self.sign(self.authority,self.auth,A.grant_namespace('resource-characterization','reservation'))
        with self.assertRaisesRegex(ValueError,'signed'):self.verify()
        # Same cryptographic namespace does not make a characterization payload a
        # qualification grant, even when its digest is altered to the new request.
        self.request['request_kind']='resource-qualification';self.request.pop('characterization_review')
        self.save_request();self.new_grants()
        changed=self.auth|{'schema':'e16-attribution-characterization-authorization-v1','request_kind':'resource-characterization'}
        self.sign(self.authority,changed,A.grant_namespace('resource-characterization','authorization'))
        with self.assertRaisesRegex(ValueError,'inapplicable'):self.verify()

    def test_fixed_two_operator_packet_and_distinct_operation(self):
        sources=A.source_bindings()
        packet=R.packet_from_inventory(sources,characterization_only=True)
        self.assertEqual(len(list(A.artifacts(packet))),2)
        self.assertEqual(set(packet['boards']),{'KA','KB'})
        for b in packet['boards'].values():self.assertEqual(set(b),{'operator'})
        self.assertNotIn('comparison',packet);self.assertNotIn('config',packet)
        self.assertIn('attribution_characterization.py',sources)
        ordinary=R.packet_from_inventory(sources)
        self.assertNotEqual(packet,ordinary)
    def test_host_receipt_preserves_characterization_purpose(self):
        import attribution_host as H
        self.prepare();out=self.root/'output';out.mkdir()
        receipt={'status':'PENDING_SHARED_GUARD','request_sha256':self.digest,'run_id':self.request['run_id'],
                 'request_kind':'resource-characterization','cleanup_complete':True,
                 'electrical_acceptance':False,'whole_board_acceptance':False,'adopted':False}
        (out/'terminal.json').write_bytes(A.canon(receipt))
        with self.assertRaisesRegex(ValueError,'purpose differs'):H.accepted_result(self.request_path,self.digest)
        receipt.update(characterization_only=True,qualification_only=False)
        (out/'terminal.json').write_bytes(A.canon(receipt))
        with patch.object(A,'verify_characterization_review',side_effect=ValueError('stale technical proof')) as review:
            with self.assertRaisesRegex(ValueError,'stale technical proof'):H.accepted_result(self.request_path,self.digest)
            review.assert_called_once()

    def test_worker_dispatch_never_calls_numerical_executor(self):
        import attribution_characterization as C
        import attribution_executor as E
        request={'request_kind':'resource-characterization','packet':{'purpose':'raw-construction-metadata-v1',
                 'boards':{'KA':{'operator':{'id':1}},'KB':{'operator':{'id':2}}}}}
        result={'status':'COMPLETE','summary':{'purpose':'CHARACTERIZATION_ONLY','full_pipeline_qualification':'NOT_QUALIFIED'}}
        with patch.object(C,'characterize',return_value=result) as characterize,patch.object(E,'run_pipeline',side_effect=AssertionError('numeric execution')):
            self.assertEqual(W.execute_request(request,self.root/'out',object()),result)
            self.assertEqual(characterize.call_args.args[0],{'KA':{'id':1},'KB':{'id':2}})
            request['request_kind']='resource-qualification'
            with self.assertRaisesRegex(ValueError,'characterization packet'):W.execute_request(request,self.root/'out',object())
        self.prepare();self.request['qualification']={'path':'invalid','sha256':'f'*64};self.save_request();self.new_grants()
        with self.assertRaisesRegex(ValueError,'nonproduction'):self.verify()

if __name__=='__main__':unittest.main(verbosity=2)
