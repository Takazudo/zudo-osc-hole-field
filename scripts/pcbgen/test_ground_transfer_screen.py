"""Aggregate source-current optimization and signed transfer intervals."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.screen_ground_transfers import bounded_absolute_current,screen,bind_artifacts


class GroundTransferScreenTests(unittest.TestCase):
    def fixture(self):
        pads=[{'ref':ref,'pad':'1','uuid':ref+'-uuid','category':category,'possible_normal_return_basis':load}
              for ref,category,load in [('TP0','main_wire_boundary',False),('GH1','GH_return_observation',False),
                                      ('U1','IC_supply_return',True),('TP1','main_wire_boundary',False)]]
        ledger={'board_sha256':'board','native_export_sha256':'native','pads':pads,
                'normal_transfer_envelope':{'aggregate_absolute_current_A':4.6}}
        receipt={'board_sha256':'board','native_export_sha256':'native','model_source_sha256':{'fixture':'hash'},
                 'reference_main':'TP0','ports':[{'ref':ref,'pad':'1','kind':kind} for ref,kind in [('GH1','GH'),('U1','load'),('TP1','main')]],
                 'all_native_AGND_pad_component_mapping':[{k:p[k] for k in ('ref','pad','uuid')} for p in pads],
                 'matrices_ohm':{'lower':[[.001,0,0],[0,.001,0],[0,0,.001]],'upper':[[.0011,0,0],[0,.0011,0],[0,0,.0011]]}}
        return receipt,ledger

    def test_ground_requires_complete_unique_source_roles_and_uuids(self):
        receipt,ledger=self.fixture();self.assertEqual(len(screen(receipt,ledger)['references']),2)
        for defect in ('omitted','duplicate','uuid','role','native'):
            r,l=copy.deepcopy(receipt),copy.deepcopy(ledger)
            if defect=='omitted':r['ports'].pop(1)
            elif defect=='duplicate':l['pads'].append(l['pads'][1])
            elif defect=='uuid':r['all_native_AGND_pad_component_mapping'][1]['uuid']='wrong'
            elif defect=='role':r['ports'][1]['kind']='GH'
            else:l['native_export_sha256']='wrong'
            with self.subTest(defect=defect),self.assertRaises(ValueError):screen(r,l)

    def test_ground_artifacts_keep_matrix_ledger_and_profile_binding(self):
        receipt,ledger=self.fixture()
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory);matrix=folder/'matrix.json';current=folder/'ledger.json';profile=folder/'matrix-profiles.json'
            profile.write_text('{"profiles":[]}\n')
            receipt['profile_receipt']={'path':str(profile),'sha256':hashlib.sha256(profile.read_bytes()).hexdigest()}
            matrix.write_text(json.dumps(receipt));current.write_text(json.dumps(ledger))
            report=screen(receipt,ledger);bind_artifacts(report,matrix,current)
            original=profile.read_bytes();profile.write_bytes(original+b' ')
            with self.assertRaisesRegex(ValueError,'finite-profile'):bind_artifacts(report,matrix,current)
            profile.write_bytes(original);current.write_text('{}')
            with self.assertRaisesRegex(ValueError,'input changed'):bind_artifacts(report,matrix,current)

    def test_one_aggregate_limit_and_finite_individual_caps(self):
        value,allocation=bounded_absolute_current([.005,.003,.002],[.01,.1,4.6],4.6)
        self.assertAlmostEqual(sum(i for _,i in allocation),4.6)
        self.assertEqual(allocation[:2],[(0,.01),(1,.1)])
        self.assertAlmostEqual(value,.005*.01+.003*.1+.002*4.49)
        value,_=bounded_absolute_current([.005,.003],[.01,.1],4.6)
        self.assertAlmostEqual(value,.00035)


if __name__=='__main__':unittest.main()
