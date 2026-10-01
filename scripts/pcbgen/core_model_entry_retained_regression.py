"""Current K native authority and complete/coupling port selection gates."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.pcbgen import core_model_entry as entry
from scripts.pcbgen import solve_conductor_volume as driver

BASE=Path('.circuit-cache/issue38-recovery/core-feasibility-v7')
NATIVE=BASE/'ground-feasibility-geometry.json'
RECEIPT=BASE/'ground-feasibility-native-receipt.json'
MANIFEST=Path('design/partition/core-ground-feasibility/osc-core.receipt.json')


class CoreModelEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native_bytes=NATIVE.read_bytes()
        cls.coupling=entry.enter(NATIVE,cls.native_bytes,RECEIPT,MANIFEST,False,0)
        cls.full=entry.enter(NATIVE,cls.native_bytes,RECEIPT,MANIFEST,True,0,True)

    def test_complete_basis_and_coupling_remain_distinct(self):
        self.assertEqual(len(self.coupling['selected_contacts']),215)
        self.assertEqual(len(self.full['contacts']),2288)
        self.assertEqual(self.full['balanced_function_count'],2287)
        self.assertEqual(self.full['source_DNP_omission_count'],8)
        self.assertEqual(self.full['board_sha256'],json.loads(self.native_bytes)['board_sha256'])
        for authority in (self.coupling,self.full):
            self.assertEqual(len(authority['selected_contacts'] if authority is self.coupling else authority['contacts']),215 if authority is self.coupling else 2288)
            entry.verify_unchanged(authority)

    def test_complete_selection_checks_identity_and_face(self):
        data=json.loads(self.native_bytes)
        ports=[{'ref':p['ref'],'pad':p['pad'],'kind':p['kind'],'layer':0 if p['physical_layer']=='F.Cu' else 3,
                'physical_layer':p['physical_layer'],'physical_foil_index':0 if p['physical_layer']=='F.Cu' else 3,
                'source_face':'top' if p['physical_layer']=='F.Cu' else 'bottom',
                **({'strand_count':19,'maximum_wetting':'test-support'} if p['kind']=='main' else {})}
               for p in self.full['contacts']]
        geometry={'data':data,'ports':ports,'physical_foil_layers':['F.Cu','In1.Cu','In2.Cu','B.Cu'],
                  'physical_to_active_sheet':{'F.Cu':0,'In1.Cu':1,'In2.Cu':2,'B.Cu':3}}
        before=json.dumps(data,sort_keys=True)
        entry.select_ports(geometry,self.full)
        self.assertEqual(len(geometry['ports']),2288)
        self.assertEqual(json.dumps(data,sort_keys=True),before)
        for mutation in ('missing','duplicate','face','uuid'):
            changed=copy.deepcopy(geometry)
            if mutation=='missing':changed['ports'].pop()
            elif mutation=='duplicate':changed['ports'].append(changed['ports'][0])
            elif mutation=='face':changed['ports'][0]['physical_layer']='B.Cu' if changed['ports'][0]['physical_layer']=='F.Cu' else 'F.Cu'
            else:
                first=changed['ports'][0]
                physical=next(p for p in changed['data']['items'] if (p.get('ref'),p.get('pad'))==(first['ref'],first['pad']))
                physical['uuid']='wrong'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):entry.select_ports(changed,self.full)

    def test_driver_rejects_missing_or_stale_authority_before_extraction(self):
        stale=Path('.circuit-cache/issue38-recovery/core-feasibility-v6')
        cases=[(NATIVE,None,None),(NATIVE,stale/'ground-feasibility-native-receipt.json',MANIFEST),
               (stale/'ground-feasibility-geometry.json',RECEIPT,MANIFEST)]
        with tempfile.TemporaryDirectory() as directory:
            for source,receipt,manifest in cases:
                output=Path(directory)/'result.json'
                with self.subTest(source=str(source),receipt=str(receipt)),patch.object(driver,'extract') as extract:
                    with self.assertRaises(ValueError):
                        driver.solve(source,output,2.,.25,1,0,include_loads=True,main_strands=True,core_receipt=receipt,core_manifest=manifest)
                    extract.assert_not_called()
                    self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError,'port-limit 0'):
            entry.enter(NATIVE,self.native_bytes,RECEIPT,MANIFEST,True,3,True)
        with self.assertRaisesRegex(ValueError,'nineteen-support'):
            entry.enter(NATIVE,self.native_bytes,RECEIPT,MANIFEST,True,0)
        with self.assertRaisesRegex(ValueError,'actual osc-core'):
            entry.enter(NATIVE,b'{"board_id":"osc-jack-left"}',RECEIPT,MANIFEST,False,0)

    def test_immutable_input_and_final_dependency_mismatch_reject(self):
        with self.assertRaisesRegex(ValueError,'immutable conductor input'):
            entry.enter(NATIVE,self.native_bytes+b' ',RECEIPT,MANIFEST,True,0,True)
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source';source.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'changed during diagnostic'):
                entry.verify_unchanged({'source_sha256':{str(source):'wrong'},'contacts':[]})


if __name__=='__main__':unittest.main()
