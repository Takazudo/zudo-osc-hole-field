import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from scripts.pcbgen import screen_core_coupling as screen
from scripts.pcbgen.screen_core_coupling import summarize,run,verify_profile_basis


class CoreCouplingScreenTests(unittest.TestCase):
    def fixture(self):
        ports=[{'ref':'J1','pad':'2','kind':'GH','layer':0},
            {'ref':'J1','pad':'4','kind':'GH','layer':0},
            {'ref':'J2','pad':'2','kind':'GH','layer':0},
            {'ref':'TP2','pad':'1','kind':'main','layer':0}]
        # A true star: shared reference arm 2; individual arms 1,3,4,5.
        z=np.ones((4,4))*2+np.diag([1,3,4,5])
        return {'reference_main':'TP1','ports':ports,
            'core_native_prerequisite':{'selected_contacts':ports+[{'ref':'TP1','pad':'1','kind':'main','layer':0}],
                'own_load_scope':'Unrepresented own-load currents remain open'},
            'matrices_ohm':{'upper':z.tolist(),'lower':z.tolist()},
            'native_export_sha256':'fixture','model_source_sha256':{'fixture':'fixture'}}

    def test_exact_star_rebasing_retains_full_private_arms(self):
        report=summarize(self.fixture());a,b=report['reference_reports']
        self.assertEqual(a['full_self']['absolute_interval_upper_ohm'],6)
        self.assertEqual(b['full_self']['absolute_interval_upper_ohm'],9)
        for name in ('same_header_distinct_contact','distinct_header_transfer'):
            self.assertEqual(a[name]['absolute_interval_upper_ohm'],2)
            self.assertEqual(b[name]['absolute_interval_upper_ohm'],5)
        for mutation in ('missing','duplicate','face'):
            r=self.fixture()
            if mutation=='missing':r['ports'].pop()
            elif mutation=='duplicate':r['ports'].append(r['ports'][0])
            else:r['ports'][0]['layer']=3
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):summarize(r)

    def complete_metadata_fixture(self):
        selected=[{'ref':f'J{i//4:03}','pad':str(2*(i%4+1)),'kind':'GH','layer':0} for i in range(206)]
        selected += [{'ref':f'TP{i:03}','pad':'1','kind':'main','layer':0} for i in range(9)]
        for i,p in enumerate(selected):p.update(uuid=f'uuid-{i}',native_layer='F.Cu',main_connected=True)
        ports=[{k:p[k] for k in ('ref','pad','kind','layer')} for p in selected if p['ref']!='TP000']
        receipt={'reference_main':'TP000','ports':ports,
            'core_native_prerequisite':{'selected_contacts':selected,'own_load_scope':'OPEN'},
            'all_native_AGND_pad_component_mapping':[{'ref':p['ref'],'pad':p['pad'],'uuid':p['uuid'],'layers':['F.Cu']} for p in selected],
            'native_export_sha256':'fixture','model_source_sha256':{'fixture':'fixture'},
            'matrices_ohm':{'upper':np.eye(214).tolist(),'lower':np.eye(214).tolist()}}
        profiles={k:copy.deepcopy(receipt[k]) for k in ('core_native_prerequisite','native_export_sha256','model_source_sha256')}
        profiles['profiles']=copy.deepcopy(ports)+[{'ref':'TP000','pad':'1','kind':'main','layer':0}]
        return receipt,profiles

    def test_exact_sidecar_order_reference_source_and_native_face_uuid(self):
        receipt,profiles=self.complete_metadata_fixture();verify_profile_basis(receipt,profiles)
        for mutation in ('order','reference','native','model','prerequisite','missing','face','uuid','ref-face'):
            r,p=copy.deepcopy(receipt),copy.deepcopy(profiles)
            if mutation=='order':r['ports'][0],r['ports'][1]=r['ports'][1],r['ports'][0]
            elif mutation=='reference':r['reference_main']='TP001'
            elif mutation=='native':p['native_export_sha256']='wrong'
            elif mutation=='model':p['model_source_sha256']={'wrong':'wrong'}
            elif mutation=='prerequisite':p['core_native_prerequisite']['own_load_scope']='wrong'
            elif mutation=='missing':r['core_native_prerequisite']['selected_contacts'].pop()
            elif mutation=='face':r['all_native_AGND_pad_component_mapping'][0]['layers']=['B.Cu']
            elif mutation=='uuid':r['all_native_AGND_pad_component_mapping'][0]['uuid']='wrong'
            else:next(x for x in r['all_native_AGND_pad_component_mapping'] if x['ref']=='TP000')['layers']=['B.Cu']
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):verify_profile_basis(r,p)

    def test_indefinite_zero_diagonal_gap_is_rejected_without_projection(self):
        r=self.fixture();u=np.array(r['matrices_ohm']['upper']);u[0,2]+=1;u[2,0]+=1
        r['matrices_ohm']['upper']=u.tolist()
        with self.assertRaisesRegex(ValueError,'indefinite'):summarize(r)


    def test_sidecar_mismatch_cannot_be_rebound(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'matrix.json';q=Path(d)/'matrix-profiles.json';out=Path(d)/'screen.json'
            r,profiles=self.complete_metadata_fixture();original=json.dumps(profiles).encode();q.write_bytes(original)
            r['profile_receipt']={'path':str(q),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}
            p.write_text(json.dumps(r));q.write_bytes(b'{"changed":true}')
            with self.assertRaisesRegex(ValueError,'solver binding'):run(p,out)
            self.assertFalse(out.exists())
            q.write_bytes(original)
            with patch.object(screen,'verify_actual_authority') as authority:
                result=run(p,out);authority.assert_called_once()
            self.assertEqual(result['input_artifacts']['matrix']['sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
            with self.assertRaisesRegex(ValueError,'fresh'):run(p,out)

    def test_algorithm_mutation_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);p=folder/'matrix.json';q=folder/'matrix-profiles.json';out=folder/'screen.json';code=folder/'algorithm.py'
            code.write_bytes(b'initial source');r,profiles=self.complete_metadata_fixture();q.write_text(json.dumps(profiles))
            r['profile_receipt']={'path':str(q),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()};p.write_text(json.dumps(r))
            original=summarize
            def mutate(receipt):
                result=original(receipt);code.write_bytes(b'changed during work');return result
            with patch.object(screen,'__file__',str(code)),patch.object(screen,'verify_actual_authority'),patch.object(screen,'summarize',side_effect=mutate):
                with self.assertRaisesRegex(ValueError,'algorithm source changed'):run(p,out)
            self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
