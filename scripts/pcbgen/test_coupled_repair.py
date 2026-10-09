import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from scripts.pcbgen import local_repair_pilot as pilot,route_jack_grid as driver
from scripts.pcbgen.test_grid_router import crossing_board


class CoupledRepairTests(unittest.TestCase):
    def test_supply_restoration_and_independent_agreement_are_mandatory(self):
        for outcome in ('native-error','unrestored','fresh-drift','success'):
            with self.subTest(outcome=outcome),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);base=root/'base.kicad_pcb';base.write_text('canonical copper')
                proposal=root/'proposal.json';proposal.write_text('{}')
                plan={'name':'coupled','signal_proposal':'proposal.json',
                      'signal_proposal_sha256':hashlib.sha256(proposal.read_bytes()).hexdigest(),
                      'input_board_sha256':hashlib.sha256(base.read_bytes()).hexdigest()}
                before=crossing_board();before['pads']=[{**p,'net':'-12V' if p['net']=='A' else p['net']} for p in before['pads']]
                before.update(open_edges=1,islands={'B':[['b0'],['b1']]})
                split={**before,'open_edges':1,'islands':{'-12V':[['a0'],['a1']]}}
                joined={**before,'open_edges':0,'islands':{}}
                clean={'violations':[],'schematic_parity':[]}
                signal_drc={'violations':[{'severity':'error'}],'schematic_parity':[]} if outcome=='native-error' else clean
                def workspace(board_id,label):
                    folder=root/label;folder.mkdir();return folder
                def apply(*args):
                    (root/args[-1]).write_text('candidate')
                def restore(board_id,candidate,spec,definition,log):
                    self.assertEqual(spec['rail_width'],.4);self.assertEqual(spec['clearance'],.25)
                    candidate.with_name('dump.json').write_text(json.dumps(split if outcome=='unrestored' else joined))
                    return candidate,{'status':'mock native test state'}
                fresh=split if outcome=='fresh-drift' else joined
                with patch.object(pilot,'ROOT',root),patch.object(driver,'ROOT',root),\
                     patch.object(driver,'workspace',side_effect=workspace),patch.object(driver,'run',side_effect=apply),\
                     patch.object(driver,'check',side_effect=[(signal_drc,split),(clean,fresh)]),\
                     patch.object(driver,'run_stage',side_effect=restore) as restoration:
                    if outcome=='success':
                        candidate,receipt=pilot.coupled_candidate('osc-jack-right',base,before,plan,{})
                        self.assertTrue(candidate.exists());self.assertIn('rail',receipt['phases'])
                    else:
                        with self.assertRaises(driver.StageRejected):
                            pilot.coupled_candidate('osc-jack-right',base,before,plan,{})
                if outcome=='native-error':restoration.assert_not_called()
                self.assertEqual(base.read_text(),'canonical copper')
