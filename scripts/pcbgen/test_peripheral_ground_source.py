import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.generate_peripheral_ground import generate,source_contacts
from scripts.pcbgen.peripheral_project_source import derive,fresh_sync_project
from scripts.pcbgen.native_companion_binding import verify
import hashlib

BASE=Path('design/partition/peripheral-ground-feasibility')


class PeripheralGroundSourceTests(unittest.TestCase):
    def test_all_fixed_sources_and_independent_contacts(self):
        proposal=json.loads((BASE/'proposal.json').read_bytes())
        with tempfile.TemporaryDirectory() as folder:
            for row in proposal['boards']:
                path=Path(folder)/(row['board_id']+'.json');receipt=generate(BASE/'proposal.json',row['board_id'],path)
                original=json.loads(Path('design/boards',path.name).read_bytes());current=json.loads(path.read_bytes())
                self.assertEqual({k:v for k,v in original.items() if k not in ('stackup','routing')},
                    {k:v for k,v in current.items() if k not in ('stackup','routing')})
                self.assertEqual(receipt,json.loads((BASE/(row['board_id']+'.receipt.json')).read_bytes()))
                self.assertEqual(len(receipt['source_packages']),row['footprints'])
                self.assertEqual(len(receipt['own_ground_contacts'])+len(receipt['GH_ground_contacts']),72 if row['board_key']=='EL' else 7)
                self.assertFalse(receipt['model_entry_allowed'])
        partition=json.loads(Path(proposal['partition']).read_bytes());io=json.loads(Path(proposal['io']).read_bytes())
        changed=copy.deepcopy(partition);changed['connectors'].append(next(h for h in changed['connectors'] if h['board']=='O1'))
        with self.assertRaisesRegex(ValueError,'duplicate source header'):
            source_contacts('osc-octave-1','O1',changed,io)

    def test_source_bridge_accounting_and_invalid_declaration(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder)
            proposal=BASE/'optical-ground-v2/proposal.json'
            for bid,count in [('osc-stage-optical',1),('osc-octave-1',0)]:
                r=generate(proposal,bid,folder/(bid+'.json'))
                self.assertEqual(r['source_added_copper'],{'tracks':0,'vias':count,'keepout_exceptions':0})
                self.assertEqual(r['no_added_tracks_vias_or_exceptions'],count==0)
            altered=json.loads(proposal.read_bytes());altered['source_ground_bridge']['net']='+5V'
            wrong=folder/'wrong.json';wrong.write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError,'unsupported source ground bridge'):
                generate(wrong,'osc-stage-optical',folder/'osc-stage-optical.json')

    def test_complete_project_is_source_derived_with_only_named_changes(self):
        template=Path('boards/osc-jack-left/osc-jack-left.kicad_pro').read_bytes()
        for bid in ['osc-octave-1','osc-stage-optical']:
            original=Path('boards',bid,bid+'.kicad_pro').read_bytes();definition=(BASE/(bid+'.json')).read_bytes()
            expected,receipt=derive(template,original,definition,bid+'-trial.kicad_pro');project=json.loads(expected)
            self.assertEqual(project['board']['design_settings']['rules']['min_copper_edge_clearance'],.5)
            self.assertEqual(project['board']['design_settings']['rules']['min_track_width'],.2)
            self.assertTrue(receipt['all_unrelated_template_values_unchanged'])
            self.assertEqual(derive(template,original,definition,bid+'-trial.kicad_pro')[0],expected)
            weakened=json.loads(definition);weakened['routing']['min_track_width_mm']=.05
            with self.assertRaisesRegex(ValueError,'cannot weaken'):
                derive(template,original,json.dumps(weakened).encode(),bid+'-trial.kicad_pro')
            changed=json.loads(original);changed['foreign_setting']='preserve me'
            with self.assertRaisesRegex(ValueError,'known source form'):
                derive(template,json.dumps(changed).encode(),definition,bid+'-trial.kicad_pro')



if __name__=='__main__':unittest.main()
