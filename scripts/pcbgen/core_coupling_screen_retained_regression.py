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

    def test_current_authority_and_wrong_native_board_or_failed_receipt(self):
        base=Path('.circuit-cache/issue38-recovery/core-feasibility-v7')
        # Recompute current native authority; never rebind the historical v6 solver receipt.
        prerequisite=screen.require_native_prerequisite(
            base/'ground-feasibility-geometry.json',
            base/'ground-feasibility-native-receipt.json',
            Path('design/partition/core-ground-feasibility/osc-core.receipt.json'))
        native=json.loads((base/'ground-feasibility-geometry.json').read_text())
        receipt={'core_native_prerequisite':prerequisite,'board_sha256':native['board_sha256'],
            'native_export_sha256':hashlib.sha256((base/'ground-feasibility-geometry.json').read_bytes()).hexdigest()}
        screen.verify_actual_authority(receipt)
        for key in ('board_sha256','native_export_sha256'):
            wrong={**receipt,key:'wrong'}
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'authority'):
                screen.verify_actual_authority(wrong)
        wrong=copy.deepcopy(receipt);deps=wrong['core_native_prerequisite']['dependency_sha256']
        for name in list(deps):
            if name.endswith('/ground-feasibility-native-receipt.json'):
                old=Path('.circuit-cache/issue38-recovery/core-feasibility-v2/ground-feasibility-native-receipt.json').resolve()
                del deps[name];deps[str(old)]=hashlib.sha256(old.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'successful native rule/parity'):
            screen.verify_actual_authority(wrong)


if __name__ == '__main__':
    unittest.main()
