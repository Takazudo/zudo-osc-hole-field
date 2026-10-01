"""Fresh driver preserves represented physics while tightening trial work."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import shapely
from shapely.geometry import box, Polygon
from scripts.pcbgen import solve_ground_volume as old_driver
from scripts.pcbgen import solve_conductor_volume as new_driver
from scripts.pcbgen import solve_rail_volume as rail_driver
from scripts.pcbgen.barrel_volume import BarrelVolume
from scripts.pcbgen.sheet_volume import SheetVolume
from scripts.pcbgen.test_sheet_volume import RHO, THICKNESS, BANDS


class ConductorDriverTests(unittest.TestCase):
    def test_rail_rejects_changed_after_publication_profile_without_rebinding(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'result-profiles.json';path.write_bytes(b'{"profiles":["original"]}')
            receipt={'profile_receipt':{'path':str(path.resolve()),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
            retained=json.dumps(receipt,sort_keys=True)
            self.assertEqual(rail_driver.verify_profile_receipt(receipt,path),b'{"profiles":["original"]}')
            path.write_bytes(b'{"profiles":["changed"]}')
            with self.assertRaisesRegex(ValueError,'changed after publication'):
                rail_driver.verify_profile_receipt(receipt,path)
            self.assertEqual(json.dumps(receipt,sort_keys=True),retained)
            with self.assertRaisesRegex(ValueError,'unexpected path'):
                rail_driver.verify_profile_receipt(receipt,path.with_name('other-profiles.json'))

    def test_native_mutation_during_extraction_is_rejected_without_receipts(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);native=folder/'native.json';native.write_bytes(b'{"old":true}')
            original=native.read_bytes();output=folder/'result.json'
            def mutate(path,*args,**kwargs):
                self.assertNotEqual(Path(path),native)
                self.assertEqual(Path(path).read_bytes(),original)
                native.write_bytes(b'{"new":true}')
                return {'geometry_export_sha256':hashlib.sha256(original).hexdigest()}
            with patch.object(new_driver,'extract',side_effect=mutate),self.assertRaisesRegex(ValueError,'changed during extraction'):
                new_driver.solve(native,output,.5,.125,1,0)
            self.assertFalse(output.exists())
            self.assertFalse((folder/'result-profiles.json').exists())
            with patch.object(new_driver,'extract',return_value={'geometry_export_sha256':'wrong'}),self.assertRaisesRegex(ValueError,'changed during extraction'):
                new_driver.solve(native,output,.5,.125,1,0)

    def test_completed_or_mixed_stem_is_rejected_before_any_input_or_output_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);output=folder/'result.json';missing=folder/'missing.json'
            for suffix in ('','-profiles','-screen','-rail-ledger'):
                artifact=output if not suffix else folder/('result'+suffix+'.json')
                retained=b'{"historical":"retain exactly"}';artifact.write_bytes(retained)
                with self.subTest(artifact=artifact.name),self.assertRaisesRegex(ValueError,'fresh stem'):
                    rail_driver.run(missing,missing,output,'+5V',.5,.125,1,(0,0),missing)
                if suffix in ('','-profiles'):
                    with self.assertRaisesRegex(ValueError,'fresh stem'):
                        new_driver.solve(missing,output,.5,.125,1,0)
                self.assertEqual(artifact.read_bytes(),retained)
                artifact.unlink()

    def test_same_profiles_native_operator_and_current_with_new_work_bound(self):
        barrel = BarrelVolume(.15, .025, .275, 1.6, BANDS, RHO,
            polygon_sides=8, angular_subdivisions=1, radial_steps=1,
            band_steps=1, gap_steps=2)
        domain = box(-1,-1,1,1).difference(Polygon(barrel.interface_polygon()))
        ports = [
            {'ref':'TP1','pad':'1','kind':'main','layer':3,'patch':box(-.7,-.5,-.45,-.25)},
            {'ref':'TP2','pad':'1','kind':'main','layer':3,'patch':box(.4,.4,.65,.65)},
            {'ref':'GH1','pad':'2','kind':'GH','layer':3,'patch':box(-.7,.4,-.45,.65)},
            {'ref':'U1','pad':'5','kind':'load','layer':0,'patch':box(.4,-.5,.65,-.25)}]
        operators = []
        class RecordVolume(SheetVolume):
            def __init__(self,*args,**kwargs):
                super().__init__(*args,**kwargs)
                operators.append((self.certificate_mode,
                    (self.hybrid_matrix if self.certificate_mode=='current' else self.potential_matrix).copy()))
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);native=folder/'native.json';native.write_text('{}\n')
            native_hash=hashlib.sha256(native.read_bytes()).hexdigest()
            geometry={'ports':ports,'geometry_export_sha256':native_hash,
                'data':{'outline_mm':[[-1,-1],[1,-1],[1,1],[-1,1]],'board_sha256':'fixture'},
                'inner':[domain]*4,'outer':[domain]*4,'thickness':THICKNESS,'barrels':[(barrel,(0,0))],
                'all_native_ground_pad_component_mapping':[], 'barrel_ownership':[],
                'unused_native_AGND_copper_uuids':[], 'native_zone_authority_audits':[],
                'computational_envelope_audits':[], 'physical_foil_layers':['F.Cu','In1.Cu','In2.Cu','B.Cu'],
                'active_sheet_layers':['F.Cu','In1.Cu','In2.Cu','B.Cu'],
                'physical_to_active_sheet':{'F.Cu':0,'In1.Cu':1,'In2.Cu':2,'B.Cu':3},
                'source_free_component_audits':[]}
            receipts=[];profiles=[]
            for name,driver in [('old',old_driver),('new',new_driver)]:
                output=folder/(name+'.json')
                with patch.object(driver,'extract',return_value=geometry),patch.object(driver,'SheetVolume',RecordVolume):
                    driver.solve(native,output,.5,.125,1,0,True,True)
                receipts.append(json.loads(output.read_text()))
                profiles.append(json.loads((folder/(name+'-profiles.json')).read_text()))
            self.assertEqual(profiles[0]['profiles'],profiles[1]['profiles'])
            self.assertEqual(profiles[0]['native_export_sha256'],native_hash)
            self.assertEqual(profiles[1]['native_export_sha256'],native_hash)
            profile_bytes=(folder/'new-profiles.json').read_bytes()
            self.assertEqual(receipts[1]['profile_receipt']['sha256'],hashlib.sha256(profile_bytes).hexdigest())
            for a,b in zip(operators[:2],operators[2:]):
                self.assertEqual(a[0],b[0]);self.assertEqual(a[1].shape,b[1].shape)
                self.assertEqual((a[1]!=b[1]).nnz,0)
            old_upper=np.array(receipts[0]['matrices_ohm']['upper'])
            new_upper=np.array(receipts[1]['matrices_ohm']['upper'])
            self.assertGreaterEqual(np.linalg.eigvalsh(old_upper-new_upper).min(),-1e-12)
            before=np.array(receipts[0]['matrices_ohm']['lower'])
            after=np.array(receipts[1]['matrices_ohm']['lower'])
            self.assertGreaterEqual(np.linalg.eigvalsh(after-before).min(),-1e-12)
            self.assertLess(receipts[1]['counts']['potential']['maximum_residual_work_allowance_ohm'],
                            receipts[0]['counts']['potential']['maximum_residual_work_allowance_ohm'])
            self.assertIn('potential_trial_matrix.py',receipts[1]['model_source_sha256'])
            self.assertIn('residual_work.py',receipts[1]['model_source_sha256'])
            for name in ('nodes','triangles','maximum_equation_residual_A','conservation_correction'):
                self.assertEqual(receipts[0]['counts']['current'][name],receipts[1]['counts']['current'][name])
            self.assertTrue(all(r['corrections']==0 for r in receipts[1]['counts']['current']['current_refinement']))
            self.assertLess(receipts[1]['counts']['potential']['maximum_equation_residual_A'],1e-8)


if __name__=='__main__':unittest.main()
