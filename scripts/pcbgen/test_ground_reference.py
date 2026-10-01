import copy
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest
import numpy as np
from shapely.geometry import box
from scripts.pcbgen.ground_reference import ordered_profiles


class GroundReferenceTests(unittest.TestCase):
    def test_actual_new_board_cli_scope_stays_closed_before_prerequisite(self):
        from scripts.pcbgen import solve_conductor_volume as driver
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'native.json';output=Path(folder)/'result.json'
            for board in ['osc-stage-optical']+[f'osc-octave-{i}' for i in range(1,6)]:
                source.write_text(json.dumps({'board_id':board}))
                with patch.object(driver,'extract') as extractor,self.assertRaisesRegex(ValueError,'peripheral successful native receipt and source manifest required'):
                    driver.solve(source,output,2,.25,1,0)
                extractor.assert_not_called();self.assertFalse(output.exists())

    def fixture(self):
        ports=[{'ref':'J900379','pad':p,'kind':'GH','layer':0,'physical_layer':'B.Cu',
                'patch':box(i,0,i+.25,.25)} for i,p in enumerate(('2','4','6'))]
        return {'ports':ports,'data':{'ground_reference':{'ref':'J900379','pad':'2',
                'uuid':'u2','layer':'B.Cu'},'items':[{'ref':'J900379','pad':p,'uuid':'u'+p,
                    'net':'AGND','copper':{'B.Cu':[]}} for p in ('2','4','6')]}}

    def test_only_exact_reference_pad_removed_and_congruence(self):
        g=self.fixture();_,ref,ports,profiles,identity=ordered_profiles(g)
        self.assertEqual([p['pad'] for p in ports],['4','6'])
        self.assertEqual(identity['physical_layer'],'B.Cu')
        physical=np.diag([2.,3.,5.]);old=np.array([[-1,-1],[1,0],[0,1]])
        g['data']['ground_reference'].update(pad='4',uuid='u4')
        _,ref,new,_,_=ordered_profiles(g)
        self.assertEqual([p['pad'] for p in new],['2','6'])
        basis=np.array([[1,0],[-1,-1],[0,1]]);change=np.array([[-1,-1],[0,1]])
        np.testing.assert_array_equal(old@change,basis)
        np.testing.assert_array_equal(change.T@(old.T@physical@old)@change,basis.T@physical@basis)

    def test_wrong_or_missing_native_reference_rejected(self):
        for kind in ('missing','duplicate','net','face','uuid'):
            g=self.fixture()
            if kind=='missing':g['ports']=g['ports'][1:]
            elif kind=='duplicate':g['ports'].append(g['ports'][0])
            elif kind=='net':g['data']['items'][0]['net']='+12V'
            elif kind=='face':g['data']['ground_reference']['layer']='F.Cu'
            else:g['data']['ground_reference']['uuid']='wrong'
            with self.assertRaises(ValueError):ordered_profiles(g)
        # Input order is canonicalized from exact identities, never inherited
        # as a relabeling of an existing matrix.
        g=self.fixture();expected=ordered_profiles(g)[4]
        g['ports'].reverse();self.assertEqual(ordered_profiles(g)[4],expected)


if __name__=='__main__':unittest.main()
