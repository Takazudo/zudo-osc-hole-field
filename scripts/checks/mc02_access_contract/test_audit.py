import copy
import json
import unittest
import audit as a


class AccessContractTests(unittest.TestCase):
    def setUp(self): self.e=json.loads(a.EVIDENCE.read_text())
    def claim(self): return next(iter(self.e['case_claims'].values()))

    def test_all31_remain_not_shown_with_source_context(self):
        r=a.audit(self.e)
        self.assertEqual(len(r['cases']),31)
        self.assertEqual(sum(x['requires_supporting_hand'] for x in r['cases']),6)
        self.assertTrue(all(x['access_verdict']=='NOT SHOWN' for x in r['cases']))
        self.assertTrue(all(x['lowering_stage'] in range(1,10) for x in r['cases']))
        self.assertTrue(all(x['guaranteed_open_envelope_mm'] is None for x in r['cases']))

    def test_global_method_conflicts_separate_from31_access_cases(self):
        r=a.audit(self.e)
        self.assertEqual(r['source_method_conflict_count'],2)
        self.assertEqual([x['step'] for x in r['source_method_conflicts']],[7,12])
        self.assertEqual([x['operations'] for x in r['source_method_conflicts']],[61,61])
        self.e['expected_source_method_conflicts']=[]
        with self.assertRaisesRegex(ValueError,'operation conflicts'):a.audit(self.e)

    def test_reference4point8_is_not_guaranteed_maximum(self):
        for key,value in [('guaranteed_maximum',True),('kind','toleranced_maximum')]:
            e=copy.deepcopy(self.e);e['handoff']['open_height_mm'][key]=value
            with self.assertRaisesRegex(ValueError,'reference opening'):a.audit(e)

    def test_closed_tolerance_not_transferred_to_open(self):
        self.e['handoff']['open_height_mm']['tolerance']='0.2'
        with self.assertRaisesRegex(ValueError,'reference opening'):a.audit(self.e)

    def test_tool_reach_and_contact1_never_imply_manual_pass(self):
        c=self.claim();c['tool_reach_shown']=True;c['contact1_mapping_shown']=True
        self.assertTrue(a.validate_claim(c))
        r=a.audit(self.e);self.assertEqual(r['access_verdict'],'NOT SHOWN')
        c['access_verdict']='PASS'
        with self.assertRaisesRegex(ValueError,'promotion forbidden'):a.audit(self.e)

    def test_manual_claim_cannot_be_asserted_without_new_contract(self):
        self.claim()['manual_access_shown']=True
        with self.assertRaisesRegex(ValueError,'manual access evidence absent'):a.audit(self.e)

    def test_no_invented_hand_corridor_or_open_bound(self):
        for key,value in [('manual_corridor_mm',10),('guaranteed_open_envelope_mm',4.8)]:
            e=copy.deepcopy(self.e);next(iter(e['case_claims'].values()))[key]=value
            with self.assertRaises(ValueError):a.audit(e)

    def test_no_tool_only_instruction_replacement(self):
        self.e['handoff']['actuation']['method']='tool operation'
        with self.assertRaisesRegex(ValueError,'central manual'):a.audit(self.e)

    def test_missing_or_extra_case_rejected(self):
        for extra in (False,True):
            e=copy.deepcopy(self.e)
            if extra:e['case_claims']['invented']=copy.deepcopy(self.claim())
            else:del e['case_claims'][next(iter(e['case_claims']))]
            with self.assertRaisesRegex(ValueError,'coverage'):a.audit(e)

    def test_handoff_hash_and_promotion_rejected(self):
        for key,value in [('verified_pdf_sha256',None),('expected_pdf_sha256','0'*64),('status','UNVERIFIED_HANDOFF')]:
            e=copy.deepcopy(self.e);e['handoff'][key]=value
            with self.assertRaises(ValueError):a.audit(e)

    def test_wrong_actual_pdf_bytes_rejected(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'wrong.pdf';p.write_bytes(b'not the reviewed PDF')
            with self.assertRaisesRegex(ValueError,'PDF bytes'):a.verify_pdf(p)

    def test_source_drift_rejected(self):
        self.e['sha256'][a.THREAD]='0'*64
        with self.assertRaisesRegex(ValueError,'source pin changed'):a.audit(self.e)


if __name__=='__main__':unittest.main()
