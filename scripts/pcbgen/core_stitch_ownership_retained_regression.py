import copy
import json
import unittest
from pathlib import Path
from scripts.pcbgen.core_stitch_ownership import validate


class CoreStitchOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=lambda p:json.loads(Path(p).read_text())
        cls.plan=read('design/partition/core-ground-feasibility/header-stitch-plan.json')
        cls.manifest=read('design/partition/core-ground-feasibility/osc-core.receipt.json')
        cls.basis=read('.circuit-cache/issue38-recovery/core-feasibility-v5/ground-feasibility-geometry.json')

    def test_complete_actual_source_ownership_and_wrong_source_identity(self):
        self.assertEqual(validate(self.plan,self.manifest,self.basis)['added_via_count'],104)
        for field,value in [('uuid','wrong-source-pad'),('native_xy_mm',[0,0]),('native_layers',['B.Cu'])]:
            changed=copy.deepcopy(self.plan);changed['added'][0]['ports'][0][field]=value
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,'source/native port identity'):
                validate(changed,self.manifest,self.basis)

    def test_missing_or_duplicate_or_foreign_stitch_is_rejected(self):
        changed=copy.deepcopy(self.plan);changed['added'].pop()
        with self.assertRaisesRegex(ValueError,'two exact stitches'):validate(changed,self.manifest,self.basis)
        changed=copy.deepcopy(self.plan);changed['added'][1]=copy.deepcopy(changed['added'][0])
        with self.assertRaisesRegex(ValueError,'UUID ownership'):validate(changed,self.manifest,self.basis)
        changed=copy.deepcopy(self.plan);changed['added'][0]['header_id']='OTHER-BOARD'
        with self.assertRaisesRegex(ValueError,'foreign header'):validate(changed,self.manifest,self.basis)


if __name__=='__main__':unittest.main()
