"""Fixture admission evidence only; never production authority or reservation."""
import copy
import hashlib
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import attribution_lifecycle as L
import attribution_transport as T
import attribution_executor as E
from test_attribution_executor import packet


class Lifecycle(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='e16-fixture-',dir='/tmp')
        self.root=Path(self.temp.name)
        payload,*_=packet(self.root)
        sources=L.source_bindings();payload['source_bindings']=sources
        self.request={'operation':'e16-selected-attribution-v1','limits':copy.deepcopy(L.LIMITS),
                      'run_id':'a'*32,'attempt':1,'source_bindings':sources,'packet':payload,
                      'fixture_only':True,'output':str(self.root/'output')}
        self.grant()
    def tearDown(self):self.temp.cleanup()
    def grant(self):
        digest=hashlib.sha256(T.canonical(self.request)).hexdigest()
        self.authority={'request_sha256':digest,'run_id':self.request['run_id'],
                        'limits':copy.deepcopy(L.LIMITS),'expires_unix':time.time()+60}
        self.reservation=self.authority|{'exclusive':True}
    def run_fixture(self,**kw):
        return L.run_fixture(self.request,self.root,self.authority,self.reservation,**kw)

    def test_single_unit_fixture_through_lifecycle(self):
        result=self.run_fixture()
        self.assertEqual(result['status'],'COMPLETE')
        self.assertEqual(len(list((self.root/'claims').iterdir())),1)
        self.assertFalse(result['summary']['production_evidence'])

    def test_missing_authority_reservation(self):
        for authority,reservation in ((None,self.reservation),(self.authority,None)):
            with self.assertRaisesRegex(ValueError,'missing authority|missing reservation'):
                L.run_fixture(self.request,self.root,authority,reservation)
        self.assertFalse((self.root/'claims').exists())

    def test_stale_expired_nonexclusive_grants(self):
        for change in ({'expires_unix':0},{'request_sha256':'0'*64},{'exclusive':False}):
            reservation=self.reservation|change
            with self.assertRaises(ValueError):L.run_fixture(self.request,self.root,self.authority,reservation)

    def test_consumed_identity_cannot_reuse_new_output(self):
        self.run_fixture()
        self.request['output']=str(self.root/'new-output');self.grant()
        with self.assertRaises(FileExistsError):self.run_fixture()
        self.assertFalse((self.root/'new-output').exists())

    def test_failed_execution_stays_consumed(self):
        self.request['packet']['certificate_limits']['max_updates']=0;self.grant()
        with self.assertRaisesRegex(ValueError,'arithmetic cap'):self.run_fixture()
        self.assertEqual(len(list((self.root/'claims').iterdir())),1)
        self.assertEqual(__import__('json').loads((self.root/'output/terminal.json').read_text())['status'],'INCOMPLETE')
        self.request['output']=str(self.root/'retry');self.grant()
        with self.assertRaises(FileExistsError):self.run_fixture()

    def test_stale_source_independent_index_and_limits(self):
        for change in ('source','limits','index'):
            request=copy.deepcopy(self.request)
            index={str(Path(b['path']).resolve()):b['sha256'] for b in L.artifact_bindings(request['packet'])}
            if change=='source':request['source_bindings']['finite_solve.py']='0'*64
            if change=='limits':request['limits']['units']=148
            if change=='index':index.clear()
            digest=hashlib.sha256(T.canonical(request)).hexdigest()
            with self.assertRaises(ValueError):L.validate_request(request,digest,index,T.Budget())

    def test_fixture_limits_before_numerical_work(self):
        self.request['packet']['boards']['KA']['operator']['decoded_limit']=5*1024**2
        with patch.object(E,'run_pipeline') as engine,self.assertRaisesRegex(ValueError,'fixture byte ceiling'):
            self.run_fixture()
        engine.assert_not_called()

    def test_production_entry_cannot_treat_fixture_grants_as_authority(self):
        import attribution_host as H
        path=self.root/'request.json';path.write_bytes(T.canonical(self.request))
        digest=hashlib.sha256(T.canonical(self.request)).hexdigest()
        with patch.object(H.resource,'setrlimit'),patch.object(H.os,'execvpe') as execute,self.assertRaises((ValueError,KeyError)):
            L.execute_production(path,digest,self.root/'authority.json',self.root/'reservation.json')
        execute.assert_not_called()
        self.assertIsNone(L.readiness()['production_request_sha256'])


if __name__=='__main__':unittest.main()
